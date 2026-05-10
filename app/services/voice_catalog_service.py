import json

from sqlmodel import Session

from app.domain.schemas import ProviderVoiceListResponse, ProviderVoiceRead
from app.models.provider_voice import ProviderVoice
from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
from app.providers.mock_speech_adapter import MockSpeechAdapter
from app.repositories.provider_voice_repo import (
    list_provider_voices,
    mark_missing_provider_voices_deprecated,
    upsert_provider_voice,
)


class VoiceCatalogService:
    def _provider(self, provider: str):
        if provider == "mock":
            return MockSpeechAdapter()
        if provider == "minimax":
            return MiniMaxSpeechAdapter()
        raise ValueError(f"Unsupported provider: {provider}")

    def _to_read(self, item: ProviderVoice) -> ProviderVoiceRead:
        return ProviderVoiceRead(
            id=item.id,
            provider=item.provider,
            provider_voice_id=item.provider_voice_id,
            voice_type=item.voice_type,
            name=item.name,
            description=item.description,
            language=item.language,
            gender=item.gender,
            status=item.status,
            provider_created_time=item.provider_created_time,
            metadata=json.loads(item.metadata_json or "{}"),
            synced_at=item.synced_at,
        )

    def _response(self, provider: str, voice_type: str, items: list[ProviderVoice]) -> ProviderVoiceListResponse:
        voices = [self._to_read(item) for item in items]
        synced_at = max((voice.synced_at for voice in voices if voice.synced_at), default=None)
        return ProviderVoiceListResponse(
            provider=provider,
            voice_type=voice_type,
            voices=voices,
            synced_at=synced_at,
            total=len(voices),
        )

    async def list_provider_voices(
        self,
        session: Session,
        *,
        provider: str,
        voice_type: str = "all",
        refresh: bool = False,
    ) -> ProviderVoiceListResponse:
        if refresh:
            adapter = self._provider(provider)
            provider_voices = await adapter.list_voices(voice_type=voice_type)
            seen_ids: set[str] = set()
            for voice in provider_voices:
                seen_ids.add(voice.provider_voice_id)
                upsert_provider_voice(
                    session,
                    provider=provider,
                    provider_voice_id=voice.provider_voice_id,
                    voice_type=voice.voice_type,
                    name=voice.name,
                    description=voice.description,
                    language=voice.language,
                    gender=voice.gender,
                    status=voice.status,
                    provider_created_time=voice.provider_created_time,
                    metadata=voice.metadata,
                    synced_at=voice.synced_at,
                )
            if voice_type == "all":
                mark_missing_provider_voices_deprecated(
                    session,
                    provider=provider,
                    seen_provider_voice_ids=seen_ids,
                )

        items = list_provider_voices(session, provider=provider, voice_type=voice_type)
        return self._response(provider, voice_type, items)
