# P17 XiangTa Backend Capability Plan C1 Archive

## Context

B9 chain completed, architecture synced. Next step is backend capability planning — C1.

## Planned capability areas

| Area | Decision |
|---|---|
| Runtime Config | default → runtime.json → env override. Secret boundary: no API key in config. |
| Storage / Data Model | Start from SQLite design with letters/tts_tasks/copywriting_jobs/voice_preset_mappings tables |
| TTS Task Queue | Design async API (POST /tasks, GET /tasks/{id}). Phase 1: in-memory, Phase 2: SQLite, Phase 3: Redis if multi-user |
| LLM Copywriting | Gateway + TemplateCopywriter + LlmCopywriter + OutputValidator + template fallback |
| Profile Mapping | voicePreset → coreProfileId via voice_preset_mappings table |
| Error Contract | Unified {ok, errorKind, message, retryable, requestId, taskId} schema |
| Security Baseline | Input validation, XSS escape, SQL injection prevention, prompt injection prevention, rate limiting, secret leakage prevention |
| Observability | Structured logging (request_id, task_id, user_id, provider, latency_ms, status, error_kind) |
| Future User/Auth/RBAC | user_id nullable in all tables, anonymous/local/user/admin/developer roles |
| API Governance | Frontend depends on /api/xiangta/* only, not /api/voice/* |

## Key decisions

1. **Runtime config**: `default → runtime.json → env` priority. `baseUrl`, `timeout`, `mode`, `feature flags` allowed; real API keys prohibited.
2. **Storage**: SQLite MVP → PostgreSQL for multi-user. All tables include `user_id nullable` and soft delete (`deleted_at`).
3. **TTS task queue**: `POST /api/xiangta/tts/tasks` + `GET /api/xiangta/tts/tasks/{taskId}`. Phase 1 in-memory, Phase 2 SQLite task table, Phase 3 Redis/worker.
4. **LLM copywriting**: `CopywritingService → CopywritingGateway → TemplateCopywriter | LlmCopywriter → OutputValidator → fallback`. Always fallback to template on LLM failure.
5. **User/Auth/RBAC**: Deferred but `user_id` designed as nullable in all data models. No registration/login in current scope.
6. **Concurrency**: Single user max 1 concurrent TTS task. Global max 1-2 concurrent Core render calls. Queue length max 10. Task TTL 30 min.
7. **Security**: No API key in logs or error responses. XSS prevention via escape. SQL injection prevention via ORM. LLM prompt injection prevention by separating system/user input.

## Implementation roadmap priority

1. C2 Runtime Config Design
2. C3 Storage Design
3. C4 TTS Task Orchestration Design
4. C5 LLM Copywriting Design
5. C6 Error Contract Design
6. C7 Profile Mapping Design
7. C8 H5 Design Alignment

**Constraint**: Design backend capabilities first, then H5 implementation. No direct LLM or user system in current scope.

## Not changed

- No business logic changed
- No Core code changed
- No H5 changed
- No tests added
- No persistence implemented
- No LLM implemented
- No user system implemented
