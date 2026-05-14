from typing import Literal

from pydantic import BaseModel, Field


AudioFormat = Literal["mp3", "wav", "flac"]
SegmentStrategy = Literal["auto", "paragraph", "sentence", "line"]


class NumericRange(BaseModel):
    min: float
    max: float


class TextLimit(BaseModel):
    min_length: int = 1
    max_length: int


class VoiceIdConstraint(BaseModel):
    min_length: int = 8
    max_length: int = 256
    pattern: str
    hint: str | None = None


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


class BatchCapability(BaseModel):
    supported: bool = True
    max_text_chars: int = 50000
    max_segments: int | None = None
    segment_strategies: list[SegmentStrategy] = Field(default_factory=list)
    max_segment_chars: NumericRange | None = None
    silence_between_ms: NumericRange | None = None
    supports_merge_audio: bool = True
    supports_merge_subtitle: bool = True


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
