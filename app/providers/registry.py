"""Provider registry: looks up providers by name and returns adapter instances.

Resolution chain:
  name -> ProviderConfig -> adapter_type -> ADAPTER_TYPE_REGISTRY -> SpeechProvider class
  -> instantiate with (provider_config, adapter_config)

All registration is config-driven via config/adapters/*.yaml plugin.import_path.
"""

from app.core.errors import UnsupportedProvider
from app.config.adapter_config_loader import get_adapter_config
from app.config.provider_config_loader import get_provider_config
from app.providers.adapter_type_registry import get_adapter_type_adapter
from app.providers.base import SpeechProvider


def get_provider(name: str) -> SpeechProvider:
    """Look up a provider by name and return a new adapter instance.

    Resolution chain:
      name -> ProviderConfig -> adapter_type
        -> get_adapter_type_adapter() [plugin discovery]
        -> Adapter class(provider_config, adapter_config)

    Args:
        name: Provider name string (e.g. 'mock', 'minimax', 'mock_configured').

    Returns:
        SpeechProvider instance.

    Raises:
        UnsupportedProvider: If provider name is not found in config or not enabled.
    """
    config = get_provider_config(name)
    if not config:
        raise UnsupportedProvider(f"Unknown provider: {name}", name)
    if not config.enabled:
        raise UnsupportedProvider(f"Provider {name} is not enabled", name)

    adapter_cls = get_adapter_type_adapter(config.adapter_type)
    adapter_config = get_adapter_config(config.adapter_type)
    return adapter_cls(provider_config=config, adapter_config=adapter_config)
