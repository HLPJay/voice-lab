"""
TTS Orchestrator — 调度 TTS 生成任务。

流程：
  1. preset_mapper.resolve_binding(voicePreset, tone) → CoreBindingRequest
  2. voice_lab_gateway.generate_tts(text, core_binding_key, tone, scene, style)
  3. 返回 TtsData（audioUrl, durationSecs, taskId）

不直接调用 provider adapter。
不构造 voice_id / model_id / sample_rate 等 Provider 参数。
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
        # 1. binding_request = self._mapper.resolve_binding(voice_preset, tone)
        # 2. result = await self._gw.generate_tts(
        #        text=text,
        #        core_binding_key=binding_request["core_binding_key"],
        #        tone=tone,
        #        scene=scene,
        #        style=None,
        #        metadata={"recipient": recipient, "voicePreset": voice_preset},
        #    )
        # 3. 构造并返回 TtsData 字典
        raise NotImplementedError
