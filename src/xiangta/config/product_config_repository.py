"""
XiangTa 产品配置仓储。

职责：
  - 只负责读取 XiangTa 产品配置 JSON
  - 不调用 Core
  - 不读取环境变量
  - 不做业务编排
"""
from __future__ import annotations

import json
from pathlib import Path

from src.xiangta.config.product_config_models import (
    ProductLimits,
    ProductVoiceMapping,
    PublicVoicePreset,
    TonePreset,
)


class ProductConfigError(Exception):
    """产品配置读取或解析失败。"""


class VoiceMappingNotFound(ProductConfigError):
    """voice preset 对应的内部映射不存在。"""


class TonePresetNotFound(ProductConfigError):
    """tone preset 不存在。"""


class ProductConfigRepository:
    def __init__(self, configs_dir: Path | None = None) -> None:
        self._configs_dir = configs_dir or (Path(__file__).parent.parent / "configs")

    def list_voice_mappings(self) -> list[ProductVoiceMapping]:
        data = self._load_json_array("voice_mappings.json")
        items = [self._to_voice_mapping(item) for item in data]
        return sorted(items, key=lambda item: item.sort_order)

    def list_public_voice_presets(self) -> list[PublicVoicePreset]:
        public_items: list[PublicVoicePreset] = []
        for item in self.list_voice_mappings():
            if not item.enabled:
                continue
            public_items.append(
                PublicVoicePreset(
                    id=item.id,
                    label=item.label,
                    desc=item.desc,
                    gender_style=item.gender_style,
                    suitable_recipients=list(item.suitable_recipients),
                    recommended_scenes=list(item.recommended_scenes),
                    default_tone=item.default_tone,
                    enabled=item.enabled,
                )
            )
        return public_items

    def get_voice_mapping(self, voice_preset_id: str) -> ProductVoiceMapping:
        for item in self.list_voice_mappings():
            if item.id == voice_preset_id:
                return item
        raise VoiceMappingNotFound(f"voice mapping '{voice_preset_id}' 不存在")

    def list_tone_presets(self) -> list[TonePreset]:
        data = self._load_json_array("tone_presets.json")
        items = [self._to_tone_preset(item, index) for index, item in enumerate(data)]
        return sorted(items, key=lambda item: item.sort_order)

    def get_tone_preset(self, tone_id: str) -> TonePreset:
        for item in self.list_tone_presets():
            if item.id == tone_id:
                return item
        raise TonePresetNotFound(f"tone preset '{tone_id}' 不存在")

    def list_recipients(self) -> list[dict]:
        return self._load_json_array("recipients.json")

    def list_scenes(self) -> list[dict]:
        return self._load_json_array("scenes.json")

    def get_limits(self) -> ProductLimits:
        return ProductLimits()

    def _load_json_array(self, filename: str) -> list[dict]:
        path = self._configs_dir / filename
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ProductConfigError(f"{filename} 应为 JSON 数组")
        return data

    def _to_voice_mapping(self, item: dict) -> ProductVoiceMapping:
        return ProductVoiceMapping(
            id=str(item.get("id", "")),
            label=str(item.get("label", "")),
            desc=str(item.get("desc", "")),
            gender_style=item.get("genderStyle"),
            suitable_recipients=list(item.get("suitableRecipients", [])),
            recommended_scenes=list(item.get("recommendedScenes", [])),
            default_tone=str(item.get("defaultTone", "")),
            enabled=bool(item.get("enabled", True)),
            sort_order=int(item.get("sortOrder", 0)),
            core_profile_id=str(item.get("coreProfileId", "")),
            provider_policy=item.get("providerPolicy"),
            render_overrides=dict(item.get("renderOverrides", {})),
            notes=item.get("notes"),
        )

    def _to_tone_preset(self, item: dict, index: int) -> TonePreset:
        return TonePreset(
            id=str(item.get("id", "")),
            label=str(item.get("label", "")),
            desc=str(item.get("desc", "")),
            style_hint=str(item.get("style_hint", "")),
            copywriting_style=item.get("copywriting_style"),
            render_overrides=dict(item.get("render_overrides", {})),
            enabled=bool(item.get("enabled", True)),
            sort_order=int(item.get("sort_order", index)),
        )

