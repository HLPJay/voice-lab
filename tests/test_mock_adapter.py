import pytest

from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.providers.mock_speech_adapter import MockSpeechAdapter


@pytest.mark.asyncio
async def test_mock_adapter_renders():
    adapter = MockSpeechAdapter()
    plan = RenderPlan(
        id="plan_mock_test",
        text="这是一段测试文本。",
        processed_text="这是一段测试文本。<#0.5#>",
        profile_id="deep_night_programmer",
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice",
        voice_params={},
        audio_params={"format": "wav", "sample_rate": 16000},
        subtitle=SubtitlePlan(enabled=True, type="sentence"),
    )
    result = await adapter.render_sync(plan)
    assert result.audio_path
    assert result.duration_ms > 0
    assert result.usage_characters == len("这是一段测试文本。")
    assert result.timeline  # subtitle enabled
