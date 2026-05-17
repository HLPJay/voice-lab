from __future__ import annotations

import inspect

import pytest

from src.xiangta.services.voice_lab_gateway import (
    CoreRenderResponseError,
    CoreRenderTarget,
    CoreRenderUnavailableError,
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
    async def test_posts_to_core_render_contract_with_forced_mock_provider(self):
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        result = await gateway.generate_tts(
            text="想念你",
            target=CoreRenderTarget(profile_id="profile_001"),
            tone="gentle",
            scene="miss",
            metadata={"voicePresetId": "female-gentle", "toneHint": "soft"},
        )

        assert fake_client.requests == [
            (
                "/api/voice/render",
                {
                    "text": "想念你",
                    "profile_id": "profile_001",
                    "provider": "mock",
                    "need_subtitle": True,
                    "output_format": "url",
                    "audio_format": "mp3",
                    "confirm_cost": False,
                },
            )
        ]
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_optional_render_fields_are_only_sent_when_present(self):
        fake_client = FakeCoreClient(_success_payload())
        gateway = VoiceLabGateway(http_client=fake_client)

        await gateway.generate_tts(
            text="晚安",
            target=CoreRenderTarget(
                profile_id="profile_002",
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
