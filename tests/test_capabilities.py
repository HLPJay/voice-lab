import pytest
from fastapi.testclient import TestClient

from app.core.errors import UnsupportedProvider
from app.domain.capabilities import ProviderCapability
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
