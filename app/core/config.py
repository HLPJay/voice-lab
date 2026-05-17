from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Voice Lab"
    app_env: str = "dev"
    database_url: str = "sqlite:///./voice_lab.db"

    voice_provider: str = "minimax"
    minimax_api_key: str | None = None
    minimax_default_model: str = "speech-2.8-hd"

    storage_dir: str = "./storage"
    default_audio_format: str = "mp3"
    default_sample_rate: int = 32000
    default_bitrate: int = 128000
    default_channel: int = 1

    mock_fallback_provider: str | None = None

    async_poll_interval_seconds: int = 5
    async_max_wait_seconds: int = 600

    clone_audio_max_size_mb: int = 20
    batch_max_concurrency: int = 5

    log_level: str = "INFO"
    log_format: str = "json"
    log_dir: str = "./logs"
    log_retention_days: int = 30

    provider_retry_max_attempts: int = 3
    provider_retry_backoff_base: float = 1.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache. Useful in tests when env vars change."""
    get_settings.cache_clear()
