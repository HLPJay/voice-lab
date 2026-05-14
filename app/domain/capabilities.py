from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator


AudioFormat = Literal["mp3", "wav", "flac"]
SegmentStrategy = Literal["auto", "paragraph", "sentence", "line"]

SENSITIVE_METADATA_KEYS = {
    "api_key", "apikey", "secret", "token", "password",
    "minimax_api_key", "openai_api_key",
}


class NumericRange(BaseModel):
    min: float
    max: float

    @model_validator(mode="after")
    def validate_range(self):
        if self.min > self.max:
            raise ValueError("NumericRange.min must be <= max")
        return self


class TextLimit(BaseModel):
    min_length: int = 1
    max_length: int


class VoiceIdConstraint(BaseModel):
    min_length: int = 8
    max_length: int = 256
    pattern: str
    hint: str | None = None

    @model_validator(mode="after")
    def validate_voice_id_constraint(self):
        if self.min_length <= 0:
            raise ValueError("VoiceIdConstraint.min_length must be > 0")
        if self.max_length < self.min_length:
            raise ValueError("VoiceIdConstraint.max_length must be >= min_length")
        try:
            re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(f"VoiceIdConstraint.pattern is invalid regex: {exc}") from exc
        return self


class TTSCapability(BaseModel):
    supported: bool = True
    models: list[str] = Field(default_factory=list)
    default_model: str | None = None
    max_text_chars: int = 10000
    audio_formats: list[AudioFormat] = Field(default_factory=list)
    supports_subtitle: bool = False
    supports_streaming: bool = False
    supports_emotion: bool = False
    speed: NumericRange | None = None
    vol: NumericRange | None = None
    pitch: NumericRange | None = None

    @model_validator(mode="after")
    def validate_tts_capability(self):
        if self.supported:
            if not self.models:
                raise ValueError("TTSCapability.models must not be empty when supported=True")
            if not self.audio_formats:
                raise ValueError("TTSCapability.audio_formats must not be empty when supported=True")
            if self.max_text_chars <= 0:
                raise ValueError("TTSCapability.max_text_chars must be > 0")
        if self.default_model and self.models and self.default_model not in self.models:
            raise ValueError("TTSCapability.default_model must be included in models")
        return self


class BatchCapability(BaseModel):
    supported: bool = True
    max_text_chars: int = 50000
    max_segments: int | None = None
    segment_strategies: list[SegmentStrategy] = Field(default_factory=list)
    max_segment_chars: NumericRange | None = None
    silence_between_ms: NumericRange | None = None
    supports_merge_audio: bool = True
    supports_merge_subtitle: bool = True

    @model_validator(mode="after")
    def validate_batch_capability(self):
        if self.supported:
            if self.max_text_chars <= 0:
                raise ValueError("BatchCapability.max_text_chars must be > 0")
            if self.max_segments is not None and self.max_segments <= 0:
                raise ValueError("BatchCapability.max_segments must be > 0")
            if not self.segment_strategies:
                raise ValueError("BatchCapability.segment_strategies must not be empty when supported=True")
        return self


class VoiceCloneCapability(BaseModel):
    supported: bool = False
    preview_text_max: int | None = None
    voice_id: VoiceIdConstraint | None = None
    supports_noise_reduction: bool = False
    supports_volume_normalization: bool = False
    max_file_size_mb: int | None = None


class VoiceDesignCapability(BaseModel):
    supported: bool = False
    prompt_max: int | None = None
    preview_text_max: int | None = None
    voice_id: VoiceIdConstraint | None = None


class ProviderVoiceCapability(BaseModel):
    supported: bool = True
    supports_list_voices: bool = True
    supports_delete_voice: bool = True
    supports_import_remote_voice: bool = True
    preview_text_max: int | None = 1000


class ProviderCapability(BaseModel):
    provider: str
    display_name: str
    enabled: bool = True
    default_model: str | None = None
    tts: TTSCapability | None = None
    batch: BatchCapability | None = None
    script: BatchCapability | None = None
    voice_clone: VoiceCloneCapability | None = None
    voice_design: VoiceDesignCapability | None = None
    provider_voices: ProviderVoiceCapability | None = None
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provider_capability(self):
        if not self.provider:
            raise ValueError("ProviderCapability.provider must not be empty")
        if not self.display_name:
            raise ValueError("ProviderCapability.display_name must not be empty")
        if self.default_model and self.tts and self.tts.models:
            if self.default_model not in self.tts.models:
                raise ValueError("ProviderCapability.default_model must be included in tts.models")
        for key, value in self.metadata.items():
            lower_key = str(key).lower()
            if lower_key in SENSITIVE_METADATA_KEYS:
                raise ValueError(f"ProviderCapability.metadata must not contain sensitive key: {key}")
            if isinstance(value, str) and "sk-" in value:
                raise ValueError(f"ProviderCapability.metadata value must not contain secret patterns: {key}")
        return self
