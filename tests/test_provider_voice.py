import json

from app.domain.schemas import ProviderVoiceListResponse, ProviderVoiceRead
from app.repositories.provider_voice_repo import (
    list_provider_voices,
    mark_missing_provider_voices_deprecated,
    upsert_provider_voice,
)


def test_provider_voice_schema_accepts_standard_fields():
    voice = ProviderVoiceRead(
        id="pv_test",
        provider="minimax",
        provider_voice_id="English_expressive_narrator",
        voice_type="system",
        name="English Expressive Narrator",
        metadata={"raw": True},
    )
    response = ProviderVoiceListResponse(provider="minimax", voices=[voice], total=1)
    assert response.voices[0].provider_voice_id == "English_expressive_narrator"
    assert response.voices[0].metadata["raw"] is True


def test_upsert_and_list_provider_voices(session):
    first = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="voice_a",
        voice_type="system",
        name="Voice A",
        metadata={"voice_id": "voice_a"},
    )
    second = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="voice_b",
        voice_type="voice_cloning",
        name="Voice B",
    )

    voices = list_provider_voices(session, provider="minimax")
    assert [voice.provider_voice_id for voice in voices] == ["voice_a", "voice_b"]
    assert json.loads(first.metadata_json)["voice_id"] == "voice_a"
    assert second.status == "available"

    system_voices = list_provider_voices(session, provider="minimax", voice_type="system")
    assert len(system_voices) == 1
    assert system_voices[0].provider_voice_id == "voice_a"


def test_upsert_updates_existing_provider_voice(session):
    created = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="voice_a",
        voice_type="system",
        name="Old Name",
    )
    updated = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="voice_a",
        voice_type="system",
        name="New Name",
    )
    assert updated.id == created.id
    assert updated.name == "New Name"
    assert len(list_provider_voices(session, provider="minimax")) == 1


def test_mark_missing_provider_voices_deprecated(session):
    upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="voice_a",
        voice_type="system",
    )
    upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="voice_b",
        voice_type="system",
    )

    changed = mark_missing_provider_voices_deprecated(
        session,
        provider="minimax",
        seen_provider_voice_ids={"voice_a"},
    )

    assert changed == 1
    available = list_provider_voices(session, provider="minimax")
    assert [voice.provider_voice_id for voice in available] == ["voice_a"]
    all_voices = list_provider_voices(session, provider="minimax", include_deprecated=True)
    deprecated = [voice for voice in all_voices if voice.provider_voice_id == "voice_b"][0]
    assert deprecated.status == "deprecated"
