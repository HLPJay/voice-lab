from sqlmodel import Field, SQLModel


class ProviderCallLog(SQLModel, table=True):
    __tablename__ = "provider_call_logs"

    id: str = Field(primary_key=True)
    request_id: str | None = None
    job_id: str | None = None
    provider: str = Field(index=True)
    api_path: str
    method: str
    status_code: int | None = None
    duration_ms: int | None = None
    provider_trace_id: str | None = None
    usage_characters: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    created_at: str = Field(index=True)
