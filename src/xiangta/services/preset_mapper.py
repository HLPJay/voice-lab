"""
Preset Mapper — 产品预设 → CoreBindingRequest。

职责边界：
  - 输入：voicePreset ID（如 "female-gentle"）、tone ID（如 "restrained"）
  - 输出：CoreBindingRequest，仅包含产品层稳定字段

CoreBindingRequest 不包含任何 Provider 参数（不含 voice_id、model_id、sample_rate、bitrate）。
Provider-specific 参数的解析责任由 voice_lab_gateway 持有，Product Server 不参与。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIGS_DIR = Path(__file__).parent.parent / "configs"


def _load(name: str) -> list[dict]:
    # TODO(P17-A1): 加载后缓存，避免每次请求读磁盘
    with open(_CONFIGS_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class PresetMapper:
    """
    将产品预设 ID 解析为 CoreBindingRequest。

    CoreBindingRequest 是 XiangTa Product Server 与 Voice Lab Gateway 之间的稳定边界，
    只包含产品语义，不包含任何 Provider-specific 参数。
    """

    def resolve_binding(self, voice_preset_id: str, tone_id: str) -> dict[str, Any]:
        """Resolve product-level voice/tone preset into a stable CoreBindingRequest.

        This method must not return provider-specific params such as:
        voice_id, model_id, sample_rate, bitrate, api_key.

        Args:
            voice_preset_id: e.g. "female-gentle"
            tone_id:         e.g. "restrained"

        Returns:
            CoreBindingRequest:
            {
              "core_binding_key": str,   # 声线的稳定 binding key（如 "xiangta_female_gentle"）
              "voice_preset": str,       # 原始 preset ID
              "tone": str,               # 原始 tone ID
              "tone_hint": str,          # 产品语义风格提示（如 "calm", "soft"）
              "enabled": bool,
            }
        """
        # TODO(P17-A1): 读取 configs/voice_presets.json 和 configs/tone_presets.json，
        #               组合成 CoreBindingRequest
        raise NotImplementedError
