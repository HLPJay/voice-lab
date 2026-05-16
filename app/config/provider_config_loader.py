"""Provider configuration loader from config/providers.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from app.domain.provider_config import ProviderConfig


_PROVIDER_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "providers.yaml"

# In-memory cache keyed by provider name
_cached_configs: dict[str, ProviderConfig] | None = None


def _load_raw_configs() -> list[dict]:
    """Load raw configs from YAML file. Does not parse into ProviderConfig."""
    path = os.environ.get("VOICE_LAB_PROVIDER_CONFIG_PATH", str(_PROVIDER_CONFIG_PATH))
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "providers" not in data:
        return []
    return data["providers"]


def list_provider_configs() -> list[ProviderConfig]:
    """List all provider configs (cached).

    Returns:
        List of ProviderConfig objects for all providers in config file.
    """
    global _cached_configs
    if _cached_configs is None:
        from app.domain.provider_config import ProviderConfig

        raw = _load_raw_configs()
        _cached_configs = {c["name"]: ProviderConfig(**c) for c in raw}
    return list(_cached_configs.values())


def get_provider_config(name: str) -> ProviderConfig | None:
    """Get a single provider config by name (cached).

    Args:
        name: Provider name string.

    Returns:
        ProviderConfig if found, None otherwise.
    """
    configs = list_provider_configs()
    for cfg in configs:
        if cfg.name == name:
            return cfg
    return None


def list_enabled_provider_configs() -> list[ProviderConfig]:
    """List all enabled provider configs.

    Returns:
        List of ProviderConfig objects where enabled=True.
    """
    return [c for c in list_provider_configs() if c.enabled]


def clear_provider_config_cache() -> None:
    """Clear the in-memory config cache.

    Call after config file changes or in tests when config state changes.
    """
    global _cached_configs
    _cached_configs = None
