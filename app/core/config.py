from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Voice Lab"
    app_env: str = "dev"
    database_url: str = "sqlite:///./voice_lab.db"

    voice_provider: str = "minimax"
    minimax_api_key: str | None = None
    minimax_base_url: str = "https://api.minimax.io"
    minimax_t2a_path: str = "/v1/t2a_v2"
    minimax_default_model: str = "speech-2.8-hd"
    minimax_timeout_seconds: int = 120

    storage_dir: str = "./storage"
    default_audio_format: str = "mp3"
    default_sample_rate: int = 32000
    default_bitrate: int = 128000
    default_channel: int = 1

    enable_mock_provider: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
