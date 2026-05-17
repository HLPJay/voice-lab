"""
Preset Mapper — 产品概念到 Core 参数的映射层。

前端传入：voicePreset（如 "female-gentle"）、tone（如 "restrained"）
本模块输出：voice_id、model_id、speed、sample_rate 等 Core 参数

前端永远不感知底层 Core 参数。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIGS_DIR = Path(__file__).parent.parent / "configs"


def _load(name: str) -> dict:
    # TODO(P17-A1): 加载后缓存，避免每次请求读磁盘
    with open(_CONFIGS_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class PresetMapper:
    """将产品预设 ID 解析为 voice_lab_gateway 所需的 Core 参数字典。"""

    def resolve_voice(self, voice_preset_id: str, tone_id: str) -> dict[str, Any]:
        """
        Args:
            voice_preset_id: e.g. "female-gentle"
            tone_id:         e.g. "restrained"

        Returns:
            Core 参数字典，如 {"voice_id": "...", "model_id": "...", "speed": 0.85, "sample_rate": 32000}
        """
        # TODO(P17-A1): 读取 configs/voice_presets.json 和 configs/tone_presets.json，
        #               合并为 Core 参数
        raise NotImplementedError
