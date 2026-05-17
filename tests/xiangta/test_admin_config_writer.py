"""
P17-XIANGTA-ADMIN-CONFIG-B4-3 — ProductConfigWriter 单元测试

所有测试使用 tmp_path，不修改 src/xiangta/configs/*.json。
"""
import json
import pytest

from src.xiangta.config.product_config_writer import (
    ConfigNotFoundError,
    ConfigWriteFailedError,
    InvalidCoreProfileError,
    InvalidConfigInputError,
    InvalidRenderOverrideError,
    ProductConfigWriter,
)

# ── 测试夹具：最小 JSON 文件 ──────────────────────────────────────────────────

_VOICE_MAPPINGS = [
    {
        "id": "vm-1",
        "label": "测试声音",
        "desc": "测试描述",
        "genderStyle": "female",
        "suitableRecipients": ["lover"],
        "recommendedScenes": ["miss"],
        "defaultTone": "gentle",
        "enabled": True,
        "sortOrder": 10,
        "coreProfileId": "core-profile-001",
        "providerPolicy": "default",
        "renderOverrides": {},
        "notes": None,
    }
]

_TONE_PRESETS = [
    {
        "id": "tp-1",
        "label": "克制",
        "desc": "少一点情绪",
        "style_hint": "calm",
        "enabled": True,
    }
]


@pytest.fixture
def writer(tmp_path):
    (tmp_path / "voice_mappings.json").write_text(
        json.dumps(_VOICE_MAPPINGS, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "tone_presets.json").write_text(
        json.dumps(_TONE_PRESETS, ensure_ascii=False), encoding="utf-8"
    )
    return ProductConfigWriter(config_dir=tmp_path)


# ── update_voice_mapping ──────────────────────────────────────────────────────

class TestUpdateVoiceMapping:

    def test_update_label_returns_updated_item(self, writer):
        result = writer.update_voice_mapping("vm-1", {"label": "新标签"})
        assert result["label"] == "新标签"

    def test_update_persists_to_file(self, writer, tmp_path):
        writer.update_voice_mapping("vm-1", {"label": "持久化"})
        data = json.loads((tmp_path / "voice_mappings.json").read_text(encoding="utf-8"))
        assert data[0]["label"] == "持久化"

    def test_update_does_not_change_id(self, writer):
        result = writer.update_voice_mapping("vm-1", {"label": "x"})
        assert result["id"] == "vm-1"

    def test_update_coreProfileId(self, writer):
        result = writer.update_voice_mapping("vm-1", {"coreProfileId": "new-profile-abc"})
        assert result["coreProfileId"] == "new-profile-abc"

    def test_update_renderOverrides(self, writer):
        result = writer.update_voice_mapping("vm-1", {"renderOverrides": {"speed": 1.2}})
        assert result["renderOverrides"] == {"speed": 1.2}

    def test_update_creates_backup_file(self, writer, tmp_path):
        writer.update_voice_mapping("vm-1", {"label": "bak"})
        assert (tmp_path / "voice_mappings.json.bak").exists()

    def test_not_found_raises(self, writer):
        with pytest.raises(ConfigNotFoundError):
            writer.update_voice_mapping("no-such-id", {"label": "x"})

    def test_forbidden_field_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"api_key": "secret"})

    def test_invalid_render_override_key_raises(self, writer):
        with pytest.raises(InvalidRenderOverrideError):
            writer.update_voice_mapping("vm-1", {"renderOverrides": {"illegal_key": 1}})

    def test_render_overrides_must_be_dict(self, writer):
        with pytest.raises(InvalidRenderOverrideError):
            writer.update_voice_mapping("vm-1", {"renderOverrides": "not_a_dict"})

    def test_label_empty_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"label": "   "})

    def test_label_too_long_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"label": "x" * 51})

    def test_desc_too_long_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"desc": "x" * 201})

    def test_gender_style_invalid_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"genderStyle": "other"})

    def test_enabled_must_be_bool(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"enabled": "yes"})

    def test_sort_order_negative_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"sortOrder": -1})

    def test_core_profile_id_empty_raises(self, writer):
        with pytest.raises(InvalidCoreProfileError):
            writer.update_voice_mapping("vm-1", {"coreProfileId": "  "})

    def test_core_profile_id_placeholder_raises(self, writer):
        with pytest.raises(InvalidCoreProfileError):
            writer.update_voice_mapping("vm-1", {"coreProfileId": "<placeholder>"})

    def test_core_profile_id_leading_space_raises(self, writer):
        with pytest.raises(InvalidCoreProfileError):
            writer.update_voice_mapping("vm-1", {"coreProfileId": " abc"})

    def test_provider_policy_invalid_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"providerPolicy": "unknown"})

    def test_notes_too_long_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_voice_mapping("vm-1", {"notes": "x" * 501})


# ── toggle_voice_mapping_enabled ─────────────────────────────────────────────

class TestToggleVoiceMappingEnabled:

    def test_toggle_false(self, writer):
        result = writer.toggle_voice_mapping_enabled("vm-1", False)
        assert result["enabled"] is False

    def test_toggle_true(self, writer):
        writer.toggle_voice_mapping_enabled("vm-1", False)
        result = writer.toggle_voice_mapping_enabled("vm-1", True)
        assert result["enabled"] is True

    def test_not_found_raises(self, writer):
        with pytest.raises(ConfigNotFoundError):
            writer.toggle_voice_mapping_enabled("bad-id", True)


# ── update_tone_preset ────────────────────────────────────────────────────────

class TestUpdateTonePreset:

    def test_update_label(self, writer):
        result = writer.update_tone_preset("tp-1", {"label": "新克制"})
        assert result["label"] == "新克制"

    def test_returns_camel_case(self, writer):
        result = writer.update_tone_preset("tp-1", {"styleHint": "strong"})
        assert "styleHint" in result
        assert result["styleHint"] == "strong"

    def test_update_render_overrides(self, writer):
        result = writer.update_tone_preset("tp-1", {"renderOverrides": {"speed": 0.9}})
        assert result["renderOverrides"] == {"speed": 0.9}

    def test_backfills_sort_order(self, writer):
        result = writer.update_tone_preset("tp-1", {"label": "x"})
        assert "sortOrder" in result
        assert isinstance(result["sortOrder"], int)

    def test_backfills_render_overrides(self, writer):
        result = writer.update_tone_preset("tp-1", {"label": "x"})
        assert "renderOverrides" in result
        assert isinstance(result["renderOverrides"], dict)

    def test_persists_to_file(self, writer, tmp_path):
        writer.update_tone_preset("tp-1", {"label": "保存"})
        data = json.loads((tmp_path / "tone_presets.json").read_text(encoding="utf-8"))
        assert data[0]["label"] == "保存"

    def test_snake_case_stored_in_file(self, writer, tmp_path):
        writer.update_tone_preset("tp-1", {"styleHint": "bright"})
        data = json.loads((tmp_path / "tone_presets.json").read_text(encoding="utf-8"))
        assert data[0].get("style_hint") == "bright"
        assert "styleHint" not in data[0]

    def test_not_found_raises(self, writer):
        with pytest.raises(ConfigNotFoundError):
            writer.update_tone_preset("no-id", {"label": "x"})

    def test_forbidden_field_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_tone_preset("tp-1", {"coreProfileId": "x"})

    def test_invalid_render_override_raises(self, writer):
        with pytest.raises(InvalidRenderOverrideError):
            writer.update_tone_preset("tp-1", {"renderOverrides": {"bad_key": 1}})

    def test_label_empty_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_tone_preset("tp-1", {"label": ""})

    def test_label_too_long_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_tone_preset("tp-1", {"label": "x" * 51})

    def test_desc_empty_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_tone_preset("tp-1", {"desc": "  "})

    def test_enabled_must_be_bool(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_tone_preset("tp-1", {"enabled": 1})

    def test_sort_order_negative_raises(self, writer):
        with pytest.raises(InvalidConfigInputError):
            writer.update_tone_preset("tp-1", {"sortOrder": -5})


# ── toggle_tone_preset_enabled ────────────────────────────────────────────────

class TestToggleTonePresetEnabled:

    def test_toggle_false(self, writer):
        result = writer.toggle_tone_preset_enabled("tp-1", False)
        assert result["enabled"] is False

    def test_toggle_true(self, writer):
        writer.toggle_tone_preset_enabled("tp-1", False)
        result = writer.toggle_tone_preset_enabled("tp-1", True)
        assert result["enabled"] is True

    def test_not_found_raises(self, writer):
        with pytest.raises(ConfigNotFoundError):
            writer.toggle_tone_preset_enabled("bad-id", False)


# ── atomic write — tmp file cleanup ──────────────────────────────────────────

class TestAtomicWrite:

    def test_no_tmp_file_left_after_success(self, writer, tmp_path):
        writer.update_voice_mapping("vm-1", {"label": "done"})
        assert not (tmp_path / "voice_mappings.json.tmp").exists()

    def test_sorted_by_sort_order(self, writer, tmp_path):
        # add second item with lower sortOrder
        second = {**_VOICE_MAPPINGS[0], "id": "vm-2", "sortOrder": 5}
        data = _VOICE_MAPPINGS + [second]
        (tmp_path / "voice_mappings.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        w = ProductConfigWriter(config_dir=tmp_path)
        w.update_voice_mapping("vm-1", {"label": "x"})
        saved = json.loads((tmp_path / "voice_mappings.json").read_text(encoding="utf-8"))
        assert saved[0]["id"] == "vm-2"
        assert saved[1]["id"] == "vm-1"
