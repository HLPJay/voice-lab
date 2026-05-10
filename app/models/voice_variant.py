from sqlmodel import Field, SQLModel


class VoiceVariantGroup(SQLModel, table=True):
    __tablename__ = "voice_variant_groups"

    id: str = Field(primary_key=True)
    scene: str | None = None
    input_text: str | None = None
    selected_variant_id: str | None = None
    created_at: str
    updated_at: str


class VoiceVariant(SQLModel, table=True):
    __tablename__ = "voice_variants"

    id: str = Field(primary_key=True)
    group_id: str = Field(index=True)
    job_id: str
    profile_id: str | None = None
    audio_asset_id: str | None = None
    speed: float | None = None
    emotion: str | None = None
    score: float | None = None
    selected: bool = False
    comment: str | None = None
    created_at: str
