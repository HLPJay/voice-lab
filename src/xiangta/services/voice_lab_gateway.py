"""
Voice Lab Gateway - XiangTa access boundary for Core contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
import uuid
from typing import Any


# ── 允许 XiangTa 使用的 Core HTTP API 路径常量（不 import Core） ────────────────

CORE_PROFILES_PATH = "/api/voice/profiles"
CORE_RENDER_PATH = "/api/voice/render"
CORE_STATUS_PATH = "/api/voice/runtime/status"

# ── 安全字段过滤列表 ────────────────────────────────────────────────────────────

FORBIDDEN_PROFILE_FIELDS = frozenset({
    "api_key",
    "provider_voice_id",
    "binding_id",
    "params_json",
    "model_id",
    "voice_id",
    "provider",
    "stack_trace",
    "core_binding_key",
    "coreBindingKey",
})


def _filter_profile(raw: dict) -> dict:
    """过滤 Core profile 中的 forbidden fields，只保留安全字段。"""
    return {k: v for k, v in raw.items() if k not in FORBIDDEN_PROFILE_FIELDS}


@dataclass(frozen=True)
class CoreRenderTarget:
    profile_id: str
    provider: str | None = None  # None / "default" / "mock" / "minimax" / "xiaomi_mimo"
    need_subtitle: bool = True
    output_format: str = "url"
    audio_format: str = "mp3"
    speed: float | None = None
    vol: float | None = None
    pitch: int | None = None
    emotion: str | None = None


class CoreRenderError(Exception):
    """Base error for XiangTa to Core render contract failures."""


class CoreRenderUnavailableError(CoreRenderError):
    """Raised when the gateway has no injected Core client for render calls."""


class CoreRenderResponseError(CoreRenderError):
    """Raised when the Core render response does not match the contract."""


class CoreStatusError(Exception):
    """Base error for XiangTa to Core status contract failures."""


class CoreStatusUnavailableError(CoreStatusError):
    """Raised when the gateway has no injected Core client for status calls."""


class CoreStatusResponseError(CoreStatusError):
    """Raised when the Core status response does not match the contract."""


class CoreProfilesError(Exception):
    """Base error for XiangTa to Core profiles query failures."""


class CoreProfilesUnavailableError(CoreProfilesError):
    """Raised when the gateway has no injected Core client for profiles calls."""


class CoreProfilesResponseError(CoreProfilesError):
    """Raised when the Core profiles response does not match the contract."""


class VoiceLabGateway:
    """Gateway for XiangTa-to-Core high-level calls."""

    def __init__(self, *, core_base_url: str = "", http_client: object | None = None) -> None:
        self._core_base_url = core_base_url.rstrip("/")
        self._http_client = http_client

    async def list_profiles(self) -> list[dict]:
        """Call Core GET /api/voice/profiles and return safe profile dicts."""
        if self._http_client is None:
            raise CoreProfilesUnavailableError(
                "VoiceLabGateway.list_profiles requires an injected Core HTTP client"
            )

        response = await self._http_client.get(self._profiles_path())
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()

        body = response.json() if hasattr(response, "json") else response
        if not isinstance(body, list):
            raise CoreProfilesResponseError(
                f"Core profiles response must be a list, got {type(body).__name__}"
            )

        # 过滤 forbidden fields，每个 profile 只返回安全字段
        return [_filter_profile(p) for p in body if isinstance(p, dict)]

    async def generate_tts(
        self,
        *,
        text: str,
        target: CoreRenderTarget,
        tone: str,
        scene: str,
        style: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call the Core render HTTP contract through an injected client."""
        if self._http_client is None:
            raise CoreRenderUnavailableError(
                "VoiceLabGateway.generate_tts requires an injected Core HTTP client"
            )

        # Provider 策略：B9 要求
        # - target.provider 为 None 或 "default"：不传 provider，让 Core 使用默认策略
        # - target.provider 为 "mock" / "minimax" / "xiaomi_mimo"：显式传给 Core
        _provider = target.provider
        if _provider is None or _provider == "default":
            # 不传 provider，或传 None，让 Core 使用默认策略
            provider_value: str | None = None
        else:
            provider_value = _provider

        payload = {
            "text": text,
            "profile_id": target.profile_id,
            "need_subtitle": target.need_subtitle,
            "output_format": "url",
            "audio_format": target.audio_format,
            "confirm_cost": False,
        }
        # 只有非 None 才加入 payload
        if provider_value is not None:
            payload["provider"] = provider_value

        for key in ("speed", "vol", "pitch", "emotion"):
            value = getattr(target, key)
            if value is not None:
                payload[key] = value

        response = await self._http_client.post(self._render_path(), json=payload)
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()

        body = response.json() if hasattr(response, "json") else response
        if not isinstance(body, dict):
            raise CoreRenderResponseError("Core render response must be a JSON object")

        if body.get("status") != "success":
            raise CoreRenderResponseError("Core render returned a non-success status")

        audio_asset = body.get("audio_asset")
        if not isinstance(audio_asset, dict):
            raise CoreRenderResponseError("Core render response missing audio_asset")

        audio_url = audio_asset.get("url")
        if not audio_url:
            raise CoreRenderResponseError("Core render response missing audio_asset.url")

        # B9-FIX3: convert relative audio URL to absolute so browser can play it
        if hasattr(self._http_client, "absolute_url"):
            audio_url = self._http_client.absolute_url(audio_url)

        duration_ms = audio_asset.get("duration_ms")
        contract = self._build_contract(
            tone=tone,
            scene=scene,
            style=style,
            metadata=metadata,
        )
        return {
            "taskId": body.get("job_id"),
            "status": "completed",
            "audioUrl": audio_url,
            "durationMs": duration_ms,
            "message": None,
            "contract": contract,
        }

    async def generate_tts_dry_run(
        self,
        *,
        text: str,
        target: CoreRenderTarget,
        tone: str,
        tone_hint: str,
        scene: str,
        voice_preset_id: str,
        style: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Dry-run contract without Core or provider access."""
        _ = (text, target, style, metadata)
        return {
            "taskId": f"dryrun_{uuid.uuid4().hex[:8]}",
            "status": "dry_run",
            "audioUrl": None,
            "durationMs": None,
            "message": "dry-run only, no provider call",
            "contract": {
                "voicePresetId": voice_preset_id,
                "tone": tone,
                "toneHint": tone_hint,
                "scene": scene,
                "mode": "dry_run",
            },
        }

    async def get_provider_status(self) -> dict[str, Any]:
        """Call Core GET /api/voice/runtime/status and return a safe status dict."""
        if self._http_client is None:
            raise CoreStatusUnavailableError(
                "VoiceLabGateway.get_provider_status requires an injected Core HTTP client"
            )

        response = await self._http_client.get(self._status_path())
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()

        body = response.json() if hasattr(response, "json") else response
        if not isinstance(body, dict):
            raise CoreStatusResponseError("Core status response must be a JSON object")

        provider_status = body.get("provider_status", {})
        if not isinstance(provider_status, dict):
            raise CoreStatusResponseError("Core status response missing provider_status object")

        state = provider_status.get("state", "unknown")
        message = provider_status.get("detail") or provider_status.get("label") or "mock runtime status"

        return {
            "ok": True,
            "provider": "mock",
            "status": state,
            "quota_pct": 0.0,
            "message": message,
        }

    async def generate_llm_text(
        self,
        *,
        prompt: str,
        max_tokens: int = 512,
    ) -> str:
        _ = (prompt, max_tokens)
        raise NotImplementedError

    def _profiles_path(self) -> str:
        if self._core_base_url:
            return f"{self._core_base_url}{CORE_PROFILES_PATH}"
        return CORE_PROFILES_PATH

    def _status_path(self) -> str:
        if self._core_base_url:
            return f"{self._core_base_url}{CORE_STATUS_PATH}"
        return CORE_STATUS_PATH

    def _render_path(self) -> str:
        if self._core_base_url:
            return f"{self._core_base_url}{CORE_RENDER_PATH}"
        return CORE_RENDER_PATH

    def _build_contract(
        self,
        *,
        tone: str,
        scene: str,
        style: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        voice_preset_id = metadata.get("voicePresetId") or metadata.get("voice_preset_id") or ""
        tone_hint = metadata.get("toneHint") or metadata.get("tone_hint") or ""
        contract = {
            "voicePresetId": voice_preset_id,
            "tone": tone,
            "toneHint": tone_hint,
            "scene": scene,
            "mode": "core_render_mock",
        }
        if style:
            contract["style"] = style
        return contract


_gateway: VoiceLabGateway | None = None


def get_gateway() -> VoiceLabGateway:
    global _gateway
    if _gateway is None:
        _gateway = VoiceLabGateway()
    return _gateway
