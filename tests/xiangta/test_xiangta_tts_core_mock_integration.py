from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.config.product_config_repository import ProductConfigRepository
from src.xiangta.services.product_service import ProductService
from src.xiangta.services.tone_preset_service import TonePresetService
from src.xiangta.services.tts_orchestrator import TtsOrchestrator
from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService


FORBIDDEN_KEYS = {
    "profile_id",
    "coreProfileId",
    "provider",
    "model",
    "provider_voice_id",
    "binding_id",
    "params_json",
    "api_key",
}


class InProcessCoreResponse:
    def __init__(self, response) -> None:
        self._response = response
        self.status_code = response.status_code

    def json(self):
        return self._response.json()

    def raise_for_status(self):
        self._response.raise_for_status()


class InProcessCoreClient:
    def __init__(self, app) -> None:
        self._client = TestClient(app)
        self.requests: list[tuple[str, dict]] = []

    async def post(self, path: str, json: dict):
        self.requests.append((path, json))
        return InProcessCoreResponse(self._client.post(path, json=json))


class FakeProductConfigRepository(ProductConfigRepository):
    def get_voice_mapping(self, voice_preset_id: str):
        mapping = super().get_voice_mapping(voice_preset_id)
        return replace(
            mapping,
            core_profile_id="deep_night_programmer",
            provider_policy="mock",
        )


def _collect_keys(obj, seen=None):
    if seen is None:
        seen = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            seen.add(key)
            _collect_keys(value, seen)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, seen)
    return seen


def _build_xiangta_service(core_app, *, use_dry_run: bool = False):
    repository = FakeProductConfigRepository()
    gateway = VoiceLabGateway(http_client=InProcessCoreClient(core_app))
    tts = TtsOrchestrator(
        gateway=gateway,
        voice_mapping_service=VoicePresetMappingService(config_repository=repository),
        tone_preset_service=TonePresetService(config_repository=repository),
        max_tts_chars=repository.get_limits().max_tts_chars,
        use_dry_run=use_dry_run,
    )
    return ProductService(
        bootstrap=MagicMock(),
        provider_status=MagicMock(),
        tts=tts,
    ), gateway


def test_xiangta_tts_returns_core_mock_audio_url(test_app, seed_mock_binding, monkeypatch):
    _ = seed_mock_binding
    xiangta_app = FastAPI()
    xiangta_app.include_router(router)
    service, gateway = _build_xiangta_service(test_app)

    import src.xiangta.api.routes as routes_module

    monkeypatch.setattr(routes_module, "create_product_service", lambda: service)
    client = TestClient(xiangta_app)

    response = client.post(
        "/api/xiangta/tts",
        json={
            "text": "想念你",
            "voicePreset": "female-gentle",
            "tone": "gentle",
            "recipient": "lover",
            "scene": "miss",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["status"] == "completed"
    assert body["data"]["taskId"]
    assert body["data"]["audioUrl"].startswith("/api/voice/assets/")
    assert body["data"]["audioUrl"].endswith("/download")
    assert body["data"]["durationMs"] > 0
    assert body["data"]["voicePreset"] == "female-gentle"
    assert body["data"]["tone"] == "gentle"
    assert body["data"]["contract"]["mode"] == "core_render_mock"
    assert body["data"]["contract"]["voicePresetId"] == "female-gentle"

    bad = _collect_keys(body) & FORBIDDEN_KEYS
    assert not bad, f"XiangTa /tts response leaked forbidden fields: {bad}"

    assert gateway._http_client.requests  # boundary assertion for the in-process client
    path, payload = gateway._http_client.requests[0]
    assert path == "/api/voice/render"
    assert payload["provider"] == "mock"
    assert payload["profile_id"] == "deep_night_programmer"
    assert payload["output_format"] == "url"


def test_xiangta_tts_mock_path_does_not_require_real_api_keys(
    test_app, seed_mock_binding, monkeypatch
):
    _ = seed_mock_binding
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("MIMO_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    xiangta_app = FastAPI()
    xiangta_app.include_router(router)
    service, _gateway = _build_xiangta_service(test_app)

    import src.xiangta.api.routes as routes_module

    monkeypatch.setattr(routes_module, "create_product_service", lambda: service)
    client = TestClient(xiangta_app)

    response = client.post(
        "/api/xiangta/tts",
        json={
            "text": "想念你",
            "voicePreset": "female-gentle",
            "tone": "gentle",
            "recipient": "lover",
            "scene": "miss",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"
