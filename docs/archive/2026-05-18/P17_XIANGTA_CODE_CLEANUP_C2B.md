# P17 XiangTa Code Cleanup C2B Archive

## Context

C2A Code Audit identified small cleanup items. C2B fixes low-risk backend cleanup items identified in the audit.

## Fixed

| Finding | File changed | Fix |
|---|---|---|
| CA-03 | `src/xiangta/services/tts_orchestrator.py` | Replaced `exc.__class__.__name__` string comparison with `isinstance()` using real `CoreRenderUnavailableError` / `CoreRenderResponseError` from `voice_lab_gateway` |
| CA-05 | `src/xiangta/api/routes.py` | Updated module docstring to reflect current implementation state: `/suggestions` ✅ template版, `/letters` ✅ 进程内内存, `/admin/*` noted as requiring auth before production |
| CA-09 | `src/xiangta/config/runtime_config.py` | Moved `XiangTaRuntimeConfig` dataclass before helper functions; added `logging` import at top |
| CA-10 | `src/xiangta/config/runtime_config.py` | Added `logger.warning()` when `runtime.json` fails to load; still returns `{}` and falls back to defaults safely |

## Tests updated

- `tests/xiangta/test_tts_orchestrator.py`: Updated `TestGatewayErrors` to use real `CoreRenderUnavailableError` / `CoreRenderResponseError` from `voice_lab_gateway` (not locally-defined stub classes)
- `tests/xiangta/test_runtime_config.py`: Added `test_corrupt_runtime_json_returns_defaults_and_logs_warning` to verify CA-10 fix

## Deferred

| Finding | Reason |
|---|---|
| CA-06 H5 duplicate-click guard | H5 change deferred to C8 H5 Design Alignment |
| CA-01 Admin auth | Requires security/design decision; deferred to C6 or dedicated security task |
| CA-04 CoreHttpClient error context loss | Belongs to C6 Error Contract redesign |
| CA-02 ProductService private gateway access | Requires constructor/dependency refactor; deferred |

## Not changed

- No Core code changed
- No H5 changed
- No ProductService changed
- No VoiceLabGateway changed
- No CoreHttpClient changed
- No storage/queue/LLM/user system implemented
- No runtime.json changed
- No new API added
