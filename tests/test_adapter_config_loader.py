"""
test_adapter_config_loader.py

P16-ADAPTER-PLUGIN-CONFIG-B1: Tests for adapter config loader.

Covers:
- AdapterConfig schema validation
- adapter_config_loader reading config/adapters/*.yaml
- adapter_config_loader cache clear
- list_adapter_configs returns mock and minimax configs
- get_adapter_config returns correct config by adapter_type
- AdapterConfig fields match expected schema
- No real external API calls
"""

import os
import sys
import pytest

# Ensure app is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAdapterConfigSchema:
    """AdapterConfig schema validation."""

    def test_adapter_config_schema_import(self):
        """AdapterConfig can be imported from app.domain.adapter_config."""
        from app.domain.adapter_config import AdapterConfig
        assert AdapterConfig is not None

    def test_endpoint_config_schema_import(self):
        """EndpointConfig can be imported from app.domain.adapter_config."""
        from app.domain.adapter_config import EndpointConfig
        assert EndpointConfig is not None

    def test_tts_capability_config_schema_import(self):
        """TTSCapabilityConfig can be imported."""
        from app.domain.adapter_config import TTSCapabilityConfig
        assert TTSCapabilityConfig is not None

    def test_adapter_config_required_adapter_type(self):
        """AdapterConfig requires adapter_type field."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(Exception):
            AdapterConfig()

    def test_adapter_config_minimal_valid(self):
        """AdapterConfig with only adapter_type is valid."""
        from app.domain.adapter_config import AdapterConfig
        cfg = AdapterConfig(adapter_type="test")
        assert cfg.adapter_type == "test"
        assert cfg.default_model is None
        assert cfg.endpoints is not None

    def test_adapter_config_full_fields(self):
        """AdapterConfig accepts all defined fields."""
        from app.domain.adapter_config import AdapterConfig, EndpointConfig, TTSCapabilityConfig

        cfg = AdapterConfig(
            adapter_type="test_adapter",
            default_base_url="https://api.test.com",
            default_model="test-model",
            default_timeout_seconds=60,
            endpoints=EndpointConfig(t2a="/t2a"),
            tts=TTSCapabilityConfig(models=["m1", "m2"], audio_formats=["mp3"]),
        )
        assert cfg.adapter_type == "test_adapter"
        assert cfg.default_base_url == "https://api.test.com"
        assert cfg.default_model == "test-model"
        assert cfg.default_timeout_seconds == 60
        assert cfg.endpoints.t2a == "/t2a"
        assert cfg.tts.models == ["m1", "m2"]
        assert cfg.tts.audio_formats == ["mp3"]

    def test_adapter_config_extra_forbidden(self):
        """AdapterConfig forbids extra fields."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(Exception):
            AdapterConfig(adapter_type="test", unknown_field="value")


class TestAdapterConfigLoader:
    """AdapterConfigLoader functionality."""

    def test_adapter_config_loader_import(self):
        """adapter_config_loader can be imported."""
        from app.config import adapter_config_loader
        assert adapter_config_loader is not None

    def test_list_adapter_configs_returns_list(self):
        """list_adapter_configs returns a list."""
        from app.config.adapter_config_loader import list_adapter_configs, clear_adapter_config_cache
        clear_adapter_config_cache()
        configs = list_adapter_configs()
        assert isinstance(configs, list)

    def test_get_adapter_config_mock(self):
        """get_adapter_config returns mock config."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg is not None
        assert cfg.adapter_type == "mock"
        assert cfg.default_model == "mock-tts"

    def test_get_adapter_config_minimax(self):
        """get_adapter_config returns minimax config."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("minimax")
        assert cfg is not None
        assert cfg.adapter_type == "minimax"
        assert cfg.default_model == "speech-2.8-hd"

    def test_get_adapter_config_unknown_returns_none(self):
        """get_adapter_config returns None for unknown type."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("nonexistent")
        assert cfg is None

    def test_list_adapter_configs_includes_mock_and_minimax(self):
        """list_adapter_configs includes both mock and minimax."""
        from app.config.adapter_config_loader import list_adapter_configs, clear_adapter_config_cache
        clear_adapter_config_cache()
        configs = list_adapter_configs()
        adapter_types = [c.adapter_type for c in configs]
        assert "mock" in adapter_types
        assert "minimax" in adapter_types

    def test_mock_config_tts_fields(self):
        """mock adapter config has correct TTS fields."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.tts is not None
        assert "mock-tts" in cfg.tts.models
        assert cfg.tts.default_model == "mock-tts"
        assert cfg.tts.max_text_chars == 10000
        assert "mp3" in cfg.tts.audio_formats
        assert cfg.tts.supports_subtitle is True

    def test_minimax_config_tts_fields(self):
        """minimax adapter config has correct TTS fields."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("minimax")
        assert cfg is not None
        assert cfg.tts is not None
        assert "speech-2.8-hd" in cfg.tts.models
        assert cfg.tts.default_model == "speech-2.8-hd"
        assert cfg.tts.max_text_chars == 10000
        assert "mp3" in cfg.tts.audio_formats
        assert cfg.tts.supports_subtitle is True
        assert cfg.tts.supports_streaming is True
        assert cfg.tts.supports_emotion is True

    def test_minimax_config_endpoints(self):
        """minimax adapter config has correct endpoints."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("minimax")
        assert cfg.endpoints is not None
        assert cfg.endpoints.t2a == "/v1/t2a_v2"
        assert cfg.endpoints.t2a_async == "/v1/t2a_async_v2"
        assert cfg.endpoints.query_async == "/v1/query/t2a_async_query_v2"
        assert cfg.endpoints.voice_clone == "/v1/voice_clone"

    def test_minimax_config_batch_fields(self):
        """minimax adapter config has correct batch fields."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("minimax")
        assert cfg.batch is not None
        assert cfg.batch.max_text_chars == 50000
        assert cfg.batch.max_segments == 200

    def test_minimax_config_voice_clone_fields(self):
        """minimax adapter config has correct voice_clone fields."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("minimax")
        assert cfg.voice_clone is not None
        assert cfg.voice_clone.preview_text_max == 1000
        assert cfg.voice_clone.supports_noise_reduction is True
        assert cfg.voice_clone.supports_volume_normalization is True
        assert cfg.voice_clone.max_file_size_mb == 20

    def test_clear_adapter_config_cache(self):
        """clear_adapter_config_cache works without error."""
        from app.config.adapter_config_loader import clear_adapter_config_cache, list_adapter_configs
        clear_adapter_config_cache()
        configs1 = list_adapter_configs()
        clear_adapter_config_cache()
        configs2 = list_adapter_configs()
        assert len(configs1) == len(configs2)

    def test_adapter_config_caching(self):
        """Configs are cached and return same objects."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg1 = get_adapter_config("mock")
        cfg2 = get_adapter_config("mock")
        assert cfg1 is cfg2


class TestCapabilityRegistryWithAdapterConfig:
    """Capability registry uses AdapterConfig."""

    def test_capability_registry_import(self):
        """capability_registry can be imported."""
        from app.providers import capability_registry
        assert capability_registry is not None

    def test_mock_capability_uses_config(self):
        """mock provider capability reflects AdapterConfig."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        cap = get_capability("mock")
        assert cap is not None
        assert cap.provider == "mock"
        assert cap.metadata.get("configured_via_yaml") is True

    def test_minimax_capability_uses_config(self):
        """minimax provider capability reflects AdapterConfig."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        cap = get_capability("minimax")
        assert cap is not None
        assert cap.provider == "minimax"
        assert cap.metadata.get("configured_via_yaml") is True

    def test_mock_configured_capability(self):
        """mock_configured uses mock adapter_type and gets correct capability."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        cap = get_capability("mock_configured")
        assert cap is not None
        assert cap.provider == "mock_configured"
        assert cap.metadata.get("adapter_type") == "mock"
        assert cap.metadata.get("real_cost") is False
        assert cap.metadata.get("configured_via_yaml") is True

    def test_list_capabilities_includes_mock_and_minimax(self):
        """list_capabilities includes mock and minimax."""
        from app.providers.capability_registry import list_capabilities, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "mock" in providers
        assert "minimax" in providers
        assert "mock_configured" in providers

    def test_capability_tts_from_adapter_config(self):
        """TTS capability is built from AdapterConfig."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        cap = get_capability("mock")
        assert cap.tts is not None
        assert "mock-tts" in cap.tts.models

    def test_capability_batch_from_adapter_config(self):
        """Batch capability is built from AdapterConfig."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        cap = get_capability("mock")
        assert cap.batch is not None
        assert cap.batch.max_text_chars == 50000

    def test_minimax_capability_tts_models_from_adapter(self):
        """minimax TTS models come from AdapterConfig."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        cap = get_capability("minimax")
        assert cap.tts is not None
        assert "speech-2.8-hd" in cap.tts.models
        assert "speech-02.5-turbo" in cap.tts.models

    def test_disabled_provider_not_in_capabilities(self):
        """disabled_provider is not in capability list."""
        from app.providers.capability_registry import list_capabilities, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "disabled_provider" not in providers

    def test_capability_metadata_has_adapter_type(self):
        """Capability metadata includes adapter_type."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_capability_registry_cache()
        clear_provider_config_cache()
        cap = get_capability("mock")
        assert cap.metadata.get("adapter_type") == "mock"
        cap_minimax = get_capability("minimax")
        assert cap_minimax.metadata.get("adapter_type") == "minimax"


class TestAdapterConfigMetadataSecurity:
    """AdapterConfig metadata sensitive field validation."""

    def test_metadata_rejects_api_key(self):
        """metadata with api_key is rejected."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(ValueError, match="must not contain sensitive key"):
            AdapterConfig(adapter_type="test", metadata={"api_key": "secret123"})

    def test_metadata_rejects_token(self):
        """metadata with token is rejected."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(ValueError, match="must not contain sensitive key"):
            AdapterConfig(adapter_type="test", metadata={"token": " bearer xyz"})

    def test_metadata_rejects_secret(self):
        """metadata with secret is rejected."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(ValueError, match="must not contain sensitive key"):
            AdapterConfig(adapter_type="test", metadata={"secret": "topsecret"})

    def test_metadata_rejects_password(self):
        """metadata with password is rejected."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(ValueError, match="must not contain sensitive key"):
            AdapterConfig(adapter_type="test", metadata={"password": "pwd123"})

    def test_metadata_rejects_sk_pattern(self):
        """metadata value containing sk- is rejected."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(ValueError, match="must not contain secret patterns"):
            AdapterConfig(adapter_type="test", metadata={"notes": "sk-abc123"})

    def test_metadata_rejects_token_key(self):
        """metadata with key containing 'token' is rejected."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(ValueError, match="must not contain secret patterns"):
            AdapterConfig(adapter_type="test", metadata={"token_key": "safe_value"})

    def test_metadata_accepts_safe_values(self):
        """metadata with safe values is accepted."""
        from app.domain.adapter_config import AdapterConfig
        cfg = AdapterConfig(
            adapter_type="test",
            metadata={"note": "safe note", "mode": "test", "version": "1.0"},
        )
        assert cfg.metadata["note"] == "safe note"

    def test_metadata_case_insensitive_key_check(self):
        """metadata key check is case insensitive."""
        from app.domain.adapter_config import AdapterConfig
        with pytest.raises(ValueError, match="must not contain sensitive key"):
            AdapterConfig(adapter_type="test", metadata={"API_KEY": "secret"})


class TestAdapterConfigSupportedField:
    """AdapterConfig capability supported field tests."""

    def test_mock_adapter_tts_supported_true(self):
        """mock adapter config has tts.supported == true."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.tts is not None
        assert cfg.tts.supported is True

    def test_minimax_adapter_tts_supported_true(self):
        """minimax adapter config has tts.supported == true."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("minimax")
        assert cfg.tts is not None
        assert cfg.tts.supported is True

    def test_mock_adapter_batch_supported_true(self):
        """mock adapter config has batch.supported == true."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.batch is not None
        assert cfg.batch.supported is True

    def test_mock_adapter_script_supported_true(self):
        """mock adapter config has script.supported == true."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.script is not None
        assert cfg.script.supported is True

    def test_mock_adapter_voice_clone_supported_true(self):
        """mock adapter config has voice_clone.supported == true."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.voice_clone is not None
        assert cfg.voice_clone.supported is True

    def test_mock_adapter_voice_design_supported_true(self):
        """mock adapter config has voice_design.supported == true."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.voice_design is not None
        assert cfg.voice_design.supported is True

    def test_mock_adapter_provider_voices_supported_true(self):
        """mock adapter config has provider_voices.supported == true."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache
        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.provider_voices is not None
        assert cfg.provider_voices.supported is True


class TestProviderConfigEnabledOverride:
    """ProviderConfig enabled=false must override AdapterConfig."""

    def test_provider_tts_disabled_stays_disabled(self):
        """When provider_config.tts.enabled=false, capability.tts.supported=false."""
        from app.domain.provider_config import ProviderConfig, TTSConfig
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.providers.capability_registry import clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_adapter_config_cache()
        clear_capability_registry_cache()
        clear_provider_config_cache()

        # Create a provider config with tts disabled
        from app.providers.capability_registry import _build_capability_from_config

        config = ProviderConfig(
            name="test_disable_tts",
            display_name="Test Disable TTS",
            enabled=True,
            adapter_type="mock",
            real_cost=False,
            tts=TTSConfig(enabled=False),
        )

        cap = _build_capability_from_config(config)
        assert cap.tts is not None
        assert cap.tts.supported is False

    def test_provider_batch_disabled_stays_disabled(self):
        """When provider_config.batch.enabled=false, capability.batch.supported=false."""
        from app.domain.provider_config import ProviderConfig, BatchConfig
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.providers.capability_registry import clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_adapter_config_cache()
        clear_capability_registry_cache()
        clear_provider_config_cache()

        from app.providers.capability_registry import _build_capability_from_config

        config = ProviderConfig(
            name="test_disable_batch",
            display_name="Test Disable Batch",
            enabled=True,
            adapter_type="mock",
            real_cost=False,
            batch=BatchConfig(enabled=False),
        )

        cap = _build_capability_from_config(config)
        assert cap.batch is not None
        assert cap.batch.supported is False

    def test_provider_script_disabled_stays_disabled(self):
        """When provider_config.script.enabled=false, capability.script.supported=false."""
        from app.domain.provider_config import ProviderConfig, ScriptConfig
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.providers.capability_registry import clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_adapter_config_cache()
        clear_capability_registry_cache()
        clear_provider_config_cache()

        from app.providers.capability_registry import _build_capability_from_config

        config = ProviderConfig(
            name="test_disable_script",
            display_name="Test Disable Script",
            enabled=True,
            adapter_type="mock",
            real_cost=False,
            script=ScriptConfig(enabled=False),
        )

        cap = _build_capability_from_config(config)
        assert cap.script is not None
        assert cap.script.supported is False

    def test_provider_voice_clone_disabled_stays_disabled(self):
        """When provider_config.voice_clone.enabled=false, capability.voice_clone.supported=false."""
        from app.domain.provider_config import ProviderConfig, VoiceCloneConfig
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.providers.capability_registry import clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_adapter_config_cache()
        clear_capability_registry_cache()
        clear_provider_config_cache()

        from app.providers.capability_registry import _build_capability_from_config

        config = ProviderConfig(
            name="test_disable_vc",
            display_name="Test Disable VC",
            enabled=True,
            adapter_type="mock",
            real_cost=False,
            voice_clone=VoiceCloneConfig(enabled=False),
        )

        cap = _build_capability_from_config(config)
        assert cap.voice_clone is not None
        assert cap.voice_clone.supported is False

    def test_provider_voice_design_disabled_stays_disabled(self):
        """When provider_config.voice_design.enabled=false, capability.voice_design.supported=false."""
        from app.domain.provider_config import ProviderConfig, VoiceDesignConfig
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.providers.capability_registry import clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_adapter_config_cache()
        clear_capability_registry_cache()
        clear_provider_config_cache()

        from app.providers.capability_registry import _build_capability_from_config

        config = ProviderConfig(
            name="test_disable_vd",
            display_name="Test Disable VD",
            enabled=True,
            adapter_type="mock",
            real_cost=False,
            voice_design=VoiceDesignConfig(enabled=False),
        )

        cap = _build_capability_from_config(config)
        assert cap.voice_design is not None
        assert cap.voice_design.supported is False

    def test_provider_provider_voices_disabled_stays_disabled(self):
        """When provider_config.provider_voices.enabled=false, capability.provider_voices.supported=false."""
        from app.domain.provider_config import ProviderConfig, ProviderVoicesConfig
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.providers.capability_registry import clear_capability_registry_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_adapter_config_cache()
        clear_capability_registry_cache()
        clear_provider_config_cache()

        from app.providers.capability_registry import _build_capability_from_config

        config = ProviderConfig(
            name="test_disable_pv",
            display_name="Test Disable PV",
            enabled=True,
            adapter_type="mock",
            real_cost=False,
            provider_voices=ProviderVoicesConfig(enabled=False),
        )

        cap = _build_capability_from_config(config)
        assert cap.provider_voices is not None
        assert cap.provider_voices.supported is False
