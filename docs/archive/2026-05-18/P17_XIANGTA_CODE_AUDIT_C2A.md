# P17 XiangTa Code Audit C2A Archive

## Context

B9 chain, architecture sync, backend capability plan (C1), and runtime config (C2) completed. C2A performs a read-only code audit of the product layer to identify risks before C3 Storage Design.

## Audit areas

| Area | Result |
|---|---|
| Core Boundary | ✅ PASS — no app imports, no API key read, no forbidden field exposure |
| Architecture & Dependency Direction | ⚠️ 2 issues — `ProductService` accesses `TtsOrchestrator._gw` private field; routes.py creates new `ProductService` per request |
| Runtime Config | ✅ PASS — no API keys, layered loading correct, silent exception on corrupt runtime.json (P3) |
| Error Contract | ⚠️ 2 issues — `TtsOrchestrator` uses string-based exception matching; `CoreHttpClient` loses HTTP error context |
| Concurrency & Task Readiness | ⚠️ H5 has no duplicate-click prevention; no task queue yet (design deferred to C4) |
| Storage Readiness | ✅ Appropriate for MVP — letters in-memory, user_id nullable in data models |
| Security Baseline | ⚠️ 1 P1 — `/admin/*` has no authentication; no API key leakage detected |
| H5 Readiness | ⚠️ Functional but no debounce; app.js state desync possible; no favicon |
| Test Gap Analysis | ⚠️ Admin auth, H5 debounce, CoreHttpClient 4xx detail not covered |

## Key findings

| ID | Severity | Summary |
|---|---|---|
| CA-01 | P1 | Admin API has no authentication — any client can read/write voice mappings and tone presets |
| CA-02 | P2 | `ProductService.list_core_profiles()` accesses `self._tts._gw` private field — architectural coupling |
| CA-03 | P2 | `TtsOrchestrator` uses `exc.__class__.__name__` string matching instead of `isinstance()` |
| CA-04 | P2 | `CoreHttpClient` loses all HTTP error context (status code, response body) |
| CA-05 | P2 | `routes.py` docstring marks `/suggestions` and `/letters` as unimplemented — they are wired |
| CA-06 | P2 | H5 has no duplicate-click guard — concurrent API requests possible |
| CA-07 | P2 | Every route creates a new `ProductService` — re-reads config and rebuilds all services per request |
| CA-08 | P2 | `voice_mappings.json` all placeholders; H5 B9 workaround accepts `profileId` directly — tracked as GAP-B2-001 |
| CA-09 | P3 | `XiangTaRuntimeConfig` dataclass at end of `runtime_config.py` — readability concern |
| CA-10 | P3 | `_load_runtime_json()` silent exception — corrupt runtime.json yields no warning |
| CA-11 | P3 | `app.js` state desync: `state.coreProfiles` stored but not used by `renderCoreProfileSelect()` |
| CA-12 | P3 | `AdminConfigData` uses `list[dict]` for recipients/scenes — loose typing vs bootstrap models |
| CA-13 | P3 | `LetterItem` exposes `favorited`, `openCount`, `openedAt` without user-scoped access control |
| CA-14 | P3 | No favicon — browser 404s on every page load |

## Decisions

- No business code changed.
- Findings are registered for future small cleanup (C2B) or design phases (C3–C8).
- No Core changes required.
- Recommended next: C2B Small Cleanup (trivially fix CA-03, CA-05, CA-09, CA-10, CA-06) alongside C3 Storage Design.
- Admin auth (CA-01) is a pre-production requirement but not blocking for MVP iterations.

## Not changed

- No Core code changed
- No XiangTa business code changed
- No H5 changed
- No tests changed
- No API changed
- No storage/queue/LLM/user system implemented
