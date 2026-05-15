# Next Tasks

## 当前阶段

**P10 产品打磨**

## 已完成

- P9-FE1：voice_clone.js、voice_import.js、voice_design.js 抽离 ✅
- P9-FE2-A0：index.html 剩余逻辑边界审查 ✅
- P10-PRODUCT-A0：产品打磨优先级审查 ✅
- P10-PRODUCT-B0：Workspace 音色快捷选择区边界审查 ✅

## P10-PRODUCT-B0 审查结论

### 关键发现

**两个独立的音色选择系统：**
- **Profile binding**：workspace 生成用 `profileSelect.value`，需先在 voices tab 绑定 voice 到 profile
- **Voice audition**：voices tab 试听用 `window._auditionSelectedVoiceId`，是不同系统

**问题本质：** workspace "配置"区无当前绑定 voice 的提示，用户不知道 profile 需要绑定 voice，也不知道去哪绑定。

### B1 最小实现方案

**不改：** `handleGenerate`、后端 API、voice list

**只做：** 在 workspace "配置" card 的 `profileSelect` 下方增加轻量提示区，显示当前 profile 绑定的 voice + "去选择音色"按钮（切换到 voices tab）

详见：`docs/P10_PRODUCT_POLISH_PLAN.md` P10-PRODUCT-B0 节

## Next

1. **P10-PRODUCT-B1** — Workspace 音色快捷选择区（不改生成链路，只增 UI 引导）

### P10 任务排序

| 优先级 | 任务 | 风险 |
|---|---|---|
| 1 | B1: Workspace 音色快捷选择区 | 低 |
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
