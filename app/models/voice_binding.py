from sqlmodel import Field, SQLModel

from app.domain.enums import BindingStatus


class VoiceBinding(SQLModel, table=True):
    __tablename__ = "voice_bindings"

    id: str = Field(primary_key=True)
    profile_id: str = Field(index=True)
    provider: str
    model: str
    provider_voice_id: str
    params_json: str = "{}"
    priority: int = 1
    status: str = BindingStatus.available
    created_at: str
    updated_at: str
