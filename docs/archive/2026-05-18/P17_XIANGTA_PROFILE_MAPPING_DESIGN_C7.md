# P17 XiangTa Profile Mapping Design C7 Archive

## Context

C6 Error Contract completed. C7 designs voicePreset → coreProfileId product mapping, resolving B9 smoke path issues.

## Designed

| Area | Decision |
|---|---|
| B9 smoke path problem | H5 directly selects Core profileId; voicePreset mapping bypassed |
| Product voicePreset goal | voicePreset as sole H5 voice entry; coreProfileId is Admin/Dev internal |
| Core Profile concept | Read-only via Core HTTP API; dev/admin visible; H5 not visible |
| Voice Preset concept | Product-layer semantic voice label; maps to coreProfileId |
| Voice Mapping concept | voicePresetId → coreProfileId; stored in JSON Phase 1, DB Phase 2 |
| Tone Preset boundary | Orthogonal to voicePreset; voicePreset = "who", tonePreset = "how" |
| Data model | 13-field JSON structure aligned with C3 voice_preset_mappings table |
| JSON-backed Phase 1 | Continue using voice_mappings.json; no DB yet |
| DB-backed Phase 2 | voice_preset_mappings table after Storage Foundation |
| H5 API contract | GET /api/xiangta/voice-presets returns id/label/desc/scenes/recipients/defaultTone only (no coreProfileId) |
| Admin API contract | GET /admin/voice-mappings returns all fields including coreProfileId; requires C6 admin gate |
| TTS resolution timing | Strategy A: resolve at task creation time, store voice_preset + profile_id |
| Core profile validation | Admin save: optional validation; TTS execution: mandatory fallback |
| C3 storage alignment | voice_preset_mappings table + letters.profile_id + tts_tasks.profile_id |
| C4 task alignment | Task creation resolves voicePreset → profile_id; task records both |
| C5 copywriting alignment | Independent; voicePreset for audio, copywriting for text |
| C6 error alignment | voice_preset_not_found / voice_preset_disabled / profile_not_found / config_validation_error |
| Admin/dev security boundary | features.adminEnabled gate; XIANGTA_ADMIN_TOKEN; dev panel with profileId |
| Validation rules | id/label/desc/coreProfileId/recommendedScenes/suitableRecipients/defaultTone/providerPolicy/renderOverrides |
| JSON→DB migration | Skip placeholder coreProfileId; mark disabled or skip; no invalid config in DB |
| Implementation phases | C7-1 voicePreset resolution → C7-2 voice-presets API → C7-3 deprecate profileId → C7-4 admin validation → C7-5 JSON→DB migration |

## Key decisions

- Ordinary H5 uses voicePreset only; coreProfileId is Admin/Dev internal
- B9 profileId smoke path is dev/smoke only; not for regular H5
- TTS task creation resolves voicePreset → profile_id at task creation time (Strategy A) for reproducibility
- voicePreset and profileId cannot both appear in same TTS request
- JSON Phase 1 (current) → DB Phase 2 (after Storage Foundation)
- Placeholder coreProfileId ("<...>") must be resolved before DB migration
- Admin mapping save with optional Core profile validation; TTS execution always has fallback
- renderOverrides stays whitelist-only; no api_key/provider_secret

## Not changed

- No business code changed
- No Core code changed
- No H5 changed
- No JSON config changed
- No API implemented
- No DB migration implemented
- C7 only designs; C7-* implementation deferred
