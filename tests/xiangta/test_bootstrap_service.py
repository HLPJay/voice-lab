"""
P17-XIANGTA-A1-FIX1 — BootstrapService 单元测试

验证 BootstrapService 的数据组装逻辑，与路由层无关。
mock ProductConfigRepository 和 ProviderStatusService，隔离文件 IO 和外部依赖。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.xiangta.services.bootstrap_service import BootstrapService
from src.xiangta.config.bootstrap_config import STYLES
from src.xiangta.config.product_config_models import ProductLimits, PublicVoicePreset, TonePreset

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
    "core_binding_key", "coreProfileId", "core_profile_id",
    "profile_id", "provider", "model", "provider_voice_id",
    "binding_id", "params_json",
}

MOCK_RECIPIENTS = [{"id": "lover", "label": "恋人", "hint": "想他、想她", "enabled": True}]
MOCK_SCENES     = [{"id": "miss",  "label": "想念", "hint": "不知不觉就想了", "enabled": True}]
MOCK_VOICES     = [
    PublicVoicePreset(
        id="female-gentle",
        label="温柔女声",
        desc="清晰",
        gender_style="female",
        suitable_recipients=["lover", "friend"],
        recommended_scenes=["miss", "night"],
        default_tone="gentle",
        enabled=True,
    )
]
MOCK_TONES      = [
    TonePreset(
        id="gentle",
        label="温柔",
        desc="柔和",
        style_hint="soft",
        enabled=True,
    )
]

NOT_INTEGRATED_STATUS = {
    "kind": "not_integrated",
    "label": "语音服务待接入",
    "detail": "XiangTa Product Server 已初始化",
    "quotaPct": 0.0,
}

OK_STATUS = {
    "kind": "ok",
    "label": "语音服务可用",
    "detail": "mock runtime available",
    "quotaPct": 0.0,
}

DEGRADED_STATUS = {
    "kind": "degraded",
    "label": "语音服务状态未知",
    "detail": "Core runtime status unavailable",
    "quotaPct": 0.0,
}


@pytest.fixture
def mock_provider_status():
    svc = MagicMock()
    svc.get_status = AsyncMock(return_value=NOT_INTEGRATED_STATUS)
    return svc


@pytest.fixture
def mock_config_repository():
    repo = MagicMock()
    repo.list_public_voice_presets.return_value = MOCK_VOICES
    repo.list_tone_presets.return_value = MOCK_TONES
    repo.list_recipients.return_value = MOCK_RECIPIENTS
    repo.list_scenes.return_value = MOCK_SCENES
    repo.get_limits.return_value = ProductLimits()
    return repo


class TestBootstrapServiceGetBootstrap:

    @pytest.mark.asyncio
    async def test_returns_recipients(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["recipients"] == MOCK_RECIPIENTS

    @pytest.mark.asyncio
    async def test_returns_scenes(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["scenes"] == MOCK_SCENES

    @pytest.mark.asyncio
    async def test_returns_static_styles(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["styles"] == STYLES
        assert len(result["styles"]) == 3

    @pytest.mark.asyncio
    async def test_returns_voice_presets_from_product_config_repository(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["voicePresets"] == [{
            "id": "female-gentle",
            "label": "温柔女声",
            "desc": "清晰",
            "genderStyle": "female",
            "suitableRecipients": ["lover", "friend"],
            "recommendedScenes": ["miss", "night"],
            "defaultTone": "gentle",
            "enabled": True,
        }]
        mock_config_repository.list_public_voice_presets.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_tone_presets_from_product_config_repository(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["tonePresets"] == [{
            "id": "gentle",
            "label": "温柔",
            "desc": "柔和",
            "styleHint": "soft",
            "enabled": True,
        }]
        mock_config_repository.list_tone_presets.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_limits_from_product_config_repository(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["limits"] == {
            "maxRawTextChars": 500,
            "maxTtsChars": 500,
            "maxSuggestions": 3,
        }
        assert result["limits"]["maxRawTextChars"] == 500

    @pytest.mark.asyncio
    async def test_returns_provider_status(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["providerStatus"]["kind"] == "not_integrated"

    @pytest.mark.asyncio
    async def test_calls_provider_status_once(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        await svc.get_bootstrap()
        mock_provider_status.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_result_has_all_expected_keys(self, mock_provider_status, mock_config_repository):
        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert set(result.keys()) == {
            "recipients", "scenes", "styles", "voicePresets",
            "tonePresets", "limits", "providerStatus",
        }

    @pytest.mark.asyncio
    async def test_provider_status_ok_kind_propagates(self, mock_config_repository):
        svc_ok = MagicMock()
        svc_ok.get_status = AsyncMock(return_value=OK_STATUS)
        svc = BootstrapService(provider_status=svc_ok, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["providerStatus"]["kind"] == "ok"

    @pytest.mark.asyncio
    async def test_provider_status_degraded_kind_propagates(self, mock_config_repository):
        svc_deg = MagicMock()
        svc_deg.get_status = AsyncMock(return_value=DEGRADED_STATUS)
        svc = BootstrapService(provider_status=svc_deg, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        assert result["providerStatus"]["kind"] == "degraded"

    @pytest.mark.asyncio
    async def test_no_forbidden_keys_in_result(self, mock_provider_status, mock_config_repository):

        def collect_keys(obj, seen=None):
            if seen is None:
                seen = set()
            if isinstance(obj, dict):
                for k, v in obj.items():
                    seen.add(k)
                    collect_keys(v, seen)
            elif isinstance(obj, list):
                for item in obj:
                    collect_keys(item, seen)
            return seen

        svc = BootstrapService(provider_status=mock_provider_status, config_repository=mock_config_repository)
        result = await svc.get_bootstrap()
        all_keys = collect_keys(result)
        bad = all_keys & FORBIDDEN_KEYS
        assert not bad, f"BootstrapService 返回了禁止字段：{bad}"
