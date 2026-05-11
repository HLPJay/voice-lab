from sqlmodel import Field, SQLModel, UniqueConstraint

from app.domain.enums import ProviderVoiceStatus


class ProviderVoice(SQLModel, table=True):
    __tablename__ = "provider_voices"
    __table_args__ = (UniqueConstraint("provider", "provider_voice_id", name="uq_provider_voice"),)

    id: str = Field(primary_key=True)
    provider: str = Field(index=True)
    provider_voice_id: str = Field(index=True)
    voice_type: str = Field(index=True)
    name: str | None = None
    description: str | None = None
    language: str | None = None
    gender: str | None = None
    status: str = Field(default=ProviderVoiceStatus.available, index=True)
    provider_created_time: str | None = None
    metadata_json: str = "{}"
    synced_at: str | None = None
    created_at: str
    updated_at: str
