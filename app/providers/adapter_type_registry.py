"""Adapter type registry: maps adapter_type string to SpeechProvider adapter class.

All registration is config-driven:
  config/adapters/*.yaml -> AdapterConfig.plugin.import_path
    -> importlib dynamic import -> register_adapter_type()

No hardcoded adapter registration. Adding a new adapter only requires:
  1. Write the adapter class (implements SpeechProvider)
  2. Add config/adapters/{type}.yaml with plugin.import_path
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
    """Register an adapter class for an adapter_type."""
    ADAPTER_TYPE_REGISTRY[adapter_type] = adapter_cls


def register_adapter_type_from_import_path(
    adapter_type: str, import_path: str
) -> type[SpeechProvider]:
    """Register an adapter class from a Python import path.

    Dynamically imports the module and retrieves the adapter class.

    Raises:
        ValueError: If import_path is invalid or not in app.providers. prefix.
        ImportError: If the module cannot be imported.
        AttributeError: If the class is not found in the module.
        TypeError: If the class is not a SpeechProvider subclass.
    """
    if not import_path.startswith("app.providers."):
        raise ValueError(
            f"import_path must start with 'app.providers.', got: {import_path}"
        )

    parts = import_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"import_path must be in format 'module.path.ClassName', got: {import_path}"
        )
    module_path, class_name = parts

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(
            f"Failed to import module '{module_path}' for adapter_type '{adapter_type}': {exc}"
        ) from exc

    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise AttributeError(
            f"Class '{class_name}' not found in module '{module_path}' "
            f"for adapter_type '{adapter_type}': {exc}"
        ) from exc

    from app.providers.base import SpeechProvider

    if not issubclass(cls, SpeechProvider):
        raise TypeError(
            f"Class '{class_name}' in '{module_path}' for adapter_type '{adapter_type}' "
            f"must be a SpeechProvider subclass, got: {cls.__mro__}"
        )

    register_adapter_type(adapter_type, cls)
    return cls


class AdapterPluginLoadError(Exception):
    """Raised when a plugin.import_path fails to load."""

    def __init__(self, adapter_type: str, import_path: str, cause: Exception):
        self.adapter_type = adapter_type
        self.import_path = import_path
        self.cause = cause
        super().__init__(
            f"Failed to load adapter plugin for '{adapter_type}' "
            f"from import_path '{import_path}': {type(cause).__name__}: {cause}"
        )


def load_adapter_plugins_from_config(*, strict: bool = True) -> None:
    """Load and register all adapter plugins from config/adapters/*.yaml.

    For each adapter config with a plugin.import_path, dynamically imports
    the adapter class and registers it in ADAPTER_TYPE_REGISTRY.
    """
    global _plugins_loaded
    if _plugins_loaded:
        return

    from app.config.adapter_config_loader import list_adapter_configs

    configs = list_adapter_configs()
    errors: list[AdapterPluginLoadError] = []
    for cfg in configs:
        if cfg.plugin and cfg.plugin.import_path:
            try:
                register_adapter_type_from_import_path(
                    cfg.adapter_type, cfg.plugin.import_path
                )
            except (ValueError, ImportError, AttributeError, TypeError) as exc:
                if strict:
                    errors.append(AdapterPluginLoadError(cfg.adapter_type, cfg.plugin.import_path, exc))

    if errors:
        raise AdapterPluginLoadError(errors[0].adapter_type, errors[0].import_path, errors[0].cause)

    _plugins_loaded = True


def clear_adapter_type_registry_for_tests() -> None:
    """Clear the adapter type registry and reset plugin loading state."""
    global _plugins_loaded
    ADAPTER_TYPE_REGISTRY.clear()
    _plugins_loaded = False


def get_adapter_type_adapter(adapter_type: str) -> type[SpeechProvider]:
    """Look up an adapter class by adapter_type string.

    Resolution:
      1. If already registered in ADAPTER_TYPE_REGISTRY, return it
      2. Try loading from config/adapters/*.yaml via plugin.import_path
      3. If still not found, raise UnsupportedProvider
    """
    from app.core.errors import UnsupportedProvider

    cls = ADAPTER_TYPE_REGISTRY.get(adapter_type)
    if cls:
        return cls

    load_adapter_plugins_from_config()
    cls = ADAPTER_TYPE_REGISTRY.get(adapter_type)
    if cls:
        return cls

    raise UnsupportedProvider(
        f"Unsupported adapter type: {adapter_type}", adapter_type
    )


def is_registered_adapter_type(adapter_type: str) -> bool:
    """Check if an adapter_type is registered."""
    return adapter_type in ADAPTER_TYPE_REGISTRY
