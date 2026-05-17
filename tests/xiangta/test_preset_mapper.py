"""
P17-XIANGTA-A1 — PresetMapper.resolve_binding 单元测试

验证：
  - 正常路径返回 CoreBindingRequest（含 core_binding_key, tone_hint）
  - 返回结果不包含任何底层 Provider 参数
  - 不存在的 preset 抛 PresetMappingError
  - disabled preset 抛 PresetMappingError
"""
import json
import pytest
from unittest.mock import patch

from src.xiangta.services.preset_mapper import PresetMapper, PresetMappingError
import src.xiangta.services.preset_mapper as _pm_module

# 在任何 mock 生效前保存真实函数引用，供集成测试恢复使用
_REAL_LOAD_VOICES = _pm_module._load_voices
_REAL_LOAD_TONES  = _pm_module._load_tones

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
}

# ── 测试数据 fixtures ──────────────────────────────────────────────────────────

MOCK_VOICES = [
    {
        "id": "female-gentle",
        "name": "温柔女声",
        "desc": "清晰、靠近、稍慢",
        "suitable_recipients": ["lover", "friend", "self"],
        "recommended_scenes": ["miss", "thanks", "night"],
        "default_tone": "gentle",
        "core_binding_key": "xiangta_female_gentle",
        "enabled": True,
    },
    {
        "id": "male-mature",
        "name": "成熟男声",
        "desc": "稳，适合父母",
        "suitable_recipients": ["family"],
        "recommended_scenes": ["thanks", "comfort", "night"],
        "default_tone": "restrained",
        "core_binding_key": "xiangta_male_mature",
        "enabled": False,  # disabled
    },
    {
        "id": "no-key-voice",
        "name": "无 key 声线",
        "desc": "测试用",
        "suitable_recipients": [],
        "recommended_scenes": [],
        "default_tone": "gentle",
        "core_binding_key": "",  # 空 key
        "enabled": True,
    },
]

MOCK_TONES = [
    {
        "id": "gentle",
        "label": "温柔",
        "desc": "更柔和、更靠近一点",
        "style_hint": "soft",
        "enabled": True,
    },
    {
        "id": "restrained",
        "label": "克制",
        "desc": "少一点情绪外露",
        "style_hint": "calm",
        "enabled": True,
    },
    {
        "id": "disabled-tone",
        "label": "禁用语气",
        "desc": "测试",
        "style_hint": "test",
        "enabled": False,
    },
    {
        "id": "no-hint-tone",
        "label": "无 hint 语气",
        "desc": "测试",
        "style_hint": "",  # 空 hint
        "enabled": True,
    },
]


@pytest.fixture(autouse=True)
def mock_config_files():
    """patch lru_cache 函数，让测试使用 mock 数据而非真实文件。"""
    import src.xiangta.services.preset_mapper as pm_module
    with (
        patch.object(pm_module, "_load_voices", return_value=MOCK_VOICES),
        patch.object(pm_module, "_load_tones",  return_value=MOCK_TONES),
    ):
        yield


# ── 正常路径 ──────────────────────────────────────────────────────────────────

class TestResolveBindingHappyPath:

    def test_returns_core_binding_key(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        assert result["core_binding_key"] == "xiangta_female_gentle"

    def test_returns_voice_preset(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        assert result["voice_preset"] == "female-gentle"

    def test_returns_tone(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        assert result["tone"] == "gentle"

    def test_returns_tone_hint(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        assert result["tone_hint"] == "soft"

    def test_returns_enabled_true(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        assert result["enabled"] is True

    def test_another_combination(self):
        result = PresetMapper().resolve_binding("female-gentle", "restrained")
        assert result["core_binding_key"] == "xiangta_female_gentle"
        assert result["tone_hint"] == "calm"

    def test_result_has_expected_keys(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        assert set(result.keys()) == {
            "core_binding_key", "voice_preset", "tone", "tone_hint", "enabled"
        }


# ── 禁止字段 ─────────────────────────────────────────────────────────────────

class TestResolveBindingForbiddenKeys:

    def test_no_forbidden_keys_in_result(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        bad = set(result.keys()) & FORBIDDEN_KEYS
        assert not bad, f"resolve_binding 返回了禁止字段：{bad}"


# ── 错误路径 ──────────────────────────────────────────────────────────────────

class TestResolveBindingErrors:

    def test_unknown_voice_preset_raises(self):
        with pytest.raises(PresetMappingError, match="不存在"):
            PresetMapper().resolve_binding("nonexistent-voice", "gentle")

    def test_unknown_tone_raises(self):
        with pytest.raises(PresetMappingError, match="不存在"):
            PresetMapper().resolve_binding("female-gentle", "nonexistent-tone")

    def test_disabled_voice_raises(self):
        with pytest.raises(PresetMappingError, match="已禁用"):
            PresetMapper().resolve_binding("male-mature", "gentle")

    def test_disabled_tone_raises(self):
        with pytest.raises(PresetMappingError, match="已禁用"):
            PresetMapper().resolve_binding("female-gentle", "disabled-tone")

    def test_missing_core_binding_key_raises(self):
        with pytest.raises(PresetMappingError, match="core_binding_key"):
            PresetMapper().resolve_binding("no-key-voice", "gentle")

    def test_missing_style_hint_raises(self):
        with pytest.raises(PresetMappingError, match="style_hint"):
            PresetMapper().resolve_binding("female-gentle", "no-hint-tone")

    def test_error_is_value_error_subclass(self):
        with pytest.raises(ValueError):
            PresetMapper().resolve_binding("nonexistent", "gentle")


# ── 真实配置文件完整性（集成）────────────────────────────────────────────────

class TestRealConfigIntegrity:
    """不 mock，直接读真实 configs/*.json，验证基础完整性。"""

    @pytest.fixture(autouse=True)
    def _no_mock(self):
        """覆盖 autouse mock，恢复真实函数引用后清除缓存。"""
        _pm_module._load_voices = _REAL_LOAD_VOICES
        _pm_module._load_tones  = _REAL_LOAD_TONES
        _pm_module._reload()
        yield
        _pm_module._reload()

    def test_real_config_female_gentle_gentle(self):
        result = PresetMapper().resolve_binding("female-gentle", "gentle")
        assert result["core_binding_key"].startswith("xiangta_")
        assert result["tone_hint"]

    def test_real_config_no_forbidden_keys(self):
        for vid in ["female-gentle", "male-gentle", "female-bright", "male-mature"]:
            for tid in ["restrained", "gentle", "sincere", "whisper", "bedtime"]:
                result = PresetMapper().resolve_binding(vid, tid)
                bad = set(result.keys()) & FORBIDDEN_KEYS
                assert not bad, f"({vid}, {tid}) 返回了禁止字段 {bad}"
