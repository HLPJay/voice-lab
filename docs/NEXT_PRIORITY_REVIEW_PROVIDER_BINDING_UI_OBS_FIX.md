# NEXT-PRIORITY-REVIEW：选择 Provider-first UI 观察项修复

## 1. 当前状态

- **分支**: `p16/real-usage-issues`
- **决策日期**: 2026-05-16
- **当前阶段**: `NEXT-PRIORITY-REVIEW`

Provider-first profile/binding UI 阶段已收口（`B2-A0 → B2 → B2-CHECK → B2-CLOSE`），存在 2 个非阻塞观察项待后续处理。

---

## 2. 已完成阶段

| 阶段 | 状态 |
|---|---|
| P16-PROVIDER-BINDING-UI-B2-A0：Provider-first profile/binding UI 设计 | ✅ |
| P16-PROVIDER-BINDING-UI-B2：实现 Provider-first profile/binding UI | ✅ |
| P16-PROVIDER-BINDING-UI-B2-CHECK：验证 Provider-first profile/binding UI | ✅ |
| P16-PROVIDER-BINDING-UI-B2-CLOSE：Provider-first profile/binding UI 阶段收口 | ✅ |

---

## 3. 当前保留观察项

### OBS-1: _voiceBindMap 非全量导致 profile 标记可能不准确

**描述**: `_voiceBindMap` 不是全量缓存，`refreshWorkspaceProfileAvailability()` 可能将实际有 binding 的其他 profile 错误标记为"未绑定当前 Provider"。

**根因**: `checkBindingStatus()` 只向 `_voiceBindMap` 写入当前 profile 的 binding，不是全量缓存。全量缓存由 `loadAllBindings()`（仅被 `refreshVoiceBindMapForHints()` 调用）填充。

**影响**: UI 标记可能不准确，但 `handleGenerate` guard 保护生成流程，不会错误发起真实生成。

### OBS-2: profileSelect change 未 await checkBindingStatus

**描述**: `profileSelect` change handler 调用 `checkBindingStatus()` 时未使用 `await`，`updateWorkspaceBindingUiState()` 可能短暂使用旧的 `workspaceBindingAvailable`。

**影响**: 按钮/参数区可能短暂状态不同步，最终由 `checkBindingStatus()` 完成后的调用修正。

---

## 4. 为什么不直接进入 Capability UI

Capability UI 依赖 Provider-first UI 的可用性判断稳定。

如果"当前 Provider 下哪些 profile/binding 可用"的标记不够准确，后续基于 provider/model capability 禁用参数和模式会更复杂：

- 参数区和模式启用的逻辑依赖准确的 binding 可用性判断
- 标记不准确会传导到 capability-driven 的禁用逻辑
- 在不稳定基础上叠加新功能会积累技术债务

因此下一阶段应先补强 Provider-first UI 的基础准确性，再进入 Capability UI。

---

## 5. 推荐下一阶段

**P16-PROVIDER-BINDING-UI-B2-OBS-FIX1：修复 Provider-first UI 观察项**

一句话目标：

> 补强 Provider-first UI 的状态准确性：确保 workspace profile 标记基于可靠 binding 数据，并让 profile change 的 binding 状态更新严格同步。

---

## 6. OBS-FIX1 建议范围

### 6.1 OBS-1 修复方向

**核心问题**: `_voiceBindMap` 不是全量缓存，导致其他 profile 的 binding 状态无法准确判断。

**修复方向**: 在 workspace 初始化 / provider change 前调用 `loadAllBindings()` 预填充全量 binding。

`loadAllBindings()` 已有实现（`index.html` 第 5025 行），它：
- 调用后端 `GET /api/voice/profiles/{id}/bindings`（本地后端，非真实 MiniMax）
- 返回所有 profile 的 available binding
- 可以被 `refreshVoiceBindMapForHints()` 以外的场景调用

**OBS-FIX1 A0/A1 需确认**：
1. `loadAllBindings()` 当前是否存在（已确认存在）
2. 调用频率是否可接受（workspace 初载 / provider change 时调用一次）
3. 是否需要节流/防抖
4. 是否需要缓存及缓存失效策略

### 6.2 OBS-2 修复方向

**核心问题**: `profileSelect` change handler 未 await `checkBindingStatus()`，导致 `updateWorkspaceBindingUiState()` 可能先于 binding 状态更新执行。

**修复方向**:

```javascript
// profileSelect change
profileSelect.addEventListener('change', async () => {
  await checkBindingStatus();
  updateWorkspaceBindingUiState();
  updateWorkspaceVoiceBindingHint();
});
```

同步评估 `providerSelect` change 是否需要 async：

```javascript
// providerSelect change - 建议评估
providerSelect.addEventListener('change', async () => {
  // 预填充全量 binding map（如果 OBS-1 也修复）
  await refreshWorkspaceBindingMap?.();
  refreshWorkspaceProfileAvailability();
  await checkBindingStatus();
  updateCostHint();
  updateWorkspaceVoiceBindingHint();
});
```

**原则**：
- 不改变 `checkBindingStatus` 的业务语义
- 不改变 `handleGenerate` guard
- 不清空文本或参数

### 6.3 OBS-FIX1 建议纳入

| 纳入项 | 说明 |
|---|---|
| Workspace 初载时调用 `loadAllBindings()` | 确保 `_voiceBindMap` 包含全量 binding |
| Provider change 前/后确保 binding map 可用 | 准确标记所有 profile |
| `profileSelect` change 改为 async/await | 严格同步状态 |
| `providerSelect` change async 评估 | 是否需要 await `checkBindingStatus()` |
| 新增或补强静态测试 | 覆盖 OBS-FIX1 修复点 |

### 6.4 OBS-FIX1 不纳入

| 不纳入项 | 说明 |
|---|---|
| Capability UI | 属于 `P16-PROVIDER-CAPABILITY-UI-B1` |
| model 下拉 | - |
| resolve_binding 修改 | - |
| 后端/API 修改 | - |
| VoiceBinding / ProviderVoice schema | - |
| Batch / Script / Clone / Design / Audition | - |
| binding_id 精确执行 | - |

---

## 7. 不纳入范围

**不直接进入 Capability UI** 的原因：

1. Provider-first UI 的 binding 可用性标记尚有观察项未修复
2. Capability UI 依赖准确的 binding 判断
3. 在不稳定基础上叠加新功能会积累技术债务

**Capability UI 等待条件**：
- OBS-FIX1 完成并验证
- Provider-first UI 状态准确性已确认

---

## 8. 决策结论

**下一阶段**: `P16-PROVIDER-BINDING-UI-B2-OBS-FIX1`

**决策依据**：
- Provider-first UI 是 Capability UI 的基础
- 两个观察项影响 UI 标记准确性，但不阻塞核心功能
- 修复成本低，收益明确
- 直接进入 Capability UI 会在不稳定基础上叠加复杂度
