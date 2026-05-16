"""Provider registry: looks up providers by name and returns adapter instances.

Resolution chain:
  name -> ProviderConfig -> adapter_type -> ADAPTER_TYPE_REGISTRY -> SpeechProvider class

If no config is found, falls back to PROVIDER_REGISTRY (backward compatibility).
"""

from app.core.errors import UnsupportedProvider
from app.providers.adapter_type_registry import (
    get_adapter_type_adapter,
)
from app.providers.base import SpeechProvider
from app.config.provider_config_loader import get_provider_config


# Static registry kept for backward compatibility and type hints.
# New providers should be added via config/providers.yaml.
PROVIDER_REGISTRY: dict[str, type[SpeechProvider]] = {}


def _register_static_providers() -> None:
    """Register static provider adapters (called once at import time)."""
    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
    from app.providers.mock_speech_adapter import MockSpeechAdapter

    PROVIDER_REGISTRY["mock"] = MockSpeechAdapter
    PROVIDER_REGISTRY["minimax"] = MiniMaxSpeechAdapter


def get_provider(name: str) -> SpeechProvider:
    """Look up a provider by name and return a new adapter instance.

    Resolution chain:
      name -> ProviderConfig -> adapter_type
        -> get_adapter_type_adapter() [config discovery -> legacy fallback]
        -> Adapter class

    Args:
        name: Provider name string (e.g. 'mock', 'minimax', 'mock_configured').

    Returns:
        SpeechProvider instance.

    Raises:
        UnsupportedProvider: If provider name is not found in config or registry.
    """
    # Try config-driven route first
    config = get_provider_config(name)
    if config:
        if not config.enabled:
            raise UnsupportedProvider(f"Provider {name} is not enabled", name)
        adapter_cls = get_adapter_type_adapter(config.adapter_type)
        return adapter_cls()

    # Fallback to static registry (backward compatibility for hardcoded providers)
    cls = PROVIDER_REGISTRY.get(name)
    if cls:
        return cls()

    raise UnsupportedProvider(f"Unsupported provider: {name}", name)


# Register static providers at module import
_register_static_providers()
