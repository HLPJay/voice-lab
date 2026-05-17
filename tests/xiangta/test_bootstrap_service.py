"""
P17-XIANGTA-A1-FIX1 — BootstrapService 单元测试

验证 BootstrapService 的数据组装逻辑，与路由层无关。
mock config.loader 和 ProviderStatusService，隔离文件 IO 和外部依赖。
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.xiangta.services.bootstrap_service import BootstrapService
from src.xiangta.config import loader as _loader_module
from src.xiangta.config.bootstrap_config import STYLES, LIMITS

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
}

MOCK_RECIPIENTS = [{"id": "lover", "label": "恋人", "hint": "想他、想她", "enabled": True}]
MOCK_SCENES     = [{"id": "miss",  "label": "想念", "hint": "不知不觉就想了", "enabled": True}]
MOCK_VOICES     = [{"id": "female-gentle", "name": "温柔女声", "desc": "清晰", "core_binding_key": "xiangta_female_gentle", "enabled": True}]
MOCK_TONES      = [{"id": "gentle", "label": "温柔", "desc": "柔和", "style_hint": "soft", "enabled": True}]

NOT_INTEGRATED_STATUS = {
    "kind": "not_integrated",
    "label": "语音服务待接入",
    "detail": "XiangTa Product Server 已初始化",
    "quotaPct": 0.0,
}


@pytest.fixture
def mock_provider_status():
    svc = MagicMock()
    svc.get_status = AsyncMock(return_value=NOT_INTEGRATED_STATUS)
    return svc


@pytest.fixture(autouse=True)
def mock_loader():
    with (
        patch.object(_loader_module, "load_recipients",    return_value=MOCK_RECIPIENTS),
        patch.object(_loader_module, "load_scenes",        return_value=MOCK_SCENES),
        patch.object(_loader_module, "load_voice_presets", return_value=MOCK_VOICES),
        patch.object(_loader_module, "load_tone_presets",  return_value=MOCK_TONES),
    ):
        yield


class TestBootstrapServiceGetBootstrap:

    @pytest.mark.asyncio
    async def test_returns_recipients(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert result["recipients"] == MOCK_RECIPIENTS

    @pytest.mark.asyncio
    async def test_returns_scenes(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert result["scenes"] == MOCK_SCENES

    @pytest.mark.asyncio
    async def test_returns_static_styles(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert result["styles"] == STYLES
        assert len(result["styles"]) == 3

    @pytest.mark.asyncio
    async def test_returns_voice_presets(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert result["voicePresets"] == MOCK_VOICES

    @pytest.mark.asyncio
    async def test_returns_tone_presets(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert result["tonePresets"] == MOCK_TONES

    @pytest.mark.asyncio
    async def test_returns_static_limits(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert result["limits"] == LIMITS
        assert result["limits"]["maxRawTextChars"] == 500

    @pytest.mark.asyncio
    async def test_returns_provider_status(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert result["providerStatus"]["kind"] == "not_integrated"

    @pytest.mark.asyncio
    async def test_calls_provider_status_once(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        await svc.get_bootstrap()
        mock_provider_status.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_result_has_all_expected_keys(self, mock_provider_status):
        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        assert set(result.keys()) == {
            "recipients", "scenes", "styles", "voicePresets",
            "tonePresets", "limits", "providerStatus",
        }

    @pytest.mark.asyncio
    async def test_no_forbidden_keys_in_result(self, mock_provider_status):

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

        svc = BootstrapService(provider_status=mock_provider_status)
        result = await svc.get_bootstrap()
        all_keys = collect_keys(result)
        bad = all_keys & FORBIDDEN_KEYS
        assert not bad, f"BootstrapService 返回了禁止字段：{bad}"
