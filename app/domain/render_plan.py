from pydantic import BaseModel, Field


class SubtitlePlan(BaseModel):
    enabled: bool = True
    type: str = "sentence"


class RenderPlan(BaseModel):
    id: str
    text: str
    processed_text: str
    profile_id: str
    provider: str
    model: str
    provider_voice_id: str
    voice_params: dict = Field(default_factory=dict)
    audio_params: dict = Field(default_factory=dict)
    subtitle: SubtitlePlan = Field(default_factory=SubtitlePlan)
    output_format: str = "hex"
    language_boost: str = "auto"
