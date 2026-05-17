"""
XiangTa Admin Config Writer.

职责：
  - 原子写 JSON 配置文件（temp → backup → rename）
  - 校验禁止字段和 renderOverrides 白名单
  - 校验 coreProfileId 格式
  - threading.Lock 保护写操作
  - 不引入 app 模块
  - 不读取 env
  - 不调用 Core / Provider
"""
from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path
from typing import Any


# ── 异常 ──────────────────────────────────────────────────────────────────────

class ProductConfigWriteError(Exception):
    """Base error for admin config write failures."""


class ConfigNotFoundError(ProductConfigWriteError):
    """指定 id 的配置项不存在。"""


class InvalidConfigInputError(ProductConfigWriteError):
    """请求字段格式错误或缺失必填字段。"""


class InvalidRenderOverrideError(ProductConfigWriteError):
    """renderOverrides 包含非白名单字段。"""


class InvalidCoreProfileError(ProductConfigWriteError):
    """coreProfileId 格式非法。"""


class ConfigWriteFailedError(ProductConfigWriteError):
    """文件写入失败（磁盘 / 权限）。"""


# ── 常量 ──────────────────────────────────────────────────────────────────────

_VOICE_MAPPING_FORBIDDEN: frozenset[str] = frozenset({
    "api_key", "minimax_api_key", "mimo_api_key", "provider_api_key",
    "provider_voice_id", "binding_id", "params_json", "model",
    "voice_id", "model_id", "sample_rate", "bitrate", "secret",
    "env", "stack_trace", "raw_config",
})

_TONE_PRESET_FORBIDDEN: frozenset[str] = frozenset({
    "coreProfileId", "provider", "model", "provider_voice_id",
    "binding_id", "params_json", "api_key",
})

_RENDER_OVERRIDES_WHITELIST: frozenset[str] = frozenset({
    "speed", "vol", "pitch", "emotion", "audio_format", "need_subtitle",
})

# Module-level lock shared across all writer instances.
_WRITE_LOCK = threading.Lock()


# ── Writer ────────────────────────────────────────────────────────────────────

class ProductConfigWriter:
    """Atomic JSON config writer with validation and backup."""

    def __init__(self, config_dir: "Path | str | None" = None) -> None:
        if config_dir is None:
            self._config_dir = Path(__file__).parent.parent / "configs"
        else:
            self._config_dir = Path(config_dir)

    # ── Voice Mapping ─────────────────────────────────────────────────────────

    def update_voice_mapping(self, id: str, data: dict) -> dict:
        """Update an existing voice mapping by id. Returns updated item (camelCase)."""
        self._check_forbidden_fields(data, _VOICE_MAPPING_FORBIDDEN)
        if "renderOverrides" in data:
            self._validate_render_overrides(data["renderOverrides"])
        self._validate_voice_mapping_fields(data)
        return self._update_voice_item(id, data, toggle_only=False)

    def toggle_voice_mapping_enabled(self, id: str, enabled: bool) -> dict:
        """Toggle enabled state of an existing voice mapping."""
        return self._update_voice_item(id, {"enabled": enabled}, toggle_only=True)

    # ── Tone Preset ───────────────────────────────────────────────────────────

    def update_tone_preset(self, id: str, data: dict) -> dict:
        """Update an existing tone preset by id. Returns updated item (camelCase)."""
        self._check_forbidden_fields(data, _TONE_PRESET_FORBIDDEN)
        if "renderOverrides" in data:
            self._validate_render_overrides(data["renderOverrides"])
        self._validate_tone_preset_fields(data)
        return self._update_tone_item(id, data, toggle_only=False)

    def toggle_tone_preset_enabled(self, id: str, enabled: bool) -> dict:
        """Toggle enabled state of an existing tone preset."""
        return self._update_tone_item(id, {"enabled": enabled}, toggle_only=True)

    # ── Internal: voice mappings (camelCase JSON) ─────────────────────────────

    def _update_voice_item(self, id: str, data: dict, toggle_only: bool) -> dict:
        path = self._config_dir / "voice_mappings.json"
        with _WRITE_LOCK:
            items = self._read_json(path)
            idx = self._find_index(items, id)

            updated = dict(items[idx])
            if toggle_only:
                updated["enabled"] = data["enabled"]
            else:
                for key, value in data.items():
                    if key != "id":
                        updated[key] = value

            items[idx] = updated
            items = sorted(items, key=lambda x: x.get("sortOrder", 0))
            self._atomic_write(path, items)
            return dict(updated)

    # ── Internal: tone presets (snake_case JSON → camelCase return) ───────────

    def _update_tone_item(self, id: str, data: dict, toggle_only: bool) -> dict:
        path = self._config_dir / "tone_presets.json"
        with _WRITE_LOCK:
            items = self._read_json(path)
            idx = self._find_index(items, id)

            updated = dict(items[idx])
            # GAP-B4-003: backfill missing fields with defaults
            updated.setdefault("sort_order", idx)
            updated.setdefault("render_overrides", {})
            updated.setdefault("copywriting_style", None)

            if toggle_only:
                updated["enabled"] = data["enabled"]
            else:
                # camelCase request → snake_case storage
                _CAMEL_TO_SNAKE = {
                    "label": "label",
                    "desc": "desc",
                    "styleHint": "style_hint",
                    "copywritingStyle": "copywriting_style",
                    "renderOverrides": "render_overrides",
                    "enabled": "enabled",
                    "sortOrder": "sort_order",
                }
                for camel, snake in _CAMEL_TO_SNAKE.items():
                    if camel in data:
                        updated[snake] = data[camel]

            items[idx] = updated
            items = sorted(items, key=lambda x: x.get("sort_order", 0))
            self._atomic_write(path, items)

            return {
                "id": updated["id"],
                "label": updated["label"],
                "desc": updated["desc"],
                "styleHint": updated.get("style_hint", ""),
                "copywritingStyle": updated.get("copywriting_style"),
                "renderOverrides": updated.get("render_overrides", {}),
                "enabled": updated["enabled"],
                "sortOrder": updated.get("sort_order", 0),
            }

    # ── Validation ────────────────────────────────────────────────────────────

    def _check_forbidden_fields(self, data: dict, forbidden: frozenset) -> None:
        bad = set(data.keys()) & forbidden
        if bad:
            raise InvalidConfigInputError(
                f"请求包含禁止字段：{', '.join(sorted(bad))}"
            )

    def _validate_render_overrides(self, overrides: Any) -> None:
        if not isinstance(overrides, dict):
            raise InvalidRenderOverrideError("renderOverrides 必须是 dict")
        bad = set(overrides.keys()) - _RENDER_OVERRIDES_WHITELIST
        if bad:
            raise InvalidRenderOverrideError(
                f"renderOverrides 包含非法字段：{', '.join(sorted(bad))}"
            )

    def _validate_voice_mapping_fields(self, data: dict) -> None:
        if "label" in data:
            v = str(data["label"]).strip()
            if not v:
                raise InvalidConfigInputError("label 不能为空")
            if len(data["label"]) > 50:
                raise InvalidConfigInputError("label 最长 50 字符")
        if "desc" in data:
            v = str(data["desc"]).strip()
            if not v:
                raise InvalidConfigInputError("desc 不能为空")
            if len(data["desc"]) > 200:
                raise InvalidConfigInputError("desc 最长 200 字符")
        if "genderStyle" in data and data["genderStyle"] is not None:
            if data["genderStyle"] not in ("female", "male"):
                raise InvalidConfigInputError("genderStyle 必须是 female / male / null")
        if "enabled" in data and not isinstance(data["enabled"], bool):
            raise InvalidConfigInputError("enabled 必须是 boolean")
        if "sortOrder" in data:
            if not isinstance(data["sortOrder"], int) or data["sortOrder"] < 0:
                raise InvalidConfigInputError("sortOrder 必须是 int >= 0")
        if "coreProfileId" in data:
            self._validate_core_profile_id(data["coreProfileId"])
        if "providerPolicy" in data and data["providerPolicy"] is not None:
            if data["providerPolicy"] not in ("default", "mock"):
                raise InvalidConfigInputError("providerPolicy 只允许 default / mock / null")
        if "notes" in data and data["notes"] is not None:
            if len(str(data["notes"])) > 500:
                raise InvalidConfigInputError("notes 最长 500 字符")

    def _validate_tone_preset_fields(self, data: dict) -> None:
        if "label" in data:
            v = str(data["label"]).strip()
            if not v:
                raise InvalidConfigInputError("label 不能为空")
            if len(data["label"]) > 50:
                raise InvalidConfigInputError("label 最长 50 字符")
        if "desc" in data:
            v = str(data["desc"]).strip()
            if not v:
                raise InvalidConfigInputError("desc 不能为空")
            if len(data["desc"]) > 200:
                raise InvalidConfigInputError("desc 最长 200 字符")
        if "styleHint" in data:
            if not str(data["styleHint"]).strip():
                raise InvalidConfigInputError("styleHint 不能为空")
        if "enabled" in data and not isinstance(data["enabled"], bool):
            raise InvalidConfigInputError("enabled 必须是 boolean")
        if "sortOrder" in data:
            if not isinstance(data["sortOrder"], int) or data["sortOrder"] < 0:
                raise InvalidConfigInputError("sortOrder 必须是 int >= 0")

    def _validate_core_profile_id(self, value: Any) -> None:
        if not value or not str(value).strip():
            raise InvalidCoreProfileError("coreProfileId 不能为空")
        s = str(value)
        if s != s.strip():
            raise InvalidCoreProfileError("coreProfileId 不能包含前后空白")
        if "<" in s or ">" in s:
            raise InvalidCoreProfileError("coreProfileId 不能是占位值（含 < >）")

    # ── I/O helpers ───────────────────────────────────────────────────────────

    def _find_index(self, items: list[dict], id: str) -> int:
        idx = next((i for i, item in enumerate(items) if item.get("id") == id), None)
        if idx is None:
            raise ConfigNotFoundError(f"配置项 '{id}' 不存在")
        return idx

    def _read_json(self, path: Path) -> list[dict]:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ConfigWriteFailedError("读取配置文件失败") from e
        if not isinstance(data, list):
            raise ConfigWriteFailedError(f"{path.name} 应为 JSON 数组")
        return data

    def _atomic_write(self, path: Path, items: list[dict]) -> None:
        tmp_path = Path(str(path) + ".tmp")
        bak_path = Path(str(path) + ".bak")
        content = json.dumps(items, indent=2, ensure_ascii=False)
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            if path.exists():
                shutil.copy2(str(path), str(bak_path))
            os.replace(str(tmp_path), str(path))
        except Exception as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            raise ConfigWriteFailedError("写入配置文件失败") from e
