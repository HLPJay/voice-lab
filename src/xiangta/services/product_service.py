"""
Product Service — 编排主业务流程。

作为各子服务（copywriting, tts, letter）的上层协调者。
路由层只调用 ProductService，不直接调用子服务。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.xiangta.services.copywriting_service import CopywritingService
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator
    from src.xiangta.services.letter_service import LetterService
    from src.xiangta.services.provider_status_service import ProviderStatusService

_CONFIGS_DIR = Path(__file__).parent.parent / "configs"

_STYLES: list[dict] = [
    {
        "id": "restrained",
        "label": "克制版",
        "desc": "少一点情绪外露，不给对方压力",
        "enabled": True,
    },
    {
        "id": "gentle",
        "label": "温柔版",
        "desc": "更柔和、更靠近一点",
        "enabled": True,
    },
    {
        "id": "sincere",
        "label": "真诚版",
        "desc": "认真表达，不绕弯",
        "enabled": True,
    },
]

_LIMITS: dict = {
    "maxRawTextChars": 500,
    "maxTtsChars": 500,
    "maxSuggestions": 3,
}


def _load_json(name: str) -> list[dict]:
    with open(_CONFIGS_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class ProductService:

    def __init__(
        self,
        provider_status: "ProviderStatusService",
        copywriting: "CopywritingService | None" = None,
        tts: "TtsOrchestrator | None" = None,
        letters: "LetterService | None" = None,
    ) -> None:
        self._provider_status = provider_status
        self._copywriting = copywriting
        self._tts = tts
        self._letters = letters

    async def get_bootstrap(self) -> dict[str, Any]:
        """
        返回前端启动所需的完整配置快照。
        读取本地 configs/*.json，不调用任何外部 API 或 voice_lab Core。
        """
        recipients  = _load_json("recipients.json")
        scenes      = _load_json("scenes.json")
        voices      = _load_json("voice_presets.json")
        tones       = _load_json("tone_presets.json")
        provider_status = await self._provider_status.get_status()

        return {
            "recipients":     recipients,
            "scenes":         scenes,
            "styles":         _STYLES,
            "voicePresets":   voices,
            "tonePresets":    tones,
            "limits":         _LIMITS,
            "providerStatus": provider_status,
        }

    async def get_provider_status(self) -> dict:
        return await self._provider_status.get_status()

    async def get_suggestions(self, recipient: str, scene: str, raw_text: str) -> dict:
        """参见 copywriting_service.generate_suggestions。"""
        # TODO(P17-A4)
        raise NotImplementedError

    async def generate_tts(
        self, *, text: str, voice_preset: str, tone: str, recipient: str, scene: str
    ) -> dict:
        """参见 tts_orchestrator.generate。"""
        # TODO(P17-A3)
        raise NotImplementedError


def create_product_service() -> ProductService:
    """默认工厂：A1 阶段只需要 ProviderStatusService（不需要 gateway）。"""
    from src.xiangta.services.provider_status_service import ProviderStatusService
    return ProductService(provider_status=ProviderStatusService(gateway=None))
