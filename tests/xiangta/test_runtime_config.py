"""
Runtime Config tests for C2: layered config (default → runtime.json → env override).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.xiangta.config.runtime_config import (
    XiangTaRuntimeConfig,
    load_runtime_config,
    _DEFAULT_CONFIG,
    _deep_merge,
    _parse_bool,
    _sanitize_timeout,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_runtime_json(tmp_path: Path, content: dict) -> Path:
    p = tmp_path / "runtime.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(content, f)
    return p


# ── Bool parsing ────────────────────────────────────────────────────────────

class TestParseBool:
    def test_true_values(self):
        for v in ["true", "True", "TRUE", "1", "yes", "on"]:
            assert _parse_bool(v) is True

    def test_false_values(self):
        for v in ["false", "False", "FALSE", "0", "no", "off"]:
            assert _parse_bool(v) is False

    def test_invalid_returns_none(self):
        assert _parse_bool("maybe") is None
        assert _parse_bool("") is None
        assert _parse_bool("invalid") is None


# ── Sanitize timeout ────────────────────────────────────────────────────────

class TestSanitizeTimeout:
    def test_positive_value(self):
        assert _sanitize_timeout(15.0) == 15.0
        assert _sanitize_timeout(1.0) == 1.0

    def test_zero_or_negative_returns_default(self):
        assert _sanitize_timeout(0.0) == 20.0
        assert _sanitize_timeout(-5.0) == 20.0

    def test_none_returns_default(self):
        assert _sanitize_timeout(None) == 20.0


# ── Deep merge ─────────────────────────────────────────────────────────────

class TestDeepMerge:
    def test_simple_override(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"core": {"enabled": False, "baseUrl": ""}}
        override = {"core": {"enabled": True}}
        result = _deep_merge(base, override)
        assert result == {"core": {"enabled": True, "baseUrl": ""}}


# ── Default config ─────────────────────────────────────────────────────────

class TestDefaultConfig:
    def test_core_defaults_to_disabled(self):
        """Without env or runtime.json, core should be disabled."""
        cfg = load_runtime_config()
        assert cfg.core_enabled is False
        assert cfg.core_base_url is None

    def test_tts_defaults(self):
        cfg = load_runtime_config()
        assert cfg.tts_mode == "sync"
        assert cfg.tts_queue_enabled is False
        assert cfg.tts_max_concurrent == 1

    def test_copywriting_defaults(self):
        cfg = load_runtime_config()
        assert cfg.copywriting_mode == "template"
        assert cfg.copywriting_fallback_to_template is True

    def test_no_real_provider_keys_in_source(self):
        """runtime_config.py must not reference real Provider API key names."""
        import inspect
        import importlib
        src = inspect.getsource(importlib.import_module("src.xiangta.config.runtime_config"))
        for token in ["MINIMAX_API_KEY", "MIMO_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]:
            assert token not in src, f"runtime_config.py must not contain {token}"


# ── Env var overrides ─────────────────────────────────────────────────────

class TestEnvOverrides:
    def teardown_method(self):
        # Clean up env vars after each test
        for key in [
            "XIANGTA_CORE_BASE_URL",
            "XIANGTA_CORE_TIMEOUT_SECS",
            "XIANGTA_CORE_ENABLED",
            "XIANGTA_COPYWRITING_MODE",
            "XIANGTA_COPYWRITING_PROVIDER",
            "XIANGTA_COPYWRITING_TIMEOUT_SECS",
            "XIANGTA_COPYWRITING_FALLBACK_TO_TEMPLATE",
            "XIANGTA_TTS_MODE",
            "XIANGTA_TTS_MAX_CONCURRENT",
            "XIANGTA_TTS_QUEUE_ENABLED",
            "XIANGTA_TTS_TIMEOUT_SECS",
            "XIANGTA_STORAGE_TYPE",
            "XIANGTA_STORAGE_DATABASE_URL",
            "XIANGTA_FEATURE_DEV_CORE_PROFILE_SELECT",
            "XIANGTA_FEATURE_LETTERS_ENABLED",
            "XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED",
            "XIANGTA_FEATURE_TTS_TASK_ENABLED",
        ]:
            os.environ.pop(key, None)

    def test_xiangta_core_base_url_enables_core(self):
        """Setting XIANGTA_CORE_BASE_URL enables core even if runtime.json has enabled=false."""
        os.environ["XIANGTA_CORE_BASE_URL"] = "http://127.0.0.1:8000"
        cfg = load_runtime_config()
        assert cfg.core_enabled is True
        assert cfg.core_base_url == "http://127.0.0.1:8000"

    def test_xiangta_core_base_url_overrides_runtime_json_url(self):
        """XIANGTA_CORE_BASE_URL overrides baseUrl in runtime.json."""
        os.environ["XIANGTA_CORE_BASE_URL"] = "http://127.0.0.1:9000"
        cfg = load_runtime_config()
        assert cfg.core_base_url == "http://127.0.0.1:9000"

    def test_xiangta_core_timeout_overrides(self):
        """XIANGTA_CORE_TIMEOUT_SECS overrides runtime.json."""
        os.environ["XIANGTA_CORE_TIMEOUT_SECS"] = "25"
        cfg = load_runtime_config()
        assert cfg.core_timeout_secs == 25.0

    def test_xiangta_core_timeout_invalid_falls_back(self):
        """Invalid XIANGTA_CORE_TIMEOUT_SECS falls back to default 20."""
        os.environ["XIANGTA_CORE_TIMEOUT_SECS"] = "bad-value"
        cfg = load_runtime_config()
        assert cfg.core_timeout_secs == 20.0

        os.environ["XIANGTA_CORE_TIMEOUT_SECS"] = "0"
        cfg2 = load_runtime_config()
        assert cfg2.core_timeout_secs == 20.0

    def test_xiangta_tts_queue_enabled_true(self):
        """XIANGTA_TTS_QUEUE_ENABLED=true enables queue."""
        os.environ["XIANGTA_TTS_QUEUE_ENABLED"] = "true"
        cfg = load_runtime_config()
        assert cfg.tts_queue_enabled is True

    def test_xiangta_tts_queue_enabled_false_via_0(self):
        """XIANGTA_TTS_QUEUE_ENABLED=0 disables queue."""
        os.environ["XIANGTA_TTS_QUEUE_ENABLED"] = "0"
        cfg = load_runtime_config()
        assert cfg.tts_queue_enabled is False

    def test_xiangta_tts_queue_enabled_yes(self):
        """XIANGTA_TTS_QUEUE_ENABLED=yes works."""
        os.environ["XIANGTA_TTS_QUEUE_ENABLED"] = "yes"
        cfg = load_runtime_config()
        assert cfg.tts_queue_enabled is True

    def test_xiangta_copywriting_mode_override(self):
        """XIANGTA_COPYWRITING_MODE overrides default."""
        os.environ["XIANGTA_COPYWRITING_MODE"] = "llm"
        cfg = load_runtime_config()
        assert cfg.copywriting_mode == "llm"

    def test_xiangta_feature_flags(self):
        """XIANGTA_FEATURE_LETTERS_ENABLED=false disables letters."""
        os.environ["XIANGTA_FEATURE_LETTERS_ENABLED"] = "false"
        cfg = load_runtime_config()
        assert cfg.feature_letters_enabled is False

    def test_backward_compatible_core_fields(self):
        """Existing code using core_base_url / core_timeout_secs still works."""
        os.environ["XIANGTA_CORE_BASE_URL"] = "http://127.0.0.1:8000"
        os.environ["XIANGTA_CORE_TIMEOUT_SECS"] = "30"
        cfg = load_runtime_config()
        assert cfg.core_base_url == "http://127.0.0.1:8000"
        assert cfg.core_timeout_secs == 30.0


# ── Runtime JSON loading ─────────────────────────────────────────────────

class TestRuntimeJsonLoading:
    """Test loading from a temporary runtime.json file."""

    def test_runtime_json_with_core_enabled(self, monkeypatch):
        """runtime.json with core.enabled=true and baseUrl sets core_enabled=true."""
        import src.xiangta.config.runtime_config as rc_module
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            p = _make_runtime_json(tmp_path, {
                "core": {
                    "enabled": True,
                    "baseUrl": "http://127.0.0.1:8000",
                    "timeoutSecs": 15,
                }
            })
            monkeypatch.setattr(rc_module, "_RUNTIME_JSON_PATH", p)
            cfg = load_runtime_config()
            assert cfg.core_enabled is True
            assert cfg.core_base_url == "http://127.0.0.1:8000"
            assert cfg.core_timeout_secs == 15.0

    def test_runtime_json_with_core_disabled(self, monkeypatch):
        """runtime.json with core.enabled=false and empty baseUrl sets core_base_url=None."""
        import src.xiangta.config.runtime_config as rc_module
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            p = _make_runtime_json(tmp_path, {
                "core": {
                    "enabled": False,
                    "baseUrl": "",
                    "timeoutSecs": 20,
                }
            })
            monkeypatch.setattr(rc_module, "_RUNTIME_JSON_PATH", p)
            cfg = load_runtime_config()
            assert cfg.core_enabled is False
            assert cfg.core_base_url is None

    def test_runtime_json_full_config(self, monkeypatch):
        """runtime.json can set all config sections."""
        import src.xiangta.config.runtime_config as rc_module
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            p = _make_runtime_json(tmp_path, {
                "core": {
                    "enabled": True,
                    "baseUrl": "http://127.0.0.1:8000",
                    "timeoutSecs": 15,
                },
                "copywriting": {
                    "mode": "llm",
                    "provider": "minimax",
                    "timeoutSecs": 30,
                    "fallbackToTemplate": True,
                },
                "tts": {
                    "mode": "async",
                    "maxConcurrent": 2,
                    "queueEnabled": True,
                    "timeoutSecs": 60,
                },
                "storage": {
                    "type": "sqlite",
                    "databaseUrl": "sqlite:///./xiangta.db",
                },
                "features": {
                    "devCoreProfileSelect": False,
                    "lettersEnabled": True,
                    "llmCopywritingEnabled": True,
                    "ttsTaskEnabled": True,
                },
            })
            monkeypatch.setattr(rc_module, "_RUNTIME_JSON_PATH", p)
            cfg = load_runtime_config()
            assert cfg.core_enabled is True
            assert cfg.core_base_url == "http://127.0.0.1:8000"
            assert cfg.core_timeout_secs == 15.0
            assert cfg.copywriting_mode == "llm"
            assert cfg.copywriting_provider == "minimax"
            assert cfg.tts_mode == "async"
            assert cfg.tts_max_concurrent == 2
            assert cfg.tts_queue_enabled is True
            assert cfg.storage_type == "sqlite"
            assert cfg.storage_database_url == "sqlite:///./xiangta.db"
            assert cfg.feature_dev_core_profile_select is False
            assert cfg.feature_llm_copywriting_enabled is True
            assert cfg.feature_tts_task_enabled is True

    def test_env_overrides_runtime_json(self, monkeypatch):
        """Env vars override runtime.json values."""
        import src.xiangta.config.runtime_config as rc_module
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            p = _make_runtime_json(tmp_path, {
                "core": {
                    "enabled": False,
                    "baseUrl": "http://wrong:8000",
                    "timeoutSecs": 99,
                }
            })
            monkeypatch.setattr(rc_module, "_RUNTIME_JSON_PATH", p)
            os.environ["XIANGTA_CORE_BASE_URL"] = "http://127.0.0.1:9000"
            os.environ["XIANGTA_CORE_TIMEOUT_SECS"] = "25"
            try:
                cfg = load_runtime_config()
                assert cfg.core_base_url == "http://127.0.0.1:9000"
                assert cfg.core_timeout_secs == 25.0
            finally:
                os.environ.pop("XIANGTA_CORE_BASE_URL", None)
                os.environ.pop("XIANGTA_CORE_TIMEOUT_SECS", None)

    def test_missing_runtime_json_returns_defaults(self, monkeypatch):
        """Missing runtime.json uses defaults only."""
        import src.xiangta.config.runtime_config as rc_module
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td) / "nonexistent.json"
            monkeypatch.setattr(rc_module, "_RUNTIME_JSON_PATH", tmp_path)
            cfg = load_runtime_config()
            assert cfg.core_enabled is False
            assert cfg.core_base_url is None
            assert cfg.tts_mode == "sync"

    def test_corrupt_runtime_json_returns_defaults_and_logs_warning(self, monkeypatch, caplog):
        """Corrupt runtime.json returns defaults and emits a warning log."""
        import src.xiangta.config.runtime_config as rc_module
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td) / "corrupt_runtime.json"
            tmp_path.write_text("{ invalid json content", encoding="utf-8")
            monkeypatch.setattr(rc_module, "_RUNTIME_JSON_PATH", tmp_path)
            cfg = load_runtime_config()
            # Should fall back to defaults (core disabled)
            assert cfg.core_enabled is False
            assert cfg.core_base_url is None
            # Warning should be logged
            assert len(caplog.records) >= 1
            assert any(
                "Failed to load" in r.message or "corrupt_runtime.json" in r.message
                for r in caplog.records
            )
