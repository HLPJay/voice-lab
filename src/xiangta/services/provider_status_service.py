"""
Provider Status Service - XiangTa product-layer provider status boundary.

B1 keeps a fixed `not_integrated` status and must not call Core, Providers,
or environment-based runtime checks.

B2/B3 may later route through VoiceLabGateway to Core
GET /api/voice/runtime/status.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway


_NOT_INTEGRATED_STATUS = {
    "kind": "not_integrated",
    "label": "语音服务待接入",
    "detail": (
        "XiangTa Product Server 已初始化，"
        "真实 TTS 状态将在后续阶段通过 VoiceLabGateway 接入 Core runtime/status。"
    ),
    "quotaPct": 0.0,
}


class ProviderStatusService:
    def __init__(self, gateway: "VoiceLabGateway | None" = None) -> None:
        # Kept for future B2/B3 integration; unused in B1.
        self._gw = gateway

    async def get_status(self) -> dict:
        """
        Return the current product-layer provider status snapshot.

        B1 always returns `not_integrated` and does not call gateway/Core.
        """
        return dict(_NOT_INTEGRATED_STATUS)
