"""
Provider Status Service — 聚合 Voice Lab Core 的 Provider 状态。

A1 阶段：固定返回 not_integrated，不调用 gateway 或 Core。
A3 阶段后：接入真实 gateway.get_provider_status()，改为动态查询。
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
        "真实 TTS 将在后续阶段通过 voice_lab_gateway 接入。"
    ),
    "quotaPct": 0.0,
}


class ProviderStatusService:

    def __init__(self, gateway: "VoiceLabGateway | None" = None) -> None:
        self._gw = gateway  # 保留参数，A3 接入时使用

    async def get_status(self) -> dict:
        """
        Returns:
            {"kind": str, "label": str, "detail": str, "quotaPct": float}

        A1 阶段固定返回 not_integrated，不调用 gateway 或外部 Provider。
        A3 接入后改为：return await self._gw.get_provider_status()
        """
        return dict(_NOT_INTEGRATED_STATUS)
