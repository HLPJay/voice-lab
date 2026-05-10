from app.providers.base import ProviderRenderResult, SpeechProvider
from app.domain.render_plan import RenderPlan
from app.utils.audio import estimate_duration_ms, write_silent_wav
from app.utils.files import storage_path
from app.utils.id_generator import new_id


class MockSpeechAdapter(SpeechProvider):
    provider_name = "mock"

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
