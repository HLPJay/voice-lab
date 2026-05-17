"""
TTS Orchestrator — 调度 TTS 生成任务。

流程：
  1. 校验产品层输入（文案长度）
  2. VoicePresetMappingService.resolve(voicePreset) → ProductVoiceMapping
  3. TonePresetService.resolve(tone) → TonePreset
  4. 组装 CoreRenderTarget
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

if TYPE_CHECKING:
    from src.xiangta.services.tone_preset_service import TonePresetService
    from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway


class TtsOrchestrator:

    def __init__(
        self,
        gateway: "VoiceLabGateway",
        voice_mapping_service: "VoicePresetMappingService",
        tone_preset_service: "TonePresetService",
    ) -> None:
        self._gw = gateway
        self._voice_mapping_service = voice_mapping_service
        self._tone_preset_service = tone_preset_service

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
              "contract": {"voicePresetId": str, ...},
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
            mapping = self._voice_mapping_service.resolve(voice_preset)
            tone_preset = self._tone_preset_service.resolve(tone)
        except Exception as exc:
            raise PresetNotFoundError(str(exc)) from exc

        from src.xiangta.services.voice_lab_gateway import CoreRenderTarget

        render_overrides = {}
        render_overrides.update(mapping.render_overrides)
        render_overrides.update(tone_preset.render_overrides)
        target = CoreRenderTarget(
            profile_id=mapping.core_profile_id,
            provider=mapping.provider_policy,
            need_subtitle=bool(render_overrides.get("need_subtitle", True)),
            output_format=str(render_overrides.get("output_format", "url")),
            audio_format=str(render_overrides.get("audio_format", "mp3")),
            speed=render_overrides.get("speed"),
            vol=render_overrides.get("vol"),
            pitch=render_overrides.get("pitch"),
            emotion=render_overrides.get("emotion"),
        )

        result = await self._gw.generate_tts_dry_run(
            text=text,
            target=target,
            tone=tone,
            tone_hint=tone_preset.style_hint,
            scene=scene,
            voice_preset_id=voice_preset,
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
