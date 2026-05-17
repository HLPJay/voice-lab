"""Environment variable resolver supporting os.environ and .env file fallback.

Resolution order:
1. os.environ[env_name]
2. VOICE_LAB_ENV_FILE env file (if set, points to a custom env file path)
3. Project root .env file
4. None if not found

Used by ProviderConfig to resolve api_key_env and base_url_env values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# Cache keyed by env file path to avoid repeated disk reads
# Structure: dict[path_str, dict[key, value]]
_cached_env_files: dict[str, dict[str, str]] = {}


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _load_env_file(env_path: Path) -> dict[str, str]:
    """Load a .env file from the given path and cache it.

    Args:
        env_path: Path to the .env file.

    Returns:
        Dictionary of key-value pairs from the env file.
    """
    path_str = str(env_path)
    if path_str in _cached_env_files:
        return _cached_env_files[path_str]

    result: dict[str, str] = {}
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        result[key.strip()] = value.strip().strip("\"'")
        except (OSError, IOError):
            # If file cannot be read, return empty dict (not an error)
            pass

    _cached_env_files[path_str] = result
    return result


def _get_env_file_path() -> Path | None:
    """Get the env file path from VOICE_LAB_ENV_FILE or project root .env.

    Returns:
        Path to the env file, or None if no file exists.
    """
    # Check VOICE_LAB_ENV_FILE first
    voice_lab_env_file = os.environ.get("VOICE_LAB_ENV_FILE")
    if voice_lab_env_file:
        env_path = Path(voice_lab_env_file)
        if env_path.exists():
            return env_path
        # If VOICE_LAB_ENV_FILE points to non-existent file, skip it silently
        return None

    # Fall back to project root .env
    project_env = _get_project_root() / ".env"
    if project_env.exists():
        return project_env

    return None


def resolve_env_value(env_name: str) -> str | None:
    """Resolve an environment variable value.

    Resolution order:
    1. os.environ[env_name] (highest priority)
    2. VOICE_LAB_ENV_FILE env file (if set)
    3. Project root .env file
    4. None if not found

    Args:
        env_name: Name of the environment variable to resolve.

    Returns:
        The resolved value, or None if not found.
    """
    # 1. Check os.environ first (highest priority)
    value = os.environ.get(env_name)
    if value is not None:
        return value

    # 2. Check VOICE_LAB_ENV_FILE if set
    voice_lab_env_file = os.environ.get("VOICE_LAB_ENV_FILE")
    if voice_lab_env_file:
        env_path = Path(voice_lab_env_file)
        env_file = _load_env_file(env_path)
        if env_name in env_file:
            return env_file[env_name]

    # 3. Fall back to project root .env
    project_env = _get_project_root() / ".env"
    if project_env.exists():
        env_file = _load_env_file(project_env)
        if env_name in env_file:
            return env_file[env_name]

    # 4. Not found
    return None


def clear_env_cache() -> None:
    """Clear all cached .env file contents.

    Call in tests when config state changes or when switching env files.
    """
    global _cached_env_files
    _cached_env_files = {}
