# Next Tasks

## 当前阶段

**P9-FE1 前端模块化**

## 已完成

- P9-FE1-G0~G4：voice_clone.js 抽离
- P9-FE1-G4-FIX：clone success E2E
- P9-FE1-H0：voice_import.js 边界审查
- P9-FE1-H1：import clone mock success E2E
- P9-FE1-H2：voice_import.js 抽离
- P9-FE1-I0：voice_design.js 边界审查（可迁移）

## Next（按优先级）

1. **P9-FE1-I1** — voice_design.js 抽离
   - 仅迁移 `handleDesignVoice`
   - 参照 voice_import.js 模式
   - I0 结论：可独立迁移，无循环依赖

2. **P9-FE1-CHECK** — voice advanced stage 收口
   - 确认 voice_clone + voice_import + voice_design 三模块边界清晰
   - 确认无遗漏依赖

## Paused / Do not touch yet

| 区域 | 原因 |
|---|---|
| `batch_shared.js` | shared batch state 风险高，需深入设计 |
| `profile_binding.js` | 被太多模块共用，强行拆出循环依赖 |
| `provider_capabilities.js` | 已稳定，无充分理由动 |
| `error_helpers.js` | 被十余处引用，迁移成本大 |
| Vite / React migration | 当前阶段不引入 |
| dynamic loading | 当前阶段不需要 |

## 详细历史来源

- 完整变更记录：`docs/PROJECT_HEALTH_CHECK.md`
- 前端模块化演进：`docs/P9_FRONTEND_MODULARIZATION.md`
