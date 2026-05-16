"""
test_xiaomi_mimo_chat_tts_adapter.py

P16-XIAOMI-MIMO-TTS-B1: Tests for Xiaomi MiMo Chat TTS adapter.

Covers:
- Plugin discovery via config/adapters/xiaomi_mimo_chat_tts.yaml
- ProviderConfig for xiaomi_mimo (disabled by default)
- render_sync request construction and response parsing
- list_voices static preset voices
- Error handling (missing API key, missing audio data, invalid base64, HTTP errors)
- No real external API calls

B1 scope:
- render_sync with mimo-v2.5-tts model
- static preset voice list
- wav non-streaming output
- base64 audio parsing
"""

import base64
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakehttpxResponse:
    """Fake httpx.Response for testing."""

    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            from httpx import HTTPStatusError

            raise HTTPStatusError(
                "server error",
                request=MagicMock(),
                response=self,
            )


class TestPluginDiscovery:
    """Verify xiaomi_mimo_chat_tts is loaded via plugin.import_path."""

    def setup_method(self):
        """Reset all caches before each test."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

    def test_xiaomi_mimo_chat_tts_adapter_discovered(self):
        """xiaomi_mimo_chat_tts adapter_type is loaded via plugin.import_path."""
        from app.providers.adapter_type_registry import (
            get_adapter_type_adapter,
        )

        cls = get_adapter_type_adapter("xiaomi_mimo_chat_tts")
        assert cls.__name__ == "XiaomiMiMoChatTTSAdapter"

    def test_xiaomi_mimo_adapter_not_hardcoded(self):
        """xiaomi_mimo_chat_tts is NOT in ADAPTER_TYPE_REGISTRY before loading."""
        from app.providers.adapter_type_registry import (
            ADAPTER_TYPE_REGISTRY,
            clear_adapter_type_registry_for_tests,
        )

        clear_adapter_type_registry_for_tests()

        # Before loading, should not be in registry
        assert "xiaomi_mimo_chat_tts" not in ADAPTER_TYPE_REGISTRY

        # After loading (via get_adapter_type_adapter), should be registered
        from app.providers.adapter_type_registry import (
            get_adapter_type_adapter,
        )

        get_adapter_type_adapter("xiaomi_mimo_chat_tts")
        assert "xiaomi_mimo_chat_tts" in ADAPTER_TYPE_REGISTRY


class TestProviderConfig:
    """ProviderConfig for xiaomi_mimo."""

    def setup_method(self):
        """Reset caches."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

    def test_xiaomi_mimo_provider_config_exists(self):
        """get_provider_config('xiaomi_mimo') returns a config."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg is not None
        assert cfg.name == "xiaomi_mimo"

    def test_xiaomi_mimo_disabled_by_default(self):
        """xiaomi_mimo provider is disabled."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.enabled is False

    def test_xiaomi_mimo_adapter_type(self):
        """xiaomi_mimo adapter_type is xiaomi_mimo_chat_tts."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.adapter_type == "xiaomi_mimo_chat_tts"

    def test_xiaomi_mimo_real_cost(self):
        """xiaomi_mimo has real_cost=true."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.real_cost is True

    def test_xiaomi_mimo_api_key_env(self):
        """xiaomi_mimo api_key_env is MIMO_API_KEY."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.api_key_env == "MIMO_API_KEY"

    def test_xiaomi_mimo_tts_enabled(self):
        """xiaomi_mimo tts is enabled."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.tts.enabled is True

    def test_xiaomi_mimo_batch_disabled(self):
        """xiaomi_mimo batch is disabled."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.batch.enabled is False

    def test_xiaomi_mimo_voice_clone_disabled(self):
        """xiaomi_mimo voice_clone is disabled."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.voice_clone.enabled is False

    def test_xiaomi_mimo_voice_design_disabled(self):
        """xiaomi_mimo voice_design is disabled."""
        from app.config.provider_config_loader import get_provider_config

        cfg = get_provider_config("xiaomi_mimo")
        assert cfg.voice_design.enabled is False


class TestAdapterConfig:
    """AdapterConfig for xiaomi_mimo_chat_tts."""

    def setup_method(self):
        """Reset caches."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

    def test_xiaomi_mimo_adapter_config_tts_supported(self):
        """xiaomi_mimo_chat_tts tts is supported."""
        from app.config.adapter_config_loader import get_adapter_config

        cfg = get_adapter_config("xiaomi_mimo_chat_tts")
        assert cfg.tts is not None
        assert cfg.tts.supported is True

    def test_xiaomi_mimo_adapter_config_model(self):
        """xiaomi_mimo_chat_tts has mimo-v2.5-tts model."""
        from app.config.adapter_config_loader import get_adapter_config

        cfg = get_adapter_config("xiaomi_mimo_chat_tts")
        assert "mimo-v2.5-tts" in cfg.tts.models

    def test_xiaomi_mimo_adapter_config_streaming_false(self):
        """xiaomi_mimo_chat_tts does not support streaming."""
        from app.config.adapter_config_loader import get_adapter_config

        cfg = get_adapter_config("xiaomi_mimo_chat_tts")
        assert cfg.tts.supports_streaming is False

    def test_xiaomi_mimo_adapter_config_wav_only(self):
        """xiaomi_mimo_chat_tts supports wav format."""
        from app.config.adapter_config_loader import get_adapter_config

        cfg = get_adapter_config("xiaomi_mimo_chat_tts")
        assert "wav" in cfg.tts.audio_formats

    def test_xiaomi_mimo_adapter_config_voice_clone_unsupported(self):
        """xiaomi_mimo_chat_tts voice_clone is not supported."""
        from app.config.adapter_config_loader import get_adapter_config

        cfg = get_adapter_config("xiaomi_mimo_chat_tts")
        assert cfg.voice_clone.supported is False

    def test_xiaomi_mimo_adapter_config_voice_design_unsupported(self):
        """xiaomi_mimo_chat_tts voice_design is not supported."""
        from app.config.adapter_config_loader import get_adapter_config

        cfg = get_adapter_config("xiaomi_mimo_chat_tts")
        assert cfg.voice_design.supported is False


class TestCapabilityAPI:
    """Capability API for xiaomi_mimo (disabled by default)."""

    def setup_method(self):
        """Reset caches."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

    def test_xiaomi_mimo_not_in_capabilities_when_disabled(self):
        """xiaomi_mimo does not appear in list_capabilities when disabled."""
        from app.providers.capability_registry import list_capabilities

        caps = list_capabilities()
        providers = [c.provider for c in caps]
        assert "xiaomi_mimo" not in providers


class TestRenderSync:
    """render_sync request construction and response parsing."""

    def setup_method(self):
        """Reset caches."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

        # Set fake environment
        os.environ["MIMO_API_KEY"] = "fake_mimo_api_key_for_testing"
        os.environ["XIAOMI_MIMO_BASE_URL"] = "https://fake.xiaomimimo.com"

    def teardown_method(self):
        """Clean up environment."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("XIAOMI_MIMO_BASE_URL", None)

    @pytest.mark.asyncio
    async def test_render_sync_url_and_headers(self):
        """render_sync sends request to correct URL with api-key header."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        # Create fake httpx.AsyncClient
        fake_client = AsyncMock()
        captured_request = {}

        async def fake_request(method, url, **kwargs):
            captured_request["method"] = method
            captured_request["url"] = url
            captured_request["headers"] = kwargs.get("headers", {})
            captured_request["json"] = kwargs.get("json", {})

            # Return fake success response with minimal audio data
            fake_wav = b"RIFF" + b"\x00" * 100  # Minimal WAV header
            encoded = base64.b64encode(fake_wav).decode()
            return FakehttpxResponse({
                "id": "test-trace-id",
                "choices": [{
                    "message": {
                        "audio": {"data": encoded, "format": "wav"},
                        "content": ""
                    }
                }],
                "usage": {"completion_tokens": 50}
            })

        fake_client.request = fake_request

        # Create adapter with fake client
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        # Create render plan
        plan = RenderPlan(
            id="test-plan-1",
            text="测试文本",
            processed_text="测试文本",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        result = await adapter.render_sync(plan)

        # Verify URL
        assert captured_request["url"] == "https://fake.xiaomimimo.com/v1/chat/completions"

        # Verify headers do NOT use Authorization: Bearer
        headers = captured_request["headers"]
        assert "api-key" in headers
        assert headers["api-key"] == "fake_mimo_api_key_for_testing"
        assert "Authorization" not in headers

        # Verify model in body
        body = captured_request["json"]
        assert body["model"] == "mimo-v2.5-tts"

        # Verify voice
        assert body["audio"]["voice"] == "冰糖"

        # Verify format
        assert body["audio"]["format"] == "wav"

        # Verify text in messages (role=assistant)
        messages = body["messages"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        assert len(assistant_msgs) >= 1
        assert "测试文本" in assistant_msgs[-1].get("content", "")

        # Verify result
        assert result.audio_path
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_render_sync_default_voice(self):
        """render_sync uses mimo_default when no voice specified."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        fake_client = AsyncMock()
        captured_body = {}

        async def fake_request(method, url, **kwargs):
            captured_body["body"] = kwargs.get("json", {})
            fake_wav = b"RIFF" + b"\x00" * 100
            encoded = base64.b64encode(fake_wav).decode()
            return FakehttpxResponse({
                "id": "test-trace-id",
                "choices": [{
                    "message": {
                        "audio": {"data": encoded, "format": "wav"},
                        "content": ""
                    }
                }],
                "usage": {"completion_tokens": 50}
            })

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-2",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="",  # Empty voice
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        await adapter.render_sync(plan)

        # Should use default voice mimo_default
        assert captured_body["body"]["audio"]["voice"] == "mimo_default"

    @pytest.mark.asyncio
    async def test_render_sync_uses_processed_text(self):
        """render_sync prefers processed_text over text."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        fake_client = AsyncMock()
        captured_body = {}

        async def fake_request(method, url, **kwargs):
            captured_body["body"] = kwargs.get("json", {})
            fake_wav = b"RIFF" + b"\x00" * 100
            encoded = base64.b64encode(fake_wav).decode()
            return FakehttpxResponse({
                "id": "test-trace-id",
                "choices": [{
                    "message": {
                        "audio": {"data": encoded, "format": "wav"},
                        "content": ""
                    }
                }],
                "usage": {"completion_tokens": 50}
            })

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-3",
            text="原始文本",
            processed_text="处理后文本",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        await adapter.render_sync(plan)

        messages = captured_body["body"]["messages"]
        assistant_content = [m["content"] for m in messages if m.get("role") == "assistant"]
        assert "处理后文本" in assistant_content
        assert "原始文本" not in str(assistant_content)

    @pytest.mark.asyncio
    async def test_render_sync_base64_decode(self):
        """render_sync correctly decodes base64 audio."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        fake_client = AsyncMock()

        # Create a recognizable WAV byte sequence
        expected_wav = b"RIFF" + b"\xAA" * 100
        encoded = base64.b64encode(expected_wav).decode()

        async def fake_request(method, url, **kwargs):
            return FakehttpxResponse({
                "id": "test-trace-id",
                "choices": [{
                    "message": {
                        "audio": {"data": encoded, "format": "wav"},
                        "content": ""
                    }
                }],
                "usage": {"completion_tokens": 50}
            })

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-4",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        result = await adapter.render_sync(plan)

        # Verify audio file was saved
        from pathlib import Path

        audio_path = Path(result.audio_path)
        assert audio_path.exists()

        # Verify content matches expected WAV
        saved_bytes = audio_path.read_bytes()
        assert saved_bytes == expected_wav

        # Verify metadata
        assert result.metadata.get("audio_format") == "wav"
        assert result.metadata.get("provider") == "xiaomi_mimo"
        assert result.metadata.get("model") == "mimo-v2.5-tts"
        assert result.metadata.get("voice") == "冰糖"


class TestListVoices:
    """list_voices static preset voices."""

    def setup_method(self):
        """Reset caches."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

    @pytest.mark.asyncio
    async def test_list_voices_returns_preset_voices(self):
        """list_voices returns all preset Xiaomi MiMo voices."""
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        adapter = XiaomiMiMoChatTTSAdapter()
        voices = await adapter.list_voices()

        voice_ids = [v.provider_voice_id for v in voices]
        assert "mimo_default" in voice_ids
        assert "冰糖" in voice_ids
        assert "茉莉" in voice_ids
        assert "苏打" in voice_ids
        assert "白桦" in voice_ids
        assert "Mia" in voice_ids
        assert "Chloe" in voice_ids
        assert "Milo" in voice_ids
        assert "Dean" in voice_ids

    @pytest.mark.asyncio
    async def test_list_voices_count(self):
        """list_voices returns exactly 9 preset voices."""
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        adapter = XiaomiMiMoChatTTSAdapter()
        voices = await adapter.list_voices()
        assert len(voices) == 9

    @pytest.mark.asyncio
    async def test_list_voices_voice_types(self):
        """All list_voices are system type."""
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        adapter = XiaomiMiMoChatTTSAdapter()
        voices = await adapter.list_voices()
        for v in voices:
            assert v.voice_type == "system"

    @pytest.mark.asyncio
    async def test_list_voices_no_http_calls(self):
        """list_voices does not make HTTP calls."""
        from unittest.mock import patch

        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        adapter = XiaomiMiMoChatTTSAdapter()

        with patch.object(adapter, "_request") as mock_request:
            voices = await adapter.list_voices()
            mock_request.assert_not_called()

        assert len(voices) == 9


class TestErrorHandling:
    """Error handling tests."""

    def setup_method(self):
        """Reset caches and set fake env."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

        os.environ["MIMO_API_KEY"] = "fake_key"
        os.environ["XIAOMI_MIMO_BASE_URL"] = "https://fake.xiaomimimo.com"

    def teardown_method(self):
        """Clean up."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("XIAOMI_MIMO_BASE_URL", None)

    @pytest.mark.asyncio
    async def test_error_missing_api_key(self):
        """Missing MIMO_API_KEY raises ProviderNotConfigured."""
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        os.environ.pop("MIMO_API_KEY", None)
        os.environ["MIMO_API_KEY"] = "replace_me"

        adapter = XiaomiMiMoChatTTSAdapter()

        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.core.errors import ProviderNotConfigured

        plan = RenderPlan(
            id="test-plan-err",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        with pytest.raises(ProviderNotConfigured, match="MIMO_API_KEY"):
            await adapter.render_sync(plan)

    @pytest.mark.asyncio
    async def test_error_missing_audio_data(self):
        """Missing audio data in response raises ProviderError."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )
        from app.core.errors import ProviderError

        fake_client = AsyncMock()

        async def fake_request(method, url, **kwargs):
            return FakehttpxResponse({
                "id": "test-trace-id",
                "choices": [{
                    "message": {
                        "audio": {},  # No data
                        "content": ""
                    }
                }]
            })

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-err2",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        with pytest.raises(ProviderError, match="missing audio data"):
            await adapter.render_sync(plan)

    @pytest.mark.asyncio
    async def test_error_invalid_base64(self):
        """Invalid base64 in response raises ProviderError."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )
        from app.core.errors import ProviderError

        fake_client = AsyncMock()

        async def fake_request(method, url, **kwargs):
            return FakehttpxResponse({
                "id": "test-trace-id",
                "choices": [{
                    "message": {
                        "audio": {"data": "!!!not-valid-base64!!!", "format": "wav"},
                        "content": ""
                    }
                }]
            })

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-err3",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        with pytest.raises(ProviderError, match="audio decode failed"):
            await adapter.render_sync(plan)

    @pytest.mark.asyncio
    async def test_error_http_500(self):
        """HTTP 500 raises ProviderError."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )
        from app.core.errors import ProviderError

        fake_client = AsyncMock()

        async def fake_request(method, url, **kwargs):
            return FakehttpxResponse(
                {"error": "internal server error"},
                status_code=500,
            )

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-err4",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        with pytest.raises(ProviderError, match="HTTP error"):
            await adapter.render_sync(plan)

    @pytest.mark.asyncio
    async def test_error_missing_choices(self):
        """Missing choices in response raises ProviderError."""
        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )
        from app.core.errors import ProviderError

        fake_client = AsyncMock()

        async def fake_request(method, url, **kwargs):
            return FakehttpxResponse({"id": "test-trace-id", "choices": []})

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-err5",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        with pytest.raises(ProviderError, match="missing choices"):
            await adapter.render_sync(plan)


class TestNoRealExternalAPICalls:
    """Verify no real external API calls are made."""

    def setup_method(self):
        """Reset caches and set fake env."""
        from app.config.adapter_config_loader import clear_adapter_config_cache
        from app.config.provider_config_loader import clear_provider_config_cache
        from app.providers.adapter_type_registry import (
            clear_adapter_type_registry_for_tests,
        )
        from app.providers.capability_registry import clear_capability_registry_cache

        clear_adapter_type_registry_for_tests()
        clear_adapter_config_cache()
        clear_provider_config_cache()
        clear_capability_registry_cache()

        os.environ["MIMO_API_KEY"] = "fake_key"
        os.environ["XIAOMI_MIMO_BASE_URL"] = "https://fake.xiaomimimo.com"

    def teardown_method(self):
        """Clean up."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("XIAOMI_MIMO_BASE_URL", None)

    @pytest.mark.asyncio
    async def test_render_sync_no_real_http_call(self):
        """render_sync with fake client does not call real httpx."""
        import httpx
        from unittest.mock import patch

        from app.domain.render_plan import RenderPlan, SubtitlePlan
        from app.providers.xiaomi_mimo_chat_tts_adapter import (
            XiaomiMiMoChatTTSAdapter,
        )

        fake_client = AsyncMock()
        fake_wav = b"RIFF" + b"\x00" * 100
        encoded = base64.b64encode(fake_wav).decode()

        async def fake_request(method, url, **kwargs):
            return FakehttpxResponse({
                "id": "test-trace-id",
                "choices": [{
                    "message": {
                        "audio": {"data": encoded, "format": "wav"},
                        "content": ""
                    }
                }],
                "usage": {"completion_tokens": 50}
            })

        fake_client.request = fake_request
        adapter = XiaomiMiMoChatTTSAdapter(http_client=fake_client)

        plan = RenderPlan(
            id="test-plan-noreal",
            text="测试",
            processed_text="测试",
            profile_id="profile-1",
            provider="xiaomi_mimo",
            model="mimo-v2.5-tts",
            provider_voice_id="冰糖",
            voice_params={},
            audio_params={"format": "wav"},
            subtitle=SubtitlePlan(enabled=False),
            output_format="wav",
            language_boost="auto",
        )

        with patch.object(httpx, "AsyncClient") as mock_client_class:
            await adapter.render_sync(plan)
            mock_client_class.assert_not_called()
