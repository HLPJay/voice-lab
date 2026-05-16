"""
test_adapter_plugin_discovery.py

P16-ADAPTER-PLUGIN-DISCOVERY-B1: Tests for adapter plugin discovery mechanism.

Covers:
- AdapterPluginConfig schema validation
- Dynamic adapter registration from config/adapters/*.yaml
- register_adapter_type_from_import_path security and error cases
- Provider routing regression (mock/minimax/mock_configured/disabled_provider)
- Capability API regression
- No real external API calls
"""

import os
import sys
import pytest

# Ensure app is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAdapterPluginConfigSchema:
    """AdapterPluginConfig schema validation."""

    def test_adapter_plugin_config_import(self):
        """AdapterPluginConfig can be imported."""
        from app.domain.adapter_config import AdapterPluginConfig

        cfg = AdapterPluginConfig(import_path="app.providers.mock_speech_adapter.MockSpeechAdapter")
        assert cfg.import_path == "app.providers.mock_speech_adapter.MockSpeechAdapter"

    def test_adapter_config_has_plugin_field(self):
        """AdapterConfig has a plugin field."""
        from app.domain.adapter_config import AdapterConfig

        cfg = AdapterConfig(adapter_type="test")
        # plugin defaults to None
        assert cfg.plugin is None

    def test_adapter_config_with_plugin(self):
        """AdapterConfig accepts plugin field."""
        from app.domain.adapter_config import AdapterConfig, AdapterPluginConfig

        cfg = AdapterConfig(
            adapter_type="test",
            plugin=AdapterPluginConfig(import_path="app.providers.mock_speech_adapter.MockSpeechAdapter"),
        )
        assert cfg.plugin is not None
        assert cfg.plugin.import_path == "app.providers.mock_speech_adapter.MockSpeechAdapter"

    def test_plugin_import_path_empty_raises(self):
        """Empty import_path is rejected."""
        from app.domain.adapter_config import AdapterPluginConfig

        with pytest.raises(ValueError, match="must not be empty"):
            AdapterPluginConfig(import_path="")

    def test_plugin_import_path_whitespace_raises(self):
        """Whitespace-only import_path is rejected."""
        from app.domain.adapter_config import AdapterPluginConfig

        with pytest.raises(ValueError, match="must not be empty"):
            AdapterPluginConfig(import_path="   ")

    def test_plugin_import_path_non_providers_prefix_raises(self):
        """import_path not starting with app.providers. is rejected."""
        from app.domain.adapter_config import AdapterPluginConfig

        with pytest.raises(ValueError, match="must start with 'app.providers.'"):
            AdapterPluginConfig(import_path="os.system")

    def test_plugin_import_path_no_class_name_raises(self):
        """import_path without a class name is rejected."""
        from app.domain.adapter_config import AdapterPluginConfig

        with pytest.raises(ValueError, match="class name must start with an uppercase letter"):
            AdapterPluginConfig(import_path="app.providers.mock_speech_adapter")

    def test_plugin_extra_field_forbidden(self):
        """Extra fields in AdapterPluginConfig are forbidden."""
        from app.domain.adapter_config import AdapterPluginConfig

        with pytest.raises(Exception):
            AdapterPluginConfig(import_path="app.providers.mock_speech_adapter.MockSpeechAdapter", extra="value")


class TestAdapterConfigPluginFromYAML:
    """AdapterConfig loaded from YAML has correct plugin.import_path."""

    def test_mock_yaml_has_plugin_import_path(self):
        """mock.yaml has plugin.import_path."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache

        clear_adapter_config_cache()
        cfg = get_adapter_config("mock")
        assert cfg.plugin is not None
        assert cfg.plugin.import_path == "app.providers.mock_speech_adapter.MockSpeechAdapter"

    def test_minimax_yaml_has_plugin_import_path(self):
        """minimax.yaml has plugin.import_path."""
        from app.config.adapter_config_loader import get_adapter_config, clear_adapter_config_cache

        clear_adapter_config_cache()
        cfg = get_adapter_config("minimax")
        assert cfg.plugin is not None
        assert cfg.plugin.import_path == "app.providers.minimax_speech_adapter.MiniMaxSpeechAdapter"


class TestDynamicRegistration:
    """Dynamic adapter registration from config."""

    def setup_method(self):
        """Reset registry state before each test."""
        from app.providers.adapter_type_registry import clear_adapter_type_registry_for_tests

        clear_adapter_type_registry_for_tests()

    def test_register_adapter_type_from_import_path_mock(self):
        """register_adapter_type_from_import_path registers MockSpeechAdapter."""
        from app.providers.adapter_type_registry import register_adapter_type_from_import_path

        cls = register_adapter_type_from_import_path(
            "mock", "app.providers.mock_speech_adapter.MockSpeechAdapter"
        )
        assert cls.__name__ == "MockSpeechAdapter"

        from app.providers.adapter_type_registry import ADAPTER_TYPE_REGISTRY

        assert "mock" in ADAPTER_TYPE_REGISTRY
        assert ADAPTER_TYPE_REGISTRY["mock"].__name__ == "MockSpeechAdapter"

    def test_register_adapter_type_from_import_path_minimax(self):
        """register_adapter_type_from_import_path registers MiniMaxSpeechAdapter."""
        from app.providers.adapter_type_registry import register_adapter_type_from_import_path

        cls = register_adapter_type_from_import_path(
            "minimax", "app.providers.minimax_speech_adapter.MiniMaxSpeechAdapter"
        )
        assert cls.__name__ == "MiniMaxSpeechAdapter"

    def test_register_adapter_type_from_import_path_invalid_prefix(self):
        """Invalid prefix raises ValueError."""
        from app.providers.adapter_type_registry import register_adapter_type_from_import_path

        with pytest.raises(ValueError, match="must start with 'app.providers.'"):
            register_adapter_type_from_import_path("evil", "os.system")

    def test_register_adapter_type_from_import_path_nonexistent_module(self):
        """Nonexistent module raises ImportError."""
        from app.providers.adapter_type_registry import register_adapter_type_from_import_path

        with pytest.raises(ImportError, match="Failed to import module"):
            register_adapter_type_from_import_path(
                "fake", "app.providers.nonexistent_module.FakeClass"
            )

    def test_register_adapter_type_from_import_path_nonexistent_class(self):
        """Nonexistent class raises AttributeError."""
        from app.providers.adapter_type_registry import register_adapter_type_from_import_path

        with pytest.raises(AttributeError, match="Class 'NonExistentClass' not found"):
            register_adapter_type_from_import_path(
                "fake", "app.providers.mock_speech_adapter.NonExistentClass"
            )

    def test_register_adapter_type_from_import_path_non_speech_provider(self):
        """Non-SpeechProvider class raises TypeError."""
        from app.providers.adapter_type_registry import register_adapter_type_from_import_path

        with pytest.raises(TypeError, match="must be a SpeechProvider subclass"):
            register_adapter_type_from_import_path(
                "evil", "app.providers.base.StreamAudioChunk"
            )

    def test_load_adapter_plugins_from_config(self):
        """load_adapter_plugins_from_config registers mock and minimax."""
        from app.providers.adapter_type_registry import (
            ADAPTER_TYPE_REGISTRY,
            load_adapter_plugins_from_config,
        )

        # Registry should be empty before loading
        assert len(ADAPTER_TYPE_REGISTRY) == 0

        load_adapter_plugins_from_config()

        # Both mock and minimax should be registered
        assert "mock" in ADAPTER_TYPE_REGISTRY
        assert "minimax" in ADAPTER_TYPE_REGISTRY
        assert ADAPTER_TYPE_REGISTRY["mock"].__name__ == "MockSpeechAdapter"
        assert ADAPTER_TYPE_REGISTRY["minimax"].__name__ == "MiniMaxSpeechAdapter"

    def test_load_adapter_plugins_idempotent(self):
        """load_adapter_plugins_from_config is idempotent."""
        from app.providers.adapter_type_registry import load_adapter_plugins_from_config

        load_adapter_plugins_from_config()
        load_adapter_plugins_from_config()  # Should not raise

    def test_get_adapter_type_adapter_loads_from_config(self):
        """get_adapter_type_adapter loads from config when not already registered."""
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
            get_adapter_type_adapter,
        )

        clear_adapter_type_registry_for_tests()

        # Without loading, mock should not be registered
        from app.providers.adapter_type_registry import ADAPTER_TYPE_REGISTRY

        assert "mock" not in ADAPTER_TYPE_REGISTRY

        # get_adapter_type_adapter should auto-load from config
        cls = get_adapter_type_adapter("mock")
        assert cls.__name__ == "MockSpeechAdapter"

    def test_get_adapter_type_adapter_minimax(self):
        """get_adapter_type_adapter('minimax') returns MiniMaxSpeechAdapter."""
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
            get_adapter_type_adapter,
        )

        clear_adapter_type_registry_for_tests()
        cls = get_adapter_type_adapter("minimax")
        assert cls.__name__ == "MiniMaxSpeechAdapter"


class TestClearRegistryForTests:
    """clear_adapter_type_registry_for_tests utility."""

    def test_clear_resets_plugins_loaded_flag(self):
        """clear_adapter_type_registry_for_tests resets state."""
        from app.providers.adapter_type_registry import (
            ADAPTER_TYPE_REGISTRY,
            clear_adapter_type_registry_for_tests,
            load_adapter_plugins_from_config,
        )

        load_adapter_plugins_from_config()
        assert len(ADAPTER_TYPE_REGISTRY) > 0

        clear_adapter_type_registry_for_tests()
        assert len(ADAPTER_TYPE_REGISTRY) == 0

        from app.providers.adapter_type_registry import _plugins_loaded

        assert _plugins_loaded is False


class TestProviderRoutingRegression:
    """Provider routing regression tests — ensure existing behavior is preserved."""

    def setup_method(self):
        """Reset all caches before each test."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import clear_adapter_type_registry_for_tests
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

    def test_get_provider_mock(self):
        """get_provider('mock') returns MockSpeechAdapter instance."""
        from app.providers.registry import get_provider

        adapter = get_provider("mock")
        assert adapter.provider_name == "mock"

    def test_get_provider_minimax(self):
        """get_provider('minimax') returns MiniMaxSpeechAdapter instance."""
        from app.providers.registry import get_provider

        adapter = get_provider("minimax")
        assert adapter.provider_name == "minimax"

    def test_get_provider_mock_configured(self):
        """get_provider('mock_configured') returns MockSpeechAdapter instance."""
        from app.providers.registry import get_provider

        adapter = get_provider("mock_configured")
        assert adapter.provider_name == "mock"

    def test_get_provider_disabled_raises(self):
        """get_provider('disabled_provider') raises UnsupportedProvider."""
        from app.core.errors import UnsupportedProvider
        from app.providers.registry import get_provider

        with pytest.raises(UnsupportedProvider, match="disabled_provider"):
            get_provider("disabled_provider")


class TestCapabilityAPIRegression:
    """Capability API regression tests."""

    def setup_method(self):
        """Reset all caches before each test."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import clear_adapter_type_registry_for_tests
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

    def test_capabilities_includes_mock(self):
        """list_capabilities includes 'mock'."""
        from app.providers.capability_registry import list_capabilities

        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "mock" in providers

    def test_capabilities_includes_minimax(self):
        """list_capabilities includes 'minimax'."""
        from app.providers.capability_registry import list_capabilities

        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "minimax" in providers

    def test_capabilities_includes_mock_configured(self):
        """list_capabilities includes 'mock_configured'."""
        from app.providers.capability_registry import list_capabilities

        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "mock_configured" in providers

    def test_capabilities_excludes_disabled_provider(self):
        """list_capabilities excludes 'disabled_provider'."""
        from app.providers.capability_registry import list_capabilities

        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "disabled_provider" not in providers

    def test_mock_metadata_has_adapter_type(self):
        """mock capability metadata has adapter_type='mock'."""
        from app.providers.capability_registry import get_capability

        cap = get_capability("mock")
        assert cap.metadata.get("adapter_type") == "mock"

    def test_minimax_metadata_has_adapter_type(self):
        """minimax capability metadata has adapter_type='minimax'."""
        from app.providers.capability_registry import get_capability

        cap = get_capability("minimax")
        assert cap.metadata.get("adapter_type") == "minimax"

    def test_minimax_metadata_has_real_cost_true(self):
        """minimax capability metadata has real_cost=True."""
        from app.providers.capability_registry import get_capability

        cap = get_capability("minimax")
        assert cap.metadata.get("real_cost") is True

    def test_mock_metadata_has_real_cost_false(self):
        """mock capability metadata has real_cost=False."""
        from app.providers.capability_registry import get_capability

        cap = get_capability("mock")
        assert cap.metadata.get("real_cost") is False

    def test_mock_configured_metadata_configured_via_yaml(self):
        """mock_configured capability metadata has configured_via_yaml=True."""
        from app.providers.capability_registry import get_capability

        cap = get_capability("mock_configured")
        assert cap.metadata.get("configured_via_yaml") is True
        assert cap.metadata.get("adapter_type") == "mock"
        assert cap.metadata.get("real_cost") is False

    def test_capabilities_do_not_expose_secrets(self):
        """Capability metadata does not contain sensitive keys."""
        from app.providers.capability_registry import list_capabilities

        sensitive = {"api_key", "token", "secret", "password", "minimax_api_key", "openai_api_key"}
        for cap in list_capabilities():
            for key in sensitive:
                assert key not in cap.metadata, f"Provider {cap.provider} metadata contains {key}"


class TestNoRealExternalAPICalls:
    """Verify no real external API calls are made."""

    def test_dynamic_import_does_not_call_external_api(self):
        """Dynamic import only loads Python modules, no HTTP calls."""
        import httpx
        from unittest.mock import patch

        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
            load_adapter_plugins_from_config,
        )

        clear_adapter_type_registry_for_tests()

        with patch.object(httpx, "get") as mock_get:
            load_adapter_plugins_from_config()
            # Should not make any HTTP requests
            mock_get.assert_not_called()

    def test_get_adapter_type_adapter_no_http_calls(self):
        """get_adapter_type_adapter does not make HTTP requests."""
        import httpx
        from unittest.mock import patch

        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
            get_adapter_type_adapter,
        )

        clear_adapter_type_registry_for_tests()

        with patch.object(httpx, "get") as mock_get:
            get_adapter_type_adapter("mock")
            mock_get.assert_not_called()
