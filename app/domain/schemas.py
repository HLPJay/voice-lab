from pydantic import BaseModel, Field


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
    output_format: str = "hex"


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
