"""Adapter type registry: maps adapter_type string to SpeechProvider adapter class.

This decouples provider names from adapter classes, enabling config-driven
provider routing without code changes per provider.

Primary registration path:
  config/adapters/*.yaml -> AdapterConfig.plugin.import_path
    -> importlib dynamic import -> register_adapter_type()

Fallback (legacy):
  _ensure_core_adapters_registered() registers mock/minimax hardcoded
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base import SpeechProvider

# Maps adapter_type string -> SpeechProvider class
ADAPTER_TYPE_REGISTRY: dict[str, type[SpeechProvider]] = {}

# Track whether plugins have been loaded from config
_plugins_loaded: bool = False


def register_adapter_type(adapter_type: str, adapter_cls: type[SpeechProvider]) -> None:
    """Register an adapter class for an adapter_type.

    Args:
        adapter_type: String key (e.g. 'mock', 'minimax', 'openai').
        adapter_cls: SpeechProvider subclass.
    """
    ADAPTER_TYPE_REGISTRY[adapter_type] = adapter_cls


def register_adapter_type_from_import_path(
    adapter_type: str, import_path: str
) -> type[SpeechProvider]:
    """Register an adapter class from a Python import path.

    Dynamically imports the module and retrieves the adapter class.

    Args:
        adapter_type: String key (e.g. 'mock', 'minimax').
        import_path: Python import path (e.g. 'app.providers.mock_speech_adapter.MockSpeechAdapter').

    Returns:
        The registered SpeechProvider class.

    Raises:
        ValueError: If import_path is invalid or not in app.providers. prefix.
        ImportError: If the module cannot be imported.
        AttributeError: If the class is not found in the module.
        TypeError: If the class is not a SpeechProvider subclass.
    """
    # Security: only allow app.providers. prefix
    if not import_path.startswith("app.providers."):
        raise ValueError(
            f"import_path must start with 'app.providers.', got: {import_path}"
        )

    # Parse module path and class name
    parts = import_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"import_path must be in format 'module.path.ClassName', got: {import_path}"
        )
    module_path, class_name = parts

    # Dynamically import the module
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(
            f"Failed to import module '{module_path}' for adapter_type '{adapter_type}': {exc}"
        ) from exc

    # Get the class from the module
    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise AttributeError(
            f"Class '{class_name}' not found in module '{module_path}' "
            f"for adapter_type '{adapter_type}': {exc}"
        ) from exc

    # Validate it's a SpeechProvider subclass
    from app.providers.base import SpeechProvider

    if not issubclass(cls, SpeechProvider):
        raise TypeError(
            f"Class '{class_name}' in '{module_path}' for adapter_type '{adapter_type}' "
            f"must be a SpeechProvider subclass, got: {cls.__mro__}"
        )

    # Register the adapter
    register_adapter_type(adapter_type, cls)
    return cls


def load_adapter_plugins_from_config() -> None:
    """Load and register all adapter plugins from config/adapters/*.yaml.

    For each adapter config with a plugin.import_path, dynamically imports
    the adapter class and registers it in ADAPTER_TYPE_REGISTRY.
    """
    global _plugins_loaded
    if _plugins_loaded:
        return

    from app.config.adapter_config_loader import list_adapter_configs

    configs = list_adapter_configs()
    for cfg in configs:
        if cfg.plugin and cfg.plugin.import_path:
            try:
                register_adapter_type_from_import_path(
                    cfg.adapter_type, cfg.plugin.import_path
                )
            except (ValueError, ImportError, AttributeError, TypeError):
                # Skip configs with invalid import_path - they may be
                # intentionally incomplete or pending migration
                pass

    _plugins_loaded = True


def clear_adapter_type_registry_for_tests() -> None:
    """Clear the adapter type registry and reset plugin loading state.

    Useful in tests when config state changes or to force re-discovery.
    """
    global _plugins_loaded
    ADAPTER_TYPE_REGISTRY.clear()
    _plugins_loaded = False


def get_adapter_type_adapter(adapter_type: str) -> type[SpeechProvider]:
    """Look up an adapter class by adapter_type string.

    Resolution chain:
      1. If already registered in ADAPTER_TYPE_REGISTRY, return it
      2. Try loading from config/adapters/*.yaml via plugin.import_path
      3. Fall back to _ensure_core_adapters_registered() (legacy mock/minimax)
      4. If still not found, raise UnsupportedProvider

    Args:
        adapter_type: The adapter type key.

    Returns:
        SpeechProvider subclass.

    Raises:
        UnsupportedProvider: If adapter_type is not registered.
    """
    from app.core.errors import UnsupportedProvider

    # Fast path: already registered
    cls = ADAPTER_TYPE_REGISTRY.get(adapter_type)
    if cls:
        return cls

    # Try loading from config
    load_adapter_plugins_from_config()
    cls = ADAPTER_TYPE_REGISTRY.get(adapter_type)
    if cls:
        return cls

    # Fallback to core adapters (legacy mock/minimax)
    _ensure_core_adapters_registered()
    cls = ADAPTER_TYPE_REGISTRY.get(adapter_type)
    if cls:
        return cls

    raise UnsupportedProvider(
        f"Unsupported adapter type: {adapter_type}", adapter_type
    )


def is_registered_adapter_type(adapter_type: str) -> bool:
    """Check if an adapter_type is registered."""
    return adapter_type in ADAPTER_TYPE_REGISTRY


def _ensure_core_adapters_registered() -> None:
    """Register core adapter types if not already registered.

    Called on first use of get_adapter_type_adapter to ensure the registry
    is populated even if providers/__init__.py was not imported.

    NOTE: This is a legacy fallback. The primary registration path is
    load_adapter_plugins_from_config() which reads from config/adapters/*.yaml.
    """
    if not ADAPTER_TYPE_REGISTRY:
        from app.providers.mock_speech_adapter import MockSpeechAdapter
        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

        register_adapter_type("mock", MockSpeechAdapter)
        register_adapter_type("minimax", MiniMaxSpeechAdapter)


# Eagerly register core adapter types on module import
_ensure_core_adapters_registered()
