# P18 XiangTa Voice Presets API C1 Archive

## Context

P18-C1 implemented GET /api/xiangta/voice-presets public API for formal H5 product use.

## Implemented

- GET /api/xiangta/voice-presets returns public voice preset fields only
- VoicePresetsData + VoicePresetsResponse schemas added
- ProductService.list_public_voice_presets() facade method added
- Public response fields: id, label, desc, genderStyle, suitableRecipients, recommendedScenes, defaultTone, enabled
- Forbidden fields NOT exposed: coreProfileId, providerPolicy, renderOverrides, apiKey, providerVoiceId, bindingId
- Disabled presets excluded from public response
- 16 new tests covering all contract requirements

## Not implemented

- H5 calling /voice-presets
- voicePreset → coreProfileId hardening (C2)
- Admin gate
- Error contract nested schema
- Storage / SQLite
- TTS task
- LLM copywriting
- Core modification
- Real Provider integration

## Tests

627 passed (611 baseline + 16 new)

## Next

P18-XIANGTA-VOICE-PRESET-RESOLUTION-C2: strengthen voicePreset → coreProfileId resolution
