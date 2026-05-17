"""
P17-XIANGTA-PRODUCT-CONFIG-B1-4 - TtsOrchestrator unit tests.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.xiangta.config.product_config_models import ProductVoiceMapping, TonePreset
from src.xiangta.services.error_translator import (
    InvalidInputError,
    PresetNotFoundError,
    TextTooLongError,
)
from src.xiangta.services.tone_preset_service import TonePresetDisabled, TonePresetNotFound
from src.xiangta.services.tts_orchestrator import TtsOrchestrator
from src.xiangta.services.voice_preset_mapping_service import (
    VoicePresetDisabled,
    VoicePresetNotFound,
)

FORBIDDEN_KEYS = {
    "voice_id",
    "model_id",
    "sample_rate",
    "bitrate",
    "api_key",
    "minimax_api_key",
    "mimo_api_key",
    "coreBindingKey",
    "core_binding_key",
    "coreProfileId",
    "core_profile_id",
    "profile_id",
    "provider",
    "model",
    "provider_voice_id",
    "binding_id",
    "params_json",
}

MOCK_MAPPING = ProductVoiceMapping(
    id="female-gentle",
    label="温柔女声",
    desc="清亮柔和",
    gender_style="female",
    suitable_recipients=["lover", "friend"],
    recommended_scenes=["miss", "night"],
    default_tone="gentle",
    enabled=True,
    sort_order=10,
    core_profile_id="<core_profile_id_from_core_profiles>",
    provider_policy="default",
    render_overrides={},
    notes=None,
)

MOCK_TONE = TonePreset(
    id="gentle",
    label="温柔",
    desc="柔和表达",
    style_hint="soft",
    render_overrides={},
    enabled=True,
    sort_order=0,
)

MOCK_GATEWAY_RESULT = {
    "taskId": "dryrun_abc12345",
    "status": "dry_run",
    "audioUrl": None,
    "durationMs": None,
    "message": "dry-run only, no provider call",
    "contract": {
        "voicePresetId": "female-gentle",
        "tone": "gentle",
        "toneHint": "soft",
        "scene": "miss",
        "mode": "dry_run",
    },
}


@pytest.fixture
def mock_voice_mapping_service():
    svc = MagicMock()
    svc.resolve.return_value = MOCK_MAPPING
    return svc


@pytest.fixture
def mock_tone_preset_service():
    svc = MagicMock()
    svc.resolve.return_value = MOCK_TONE
    return svc


@pytest.fixture
def mock_gateway():
    gateway = MagicMock()
    gateway.generate_tts_dry_run = AsyncMock(return_value=MOCK_GATEWAY_RESULT)
    return gateway


@pytest.fixture
def orchestrator(mock_gateway, mock_voice_mapping_service, mock_tone_preset_service):
    return TtsOrchestrator(
        gateway=mock_gateway,
        voice_mapping_service=mock_voice_mapping_service,
        tone_preset_service=mock_tone_preset_service,
        max_tts_chars=500,
    )


class TestGenerateHappyPath:
    @pytest.mark.asyncio
    async def test_calls_voice_mapping_service_once(self, orchestrator, mock_voice_mapping_service):
        await orchestrator.generate(
            text="想念你",
            voice_preset="female-gentle",
            tone="gentle",
            recipient="lover",
            scene="miss",
        )
        mock_voice_mapping_service.resolve.assert_called_once_with("female-gentle")

    @pytest.mark.asyncio
    async def test_calls_tone_preset_service_once(self, orchestrator, mock_tone_preset_service):
        await orchestrator.generate(
            text="想念你",
            voice_preset="female-gentle",
            tone="gentle",
            recipient="lover",
            scene="miss",
        )
        mock_tone_preset_service.resolve.assert_called_once_with("gentle")

    @pytest.mark.asyncio
    async def test_calls_gateway_dry_run_once(self, orchestrator, mock_gateway):
        await orchestrator.generate(
            text="想念你",
            voice_preset="female-gentle",
            tone="gentle",
            recipient="lover",
            scene="miss",
        )
        mock_gateway.generate_tts_dry_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_gateway_dry_run_receives_core_render_target(self, orchestrator, mock_gateway):
        await orchestrator.generate(
            text="想念你",
            voice_preset="female-gentle",
            tone="gentle",
            recipient="lover",
            scene="miss",
        )
        kwargs = mock_gateway.generate_tts_dry_run.call_args.kwargs
        target = kwargs["target"]
        assert target.profile_id == "<core_profile_id_from_core_profiles>"
        assert kwargs["voice_preset_id"] == "female-gentle"
        assert kwargs["tone_hint"] == "soft"

    @pytest.mark.asyncio
    async def test_returns_safe_product_fields(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你",
            voice_preset="female-gentle",
            tone="gentle",
            recipient="lover",
            scene="miss",
        )
        assert result["taskId"] == "dryrun_abc12345"
        assert result["status"] == "dry_run"
        assert result["charCount"] == len("想念你")
        assert result["voicePreset"] == "female-gentle"
        assert result["tone"] == "gentle"
        assert result["contract"]["voicePresetId"] == "female-gentle"


class TestNoCoreLeaks:
    def _collect_keys(self, obj, seen=None):
        if seen is None:
            seen = set()
        if isinstance(obj, dict):
            for key, value in obj.items():
                seen.add(key)
                self._collect_keys(value, seen)
        elif isinstance(obj, list):
            for item in obj:
                self._collect_keys(item, seen)
        return seen

    @pytest.mark.asyncio
    async def test_result_does_not_expose_core_fields(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你",
            voice_preset="female-gentle",
            tone="gentle",
            recipient="lover",
            scene="miss",
        )
        all_keys = self._collect_keys(result)
        bad = all_keys & FORBIDDEN_KEYS
        assert not bad, f"TtsOrchestrator returned forbidden fields: {bad}"


class TestInputValidationErrors:
    @pytest.mark.asyncio
    async def test_empty_text_raises_invalid_input(self, orchestrator):
        with pytest.raises(InvalidInputError):
            await orchestrator.generate(
                text="",
                voice_preset="female-gentle",
                tone="gentle",
                recipient="lover",
                scene="miss",
            )

    @pytest.mark.asyncio
    async def test_text_over_default_limit_raises_text_too_long(self, orchestrator):
        with pytest.raises(TextTooLongError):
            await orchestrator.generate(
                text="字" * 501,
                voice_preset="female-gentle",
                tone="gentle",
                recipient="lover",
                scene="miss",
            )

    @pytest.mark.asyncio
    async def test_text_over_injected_limit_raises_text_too_long(
        self, mock_gateway, mock_voice_mapping_service, mock_tone_preset_service
    ):
        orch = TtsOrchestrator(
            gateway=mock_gateway,
            voice_mapping_service=mock_voice_mapping_service,
            tone_preset_service=mock_tone_preset_service,
            max_tts_chars=3,
        )
        with pytest.raises(TextTooLongError):
            await orch.generate(
                text="1234",
                voice_preset="female-gentle",
                tone="gentle",
                recipient="lover",
                scene="miss",
            )


class TestPresetErrors:
    @pytest.mark.asyncio
    async def test_unknown_voice_preset_raises_stable_error(self, mock_gateway, mock_tone_preset_service):
        voice_mapping_service = MagicMock()
        voice_mapping_service.resolve.side_effect = VoicePresetNotFound("voice mapping 'x' does not exist")
        orch = TtsOrchestrator(
            gateway=mock_gateway,
            voice_mapping_service=voice_mapping_service,
            tone_preset_service=mock_tone_preset_service,
            max_tts_chars=500,
        )
        with pytest.raises(PresetNotFoundError, match="does not exist"):
            await orch.generate(
                text="想念你",
                voice_preset="x",
                tone="gentle",
                recipient="lover",
                scene="miss",
            )

    @pytest.mark.asyncio
    async def test_disabled_voice_preset_raises_stable_error(self, mock_gateway, mock_tone_preset_service):
        voice_mapping_service = MagicMock()
        voice_mapping_service.resolve.side_effect = VoicePresetDisabled("voicePreset 'x' is disabled")
        orch = TtsOrchestrator(
            gateway=mock_gateway,
            voice_mapping_service=voice_mapping_service,
            tone_preset_service=mock_tone_preset_service,
            max_tts_chars=500,
        )
        with pytest.raises(PresetNotFoundError, match="disabled"):
            await orch.generate(
                text="想念你",
                voice_preset="x",
                tone="gentle",
                recipient="lover",
                scene="miss",
            )

    @pytest.mark.asyncio
    async def test_unknown_tone_raises_stable_error(self, mock_gateway, mock_voice_mapping_service):
        tone_preset_service = MagicMock()
        tone_preset_service.resolve.side_effect = TonePresetNotFound("tone preset 'x' does not exist")
        orch = TtsOrchestrator(
            gateway=mock_gateway,
            voice_mapping_service=mock_voice_mapping_service,
            tone_preset_service=tone_preset_service,
            max_tts_chars=500,
        )
        with pytest.raises(PresetNotFoundError, match="does not exist"):
            await orch.generate(
                text="想念你",
                voice_preset="female-gentle",
                tone="x",
                recipient="lover",
                scene="miss",
            )

    @pytest.mark.asyncio
    async def test_disabled_tone_raises_stable_error(self, mock_gateway, mock_voice_mapping_service):
        tone_preset_service = MagicMock()
        tone_preset_service.resolve.side_effect = TonePresetDisabled("tone 'x' is disabled")
        orch = TtsOrchestrator(
            gateway=mock_gateway,
            voice_mapping_service=mock_voice_mapping_service,
            tone_preset_service=tone_preset_service,
            max_tts_chars=500,
        )
        with pytest.raises(PresetNotFoundError, match="disabled"):
            await orch.generate(
                text="想念你",
                voice_preset="female-gentle",
                tone="x",
                recipient="lover",
                scene="miss",
            )
