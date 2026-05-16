"""Adapter type registry: maps adapter_type string to SpeechProvider adapter class.

This decouples provider names from adapter classes, enabling config-driven
provider routing without code changes per provider.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base import SpeechProvider

# Maps adapter_type string -> SpeechProvider class
ADAPTER_TYPE_REGISTRY: dict[str, type[SpeechProvider]] = {}


def register_adapter_type(adapter_type: str, adapter_cls: type[SpeechProvider]) -> None:
    """Register an adapter class for an adapter_type.

    Args:
        adapter_type: String key (e.g. 'mock', 'minimax', 'openai').
        adapter_cls: SpeechProvider subclass.
    """
    ADAPTER_TYPE_REGISTRY[adapter_type] = adapter_cls


def get_adapter_type_adapter(adapter_type: str) -> type[SpeechProvider]:
    """Look up an adapter class by adapter_type string.

    Args:
        adapter_type: The adapter type key.

    Returns:
        SpeechProvider subclass.

    Raises:
        UnsupportedProvider: If adapter_type is not registered.
    """
    from app.core.errors import UnsupportedProvider

    cls = ADAPTER_TYPE_REGISTRY.get(adapter_type)
    if not cls:
        raise UnsupportedProvider(
            f"Unsupported adapter type: {adapter_type}", adapter_type
        )
    return cls


def is_registered_adapter_type(adapter_type: str) -> bool:
    """Check if an adapter_type is registered."""
    return adapter_type in ADAPTER_TYPE_REGISTRY


def _ensure_core_adapters_registered() -> None:
    """Register core adapter types if not already registered.

    Called on first use of get_adapter_type_adapter to ensure the registry
    is populated even if providers/__init__.py was not imported.
    """
    if not ADAPTER_TYPE_REGISTRY:
        from app.providers.mock_speech_adapter import MockSpeechAdapter
        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

        register_adapter_type("mock", MockSpeechAdapter)
        register_adapter_type("minimax", MiniMaxSpeechAdapter)


# Eagerly register core adapter types on module import
_ensure_core_adapters_registered()
