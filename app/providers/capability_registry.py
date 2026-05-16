"""Capability registry: provides ProviderCapability for each provider.

Built from config/providers.yaml + adapter_type capability builders.
The /api/voice/capabilities response format is unchanged.
"""

from app.core.errors import UnsupportedProvider
from app.domain.capabilities import ProviderCapability
from app.config.provider_config_loader import list_enabled_provider_configs
from app.providers.mock_capabilities import MOCK_CAPABILITY
from app.providers.minimax_capabilities import build_minimax_capability

# Maps adapter_type -> capability builder function
_CAPABILITY_BUILDERS: dict[str, callable] = {
    "mock": lambda: MOCK_CAPABILITY,
    "minimax": build_minimax_capability,
}


def _build_capability_from_config(config) -> ProviderCapability:
    """Build ProviderCapability from a ProviderConfig + adapter_type builder.

    Args:
        config: ProviderConfig object.

    Returns:
        ProviderCapability with config-driven metadata.
    """
    builder = _CAPABILITY_BUILDERS.get(config.adapter_type)
    if not builder:
        # Unknown adapter type — return a minimal capability rather than raising,
        # so the provider still appears in /api/voice/capabilities
        return ProviderCapability(
            provider=config.name,
            display_name=config.display_name,
            enabled=config.enabled,
            metadata={
                "adapter_type": config.adapter_type,
                "real_cost": config.real_cost,
                "configured_via_yaml": True,
                "warning": f"No capability builder for adapter_type '{config.adapter_type}'",
            },
        )

    base_capability = builder()

    return ProviderCapability(
        provider=config.name,
        display_name=config.display_name,
        enabled=config.enabled,
        default_model=config.default_model or base_capability.default_model,
        tts=base_capability.tts,
        batch=base_capability.batch,
        script=base_capability.script,
        voice_clone=base_capability.voice_clone,
        voice_design=base_capability.voice_design,
        provider_voices=base_capability.provider_voices,
        metadata={
            **base_capability.metadata,
            "adapter_type": config.adapter_type,
            "real_cost": config.real_cost,
            "configured_via_yaml": True,
        },
    )


def _build_registry() -> dict[str, ProviderCapability]:
    """Build the full capability registry from YAML config."""
    registry = {}
    for config in list_enabled_provider_configs():
        cap = _build_capability_from_config(config)
        registry[config.name] = cap
    return registry


# Module-level registry cache
_capability_registry: dict[str, ProviderCapability] | None = None


def _get_registry() -> dict[str, ProviderCapability]:
    """Get the capability registry (cached)."""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = _build_registry()
    return _capability_registry


def list_capabilities() -> list[ProviderCapability]:
    """List all provider capabilities."""
    return list(_get_registry().values())


def get_capability(provider: str) -> ProviderCapability:
    """Get capability for a specific provider."""
    registry = _get_registry()
    cap = registry.get(provider)
    if not cap:
        raise UnsupportedProvider(f"Unsupported provider: {provider}", provider)
    return cap


def provider_exists(provider: str) -> bool:
    """Check if a provider exists in the capability registry."""
    return provider in _get_registry()


def clear_capability_registry_cache() -> None:
    """Clear the in-memory capability registry cache.

    Useful in tests when provider configs change.
    """
    global _capability_registry
    _capability_registry = None
