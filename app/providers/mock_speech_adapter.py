from app.providers.base import AsyncTaskResult, AsyncTaskStatus, ProviderRenderResult, SpeechProvider
from app.domain.render_plan import RenderPlan
from app.domain.schemas import ProviderVoiceRead
from app.utils.audio import estimate_duration_ms, write_silent_wav
from app.utils.files import storage_path
from app.utils.id_generator import new_id


class MockSpeechAdapter(SpeechProvider):
    provider_name = "mock"

    async def list_voices(self, voice_type: str = "all") -> list[ProviderVoiceRead]:
        voices = [
            ProviderVoiceRead(
                id="mock_voice_system",
                provider=self.provider_name,
                provider_voice_id="mock_system_narrator",
                voice_type="system",
                name="Mock System Narrator",
                description="A stable mock narrator voice for tests.",
                language="zh",
                gender="neutral",
                metadata={"mock": True},
            ),
            ProviderVoiceRead(
                id="mock_voice_clone",
                provider=self.provider_name,
                provider_voice_id="mock_clone_soft",
                voice_type="voice_cloning",
                name="Mock Clone Soft",
                description="A mock cloned-style voice for catalog tests.",
                language="zh",
                gender="female",
                metadata={"mock": True},
            ),
            ProviderVoiceRead(
                id="mock_voice_generation",
                provider=self.provider_name,
                provider_voice_id="mock_generated_warm",
                voice_type="voice_generation",
                name="Mock Generated Warm",
                description="A mock generated voice for catalog tests.",
                language="en",
                gender="male",
                metadata={"mock": True},
            ),
        ]
        if voice_type == "all":
            return voices
        return [voice for voice in voices if voice.voice_type == voice_type]

    async def render_sync(self, plan: RenderPlan) -> ProviderRenderResult:
        audio_id = new_id("audio_file")
        audio_path = storage_path("audio", f"{audio_id}.wav")
        duration_ms = estimate_duration_ms(plan.processed_text)
        write_silent_wav(audio_path, duration_ms=min(duration_ms, 2000), sample_rate=plan.audio_params.get("sample_rate", 16000))
        timeline = [{"text": plan.text, "start": 0.0, "end": round(duration_ms / 1000, 2)}] if plan.subtitle.enabled else []
        return ProviderRenderResult(
            audio_path=str(audio_path),
            duration_ms=duration_ms,
            usage_characters=len(plan.text),
            trace_id="mock_trace",
            response_json={"mock": True},
            timeline=timeline,
            metadata={"mock": True, "plan_id": plan.id},
        )

    async def create_async_task(self, plan: RenderPlan) -> AsyncTaskResult:
        task_id = new_id("async_task")
        return AsyncTaskResult(
            task_id=task_id,
            provider_task_id=f"mock_provider_{task_id}",
            status="processing",
            trace_id="mock_async_trace",
        )

    async def query_async_task(self, provider_task_id: str) -> AsyncTaskStatus:
        audio_path = storage_path("audio", f"{new_id('audio_file')}.wav")
        write_silent_wav(audio_path, duration_ms=2000, sample_rate=16000)
        return AsyncTaskStatus(
            task_id=provider_task_id,
            status="success",
            file_url=str(audio_path),
            duration_ms=2000,
            usage_characters=100,
            trace_id="mock_async_trace",
        )

    async def upload_voice_file(self, file_data: bytes, filename: str, purpose: str) -> dict:
        return {
            "file_id": 99999,
            "filename": filename,
            "purpose": purpose,
            "bytes": len(file_data),
            "created_at": 1700000000,
        }

    async def clone_voice(self, request: dict) -> dict:
        return {
            "voice_id": request["voice_id"],
            "demo_audio_url": None,
            "duration_ms": None,
            "usage_characters": None,
            "message": "mock clone success",
        }

    async def design_voice(self, prompt: str, preview_text: str, voice_id: str | None = None) -> dict:
        return {
            "voice_id": voice_id or f"mock_designed_{new_id('voice')}",
            "trial_audio_hex": None,
        }
