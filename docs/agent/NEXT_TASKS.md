# Next Tasks

## 当前阶段

**P9-FE2 前端模块化边界审查**

## 已完成

- P9-FE1：voice_clone.js、voice_import.js、voice_design.js 抽离 ✅
- P9-FE2-A0：index.html 剩余逻辑边界审查 ✅

## P9-FE2-A0 审查结论

### 剩余模块候选及优先级

| 优先级 | 候选模块 | 风险 | 结论 |
|---|---|---|---|
| 1 | `voice_list.js` | 中 | 可小步抽离，`handleListVoices` 可独立迁移 |
| 2 | `audition_workstation.js` | 高 | 强耦合 `handleGenerate`，不建议单独抽 |
| 3 | `profile_binding.js` | 极高 | 依赖太广，强耦合 voice list 和 batch |
| 4 | `error_helpers.js` | 中 | 可抽但收益小，收益覆盖不了风险 |
| 5 | `batch_shared.js` | 极高 | shared state 冲突，需统一设计 |

**建议暂停前端模块化，转产品功能打磨。**

详见：`docs/P9_FRONTEND_MODULARIZATION.md` P9-FE2-A0 节

## Next（按优先级）

1. **暂停前端模块化** — 理由见 P9-FE2-A0 审查结论
2. 产品功能打磨优先级更高

## Paused / Do not touch yet

| 区域 | 原因 |
|---|---|
| `batch_shared.js` | shared batch state 风险极高，需统一状态管理设计 |
| `profile_binding.js` | 被 voice list / audition / batch / clone / design 多处共用，强行拆出循环依赖 |
| `audition_workstation.js` | 强耦合 `handleGenerate` 单条生成链路，单独抽离无意义 |
| `error_helpers.js` | 被十余处引用，迁移成本大，收益小 |
| `provider_capabilities.js` | 已稳定，无充分理由动 |
| Vite / React migration | 当前阶段不引入 |
| dynamic loading | 当前阶段不需要 |
| tab/subtab switching | 涉及所有 Tab DOM visibility 状态，不应抽 |

## 详细历史来源

- 完整变更记录：`docs/PROJECT_HEALTH_CHECK.md`
- 前端模块化演进：`docs/P9_FRONTEND_MODULARIZATION.md`
