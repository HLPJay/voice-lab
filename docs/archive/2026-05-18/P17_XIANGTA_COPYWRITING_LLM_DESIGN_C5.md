# P17 XiangTa Copywriting LLM Design C5 Archive

## Context

C4 TTS Task Orchestration completed. C5 designs LLM copywriting capability with gateway/fallback/structure/security.

## Designed

| Area | Decision |
|---|---|
| Architecture | CopywritingService → CopywritingGateway → TemplateCopywriter / LlmCopywriter / OutputValidator |
| Input Schema | recipient/scene/rawText (required) + tone/style/relationshipContext/targetLength (optional) |
| Output Schema | summary/intent/suggestions[3]/source/fallbackUsed — backward compatible |
| Prompt Design | JSON payload separation, system/user prompt split, structured output contract |
| Prompt Injection Defense | Structured JSON payload, output validation, charCount recalculated by backend |
| Fallback Strategy | LLM timeout/error/invalid output → template, ok=true always for frontend |
| Runtime Config | 10 new fields in copywriting section (mode/provider/timeoutSecs/fallbackToTemplate/maxChars/temperature/minMaxSuggestions) |
| Provider Abstraction | LlmProviderClient Protocol, future support minimax/openai/deepseek |
| Error Types | validation_error/timeout/provider_error/invalid_output/blocked |
| Storage alignment | copywriting_jobs table (C3) stores validated suggestions, not raw LLM logs |
| H5 strategy | Ignore unknown fields, wait for API stability before H5 implementation |
| Implementation phases | C5→C6→C7→C8→C9→C10→C11 (storage before LLM) |

## Key decisions

- Template remains as reliable fallback, LLM is enhancement not replacement
- User input as JSON payload fields, not free-text prompt concatenation
- charCount recalculated by backend, never trusted from LLM output
- Most LLM errors absorbed by fallback, frontend always gets ok=true
- copywriting_jobs stores validated product structure, not raw LLM logs
- API key stays out of runtime.json (env variable injection only)
- Copywriting and TTS are independent chains, no coupling

## Not changed

- No business code changed
- No Core code changed
- No H5 changed
- No LLM provider implemented
- No storage implemented
- C5 only designs; C11 implements LLM Copywriting MVP
