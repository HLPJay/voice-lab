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


VOICE_ID_PATTERN = r"^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
VOICE_ID_HINT = "至少 8 位，必须以字母开头，只能包含字母、数字、下划线和短横线，且不能以短横线或下划线结尾。"


MOCK_CAPABILITY = ProviderCapability(
    provider="mock",
    display_name="Mock",
    enabled=True,
    default_model="mock-tts",
    tts=TTSCapability(
        supported=True,
        models=["mock-tts"],
        default_model="mock-tts",
        max_text_chars=10000,
        audio_formats=["mp3", "wav", "flac"],
        supports_subtitle=True,
        supports_streaming=True,
        supports_emotion=True,
        speed=NumericRange(min=0.5, max=2.0),
        vol=NumericRange(min=0.1, max=10.0),
        pitch=NumericRange(min=-12, max=12),
    ),
    batch=BatchCapability(
        supported=True,
        max_text_chars=50000,
        max_segments=200,
        segment_strategies=["auto", "paragraph", "sentence", "line"],
        max_segment_chars=NumericRange(min=100, max=5000),
        silence_between_ms=NumericRange(min=0, max=3000),
        supports_merge_audio=True,
        supports_merge_subtitle=True,
    ),
    script=BatchCapability(
        supported=True,
        max_text_chars=50000,
        max_segments=200,
        segment_strategies=["line"],
        max_segment_chars=NumericRange(min=100, max=5000),
        silence_between_ms=NumericRange(min=0, max=3000),
        supports_merge_audio=True,
        supports_merge_subtitle=True,
    ),
    voice_clone=VoiceCloneCapability(
        supported=True,
        preview_text_max=1000,
        voice_id=VoiceIdConstraint(
            min_length=8,
            max_length=256,
            pattern=VOICE_ID_PATTERN,
            hint=VOICE_ID_HINT,
        ),
        supports_noise_reduction=True,
        supports_volume_normalization=True,
        max_file_size_mb=20,
    ),
    voice_design=VoiceDesignCapability(
        supported=True,
        prompt_max=2000,
        preview_text_max=500,
        voice_id=VoiceIdConstraint(
            min_length=8,
            max_length=256,
            pattern=VOICE_ID_PATTERN,
            hint=VOICE_ID_HINT,
        ),
    ),
    provider_voices=ProviderVoiceCapability(
        supported=True,
        supports_list_voices=True,
        supports_delete_voice=True,
        supports_import_remote_voice=True,
        preview_text_max=1000,
    ),
    metadata={"mode": "mock"},
)
