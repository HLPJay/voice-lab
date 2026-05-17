"""
TonePresetService - resolve product tone IDs into XiangTa tone presets.

Responsibilities:
  - depends on ProductConfigRepository
  - does not read JSON paths directly
  - does not call Core or any Provider
"""
from __future__ import annotations

from src.xiangta.config.product_config_models import TonePreset
from src.xiangta.config.product_config_repository import (
    ProductConfigRepository,
    TonePresetNotFound as RepoTonePresetNotFound,
)


class TonePresetError(Exception):
    """Base error for tone preset resolution failures."""


class TonePresetNotFound(TonePresetError):
    """Raised when the requested tone preset does not exist."""


class TonePresetDisabled(TonePresetError):
    """Raised when the requested tone preset is disabled."""


class TonePresetService:
    def __init__(self, config_repository: ProductConfigRepository) -> None:
        self._config_repository = config_repository

    def resolve(self, tone_id: str) -> TonePreset:
        try:
            tone = self._config_repository.get_tone_preset(tone_id)
        except RepoTonePresetNotFound as exc:
            raise TonePresetNotFound(str(exc)) from exc

        if not tone.enabled:
            raise TonePresetDisabled(f"tone '{tone_id}' is disabled")
        return tone
