from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from src.xiangta.config.product_config_models import ProductVoiceMapping
from src.xiangta.config.product_config_repository import VoiceMappingNotFound
from src.xiangta.services.error_translator import translate
from src.xiangta.services.voice_preset_mapping_service import (
    VoicePresetDisabled,
    VoicePresetMappingService,
    VoicePresetNotFound,
    VoicePresetProfileNotConfigured,
)


@dataclass(frozen=True)
class FakeVoiceMapping:
    id: str = "female-gentle"
    label: str = "温柔女声"
    desc: str = "适合轻声表达"
    gender_style: str | None = "female"
    suitable_recipients: list[str] = field(default_factory=list)
    recommended_scenes: list[str] = field(default_factory=list)
    default_tone: str = "gentle"
    enabled: bool = True
    sort_order: int = 10
    core_profile_id: str | None = "deep_night_programmer"
    provider_policy: str | None = "mock"
    render_overrides: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None


class FakeRepository:
    def __init__(self, mapping=None) -> None:
        self._mapping = mapping

    def get_voice_mapping(self, voice_preset_id: str):
        if self._mapping is None:
            raise VoiceMappingNotFound(f"voice mapping '{voice_preset_id}' 不存在")
        return self._mapping


def _real_mapping(core_profile_id: str = "deep_night_programmer") -> ProductVoiceMapping:
    return ProductVoiceMapping(
        id="female-gentle",
        label="温柔女声",
        desc="适合轻声表达",
        gender_style="female",
        suitable_recipients=["lover"],
        recommended_scenes=["miss"],
        default_tone="gentle",
        enabled=True,
        sort_order=10,
        core_profile_id=core_profile_id,
        provider_policy="mock",
        render_overrides={},
        notes=None,
    )


def _resolve_with(mapping):
    return VoicePresetMappingService(config_repository=FakeRepository(mapping)).resolve("female-gentle")


def test_resolve_valid_mapping_with_real_looking_core_profile_id_returns_mapping():
    mapping = _real_mapping("deep_night_programmer")

    result = _resolve_with(mapping)

    assert result is mapping
    assert result.core_profile_id == "deep_night_programmer"


def test_resolve_unknown_voice_preset_raises_not_found():
    service = VoicePresetMappingService(config_repository=FakeRepository(mapping=None))

    with pytest.raises(VoicePresetNotFound):
        service.resolve("unknown")


def test_resolve_disabled_voice_preset_raises_disabled():
    mapping = FakeVoiceMapping(enabled=False, core_profile_id="deep_night_programmer")

    with pytest.raises(VoicePresetDisabled):
        _resolve_with(mapping)


@pytest.mark.parametrize(
    "core_profile_id",
    [
        None,
        "",
        "   ",
        "<core_profile_id_from_core_profiles>",
        "prefix<placeholder",
        "placeholder>suffix",
        "TODO_bind_profile",
        "todo_bind_profile",
    ],
)
def test_resolve_placeholder_core_profile_id_raises_not_configured(core_profile_id):
    mapping = FakeVoiceMapping(core_profile_id=core_profile_id)

    with pytest.raises(VoicePresetProfileNotConfigured):
        _resolve_with(mapping)


def test_translate_profile_not_configured_returns_product_error_kind():
    exc = VoicePresetProfileNotConfigured("voicePreset 'female-gentle' 尚未配置有效 Core profile")

    result = translate(exc)

    assert result.kind == "voice_preset_not_bound"


def test_translate_profile_not_configured_is_not_retryable():
    exc = VoicePresetProfileNotConfigured("voicePreset 'female-gentle' 尚未配置有效 Core profile")

    result = translate(exc)

    assert result.retryable is False
