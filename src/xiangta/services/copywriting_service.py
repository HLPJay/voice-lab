"""
CopywritingService — 生成文案建议。

B5-1 版本：基于模板，不调用 LLM / 外部 API。
C8 版本：支持可选 CopywritingGateway（fake LLM）+ template fallback。
C10D-FIX2 版本：LLM timeout（8s）+ in-memory cache（5-min TTL，100-entry）+ degraded/latencyMs 字段。

输入：recipient, scene, raw_text
输出：summary + intent + 3 条 style 建议（restrained / gentle / sincere）
"""
from __future__ import annotations

import asyncio
import hashlib
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.copywriting_gateway import CopywritingGateway


# ── In-memory cache ────────────────────────────────────────────────────────────

class _CopywritingCache:
    """Process-local result cache for copywriting suggestions.

    TTL: 5 minutes per entry.
    Max entries: 100 (FIFO eviction when full).
    Key: sha256(recipient:scene:raw_text).
    """

    _MAX_SIZE = 100
    _TTL_SECS = 300  # 5 minutes

    def __init__(self) -> None:
        self._entries: dict[str, tuple[object, float]] = {}

    def _make_key(self, recipient: str, scene: str, raw_text: str) -> str:
        raw = f"{recipient}:{scene}:{raw_text}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, recipient: str, scene: str, raw_text: str) -> object | None:
        key = self._make_key(recipient, scene, raw_text)
        entry = self._entries.get(key)
        if entry is None:
            return None
        value, timestamp = entry
        if time.monotonic() - timestamp > self._TTL_SECS:
            del self._entries[key]
            return None
        return value

    def set(self, recipient: str, scene: str, raw_text: str, value: object) -> None:
        if len(self._entries) >= self._MAX_SIZE:
            # FIFO: remove oldest entry
            oldest_key = min(self._entries, key=lambda k: self._entries[k][1])
            del self._entries[oldest_key]
        key = self._make_key(recipient, scene, raw_text)
        self._entries[key] = (value, time.monotonic())

    def clear(self) -> None:
        self._entries.clear()


# ── Service ────────────────────────────────────────────────────────────────────

_DEFAULT_LLM_TIMEOUT_SECS = 8.0


class CopywritingService:

    def __init__(
        self,
        gateway: "CopywritingGateway | None" = None,
        fallback_to_template: bool = True,
        llm_timeout_secs: float = _DEFAULT_LLM_TIMEOUT_SECS,
        cache: _CopywritingCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._template_gateway = None  # lazy
        self._fallback_to_template = fallback_to_template
        self._llm_timeout_secs = llm_timeout_secs
        self._cache = cache or _CopywritingCache()

    def _get_template_gateway(self):
        """Lazy-load template gateway to avoid circular import at construction."""
        if self._template_gateway is None:
            from src.xiangta.services.copywriting_gateway import TemplateCopywritingGateway
            self._template_gateway = TemplateCopywritingGateway()
        return self._template_gateway

    def _to_dict(self, gateway_result, *, degraded: bool = False) -> dict:
        """Convert CopywritingResult to API dict (camelCase)."""
        return {
            "summary":   gateway_result.summary,
            "intent":    gateway_result.intent,
            "source":    gateway_result.source,
            "degraded":   degraded,
            "latencyMs": gateway_result.latency_ms,
            "suggestions": [
                {
                    "style":      s.style,
                    "styleLabel": s.style_label,
                    "fitsFor":    s.fits_for,
                    "text":       s.text,
                    "charCount":  len(s.text),
                }
                for s in gateway_result.suggestions
            ],
        }

    async def generate_suggestions(
        self,
        *,
        recipient: str,
        scene: str,
        raw_text: str,
    ) -> dict:
        """
        Generate 3 style suggestions (restrained / gentle / sincere).

        Cache lookup is keyed on recipient+scene+raw_text.

        If gateway is set, try gateway.generate() first with llm_timeout_secs timeout.
        On timeout or other gateway failure with fallback=True, fall back to template.
        On gateway failure with fallback=False, raise LlmFailedError.
        """
        raw_text = raw_text.strip()
        if not raw_text:
            raise ValueError("raw_text 不能为空")

        from src.xiangta.services.copywriting_gateway import CopywritingRequest
        from src.xiangta.services.error_translator import LlmFailedError

        # Cache lookup (only for non-empty raw_text)
        cached = self._cache.get(recipient, scene, raw_text)
        if cached is not None:
            return self._to_dict(cached)

        request = CopywritingRequest(
            recipient=recipient,
            scene=scene,
            raw_text=raw_text,
        )

        if self._gateway is None:
            tg = self._get_template_gateway()
            result = await tg.generate(request)
            self._cache.set(recipient, scene, raw_text, result)
            return self._to_dict(result)

        # Try LLM gateway with timeout
        try:
            result = await asyncio.wait_for(
                self._gateway.generate(request),
                timeout=self._llm_timeout_secs,
            )
            self._cache.set(recipient, scene, raw_text, result)
            return self._to_dict(result)
        except TimeoutError:
            # LLM timeout — fall back to template
            tg = self._get_template_gateway()
            fallback_result = await tg.generate(request)
            self._cache.set(recipient, scene, raw_text, fallback_result)
            return self._to_dict(fallback_result, degraded=True)
        except Exception:
            if self._fallback_to_template:
                tg = self._get_template_gateway()
                fallback_result = await tg.generate(request)
                self._cache.set(recipient, scene, raw_text, fallback_result)
                return self._to_dict(fallback_result, degraded=True)
            raise LlmFailedError()
