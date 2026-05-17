"""
VoicePresetMappingService — 产品声线 ID 到内部映射的解析服务。

职责：
  - 依赖 ProductConfigRepository
  - 不直接读 JSON 路径
  - 不调用 Core / Provider
"""
from __future__ import annotations

from src.xiangta.config.product_config_models import ProductVoiceMapping
from src.xiangta.config.product_config_repository import (
    ProductConfigRepository,
    VoiceMappingNotFound,
)


class VoicePresetMappingError(Exception):
    """voice preset 映射解析失败。"""


class VoicePresetNotFound(VoicePresetMappingError):
    """voice preset 不存在。"""


class VoicePresetDisabled(VoicePresetMappingError):
    """voice preset 已禁用。"""


class VoicePresetMappingService:
    def __init__(self, config_repository: ProductConfigRepository) -> None:
        self._config_repository = config_repository

    def resolve(self, voice_preset_id: str) -> ProductVoiceMapping:
        try:
            mapping = self._config_repository.get_voice_mapping(voice_preset_id)
        except VoiceMappingNotFound as exc:
            raise VoicePresetNotFound(str(exc)) from exc

        if not mapping.enabled:
            raise VoicePresetDisabled(f"voicePreset '{voice_preset_id}' 已禁用")
        return mapping
