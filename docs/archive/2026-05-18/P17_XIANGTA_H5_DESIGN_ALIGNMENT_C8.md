# P17 XiangTa H5 Design Alignment C8 Archive

## Context

C7 Profile Mapping completed. C8 designs H5 product design alignment with C5/C6/C7 API contracts.

## Designed

| Area | Decision |
|---|---|
| Design files tech stack | React 17 + JSX + Vite (not plain JS) |
| Formal H5 voice entry | voicePreset only (GET /voice-presets, no coreProfileId) |
| Dev panel | coreProfileSelect retained (dev mode only, labeled) |
| H5 normalizeError | normalizeError() helper for flat/nested error compatibility |
| Error UX | 8 error types mapped to states: StateNoProvider/StateFailed/StateQuota/StateFailed |
| Copywriting UX | summary + source badge (dev) + fallbackUsed badge (dev) |
| Async TTS | POST /tts/tasks + GET /tts/tasks/{id} polling flow |
| H5 screen flow | Home → Suggestions → Voice → Letter (guided) / Input → Voice → Letter (free) |
| CA-06 debounce | Button disable + concurrent protection (deferred to C8-6) |
| Implementation order | C8-1 screen structure → C8-2 normalizeError → C8-3 error UX → C8-4 async TTS → C8-5 dev panel → C8-6 debounce |
| React vs plain JS | Short-term: plain JS IIFE with design tokens (CSS variables); Long-term: C12 React migration |

## Key decisions

- Design files use React JSX; current app.js is plain JS — future migration needs component rewrite
- normalizeError() helper must handle both flat (legacy) and nested (C6) error structures
- 8 errorKind categories with specific UX: StateNoProvider (core unavailable), StateFailed (provider/tts errors), StateQuota (rate/queue/quota), copywriting_blocked (文案区提示)
- voicePresetSelect source: GET /voice-presets (C7), not bootstrap
- profileId and voicePreset cannot both appear in same TTS request
- Dev mode: show profileIdSelect + /core/profiles; Formal mode: hide both
- Short-term plain JS + CSS variables reuse design tokens; React migration is C12 future work

## Not changed

- No business code changed
- No design_h5 files changed
- No apps/xiangta-h5/app.js changed
- No API implemented
- No React migration implemented
- C8 only designs; C8-* implementation deferred
