"""
P17-XIANGTA-A2 — TtsOrchestrator 单元测试

验证：
  - 正常 dry-run 返回产品层字段（taskId, status, charCount …）
  - 会调用 PresetMapper.resolve_binding
  - 会调用 VoiceLabGateway.generate_tts_dry_run
  - voicePreset 不存在 / disabled 抛 PresetNotFoundError
  - tone 不存在 / disabled 抛 PresetNotFoundError
  - text 为空抛 InvalidInputError
  - text 超过 maxTtsChars 抛 TextTooLongError
  - 返回结果不包含禁止字段
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.xiangta.services.tts_orchestrator import TtsOrchestrator
from src.xiangta.services.preset_mapper import PresetMappingError
from src.xiangta.services.error_translator import (
    InvalidInputError,
    TextTooLongError,
    PresetNotFoundError,
)

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
}

MOCK_BINDING = {
    "core_binding_key": "xiangta_female_gentle",
    "voice_preset":     "female-gentle",
    "tone":             "gentle",
    "tone_hint":        "soft",
    "enabled":          True,
}

MOCK_GATEWAY_RESULT = {
    "taskId":    "dryrun_abc12345",
    "status":    "dry_run",
    "audioUrl":  None,
    "durationMs": None,
    "message":   "dry-run only, no provider call",
    "contract":  {
        "coreBindingKey": "xiangta_female_gentle",
        "voicePreset":    "female-gentle",
        "tone":           "gentle",
        "toneHint":       "soft",
        "scene":          "miss",
    },
}


@pytest.fixture
def mock_mapper():
    m = MagicMock()
    m.resolve_binding.return_value = MOCK_BINDING
    return m


@pytest.fixture
def mock_gateway():
    g = MagicMock()
    g.generate_tts_dry_run = AsyncMock(return_value=MOCK_GATEWAY_RESULT)
    return g


@pytest.fixture
def orchestrator(mock_gateway, mock_mapper):
    return TtsOrchestrator(gateway=mock_gateway, mapper=mock_mapper)


# ── 正常路径 ──────────────────────────────────────────────────────────────────

class TestGenerateHappyPath:

    @pytest.mark.asyncio
    async def test_returns_task_id(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["taskId"] == "dryrun_abc12345"

    @pytest.mark.asyncio
    async def test_returns_dry_run_status(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_audio_url_is_none(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["audioUrl"] is None

    @pytest.mark.asyncio
    async def test_char_count_matches_text(self, orchestrator):
        text = "想念你"
        result = await orchestrator.generate(
            text=text, voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["charCount"] == len(text)

    @pytest.mark.asyncio
    async def test_returns_voice_preset(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["voicePreset"] == "female-gentle"

    @pytest.mark.asyncio
    async def test_returns_tone(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["tone"] == "gentle"

    @pytest.mark.asyncio
    async def test_returns_contract(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["contract"]["coreBindingKey"] == "xiangta_female_gentle"

    @pytest.mark.asyncio
    async def test_calls_resolve_binding_once(self, orchestrator, mock_mapper):
        await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        mock_mapper.resolve_binding.assert_called_once_with("female-gentle", "gentle")

    @pytest.mark.asyncio
    async def test_calls_generate_tts_dry_run_once(self, orchestrator, mock_gateway):
        await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        mock_gateway.generate_tts_dry_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_dry_run_called_with_core_binding_key(self, orchestrator, mock_gateway):
        await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        call_kwargs = mock_gateway.generate_tts_dry_run.call_args.kwargs
        assert call_kwargs["core_binding_key"] == "xiangta_female_gentle"


# ── 禁止字段 ─────────────────────────────────────────────────────────────────

class TestNoForbiddenKeysInResult:

    def _collect_keys(self, obj, seen=None):
        if seen is None:
            seen = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                seen.add(k)
                self._collect_keys(v, seen)
        elif isinstance(obj, list):
            for item in obj:
                self._collect_keys(item, seen)
        return seen

    @pytest.mark.asyncio
    async def test_no_forbidden_keys(self, orchestrator):
        result = await orchestrator.generate(
            text="想念你", voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        all_keys = self._collect_keys(result)
        bad = all_keys & FORBIDDEN_KEYS
        assert not bad, f"generate() 返回了禁止字段：{bad}"


# ── 输入校验错误路径 ──────────────────────────────────────────────────────────

class TestInputValidationErrors:

    @pytest.mark.asyncio
    async def test_empty_text_raises_invalid_input(self, orchestrator):
        with pytest.raises(InvalidInputError):
            await orchestrator.generate(
                text="", voice_preset="female-gentle",
                tone="gentle", recipient="lover", scene="miss",
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_text_raises_invalid_input(self, orchestrator):
        with pytest.raises(InvalidInputError):
            await orchestrator.generate(
                text="   ", voice_preset="female-gentle",
                tone="gentle", recipient="lover", scene="miss",
            )

    @pytest.mark.asyncio
    async def test_text_over_limit_raises_text_too_long(self, orchestrator):
        long_text = "字" * 501
        with pytest.raises(TextTooLongError):
            await orchestrator.generate(
                text=long_text, voice_preset="female-gentle",
                tone="gentle", recipient="lover", scene="miss",
            )

    @pytest.mark.asyncio
    async def test_text_at_limit_is_ok(self, orchestrator):
        text_at_limit = "字" * 500
        result = await orchestrator.generate(
            text=text_at_limit, voice_preset="female-gentle",
            tone="gentle", recipient="lover", scene="miss",
        )
        assert result["charCount"] == 500


# ── 预设错误路径 ──────────────────────────────────────────────────────────────

class TestPresetErrors:

    @pytest.mark.asyncio
    async def test_unknown_voice_preset_raises_preset_not_found(
        self, mock_gateway
    ):
        mapper = MagicMock()
        mapper.resolve_binding.side_effect = PresetMappingError("voicePreset 'x' 不存在")
        orch = TtsOrchestrator(gateway=mock_gateway, mapper=mapper)
        with pytest.raises(PresetNotFoundError, match="不存在"):
            await orch.generate(
                text="想念你", voice_preset="x",
                tone="gentle", recipient="lover", scene="miss",
            )

    @pytest.mark.asyncio
    async def test_unknown_tone_raises_preset_not_found(self, mock_gateway):
        mapper = MagicMock()
        mapper.resolve_binding.side_effect = PresetMappingError("tone 'x' 不存在")
        orch = TtsOrchestrator(gateway=mock_gateway, mapper=mapper)
        with pytest.raises(PresetNotFoundError, match="不存在"):
            await orch.generate(
                text="想念你", voice_preset="female-gentle",
                tone="x", recipient="lover", scene="miss",
            )

    @pytest.mark.asyncio
    async def test_disabled_voice_raises_preset_not_found(self, mock_gateway):
        mapper = MagicMock()
        mapper.resolve_binding.side_effect = PresetMappingError("voicePreset 'x' 已禁用")
        orch = TtsOrchestrator(gateway=mock_gateway, mapper=mapper)
        with pytest.raises(PresetNotFoundError, match="已禁用"):
            await orch.generate(
                text="想念你", voice_preset="x",
                tone="gentle", recipient="lover", scene="miss",
            )

    @pytest.mark.asyncio
    async def test_disabled_tone_raises_preset_not_found(self, mock_gateway):
        mapper = MagicMock()
        mapper.resolve_binding.side_effect = PresetMappingError("tone 'x' 已禁用")
        orch = TtsOrchestrator(gateway=mock_gateway, mapper=mapper)
        with pytest.raises(PresetNotFoundError, match="已禁用"):
            await orch.generate(
                text="想念你", voice_preset="female-gentle",
                tone="x", recipient="lover", scene="miss",
            )

    @pytest.mark.asyncio
    async def test_preset_not_found_is_xiangta_error(self, mock_gateway):
        from src.xiangta.services.error_translator import XiangTaError
        mapper = MagicMock()
        mapper.resolve_binding.side_effect = PresetMappingError("不存在")
        orch = TtsOrchestrator(gateway=mock_gateway, mapper=mapper)
        with pytest.raises(XiangTaError):
            await orch.generate(
                text="想念你", voice_preset="female-gentle",
                tone="gentle", recipient="lover", scene="miss",
            )
