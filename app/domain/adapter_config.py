"""Adapter configuration schema for config-driven adapter default capabilities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


SENSITIVE_METADATA_KEYS = frozenset({
    "api_key", "apikey", "secret", "token", "password",
    "minimax_api_key", "openai_api_key",
})


class EndpointConfig(BaseModel):
    """API endpoint paths for an adapter."""

    t2a: str | None = None
    t2a_async: str | None = None
    query_async: str | None = None
    file_upload: str | None = None
    voice_clone: str | None = None
    voice_design: str | None = None
    delete_voice: str | None = None
    list_voices: str | None = None


class TTSCapabilityConfig(BaseModel):
    """TTS capability defaults for an adapter."""

    supported: bool = True
    models: list[str] = Field(default_factory=list)
    default_model: str | None = None
    max_text_chars: int = 10000
    audio_formats: list[str] = Field(default_factory=list)
    supports_subtitle: bool = False
    supports_streaming: bool = False
    supports_emotion: bool = False


class BatchCapabilityConfig(BaseModel):
    """Batch capability defaults for an adapter."""

    supported: bool = True
    max_text_chars: int = 50000
    max_segments: int | None = None


class ScriptCapabilityConfig(BaseModel):
    """Script capability defaults for an adapter."""

    supported: bool = True
    max_text_chars: int = 50000
    max_segments: int | None = None


class VoiceCloneCapabilityConfig(BaseModel):
    """Voice clone capability defaults for an adapter."""

    supported: bool = False
    preview_text_max: int | None = None
    supports_noise_reduction: bool = False
    supports_volume_normalization: bool = False
    max_file_size_mb: int | None = None


class VoiceDesignCapabilityConfig(BaseModel):
    """Voice design capability defaults for an adapter."""

    supported: bool = False
    prompt_max: int | None = None
    preview_text_max: int | None = None


class ProviderVoicesCapabilityConfig(BaseModel):
    """Provider voices capability defaults for an adapter."""

    supported: bool = True
    supports_list_voices: bool = True
    supports_delete_voice: bool = True
    supports_import_remote_voice: bool = True
    preview_text_max: int | None = None


class AdapterConfig(BaseModel):
    """Configuration schema for an adapter plugin's default capabilities.

    Loaded from config/adapters/{adapter_type}.yaml. Provides default
    capability values that can be overridden by ProviderConfig.
    """

    adapter_type: str = Field(
        ...,
        description="Unique adapter type identifier (matches adapter_type in providers.yaml)",
    )

    # API defaults
    default_base_url: str | None = None
    default_timeout_seconds: int = 120
    endpoints: EndpointConfig = Field(default_factory=EndpointConfig)

    # Model defaults
    default_model: str | None = None

    # Capability defaults
    tts: TTSCapabilityConfig | None = None
    batch: BatchCapabilityConfig | None = None
    script: ScriptCapabilityConfig | None = None
    voice_clone: VoiceCloneCapabilityConfig | None = None
    voice_design: VoiceDesignCapabilityConfig | None = None
    provider_voices: ProviderVoicesCapabilityConfig | None = None

    # Arbitrary non-secret metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_no_secret_metadata(self) -> AdapterConfig:
        """Ensure metadata does not contain secret values."""
        for key, value in self.metadata.items():
            lower_key = str(key).lower()
            if lower_key in SENSITIVE_METADATA_KEYS:
                raise ValueError(
                    f"AdapterConfig.metadata must not contain sensitive key: {key}"
                )
            if isinstance(value, str) and ("sk-" in value or "token" in lower_key):
                raise ValueError(
                    f"AdapterConfig.metadata value must not contain secret patterns: {key}"
                )
        return self

    model_config = {"extra": "forbid"}
