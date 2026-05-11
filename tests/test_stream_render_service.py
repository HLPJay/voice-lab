import base64

import pytest
from pydantic import ValidationError

from app.domain.schemas import StreamRenderRequest
from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob
from app.services.stream_render_service import StreamRenderService


@pytest.fixture
def service():
    return StreamRenderService()


@pytest.fixture
def stream_request():
    return StreamRenderRequest(
        text="流式测试文本",
        profile_id="deep_night_programmer",
        provider="mock",
        output_format="mp3",
    )


@pytest.mark.asyncio
async def test_stream_yields_started_event(service, stream_request, session, seed_mock_binding):
    """流式渲染 yield started 事件."""
    events = []
    async for event in service.render_stream(session, stream_request):
        events.append(event)
        if event["event"] == "started":
            break

    assert len(events) >= 1
    assert events[0]["event"] == "started"
    assert "job_id" in events[0]
    assert "provider" in events[0]
    assert "model" in events[0]


@pytest.mark.asyncio
async def test_stream_yields_audio_chunks(service, stream_request, session, seed_mock_binding):
    """流式渲染 yield audio_chunk 事件."""
    events = []
    async for event in service.render_stream(session, stream_request):
        events.append(event)

    chunks = [e for e in events if e["event"] == "audio_chunk"]
    assert len(chunks) >= 1
    for chunk in chunks:
        assert "chunk_index" in chunk
        assert "audio_base64" in chunk
        assert chunk["audio_base64"]
        decoded = base64.b64decode(chunk["audio_base64"])
        assert isinstance(decoded, bytes)
        assert "is_final" in chunk


@pytest.mark.asyncio
async def test_stream_yields_completed_event(service, stream_request, session, seed_mock_binding):
    """流式渲染完成 yield completed 事件."""
    events = []
    async for event in service.render_stream(session, stream_request):
        events.append(event)

    completed = [e for e in events if e["event"] == "completed"]
    assert len(completed) == 1
    assert completed[0]["event"] == "completed"
    assert "job_id" in completed[0]
    assert completed[0]["total_chunks"] > 0
    assert "audio_asset" in completed[0]
    assert "id" in completed[0]["audio_asset"]
    assert "url" in completed[0]["audio_asset"]


@pytest.mark.asyncio
async def test_stream_creates_job_and_asset(service, stream_request, session, seed_mock_binding):
    """渲染完成后数据库中有 VoiceJob 和 AudioAsset."""
    async for _ in service.render_stream(session, stream_request):
        pass

    from sqlmodel import select
    job = session.exec(select(VoiceJob).where(VoiceJob.job_type == "stream_render")).first()
    assert job is not None
    assert job.status == "success"

    audio = session.exec(select(AudioAsset).where(AudioAsset.job_id == job.id)).first()
    assert audio is not None
    from pathlib import Path
    assert Path(audio.file_path).exists()
    assert Path(audio.file_path).stat().st_size > 0


@pytest.mark.asyncio
async def test_stream_invalid_profile_raises(service, session, seed_mock_binding):
    """不存在的 profile 抛出 ProfileNotFound."""
    request = StreamRenderRequest(
        text="test",
        profile_id="nonexistent_profile",
        provider="mock",
    )
    gen = service.render_stream(session, request)
    with pytest.raises(Exception):
        async for event in gen:
            if event["event"] == "error":
                break


def test_stream_empty_text_rejected():
    """空文本被 Pydantic 校验拒绝."""
    with pytest.raises(ValidationError):
        StreamRenderRequest(text="", profile_id="deep_night_programmer")
