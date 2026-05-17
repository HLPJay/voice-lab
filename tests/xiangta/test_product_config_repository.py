from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from src.xiangta.config.product_config_models import ProductLimits
from src.xiangta.config.product_config_repository import (
    ProductConfigRepository,
    TonePresetNotFound,
    VoiceMappingNotFound,
)


def _write_json(path: Path, data: list[dict]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@pytest.fixture
def repo_config_dir() -> Path:
    base_dir = Path(__file__).parent / ".tmp_product_config_repository" / uuid4().hex
    configs_dir = base_dir / "configs"
    configs_dir.mkdir(parents=True)
    _write_json(
        configs_dir / "voice_mappings.json",
        [
            {
                "id": "b-item",
                "label": "B",
                "desc": "sorted second",
                "genderStyle": "female",
                "suitableRecipients": ["friend"],
                "recommendedScenes": ["thanks"],
                "defaultTone": "gentle",
                "enabled": True,
                "sortOrder": 20,
                "coreProfileId": "<core_profile_id_from_core_profiles>",
                "providerPolicy": "default",
                "renderOverrides": {},
                "notes": None,
            },
            {
                "id": "disabled-item",
                "label": "Disabled",
                "desc": "should be filtered out",
                "genderStyle": "male",
                "suitableRecipients": ["self"],
                "recommendedScenes": ["night"],
                "defaultTone": "restrained",
                "enabled": False,
                "sortOrder": 5,
                "coreProfileId": "<core_profile_id_from_core_profiles>",
                "providerPolicy": "default",
                "renderOverrides": {},
                "notes": None,
            },
            {
                "id": "a-item",
                "label": "A",
                "desc": "sorted first",
                "genderStyle": "female",
                "suitableRecipients": ["lover"],
                "recommendedScenes": ["miss"],
                "defaultTone": "gentle",
                "enabled": True,
                "sortOrder": 10,
                "coreProfileId": "<core_profile_id_from_core_profiles>",
                "providerPolicy": "default",
                "renderOverrides": {},
                "notes": None,
            },
        ],
    )
    _write_json(
        configs_dir / "tone_presets.json",
        [
            {
                "id": "gentle",
                "label": "温柔",
                "desc": "gentle desc",
                "style_hint": "soft",
                "enabled": True,
            }
        ],
    )
    _write_json(
        configs_dir / "recipients.json",
        [{"id": "lover", "label": "恋人", "hint": "hint", "enabled": True}],
    )
    _write_json(
        configs_dir / "scenes.json",
        [{"id": "miss", "label": "想念", "hint": "hint", "enabled": True}],
    )
    try:
        yield configs_dir
    finally:
        if base_dir.exists():
            for path in sorted(base_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()


class TestProductConfigRepositoryRealFiles:
    def test_list_voice_mappings_reads_json(self):
        repo = ProductConfigRepository()
        items = repo.list_voice_mappings()
        assert items, "voice_mappings.json 应能被读取"

    def test_get_voice_mapping_returns_internal_mapping_with_core_profile_id(self):
        repo = ProductConfigRepository()
        item = repo.get_voice_mapping("female-gentle")
        assert item.id == "female-gentle"
        assert item.core_profile_id == "<core_profile_id_from_core_profiles>"

    def test_get_voice_mapping_unknown_raises(self):
        repo = ProductConfigRepository()
        with pytest.raises(VoiceMappingNotFound):
            repo.get_voice_mapping("unknown")

    def test_list_tone_presets_reads_existing_tone_presets(self):
        repo = ProductConfigRepository()
        items = repo.list_tone_presets()
        assert items, "tone_presets.json 应能被读取"

    def test_get_tone_preset_returns_existing_item(self):
        repo = ProductConfigRepository()
        tone = repo.get_tone_preset("gentle")
        assert tone.id == "gentle"
        assert tone.style_hint == "soft"

    def test_get_tone_preset_unknown_raises(self):
        repo = ProductConfigRepository()
        with pytest.raises(TonePresetNotFound):
            repo.get_tone_preset("unknown")

    def test_list_recipients_reads_existing_json(self):
        repo = ProductConfigRepository()
        items = repo.list_recipients()
        assert items
        assert items[0]["id"] == "lover"

    def test_list_scenes_reads_existing_json(self):
        repo = ProductConfigRepository()
        items = repo.list_scenes()
        assert items
        assert items[0]["id"] == "miss"

    def test_get_limits_returns_default_product_limits(self):
        repo = ProductConfigRepository()
        limits = repo.get_limits()
        assert limits == ProductLimits()


class TestProductConfigRepositoryProjectionAndSorting:
    def test_list_public_voice_presets_hides_core_fields(self, repo_config_dir: Path):
        repo = ProductConfigRepository(configs_dir=repo_config_dir)
        items = repo.list_public_voice_presets()
        assert items
        item_dict = items[0].__dict__
        forbidden = {
            "coreProfileId",
            "core_profile_id",
            "profile_id",
            "provider",
            "model",
            "provider_voice_id",
            "binding_id",
            "params_json",
            "api_key",
        }
        assert forbidden.isdisjoint(item_dict.keys())

    def test_list_public_voice_presets_filters_disabled(self, repo_config_dir: Path):
        repo = ProductConfigRepository(configs_dir=repo_config_dir)
        ids = [item.id for item in repo.list_public_voice_presets()]
        assert "disabled-item" not in ids

    def test_list_public_voice_presets_sorts_by_sort_order(self, repo_config_dir: Path):
        repo = ProductConfigRepository(configs_dir=repo_config_dir)
        ids = [item.id for item in repo.list_public_voice_presets()]
        assert ids == ["a-item", "b-item"]
