from sqlmodel import Field, SQLModel


class BatchJob(SQLModel, table=True):
    __tablename__ = "batch_jobs"

    id: str = Field(primary_key=True)
    mode: str  # "longtext" | "script"
    status: str = "pending"  # pending/running/success/partial/failed
    provider: str | None = None
    output_format: str = "mp3"
    total_segments: int = 0
    completed_segments: int = 0
    failed_segments: int = 0
    merged_audio_asset_id: str | None = None
    merged_subtitle_asset_id: str | None = None
    silence_between_ms: int = 300
    config_json: str = "{}"
    error_message: str | None = None
    created_at: str
    updated_at: str


class BatchSegment(SQLModel, table=True):
    __tablename__ = "batch_segments"

    id: str = Field(primary_key=True)
    batch_job_id: str = Field(index=True)
    index: int  # 顺序号
    text: str
    profile_id: str
    role: str | None = None  # 角色名（剧本模式）
    params_json: str = "{}"  # 该段参数覆盖
    status: str = "pending"  # pending/running/success/failed
    voice_job_id: str | None = None
    audio_asset_id: str | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str