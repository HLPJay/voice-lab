# P17 XiangTa Runtime Config C2 Archive

## Context

C1 (Backend Capability Plan) completed. Next step is C2: implement layered runtime config.

## What was implemented

### Files created

- **`src/xiangta/config/runtime_config.py`**: Layered config loader (`default → runtime.json → env override`)
- **`src/xiangta/configs/runtime.json`**: Default config file (all capability sections, `core.enabled=false`)
- **`tests/xiangta/test_runtime_config.py`**: Full test coverage (27 tests)

### Files modified

- **`apps/xiangta_runtime/README.md`**: Added two config methods (env var vs runtime.json)
- **`docs/agent/NEXT_TASKS.md`**: Marked C2 completed, next = C3

### Config priority

```
default (core.enabled=false)
  ↓ runtime.json (file override)
    ↓ XIANGTA_* env vars (explicit override)
```

### Security boundary

- No real Provider API key names in source (`runtime_config.py` contains no `MINIMAX_API_KEY`, `MIMO_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`)
- No API key in `runtime.json`
- API keys come only from external injection (env vars, injected clients)

### Config sections

| Section | Key fields |
|---|---|
| `core` | `enabled`, `baseUrl`, `timeoutSecs` |
| `copywriting` | `mode`, `provider`, `timeoutSecs`, `fallbackToTemplate` |
| `tts` | `mode`, `maxConcurrent`, `queueEnabled`, `timeoutSecs` |
| `storage` | `type`, `databaseUrl` |
| `features` | `devCoreProfileSelect`, `lettersEnabled`, `llmCopywritingEnabled`, `ttsTaskEnabled` |

### Env var mapping

| Env var | Config path | Type |
|---|---|---|
| `XIANGTA_CORE_BASE_URL` | `core.baseUrl` | str |
| `XIANGTA_CORE_TIMEOUT_SECS` | `core.timeoutSecs` | float |
| `XIANGTA_CORE_ENABLED` | `core.enabled` | bool |
| `XIANGTA_COPYWRITING_MODE` | `copywriting.mode` | str |
| `XIANGTA_COPYWRITING_PROVIDER` | `copywriting.provider` | str |
| `XIANGTA_COPYWRITING_TIMEOUT_SECS` | `copywriting.timeoutSecs` | float |
| `XIANGTA_COPYWRITING_FALLBACK_TO_TEMPLATE` | `copywriting.fallbackToTemplate` | bool |
| `XIANGTA_TTS_MODE` | `tts.mode` | str |
| `XIANGTA_TTS_MAX_CONCURRENT` | `tts.maxConcurrent` | int |
| `XIANGTA_TTS_QUEUE_ENABLED` | `tts.queueEnabled` | bool |
| `XIANGTA_TTS_TIMEOUT_SECS` | `tts.timeoutSecs` | float |
| `XIANGTA_STORAGE_TYPE` | `storage.type` | str |
| `XIANGTA_STORAGE_DATABASE_URL` | `storage.databaseUrl` | str |
| `XIANGTA_FEATURE_DEV_CORE_PROFILE_SELECT` | `features.devCoreProfileSelect` | bool |
| `XIANGTA_FEATURE_LETTERS_ENABLED` | `features.lettersEnabled` | bool |
| `XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED` | `features.llmCopywritingEnabled` | bool |
| `XIANGTA_FEATURE_TTS_TASK_ENABLED` | `features.ttsTaskEnabled` | bool |

### Backward compatibility

`XiangTaRuntimeConfig` keeps `core_base_url` and `core_timeout_secs` fields for `product_service.py` compatibility.

### Tests

```
27 passed (test_runtime_config.py)
610 passed (all xiangta tests)
```

## Not changed

- No Core code changed
- No `app/**` changed
- No `src/voice_lab/**` changed
- No `src/xiangta/api/**` changed
- No `src/xiangta/services/**` changed
- No H5 changed
- No business logic changed
