"""
XiangTa Runtime Configuration — layered config:
  default → runtime.json → runtime local config → XIANGTA_* env override

只读取 XiangTa 自有运行时配置变量。
默认不读取任何真实 Provider API key；
仅在显式配置 XIANGTA_MINIMAX_COPYWRITING_API_KEY env
  或本地私有 configs/xiangta.runtime.local.json 时读取。
不会将 key 写入可提交的 runtime.json，不会记录日志，不会暴露给前端。
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
# Local private config at project root (gitignored — may contain secrets)
_RUNTIME_LOCAL_JSON_PATH = Path("configs/xiangta.runtime.local.json")


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
    minimax_copywriting_base_url: str | None = None
    minimax_copywriting_model: str | None = None
    minimax_copywriting_endpoint_path: str = "/v1/chat/completions"
    minimax_copywriting_api_key: str | None = None

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

    # Safe repr: never expose apiKey
    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        parts = []
        for field_name in self.__dataclass_fields__:
            if field_name == "minimax_copywriting_api_key":
                parts.append(f"{field_name}=<hidden>")
            else:
                parts.append(f"{field_name}={getattr(self, field_name)!r}")
        return f"{cls_name}({', '.join(parts)})"


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

def _load_runtime_json(path: Path | None = None, *, is_local: bool = False) -> dict:
    """
    Load a runtime JSON config from disk.

    Args:
        path: file path; defaults to _RUNTIME_JSON_PATH.
        is_local: if True, the file is the local private config (may contain secrets).

    Returns merged dict, or empty dict on error / missing file.
    Logs a warning on error but never exposes secret values.
    """
    try:
        p = path or _RUNTIME_JSON_PATH
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:
        kind = "local runtime" if is_local else "runtime"
        logger.warning(
            "Failed to load XiangTa %s config from %s; using previous config: %s",
            kind,
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

    # MiniMax copywriting
    if _get_env("XIANGTA_MINIMAX_COPYWRITING_BASE_URL"):
        config.setdefault("copywriting", {})["minimaxBaseUrl"] = _get_env("XIANGTA_MINIMAX_COPYWRITING_BASE_URL")
    if _get_env("XIANGTA_MINIMAX_COPYWRITING_MODEL"):
        config.setdefault("copywriting", {})["minimaxModel"] = _get_env("XIANGTA_MINIMAX_COPYWRITING_MODEL")
    if _get_env("XIANGTA_MINIMAX_COPYWRITING_ENDPOINT_PATH"):
        config.setdefault("copywriting", {})["minimaxEndpointPath"] = _get_env("XIANGTA_MINIMAX_COPYWRITING_ENDPOINT_PATH")
    # Note: XIANGTA_MINIMAX_COPYWRITING_API_KEY is read directly in return statement (never stored in config dict)

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

    # 3. Overlay runtime local config (gitignored — may contain secrets)
    local_config = _load_runtime_json(_RUNTIME_LOCAL_JSON_PATH, is_local=True)
    config = _deep_merge(config, local_config)

    # 4. Apply env overrides
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

    # MiniMax: nested copywriting.minimax.* preferred over flat minimaxBaseUrl/minimaxModel
    _minimax = copywriting.get("minimax") or {}
    _env_endpoint_path = _get_env("XIANGTA_MINIMAX_COPYWRITING_ENDPOINT_PATH")
    _minimax_base_url = (
        str(_minimax["baseUrl"]) if _minimax.get("baseUrl")
        else (str(copywriting["minimaxBaseUrl"]) if copywriting.get("minimaxBaseUrl") else None)
    )
    _minimax_model = (
        str(_minimax["model"]) if _minimax.get("model")
        else (str(copywriting["minimaxModel"]) if copywriting.get("minimaxModel") else None)
    )
    # Env always wins; then nested local config; then flat local config; then default
    _minimax_endpoint_path = (
        str(_env_endpoint_path) if _env_endpoint_path
        else (str(_minimax["endpointPath"]) if _minimax.get("endpointPath")
        else (str(copywriting["minimaxEndpointPath"]) if copywriting.get("minimaxEndpointPath") else "/v1/chat/completions"))
    )
    # apiKey: read directly from local config file only — never from merged runtime.json
    _local_config_api_key: str | None = None
    try:
        if _RUNTIME_LOCAL_JSON_PATH.exists():
            with open(_RUNTIME_LOCAL_JSON_PATH, encoding="utf-8") as f:
                _local_raw = json.load(f)
            _local_minimax = _local_raw.get("copywriting", {}).get("minimax") or {}
            if _local_minimax.get("apiKey"):
                _local_config_api_key = str(_local_minimax["apiKey"])
    except Exception:
        pass  # silent — don't expose in logs
    _env_api_key = _get_env("XIANGTA_MINIMAX_COPYWRITING_API_KEY")

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
        minimax_copywriting_base_url=_minimax_base_url,
        minimax_copywriting_model=_minimax_model,
        minimax_copywriting_endpoint_path=_minimax_endpoint_path,
        # apiKey: env wins over local config over none
        minimax_copywriting_api_key=_env_api_key or _local_config_api_key,
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
