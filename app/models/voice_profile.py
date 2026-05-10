from sqlmodel import Field, SQLModel


class VoiceProfile(SQLModel, table=True):
    __tablename__ = "voice_profiles"

    id: str = Field(primary_key=True)
    name: str
    description: str | None = None
    gender_style: str | None = None
    age_style: str | None = None
    tone_style: str | None = None
    emotion_style: str | None = None
    speed_style: str | None = None
    pause_style: str | None = None
    scene_tags_json: str = "[]"
    is_active: bool = True
    created_at: str
    updated_at: str
