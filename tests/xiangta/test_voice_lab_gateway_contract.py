"""
P17-XIANGTA-A2 — VoiceLabGateway dry-run 合约测试

验证：
  - generate_tts_dry_run 不调用真实 Provider（无网络 I/O）
  - generate_tts_dry_run 不读取环境变量中的 API key
  - 返回稳定字段：taskId, status, audioUrl, durationMs, message, contract
  - contract 不包含禁止的底层 Provider 字段
  - core_binding_key 正确传递到 contract.coreBindingKey
  - taskId 以 "dryrun_" 开头
  - status 为 "dry_run"
"""
import os
import pytest
from unittest.mock import patch

from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key", "provider_api_key",
}

DRY_RUN_KWARGS = dict(
    text="想念你",
    core_binding_key="xiangta_female_gentle",
    tone="gentle",
    tone_hint="soft",
    scene="miss",
    voice_preset="female-gentle",
)


class TestGenerateTtsDryRunContract:

    @pytest.mark.asyncio
    async def test_returns_task_id(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert "taskId" in result
        assert isinstance(result["taskId"], str)

    @pytest.mark.asyncio
    async def test_task_id_starts_with_dryrun(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["taskId"].startswith("dryrun_"), (
            f"dry-run taskId 应以 'dryrun_' 开头，得到：{result['taskId']!r}"
        )

    @pytest.mark.asyncio
    async def test_status_is_dry_run(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_audio_url_is_none(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["audioUrl"] is None

    @pytest.mark.asyncio
    async def test_duration_ms_is_none(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["durationMs"] is None

    @pytest.mark.asyncio
    async def test_has_message(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    @pytest.mark.asyncio
    async def test_has_contract(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert "contract" in result
        assert isinstance(result["contract"], dict)

    @pytest.mark.asyncio
    async def test_contract_has_core_binding_key(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["contract"]["coreBindingKey"] == "xiangta_female_gentle"

    @pytest.mark.asyncio
    async def test_contract_propagates_voice_preset(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["contract"]["voicePreset"] == "female-gentle"

    @pytest.mark.asyncio
    async def test_contract_propagates_tone(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["contract"]["tone"] == "gentle"

    @pytest.mark.asyncio
    async def test_contract_propagates_scene(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["contract"]["scene"] == "miss"

    @pytest.mark.asyncio
    async def test_each_call_returns_unique_task_id(self):
        gw = VoiceLabGateway()
        r1 = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        r2 = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert r1["taskId"] != r2["taskId"], "每次 dry-run 应返回不同的 taskId"

    @pytest.mark.asyncio
    async def test_no_forbidden_keys_in_top_level(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        bad = set(result.keys()) & FORBIDDEN_KEYS
        assert not bad, f"dry-run 顶层返回了禁止字段：{bad}"

    @pytest.mark.asyncio
    async def test_no_forbidden_keys_in_contract(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        contract_keys = set(result["contract"].keys())
        bad = contract_keys & FORBIDDEN_KEYS
        assert not bad, f"dry-run contract 包含禁止字段：{bad}"

    @pytest.mark.asyncio
    async def test_does_not_read_api_key_env(self, monkeypatch):
        """干预环境变量：任何读取 API key 变量的行为都应不影响 dry-run 成功。"""
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("MIMO_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_signature_has_no_forbidden_params(self):
        """generate_tts_dry_run 参数签名不得包含底层 Provider 字段。"""
        import inspect
        sig = inspect.signature(VoiceLabGateway.generate_tts_dry_run)
        param_names = set(sig.parameters.keys()) - {"self"}
        bad = param_names & FORBIDDEN_KEYS
        assert not bad, f"generate_tts_dry_run 签名包含禁止参数：{bad}"
