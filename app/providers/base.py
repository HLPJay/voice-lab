from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from app.domain.render_plan import RenderPlan


class ProviderRenderResult(BaseModel):
    audio_path: str
    duration_ms: int | None = None
    usage_characters: int | None = None
    trace_id: str | None = None
    response_json: dict = Field(default_factory=dict)
    timeline: list[dict] = Field(default_factory=list)
    subtitle_path: str | None = None
    srt_path: str | None = None
    metadata: dict = Field(default_factory=dict)


class SpeechProvider(ABC):
    provider_name: str

    @abstractmethod
    async def render_sync(self, plan: RenderPlan) -> ProviderRenderResult:
        raise NotImplementedError

    async def list_voices(self, voice_type: str = "all"):
        raise NotImplementedError

    async def delete_voice(self, provider_voice_id: str):
        raise NotImplementedError

    async def design_voice(self, prompt: str, preview_text: str, voice_id: str | None = None):
        raise NotImplementedError

    async def create_async_tts_job(self, plan: RenderPlan):
        raise NotImplementedError
