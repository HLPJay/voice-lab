from sqlmodel import Field, SQLModel


class VoiceBinding(SQLModel, table=True):
    __tablename__ = "voice_bindings"

    id: str = Field(primary_key=True)
    profile_id: str = Field(index=True)
    provider: str
    model: str
    provider_voice_id: str
    params_json: str = "{}"
    priority: int = 1
    status: str = "available"
    created_at: str
    updated_at: str
