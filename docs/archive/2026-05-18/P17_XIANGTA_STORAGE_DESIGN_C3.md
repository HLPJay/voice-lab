# P17 XiangTa Storage Design C3 Archive

## Context

C2B cleanup completed. C3 designs XiangTa storage model for future SQLite MVP implementation.

## Designed

| Area | Decision |
|---|---|
| letters | `letters` table with soft delete, user_id nullable, audio_url storage |
| tts_tasks | `tts_tasks` table with full status lifecycle (queued/running/completed/failed/cancelled/expired) |
| copywriting_jobs | `copywriting_jobs` table for LLM audit trail |
| voice_preset_mappings | `voice_preset_mappings` table to replace voice_mappings.json |
| schema_migrations | `schema_migrations` table for migration governance |
| app_settings | Deferred — continue using runtime.json + env |
| Database choice | SQLite MVP, PostgreSQL upgrade path documented |
| ORM | Prefer project-existing dependency (SQLModel > SQLAlchemy Core > sqlite3 stdlib) |
| Repository structure | `src/xiangta/storage/` + `*_repository.py` pattern |
| Core asset boundary | XiangTa stores audio_url only; does not replicate Core files |

## Key decisions

- SQLite MVP: zero deployment dependency, file-based, suitable for local H5 runtime
- PostgreSQL upgrade trigger: multi-user, concurrent writes, remote deployment
- user_id nullable: all tables support NULL for local single-user; future filter by user_id
- soft delete via `deleted_at`: no physical delete, preserves audit trail
- Core audio URL stored, not binary: XiangTa does not copy Core asset files
- C3 only designs; C9 implements Storage Foundation

## Not changed

- No business code changed
- No Core code changed
- No H5 changed
- No database implemented
- No migration implemented
- No repository implemented
- C3 只做设计，C9 才进入实现
