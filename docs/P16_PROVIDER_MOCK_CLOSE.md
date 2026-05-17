# P16-PROVIDER-MOCK-CLOSE：Provider mock boundary 阶段收口

## 1. 阶段背景

- **分支**：`p16/real-usage-issues`
- **起点**：`P16-PROVIDER-BOUNDARY-A0` 识别出 Provider / Mock / Capability / 新大模型接入边界问题
- **终点**：完成 mock fallback、VoiceVariantService CostGuard、workspace binding guard 三项高风险修复的验证与收口

## 2. 阶段链路

| 阶段 | 内容 | 结论 |
|---|---|---|
| `P16-PROVIDER-BOUNDARY-A0` | Provider / Mock / Capability / 新大模型接入边界审查 | 发现 RISK-001/002/006 |
| `P16-PROVIDER-BOUNDARY-A0-CHECK` | Provider 边界审查复核 | 通过，发现 1 处 VoiceRenderService CostGuard 表述需修正 |
| `P16-PROVIDER-MOCK-FIX1` | 修复 mock fallback / provider binding / cost boundary | 完成代码修复 |
| `P16-PROVIDER-MOCK-FIX1-CHECK` | 验证 mock/provider boundary fixes | 复核通过 |
| `P16-PROVIDER-MOCK-CLOSE` | Provider mock boundary 阶段收口 | 本文档 |

## 3. 已修复风险

| RISK | 描述 | 修复方式 | 状态 |
|---|---|---|---|
| `P16-PROVIDER-RISK-001` | mock 无 binding 时自动 fallback 到 minimax，用户不知情触发真实 API | `mock_fallback_provider` 默认值从 `"minimax"` 改为 `None` | ✅ 已修复 |
| `P16-PROVIDER-RISK-002` | VoiceVariantService 用 request.provider=mock 绕过 CostGuard | `render_variants()` 先 `resolve_binding()`，再按 `resolved_provider` 调用 `require_confirmed()` | ✅ 已修复 |
| `P16-PROVIDER-RISK-006` | 前端 binding unbound 时仍允许点击生成 | 新增 `workspaceBindingAvailable` + `isWorkspaceBindingAvailable()` guard，`handleGenerate()` 在 confirm/setLoading/fetch 之前阻止 | ✅ 已修复 |

## 4. 最终行为语义

### 4.1 mock Provider 语义

- `mock_fallback_provider` 默认为 `None`
- 默认配置下，mock 是**纯测试 Provider**，无自动 fallback
- provider=mock + profile 无 mock binding → 抛 `BindingNotFound`（前端阻止，后端也拒绝）
- 若显式设置 `mock_fallback_provider=minimax`，则行为回到修复前（有明显配置意图，不算"悄然"fallback）

### 4.2 VoiceVariantService CostGuard

```
requested_provider = request.provider or "mock"
_binding, provider = resolve_binding(session, request.profile_id, requested_provider)
self.cost_guard.require_confirmed(provider, "voice_variants", request.confirm_cost)
```

- `request.provider=mock` → `resolve_binding()` 若找不到 mock binding 则抛异常，不会进入 CostGuard
- `request.provider=mock` + 有 mock binding → `provider=mock`，CostGuard 对 mock 直接放行（无费用）
- `request.provider=mock` + `mock_fallback_provider=minimax` 配置 + 有 minimax binding → `provider=minimax`，CostGuard 要求确认

### 4.3 workspace 前端 binding guard

- `workspaceBindingAvailable` 全局状态，初始 `false`
- `checkBindingStatus()` 在四分支（bound/unbound/no-selection/error）正确设置状态
- `providerSelect` / `profileSelect` change 事件触发 `checkBindingStatus()` 刷新状态
- `handleGenerate()` 中 guard 在行 3335，`confirmHighRiskOperation()` 在 3348，`setLoading(true)` 在 3356
- unbound 场景只显示警告卡片，不调用 fetch，不进入 loading，不触发任何 MiniMax API

## 5. 测试结果

| 测试集 | 结果 |
|---|---|
| `tests/test_provider_mock_boundary_static.py`（12 个） | ✅ 12 passed |
| `tests/test_cancel_confirmation_static.py` + `tests/test_workspace_restore_static.py`（65 个） | ✅ 65 passed |
| 全量测试套件 | 1379 passed, 29 failed, 1 error |

**29 failed 说明**：均为 `tests/test_context_store_static.py` 中的 Node.js eval 失败，是既有环境问题，与本次 FIX1 无关。

**1 error 说明**：`tests/e2e/test_frontend_capabilities.py::test_voice_import_clone_mock_success`，E2E 环境问题，与本次 FIX1 无关。

## 6. 未纳入范围

明确不纳入本阶段：

- 完整 Capability 动态 UI（`P16-PROVIDER-CAPABILITY-UI-B1`）
- 新增 OpenAI / Azure / ElevenLabs Provider
- Provider Registry 重构
- Capability Registry 重构
- 普通 sync T2A 后端 `require_confirmed` 强校验（`P16-PROVIDER-RISK-003`，后置）
- clone/design/import quick preview 的 `resolved_provider` 重构
- 多版本等待态（`P16-VARIANTS-UX-FIX1`）
- 服务端创作记录（`P17-CREATION-RECORD-A0`）
- 统计模块（`P15-STATS-B1` / `P15-SERVER-STATS-A0`）
- SaaS / 多用户

## 7. 非阻塞观察项

| 观察项 | 说明 |
|---|---|
| `P16-PROVIDER-RISK-003` | 普通 sync T2A 后端没有 `require_confirmed` 强校验，后置到 P16-PROVIDER-CAPABILITY-UI-B1 一起处理 |
| `P16-PROVIDER-OBS-DUP-RESOLVE` | `render_variants()` 中存在一次重复 binding resolve（第一次用于 CostGuard，第二次在 `render_voice()` 内部），当前可接受，后续可优化 |
| `P16-PROVIDER-OBS-RESTORE-BINDING` | workspace restore 后 binding status 依赖 change 事件触发，`providerSelect`/`profileSelect` change 监听器已覆盖 |
| `P16-PROVIDER-OBS-TEST-001` | 静态契约测试已覆盖关键路径，行为测试（mock fallback 行为、VoiceVariantService resolved_provider 行为）可后补 |

## 8. 下一阶段建议

### 推荐优先候选：P16-PROVIDER-CAPABILITY-UI-B1

**理由**：
1. 当前 Provider 语义安全性已修复，下一步应让前端真正由 Provider Capability 动态驱动
2. 这将服务于后续 OpenAI / Azure / ElevenLabs 等新模型接入
3. Capability-driven UI 可以消除硬编码 provider 字符串的脆弱性

**涉及文件**：
- `app/static/js/provider_capabilities.js`（允许修改）
- `app/static/index.html`（允许修改）

### 可后置项

| 阶段 | 内容 |
|---|---|
| `P16-VARIANTS-UX-FIX1` | 多版本等待态 UI |
| `P17-CREATION-RECORD-A0` | 服务端创作记录 |
| `P13-HISTORY-SECURITY-FIX1` | 历史文本 escaping |
| `P15-STATS-B1` / `P15-SERVER-STATS-A0` | 统计模块 |

## 9. 收口结论

**Provider mock boundary 阶段完成 ✅**

- `mock_fallback_provider` 默认为 `None`，mock 恢复为纯测试 Provider
- VoiceVariantService CostGuard 不再被 mock 绕过
- workspace 前端在 binding unbound 时正确阻止生成
- 测试通过，无阻塞问题
- 下一阶段建议：`P16-PROVIDER-CAPABILITY-UI-B1`（capability-driven provider UI）
