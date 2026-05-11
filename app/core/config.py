from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Voice Lab"
    app_env: str = "dev"
    database_url: str = "sqlite:///./voice_lab.db"

    voice_provider: str = "minimax"
    minimax_api_key: str | None = None
    minimax_base_url: str = "https://api.minimaxi.com"
    minimax_t2a_path: str = "/v1/t2a_v2"
    minimax_default_model: str = "speech-2.8-hd"
    minimax_timeout_seconds: int = 120

    storage_dir: str = "./storage"
    default_audio_format: str = "mp3"
    default_sample_rate: int = 32000
    default_bitrate: int = 128000
    default_channel: int = 1

    mock_fallback_provider: str | None = "minimax"

    minimax_async_t2a_path: str = "/v1/t2a_async_v2"
    minimax_async_query_path: str = "/v1/query/t2a_async_query_v2"
    async_poll_interval_seconds: int = 5
    async_max_wait_seconds: int = 600

    minimax_file_upload_path: str = "/v1/files/upload"
    minimax_voice_clone_path: str = "/v1/voice_clone"

    minimax_voice_design_path: str = "/v1/voice_design"
    minimax_delete_voice_path: str = "/v1/delete_voice"
    clone_audio_max_size_mb: int = 20
    clone_audio_min_duration_sec: int = 10
    clone_audio_max_duration_sec: int = 300
    prompt_audio_max_duration_sec: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
