from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import BindingStatus, ProviderVoiceStatus


class VoiceProfileCreate(BaseModel):
    id: str
    name: str
    description: str | None = None
    gender_style: str | None = None
    age_style: str | None = None
    tone_style: str | None = None
    emotion_style: str | None = None
    speed_style: str | None = None
    pause_style: str | None = None
    scene_tags: list[str] = Field(default_factory=list)


class VoiceProfileRead(VoiceProfileCreate):
    is_active: bool = True


class VoiceRenderRequest(BaseModel):
    text: str = Field(min_length=1)
    profile_id: str = "deep_night_programmer"
    provider: str | None = None
    need_subtitle: bool = True
    output_format: Literal["hex", "url"] = "hex"
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"
    speed: float | None = Field(None, ge=0.5, le=2.0)
    vol: float | None = Field(None, ge=0.1, le=10.0)
    pitch: int | None = Field(None, ge=-12, le=12)
    emotion: str | None = None


class AudioAssetResponse(BaseModel):
    id: str
    url: str | None = None
    duration_ms: int | None = None
    format: str | None = None


class SubtitleAssetResponse(BaseModel):
    id: str
    url: str | None = None
    timeline: list[dict] = Field(default_factory=list)


class VoiceRenderResponse(BaseModel):
    job_id: str
    status: str
    audio_asset: AudioAssetResponse | None = None
    subtitle_asset: SubtitleAssetResponse | None = None
    provider: str
    model: str


class VoiceVariantRenderRequest(BaseModel):
    text: str = Field(min_length=1)
    scene: str = "deep_night_monologue"
    profile_id: str = "deep_night_programmer"
    variant_count: int = Field(default=3, ge=1, le=5)
    need_subtitle: bool = True
    provider: str | None = None


class VoiceVariantResponse(BaseModel):
    variant_id: str
    job_id: str
    profile_id: str
    speed: float | None = None
    emotion: str | None = None
    audio_asset_id: str | None = None
    audio_url: str | None = None
    duration_ms: int | None = None


class VoiceVariantGroupResponse(BaseModel):
    group_id: str
    variants: list[VoiceVariantResponse]


class ProviderVoiceRead(BaseModel):
    id: str
    provider: str
    provider_voice_id: str
    voice_type: str
    name: str | None = None
    description: str | None = None
    language: str | None = None
    gender: str | None = None
    status: str = ProviderVoiceStatus.available
    provider_created_time: str | None = None
    metadata: dict = Field(default_factory=dict)
    synced_at: str | None = None


class ProviderVoiceListResponse(BaseModel):
    provider: str
    voice_type: str = "all"
    voices: list[ProviderVoiceRead] = Field(default_factory=list)
    synced_at: str | None = None
    total: int = 0


class VoiceBindingCreate(BaseModel):
    provider: str
    model: str
    provider_voice_id: str
    params: dict = Field(default_factory=dict)
    priority: int = 1


class VoiceBindingUpdate(BaseModel):
    provider_voice_id: str | None = None
    params: dict | None = None
    priority: int | None = None
    status: str | None = None


class VoiceBindingRead(BaseModel):
    id: str
    profile_id: str
    provider: str
    model: str
    provider_voice_id: str
    provider_voice_name: str | None = None
    params: dict = Field(default_factory=dict)
    priority: int = 1
    status: str = BindingStatus.available
    created_at: str
    updated_at: str


class VoiceJobRead(BaseModel):
    job_id: str
    job_type: str
    status: str
    provider: str | None = None
    model: str | None = None
    profile_id: str | None = None
    input_text: str | None = None
    processed_text: str | None = None
    provider_trace_id: str | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class AudioAssetRead(BaseModel):
    asset_id: str
    type: str = "audio"
    file_path: str
    format: str | None = None
    duration_ms: int | None = None
    provider: str | None = None
    model: str | None = None
    usage_characters: int | None = None
    download_url: str | None = None
    created_at: str


class SubtitleAssetRead(BaseModel):
    asset_id: str
    type: str = "subtitle"
    file_path: str | None = None
    srt_path: str | None = None
    subtitle_type: str | None = None
    timeline: list[dict] = Field(default_factory=list)
    created_at: str


class AsyncRenderRequest(BaseModel):
    text: str = Field(min_length=1)
    profile_id: str = "deep_night_programmer"
    provider: str | None = None
    need_subtitle: bool = True
    output_format: Literal["hex", "url"] = "hex"
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"


class AsyncRenderResponse(BaseModel):
    job_id: str
    status: str
    provider: str
    model: str
    message: str = "任务已提交"


class AsyncJobStatusResponse(BaseModel):
    job_id: str
    status: str
    provider: str | None = None
    model: str | None = None
    audio_asset: AudioAssetResponse | None = None
    subtitle_asset: SubtitleAssetResponse | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class VoiceCloneUploadResponse(BaseModel):
    file_id: int
    filename: str
    purpose: str
    bytes: int | None = None
    created_at: str | None = None


class VoiceCloneRequest(BaseModel):
    voice_id: str = Field(min_length=8, max_length=256, pattern=r"^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$")
    file_id: int
    prompt_file_id: int | None = None
    prompt_text: str | None = None
    preview_text: str | None = Field(default=None, max_length=1000)
    model: str | None = None
    language_boost: str | None = None
    need_noise_reduction: bool = False
    need_volume_normalization: bool = False
    input_sensitive: bool = False

    @model_validator(mode="after")
    def check_clone_request_consistency(self):
        if self.preview_text and not self.model:
            raise ValueError("preview_text requires model to be set (official requirement: when text is provided, model is mandatory)")
        if (self.prompt_file_id is None) ^ (self.prompt_text is None):
            raise ValueError("prompt_file_id and prompt_text must be provided together")
        return self


class VoiceCloneResponse(BaseModel):
    voice_id: str
    demo_audio_url: str | None = None
    duration_ms: int | None = None
    usage_characters: int | None = None
    message: str = "克隆成功"


class VoiceDesignRequest(BaseModel):
    prompt: str = Field(min_length=1, description="音色描述，如'成熟女性，温柔知性'")
    preview_text: str = Field(min_length=1, max_length=500, description="试听文本")
    voice_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=256,
        pattern=r"^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$",
    )


class VoiceDesignResponse(BaseModel):
    voice_id: str
    trial_audio_url: str | None = None
    trial_audio_hex: str | None = None
    message: str = "设计成功"


class VoiceDeleteRequest(BaseModel):
    provider_voice_id: str = Field(min_length=1)
    voice_type: str = Field(default="voice_cloning", pattern=r"^(voice_cloning|voice_generation)$")


class VoiceDeleteResponse(BaseModel):
    voice_id: str
    deleted: bool = True
    message: str = "删除成功"


class StreamRenderRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    profile_id: str = "deep_night_programmer"
    provider: str | None = None
    audio_format: Literal["mp3"] = "mp3"
    need_subtitle: bool = False
    speed: float | None = Field(None, ge=0.5, le=2.0)
    vol: float | None = Field(None, ge=0.1, le=10.0)
    pitch: int | None = Field(None, ge=-12, le=12)
    emotion: str | None = None


# ─── Batch Job Schemas ───────────────────────────────────────────────────────


class LongtextBatchRequest(BaseModel):
    mode: Literal["longtext"] = "longtext"
    text: str = Field(min_length=1)
    profile_id: str = "deep_night_programmer"
    provider: str | None = None
    output_format: Literal["hex", "url"] = "hex"
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"
    segment_strategy: str = "auto"  # auto/paragraph/sentence
    max_segment_chars: int = Field(default=2000, ge=100, le=5000)
    silence_between_ms: int = Field(default=300, ge=0, le=3000)
    params: dict = Field(default_factory=dict)
    need_subtitle: bool = True


class ScriptLine(BaseModel):
    role: str
    text: str = Field(min_length=1)
    profile_id: str
    params: dict = Field(default_factory=dict)


class ScriptBatchRequest(BaseModel):
    mode: Literal["script"] = "script"
    script: list[ScriptLine] = Field(min_length=1, max_length=200)
    provider: str | None = None
    output_format: Literal["hex", "url"] = "hex"
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"
    silence_between_ms: int = Field(default=500, ge=0, le=3000)
    need_subtitle: bool = True


class BatchSubmitResponse(BaseModel):
    batch_id: str
    mode: str
    total_segments: int
    status: str
    message: str = "批量任务已提交"


class BatchSegmentStatus(BaseModel):
    index: int
    role: str | None = None
    text_preview: str  # 前30字
    status: str
    duration_ms: int | None = None
    audio_asset_id: str | None = None
    error_message: str | None = None


class BatchStatusResponse(BaseModel):
    batch_id: str
    mode: str
    status: str
    total_segments: int
    completed_segments: int
    failed_segments: int
    segments: list[BatchSegmentStatus]
    merged_audio: dict | None = None  # {"id": "audio_xxx", "url": "/api/voice/assets/xxx/download"}
    merged_subtitle: dict | None = None
    total_duration_ms: int | None = None
    created_at: str
    updated_at: str
