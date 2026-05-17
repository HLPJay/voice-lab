"""
Provider Status Service — 聚合 Voice Lab Core 的 Provider 状态。

将 Core 的技术状态（provider_kind, quota_used 等）映射为前端可显示的状态结构。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway


class ProviderStatusService:

    def __init__(self, gateway: "VoiceLabGateway") -> None:
        self._gw = gateway

    async def get_status(self) -> dict:
        """
        Returns:
            {"kind": "ok"|"degraded"|"quota"|"error",
             "label": str, "detail": str, "quotaPct": float}
        """
        # TODO(P17-A1): 调用 self._gw.get_provider_status()，映射为前端结构
        raise NotImplementedError
