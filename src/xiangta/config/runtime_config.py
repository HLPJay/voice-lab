"""
XiangTa Runtime Configuration — layered config: default → runtime.json → env override.

只读取 XiangTa 自有运行时配置变量。
不读取任何真实 Provider API key.
不引入 Core 内部模块。
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


# ── Paths ────────────────────────────────────────────────────────────────────────

_CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"
_RUNTIME_JSON_PATH = _CONFIG_DIR / "runtime.json"


# ── Default config ─────────────────────────────────────────────────────────────

_DEFAULT_CONFIG: dict[str, Any] = {
    "admin": {
        "enabled": False,
    },
    "core": {
        "enabled": False,
        "baseUrl": "",
        "timeoutSecs": 20,
    },
    "copywriting": {
        "mode": "template",
        "provider": "none",
        "timeoutSecs": 20,
        "fallbackToTemplate": True,
    },
    "tts": {
        "mode": "sync",
        "maxConcurrent": 1,
        "queueEnabled": False,
        "timeoutSecs": 120,
    },
    "storage": {
        "type": "memory",
        "databaseUrl": "",
    },
    "features": {
        "devCoreProfileSelect": True,
        "lettersEnabled": True,
        "llmCopywritingEnabled": False,
        "ttsTaskEnabled": False,
    },
}


# ── Bool parsing ───────────────────────────────────────────────────────────────

_TRUE_VALUES = frozenset({"true", "1", "yes", "on"})
_FALSE_VALUES = frozenset({"false", "0", "no", "off"})


def _parse_bool(value: str) -> bool | None:
    """Parse bool from string. Returns None if the value is not a recognised bool string."""
    v = value.lower().strip()
    if v in _TRUE_VALUES:
        return True
    if v in _FALSE_VALUES:
        return False
    return None


# ── Config model ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class XiangTaRuntimeConfig:
    """
    只读运行时配置 — 不包含任何真实 Provider API key。

    Backward-compatible fields (kept for product_service.py compatibility):
      core_base_url: str | None
      core_timeout_secs: float

    New fields:
      core_enabled: bool
      core_url: str | None
      copywriting_*
      tts_*
      storage_*
      feature_*
    """
    # Backward-compatible core fields
    core_base_url: str | None = None
    core_timeout_secs: float = 20.0

    # Admin
    admin_enabled: bool = False
    admin_token: str | None = None

    # Core (new)
    core_enabled: bool = False
    core_url: str | None = None

    # Copywriting
    copywriting_mode: str = "template"
    copywriting_provider: str = "none"
    copywriting_timeout_secs: float = 20.0
    copywriting_fallback_to_template: bool = True

    # TTS
    tts_mode: str = "sync"
    tts_max_concurrent: int = 1
    tts_queue_enabled: bool = False
    tts_timeout_secs: float = 120.0

    # Storage
    storage_type: str = "memory"
    storage_database_url: str | None = None

    # Features
    feature_dev_core_profile_select: bool = True
    feature_letters_enabled: bool = True
    feature_llm_copywriting_enabled: bool = False
    feature_tts_task_enabled: bool = False


# ── Deep merge ────────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins on conflict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ── Config loading ────────────────────────────────────────────────────────────

def _load_runtime_json(path: Path | None = None) -> dict:
    """Load runtime.json from disk. Returns empty dict on error or missing file."""
    try:
        p = path or _RUNTIME_JSON_PATH
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:
        logger.warning(
            "Failed to load XiangTa runtime config from %s; using defaults: %s",
            str(path or _RUNTIME_JSON_PATH),
            exc,
        )
    return {}


def _get_env(key: str) -> str | None:
    """Get env var, returning None if empty or not set."""
    return os.environ.get(key) or None


def _apply_env_overrides(config: dict) -> dict:
    """
    Apply XIANGTA_* env vars on top of config dict.
    Priority: explicit env > config file > default.
    """
    # Admin
    admin = dict(config.get("admin", {}))
    admin_enabled_env_str = _get_env("XIANGTA_ADMIN_ENABLED")
    if admin_enabled_env_str is not None:
        parsed = _parse_bool(admin_enabled_env_str)
        admin["enabled"] = parsed if parsed is not None else False
    config = dict(config)
    config["admin"] = admin

    # Core
    core_base_url_env = _get_env("XIANGTA_CORE_BASE_URL")
    core_timeout_env = _get_env("XIANGTA_CORE_TIMEOUT_SECS")
    core_enabled_env_str = _get_env("XIANGTA_CORE_ENABLED")
    core_enabled_from_env: bool | None = None
    if core_enabled_env_str is not None:
        core_enabled_from_env = _parse_bool(core_enabled_env_str)

    core = dict(config.get("core", {}))

    # XIANGTA_CORE_BASE_URL always wins (explicit enable)
    if core_base_url_env:
        core["enabled"] = True
        core["baseUrl"] = core_base_url_env
    elif core_enabled_from_env is not None:
        core["enabled"] = core_enabled_from_env

    if core_timeout_env:
        try:
            core["timeoutSecs"] = float(core_timeout_env)
        except ValueError:
            pass  # fall back to file/default

    config["core"] = core

    # Copywriting
    if _get_env("XIANGTA_COPYWRITING_MODE"):
        config.setdefault("copywriting", {})["mode"] = _get_env("XIANGTA_COPYWRITING_MODE")
    if _get_env("XIANGTA_COPYWRITING_PROVIDER"):
        config.setdefault("copywriting", {})["provider"] = _get_env("XIANGTA_COPYWRITING_PROVIDER")
    if _get_env("XIANGTA_COPYWRITING_TIMEOUT_SECS"):
        try:
            config.setdefault("copywriting", {})["timeoutSecs"] = float(
                _get_env("XIANGTA_COPYWRITING_TIMEOUT_SECS")
            )
        except ValueError:
            pass
    if _get_env("XIANGTA_COPYWRITING_FALLBACK_TO_TEMPLATE"):
        env_val = _get_env("XIANGTA_COPYWRITING_FALLBACK_TO_TEMPLATE")
        if env_val is not None:
            v = _parse_bool(env_val)
            if v is not None:
                config.setdefault("copywriting", {})["fallbackToTemplate"] = v

    # TTS
    if _get_env("XIANGTA_TTS_MODE"):
        config.setdefault("tts", {})["mode"] = _get_env("XIANGTA_TTS_MODE")
    if _get_env("XIANGTA_TTS_MAX_CONCURRENT"):
        try:
            config.setdefault("tts", {})["maxConcurrent"] = int(
                _get_env("XIANGTA_TTS_MAX_CONCURRENT")
            )
        except ValueError:
            pass
    if _get_env("XIANGTA_TTS_QUEUE_ENABLED"):
        env_val = _get_env("XIANGTA_TTS_QUEUE_ENABLED")
        if env_val is not None:
            v = _parse_bool(env_val)
            if v is not None:
                config.setdefault("tts", {})["queueEnabled"] = v
    if _get_env("XIANGTA_TTS_TIMEOUT_SECS"):
        try:
            config.setdefault("tts", {})["timeoutSecs"] = float(
                _get_env("XIANGTA_TTS_TIMEOUT_SECS")
            )
        except ValueError:
            pass

    # Storage
    if _get_env("XIANGTA_STORAGE_TYPE"):
        config.setdefault("storage", {})["type"] = _get_env("XIANGTA_STORAGE_TYPE")
    if _get_env("XIANGTA_STORAGE_DATABASE_URL"):
        config.setdefault("storage", {})["databaseUrl"] = _get_env("XIANGTA_STORAGE_DATABASE_URL")

    # Features
    for env_key, config_key in [
        ("XIANGTA_FEATURE_DEV_CORE_PROFILE_SELECT", "devCoreProfileSelect"),
        ("XIANGTA_FEATURE_LETTERS_ENABLED", "lettersEnabled"),
        ("XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED", "llmCopywritingEnabled"),
        ("XIANGTA_FEATURE_TTS_TASK_ENABLED", "ttsTaskEnabled"),
    ]:
        v = _get_env(env_key)
        if v is not None:
            parsed = _parse_bool(v)
            if parsed is not None:
                config.setdefault("features", {})[config_key] = parsed

    return config


def _sanitize_timeout(value: float | None) -> float:
    """Return value if positive, else return default 20.0."""
    if value and value > 0:
        return float(value)
    return 20.0


# ── Public API ────────────────────────────────────────────────────────────────

def load_runtime_config() -> XiangTaRuntimeConfig:
    """
    Load XiangTa runtime config with priority:
      default → runtime.json → XIANGTA_* env vars

    只读取 XiangTa 自有 env 变量（XIANGTA_* 前缀）。
    不读取任何真实 Provider API key。
    不抛出未捕获异常。
    """
    # 1. Start with defaults
    config = _deep_merge({}, _DEFAULT_CONFIG)

    # 2. Overlay runtime.json
    file_config = _load_runtime_json(_RUNTIME_JSON_PATH)
    config = _deep_merge(config, file_config)

    # 3. Apply env overrides
    config = _apply_env_overrides(config)

    # Extract core settings
    admin = config.get("admin", {})
    core = config.get("core", {})
    copywriting = config.get("copywriting", {})
    tts = config.get("tts", {})
    storage = config.get("storage", {})
    features = config.get("features", {})

    # core_base_url: derive from enabled + baseUrl
    core_base_url: str | None = None
    if core.get("enabled") and core.get("baseUrl"):
        core_base_url = str(core["baseUrl"])

    core_timeout = _sanitize_timeout(core.get("timeoutSecs"))

    return XiangTaRuntimeConfig(
        # Core (backward-compatible)
        core_base_url=core_base_url,
        core_timeout_secs=core_timeout,
        # Admin
        admin_enabled=bool(admin.get("enabled", False)),
        admin_token=_get_env("XIANGTA_ADMIN_TOKEN"),
        # Core (new fields)
        core_enabled=bool(core.get("enabled", False)),
        core_url=(str(core["baseUrl"]) if core.get("baseUrl") else None),
        # Copywriting
        copywriting_mode=str(copywriting.get("mode", "template")),
        copywriting_provider=str(copywriting.get("provider", "none")),
        copywriting_timeout_secs=_sanitize_timeout(copywriting.get("timeoutSecs")),
        copywriting_fallback_to_template=bool(copywriting.get("fallbackToTemplate", True)),
        # TTS
        tts_mode=str(tts.get("mode", "sync")),
        tts_max_concurrent=max(1, int(tts.get("maxConcurrent", 1))),
        tts_queue_enabled=bool(tts.get("queueEnabled", False)),
        tts_timeout_secs=_sanitize_timeout(tts.get("timeoutSecs")),
        # Storage
        storage_type=str(storage.get("type", "memory")),
        storage_database_url=(str(storage["databaseUrl"]) if storage.get("databaseUrl") else None),
        # Features
        feature_dev_core_profile_select=bool(features.get("devCoreProfileSelect", True)),
        feature_letters_enabled=bool(features.get("lettersEnabled", True)),
        feature_llm_copywriting_enabled=bool(features.get("llmCopywritingEnabled", False)),
        feature_tts_task_enabled=bool(features.get("ttsTaskEnabled", False)),
    )
