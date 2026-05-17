"""
TTS Orchestrator — 调度 TTS 生成任务。

流程：
  1. preset_mapper 将 voicePreset + tone → Core 参数
  2. voice_lab_gateway.generate_tts(text, **core_params)
  3. 返回 TtsData（audioUrl, durationSecs, taskId）

不直接调用 provider adapter，不暴露 voice_id 等参数给上层。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
    from src.xiangta.services.preset_mapper import PresetMapper


class TtsOrchestrator:

    def __init__(self, gateway: "VoiceLabGateway", mapper: "PresetMapper") -> None:
        self._gw = gateway
        self._mapper = mapper

    async def generate(
        self,
        *,
        text: str,
        voice_preset: str,
        tone: str,
        recipient: str,
        scene: str,
    ) -> dict:
        """
        Returns:
            {"taskId": str, "audioUrl": str, "durationSecs": float, "charCount": int,
             "voicePreset": str, "tone": str}
        """
        # TODO(P17-A3):
        # 1. core_params = self._mapper.resolve_voice(voice_preset, tone)
        # 2. result = await self._gw.generate_tts(text=text, **core_params)
        # 3. 构造并返回 TtsData 字典
        raise NotImplementedError
