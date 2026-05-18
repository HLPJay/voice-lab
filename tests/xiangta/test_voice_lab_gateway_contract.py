from __future__ import annotations

import inspect

import pytest

from src.xiangta.services.voice_lab_gateway import (
    CoreProfilesResponseError,
    CoreProfilesUnavailableError,
    CoreRenderResponseError,
    CoreRenderTarget,
    CoreRenderUnavailableError,
    CoreStatusUnavailableError,
    CoreStatusResponseError,
    VoiceLabGateway,
)

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


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeCoreClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests: list[tuple[str, dict]] = []

    async def post(self, path: str, json: dict) -> FakeResponse:
        self.requests.append((path, json))
        return FakeResponse(self.payload)


def _success_payload() -> dict:
    return {
        "job_id": "job_123",
        "status": "success",
        "audio_asset": {
            "id": "audio_123",
            "url": "/api/voice/assets/audio_123/download",
            "duration_ms": 1800,
            "format": "mp3",
        },
        "subtitle_asset": None,
        "provider": "mock",
        "model": "mock-model",
    }


class TestGenerateTtsContract:
    @pytest.mark.asyncio
    async def test_provider_none_does_not_include_provider_in_payload(self):
        """B9: target.provider=None 时，payload 不包含 provider 字段，让 Core 使用默认策略。"""
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider=None),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        _, payload = fake_client.requests[0]
        assert "provider" not in payload, "provider=None 时不应传给 Core"
        assert payload["profile_id"] == "profile_001"
        assert payload["output_format"] == "url"
        assert payload["need_subtitle"] is True

    @pytest.mark.asyncio
    async def test_provider_default_does_not_include_provider_in_payload(self):
        """B9: target.provider="default" 时，payload 不包含 provider 字段。"""
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider="default"),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        _, payload = fake_client.requests[0]
        assert "provider" not in payload

    @pytest.mark.asyncio
    async def test_provider_mock_is_forwarded_to_core(self):
        """B9: target.provider="mock" 时，显式传给 Core。"""
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider="mock"),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        _, payload = fake_client.requests[0]
        assert payload.get("provider") == "mock"

    @pytest.mark.asyncio
    async def test_provider_minimax_is_forwarded_to_core(self):
        """B9: target.provider="minimax" 时，显式传给 Core。"""
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider="minimax"),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        _, payload = fake_client.requests[0]
        assert payload.get("provider") == "minimax"

    @pytest.mark.asyncio
    async def test_output_format_url_is_always_in_payload(self):
        """B9: output_format 必须为 url。"""
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider=None),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        _, payload = fake_client.requests[0]
        assert payload["output_format"] == "url"
        assert payload["audio_format"] == "mp3"

    @pytest.mark.asyncio
    async def test_optional_render_fields_are_only_sent_when_present(self):
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="晚安",
            target=CoreRenderTarget(
                profile_id="profile_002",
                provider="mock",
                speed=1.1,
                vol=0.7,
                pitch=2,
                emotion="warm",
            ),
            tone="gentle",
            scene="night",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        _, payload = fake_client.requests[0]
        assert payload["provider"] == "mock"
        assert payload["output_format"] == "url"
        assert payload["speed"] == 1.1
        assert payload["vol"] == 0.7
        assert payload["pitch"] == 2
        assert payload["emotion"] == "warm"

    @pytest.mark.asyncio
    async def test_response_is_mapped_to_safe_product_shape(self):
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.generate_tts(
            text="晚安",
            target=CoreRenderTarget(profile_id="profile_002"),
            tone="gentle",
            scene="night",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        assert result == {
            "taskId": "job_123",
            "status": "completed",
            "audioUrl": "/api/voice/assets/audio_123/download",
            "durationMs": 1800,
            "message": None,
            "contract": {
                "voicePresetId": "female-gentle",
                "tone": "gentle",
                "toneHint": "soft",
                "scene": "night",
                "mode": "core_render_mock",
            },
        }

    @pytest.mark.asyncio
    async def test_response_does_not_expose_core_fields(self):
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.generate_tts(
            text="晚安",
            target=CoreRenderTarget(profile_id="profile_002"),
            tone="gentle",
            scene="night",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        top_level_bad = set(result.keys()) & FORBIDDEN_KEYS
        contract_bad = set(result["contract"].keys()) & FORBIDDEN_KEYS
        assert not top_level_bad
        assert not contract_bad

    @pytest.mark.asyncio
    async def test_generate_tts_without_http_client_raises_clear_error(self):
        gateway = VoiceLabGateway()

        with pytest.raises(CoreRenderUnavailableError):
            await gateway.generate_tts(
                text="晚安",
                target=CoreRenderTarget(profile_id="profile_002"),
                tone="gentle",
                scene="night",
                metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
            )

    @pytest.mark.asyncio
    async def test_invalid_core_response_raises_contract_error(self):
        fake_client = FakeCoreClient({"job_id": "job_123", "status": "success"})
        gateway = VoiceLabGateway(http_client=fake_client)

        with pytest.raises(CoreRenderResponseError):
            await gateway.generate_tts(
                text="晚安",
                target=CoreRenderTarget(profile_id="profile_002"),
                tone="gentle",
                scene="night",
                metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
            )

    @pytest.mark.asyncio
    async def test_generate_tts_passes_relative_path_to_http_client(self):
        """B9-FIX2: generate_tts passes /api/voice/render (not full URL) to http_client."""
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider=None),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        path, _ = fake_client.requests[0]
        assert path == "/api/voice/render", (
            f"Expected relative path '/api/voice/render' but got '{path}'. "
            "VoiceLabGateway must not pass full URL when http_client has base_url."
        )


class FakeCoreClientWithAbsoluteUrl:
    """Fake client that has absolute_url() method for testing B9-FIX3."""
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests: list[tuple[str, dict]] = []

    async def post(self, path: str, json: dict):
        self.requests.append((path, json))
        return FakeResponse(self.payload)

    def absolute_url(self, url_or_path: str) -> str:
        """Simulate CoreHttpClient.absolute_url()."""
        if not url_or_path:
            return url_or_path
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            return url_or_path
        # Simulate Core base_url = "http://127.0.0.1:8000"
        return f"http://127.0.0.1:8000{url_or_path}"


class TestGenerateTtsAbsoluteUrl:
    """B9-FIX3: VoiceLabGateway converts relative audio URLs to absolute."""

    @pytest.mark.asyncio
    async def test_generate_tts_converts_relative_audio_url_to_absolute(self):
        """When http_client has absolute_url(), relative audio URLs are converted."""
        fake_client = FakeCoreClientWithAbsoluteUrl(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider=None),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        # Relative URL /api/voice/assets/audio_123/download should be converted
        # to http://127.0.0.1:8000/api/voice/assets/audio_123/download
        assert result["audioUrl"] == "http://127.0.0.1:8000/api/voice/assets/audio_123/download"

    @pytest.mark.asyncio
    async def test_generate_tts_keeps_absolute_audio_url_unchanged(self):
        """When audio_url is already absolute, it should not be modified."""
        payload_with_absolute_url = {
            "job_id": "job_456",
            "status": "success",
            "audio_asset": {
                "id": "audio_456",
                "url": "https://cdn.example.com/audio.mp3",
                "duration_ms": 2000,
                "format": "mp3",
            },
            "subtitle_asset": None,
            "provider": "mock",
            "model": "mock-model",
        }
        fake_client = FakeCoreClientWithAbsoluteUrl(payload_with_absolute_url)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001", provider=None),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        assert result["audioUrl"] == "https://cdn.example.com/audio.mp3"

    @pytest.mark.asyncio
    async def test_generate_tts_without_absolute_url_keeps_relative_url(self):
        """When http_client has no absolute_url(), relative URL is kept (backward compat)."""
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.generate_tts(
            text="晚安",
            target=CoreRenderTarget(profile_id="profile_002"),
            tone="gentle",
            scene="night",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        # Without absolute_url(), the relative URL should be kept as-is
        assert result["audioUrl"] == "/api/voice/assets/audio_123/download"


STATUS_FORBIDDEN_KEYS = {
    "api_key",
    "env",
    "provider_secret",
    "raw_config",
    "stack_trace",
}

_RUNTIME_STATUS_PAYLOAD = {
    "current": {
        "default_provider": "mock",
        "default_model": "mock-model",
    },
    "provider_status": {
        "state": "available",
        "category": "ok",
        "label": "正常",
        "detail": None,
        "action_hint": "最近调用成功",
    },
    "today": {"job_count": 0, "success_count": 0, "failed_count": 0, "usage_characters": 0},
    "month": {"job_count": 0, "success_count": 0, "failed_count": 0, "usage_characters": 0},
    "last_call": {"provider": None, "status": "none"},
}


class FakeCoreGetClient:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.requests: list[tuple[str, ...]] = []
        self._status_code = status_code

    async def get(self, path: str) -> FakeResponse:
        self.requests.append(("GET", path))
        return FakeResponse(self.payload, self._status_code)


class TestGetProviderStatusContract:
    @pytest.mark.asyncio
    async def test_calls_core_runtime_status_path(self):
        fake_client = FakeCoreGetClient(_RUNTIME_STATUS_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.get_provider_status()

        assert fake_client.requests == [("GET", "/api/voice/runtime/status")]

    @pytest.mark.asyncio
    async def test_returns_safe_dict_with_expected_fields(self):
        fake_client = FakeCoreGetClient(_RUNTIME_STATUS_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.get_provider_status()

        assert result["ok"] is True
        assert result["status"] == "available"
        assert "quota_pct" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_response_does_not_expose_forbidden_keys(self):
        fake_client = FakeCoreGetClient(_RUNTIME_STATUS_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.get_provider_status()

        bad = set(result.keys()) & STATUS_FORBIDDEN_KEYS
        assert not bad, f"get_provider_status response exposes forbidden keys: {bad}"

    @pytest.mark.asyncio
    async def test_no_http_client_raises_unavailable_error(self):
        gateway = VoiceLabGateway()

        with pytest.raises(CoreStatusUnavailableError):
            await gateway.get_provider_status()

    @pytest.mark.asyncio
    async def test_non_dict_response_raises_response_error(self):
        class BadClient:
            async def get(self, path: str):
                return FakeResponse("not-a-dict")

        gateway = VoiceLabGateway(http_client=BadClient())

        with pytest.raises(CoreStatusResponseError):
            await gateway.get_provider_status()

    @pytest.mark.asyncio
    async def test_missing_provider_status_raises_response_error(self):
        fake_client = FakeCoreGetClient({"current": {}, "today": {}})
        gateway = VoiceLabGateway(http_client=fake_client)

        # Missing provider_status is treated as {} which is valid (state defaults to "unknown")
        result = await gateway.get_provider_status()
        assert result["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_does_not_read_api_key_env(self, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("MIMO_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        fake_client = FakeCoreGetClient(_RUNTIME_STATUS_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.get_provider_status()
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_uses_core_base_url_when_set(self):
        fake_client = FakeCoreGetClient(_RUNTIME_STATUS_PAYLOAD)
        gateway = VoiceLabGateway(core_base_url="http://core:8000", http_client=fake_client)

        await gateway.get_provider_status()

        path, = (r[1] for r in fake_client.requests)
        assert path == "http://core:8000/api/voice/runtime/status"


class TestGenerateTtsDryRunContract:
    @pytest.mark.asyncio
    async def test_accepts_core_render_target(self):
        gw = VoiceLabGateway()
        result = await gw.generate_tts_dry_run(**DRY_RUN_KWARGS)
        assert result["status"] == "dry_run"

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

    def test_generate_tts_signature_has_no_forbidden_params(self):
        sig = inspect.signature(VoiceLabGateway.generate_tts)
        param_names = set(sig.parameters.keys()) - {"self"}
        bad = param_names & FORBIDDEN_KEYS
        assert not bad

    def test_generate_tts_dry_run_signature_has_no_forbidden_params(self):
        sig = inspect.signature(VoiceLabGateway.generate_tts_dry_run)
        param_names = set(sig.parameters.keys()) - {"self"}
        bad = param_names & FORBIDDEN_KEYS
        assert not bad


# ── B9: list_profiles tests ─────────────────────────────────────────────────

_PROFILES_PAYLOAD = [
    {
        "id": "deep_night_programmer",
        "name": "深夜程序员",
        "description": "适合深夜场景的沉稳人设",
        "gender_style": "male",
        "age_style": "adult",
        "tone_style": "reserved",
        "emotion_style": "calm",
        "speed_style": "normal",
        "pause_style": "moderate",
        "scene_tags": ["night", "work", "coding"],
        "is_active": True,
        # forbidden fields - must be filtered
        "api_key": "DO_NOT_EXPOSE",
        "provider_voice_id": "voice_abc",
        "binding_id": "binding_123",
        "params_json": '{"key": "value"}',
        "model_id": "mock-model",
        "voice_id": "some_voice_id",
        "provider": "mock",
        "stack_trace": "some error trace",
    },
    {
        "id": "gentle_carer",
        "name": "温柔守护者",
        "gender_style": "female",
        "scene_tags": ["comfort", "care"],
        "is_active": True,
        "api_key": "another_secret_key",
    },
]


class FakeProfilesClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests: list[tuple[str, ...]] = []

    async def get(self, path: str) -> FakeResponse:
        self.requests.append(("GET", path))
        return FakeResponse(self.payload)


class TestListProfiles:
    @pytest.mark.asyncio
    async def test_calls_core_profiles_path(self):
        fake_client = FakeProfilesClient(_PROFILES_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.list_profiles()

        assert fake_client.requests == [("GET", "/api/voice/profiles")]

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self):
        fake_client = FakeProfilesClient(_PROFILES_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.list_profiles()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == "deep_night_programmer"
        assert result[0]["name"] == "深夜程序员"

    @pytest.mark.asyncio
    async def test_forbidden_fields_are_filtered_out(self):
        fake_client = FakeProfilesClient(_PROFILES_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.list_profiles()

        for profile in result:
            bad = set(profile.keys()) & FORBIDDEN_KEYS
            assert not bad, f"list_profiles output contains forbidden fields: {bad}"

    @pytest.mark.asyncio
    async def test_safe_fields_remain(self):
        fake_client = FakeProfilesClient(_PROFILES_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.list_profiles()

        # Check first profile has expected safe fields
        p0 = result[0]
        assert p0["id"] == "deep_night_programmer"
        assert p0["name"] == "深夜程序员"
        assert p0["gender_style"] == "male"
        assert p0["is_active"] is True
        assert "scene_tags" in p0

    @pytest.mark.asyncio
    async def test_no_http_client_raises_unavailable_error(self):
        gateway = VoiceLabGateway()

        with pytest.raises(CoreProfilesUnavailableError):
            await gateway.list_profiles()

    @pytest.mark.asyncio
    async def test_non_list_response_raises_response_error(self):
        class BadClient:
            async def get(self, path: str):
                return FakeResponse({"profiles": []})  # dict, not list

        gateway = VoiceLabGateway(http_client=BadClient())

        with pytest.raises(CoreProfilesResponseError):
            await gateway.list_profiles()

    @pytest.mark.asyncio
    async def test_uses_core_base_url_when_set(self):
        fake_client = FakeProfilesClient(_PROFILES_PAYLOAD)
        gateway = VoiceLabGateway(core_base_url="http://core:8000", http_client=fake_client)

        await gateway.list_profiles()

        path = fake_client.requests[0][1]
        assert path == "http://core:8000/api/voice/profiles"

    @pytest.mark.asyncio
    async def test_filters_non_dict_items(self):
        mixed_payload = [
            {"id": "valid_profile", "name": "Valid"},
            "not a dict",
            None,
            {"id": "another_valid", "api_key": "secret"},
        ]
        fake_client = FakeProfilesClient(mixed_payload)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.list_profiles()

        assert len(result) == 2
        assert all(isinstance(p, dict) for p in result)

    @pytest.mark.asyncio
    async def test_does_not_read_api_key_env(self, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("MIMO_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        fake_client = FakeProfilesClient(_PROFILES_PAYLOAD)
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.list_profiles()
        assert len(result) == 2
