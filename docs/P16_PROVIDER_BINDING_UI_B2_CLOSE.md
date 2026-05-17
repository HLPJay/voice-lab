# P16-PROVIDER-BINDING-UI-B2-CLOSE：Provider-first profile/binding UI 阶段收口

## 1. 阶段背景

- **分支**: `p16/real-usage-issues`
- **收口日期**: 2026-05-16
- **阶段链路**: B2-A0 → B2 → B2-CHECK → B2-CLOSE

---

## 2. 阶段链路

| 阶段 | 状态 | 说明 |
|---|---|---|
| P16-PROVIDER-BINDING-UI-B2-A0 | ✅ 完成 | Provider-first profile/binding UI 设计 |
| P16-PROVIDER-BINDING-UI-B2 | ✅ 完成 | 实现 Provider-first Workspace UI |
| P16-PROVIDER-BINDING-UI-B2-CHECK | ✅ 通过（存在非阻塞观察项）| 验证 Provider-first profile/binding UI |
| P16-PROVIDER-BINDING-UI-B2-CLOSE | 🔄 进行中 | 阶段收口 |

---

## 3. 已完成能力

### 3.1 Workspace Provider-first 顺序

- Workspace 配置区已从 `profile-first` 调整为 `provider-first`
- Provider 下拉位于声音人设下拉之前
- 不影响绑定管理、Batch、Script 区域
- `providerSelect`/`profileSelect` 的 `id` 未改变
- 未新增 model 下拉

### 3.2 Profile 下拉标记

- Profile 下拉展示全部人设（方案 C：不隐藏）
- 当前 Provider 下无 binding 的 profile 标记为"未绑定当前 Provider"
- `dataset.bindingState` 标记为 `available` / `unbound` / `no-provider`
- 不全局修改 `populateProfileSelect`
- `bindingProfileSelect` / `newBindingProfile` / `batchProfile` 仍使用原 `populateProfileSelect`

### 3.3 参数区禁用

无 binding 时禁用：

| 元素 | 状态 |
|---|---|
| `paramSpeed` | ✅ 禁用 |
| `paramVol` | ✅ 禁用 |
| `paramPitch` | ✅ 禁用 |
| `paramEmotion` | ✅ 禁用 |
| `textInput` | ✅ 不禁用 |
| `providerSelect` | ✅ 不禁用 |
| `profileSelect` | ✅ 不禁用 |
| `audioFormat` | ✅ 不禁用 |
| `outputFormat` | ✅ 不禁用 |
| 参数值 | ✅ 不清空 |

CSS `.param-row.disabled-by-binding { opacity: 0.55; }` 已添加。

### 3.4 生成按钮禁用 + guard 保留

- 无 binding 时禁用 `generateBtn`
- `handleGenerate` 中 `isWorkspaceBindingAvailable()` guard 保留
- guard 位于 `confirmHighRiskOperation` / `setLoading(true)` / `fetch` 之前
- guard 文案："当前声音人设在所选 Provider 下没有可用绑定，请先到「绑定管理」创建绑定，或切换 Provider。"

### 3.5 Restore 后重新校验

- workspace restore 后触发 provider/profile change 事件
- `refreshWorkspaceProfileAvailability()` 刷新 profile 标记
- `checkBindingStatus()` 重新校验 binding 状态
- `updateWorkspaceBindingUiState()` 更新参数区/按钮状态
- 不直接信任历史 context 中的 binding_id/model

---

## 4. 当前最终语义

```
Provider 是 Workspace 第一约束。
Profile 是否可执行取决于当前 Provider 下是否存在 available binding。
无 binding 时允许用户看到 profile，但不能生成。
无 binding 时参数区禁用并提示绑定缺失。
真实生成仍由 handleGenerate guard 做最后防线。
```

---

## 5. 测试结果

| 测试文件 | 结果 |
|---|---|
| `tests/test_provider_binding_ui_static.py` | 28 passed |
| `tests/test_provider_model_binding_static.py` | 63 passed |
| `tests/test_provider_mock_boundary_static.py` | 37 passed |
| `tests/test_workspace_restore_static.py` + `tests/test_sample_sidebar_static.py` | 152 passed, 1 pre-existing failure |
| `tests/test_cancel_confirmation_static.py` | 26 passed |

**Pre-existing failure 说明**: `test_safePushWorkspaceSample_writes_context_id_to_sample` 在 `tests/test_workspace_restore_static.py` 中，与 B2 功能无关，是既有固定窗口测试问题。

---

## 6. 未纳入范围

B2 没有做以下任何一项：

| 未纳入项 | 说明 |
|---|---|
| 后端/API 修改 | - |
| VoiceBinding schema 修改 | - |
| ProviderVoice schema 修改 | - |
| resolve_binding 修改 | - |
| model 下拉 | - |
| binding_id 精确执行 | - |
| Capability-driven 参数禁用 | - |
| stream/subtitle/emotion/audio_format 动态禁用 | - |
| Batch longtext 改造 | - |
| Batch script 多角色 binding 改造 | - |
| Audition model 来源统一 | - |
| Clone / Design / Import model 来源统一 | - |
| Provider Registry / Capability Registry 改造 | - |
| SaaS / 多用户 | - |

---

## 7. 非阻塞观察项

### OBS-1: refreshWorkspaceProfileAvailability 标记可能不准确

**描述**: `_voiceBindMap` 不是全量缓存，`refreshWorkspaceProfileAvailability()` 可能将实际有 binding 的其他 profile 错误标记为"未绑定当前 Provider"。

**根因**: `checkBindingStatus()` 只向 `_voiceBindMap` 写入当前 profile 的 binding，不是全量缓存。全量缓存由 `loadAllBindings()`（仅被 `refreshVoiceBindMapForHints()` 调用，用于 longtext/script tab）填充。

**影响**: UI 标记可能不准确，但 `handleGenerate` guard 保护生成流程，不会错误发起真实生成。

**建议**: 后续可在 workspace tab 加载时预填充全量 binding，或将标记限制为当前 profile。

### OBS-2: profileSelect change 未 await checkBindingStatus

**描述**: `profileSelect` change handler 调用 `checkBindingStatus()` 时未使用 `await`，`updateWorkspaceBindingUiState()` 可能短暂使用旧的 `workspaceBindingAvailable`。

**影响**: 按钮/参数区可能短暂状态不同步，最终由 `checkBindingStatus()` 完成后的调用修正。

**建议**: 后续可将 profile change handler 改为 `async/await`。

---

## 8. 后续路线建议

### 推荐顺序

```
NEXT-PRIORITY-REVIEW（下一阶段优先级确认）
  ↓
P16-PROVIDER-BINDING-UI-B2-OBS-FIX1（优先）
  ↓
P16-PROVIDER-CAPABILITY-UI-B1
```

### P16-PROVIDER-BINDING-UI-B2-OBS-FIX1

**内容**:

1. 修复 `_voiceBindMap` 非全量导致 profile 标记可能不准确
2. 修复 `profileSelect` change 未 await checkBindingStatus 导致的短暂状态不同步

**推荐理由**: 这是进入 Capability UI 前的基础稳定性补强。Provider-first UI 如果标记不够准，后续做 capability-driven 参数区会更复杂。

### P16-PROVIDER-CAPABILITY-UI-B1

**内容**: 实现 provider/model capability 驱动 UI：stream/subtitle/emotion/audio_format/参数范围动态启用或禁用。

**前提**: 完成 B2 OBS-FIX1 后评估。

---

## 9. 收口结论

**Provider-first profile/binding UI 阶段完成** ✅

- Workspace 已调整为 Provider-first 顺序
- Profile 下拉标记"未绑定当前 Provider"
- 无 binding 时参数区和生成按钮正确禁用
- `handleGenerate` guard 保留作为最后防线
- restore 后重新校验 binding 状态
- 无阻塞问题
- 存在 2 个非阻塞观察项，不影响核心功能
- 测试全量通过（1 个 pre-existing failure 与 B2 无关）
