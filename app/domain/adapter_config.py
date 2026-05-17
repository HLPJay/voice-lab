"""Adapter configuration schema for config-driven adapter default capabilities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


SENSITIVE_METADATA_KEYS = frozenset({
    "api_key", "apikey", "secret", "token", "password",
    "minimax_api_key", "openai_api_key",
})


class AdapterPluginConfig(BaseModel):
    """Plugin configuration for dynamically loading an adapter class.

    Loaded from config/adapters/{adapter_type}.yaml plugin.import_path.
    """

    import_path: str = Field(
        ...,
        description="Python import path to the adapter class (e.g. 'app.providers.mock_speech_adapter.MockSpeechAdapter')",
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_import_path(self) -> AdapterPluginConfig:
        """Validate import_path is non-empty and starts with app.providers."""
        if not self.import_path or not self.import_path.strip():
            raise ValueError("plugin.import_path must not be empty")
        if not self.import_path.startswith("app.providers."):
            raise ValueError("plugin.import_path must start with 'app.providers.'")
        parts = self.import_path.rsplit(".", 1)
        if len(parts) != 2 or not parts[1]:
            raise ValueError(
                "plugin.import_path must be in the format 'module.path.ClassName'"
            )
        class_name = parts[1]
        if not class_name[0].isupper():
            raise ValueError(
                "plugin.import_path class name must start with an uppercase letter "
                f"(e.g. 'MockSpeechAdapter'), got: {class_name}"
            )
        return self


class EndpointConfig(BaseModel):
    """API endpoint paths for an adapter."""

    tts: str | None = None
    t2a: str | None = None
    t2a_async: str | None = None
    query_async: str | None = None
    file_upload: str | None = None
    voice_clone: str | None = None
    voice_design: str | None = None
    delete_voice: str | None = None
    list_voices: str | None = None


class NumericRangeConfig(BaseModel):
    """Numeric range (min/max) for parameter constraints."""

    min: float
    max: float

    @model_validator(mode="after")
    def validate_range(self) -> NumericRangeConfig:
        if self.min > self.max:
            raise ValueError("NumericRangeConfig.min must be <= max")
        return self


class VoiceIdConfig(BaseModel):
    """Voice ID format constraints."""

    min_length: int = 8
    max_length: int = 256
    pattern: str | None = None
    hint: str | None = None

    @model_validator(mode="after")
    def validate_lengths(self) -> VoiceIdConfig:
        if self.min_length <= 0:
            raise ValueError("VoiceIdConfig.min_length must be > 0")
        if self.max_length < self.min_length:
            raise ValueError("VoiceIdConfig.max_length must be >= min_length")
        return self


class WebSocketConfig(BaseModel):
    """WebSocket connection configuration."""

    url: str | None = None
    model: str | None = None
    timeout_seconds: int = 120


class TTSCapabilityConfig(BaseModel):
    """TTS capability defaults for an adapter."""

    supported: bool = True
    models: list[str] = Field(default_factory=list)
    default_model: str | None = None
    max_text_chars: int = 10000
    audio_formats: list[str] = Field(default_factory=list)
    supports_subtitle: bool = False
    supports_streaming: bool = False
    supports_async: bool = False
    supports_emotion: bool = False
    speed: NumericRangeConfig | None = None
    vol: NumericRangeConfig | None = None
    pitch: NumericRangeConfig | None = None


class BatchCapabilityConfig(BaseModel):
    """Batch capability defaults for an adapter."""

    supported: bool = True
    max_text_chars: int = 50000
    max_segments: int | None = None
    segment_strategies: list[str] = Field(default_factory=list)
    max_segment_chars: NumericRangeConfig | None = None
    silence_between_ms: NumericRangeConfig | None = None
    supports_merge_audio: bool = True
    supports_merge_subtitle: bool = True


class ScriptCapabilityConfig(BaseModel):
    """Script capability defaults for an adapter."""

    supported: bool = True
    max_text_chars: int = 50000
    max_segments: int | None = None
    segment_strategies: list[str] = Field(default_factory=list)
    max_segment_chars: NumericRangeConfig | None = None
    silence_between_ms: NumericRangeConfig | None = None
    supports_merge_audio: bool = True
    supports_merge_subtitle: bool = True


class VoiceCloneCapabilityConfig(BaseModel):
    """Voice clone capability defaults for an adapter."""

    supported: bool = False
    preview_text_max: int | None = None
    supports_noise_reduction: bool = False
    supports_volume_normalization: bool = False
    max_file_size_mb: int | None = None
    voice_id: VoiceIdConfig | None = None


class VoiceDesignCapabilityConfig(BaseModel):
    """Voice design capability defaults for an adapter."""

    supported: bool = False
    prompt_max: int | None = None
    preview_text_max: int | None = None
    voice_id: VoiceIdConfig | None = None


class StaticVoiceConfig(BaseModel):
    """Static voice configuration for preset/system voices."""

    voice_id: str = Field(
        ...,
        description="Voice ID used in API calls (e.g., '冰糖')",
    )
    name: str = Field(..., description="Display name of the voice")
    language: str = Field(..., description="Language code (e.g., 'zh', 'en')")
    gender: str | None = Field(None, description="Gender: 'female', 'male', or 'neutral'")
    description: str | None = Field(None, description="Optional description of the voice")


class ProviderVoicesCapabilityConfig(BaseModel):
    """Provider voices capability defaults for an adapter."""

    supported: bool = True
    supports_list_voices: bool = True
    supports_delete_voice: bool = True
    supports_import_remote_voice: bool = True
    preview_text_max: int | None = None
    static_voices: list[StaticVoiceConfig] = Field(default_factory=list)


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

    # WebSocket configuration
    websocket: WebSocketConfig | None = None

    # Plugin for dynamic class loading
    plugin: AdapterPluginConfig | None = Field(default=None)

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
