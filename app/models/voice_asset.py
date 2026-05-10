from sqlmodel import Field, SQLModel


class AudioAsset(SQLModel, table=True):
    __tablename__ = "audio_assets"

    id: str = Field(primary_key=True)
    job_id: str = Field(index=True)
    provider: str | None = None
    model: str | None = None
    file_path: str
    file_url: str | None = None
    format: str | None = None
    duration_ms: int | None = None
    sample_rate: int | None = None
    bitrate: int | None = None
    channel: int | None = None
    usage_characters: int | None = None
    metadata_json: str = "{}"
    created_at: str


class SubtitleAsset(SQLModel, table=True):
    __tablename__ = "subtitle_assets"

    id: str = Field(primary_key=True)
    job_id: str = Field(index=True)
    audio_asset_id: str | None = None
    subtitle_type: str | None = None
    file_path: str | None = None
    srt_path: str | None = None
    timeline_json: str = "[]"
    created_at: str
