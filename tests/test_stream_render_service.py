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


class TestStreamRenderResourceGuard:
    """Tests for Resource Guard integration in StreamRenderService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_stream_rejected_when_slot_full_no_started(self, session, seed_mock_binding):
        """When t2a_stream limit=1 is held, render_stream should yield error event, not started."""
        from unittest.mock import patch
        from app.services.stream_render_service import StreamRenderService
        from app.services.resource_guard_service import get_resource_guard
        from app.domain.schemas import StreamRenderRequest

        adapter_called = False

        class CheckedStreamAdapter:
            provider_name = "minimax"

            async def render_stream(self, plan):
                nonlocal adapter_called
                adapter_called = True
                # Never yield - should not be reached
                return
                yield  # make it async generator

        svc = StreamRenderService()

        # Hold the t2a_stream slot (limit=1)
        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="t2a_stream", job_id=None)

        with patch("app.services.stream_render_service.get_provider", return_value=CheckedStreamAdapter()):
            with patch("app.services.stream_render_service.validate_binding_provider_voice"):
                req = StreamRenderRequest(
                    text="流式测试",
                    profile_id="deep_night_programmer",
                    provider="minimax",
                    output_format="mp3",
                    confirm_cost=True,
                )
                gen = svc.render_stream(session, req)
                events = []
                async for event in gen:
                    events.append(event)
                    if len(events) >= 3:
                        break

        # First event must be error, not started
        assert len(events) >= 1, "Should yield at least one event"
        assert events[0]["event"] == "error", "First event should be error, not started"
        assert events[0]["code"] == "RESOURCE_LIMIT_EXCEEDED"
        assert adapter_called is False, "render_stream should not be called when guard rejects"

        # Cleanup
        await guard._release(lease)

    @pytest.mark.asyncio
    async def test_stream_success_path_regression(self, session, seed_mock_binding):
        """Normal stream rendering still works correctly (regression test)."""
        from app.services.stream_render_service import StreamRenderService
        from app.domain.schemas import StreamRenderRequest

        svc = StreamRenderService()
        req = StreamRenderRequest(
            text="流式回归测试",
            profile_id="deep_night_programmer",
            provider="mock",
            output_format="mp3",
            confirm_cost=True,
        )
        events = []
        async for event in svc.render_stream(session, req):
            events.append(event)

        started = [e for e in events if e["event"] == "started"]
        chunks = [e for e in events if e["event"] == "audio_chunk"]
        completed = [e for e in events if e["event"] == "completed"]
        errors = [e for e in events if e["event"] == "error"]

        assert len(started) == 1, "Should yield started event"
        assert len(chunks) >= 1, "Should yield at least one audio chunk"
        assert len(completed) == 1, "Should yield completed event"
        assert len(errors) == 0, "Should not yield error event"

    @pytest.mark.asyncio
    async def test_stream_generator_close_releases_guard(self, session, seed_mock_binding):
        """When generator is closed early, Resource Guard lease is released."""
        from unittest.mock import patch
        from app.services.stream_render_service import StreamRenderService
        from app.services.resource_guard_service import get_resource_guard
        from app.domain.schemas import StreamRenderRequest

        import asyncio

        class SlowStreamAdapter:
            provider_name = "minimax"

            async def render_stream(self, plan):
                # Yield one chunk then hang forever
                from app.providers.base import ProviderStreamChunk
                yield ProviderStreamChunk(
                    audio_data=b"fake_audio_data",
                    chunk_index=0,
                    duration_ms=100,
                    usage_characters=10,
                    is_final=False,
                )
                await asyncio.sleep(10)  # Simulate long stream
                yield ProviderStreamChunk(
                    audio_data=b"",
                    chunk_index=1,
                    duration_ms=0,
                    usage_characters=0,
                    is_final=True,
                )

        svc = StreamRenderService()

        # Do NOT hold the slot - let render_stream acquire it
        guard = get_resource_guard()
        assert guard.current("minimax", "t2a_stream") == 0, "Slot should be free before test"

        with patch("app.services.stream_render_service.get_provider", return_value=SlowStreamAdapter()):
            with patch("app.services.stream_render_service.validate_binding_provider_voice"):
                req = StreamRenderRequest(
                    text="长时间流式",
                    profile_id="deep_night_programmer",
                    provider="minimax",
                    output_format="mp3",
                    confirm_cost=True,
                )
                gen = svc.render_stream(session, req)
                agen = gen.__aiter__()

                # Read first event (started)
                first_event = await agen.__anext__()
                assert first_event["event"] == "started"

                # Guard slot should be held (current=1)
                assert guard.current("minimax", "t2a_stream") == 1

                # Close the generator (WebSocket disconnects)
                await agen.aclose()

                # Guard slot should be released (current=0)
                assert guard.current("minimax", "t2a_stream") == 0
