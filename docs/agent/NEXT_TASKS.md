# Next Tasks

## 当前阶段

**P12 真实使用验证**

## 已完成

- P9-FE1：voice_clone.js、voice_import.js、voice_design.js 抽离 ✅
- P9-FE2-A0：index.html 剩余逻辑边界审查 ✅
- P10-PRODUCT-A0：产品打磨优先级审查 ✅
- P10-PRODUCT-B0：Workspace 音色快捷选择区边界审查 ✅
- P10-PRODUCT-B1：Workspace 音色快捷选择区实现 ✅
- P10-PRODUCT-B2-A0：Voices tab 快速创作联动边界审查 ✅
- P10-PRODUCT-B2：Voices tab 快速创作联动实现 ✅
- P10-PRODUCT-B3-A0：Batch tab 音色快速选择边界审查 ✅
- P10-PRODUCT-B3-longtext：Batch longtext tab 绑定音色提示实现 ✅
- P10-PRODUCT-B3-script：Batch script tab 每行动态绑定音色提示实现 ✅
- P10-PRODUCT-B4：简化 onboarding 文案 ✅
- P10-PRODUCT-B5：Advanced tab 重命名为音色工具 ✅
- P10-PRODUCT-B6：历史最近任务快捷入口实现 ✅
- P11-FE-REDUCE-A0：index.html 瘦身审查 ✅
- P11-FE-REDUCE-A1：product_hints.js 抽离 ✅
- P11-FE-REDUCE-A1-CHECK：product_hints.js 验证 ✅
- P11-FE-REDUCE-A2-A0：recent_job 模块审查（结论：不迁移） ✅
- P11-FE-REDUCE-CHECK：index.html 瘦身收口 ✅
- P12-USAGE-FIX1：workspace binding hint 与 #bindingStatus 同步修复 ✅
- P12-USAGE-UX1：compact advanced tool hints ✅
- P12-USAGE-FIX2：check initial workspace binding status ✅
- P12-USAGE-FIX3：sync batch binding hints ✅
- P12-USAGE-FIX3B：add status to bind map entries ✅
- P12-USAGE-UX2：redesign recent job entry ✅
- P12-USAGE-FIX4-A0：audit audio download failures ✅
- P12-USAGE-FIX4-B0：audit batch merged audio asset_id ✅
- P12-USAGE-FIX4：normalize batch download href ✅
- P12-USAGE-UX3：clarify async mode positioning ✅
- P12-USAGE-UX4-A0：audit advanced quick bind panels ✅

## Next

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P12-USAGE-UX4-B1 | normalize advanced quick bind panel layout | UX4-A0 审查完成 |
| P13-CREATION-A0 | design sample observation sidebar | P10 完成 |
| P12-BE | 后端能力增强（如有需求） | 用户反馈 |
| P12-APP | 本地 App 打包评估 | P10 完成 |
| 后续 | SaaS / 多用户 | 产品验证后 |

## Paused / Do not touch yet

| 区域 | 原因 |
|---|---|
| `batch_shared.js` | shared batch state 风险极高，需统一状态管理设计 |
| `profile_binding.js` | 被 voice list / audition / batch / clone / design 多处共用 |
| `audition_workstation.js` | 强耦合 `handleGenerate` 单条生成链路 |
| `error_helpers.js` | 被十余处引用，迁移成本大，收益小 |
| `provider_capabilities.js` | 已稳定，无充分理由动 |
| Vite / React migration | 当前阶段不引入 |
| dynamic loading | 当前阶段不需要 |
| tab/subtab switching | 涉及所有 Tab DOM visibility 状态，不应抽 |
| 移动端 H5 | 当前阶段不优先 |
| SaaS / 多用户 | 当前阶段不引入 |

## 详细历史来源

- 完整变更记录：`docs/PROJECT_HEALTH_CHECK.md`
- 前端模块化演进：`docs/P9_FRONTEND_MODULARIZATION.md`
- 产品打磨计划：`docs/P10_PRODUCT_POLISH_PLAN.md`
- P11 瘦身计划：`docs/P11_INDEX_REDUCTION_PLAN.md`
- P12 真实使用验证：`docs/P12_USAGE_VALIDATION_PLAN.md`
