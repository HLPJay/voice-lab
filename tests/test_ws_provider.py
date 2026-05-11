import pytest

from app.providers.base import StreamAudioChunk


def test_stream_audio_chunk_model():
    """StreamAudioChunk 可正常构造."""
    chunk = StreamAudioChunk(
        chunk_index=0,
        audio_data=b"fake_audio",
        duration_ms=500,
        is_final=False,
    )
    assert chunk.chunk_index == 0
    assert chunk.audio_data == b"fake_audio"
    assert chunk.is_final is False


@pytest.mark.asyncio
async def test_mock_render_stream():
    """Mock adapter render_stream 返回多个 chunk."""
    from app.domain.render_plan import RenderPlan, SubtitlePlan
    from app.providers.mock_speech_adapter import MockSpeechAdapter

    adapter = MockSpeechAdapter()
    plan = RenderPlan(
        id="plan_test",
        text="流式测试",
        processed_text="流式测试",
        profile_id="test",
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice",
        voice_params={},
        audio_params={"format": "wav", "sample_rate": 32000, "bitrate": 128000, "channel": 1},
        subtitle=SubtitlePlan(enabled=False, type="sentence"),
    )

    chunks = []
    async for chunk in adapter.render_stream(plan):
        chunks.append(chunk)

    assert len(chunks) == 3
    assert all(isinstance(c, StreamAudioChunk) for c in chunks)
    assert chunks[-1].is_final is True
    assert all(len(c.audio_data) > 0 for c in chunks)


@pytest.mark.asyncio
async def test_mock_stream_chunk_indices():
    """Chunk index 从 0 递增."""
    from app.domain.render_plan import RenderPlan, SubtitlePlan
    from app.providers.mock_speech_adapter import MockSpeechAdapter

    adapter = MockSpeechAdapter()
    plan = RenderPlan(
        id="plan_test",
        text="流式测试",
        processed_text="流式测试",
        profile_id="test",
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice",
        voice_params={},
        audio_params={"format": "wav", "sample_rate": 32000, "bitrate": 128000, "channel": 1},
        subtitle=SubtitlePlan(enabled=False, type="sentence"),
    )

    chunks = []
    async for chunk in adapter.render_stream(plan):
        chunks.append(chunk)

    indices = [c.chunk_index for c in chunks]
    assert indices == [0, 1, 2]


@pytest.mark.asyncio
async def test_mock_stream_trace_id():
    """Mock 流式返回 trace_id."""
    from app.domain.render_plan import RenderPlan, SubtitlePlan
    from app.providers.mock_speech_adapter import MockSpeechAdapter

    adapter = MockSpeechAdapter()
    plan = RenderPlan(
        id="plan_test",
        text="流式测试",
        processed_text="流式测试",
        profile_id="test",
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice",
        voice_params={},
        audio_params={"format": "wav", "sample_rate": 32000, "bitrate": 128000, "channel": 1},
        subtitle=SubtitlePlan(enabled=False, type="sentence"),
    )

    chunks = []
    async for chunk in adapter.render_stream(plan):
        chunks.append(chunk)

    assert all(c.trace_id == "mock_stream_trace" for c in chunks)


def test_minimax_ws_config():
    """WebSocket 配置项存在且有默认值."""
    from app.core.config import get_settings

    settings = get_settings()
    assert settings.minimax_ws_url.startswith("wss://")
    assert settings.minimax_ws_model
    assert settings.minimax_ws_timeout_seconds > 0
