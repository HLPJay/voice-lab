# Next Tasks

## 当前阶段

**P10 产品打磨**

## 已完成

- P9-FE1：voice_clone.js、voice_import.js、voice_design.js 抽离 ✅
- P9-FE2-A0：index.html 剩余逻辑边界审查 ✅
- P10-PRODUCT-A0：产品打磨优先级审查 ✅

## P10-PRODUCT-A0 审查结论

### 用户主流程问题

| 问题 | 优先级 | 说明 |
|---|---|---|
| Workspace 音色入口不直观 | 1 | 音色选择隐藏在 audition workstation，需要跳转 |
| Voices tab 孤立于创作流程 | 2 | 选音色后要跳转到 workspace 继续 |
| Batch tab 音色选择需跨 tab | 3 | 长文本/剧本需要跳转选音色 |
| 没有 first-time guidance | 4 | 新用户不知道从哪开始 |
| Advanced tab 入口深 | 5 | clone/design/import 入口不明确 |

### P10 任务排序

| 优先级 | 任务 | 风险 |
|---|---|---|
| 1 | Workspace 音色快捷选择区 | 低 |
| 2 | Voices tab 快速创作联动 | 中 |
| 3 | Batch tab 音色快速选择 | 中 |
| 4 | 简化 onboarding 文案 | 极低 |
| 5 | Advanced tab 重命名 | 极低 |
| 6 | 历史最近任务快捷入口 | 低 |

### 不应该投入的方向

- 移动端 H5 适配
- 创作模板 / 场景入口
- SaaS / 多用户
- 开放 API 平台
- 桌面 App 打包

详见：`docs/P10_PRODUCT_POLISH_PLAN.md`

## Next

1. **P10-PRODUCT-B1** — Workspace 音色快捷选择区（优先级 1）

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
