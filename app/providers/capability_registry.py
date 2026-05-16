"""Capability registry: provides ProviderCapability for each provider.

Built from config/providers.yaml + config/adapters/*.yaml + adapter_type capability builders.
The /api/voice/capabilities response format is unchanged.
"""

from app.core.errors import UnsupportedProvider
from app.domain.capabilities import ProviderCapability
from app.config.provider_config_loader import list_enabled_provider_configs
from app.config.adapter_config_loader import get_adapter_config
from app.providers.mock_capabilities import MOCK_CAPABILITY
from app.providers.minimax_capabilities import build_minimax_capability

# Maps adapter_type -> capability builder function
_CAPABILITY_BUILDERS: dict[str, callable] = {
    "mock": lambda: MOCK_CAPABILITY,
    "minimax": build_minimax_capability,
}


def _build_capability_from_config(config) -> ProviderCapability:
    """Build ProviderCapability from a ProviderConfig + AdapterConfig + builder.

    Merge rules:
    1. Start with base capability from adapter_type builder (fallback)
    2. Override with AdapterConfig defaults (from config/adapters/*.yaml)
    3. Override with ProviderConfig values (highest priority)

    Args:
        config: ProviderConfig object.

    Returns:
        ProviderCapability with merged config.
    """
    # Get AdapterConfig if available
    adapter_config = get_adapter_config(config.adapter_type)

    # Get base capability from builder (fallback)
    builder = _CAPABILITY_BUILDERS.get(config.adapter_type)
    if builder:
        base_capability = builder()
    else:
        base_capability = None

    # Start building the final capability
    # Priority: ProviderConfig > AdapterConfig > builder fallback

    # default_model: ProviderConfig first, then AdapterConfig, then builder
    default_model = config.default_model
    if not default_model and adapter_config:
        default_model = adapter_config.default_model
    if not default_model and base_capability:
        default_model = base_capability.default_model

    # Build TTS capability with merge rules
    # Priority: ProviderConfig.enabled (highest) > AdapterConfig > builder fallback
    tts_cap = None
    if base_capability and base_capability.tts:
        tts_builder = base_capability.tts
    else:
        from app.domain.capabilities import TTSCapability
        tts_builder = TTSCapability(supported=False)

    # Check if provider explicitly disables TTS
    provider_tts_disabled = config.tts and not config.tts.enabled

    if provider_tts_disabled:
        # Provider-level TTS disabled - must respect, do not re-enable via AdapterConfig
        from app.domain.capabilities import TTSCapability
        tts_cap = TTSCapability(supported=False)
    elif config.tts and config.tts.enabled:
        # Provider-level TTS enabled - merge with builder/AdapterConfig
        from app.domain.capabilities import TTSCapability

        tts_models = None
        tts_default_model = None
        tts_max_chars = tts_builder.max_text_chars
        tts_audio_formats = list(tts_builder.audio_formats)
        tts_supports_subtitle = tts_builder.supports_subtitle
        tts_supports_streaming = tts_builder.supports_streaming
        tts_supports_emotion = tts_builder.supports_emotion

        if adapter_config and adapter_config.tts:
            tts_models = adapter_config.tts.models
            tts_default_model = adapter_config.tts.default_model
            tts_max_chars = adapter_config.tts.max_text_chars
            tts_audio_formats = adapter_config.tts.audio_formats
            tts_supports_subtitle = adapter_config.tts.supports_subtitle
            tts_supports_streaming = adapter_config.tts.supports_streaming
            tts_supports_emotion = adapter_config.tts.supports_emotion

        tts_cap = TTSCapability(
            supported=True,
            models=tts_models or list(tts_builder.models),
            default_model=tts_default_model or config.default_model or tts_builder.default_model,
            max_text_chars=tts_max_chars,
            audio_formats=tts_audio_formats,
            supports_subtitle=tts_supports_subtitle,
            supports_streaming=tts_supports_streaming,
            supports_emotion=tts_supports_emotion,
            speed=tts_builder.speed,
            vol=tts_builder.vol,
            pitch=tts_builder.pitch,
        )
    elif adapter_config and adapter_config.tts and adapter_config.tts.supported:
        # Adapter has TTS config and says supported - use AdapterConfig
        from app.domain.capabilities import TTSCapability
        tts_a = adapter_config.tts
        tts_cap = TTSCapability(
            supported=True,
            models=tts_a.models or list(tts_builder.models),
            default_model=tts_a.default_model or tts_builder.default_model,
            max_text_chars=tts_a.max_text_chars,
            audio_formats=tts_a.audio_formats,
            supports_subtitle=tts_a.supports_subtitle,
            supports_streaming=tts_a.supports_streaming,
            supports_emotion=tts_a.supports_emotion,
            speed=tts_builder.speed,
            vol=tts_builder.vol,
            pitch=tts_builder.pitch,
        )
    else:
        # Use builder's TTS
        tts_cap = tts_builder

    # Build Batch capability
    # Priority: ProviderConfig.enabled (highest) > AdapterConfig > builder fallback
    batch_cap = None
    if base_capability and base_capability.batch:
        batch_builder = base_capability.batch
    else:
        from app.domain.capabilities import BatchCapability
        batch_builder = BatchCapability(supported=False)

    # Check if provider explicitly disables batch
    provider_batch_disabled = config.batch and not config.batch.enabled

    if provider_batch_disabled:
        # Provider-level batch disabled - must respect, do not re-enable via AdapterConfig
        from app.domain.capabilities import BatchCapability
        batch_cap = BatchCapability(supported=False)
    elif config.batch and config.batch.enabled:
        from app.domain.capabilities import BatchCapability

        batch_max_chars = batch_builder.max_text_chars
        batch_max_segs = batch_builder.max_segments
        if adapter_config and adapter_config.batch:
            batch_max_chars = adapter_config.batch.max_text_chars
            batch_max_segs = adapter_config.batch.max_segments

        batch_cap = BatchCapability(
            supported=True,
            max_text_chars=batch_max_chars,
            max_segments=batch_max_segs,
            segment_strategies=list(batch_builder.segment_strategies) if batch_builder.segment_strategies else [],
            max_segment_chars=batch_builder.max_segment_chars,
            silence_between_ms=batch_builder.silence_between_ms,
            supports_merge_audio=batch_builder.supports_merge_audio,
            supports_merge_subtitle=batch_builder.supports_merge_subtitle,
        )
    elif adapter_config and adapter_config.batch and adapter_config.batch.supported:
        from app.domain.capabilities import BatchCapability
        b_a = adapter_config.batch
        batch_cap = BatchCapability(
            supported=True,
            max_text_chars=b_a.max_text_chars,
            max_segments=b_a.max_segments,
            segment_strategies=list(batch_builder.segment_strategies) if batch_builder.segment_strategies else [],
            max_segment_chars=batch_builder.max_segment_chars,
            silence_between_ms=batch_builder.silence_between_ms,
            supports_merge_audio=batch_builder.supports_merge_audio,
            supports_merge_subtitle=batch_builder.supports_merge_subtitle,
        )
    else:
        batch_cap = batch_builder

    # Build Script capability
    # Priority: ProviderConfig.enabled (highest) > AdapterConfig > builder fallback
    script_cap = None
    if base_capability and base_capability.script:
        script_builder = base_capability.script
    else:
        from app.domain.capabilities import BatchCapability
        script_builder = BatchCapability(supported=False)

    # Check if provider explicitly disables script
    provider_script_disabled = config.script and not config.script.enabled

    if provider_script_disabled:
        # Provider-level script disabled - must respect, do not re-enable via AdapterConfig
        from app.domain.capabilities import BatchCapability
        script_cap = BatchCapability(supported=False)
    elif config.script and config.script.enabled:
        from app.domain.capabilities import BatchCapability

        script_max_chars = script_builder.max_text_chars
        script_max_segs = script_builder.max_segments
        if adapter_config and adapter_config.script:
            script_max_chars = adapter_config.script.max_text_chars
            script_max_segs = adapter_config.script.max_segments

        script_cap = BatchCapability(
            supported=True,
            max_text_chars=script_max_chars,
            max_segments=script_max_segs,
            segment_strategies=["line"],
            max_segment_chars=script_builder.max_segment_chars,
            silence_between_ms=script_builder.silence_between_ms,
            supports_merge_audio=script_builder.supports_merge_audio,
            supports_merge_subtitle=script_builder.supports_merge_subtitle,
        )
    elif adapter_config and adapter_config.script and adapter_config.script.supported:
        from app.domain.capabilities import BatchCapability
        s_a = adapter_config.script
        script_cap = BatchCapability(
            supported=True,
            max_text_chars=s_a.max_text_chars,
            max_segments=s_a.max_segments,
            segment_strategies=["line"],
            max_segment_chars=script_builder.max_segment_chars,
            silence_between_ms=script_builder.silence_between_ms,
            supports_merge_audio=script_builder.supports_merge_audio,
            supports_merge_subtitle=script_builder.supports_merge_subtitle,
        )
    else:
        script_cap = script_builder

    # Build VoiceClone capability - respect ProviderConfig enabled=false
    from app.domain.capabilities import VoiceCloneCapability
    voice_clone_cap = None
    if base_capability and base_capability.voice_clone:
        voice_clone_builder = base_capability.voice_clone
    else:
        voice_clone_builder = VoiceCloneCapability(supported=False)

    provider_vc_disabled = config.voice_clone and not config.voice_clone.enabled
    if provider_vc_disabled:
        voice_clone_cap = VoiceCloneCapability(supported=False)
    else:
        voice_clone_cap = voice_clone_builder

    # Build VoiceDesign capability - respect ProviderConfig enabled=false
    from app.domain.capabilities import VoiceDesignCapability
    voice_design_cap = None
    if base_capability and base_capability.voice_design:
        voice_design_builder = base_capability.voice_design
    else:
        voice_design_builder = VoiceDesignCapability(supported=False)

    provider_vd_disabled = config.voice_design and not config.voice_design.enabled
    if provider_vd_disabled:
        voice_design_cap = VoiceDesignCapability(supported=False)
    else:
        voice_design_cap = voice_design_builder

    # Build ProviderVoices capability - respect ProviderConfig enabled=false
    from app.domain.capabilities import ProviderVoiceCapability
    provider_voices_cap = None
    if base_capability and base_capability.provider_voices:
        provider_voices_builder = base_capability.provider_voices
    else:
        provider_voices_builder = ProviderVoiceCapability(supported=False)

    provider_pv_disabled = config.provider_voices and not config.provider_voices.enabled
    if provider_pv_disabled:
        provider_voices_cap = ProviderVoiceCapability(supported=False)
    else:
        provider_voices_cap = provider_voices_builder

    # Build metadata
    metadata = {
        "adapter_type": config.adapter_type,
        "real_cost": config.real_cost,
        "configured_via_yaml": True,
    }
    if base_capability and base_capability.metadata:
        metadata.update(base_capability.metadata)
    if adapter_config and adapter_config.metadata:
        metadata.update(adapter_config.metadata)

    # Check for unknown adapter type
    warning = None
    if not builder:
        warning = f"No capability builder for adapter_type '{config.adapter_type}'"

    if warning:
        metadata["warning"] = warning

    return ProviderCapability(
        provider=config.name,
        display_name=config.display_name,
        enabled=config.enabled,
        default_model=default_model,
        tts=tts_cap,
        batch=batch_cap,
        script=script_cap,
        voice_clone=voice_clone_cap,
        voice_design=voice_design_cap,
        provider_voices=provider_voices_cap,
        metadata=metadata,
    )


def _build_registry() -> dict[str, ProviderCapability]:
    """Build the full capability registry from YAML config."""
    registry = {}
    for config in list_enabled_provider_configs():
        cap = _build_capability_from_config(config)
        registry[config.name] = cap
    return registry


# Module-level registry cache
_capability_registry: dict[str, ProviderCapability] | None = None


def _get_registry() -> dict[str, ProviderCapability]:
    """Get the capability registry (cached)."""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = _build_registry()
    return _capability_registry


def list_capabilities() -> list[ProviderCapability]:
    """List all provider capabilities."""
    return list(_get_registry().values())


def get_capability(provider: str) -> ProviderCapability:
    """Get capability for a specific provider."""
    registry = _get_registry()
    cap = registry.get(provider)
    if not cap:
        raise UnsupportedProvider(f"Unsupported provider: {provider}", provider)
    return cap


def provider_exists(provider: str) -> bool:
    """Check if a provider exists in the capability registry."""
    return provider in _get_registry()


def clear_capability_registry_cache() -> None:
    """Clear the in-memory capability registry cache.

    Useful in tests when provider configs change.
    """
    global _capability_registry
    _capability_registry = None
