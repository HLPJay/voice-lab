import asyncio
import struct
from pathlib import Path
from typing import AsyncGenerator

from app.providers.base import AsyncTaskResult, AsyncTaskStatus, ProviderRenderResult, SpeechProvider, StreamAudioChunk
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

    async def delete_voice(self, provider_voice_id: str, voice_type: str = "voice_cloning") -> dict:
        return {"voice_id": provider_voice_id, "deleted": True}

    async def render_stream(self, plan: RenderPlan) -> AsyncGenerator[StreamAudioChunk, None]:
        """Mock streaming: yield 3 small audio chunks from a synthetic WAV."""
        sample_rate = plan.audio_params.get("sample_rate", 32000)
        num_channels = plan.audio_params.get("channel", 1)
        bits_per_sample = 16
        duration_ms = 300
        num_samples = int(sample_rate * duration_ms / 1000)
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = num_samples * block_align

        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", 36 + data_size, b"WAVE",
            b"fmt ", 16, 1, num_channels, sample_rate,
            byte_rate, block_align, bits_per_sample,
            b"data", data_size,
        )
        silence = b"\x00" * data_size
        wav_data = wav_header + silence

        total = len(wav_data)
        chunk_size = total // 3
        for i in range(3):
            start = i * chunk_size
            end = total if i == 2 else (i + 1) * chunk_size
            await asyncio.sleep(0.05)
            yield StreamAudioChunk(
                chunk_index=i,
                audio_data=wav_data[start:end],
                duration_ms=duration_ms,
                audio_size=end - start,
                is_final=(i == 2),
                usage_characters=len(plan.processed_text) if i == 2 else 0,
                trace_id="mock_stream_trace",
            )
