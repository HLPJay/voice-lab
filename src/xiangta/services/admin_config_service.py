"""
AdminConfigService — thin wrapper around ProductConfigWriter.

职责：
  - 委托给 ProductConfigWriter，隔离 API 层与文件写入层
  - 不持有 HTTP / env / app.* 依赖
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.config.product_config_writer import ProductConfigWriter


class AdminConfigService:

    def __init__(self, writer: "ProductConfigWriter") -> None:
        self._writer = writer

    def update_voice_mapping(self, id: str, data: dict) -> dict:
        return self._writer.update_voice_mapping(id, data)

    def toggle_voice_mapping_enabled(self, id: str, enabled: bool) -> dict:
        return self._writer.toggle_voice_mapping_enabled(id, enabled)

    def update_tone_preset(self, id: str, data: dict) -> dict:
        return self._writer.update_tone_preset(id, data)

    def toggle_tone_preset_enabled(self, id: str, enabled: bool) -> dict:
        return self._writer.toggle_tone_preset_enabled(id, enabled)
