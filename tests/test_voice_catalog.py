import pytest

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
