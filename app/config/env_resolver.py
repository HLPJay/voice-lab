"""Environment variable resolver supporting os.environ and .env file fallback.

Used by ProviderConfig to resolve api_key_env and base_url_env values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# Cache for .env file contents to avoid repeated disk reads
_cached_env_file: dict[str, str] | None = None


def _load_env_file() -> dict[str, str]:
    """Load .env file from project root and cache it."""
    global _cached_env_file
    if _cached_env_file is not None:
        return _cached_env_file

    _cached_env_file = {}
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    _cached_env_file[key.strip()] = value.strip().strip("\"'")
    return _cached_env_file


def resolve_env_value(env_name: str) -> str | None:
    """Resolve an environment variable value.

    Checks os.environ first, then falls back to .env file in project root.

    Args:
        env_name: Name of the environment variable to resolve.

    Returns:
        The resolved value, or None if not found.
    """
    # Check os.environ first
    value = os.environ.get(env_name)
    if value is not None:
        return value

    # Fall back to .env file
    env_file = _load_env_file()
    return env_file.get(env_name)


def clear_env_cache() -> None:
    """Clear the .env file cache.

    Call in tests when config state changes.
    """
    global _cached_env_file
    _cached_env_file = None
