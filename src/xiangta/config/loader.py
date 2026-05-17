"""
Config Loader — 统一从 configs/*.json 读取，带 lru_cache。

所有配置读取集中于此，其他服务/模块通过本模块函数获取配置，
不直接操作文件路径或 json.load。

reload_all() 供测试使用，清除所有缓存以重新读取。
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CONFIGS_DIR = Path(__file__).parent.parent / "configs"


def _load_file(name: str) -> list[dict]:
    with open(_CONFIGS_DIR / name, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_recipients() -> list[dict]:
    return _load_file("recipients.json")


@lru_cache(maxsize=1)
def load_scenes() -> list[dict]:
    return _load_file("scenes.json")


@lru_cache(maxsize=1)
def load_voice_presets() -> list[dict]:
    return _load_file("voice_presets.json")


@lru_cache(maxsize=1)
def load_tone_presets() -> list[dict]:
    return _load_file("tone_presets.json")


def reload_all() -> None:
    """清除全部 lru_cache，强制下次调用重新读取文件。供测试使用。"""
    load_recipients.cache_clear()
    load_scenes.cache_clear()
    load_voice_presets.cache_clear()
    load_tone_presets.cache_clear()
