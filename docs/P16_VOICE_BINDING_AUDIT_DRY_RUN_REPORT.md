# P16 Voice Binding Audit Dry-Run Report

## Phase D4-D0: Initial Dry-Run

Date: 2026-05-17
Commit: ee5f1f9

Found 4 deprecated invalid bindings:
- binding_fba6107d7a304729 (xiaomi_mimo + speech-2.8-hd)
- binding_minimax_deep_night_programmer (VOICE_NOT_IN_PROVIDER)
- binding_mock_deep_night_programmer (VOICE_NOT_IN_PROVIDER)
- binding_f0525fb7f0654bf6 (VOICE_DEPRECATED)

---

## Phase D4-D1: Apply Delete

Date: 2026-05-17
Commit: 130a4f3 (pre-delete)

### Pre-Delete Dry-Run

```
Commit:   130a4f3
Database: sqlite:///./voice_lab.db
Bindings scanned:     23
Bindings with issues:  4
Problem counts:
  MODEL_NOT_IN_PROVIDER_TTS_MODELS: 1
  VOICE_DEPRECATED:                 1
  VOICE_NOT_IN_PROVIDER:            2
```

xiaomi_mimo filter:
```
Bindings scanned:     3
Bindings with issues: 1  (xiaomi_mimo + speech-2.8-hd)
```

### Delete Command

```
python scripts/audit_voice_bindings.py --delete-deprecated-issues --confirm-delete
```

### Delete Result

```
About to delete 4 deprecated issue binding(s):
  binding_minimax_deep_night_programmer  provider=minimax  status=deprecated
  binding_mock_deep_night_programmer     provider=mock     status=deprecated
  binding_f0525fb7f0654bf6              provider=minimax  status=deprecated
  binding_fba6107d7a304729              provider=xiaomi_mimo  status=deprecated
Deleted: 4
```

### Post-Delete Dry-Run

```
Commit:   130a4f3
Database: sqlite:///./voice_lab.db
Bindings scanned:     19
Bindings with issues:  0
Problem counts: {}
```

xiaomi_mimo filter:
```
Bindings scanned:     2
Bindings with issues: 0
Problem counts: {}
```

### Safety Verification

| Check | Result |
|-------|--------|
| available bindings deleted | **NO** — only status=deprecated |
| model auto-rewritten | **NO** — delete only |
| provider_voices modified | **NO** |
| real API called | **NO** |
| DB writes beyond delete | **NO** |
| xiaomi_mimo + speech-2.8-hd remains | **NO** — deleted |

### Remaining Bindings

19 bindings remain. All pass audit (0 issues).

No further D4 apply phase required.
