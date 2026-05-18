# -*- coding: utf-8 -*-
"""
MiniMax Copywriting Gateway — C10D.

Real MiniMax LLM adapter for copywriting suggestions.
Behind flag, default disabled.

真实 MiniMax API 字段和模型效果仍需 C10E 手工联调确认。
"""
from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Protocol

from src.xiangta.services.copywriting_gateway import (
    CopywritingRequest,
    CopywritingResult,
    CopywritingSuggestion,
)
from src.xiangta.services.copywriting_prompt_contract import (
    PromptContractInput,
    build_copywriting_prompt_contract,
)


# ── Protocol ────────────────────────────────────────────────────────────────────

class MiniMaxHttpClient(Protocol):
    """Abortable HTTP client for MiniMax copywriting API."""

    async def create_chat_completion(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        timeout_seconds: float,
    ) -> dict:
        ...


# ── Real HTTP client (stdlib only) ─────────────────────────────────────────────

class UrllibMiniMaxHttpClient:
    """Real MiniMax HTTP client using urllib. Does not print api_key."""

    async def create_chat_completion(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        timeout_seconds: float,
    ) -> dict:
        """
        Send a chat completion request to MiniMax API.

        Returns parsed JSON response dict.
        Raises MiniMaxHttpError on network or HTTP error.
        """
        url = f"{base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model,
            "messages": messages,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise MiniMaxHttpError(f"HTTP {exc.code}: {body[:200]}")
        except urllib.error.URLError as exc:
            raise MiniMaxHttpError(f"Network error: {exc.reason}")
        except json.JSONDecodeError as exc:
            raise MiniMaxHttpError(f"Invalid JSON response: {exc}")


class MiniMaxHttpError(Exception):
    """Raised on network or HTTP error from MiniMax API."""


# ── Response parse error ─────────────────────────────────────────────────────────

class MiniMaxCopywritingResponseError(Exception):
    """Raised when LLM response cannot be parsed or fails validation."""


# ── Response parser ───────────────────────────────────────────────────────────────

_STRICT_STYLES = frozenset({"restrained", "gentle", "sincere"})
_STRICT_STYLE_LABELS = frozenset({"克制版", "温柔版", "真诚版"})
_FORBIDDEN_OUTPUT_FIELDS = frozenset({"apikey", "coreprofileid", "providerrawresponse", "rawresponse"})


def parse_minimax_copywriting_response(payload: dict) -> CopywritingResult:
    """
    Parse MiniMax LLM JSON response into CopywritingResult.

    Handles:
    - Content in ``choices[0].message.content``
    - Content in ``reply`` (common alt field)
    - Content in ``content``
    - Content in ``data.choices[0].message.content``
    - JSON wrapped in ```json ...```
    - Extra whitespace / newlines
    - Missing or extra suggestions
    - Invalid styles

    Raises MiniMaxCopywritingResponseError on validation failure.
    """
    # Extract text content from response
    content = _extract_content(payload)

    # Parse JSON — handle ```json fences
    try:
        parsed = _extract_json(content)
    except Exception as exc:
        raise MiniMaxCopywritingResponseError(
            f"Failed to parse JSON from LLM response: {exc}"
        )

    # Validate top-level structure
    if not isinstance(parsed, dict):
        raise MiniMaxCopywritingResponseError(
            f"Expected JSON object, got {type(parsed).__name__}"
        )

    summary = _field_str(parsed, "summary")
    intent = _field_str(parsed, "intent")

    # Parse suggestions
    suggestions_raw = parsed.get("suggestions")
    if not isinstance(suggestions_raw, list):
        raise MiniMaxCopywritingResponseError(
            f"Expected suggestions to be a list, got {type(suggestions_raw).__name__}"
        )

    suggestions = []
    for i, item in enumerate(suggestions_raw):
        if not isinstance(item, dict):
            raise MiniMaxCopywritingResponseError(
                f"Suggestion {i} is not a dict"
            )

        style = str(item.get("style") or "").strip().lower()
        style_label = str(item.get("styleLabel") or "").strip()
        fits_for = _field_str(item, "fitsFor")
        text = _field_str(item, "text")

        if style not in _STRICT_STYLES:
            raise MiniMaxCopywritingResponseError(
                f"Suggestion {i} has invalid style: {style!r} "
                f"(expected one of {list(_STRICT_STYLES)})"
            )

        if not text:
            raise MiniMaxCopywritingResponseError(
                f"Suggestion {i} has empty text"
            )

        if not fits_for:
            raise MiniMaxCopywritingResponseError(
                f"Suggestion {i} has empty fitsFor"
            )

        suggestions.append(CopywritingSuggestion(
            style=style,
            style_label=style_label or _DEFAULT_STYLE_LABELS.get(style, style),
            fits_for=fits_for,
            text=text,
        ))

    if len(suggestions) != 3:
        raise MiniMaxCopywritingResponseError(
            f"Expected exactly 3 suggestions, got {len(suggestions)}"
        )

    # Check for forbidden fields in output
    result_str = json.dumps(parsed)
    for field in _FORBIDDEN_OUTPUT_FIELDS:
        if field in result_str.lower():
            raise MiniMaxCopywritingResponseError(
                f"Output contains forbidden field: {field}"
            )

    return CopywritingResult(
        summary=summary or "AI 整理你的表达",
        intent=intent or "在保留原意的基础上，生成更适合发送的情绪文案",
        suggestions=suggestions,
        source="minimax",
    )


_DEFAULT_STYLE_LABELS = {
    "restrained": "克制版",
    "gentle": "温柔版",
    "sincere": "真诚版",
}


def _extract_content(payload: dict) -> str:
    """Extract text content from various MiniMax response shapes."""
    # shape: {"choices":[{"message":{"content":"..."}}]}
    try:
        choices = payload.get("choices") or []
        if choices:
            msg = choices[0].get("message", {})
            content = msg.get("content")
            if content:
                return str(content).strip()
    except (TypeError, IndexError, AttributeError):
        pass

    # shape: {"reply": "..."}
    reply = payload.get("reply")
    if reply:
        return str(reply).strip()

    # shape: {"content": "..."}
    content = payload.get("content")
    if content:
        return str(content).strip()

    # shape: {"data":{"choices":[{"message":{"content":"..."}}]}}
    try:
        data = payload.get("data") or {}
        data_choices = data.get("choices") or []
        if data_choices:
            msg = data_choices[0].get("message", {})
            content = msg.get("content")
            if content:
                return str(content).strip()
    except (TypeError, IndexError, AttributeError):
        pass

    raise MiniMaxCopywritingResponseError(
        f"Cannot extract content from response keys: {list(payload.keys())}"
    )


def _extract_json(content: str) -> dict:
    """Extract JSON from content, handling ```json fences."""
    content = content.strip()

    # Remove markdown code fences
    fenced = re.match(r"^\s*```(?:json)?\s*(.*?)```\s*$", content, re.DOTALL)
    if fenced:
        content = fenced.group(1).strip()

    return json.loads(content)


def _field_str(obj: dict, key: str) -> str:
    """Return a string field or empty string."""
    val = obj.get(key)
    if val is None:
        return ""
    return str(val).strip()


# ── Gateway ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MiniMaxCopywritingGateway:
    """
    MiniMax LLM copywriting gateway.

    - Reuses build_copywriting_prompt_contract() for prompt construction
    - Validates output with parse_minimax_copywriting_response()
    - Raises MiniMaxCopywritingResponseError on invalid response
    - Raises MiniMaxHttpError on network error

    The caller (CopywritingService) handles fallback when these are raised.
    """
    api_key: str
    base_url: str
    model: str
    timeout_seconds: float = 20.0
    _http_client: MiniMaxHttpClient | None = None

    @property
    def _client(self) -> MiniMaxHttpClient:
        if self._http_client is not None:
            return self._http_client
        return UrllibMiniMaxHttpClient()

    def _to_chat_messages(self, prompt_contract) -> list[dict]:
        """Convert PromptContract messages to MiniMax chat format."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in prompt_contract.messages
        ]

    async def generate(self, request: CopywritingRequest) -> CopywritingResult:
        """
        Generate copywriting suggestions via MiniMax LLM.

        Uses the C10C prompt contract.
        Raises MiniMaxCopywritingResponseError on parse/validation failure.
        Raises MiniMaxHttpError on network failure.
        """
        # Build prompt via contract
        contract_input = PromptContractInput(
            recipient=request.recipient,
            scene=request.scene,
            raw_text=request.raw_text,
            max_suggestions=request.max_suggestions,
        )
        contract = build_copywriting_prompt_contract(contract_input)

        # Call MiniMax
        messages = self._to_chat_messages(contract)
        payload = await self._client.create_chat_completion(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            timeout_seconds=self.timeout_seconds,
        )

        # Parse and validate response
        return parse_minimax_copywriting_response(payload)
