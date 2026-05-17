# P16 Voice Binding Audit Dry-Run Report

Date: 2026-05-17
Commit: ee5f1f9 (test: reconcile mock_configured provider expectations)

Scope: read-only audit of existing `voice_bindings` rows against provider capability
config and local `provider_voices`. No database writes. No real API calls.

## Commands Executed

```
python scripts/audit_voice_bindings.py --dry-run
python scripts/audit_voice_bindings.py --provider xiaomi_mimo --dry-run
```

## Full Audit Summary

```
Commit:   ee5f1f9
Database: sqlite:///./voice_lab.db
Bindings scanned:     23
Bindings with issues:  4
Problem counts:
  MODEL_NOT_IN_PROVIDER_TTS_MODELS: 1
  VOICE_DEPRECATED:                 1
  VOICE_NOT_IN_PROVIDER:            2
```

## xiaomi_mimo Provider Filter

```
Provider filter: xiaomi_mimo
Bindings scanned:     3
Bindings with issues: 1
Problem counts:
  MODEL_NOT_IN_PROVIDER_TTS_MODELS: 1
```

## Issue Detail

### Issue 1 — CRITICAL: xiaomi_mimo + speech-2.8-hd (MiniMax model on MiMo provider)

```
binding_id:        binding_fba6107d7a304729
profile_id:        小米白桦
provider:          xiaomi_mimo
model:             speech-2.8-hd
provider_voice_id: 茉莉
status:            deprecated
problem_type:      MODEL_NOT_IN_PROVIDER_TTS_MODELS
```

`speech-2.8-hd` belongs to MiniMax. Xiaomi MiMo TTS capability only exposes `mimo-v2.5-tts`.
This binding was created before provider-aware UI was in place.

Suggested action: Delete and recreate through provider-aware UI (do not blindly rewrite model).

### Issue 2 — minimax: VOICE_NOT_IN_PROVIDER

```
binding_id:        binding_minimax_deep_night_programmer
profile_id:        deep_night_programmer
provider:          minimax
model:             speech-2.8-hd
provider_voice_id: English_expressive_narrator
status:            deprecated
problem_type:      VOICE_NOT_IN_PROVIDER
```

Voice `English_expressive_narrator` is not in the local `provider_voices` table under `minimax`.
Status is already `deprecated`. No active rendering expected.

Suggested action: Delete binding; not needed (voice no longer registered locally).

### Issue 3 — mock: VOICE_NOT_IN_PROVIDER

```
binding_id:        binding_mock_deep_night_programmer
profile_id:        deep_night_programmer
provider:          mock
model:             mock-tts
provider_voice_id: mock_voice_default
status:            deprecated
problem_type:      VOICE_NOT_IN_PROVIDER
```

`mock_voice_default` is not in local `provider_voices` under `mock`.
Status is already `deprecated`. This is a dev/test artifact.

Suggested action: Delete binding; harmless but stale.

### Issue 4 — minimax: VOICE_DEPRECATED

```
binding_id:        binding_f0525fb7f0654bf6
profile_id:        deep_night_programmer
provider:          minimax
model:             speech-2.8-hd
provider_voice_id: voice_clone_20260512170952_edxw6n
status:            deprecated
problem_type:      VOICE_DEPRECATED
```

Voice exists in `provider_voices` but is marked `deprecated`. Binding still points to it.

Suggested action: Do not render with this binding; choose an available voice and recreate.

## Checks

| Check | Result |
|-------|--------|
| xiaomi_mimo + speech-2.8-hd detected | **YES** — binding_fba6107d7a304729 |
| minimax + mimo-v2.5-tts detected | **NO** — no such binding exists |
| provider/model not in capability detected | **YES** — MODEL_NOT_IN_PROVIDER_TTS_MODELS |
| Database modified | **NO** — read-only |
| Real API called | **NO** — DB reads only |

## Script Capabilities

The audit script (`scripts/audit_voice_bindings.py`) detects:
- `UNKNOWN_PROVIDER` — provider not in config/providers.yaml
- `PROVIDER_DISABLED` — provider exists but `enabled: false`
- `MODEL_NOT_IN_PROVIDER_TTS_MODELS` — model not in provider's TTS models list
- `VOICE_NOT_IN_PROVIDER` — voice_id not in `provider_voices` for that provider
- `VOICE_DEPRECATED` / `VOICE_NOT_AVAILABLE` — voice exists but not in available status

Supports:
- `--dry-run` flag (always read-only; flag for explicitness)
- `--provider <name>` filter
- `--json` full JSON output
- Commit hash in output for traceability

## Next Step Recommendation

**D4-D1 apply phase IS required.** There are 4 dirty bindings:

| Priority | Binding | Action |
|----------|---------|--------|
| HIGH | xiaomi_mimo + speech-2.8-hd (小米白桦 profile) | Delete; recreate with mimo-v2.5-tts model via UI |
| MEDIUM | minimax + English_expressive_narrator (deprecated) | Delete; voice no longer registered |
| MEDIUM | minimax + voice_clone_20260512170952 (deprecated) | Delete or reassign to available voice |
| LOW | mock + mock_voice_default (deprecated, dev artifact) | Delete |

All four bindings are already `status: deprecated` in the database, meaning they are
not actively used for rendering. D4-D1 can safely delete all four after user confirmation.
No apply should write new model values — only deletion, then UI-driven recreation.
