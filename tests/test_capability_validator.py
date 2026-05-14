import pytest

from app.core.errors import UnsupportedProvider, ValidationError
from app.domain.capabilities import (
    BatchCapability,
    NumericRange,
    ProviderCapability,
    ProviderVoiceCapability,
    TTSCapability,
    VoiceCloneCapability,
    VoiceDesignCapability,
    VoiceIdConstraint,
)
from app.services.capability_validator import CapabilityValidator


VOICE_ID_PATTERN = r"^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
VOICE_ID_HINT = "至少 8 位，必须以字母开头。"


_UNSET = object()


def make_tts_cap(
    supported=True,
    models=None,
    default_model=None,
    max_text_chars=10000,
    audio_formats=None,
    supports_subtitle=True,
    supports_streaming=True,
    supports_emotion=True,
    speed_range=_UNSET,
    vol_range=_UNSET,
    pitch_range=_UNSET,
):
    if models is None:
        models = ["mock-tts"]
    if audio_formats is None:
        audio_formats = ["mp3", "wav", "flac"]
    return TTSCapability(
        supported=supported,
        models=models,
        default_model=default_model or (models[0] if models else None),
        max_text_chars=max_text_chars,
        audio_formats=audio_formats,
        supports_subtitle=supports_subtitle,
        supports_streaming=supports_streaming,
        supports_emotion=supports_emotion,
        speed=speed_range if speed_range is not _UNSET else NumericRange(min=0.5, max=2.0),
        vol=vol_range if vol_range is not _UNSET else NumericRange(min=0.1, max=10.0),
        pitch=pitch_range if pitch_range is not _UNSET else NumericRange(min=-12, max=12),
    )


def make_batch_cap(supported=True, max_text_chars=50000, segment_strategies=None, max_segments=200, max_segment_chars=_UNSET, silence_between_ms=_UNSET):
    if segment_strategies is None:
        segment_strategies = ["auto", "line"]
    return BatchCapability(
        supported=supported,
        max_text_chars=max_text_chars,
        max_segments=max_segments,
        segment_strategies=segment_strategies,
        max_segment_chars=max_segment_chars if max_segment_chars is not _UNSET else NumericRange(min=100, max=5000),
        silence_between_ms=silence_between_ms if silence_between_ms is not _UNSET else NumericRange(min=0, max=3000),
        supports_merge_audio=True,
        supports_merge_subtitle=True,
    )


def make_provider_cap(
    provider="test",
    display_name="Test",
    enabled=True,
    default_model=None,
    tts=None,
    batch=None,
    script=None,
    voice_clone=None,
    voice_design=None,
    provider_voices=None,
    metadata=None,
):
    return ProviderCapability(
        provider=provider,
        display_name=display_name,
        enabled=enabled,
        default_model=default_model,
        tts=tts,
        batch=batch,
        script=script,
        voice_clone=voice_clone,
        voice_design=voice_design,
        provider_voices=provider_voices,
        metadata=metadata or {},
    )


class TestValidateTTS:
    def _make_validator(self, cap):
        v = CapabilityValidator()
        v.get_capability = lambda p: cap
        return v

    def test_validate_tts_passes_with_valid_params(self):
        cap = make_provider_cap(
            tts=make_tts_cap(models=["mock-tts"], audio_formats=["mp3"]),
            batch=make_batch_cap(),
        )
        v = self._make_validator(cap)
        v.validate_tts(provider="test", text="hello", audio_format="mp3")

    def test_validate_tts_provider_not_found(self, monkeypatch):
        def fake_get_capability(provider):
            raise UnsupportedProvider(provider)
        monkeypatch.setattr("app.services.capability_validator.get_capability", fake_get_capability)
        v = CapabilityValidator()
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="bad")
        assert "UNSUPPORTED_PROVIDER" in exc_info.value.detail

    def test_validate_tts_unsupported_subtitle(self):
        cap = make_provider_cap(
            tts=make_tts_cap(supports_subtitle=False, audio_formats=["mp3"]),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", need_subtitle=True)
        assert "SUBTITLE_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_tts_unsupported_audio_format(self):
        cap = make_provider_cap(
            tts=make_tts_cap(audio_formats=["mp3"]),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", audio_format="flac")
        assert "UNSUPPORTED_AUDIO_FORMAT" in exc_info.value.detail

    def test_validate_tts_speed_out_of_range(self):
        cap = make_provider_cap(
            tts=make_tts_cap(speed_range=NumericRange(min=0.5, max=2.0)),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", speed=3.0)
        assert "PARAM_OUT_OF_RANGE" in exc_info.value.detail or "语速范围" in exc_info.value.message

    def test_validate_tts_emotion_not_supported(self):
        cap = make_provider_cap(
            tts=make_tts_cap(supports_emotion=False),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", emotion="happy")
        assert "EMOTION_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_tts_require_streaming_but_not_supported(self):
        cap = make_provider_cap(
            tts=make_tts_cap(supports_streaming=False),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", require_streaming=True)
        assert "STREAMING_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_tts_unsupported_param_when_range_is_none(self):
        cap = make_provider_cap(
            tts=make_tts_cap(speed_range=None),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", speed=1.0)
        assert "UNSUPPORTED_PARAM" in exc_info.value.detail

    def test_validate_tts_text_too_long(self):
        cap = make_provider_cap(
            tts=make_tts_cap(max_text_chars=100),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", text="a" * 200)
        assert "TEXT_TOO_LONG" in exc_info.value.detail

    def test_validate_tts_provider_disabled(self):
        cap = make_provider_cap(enabled=False, tts=make_tts_cap())
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test")
        assert "PROVIDER_DISABLED" in exc_info.value.detail

    def test_validate_tts_tts_not_supported(self):
        cap = make_provider_cap(tts=TTSCapability(supported=False))
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test")
        assert "TTS_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_tts_unsupported_model(self):
        cap = make_provider_cap(
            tts=make_tts_cap(models=["model-a"]),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_tts(provider="test", model="model-b")
        assert "UNSUPPORTED_MODEL" in exc_info.value.detail


class TestValidateBatch:
    def _make_validator(self, cap):
        v = CapabilityValidator()
        v.get_capability = lambda p: cap
        return v

    def test_validate_batch_passes_with_valid_params(self):
        cap = make_provider_cap(
            tts=make_tts_cap(audio_formats=["mp3"]),
            batch=make_batch_cap(segment_strategies=["auto", "line"]),
        )
        v = self._make_validator(cap)
        v.validate_batch(
            provider="test",
            text="hello",
            audio_format="mp3",
            need_subtitle=False,
            segment_strategy="auto",
            max_segment_chars=2000,
            silence_between_ms=300,
        )

    def test_validate_batch_unsupported_segment_strategy(self):
        cap = make_provider_cap(
            batch=make_batch_cap(segment_strategies=["auto"]),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_batch(
                provider="test",
                text="hello",
                audio_format="mp3",
                need_subtitle=False,
                segment_strategy="line",
                max_segment_chars=2000,
                silence_between_ms=300,
            )
        assert "UNSUPPORTED_SEGMENT_STRATEGY" in exc_info.value.detail

    def test_validate_batch_max_segment_chars_out_of_range(self):
        cap = make_provider_cap(
            batch=make_batch_cap(max_segment_chars=NumericRange(min=100, max=5000)),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_batch(
                provider="test",
                text="hello",
                audio_format="mp3",
                need_subtitle=False,
                segment_strategy="auto",
                max_segment_chars=10000,
                silence_between_ms=300,
            )
        assert "SEGMENT_CHARS_OUT_OF_RANGE" in exc_info.value.detail

    def test_validate_batch_need_subtitle_but_tts_not_supported(self):
        cap = make_provider_cap(
            tts=make_tts_cap(supports_subtitle=False),
            batch=make_batch_cap(),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_batch(
                provider="test",
                text="hello",
                audio_format="mp3",
                need_subtitle=True,
                segment_strategy="auto",
                max_segment_chars=2000,
                silence_between_ms=300,
            )
        assert "SUBTITLE_NOT_SUPPORTED" in exc_info.value.detail


class TestValidateScript:
    def _make_validator(self, cap):
        v = CapabilityValidator()
        v.get_capability = lambda p: cap
        return v

    def test_validate_script_passes_with_valid_params(self):
        cap = make_provider_cap(
            tts=make_tts_cap(audio_formats=["mp3"]),
            script=BatchCapability(
                supported=True,
                max_segments=200,
                segment_strategies=["line"],
                silence_between_ms=NumericRange(min=0, max=3000),
                supports_merge_subtitle=True,
            ),
        )
        v = self._make_validator(cap)
        v.validate_script(
            provider="test",
            script_count=5,
            audio_format="mp3",
            need_subtitle=False,
            silence_between_ms=500,
        )

    def test_validate_script_count_exceeded(self):
        cap = make_provider_cap(
            script=BatchCapability(
                supported=True,
                max_segments=10,
                segment_strategies=["line"],
                silence_between_ms=NumericRange(min=0, max=3000),
            ),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_script(
                provider="test",
                script_count=100,
                audio_format="mp3",
                need_subtitle=False,
                silence_between_ms=500,
            )
        assert "SCRIPT_COUNT_EXCEEDED" in exc_info.value.detail

    def test_validate_script_not_supported(self):
        cap = make_provider_cap(
            script=BatchCapability(supported=False),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_script(
                provider="test",
                script_count=5,
                audio_format="mp3",
                need_subtitle=False,
                silence_between_ms=500,
            )
        assert "SCRIPT_NOT_SUPPORTED" in exc_info.value.detail


class TestValidateVoiceClone:
    def _make_validator(self, cap):
        v = CapabilityValidator()
        v.get_capability = lambda p: cap
        return v

    def test_validate_voice_clone_passes_with_valid_params(self):
        cap = make_provider_cap(
            voice_clone=VoiceCloneCapability(
                supported=True,
                preview_text_max=1000,
                voice_id=VoiceIdConstraint(
                    min_length=8,
                    max_length=256,
                    pattern=VOICE_ID_PATTERN,
                ),
                supports_noise_reduction=True,
                supports_volume_normalization=True,
            ),
        )
        v = self._make_validator(cap)
        v.validate_voice_clone(
            provider="test",
            voice_id="my_voice_01",
            preview_text="hello",
            need_noise_reduction=True,
            need_volume_normalization=True,
        )

    def test_validate_voice_clone_not_supported(self):
        cap = make_provider_cap(
            voice_clone=VoiceCloneCapability(supported=False),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_voice_clone(provider="test", voice_id="my_voice_01")
        assert "VOICE_CLONE_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_voice_clone_need_noise_reduction_not_supported(self):
        cap = make_provider_cap(
            voice_clone=VoiceCloneCapability(
                supported=True,
                supports_noise_reduction=False,
            ),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_voice_clone(provider="test", voice_id="my_voice_01", need_noise_reduction=True)
        assert "NOISE_REDUCTION_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_voice_clone_invalid_voice_id_pattern(self):
        cap = make_provider_cap(
            voice_clone=VoiceCloneCapability(
                supported=True,
                voice_id=VoiceIdConstraint(
                    min_length=8,
                    max_length=256,
                    pattern=VOICE_ID_PATTERN,
                ),
            ),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_voice_clone(provider="test", voice_id="invalid!")
        assert "INVALID_VOICE_ID" in exc_info.value.detail


class TestValidateVoiceDesign:
    def _make_validator(self, cap):
        v = CapabilityValidator()
        v.get_capability = lambda p: cap
        return v

    def test_validate_voice_design_passes_with_valid_params(self):
        cap = make_provider_cap(
            voice_design=VoiceDesignCapability(
                supported=True,
                prompt_max=2000,
                preview_text_max=500,
                voice_id=VoiceIdConstraint(
                    min_length=8,
                    max_length=256,
                    pattern=VOICE_ID_PATTERN,
                ),
            ),
        )
        v = self._make_validator(cap)
        v.validate_voice_design(
            provider="test",
            prompt="成熟女性，温柔知性",
            preview_text="你好，这是试听文本。",
            voice_id="my_design_01",
        )

    def test_validate_voice_design_not_supported(self):
        cap = make_provider_cap(
            voice_design=VoiceDesignCapability(supported=False),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_voice_design(
                provider="test",
                prompt="成熟女性",
                preview_text="你好。",
            )
        assert "VOICE_DESIGN_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_voice_design_prompt_too_long(self):
        cap = make_provider_cap(
            voice_design=VoiceDesignCapability(
                supported=True,
                prompt_max=10,
            ),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_voice_design(
                provider="test",
                prompt="a" * 100,
                preview_text="你好。",
            )
        assert "PROMPT_TOO_LONG" in exc_info.value.detail


class TestValidateProviderVoiceImport:
    def _make_validator(self, cap):
        v = CapabilityValidator()
        v.get_capability = lambda p: cap
        return v

    def test_validate_provider_voice_import_passes(self):
        cap = make_provider_cap(
            provider_voices=ProviderVoiceCapability(
                supported=True,
                supports_import_remote_voice=True,
                preview_text_max=1000,
            ),
            tts=TTSCapability(
                supported=True,
                models=["model-a"],
                audio_formats=["mp3"],
            ),
        )
        v = self._make_validator(cap)
        v.validate_provider_voice_import(
            provider="test",
            preview_text="hello",
            verify=True,
            model="model-a",
        )

    def test_validate_provider_voice_import_not_supported(self):
        cap = make_provider_cap(
            provider_voices=ProviderVoiceCapability(supported=False),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_provider_voice_import(provider="test", preview_text="hello")
        assert "PROVIDER_VOICES_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_provider_voice_import_import_not_supported(self):
        cap = make_provider_cap(
            provider_voices=ProviderVoiceCapability(
                supported=True,
                supports_import_remote_voice=False,
            ),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_provider_voice_import(provider="test", preview_text="hello")
        assert "IMPORT_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_provider_voice_import_verify_requires_tts(self):
        cap = make_provider_cap(
            provider_voices=ProviderVoiceCapability(
                supported=True,
                supports_import_remote_voice=True,
                preview_text_max=1000,
            ),
            tts=None,
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_provider_voice_import(provider="test", preview_text="hello", verify=True)
        assert "IMPORT_VERIFY_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_provider_voice_import_verify_tts_not_supported(self):
        cap = make_provider_cap(
            provider_voices=ProviderVoiceCapability(
                supported=True,
                supports_import_remote_voice=True,
                preview_text_max=1000,
            ),
            tts=TTSCapability(supported=False),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_provider_voice_import(provider="test", preview_text="hello", verify=True)
        assert "IMPORT_VERIFY_NOT_SUPPORTED" in exc_info.value.detail

    def test_validate_provider_voice_import_verify_invalid_model(self):
        cap = make_provider_cap(
            provider_voices=ProviderVoiceCapability(
                supported=True,
                supports_import_remote_voice=True,
                preview_text_max=1000,
            ),
            tts=TTSCapability(
                supported=True,
                models=["model-a"],
                audio_formats=["mp3"],
            ),
        )
        v = self._make_validator(cap)
        with pytest.raises(ValidationError) as exc_info:
            v.validate_provider_voice_import(provider="test", preview_text="hello", verify=True, model="model-b")
        assert "UNSUPPORTED_MODEL" in exc_info.value.detail

    def test_validate_provider_voice_import_verify_false_allows_no_tts(self):
        cap = make_provider_cap(
            provider_voices=ProviderVoiceCapability(
                supported=True,
                supports_import_remote_voice=True,
                preview_text_max=1000,
            ),
            tts=None,
        )
        v = self._make_validator(cap)
        v.validate_provider_voice_import(provider="test", preview_text="hello", verify=False)
