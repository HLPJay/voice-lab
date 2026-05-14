import re

from app.core.config import get_settings
from app.core.errors import UnsupportedProvider, ValidationError
from app.domain.capabilities import NumericRange, ProviderCapability
from app.providers.capability_registry import get_capability


class CapabilityValidator:
    def resolve_provider(self, provider: str | None) -> str:
        if provider:
            return provider
        return get_settings().voice_provider

    def get_capability(self, provider: str | None) -> ProviderCapability:
        resolved = self.resolve_provider(provider)
        try:
            return get_capability(resolved)
        except UnsupportedProvider as exc:
            raise ValidationError(
                message=f"不支持的 Provider：{provider}。",
                detail="UNSUPPORTED_PROVIDER",
            ) from exc

    def _fail(self, message: str, detail: str = "CAPABILITY_NOT_SUPPORTED"):
        raise ValidationError(message=message, detail=detail)

    def _validate_range(
        self,
        name: str,
        value: float | int | None,
        range_obj: NumericRange | None,
    ) -> None:
        if value is None:
            return
        if range_obj is None:
            self._fail(
                f"当前 Provider 不支持{name}参数。",
                detail="UNSUPPORTED_PARAM",
            )
            return
        if value < range_obj.min or value > range_obj.max:
            self._fail(
                f"当前 Provider 的{name}范围是 {range_obj.min} - {range_obj.max}。",
                detail="PARAM_OUT_OF_RANGE",
            )

    def _validate_audio_format(
        self,
        audio_format: str | None,
        supported_formats: list[str],
    ) -> None:
        if audio_format is None:
            return
        if audio_format not in supported_formats:
            self._fail(
                f"当前 Provider 不支持 {audio_format} 音频格式，仅支持 {', '.join(supported_formats)}。",
                detail="UNSUPPORTED_AUDIO_FORMAT",
            )

    def _validate_model(
        self,
        model: str | None,
        supported_models: list[str],
    ) -> None:
        if model is None:
            return
        if supported_models and model not in supported_models:
            self._fail(
                f"当前 Provider 不支持模型 {model}。",
                detail="UNSUPPORTED_MODEL",
            )

    def _validate_voice_id_pattern(
        self,
        voice_id: str,
        pattern: str,
    ) -> None:
        if not re.fullmatch(pattern, voice_id):
            self._fail(
                f"voice_id 格式不符合当前 Provider 要求。",
                detail="INVALID_VOICE_ID",
            )

    # ─── TTS ────────────────────────────────────────────────────────────────

    def validate_tts(
        self,
        *,
        provider: str | None,
        model: str | None = None,
        text: str | None = None,
        audio_format: str | None = None,
        need_subtitle: bool | None = None,
        speed: float | None = None,
        vol: float | None = None,
        pitch: int | None = None,
        emotion: str | None = None,
        require_streaming: bool = False,
    ) -> None:
        cap = self.get_capability(provider)

        if not cap.enabled:
            self._fail("当前 Provider 未启用。", detail="PROVIDER_DISABLED")

        if not cap.tts or not cap.tts.supported:
            self._fail("当前 Provider 不支持 TTS 语音生成。", detail="TTS_NOT_SUPPORTED")

        self._validate_model(model, cap.tts.models if cap.tts else [])

        if text is not None and cap.tts:
            if len(text) > cap.tts.max_text_chars:
                self._fail(
                    f"文本长度超出当前 Provider 的限制（最大 {cap.tts.max_text_chars} 字符）。",
                    detail="TEXT_TOO_LONG",
                )

        self._validate_audio_format(
            audio_format,
            cap.tts.audio_formats if cap.tts else [],
        )

        if need_subtitle and cap.tts and not cap.tts.supports_subtitle:
            self._fail(
                "当前 Provider 不支持字幕生成，请关闭字幕或切换 Provider。",
                detail="SUBTITLE_NOT_SUPPORTED",
            )

        if require_streaming and cap.tts and not cap.tts.supports_streaming:
            self._fail(
                "当前 Provider 不支持流式生成。",
                detail="STREAMING_NOT_SUPPORTED",
            )

        if emotion and cap.tts and not cap.tts.supports_emotion:
            self._fail(
                "当前 Provider 不支持情绪参数。",
                detail="EMOTION_NOT_SUPPORTED",
            )

        if cap.tts:
            self._validate_range("语速", speed, cap.tts.speed)
            self._validate_range("音量", vol, cap.tts.vol)
            self._validate_range("音调", pitch, cap.tts.pitch)

    # ─── Batch ────────────────────────────────────────────────────────────

    def validate_batch(
        self,
        *,
        provider: str | None,
        text: str,
        audio_format: str,
        need_subtitle: bool,
        segment_strategy: str,
        max_segment_chars: int,
        silence_between_ms: int,
    ) -> None:
        cap = self.get_capability(provider)

        if not cap.enabled:
            self._fail("当前 Provider 未启用。", detail="PROVIDER_DISABLED")

        if not cap.batch or not cap.batch.supported:
            self._fail("当前 Provider 不支持长文本批量生成。", detail="BATCH_NOT_SUPPORTED")

        if len(text) > cap.batch.max_text_chars:
            self._fail(
                f"文本长度超出当前 Provider 的限制（最大 {cap.batch.max_text_chars} 字符）。",
                detail="TEXT_TOO_LONG",
            )

        if cap.batch.segment_strategies and segment_strategy not in cap.batch.segment_strategies:
            self._fail(
                f"当前 Provider 不支持分段策略 {segment_strategy}，仅支持 {', '.join(cap.batch.segment_strategies)}。",
                detail="UNSUPPORTED_SEGMENT_STRATEGY",
            )

        if cap.batch.max_segment_chars:
            nr = cap.batch.max_segment_chars
            if max_segment_chars < nr.min or max_segment_chars > nr.max:
                self._fail(
                    f"当前 Provider 的每段字符范围是 {nr.min} - {nr.max}。",
                    detail="SEGMENT_CHARS_OUT_OF_RANGE",
                )

        if cap.batch.silence_between_ms:
            nr = cap.batch.silence_between_ms
            if silence_between_ms < nr.min or silence_between_ms > nr.max:
                self._fail(
                    f"当前 Provider 的段间静音范围是 {nr.min} - {nr.max} ms。",
                    detail="SILENCE_OUT_OF_RANGE",
                )

        if need_subtitle:
            if cap.batch and not cap.batch.supports_merge_subtitle:
                self._fail(
                    "当前 Provider 不支持批量字幕合并。",
                    detail="BATCH_SUBTITLE_NOT_SUPPORTED",
                )
            if cap.tts and not cap.tts.supports_subtitle:
                self._fail(
                    "当前 Provider 不支持字幕生成，请关闭字幕或切换 Provider。",
                    detail="SUBTITLE_NOT_SUPPORTED",
                )

        self._validate_audio_format(
            audio_format,
            cap.tts.audio_formats if cap.tts else [],
        )

    # ─── Script ───────────────────────────────────────────────────────────

    def validate_script(
        self,
        *,
        provider: str | None,
        script_count: int,
        audio_format: str,
        need_subtitle: bool,
        silence_between_ms: int,
    ) -> None:
        cap = self.get_capability(provider)

        if not cap.enabled:
            self._fail("当前 Provider 未启用。", detail="PROVIDER_DISABLED")

        if not cap.script or not cap.script.supported:
            self._fail("当前 Provider 不支持剧本文本批量生成。", detail="SCRIPT_NOT_SUPPORTED")

        if cap.script.max_segments and script_count > cap.script.max_segments:
            self._fail(
                f"当前 Provider 最多支持 {cap.script.max_segments} 个剧本角色，当前为 {script_count} 个。",
                detail="SCRIPT_COUNT_EXCEEDED",
            )

        if cap.script.silence_between_ms:
            nr = cap.script.silence_between_ms
            if silence_between_ms < nr.min or silence_between_ms > nr.max:
                self._fail(
                    f"当前 Provider 的段间静音范围是 {nr.min} - {nr.max} ms。",
                    detail="SILENCE_OUT_OF_RANGE",
                )

        if need_subtitle:
            if cap.script and not cap.script.supports_merge_subtitle:
                self._fail(
                    "当前 Provider 不支持剧本字幕合并。",
                    detail="SCRIPT_SUBTITLE_NOT_SUPPORTED",
                )
            if cap.tts and not cap.tts.supports_subtitle:
                self._fail(
                    "当前 Provider 不支持字幕生成，请关闭字幕或切换 Provider。",
                    detail="SUBTITLE_NOT_SUPPORTED",
                )

        self._validate_audio_format(
            audio_format,
            cap.tts.audio_formats if cap.tts else [],
        )

    # ─── Voice Clone ───────────────────────────────────────────────────────

    def validate_voice_clone(
        self,
        *,
        provider: str | None,
        voice_id: str,
        preview_text: str | None = None,
        need_noise_reduction: bool = False,
        need_volume_normalization: bool = False,
    ) -> None:
        cap = self.get_capability(provider)

        if not cap.enabled:
            self._fail("当前 Provider 未启用。", detail="PROVIDER_DISABLED")

        if not cap.voice_clone or not cap.voice_clone.supported:
            self._fail(
                "当前 Provider 不支持声音克隆。",
                detail="VOICE_CLONE_NOT_SUPPORTED",
            )

        if preview_text is not None and cap.voice_clone and cap.voice_clone.preview_text_max:
            if len(preview_text) > cap.voice_clone.preview_text_max:
                self._fail(
                    f"试听文本超出当前 Provider 的限制（最大 {cap.voice_clone.preview_text_max} 字符）。",
                    detail="PREVIEW_TEXT_TOO_LONG",
                )

        if need_noise_reduction and cap.voice_clone and not cap.voice_clone.supports_noise_reduction:
            self._fail(
                "当前 Provider 不支持降噪处理。",
                detail="NOISE_REDUCTION_NOT_SUPPORTED",
            )

        if need_volume_normalization and cap.voice_clone and not cap.voice_clone.supports_volume_normalization:
            self._fail(
                "当前 Provider 不支持音量标准化。",
                detail="VOLUME_NORMALIZATION_NOT_SUPPORTED",
            )

        if cap.voice_clone and cap.voice_clone.voice_id:
            self._validate_voice_id_pattern(voice_id, cap.voice_clone.voice_id.pattern)

    # ─── Voice Design ──────────────────────────────────────────────────────

    def validate_voice_design(
        self,
        *,
        provider: str | None,
        prompt: str,
        preview_text: str,
        voice_id: str | None = None,
    ) -> None:
        cap = self.get_capability(provider)

        if not cap.enabled:
            self._fail("当前 Provider 未启用。", detail="PROVIDER_DISABLED")

        if not cap.voice_design or not cap.voice_design.supported:
            self._fail(
                "当前 Provider 不支持声音设计。",
                detail="VOICE_DESIGN_NOT_SUPPORTED",
            )

        if cap.voice_design and cap.voice_design.prompt_max:
            if len(prompt) > cap.voice_design.prompt_max:
                self._fail(
                    f"prompt 超出当前 Provider 的限制（最大 {cap.voice_design.prompt_max} 字符）。",
                    detail="PROMPT_TOO_LONG",
                )

        if cap.voice_design and cap.voice_design.preview_text_max:
            if len(preview_text) > cap.voice_design.preview_text_max:
                self._fail(
                    f"试听文本超出当前 Provider 的限制（最大 {cap.voice_design.preview_text_max} 字符）。",
                    detail="PREVIEW_TEXT_TOO_LONG",
                )

        if voice_id and cap.voice_design and cap.voice_design.voice_id:
            self._validate_voice_id_pattern(voice_id, cap.voice_design.voice_id.pattern)

    # ─── Provider Voice Preview ───────────────────────────────────────────

    def validate_provider_voice_preview(
        self,
        *,
        provider: str | None,
        text: str,
        audio_format: str | None = None,
        need_subtitle: bool = False,
        speed: float | None = None,
        vol: float | None = None,
        pitch: int | None = None,
        emotion: str | None = None,
        model: str | None = None,
    ) -> None:
        cap = self.get_capability(provider)

        if not cap.enabled:
            self._fail("当前 Provider 未启用。", detail="PROVIDER_DISABLED")

        if not cap.provider_voices or not cap.provider_voices.supported:
            self._fail(
                "当前 Provider 不支持音色管理。",
                detail="PROVIDER_VOICES_NOT_SUPPORTED",
            )

        if cap.provider_voices and cap.provider_voices.preview_text_max:
            if len(text) > cap.provider_voices.preview_text_max:
                self._fail(
                    f"试听文本超出当前 Provider 的限制（最大 {cap.provider_voices.preview_text_max} 字符）。",
                    detail="PREVIEW_TEXT_TOO_LONG",
                )

        self._validate_audio_format(
            audio_format,
            cap.tts.audio_formats if cap.tts else [],
        )

        if need_subtitle and cap.tts and not cap.tts.supports_subtitle:
            self._fail(
                "当前 Provider 不支持字幕生成。",
                detail="SUBTITLE_NOT_SUPPORTED",
            )

        self._validate_model(model, cap.tts.models if cap.tts else [])

        if cap.tts:
            self._validate_range("语速", speed, cap.tts.speed)
            self._validate_range("音量", vol, cap.tts.vol)
            self._validate_range("音调", pitch, cap.tts.pitch)

        if emotion and cap.tts and not cap.tts.supports_emotion:
            self._fail(
                "当前 Provider 不支持情绪参数。",
                detail="EMOTION_NOT_SUPPORTED",
            )

    # ─── Provider Voice Import ────────────────────────────────────────────

    def validate_provider_voice_import(
        self,
        *,
        provider: str | None,
        preview_text: str,
        verify: bool = False,
        model: str | None = None,
    ) -> None:
        cap = self.get_capability(provider)

        if not cap.enabled:
            self._fail("当前 Provider 未启用。", detail="PROVIDER_DISABLED")

        if not cap.provider_voices or not cap.provider_voices.supported:
            self._fail(
                "当前 Provider 不支持音色管理。",
                detail="PROVIDER_VOICES_NOT_SUPPORTED",
            )

        if not cap.provider_voices.supports_import_remote_voice:
            self._fail(
                "当前 Provider 不支持远端音色导入。",
                detail="IMPORT_NOT_SUPPORTED",
            )

        if cap.provider_voices and cap.provider_voices.preview_text_max:
            if len(preview_text) > cap.provider_voices.preview_text_max:
                self._fail(
                    f"试听文本超出当前 Provider 的限制（最大 {cap.provider_voices.preview_text_max} 字符）。",
                    detail="PREVIEW_TEXT_TOO_LONG",
                )


capability_validator = CapabilityValidator()
