"""Adapter configuration loader from config/adapters/*.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from app.domain.adapter_config import AdapterConfig


def _get_adapter_config_dir() -> Path:
    """Get the adapter config directory path."""
    env_path = os.environ.get("VOICE_LAB_ADAPTER_CONFIG_DIR")
    if env_path:
        return Path(env_path)
    return Path(__file__).parent.parent.parent / "config" / "adapters"


def _discover_adapter_configs() -> list[dict]:
    """Discover all adapter config files in the adapters directory."""
    config_dir = _get_adapter_config_dir()
    if not config_dir.exists():
        return []

    configs = []
    for yaml_file in sorted(config_dir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data:
            configs.append(data)
    return configs


# In-memory cache keyed by adapter_type
_cached_configs: dict[str, AdapterConfig] | None = None


def list_adapter_configs() -> list[AdapterConfig]:
    """List all adapter configs (cached).

    Returns:
        List of AdapterConfig objects for all adapter configs in config/adapters/.
    """
    global _cached_configs
    if _cached_configs is None:
        from app.domain.adapter_config import AdapterConfig

        raw_configs = _discover_adapter_configs()
        _cached_configs = {}
        for raw in raw_configs:
            cfg = AdapterConfig(**raw)
            _cached_configs[cfg.adapter_type] = cfg
    return list(_cached_configs.values())


def get_adapter_config(adapter_type: str) -> AdapterConfig | None:
    """Get a single adapter config by adapter_type (cached).

    Args:
        adapter_type: Adapter type string (e.g. 'mock', 'minimax').

    Returns:
        AdapterConfig if found, None otherwise.
    """
    configs = list_adapter_configs()
    for cfg in configs:
        if cfg.adapter_type == adapter_type:
            return cfg
    return None


def clear_adapter_config_cache() -> None:
    """Clear the in-memory adapter config cache.

    Call after config file changes or in tests when config state changes.
    """
    global _cached_configs
    _cached_configs = None
