"""
Preset Mapper — 产品预设 → CoreBindingRequest。

职责边界：
  - 输入：voicePreset ID（如 "female-gentle"）、tone ID（如 "restrained"）
  - 输出：CoreBindingRequest，仅包含产品层稳定字段

CoreBindingRequest 不包含任何 Provider 参数（不含 voice_id、model_id、sample_rate、bitrate）。
Provider-specific 参数的解析责任由 voice_lab_gateway 持有，Product Server 不参与。

配置读取委托给 config.loader，不直接操作文件路径。
"""
from __future__ import annotations

from typing import Any

from src.xiangta.config import loader as _loader


class PresetMappingError(ValueError):
    """voicePreset 或 tone 配置不合法或不存在时抛出。"""
    pass


class PresetMapper:
    """
    将产品预设 ID 解析为 CoreBindingRequest。

    CoreBindingRequest 只包含产品语义：
      core_binding_key, voice_preset, tone, tone_hint, enabled

    不返回 voice_id, model_id, sample_rate, bitrate 等 Provider-specific 参数。
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
              "core_binding_key": str,
              "voice_preset": str,
              "tone": str,
              "tone_hint": str,
              "enabled": bool,
            }

        Raises:
            PresetMappingError: 当 preset 不存在、已禁用、或缺少必要字段时。
        """
        voices = _loader.load_voice_presets()
        tones  = _loader.load_tone_presets()

        voice = next((v for v in voices if v.get("id") == voice_preset_id), None)
        if voice is None:
            raise PresetMappingError(f"voicePreset '{voice_preset_id}' 不存在")

        tone = next((t for t in tones if t.get("id") == tone_id), None)
        if tone is None:
            raise PresetMappingError(f"tone '{tone_id}' 不存在")

        if not voice.get("enabled", True):
            raise PresetMappingError(f"voicePreset '{voice_preset_id}' 已禁用")

        if not tone.get("enabled", True):
            raise PresetMappingError(f"tone '{tone_id}' 已禁用")

        core_binding_key = voice.get("core_binding_key", "")
        if not core_binding_key:
            raise PresetMappingError(
                f"voicePreset '{voice_preset_id}' 缺少 core_binding_key"
            )

        tone_hint = tone.get("style_hint", "")
        if not tone_hint:
            raise PresetMappingError(
                f"tone '{tone_id}' 缺少 style_hint"
            )

        return {
            "core_binding_key": core_binding_key,
            "voice_preset":     voice["id"],
            "tone":             tone["id"],
            "tone_hint":        tone_hint,
            "enabled":          True,
        }
