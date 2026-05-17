"""
TTS Orchestrator — 调度 TTS 生成任务。

流程：
  1. 校验产品层输入（文案长度）
  2. preset_mapper.resolve_binding(voicePreset, tone) → CoreBindingRequest
  3. voice_lab_gateway.generate_tts_dry_run(...)
  4. 返回产品层任务响应

不直接调用 provider adapter。
不构造 voice_id / model_id / sample_rate 等 Provider 参数。
不直接读取配置文件或环境变量。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.xiangta.config.bootstrap_config import LIMITS
from src.xiangta.services.error_translator import (
    InvalidInputError,
    PresetNotFoundError,
    TextTooLongError,
)
from src.xiangta.services.preset_mapper import PresetMappingError

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
        Product-layer TTS dry-run.

        Returns:
            {
              "taskId": str,
              "status": "dry_run",
              "audioUrl": None,
              "durationMs": None,
              "charCount": int,
              "voicePreset": str,
              "tone": str,
              "message": str,
              "contract": {"coreBindingKey": str, ...},
            }

        Raises:
            InvalidInputError: 文案为空
            TextTooLongError:  文案超过 maxTtsChars
            PresetNotFoundError: voicePreset 或 tone 不存在 / 已禁用
        """
        if not text or not text.strip():
            raise InvalidInputError("文案不能为空。")

        max_chars = LIMITS["maxTtsChars"]
        if len(text) > max_chars:
            raise TextTooLongError(max_chars)

        try:
            binding = self._mapper.resolve_binding(voice_preset, tone)
        except PresetMappingError as exc:
            raise PresetNotFoundError(str(exc)) from exc

        result = await self._gw.generate_tts_dry_run(
            text=text,
            core_binding_key=binding["core_binding_key"],
            tone=tone,
            tone_hint=binding["tone_hint"],
            scene=scene,
            voice_preset=voice_preset,
            metadata={"recipient": recipient},
        )

        return {
            "taskId":      result["taskId"],
            "status":      result["status"],
            "audioUrl":    result.get("audioUrl"),
            "durationMs":  result.get("durationMs"),
            "charCount":   len(text),
            "voicePreset": voice_preset,
            "tone":        tone,
            "message":     result.get("message"),
            "contract":    result.get("contract"),
        }
