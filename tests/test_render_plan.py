import pytest

from app.domain.render_plan import RenderPlan, SubtitlePlan


def test_render_plan_creation():
    plan = RenderPlan(
        id="plan_test",
        text="测试文本",
        processed_text="测试文本<#0.5#>",
        profile_id="deep_night_programmer",
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="English_expressive_narrator",
        voice_params={"speed": 0.88, "emotion": "sad"},
        audio_params={"format": "mp3", "sample_rate": 32000},
        subtitle=SubtitlePlan(enabled=True, type="sentence"),
        output_format="hex",
        language_boost="auto",
    )
    assert plan.id == "plan_test"
    assert plan.provider == "mock"
    assert plan.subtitle.enabled is True


def test_subtitle_plan_defaults():
    plan = SubtitlePlan()
    assert plan.enabled is True
    assert plan.type == "sentence"


def test_voice_params_filters_unknown_keys():
    plan = RenderPlan(
        id="plan_filter",
        text="t",
        processed_text="t",
        profile_id="p",
        provider="mock",
        model="m",
        provider_voice_id="v",
        voice_params={"speed": 0.88, "emotion": "sad", "api_key": "LEAK", "unknown": 42},
    )
    assert "speed" in plan.voice_params
    assert "emotion" in plan.voice_params
    assert "api_key" not in plan.voice_params
    assert "unknown" not in plan.voice_params
