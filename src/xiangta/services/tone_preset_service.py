"""
TonePresetService — 产品 tone ID 到 tone 配置的解析服务。

职责：
  - 依赖 ProductConfigRepository
  - 不直接读 JSON 路径
  - 不调用 Core / Provider
"""
from __future__ import annotations

from src.xiangta.config.product_config_models import TonePreset
from src.xiangta.config.product_config_repository import (
    ProductConfigRepository,
    TonePresetNotFound as RepoTonePresetNotFound,
)


class TonePresetError(Exception):
    """tone preset 解析失败。"""


class TonePresetDisabled(TonePresetError):
    """tone preset 已禁用。"""


class TonePresetService:
    def __init__(self, config_repository: ProductConfigRepository) -> None:
        self._config_repository = config_repository

    def resolve(self, tone_id: str) -> TonePreset:
        try:
            tone = self._config_repository.get_tone_preset(tone_id)
        except RepoTonePresetNotFound as exc:
            raise RepoTonePresetNotFound(str(exc)) from exc

        if not tone.enabled:
            raise TonePresetDisabled(f"tone '{tone_id}' 已禁用")
        return tone
