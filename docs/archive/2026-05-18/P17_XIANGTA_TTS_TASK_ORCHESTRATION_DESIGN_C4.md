# P17 XiangTa TTS Task Orchestration Design C4 Archive

## Context

C3 Storage Design completed. C4 designs async TTS task orchestration, concurrency boundaries, and the full L0-L6 layered concurrency model.

## Designed

| Area | Decision |
|---|---|
| L0 Frontend | Button disable, polling, state display, CA-06 deferred to C8 |
| L1 API Admission | Input validation, rate limit, idempotency, queue size check |
| L2 TtsTaskService | Task lifecycle, state machine, mark_running/completed/failed |
| L3 Queue/Worker | Phase 1 in-memory, Phase 2 SQLite-backed, Phase 3 Redis |
| L4 Core Gateway | coreRenderMaxConcurrent, timeout, error mapping |
| L5 Core/Provider | ResourceGuard boundary, not modified by XiangTa |
| L6 Storage | tts_tasks table alignment with C3 |
| async API | POST /tts/tasks + GET /tts/tasks/{id} |
| state machine | 6 states (queued/running/completed/failed/cancelled/expired) |
| idempotency | clientRequestId → request_id |
| concurrency limits | global/user/Core render layers |
| runtime config | tts section extension with 10 new fields |
| retry/cancel | MVP no auto-retry, manual retry creates new task; cancel queued only |
| frontend polling | pollAfterMs=1000, backoff after 30s, taskTtlSecs=1800 |

## Key decisions

- Concurrency is layered L0-L6, not only a queue.
- POST /api/xiangta/tts kept as B9 smoke/debug path; /tts/tasks is future product path.
- MVP queue starts in-memory (Phase 1); SQLite-backed (Phase 2) comes after C9.
- No automatic retry in MVP; retry creates new task.
- Cancel only works for queued tasks; running cannot be guaranteed cancelled.
- Core ResourceGuard and XiangTa task queue are separate layers, not substitutes.
- C4 only designs; C10 implements TTS Task MVP.

## Not changed

- No business code changed
- No Core code changed
- No H5 changed
- No queue implemented
- No worker implemented
- No storage implemented
- No API implemented
