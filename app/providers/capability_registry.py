"""Capability registry: provides ProviderCapability for each provider.

Built purely from config/providers.yaml + config/adapters/*.yaml.
No hardcoded capability builders needed.
"""

from app.core.errors import UnsupportedProvider
from app.domain.capabilities import (
    BatchCapability,
    NumericRange,
    ProviderCapability,
    ProviderVoiceCapability,
    TTSCapability,
    VoiceCloneCapability,
    VoiceDesignCapability,
    VoiceIdConstraint,
)
from app.config.provider_config_loader import list_enabled_provider_configs
from app.config.adapter_config_loader import get_adapter_config


def _range_from_config(range_cfg) -> NumericRange | None:
    if range_cfg is None:
        return None
    return NumericRange(min=range_cfg.min, max=range_cfg.max)


def _voice_id_from_config(vid_cfg) -> VoiceIdConstraint | None:
    if vid_cfg is None:
        return None
    return VoiceIdConstraint(
        min_length=vid_cfg.min_length,
        max_length=vid_cfg.max_length,
        pattern=vid_cfg.pattern or r"^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$",
        hint=vid_cfg.hint,
    )


def _build_capability_from_config(config) -> ProviderCapability:
    """Build ProviderCapability purely from ProviderConfig + AdapterConfig.

    Priority: ProviderConfig toggles (enable/disable) > AdapterConfig defaults.
    """
    adapter_config = get_adapter_config(config.adapter_type)

    default_model = config.default_model
    if not default_model and adapter_config:
        default_model = adapter_config.default_model

    # TTS
    tts_cap = None
    provider_tts_disabled = config.tts and not config.tts.enabled
    if provider_tts_disabled:
        tts_cap = TTSCapability(supported=False)
    elif adapter_config and adapter_config.tts and adapter_config.tts.supported:
        a = adapter_config.tts
        tts_cap = TTSCapability(
            supported=True,
            models=a.models,
            default_model=a.default_model or default_model,
            max_text_chars=a.max_text_chars,
            audio_formats=a.audio_formats,
            supports_subtitle=a.supports_subtitle,
            supports_streaming=a.supports_streaming,
            supports_emotion=a.supports_emotion,
            speed=_range_from_config(a.speed),
            vol=_range_from_config(a.vol),
            pitch=_range_from_config(a.pitch),
        )
    else:
        tts_cap = TTSCapability(supported=False)

    # Batch
    batch_cap = None
    provider_batch_disabled = config.batch and not config.batch.enabled
    if provider_batch_disabled:
        batch_cap = BatchCapability(supported=False)
    elif adapter_config and adapter_config.batch and adapter_config.batch.supported:
        b = adapter_config.batch
        batch_cap = BatchCapability(
            supported=True,
            max_text_chars=b.max_text_chars,
            max_segments=b.max_segments,
            segment_strategies=b.segment_strategies,
            max_segment_chars=_range_from_config(b.max_segment_chars),
            silence_between_ms=_range_from_config(b.silence_between_ms),
            supports_merge_audio=b.supports_merge_audio,
            supports_merge_subtitle=b.supports_merge_subtitle,
        )
    else:
        batch_cap = BatchCapability(supported=False)

    # Script
    script_cap = None
    provider_script_disabled = config.script and not config.script.enabled
    if provider_script_disabled:
        script_cap = BatchCapability(supported=False)
    elif adapter_config and adapter_config.script and adapter_config.script.supported:
        s = adapter_config.script
        script_cap = BatchCapability(
            supported=True,
            max_text_chars=s.max_text_chars,
            max_segments=s.max_segments,
            segment_strategies=s.segment_strategies,
            max_segment_chars=_range_from_config(s.max_segment_chars),
            silence_between_ms=_range_from_config(s.silence_between_ms),
            supports_merge_audio=s.supports_merge_audio,
            supports_merge_subtitle=s.supports_merge_subtitle,
        )
    else:
        script_cap = BatchCapability(supported=False)

    # VoiceClone
    voice_clone_cap = None
    provider_vc_disabled = config.voice_clone and not config.voice_clone.enabled
    if provider_vc_disabled:
        voice_clone_cap = VoiceCloneCapability(supported=False)
    elif adapter_config and adapter_config.voice_clone and adapter_config.voice_clone.supported:
        vc = adapter_config.voice_clone
        voice_clone_cap = VoiceCloneCapability(
            supported=True,
            preview_text_max=vc.preview_text_max,
            voice_id=_voice_id_from_config(vc.voice_id),
            supports_noise_reduction=vc.supports_noise_reduction,
            supports_volume_normalization=vc.supports_volume_normalization,
            max_file_size_mb=vc.max_file_size_mb,
        )
    else:
        voice_clone_cap = VoiceCloneCapability(supported=False)

    # VoiceDesign
    voice_design_cap = None
    provider_vd_disabled = config.voice_design and not config.voice_design.enabled
    if provider_vd_disabled:
        voice_design_cap = VoiceDesignCapability(supported=False)
    elif adapter_config and adapter_config.voice_design and adapter_config.voice_design.supported:
        vd = adapter_config.voice_design
        voice_design_cap = VoiceDesignCapability(
            supported=True,
            prompt_max=vd.prompt_max,
            preview_text_max=vd.preview_text_max,
            voice_id=_voice_id_from_config(vd.voice_id),
        )
    else:
        voice_design_cap = VoiceDesignCapability(supported=False)

    # ProviderVoices
    provider_voices_cap = None
    provider_pv_disabled = config.provider_voices and not config.provider_voices.enabled
    if provider_pv_disabled:
        provider_voices_cap = ProviderVoiceCapability(supported=False)
    elif adapter_config and adapter_config.provider_voices and adapter_config.provider_voices.supported:
        pv = adapter_config.provider_voices
        provider_voices_cap = ProviderVoiceCapability(
            supported=True,
            supports_list_voices=pv.supports_list_voices,
            supports_delete_voice=pv.supports_delete_voice,
            supports_import_remote_voice=pv.supports_import_remote_voice,
            preview_text_max=pv.preview_text_max,
        )
    else:
        provider_voices_cap = ProviderVoiceCapability(supported=False)

    # Metadata
    metadata = {
        "adapter_type": config.adapter_type,
        "real_cost": config.real_cost,
        "configured_via_yaml": True,
    }
    if adapter_config and adapter_config.metadata:
        metadata.update(adapter_config.metadata)

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
