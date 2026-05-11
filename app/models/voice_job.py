from sqlmodel import Field, SQLModel


class VoiceJob(SQLModel, table=True):
    __tablename__ = "voice_jobs"

    id: str = Field(primary_key=True)
    job_type: str
    status: str = Field(index=True)
    provider: str | None = None
    model: str | None = None
    profile_id: str | None = Field(default=None, index=True)
    binding_id: str | None = None
    input_text: str | None = None
    processed_text: str | None = None
    render_plan_json: str | None = None
    provider_trace_id: str | None = None
    response_json: str | None = None
    error_message: str | None = None
    created_at: str = Field(index=True)
    updated_at: str
