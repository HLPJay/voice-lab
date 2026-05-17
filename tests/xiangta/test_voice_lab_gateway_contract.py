"""
P17-XIANGTA-PRODUCT-CONFIG-B1-3 — VoiceLabGateway dry-run 合约测试
"""
from __future__ import annotations

import inspect
import pytest

from src.xiangta.services.voice_lab_gateway import CoreRenderTarget, VoiceLabGateway

FORBIDDEN_KEYS = {
    "voice_id",
    "model_id",
    "sample_rate",
    "bitrate",
    "api_key",
    "minimax_api_key",
    "mimo_api_key",
    "provider_api_key",
    "coreBindingKey",
    "core_binding_key",
    "coreProfileId",
    "core_profile_id",
    "profile_id",
    "provider",
    "model",
    "provider_voice_id",
    "binding_id",
    "params_json",
}

DRY_RUN_KWARGS = dict(
    text="想念你",
    target=CoreRenderTarget(profile_id="<core_profile_id_from_core_profiles>"),
    tone="gentle",
    tone_hint="soft",
    scene="miss",
    voice_preset_id="female-gentle",
)


class TestGenerateTtsDryRunContract:
    @pytest.mark.asyncio
    async def test_accepts_core_render_target(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_does_not_call_core_or_provider(self, monkeypatch):
        gw = VoiceLabGateway()

        def fail(*args, **kwargs):
            raise AssertionError("dry-run 不应触发真实调用")

        monkeypatch.setattr("uuid.uuid4", __import__("uuid").uuid4)
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["status"] == "dry_run"
        assert "provider" not in result

    @pytest.mark.asyncio
    async def test_does_not_read_api_key_env(self, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("MIMO_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["status"] == "dry_run"

    @pytest.mark.asyncio
    async def test_contract_does_not_expose_core_fields(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        top_level_bad = set(result.keys()) & FORBIDDEN_KEYS
        contract_bad = set(result["contract"].keys()) & FORBIDDEN_KEYS
        assert not top_level_bad
        assert not contract_bad

    @pytest.mark.asyncio
    async def test_contract_returns_safe_fields(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["contract"] == {
            "voicePresetId": "female-gentle",
            "tone": "gentle",
            "toneHint": "soft",
            "scene": "miss",
            "mode": "dry_run",
        }

    def test_signature_has_no_forbidden_params(self):
        sig = inspect.signature(VoiceLabGateway.generate_tts_dry_run)
        param_names = set(sig.parameters.keys()) - {"self"}
        bad = param_names & FORBIDDEN_KEYS
        assert not bad
