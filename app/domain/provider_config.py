"""Provider configuration schema for config-driven provider registry."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field, model_validator


SENSITIVE_METADATA_KEYS = frozenset({
    "api_key", "apikey", "secret", "token", "password",
    "minimax_api_key", "openai_api_key",
})


class EndpointConfig(BaseModel):
    tts: str | None = None
    t2a: str | None = None
    t2a_async: str | None = None
    query_async: str | None = None
    file_upload: str | None = None
    voice_clone: str | None = None
    voice_design: str | None = None
    delete_voice: str | None = None
    list_voices: str | None = None


class CapabilityToggle(BaseModel):
    enabled: bool = True


class TTSConfig(CapabilityToggle):
    default_model: str | None = None


class BatchConfig(CapabilityToggle):
    pass


class ScriptConfig(CapabilityToggle):
    pass


class VoiceCloneConfig(CapabilityToggle):
    pass


class VoiceDesignConfig(CapabilityToggle):
    pass


class ProviderVoicesConfig(CapabilityToggle):
    pass


class ProviderConfig(BaseModel):
    """Configuration schema for a single provider.

    Loaded from config/providers.yaml. Controls provider identity,
    adapter routing, cost behavior, and capability toggles.
    """

    # Core identity
    name: str = Field(..., description="Unique provider identifier (used in API and registry)")
    display_name: str = Field(..., description="Human-readable display name")

    # Lifecycle
    enabled: bool = Field(True, description="Whether this provider is active")

    # Adapter routing
    adapter_type: str = Field(
        ...,
        description="Adapter type key, maps to ADAPTER_TYPE_REGISTRY. "
                   "e.g. 'mock', 'minimax', 'openai', 'azure', 'volcengine', 'aliyun'",
    )

    # Cost behavior
    real_cost: bool = Field(
        False,
        description="Whether this provider incurs real costs (affects CostGuardService)",
    )

    # API configuration
    api_key_env: str | None = Field(
        None,
        description="Environment variable name containing the API key. "
                    "Never serialized to API responses.",
    )
    base_url_env: str | None = Field(
        None,
        description="Environment variable name containing the base URL override.",
    )
    base_url: str | None = Field(
        None,
        description="Default base URL for this provider (used if base_url_env not set)",
    )

    # API endpoints
    endpoints: EndpointConfig = Field(
        default_factory=EndpointConfig,
        description="API endpoint paths for this provider",
    )

    # Default model
    default_model: str | None = Field(
        None,
        description="Default model for this provider",
    )

    # Capability toggles (detailed capability specs are still built in Python)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    batch: BatchConfig = Field(default_factory=BatchConfig)
    script: ScriptConfig = Field(default_factory=ScriptConfig)
    voice_clone: VoiceCloneConfig = Field(default_factory=VoiceCloneConfig)
    voice_design: VoiceDesignConfig = Field(default_factory=VoiceDesignConfig)
    provider_voices: ProviderVoicesConfig = Field(default_factory=ProviderVoicesConfig)

    # Arbitrary non-secret metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def resolved_api_key(self) -> str | None:
        """Resolve API key from environment variable.

        Checks os.environ first, then falls back to .env file.
        """
        if not self.api_key_env:
            return None
        from app.config.env_resolver import resolve_env_value
        return resolve_env_value(self.api_key_env)

    @property
    def resolved_base_url(self) -> str | None:
        """Resolve base URL from env var or config.

        If base_url_env is set, resolves from environment (os.environ or .env).
        Otherwise returns base_url from config.
        """
        if self.base_url_env:
            from app.config.env_resolver import resolve_env_value
            return resolve_env_value(self.base_url_env)
        return self.base_url

    @model_validator(mode="after")
    def validate_no_secret_metadata(self) -> ProviderConfig:
        """Ensure metadata does not contain secret values."""
        for key, value in self.metadata.items():
            lower_key = str(key).lower()
            if lower_key in SENSITIVE_METADATA_KEYS:
                raise ValueError(
                    f"ProviderConfig.metadata must not contain sensitive key: {key}"
                )
            if isinstance(value, str) and ("sk-" in value or "token" in lower_key):
                raise ValueError(
                    f"ProviderConfig.metadata value must not contain secret patterns: {key}"
                )
        return self

    model_config = {"extra": "forbid"}
