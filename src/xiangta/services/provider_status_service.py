"""
Provider Status Service - XiangTa product-layer provider status boundary.

B3: routes through VoiceLabGateway to Core GET /api/voice/runtime/status.
Falls back to not_integrated when gateway has no client, or degraded on
response errors.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway


_NOT_INTEGRATED_STATUS = {
    "kind": "not_integrated",
    "label": "语音服务待接入",
    "detail": "XiangTa Product Server 已初始化",
    "quotaPct": 0.0,
}

_DEGRADED_STATUS = {
    "kind": "degraded",
    "label": "语音服务状态未知",
    "detail": "Core runtime status unavailable",
    "quotaPct": 0.0,
}


class ProviderStatusService:
    def __init__(self, gateway: "VoiceLabGateway | None" = None) -> None:
        self._gw = gateway

    async def get_status(self) -> dict:
        """
        Return the current product-layer provider status snapshot.

        - No gateway → not_integrated
        - Gateway but no http_client (CoreStatusUnavailableError) → not_integrated
        - Gateway http_client returns bad response → degraded
        - Gateway returns state "available" → kind "ok"
        - Other states → degraded
        """
        if self._gw is None:
            return dict(_NOT_INTEGRATED_STATUS)

        from src.xiangta.services.voice_lab_gateway import CoreStatusUnavailableError

        try:
            raw = await self._gw.get_provider_status()
        except CoreStatusUnavailableError:
            return dict(_NOT_INTEGRATED_STATUS)
        except Exception:
            return dict(_DEGRADED_STATUS)

        state = raw.get("status", "unknown")
        message = raw.get("message") or ""

        if state == "available":
            return {
                "kind": "ok",
                "label": "语音服务可用",
                "detail": message or "mock runtime available",
                "quotaPct": raw.get("quota_pct", 0.0),
            }

        return {
            "kind": "degraded",
            "label": "语音服务状态未知",
            "detail": message or "Core runtime status unknown",
            "quotaPct": raw.get("quota_pct", 0.0),
        }
