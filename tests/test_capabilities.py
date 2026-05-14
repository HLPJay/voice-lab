import pytest
from fastapi.testclient import TestClient

from app.core.errors import UnsupportedProvider
from app.domain.capabilities import (
    BatchCapability,
    NumericRange,
    ProviderCapability,
    TTSCapability,
    VoiceIdConstraint,
)
from app.providers.capability_registry import (
    get_capability,
    list_capabilities,
    provider_exists,
)
from app.providers.mock_capabilities import MOCK_CAPABILITY


class TestCapabilityRegistry:
    def test_list_capabilities_contains_mock_and_minimax(self):
        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "mock" in providers
        assert "minimax" in providers

    def test_get_capability_mock(self):
        cap = get_capability("mock")
        assert cap.provider == "mock"
        assert isinstance(cap, ProviderCapability)

    def test_get_capability_minimax(self):
        cap = get_capability("minimax")
        assert cap.provider == "minimax"
        assert isinstance(cap, ProviderCapability)

    def test_get_capability_unknown_raises(self):
        with pytest.raises(UnsupportedProvider) as exc_info:
            get_capability("unknown_provider")
        assert "unknown_provider" in str(exc_info.value)

    def test_provider_exists_mock(self):
        assert provider_exists("mock") is True

    def test_provider_exists_minimax(self):
        assert provider_exists("minimax") is True

    def test_provider_exists_unknown(self):
        assert provider_exists("unknown_provider") is False

    def test_mock_capability_structure(self):
        assert MOCK_CAPABILITY.provider == "mock"
        assert MOCK_CAPABILITY.tts is not None
        assert MOCK_CAPABILITY.batch is not None
        assert MOCK_CAPABILITY.script is not None
        assert MOCK_CAPABILITY.voice_clone is not None
        assert MOCK_CAPABILITY.voice_design is not None

    def test_mock_tts_capability(self):
        tts = MOCK_CAPABILITY.tts
        assert tts.supported is True
        assert "mock-tts" in tts.models
        assert "mp3" in tts.audio_formats
        assert tts.supports_streaming is True

    def test_mock_batch_capability(self):
        batch = MOCK_CAPABILITY.batch
        assert batch.supported is True
        assert "line" in batch.segment_strategies
        assert batch.max_segment_chars is not None
        assert batch.max_segment_chars.min == 100
        assert batch.max_segment_chars.max == 5000

    def test_mock_voice_clone_capability(self):
        vc = MOCK_CAPABILITY.voice_clone
        assert vc.supported is True
        assert vc.voice_id is not None
        assert vc.voice_id.min_length == 8
        assert vc.supports_noise_reduction is True

    def test_mock_voice_design_capability(self):
        vd = MOCK_CAPABILITY.voice_design
        assert vd.supported is True
        assert vd.prompt_max == 2000


class TestCapabilitiesAPI:
    def test_get_all_capabilities(self, test_app):
        client = TestClient(test_app)
        resp = client.get("/api/voice/capabilities")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 2
        providers = body["providers"]
        provider_names = [p["provider"] for p in providers]
        assert "mock" in provider_names
        assert "minimax" in provider_names

    def test_get_minimax_capability(self, test_app):
        client = TestClient(test_app)
        resp = client.get("/api/voice/capabilities?provider=minimax")
        assert resp.status_code == 200
        body = resp.json()
        assert body["provider"] == "minimax"
        assert body["tts"]["supported"] is True
        assert "mp3" in body["tts"]["audio_formats"]
        assert "line" in body["batch"]["segment_strategies"]
        assert body["voice_clone"]["supported"] is True
        assert body["voice_design"]["supported"] is True
        assert "api_key_configured" in body["metadata"]
        assert isinstance(body["metadata"]["api_key_configured"], bool)
        assert "minimax_api_key" not in body["metadata"]
        assert "minimax_api_key" not in str(body)

    def test_get_mock_capability(self, test_app):
        client = TestClient(test_app)
        resp = client.get("/api/voice/capabilities?provider=mock")
        assert resp.status_code == 200
        body = resp.json()
        assert body["provider"] == "mock"
        assert body["tts"]["supported"] is True

    def test_get_unknown_provider_returns_404(self, test_app):
        client = TestClient(test_app)
        resp = client.get("/api/voice/capabilities?provider=unknown")
        assert resp.status_code == 404
        assert resp.status_code != 500

    def test_capability_dump_does_not_leak_secrets(self, test_app):
        client = TestClient(test_app)
        resp = client.get("/api/voice/capabilities?provider=minimax")
        assert resp.status_code == 200
        text = resp.text
        assert "sk-" not in text
        assert "minimax_api_key" not in text


class TestCapabilityModelValidation:
    def test_numeric_range_valid(self):
        nr = NumericRange(min=0.5, max=2.0)
        assert nr.min == 0.5
        assert nr.max == 2.0

    def test_numeric_range_invalid_min_gt_max(self):
        with pytest.raises(ValueError) as exc_info:
            NumericRange(min=3.0, max=1.0)
        assert "min must be <= max" in str(exc_info.value)

    def test_numeric_range_equal_min_max_is_valid(self):
        nr = NumericRange(min=1.0, max=1.0)
        assert nr.min == nr.max

    def test_voice_id_constraint_valid(self):
        vic = VoiceIdConstraint(min_length=8, max_length=256, pattern=r"^[a-z]+$")
        assert vic.min_length == 8
        assert vic.max_length == 256

    def test_voice_id_constraint_invalid_min_length_zero(self):
        with pytest.raises(ValueError) as exc_info:
            VoiceIdConstraint(min_length=0, max_length=256, pattern=r"^[a-z]+$")
        assert "min_length must be > 0" in str(exc_info.value)

    def test_voice_id_constraint_invalid_min_length_negative(self):
        with pytest.raises(ValueError) as exc_info:
            VoiceIdConstraint(min_length=-1, max_length=256, pattern=r"^[a-z]+$")
        assert "min_length must be > 0" in str(exc_info.value)

    def test_voice_id_constraint_invalid_max_length_less_than_min(self):
        with pytest.raises(ValueError) as exc_info:
            VoiceIdConstraint(min_length=10, max_length=5, pattern=r"^[a-z]+$")
        assert "max_length must be >= min_length" in str(exc_info.value)

    def test_voice_id_constraint_invalid_pattern_not_regex(self):
        with pytest.raises(ValueError) as exc_info:
            VoiceIdConstraint(min_length=8, max_length=256, pattern=r"**[invalid")
        assert "pattern is invalid regex" in str(exc_info.value)

    def test_tts_capability_valid(self):
        tts = TTSCapability(
            supported=True,
            models=["mock-tts"],
            default_model="mock-tts",
            max_text_chars=10000,
            audio_formats=["mp3"],
        )
        assert tts.supported is True

    def test_tts_capability_invalid_empty_models_when_supported(self):
        with pytest.raises(ValueError) as exc_info:
            TTSCapability(supported=True, models=[], audio_formats=["mp3"])
        assert "models must not be empty" in str(exc_info.value)

    def test_tts_capability_invalid_empty_audio_formats_when_supported(self):
        with pytest.raises(ValueError) as exc_info:
            TTSCapability(supported=True, models=["mock-tts"], audio_formats=[])
        assert "audio_formats must not be empty" in str(exc_info.value)

    def test_tts_capability_invalid_max_text_chars_zero(self):
        with pytest.raises(ValueError) as exc_info:
            TTSCapability(supported=True, models=["mock-tts"], audio_formats=["mp3"], max_text_chars=0)
        assert "max_text_chars must be > 0" in str(exc_info.value)

    def test_tts_capability_invalid_default_model_not_in_models(self):
        with pytest.raises(ValueError) as exc_info:
            TTSCapability(supported=True, models=["model-a"], default_model="model-b", audio_formats=["mp3"])
        assert "default_model must be included in models" in str(exc_info.value)

    def test_tts_capability_supported_false_allows_empty_models(self):
        tts = TTSCapability(supported=False, models=[], audio_formats=[])
        assert tts.supported is False

    def test_batch_capability_valid(self):
        batch = BatchCapability(
            supported=True,
            max_text_chars=50000,
            max_segments=200,
            segment_strategies=["auto", "line"],
        )
        assert batch.supported is True

    def test_batch_capability_invalid_max_text_chars_zero(self):
        with pytest.raises(ValueError) as exc_info:
            BatchCapability(supported=True, max_text_chars=0, segment_strategies=["auto"])
        assert "max_text_chars must be > 0" in str(exc_info.value)

    def test_batch_capability_invalid_max_segments_zero(self):
        with pytest.raises(ValueError) as exc_info:
            BatchCapability(supported=True, max_text_chars=50000, max_segments=0, segment_strategies=["auto"])
        assert "max_segments must be > 0" in str(exc_info.value)

    def test_batch_capability_invalid_empty_segment_strategies(self):
        with pytest.raises(ValueError) as exc_info:
            BatchCapability(supported=True, max_text_chars=50000, segment_strategies=[])
        assert "segment_strategies must not be empty" in str(exc_info.value)

    def test_batch_capability_supported_false_allows_empty_strategies(self):
        batch = BatchCapability(supported=False, max_text_chars=0, segment_strategies=[])
        assert batch.supported is False

    def test_provider_capability_valid(self):
        cap = ProviderCapability(
            provider="test",
            display_name="Test",
            tts=TTSCapability(supported=True, models=["t1"], audio_formats=["mp3"]),
            metadata={"api_key_configured": False},
        )
        assert cap.provider == "test"

    def test_provider_capability_invalid_empty_provider(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderCapability(provider="", display_name="Test")
        assert "provider must not be empty" in str(exc_info.value)

    def test_provider_capability_invalid_empty_display_name(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderCapability(provider="test", display_name="")
        assert "display_name must not be empty" in str(exc_info.value)

    def test_provider_capability_invalid_default_model_not_in_tts_models(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderCapability(
                provider="test",
                display_name="Test",
                default_model="model-x",
                tts=TTSCapability(supported=True, models=["model-a"], audio_formats=["mp3"]),
            )
        assert "default_model must be included in tts.models" in str(exc_info.value)

    def test_provider_capability_metadata_blocks_exact_sensitive_key(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderCapability(provider="test", display_name="Test", metadata={"minimax_api_key": "sk-xxx"})
        assert "must not contain sensitive key" in str(exc_info.value)
        assert "minimax_api_key" in str(exc_info.value)

    def test_provider_capability_metadata_allows_api_key_configured(self):
        cap = ProviderCapability(provider="test", display_name="Test", metadata={"api_key_configured": True})
        assert cap.metadata["api_key_configured"] is True

    def test_provider_capability_metadata_blocks_sk_value(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderCapability(provider="test", display_name="Test", metadata={"custom_key": "sk-xxxxx"})
        assert "must not contain secret patterns" in str(exc_info.value)
