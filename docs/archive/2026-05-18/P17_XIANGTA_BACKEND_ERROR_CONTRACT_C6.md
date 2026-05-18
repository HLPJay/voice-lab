# P17 XiangTa Backend Error Contract C6 Archive

## Context

C5 Copywriting LLM Design completed. C6 designs unified backend error contract covering all API error response structures, errorKind enum, HTTP status mapping, retryable semantics, user/internal detail boundary, requestId/taskId, and cross-layer error mapping.

## Designed

| Area | Decision |
|---|---|
| Unified error schema | Nested `error` object with `errorKind/message/retryable/requestId/taskId/details`; flat legacy structure kept for backward compatibility |
| errorKind enum | 40+ stable errorKind values across 7 groups: General, Core/Gateway, TTS, Copywriting/LLM, Storage, Admin/Config, Task |
| HTTP status mapping | Full mapping from errorKind to HTTP status (400/401/403/404/408/409/422/429/500/502/503) |
| retryable semantics | 18 retryable=true (core_unavailable, timeout, provider_error, etc.); 21 retryable=false (validation, auth, not_found, etc.) |
| user vs internal detail | message is user-visible (1-100 chars, no tech terms); details=null in production, safe dev context in dev mode |
| requestId/taskId | req_<12chars> per HTTP request, T_<10chars> per TTS task; returned in error responses |
| Core/Gateway mapping | CoreHttpClient → CoreHttpError(kind/status_code/safe_detail); VoiceLabGateway → gateway exceptions; TtsOrchestrator → XiangTaError |
| TTS task mapping | Create: fail-fast (validation/queue/profile_not_found); Execute: task status=failed + errorKind; Query: ok=true with status=failed |
| Copywriting/LLM mapping | LLM technical failures → template fallback (ok=true); validation_error/copywriting_blocked → ok=false |
| Storage mapping | SQLite unavailable → storage_unavailable; write fail → storage_write_failed; aligned with C3 |
| Admin gate | features.adminEnabled=false → admin_disabled (403); XIANGTA_ADMIN_TOKEN header → auth_required/forbidden |
| H5 display | 13 errorKind display categories with user-facing messages; normalizeError() helper for schema compatibility |
| observability/logging | request_id/task_id/route/error_kind/latency_ms/core_status_code; no raw_text/API key logged |
| migration strategy | Phase 1: add requestId; Phase 2: new APIs use nested structure; Phase 3: legacy migration; Phase 4: H5 normalizeError |

## Key decisions

- New APIs use nested error object; legacy flat structure kept for backward compatibility
- errorKind is stable contract (H5 and logs depend on it); message can change without breaking frontend
- Task failed status returns ok=true with data.status=failed (query succeeded, task state is data)
- LLM technical failures absorbed by template fallback; ok=true always for frontend
- validation_error and copywriting_blocked do NOT fallback by default
- Admin gate first uses features.adminEnabled env flag; token-based auth designed but deferred
- CoreHttpClient should throw structured CoreHttpError instead of returning dict error
- No stack trace / API key / provider raw response in any frontend-facing error
- requestId via FastAPI middleware; does not change existing sync API signatures

## Not changed

- No business code changed
- No Core code changed
- No H5 changed
- No error middleware implemented
- No Admin auth implemented
- No CoreHttpClient changes
- C6 only designs; C6-* implementation deferred
