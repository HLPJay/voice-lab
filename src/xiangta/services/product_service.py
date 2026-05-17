"""
Product Service — 编排主业务流程。

作为各子服务（copywriting, tts, letter）的上层协调者。
路由层只调用 ProductService，不直接调用子服务。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.copywriting_service import CopywritingService
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator
    from src.xiangta.services.letter_service import LetterService
    from src.xiangta.services.provider_status_service import ProviderStatusService


class ProductService:

    def __init__(
        self,
        copywriting: "CopywritingService",
        tts: "TtsOrchestrator",
        letters: "LetterService",
        provider_status: "ProviderStatusService",
    ) -> None:
        self._copywriting = copywriting
        self._tts = tts
        self._letters = letters
        self._provider_status = provider_status

    async def get_suggestions(self, recipient: str, scene: str, raw_text: str) -> dict:
        """参见 copywriting_service.generate_suggestions。"""
        # TODO(P17-A2)
        return await self._copywriting.generate_suggestions(
            recipient=recipient, scene=scene, raw_text=raw_text,
        )

    async def generate_tts(self, *, text: str, voice_preset: str, tone: str, recipient: str, scene: str) -> dict:
        """参见 tts_orchestrator.generate。"""
        # TODO(P17-A3)
        return await self._tts.generate(
            text=text, voice_preset=voice_preset, tone=tone,
            recipient=recipient, scene=scene,
        )

    async def get_provider_status(self) -> dict:
        """参见 provider_status_service.get_status。"""
        # TODO(P17-A1)
        return await self._provider_status.get_status()
