from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncGenerator

from pydantic import BaseModel, Field

from app.domain.render_plan import RenderPlan
from app.domain.schemas import ProviderVoiceRead

if TYPE_CHECKING:
    from app.domain.adapter_config import AdapterConfig
    from app.domain.provider_config import ProviderConfig


class StreamAudioChunk(BaseModel):
    """Single audio chunk from streaming T2A."""
    chunk_index: int
    audio_data: bytes
    duration_ms: int | None = None
    audio_size: int | None = None
    is_final: bool = False
    usage_characters: int | None = None
    trace_id: str | None = None
    metadata: dict = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


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


class AsyncTaskResult(BaseModel):
    """Result returned immediately after creating an async T2A task."""
    task_id: str
    provider_task_id: str
    status: str = "processing"
    trace_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class AsyncTaskStatus(BaseModel):
    """Status result from polling an async T2A task."""
    task_id: str
    status: str
    file_url: str | None = None
    duration_ms: int | None = None
    usage_characters: int | None = None
    trace_id: str | None = None
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict)


class SpeechProvider(ABC):
    provider_name: str

    def __init__(
        self,
        provider_config: ProviderConfig | None = None,
        adapter_config: AdapterConfig | None = None,
    ) -> None:
        self._provider_config = provider_config
        self._adapter_config = adapter_config
        if provider_config:
            self.provider_name = provider_config.name

    @abstractmethod
    async def render_sync(self, plan: RenderPlan) -> ProviderRenderResult:
        raise NotImplementedError

    async def list_voices(self, voice_type: str = "all") -> list[ProviderVoiceRead]:
        raise NotImplementedError

    async def delete_voice(self, provider_voice_id: str, voice_type: str = "voice_cloning") -> dict:
        raise NotImplementedError

    async def design_voice(self, prompt: str, preview_text: str, voice_id: str | None = None) -> dict:
        raise NotImplementedError

    async def create_async_task(self, plan: RenderPlan) -> AsyncTaskResult:
        raise NotImplementedError

    async def query_async_task(self, provider_task_id: str) -> AsyncTaskStatus:
        raise NotImplementedError

    async def upload_voice_file(self, file_data: bytes, filename: str, purpose: str) -> dict:
        raise NotImplementedError

    async def clone_voice(self, request: dict) -> dict:
        raise NotImplementedError

    async def render_stream(
        self, plan: RenderPlan
    ) -> AsyncGenerator[StreamAudioChunk, None]:
        """Stream audio chunks from T2A provider."""
        raise NotImplementedError
        yield  # make it a valid async generator
