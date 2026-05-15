# Next Tasks

## 当前阶段

**P10 产品打磨**

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

## P10-PRODUCT-B2 实现总结

**实现内容：**
- 在 quickBindVoice 绑定成功消息中增加"去创作"按钮
- 点击"去创作"按钮切换到 workspace tab
- 不改生成链路，不改绑定逻辑，不改后端 API

**E2E：** `test_quick_bind_success_go_create_switches_workspace` — mock profiles/bindings/provider-voices/capabilities，验证绑定成功后出现"去创作"按钮，点击后切换到 workspace tab

**E2E 结果：** 27 passed

详见：`docs/P10_PRODUCT_POLISH_PLAN.md` P10-PRODUCT-B2 节

## Next

1. **P10-PRODUCT-B3-script** — Batch script tab 每行动态绑定音色提示

**实现内容：**
- 在 workspace "配置" card 的 `profileSelect` 下方增加轻量提示区 `#workspaceVoiceBindingHint`
- `updateWorkspaceVoiceBindingHint()` 读取 `_voiceBindMap`，显示当前绑定 voice 或"尚未绑定音色"
- 无绑定时显示"去选择音色"按钮，点击切换到 voices tab
- profileSelect change / providerSelect change / populateAllProfiles / workspace tab 切换时更新提示

**E2E：** `test_workspace_voice_binding_hint_switches_to_voices` — 验证 hint 显示"尚未绑定音色"、点击按钮切换到 voices tab

**E2E 结果：** 26 passed

详见：`docs/P10_PRODUCT_POLISH_PLAN.md` P10-PRODUCT-B1 节

## Next

1. **P10-PRODUCT-B2** — Voices tab 快速创作联动实现（添加"去创作"按钮）

### P10 任务排序

| 优先级 | 任务 | 状态 |
|---|---|---|
| 1 | B1: Workspace 音色快捷选择区 | ✅ 已完成 |
| 2 | B2-A0: Voices tab 快速创作联动边界审查 | ✅ 已完成 |
| 3 | B2: Voices tab 快速创作联动实现 | ✅ 已完成 |
| 4 | B3-A0: Batch tab 音色快速选择边界审查 | ✅ 已完成 |
| 5 | B3-longtext: Batch longtext tab 绑定音色提示 | ✅ 已完成 |
| 6 | B3-script: Batch script tab 每行动态绑定音色提示 | 待做 |
| 4 | B4: 简化 onboarding 文案 | 待做 |
| 5 | B5: Advanced tab 重命名 | 待做 |
| 6 | B6: 历史最近任务快捷入口 | 待做 |

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
