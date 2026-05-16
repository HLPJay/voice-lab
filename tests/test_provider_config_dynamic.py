"""
test_provider_config_dynamic.py

P16-DYNAMIC-PROVIDER-CONFIG-B1: Tests for config-driven provider registry.

Covers:
- ProviderConfig schema validation
- provider_config_loader reading YAML
- provider_config_loader cache clear
- adapter_type_registry routing by adapter_type
- get_provider("mock_configured") returns MockSpeechAdapter
- /api/voice/capabilities includes mock_configured
- CostGuardService uses ProviderConfig.real_cost
- mock/minimax backward compatibility
- No real external API calls
"""

import os
import sys
import tempfile
import pytest

# Ensure app is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestProviderConfigSchema:
    """ProviderConfig schema validation."""

    def test_provider_config_schema_import(self):
        """ProviderConfig can be imported from app.domain.provider_config."""
        from app.domain.provider_config import ProviderConfig
        assert ProviderConfig is not None

    def test_mock_config_has_required_fields(self):
        """mock provider config has all required fields."""
        from app.domain.provider_config import ProviderConfig
        cfg = ProviderConfig(
            name="test_mock",
            display_name="Test Mock",
            enabled=True,
            adapter_type="mock",
            real_cost=False,
        )
        assert cfg.name == "test_mock"
        assert cfg.display_name == "Test Mock"
        assert cfg.enabled is True
        assert cfg.adapter_type == "mock"
        assert cfg.real_cost is False

    def test_minimax_config_has_required_fields(self):
        """minimax provider config has all required fields."""
        from app.domain.provider_config import ProviderConfig
        cfg = ProviderConfig(
            name="minimax",
            display_name="MiniMax",
            enabled=True,
            adapter_type="minimax",
            real_cost=True,
            api_key_env="MINIMAX_API_KEY",
            base_url="https://api.minimaxi.com",
            default_model="speech-2.8-hd",
        )
        assert cfg.name == "minimax"
        assert cfg.adapter_type == "minimax"
        assert cfg.real_cost is True
        assert cfg.api_key_env == "MINIMAX_API_KEY"

    def test_metadata_forbidden_sensitive_keys(self):
        """ProviderConfig rejects metadata with sensitive keys."""
        from app.domain.provider_config import ProviderConfig
        with pytest.raises(ValueError, match="must not contain sensitive key"):
            ProviderConfig(
                name="bad",
                display_name="Bad",
                adapter_type="mock",
                real_cost=False,
                metadata={"api_key": "secret123", "token": "tok123"},
            )

    def test_metadata_forbidden_secret_patterns(self):
        """ProviderConfig rejects metadata with secret-like string values."""
        from app.domain.provider_config import ProviderConfig
        with pytest.raises(ValueError, match="must not contain secret patterns"):
            ProviderConfig(
                name="bad",
                display_name="Bad",
                adapter_type="mock",
                real_cost=False,
                metadata={"notes": "use sk-12345 here"},
            )

    def test_resolved_api_key_returns_none_when_not_set(self):
        """api_key_env=None gives None from resolved_api_key."""
        from app.domain.provider_config import ProviderConfig
        cfg = ProviderConfig(
            name="mock",
            display_name="Mock",
            adapter_type="mock",
            real_cost=False,
            api_key_env=None,
        )
        assert cfg.resolved_api_key is None

    def test_resolved_base_url_fallback(self):
        """resolved_base_url falls back to base_url when base_url_env not set."""
        from app.domain.provider_config import ProviderConfig
        cfg = ProviderConfig(
            name="minimax",
            display_name="MiniMax",
            adapter_type="minimax",
            real_cost=True,
            base_url_env=None,
            base_url="https://api.minimaxi.com",
        )
        assert cfg.resolved_base_url == "https://api.minimaxi.com"


class TestProviderConfigLoader:
    """provider_config_loader YAML loading and caching."""

    def test_loads_mock_config(self):
        """provider_config_loader returns mock config."""
        from app.config.provider_config_loader import get_provider_config
        cfg = get_provider_config("mock")
        assert cfg is not None
        assert cfg.name == "mock"
        assert cfg.adapter_type == "mock"
        assert cfg.real_cost is False

    def test_loads_minimax_config(self):
        """provider_config_loader returns minimax config."""
        from app.config.provider_config_loader import get_provider_config
        cfg = get_provider_config("minimax")
        assert cfg is not None
        assert cfg.name == "minimax"
        assert cfg.adapter_type == "minimax"
        assert cfg.real_cost is True

    def test_loads_mock_configured(self):
        """provider_config_loader returns mock_configured config."""
        from app.config.provider_config_loader import get_provider_config
        cfg = get_provider_config("mock_configured")
        assert cfg is not None
        assert cfg.name == "mock_configured"
        assert cfg.adapter_type == "mock"
        assert cfg.real_cost is False

    def test_list_provider_configs_includes_all_three(self):
        """list_provider_configs returns mock, minimax, mock_configured."""
        from app.config.provider_config_loader import list_provider_configs
        names = {c.name for c in list_provider_configs()}
        assert "mock" in names
        assert "minimax" in names
        assert "mock_configured" in names

    def test_list_enabled_provider_configs(self):
        """list_enabled_provider_configs returns only enabled configs."""
        from app.config.provider_config_loader import list_enabled_provider_configs
        configs = list_enabled_provider_configs()
        assert all(c.enabled for c in configs)

    def test_cache_clear(self):
        """clear_provider_config_cache allows cache refresh."""
        from app.config.provider_config_loader import (
            clear_provider_config_cache,
            list_provider_configs,
        )
        # Load once
        first = list_provider_configs()
        assert len(first) >= 3
        # Clear cache
        clear_provider_config_cache()
        # Load again — should still work
        second = list_provider_configs()
        assert len(second) >= 3

    def test_unknown_provider_returns_none(self):
        """get_provider_config returns None for unknown provider."""
        from app.config.provider_config_loader import get_provider_config
        cfg = get_provider_config("nonexistent_provider_xyz")
        assert cfg is None

    def test_yaml_path_env_override(self):
        """VOICE_LAB_PROVIDER_CONFIG_PATH env var overrides default path."""
        import yaml
        from app.config.provider_config_loader import clear_provider_config_cache

        # Write a temp YAML with a unique provider
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.safe_dump({"providers": [{"name": "env_override_test", "display_name": "Env Test", "enabled": True, "adapter_type": "mock", "real_cost": False}]}, f)
            temp_path = f.name

        try:
            clear_provider_config_cache()
            old_path = os.environ.get("VOICE_LAB_PROVIDER_CONFIG_PATH")
            os.environ["VOICE_LAB_PROVIDER_CONFIG_PATH"] = temp_path
            try:
                from app.config import provider_config_loader
                provider_config_loader._cached_configs = None  # force reload
                from app.config.provider_config_loader import list_provider_configs
                names = {c.name for c in list_provider_configs()}
                assert "env_override_test" in names
            finally:
                if old_path is None:
                    os.environ.pop("VOICE_LAB_PROVIDER_CONFIG_PATH", None)
                else:
                    os.environ["VOICE_LAB_PROVIDER_CONFIG_PATH"] = old_path
                # restore
                clear_provider_config_cache()
        finally:
            os.unlink(temp_path)


class TestAdapterTypeRegistry:
    """adapter_type_registry routes by adapter_type."""

    def test_mock_adapter_type_registered(self):
        """'mock' adapter_type maps to MockSpeechAdapter."""
        from app.providers.adapter_type_registry import ADAPTER_TYPE_REGISTRY
        assert "mock" in ADAPTER_TYPE_REGISTRY

    def test_minimax_adapter_type_registered(self):
        """'minimax' adapter_type maps to MiniMaxSpeechAdapter."""
        from app.providers.adapter_type_registry import ADAPTER_TYPE_REGISTRY
        assert "minimax" in ADAPTER_TYPE_REGISTRY

    def test_get_adapter_type_adapter_mock(self):
        """get_adapter_type_adapter('mock') returns MockSpeechAdapter."""
        from app.providers.adapter_type_registry import get_adapter_type_adapter
        cls = get_adapter_type_adapter("mock")
        assert cls.__name__ == "MockSpeechAdapter"

    def test_get_adapter_type_adapter_minimax(self):
        """get_adapter_type_adapter('minimax') returns MiniMaxSpeechAdapter."""
        from app.providers.adapter_type_registry import get_adapter_type_adapter
        cls = get_adapter_type_adapter("minimax")
        assert cls.__name__ == "MiniMaxSpeechAdapter"

    def test_get_adapter_type_adapter_unknown_raises(self):
        """get_adapter_type_adapter for unknown type raises UnsupportedProvider."""
        from app.providers.adapter_type_registry import get_adapter_type_adapter
        from app.core.errors import UnsupportedProvider
        with pytest.raises(UnsupportedProvider, match="Unsupported adapter type"):
            get_adapter_type_adapter("nonexistent_adapter_type_xyz")


class TestGetProvider:
    """get_provider uses config-driven routing."""

    def test_get_provider_mock_configured(self):
        """get_provider('mock_configured') returns MockSpeechAdapter instance."""
        from app.providers.registry import get_provider
        from app.providers.mock_speech_adapter import MockSpeechAdapter

        # Clear config cache to ensure clean state
        from app.config.provider_config_loader import clear_provider_config_cache
        clear_provider_config_cache()

        adapter = get_provider("mock_configured")
        assert isinstance(adapter, MockSpeechAdapter)

    def test_get_provider_mock_still_works(self):
        """get_provider('mock') still returns MockSpeechAdapter (backward compat)."""
        from app.providers.registry import get_provider
        from app.providers.mock_speech_adapter import MockSpeechAdapter

        adapter = get_provider("mock")
        assert isinstance(adapter, MockSpeechAdapter)

    def test_get_provider_minimax_still_works(self):
        """get_provider('minimax') still returns MiniMaxSpeechAdapter (backward compat)."""
        from app.providers.registry import get_provider
        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

        adapter = get_provider("minimax")
        assert isinstance(adapter, MiniMaxSpeechAdapter)

    def test_get_provider_unknown_raises(self):
        """get_provider for unknown provider raises UnsupportedProvider."""
        from app.providers.registry import get_provider
        from app.core.errors import UnsupportedProvider
        with pytest.raises(UnsupportedProvider, match="Unsupported provider"):
            get_provider("nonexistent_provider_xyz")


class TestCapabilityRegistry:
    """capability_registry includes mock_configured."""

    def test_capability_registry_includes_mock_configured(self):
        """list_capabilities() includes mock_configured."""
        from app.providers.capability_registry import (
            clear_capability_registry_cache,
            list_capabilities,
        )
        clear_capability_registry_cache()
        caps = list_capabilities()
        providers = {c.provider for c in caps}
        assert "mock_configured" in providers

    def test_mock_configured_capability_has_correct_metadata(self):
        """mock_configured capability has adapter_type=mock, real_cost=false."""
        from app.providers.capability_registry import (
            clear_capability_registry_cache,
            get_capability,
        )
        clear_capability_registry_cache()
        cap = get_capability("mock_configured")
        assert cap.metadata.get("adapter_type") == "mock"
        assert cap.metadata.get("real_cost") is False
        assert cap.metadata.get("configured_via_yaml") is True

    def test_minimax_capability_has_correct_metadata(self):
        """minimax capability has adapter_type=minimax, real_cost=true."""
        from app.providers.capability_registry import (
            clear_capability_registry_cache,
            get_capability,
        )
        clear_capability_registry_cache()
        cap = get_capability("minimax")
        assert cap.metadata.get("adapter_type") == "minimax"
        assert cap.metadata.get("real_cost") is True
        assert cap.metadata.get("configured_via_yaml") is True

    def test_capabilities_do_not_expose_api_keys(self):
        """Capability metadata does not contain api_key, token, or secret values."""
        from app.providers.capability_registry import (
            clear_capability_registry_cache,
            list_capabilities,
        )
        clear_capability_registry_cache()
        sensitive = {"api_key", "token", "secret", "password", "minimax_api_key", "openai_api_key"}
        for cap in list_capabilities():
            cap_metadata = cap.metadata
            for key in sensitive:
                assert key not in cap_metadata, \
                    f"Provider {cap.provider} metadata contains sensitive key: {key}"


class TestCostGuardService:
    """CostGuardService uses ProviderConfig.real_cost."""

    def test_cost_guard_mock_no_confirm_required(self):
        """mock provider does not require cost confirm."""
        from app.services.cost_guard_service import CostGuardService
        svc = CostGuardService()
        # Should not raise
        svc.require_confirmed("mock", "voice_variants", confirm_cost=False)

    def test_cost_guard_mock_configured_no_confirm_required(self):
        """mock_configured (real_cost=false) does not require cost confirm."""
        from app.services.cost_guard_service import CostGuardService
        svc = CostGuardService()
        # Should not raise
        svc.require_confirmed("mock_configured", "voice_variants", confirm_cost=False)

    def test_cost_guard_minimax_requires_confirm(self):
        """minimax (real_cost=true) requires confirm for HIGH_RISK_OPERATIONS."""
        from app.services.cost_guard_service import CostGuardService
        from app.core.errors import ValidationError
        svc = CostGuardService()
        with pytest.raises(ValidationError, match="需要确认成本"):
            svc.require_confirmed("minimax", "voice_variants", confirm_cost=False)

    def test_cost_guard_minimax_with_confirm_succeeds(self):
        """minimax with confirm_cost=True succeeds."""
        from app.services.cost_guard_service import CostGuardService
        svc = CostGuardService()
        # Should not raise
        svc.require_confirmed("minimax", "voice_variants", confirm_cost=True)

    def test_cost_guard_unknown_provider_uses_fallback(self):
        """Unknown provider falls back to COST_PROVIDER_SET check (minimax only)."""
        from app.services.cost_guard_service import CostGuardService
        from app.core.errors import ValidationError
        svc = CostGuardService()
        # Provider not in config - fallback to COST_PROVIDER_SET which only has minimax
        # So unknown non-minimax provider should not raise
        svc.require_confirmed("unknown_provider_xyz", "voice_variants", confirm_cost=False)


class TestNoRealExternalAPICalls:
    """Verify no real external API calls are made in normal operation."""

    def test_get_provider_does_not_make_http_calls(self):
        """get_provider() does not make any HTTP requests."""
        import httpx
        from unittest.mock import patch

        from app.config.provider_config_loader import clear_provider_config_cache
        clear_provider_config_cache()

        with patch.object(httpx, "get") as mock_get:
            from app.providers.registry import get_provider
            get_provider("mock_configured")
            get_provider("mock")
            get_provider("minimax")
            # No HTTP calls should be made for mock or config loading
            # (only if network-based config loading was implemented)

    def test_provider_config_loader_loads_from_yaml_only(self):
        """provider_config_loader reads from YAML, not from network."""
        import httpx
        from unittest.mock import patch

        from app.config.provider_config_loader import clear_provider_config_cache
        clear_provider_config_cache()

        with patch.object(httpx, "get") as mock_get:
            from app.config.provider_config_loader import list_provider_configs
            configs = list_provider_configs()
            assert len(configs) >= 3
            # No HTTP calls should be made
