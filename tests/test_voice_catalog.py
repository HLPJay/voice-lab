import pytest

from app.core.errors import ProviderNotConfigured
from app.repositories.provider_voice_repo import upsert_provider_voice
from app.services.voice_catalog_service import VoiceCatalogService


@pytest.mark.asyncio
async def test_mock_adapter_list_voices_filters_by_type():
    from app.providers.mock_speech_adapter import MockSpeechAdapter

    adapter = MockSpeechAdapter()
    all_voices = await adapter.list_voices()
    system_voices = await adapter.list_voices(voice_type="system")

    assert len(all_voices) == 3
    assert len(system_voices) == 1
    assert system_voices[0].voice_type == "system"


@pytest.mark.asyncio
async def test_voice_catalog_refresh_upserts_mock_voices(session):
    service = VoiceCatalogService()

    response = await service.list_provider_voices(session, provider="mock", refresh=True)

    assert response.provider == "mock"
    assert response.voice_type == "all"
    assert response.total == 3
    assert {voice.voice_type for voice in response.voices} == {"system", "voice_cloning", "voice_generation"}


@pytest.mark.asyncio
async def test_voice_catalog_reads_cache_without_refresh(session):
    upsert_provider_voice(
        session,
        provider="mock",
        provider_voice_id="cached_voice",
        voice_type="system",
        name="Cached Voice",
    )
    service = VoiceCatalogService()

    response = await service.list_provider_voices(session, provider="mock", refresh=False)

    assert response.total == 1
    assert response.voices[0].provider_voice_id == "cached_voice"


@pytest.mark.asyncio
async def test_voice_catalog_empty_cache_does_not_auto_refresh(session):
    service = VoiceCatalogService()

    response = await service.list_provider_voices(session, provider="mock", refresh=False)

    assert response.total == 0
    assert response.synced_at is None
    assert response.voices == []


def test_provider_voices_api_refreshes_mock_catalog(test_app):
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    response = client.get("/api/voice/provider-voices?provider=mock&refresh=true")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["voice_type"] == "all"
    assert data["total"] == 3
    assert {voice["voice_type"] for voice in data["voices"]} == {"system", "voice_cloning", "voice_generation"}


def test_provider_voices_api_reads_empty_minimax_cache_without_network(test_app):
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    response = client.get("/api/voice/provider-voices?provider=minimax")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "minimax"
    assert data["total"] == 0
    assert data["voices"] == []


@pytest.mark.asyncio
async def test_minimax_list_voices_requires_api_key(monkeypatch):
    from app.providers import minimax_speech_adapter
    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    class MissingKeySettings:
        minimax_api_key = None
        minimax_base_url = "https://api.minimaxi.com"
        minimax_timeout_seconds = 120

    monkeypatch.setattr(minimax_speech_adapter, "get_settings", lambda: MissingKeySettings())

    adapter = MiniMaxSpeechAdapter()

    with pytest.raises(ProviderNotConfigured):
        await adapter.list_voices()


def test_minimax_voice_response_conversion():
    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    adapter = MiniMaxSpeechAdapter()
    voices = adapter._convert_voice_response(
        {
            "system_voice": [
                {
                    "voice_id": "Chinese (Mandarin)_News_Anchor",
                    "voice_name": "新闻女声",
                    "description": ["一位专业、播音腔的中年女性新闻主播，标准普通话。"],
                    "created_time": "1970-01-01",
                }
            ],
            "voice_cloning": [{"voice_id": "clone_1", "description": [], "created_time": "2025-08-20"}],
            "voice_generation": [{"voice_id": "gen_1", "description": [], "created_time": "2025-08-21"}],
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }
    )

    assert [voice.voice_type for voice in voices] == ["system", "voice_cloning", "voice_generation"]
    assert voices[0].provider_voice_id == "Chinese (Mandarin)_News_Anchor"
    assert voices[0].name == "新闻女声"
    assert voices[0].description == "一位专业、播音腔的中年女性新闻主播，标准普通话。"
