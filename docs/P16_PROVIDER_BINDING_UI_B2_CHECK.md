# P16-PROVIDER-BINDING-UI-B2-CHECK：验证 Provider-first profile/binding UI

## 1. 阶段背景

- **分支**: `p16/real-usage-issues`
- **被检核提交**: `d8ba100 feat: add provider-first workspace binding UI`
- **检核时间**: 2026-05-16
- **检核结论**: 通过（存在非阻塞观察项）

---

## 2. 提交范围核验

确认修改文件只包含：

| 文件 | 状态 |
|---|---|
| `app/static/index.html` | ✅ |
| `tests/test_provider_binding_ui_static.py`（新增） | ✅ |
| `docs/PROJECT_HEALTH_CHECK.md` | ✅ |
| `docs/agent/NEXT_TASKS.md` | ✅ |

未修改以下禁止区域：

| 文件 | 状态 |
|---|---|
| `app/models/*` | ✅ 未修改 |
| `app/repositories/*` | ✅ 未修改 |
| `app/services/*` | ✅ 未修改 |
| `app/api/*` | ✅ 未修改 |
| `app/providers/*` | ✅ 未修改 |
| `app/domain/*` | ✅ 未修改 |
| `profile_binding.js` | ✅ 未修改 |
| `provider_capabilities.js` | ✅ 未修改 |
| `context_store.js` | ✅ 未修改 |
| `sample_store.js` | ✅ 未修改 |
| `sample_sidebar.js` | ✅ 未修改 |
| `batch_shared.js` | ✅ 未修改 |
| `audition_records.js` | ✅ 未修改 |
| `voice_clone.js` | ✅ 未修改 |
| `voice_design.js` | ✅ 未修改 |
| `voice_import.js` | ✅ 未修改 |

---

## 3. Provider-first DOM 复核

**结论**: ✅ 通过

Workspace 配置区 DOM 顺序已从 `profile-first` 调整为 `provider-first`：

```html
<!-- B2 实现：Provider 在前 -->
<div class="form-group">
  <label for="providerSelect">Provider</label>
  <select id="providerSelect">...</select>
</div>
<div class="form-group">
  <div class="field-label-row">
    <label for="profileSelect">声音人设</label>
    <span id="bindingStatus" class="binding-status-inline"></span>
  </div>
  <select id="profileSelect">...</select>
  <div id="workspaceVoiceBindingHint">...</div>
</div>
```

- ✅ `providerSelect` 出现在 `profileSelect` 之前
- ✅ 不影响绑定管理、Batch、Script 区域
- ✅ `providerSelect`/`profileSelect` 的 `id` 未改变
- ✅ 未新增 model 下拉

---

## 4. Workspace helper 复核

**结论**: ✅ 通过

| Helper 函数 | 状态 |
|---|---|
| `getWorkspaceProfileBindingState(provider, profileId)` | ✅ 存在，返回 `available`/`unbound`/`no-provider`/`no-profile` |
| `refreshWorkspaceProfileAvailability()` | ✅ 存在，遍历 `_cachedProfiles`，不调用 `populateProfileSelect` |
| `setWorkspaceBindingControlsEnabled(enabled, reason)` | ✅ 存在，禁用参数区 |
| `updateWorkspaceBindingUiState(reasonOverride)` | ✅ 存在，统一状态函数 |

---

## 5. Profile 标记逻辑复核（重点）

**结论**: ⚠️ 非阻塞观察项（OBS-1）

### 观察项说明

`refreshWorkspaceProfileAvailability()` 通过遍历 `_voiceBindMap` 判断每个 profile 是否绑定当前 Provider。但 `_voiceBindMap` 的填充逻辑如下：

| 场景 | `_voiceBindMap` 内容 | 标记结果 |
|---|---|---|
| 页面初载 | `checkBindingStatus()` 仅填充当前 profile 的 binding | ✅ 当前 profile 标记正确；其他 profile 标记为"未绑定当前 Provider"（可能不准确） |
| Provider 切换后（`refreshWorkspaceProfileAvailability()` 先执行） | 仍是旧 Provider 下当前 profile 的 binding | ⚠️ 所有 profile 标记为"未绑定当前 Provider"（瞬时，不准确） |
| `checkBindingStatus()` 返回后 | 当前 profile 的 binding 被更新 | ✅ 当前 profile 标记正确；其他 profile 标记仍可能不准确 |

### 根因分析

`checkBindingStatus()`（第 4304-4326 行）只向 `_voiceBindMap` 写入**当前选中的 profile**的 binding，不是全量缓存。全量缓存由 `loadAllBindings()`（仅被 `refreshVoiceBindMapForHints()` 调用，用于 longtext/script tab）填充。

### 影响评估

1. **不导致错误生成**: `handleGenerate` guard (`isWorkspaceBindingAvailable()`) 基于 `checkBindingStatus()` 后的 `workspaceBindingAvailable` 状态，与标记无关。
2. **UI 显示不准确**: 用户可能看到其他 profile 显示"未绑定当前 Provider"，但实际可能有 binding。
3. **最终状态正确**: 用户切换到有 binding 的 profile 后，`checkBindingStatus()` 会正确设置 `workspaceBindingAvailable`，按钮会启用。
4. **标记是信息提示，不是功能约束**: 参数区和生成按钮的启用/禁用由 `updateWorkspaceBindingUiState()` 控制，该函数使用 `workspaceBindingAvailable`（准确值），而非标记。

### 是否阻塞

**不阻塞**: 虽然标记不完美，但：
- `handleGenerate` guard 始终保护生成流程
- `updateWorkspaceBindingUiState()` 对当前 profile 使用准确状态
- 用户仍可通过选择不同 profile 获得正确 UI 状态

建议后续优化：考虑在 workspace tab 也调用 `loadAllBindings()` 预填充全量 binding，或将标记改为仅针对当前 profile。

---

## 6. Provider/Profile change 事件顺序复核

**结论**: ✅ 通过（存在非阻塞观察项 OBS-2）

### 实现确认

```javascript
providerSelect.addEventListener('change', () => {
  refreshWorkspaceProfileAvailability();
  checkBindingStatus();
  updateCostHint();
  updateWorkspaceVoiceBindingHint();
});

profileSelect.addEventListener('change', () => {
  checkBindingStatus();
  updateWorkspaceBindingUiState();
  updateWorkspaceVoiceBindingHint();
});
```

- ✅ Provider change: 先 `refreshWorkspaceProfileAvailability()` 再 `checkBindingStatus()`
- ✅ Profile change: `checkBindingStatus()` 再 `updateWorkspaceBindingUiState()`
- ✅ 均不清空 textInput 或参数值

### 观察项 OBS-2: profileSelect change 未 await checkBindingStatus

`checkBindingStatus()` 是 async 函数，但 profileSelect change handler 中未使用 `await`。因此 `updateWorkspaceBindingUiState()` 可能在 `checkBindingStatus()` 返回前执行，使用旧的 `workspaceBindingAvailable` 值。

**影响**: 按钮/参数区状态可能短暂不准确，最终由 `checkBindingStatus()` 完成后的 `updateWorkspaceBindingUiState()` 调用修正。

**不阻塞原因**: `handleGenerate` guard 保护，即使按钮误启用也不会发出真实请求。

---

## 7. 参数区禁用复核

**结论**: ✅ 通过

`setWorkspaceBindingControlsEnabled(enabled, reason)` 实现：

| 元素 | 禁用行为 |
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

---

## 8. generateBtn / setLoading 复核

**结论**: ✅ 通过（无冲突）

### setLoading 实现

```javascript
function setLoading(on) {
  generateBtn.disabled = on;
  generateBtn.innerHTML = on
    ? '<span class="spinner"></span>生成中…'
    : '生成';
}
```

### Guard 流程分析

当 `handleGenerate()` 被调用时：

| 场景 | Guard 结果 | setLoading 调用 | 按钮最终状态 |
|---|---|---|---|
| unbound | 失败，显示错误，返回 | 不调用 | 保持 disabled（由 updateWorkspaceBindingUiState 设置） |
| bound + 用户未 confirm | confirm 返回 false | 不调用 | 保持 enabled |
| bound + 用户 confirm | 通过 | `setLoading(true)` | disabled（loading） |
| fetch 成功/失败 | - | `setLoading(false)` | enabled |

**关键验证**: unbound 场景下，`handleGenerate` guard 先于 `setLoading(true)` 检查 `isWorkspaceBindingAvailable()`，因此 `setLoading` 不会在 unbound 时覆盖 disabled 状态。

**即使 setLoading(false) 覆盖 disabled**: `updateWorkspaceBindingUiState()` 在 `checkBindingStatus()` 完成后会重新设置正确的按钮状态。

---

## 9. handleGenerate guard 复核

**结论**: ✅ 通过

Guard 保留在 `handleGenerate()` 开头：

```javascript
if (!isWorkspaceBindingAvailable()) {
  resultsArea.innerHTML = `
    <div class="card" style="border-left:4px solid #dd6b20">
      <div class="result-label" style="color:#dd6b20">无法生成</div>
      <p style="font-size:0.9rem;color:#4a5568;margin-top:8px">
        当前声音人设在所选 Provider 下没有可用绑定，请先到「绑定管理」创建绑定，或切换 Provider。
      </p>
    </div>
  `;
  return;
}
```

- ✅ 在 `confirmHighRiskOperation` 之前
- ✅ 在 `setLoading(true)` 之前
- ✅ 在 fetch 之前
- ✅ 文案提示"创建绑定或切换 Provider"

---

## 10. checkBindingStatus 集成复核

**结论**: ✅ 通过

各分支均调用 `updateWorkspaceBindingUiState()`：

| 分支 | updateWorkspaceBindingUiState 调用 |
|---|---|
| no-selection (`if (!profileId \|\| !provider)`) | ✅ `updateWorkspaceBindingUiState()` |
| bound (`matched.length > 0`) | ✅ `updateWorkspaceBindingUiState()` |
| unbound | ✅ `updateWorkspaceBindingUiState(reason)` |
| catch | ✅ `updateWorkspaceBindingUiState(reason)` |

- ✅ `workspaceBindingAvailable` 语义未破坏
- ✅ `currentWorkspaceBindingInfo` 清理语义未破坏
- ✅ `updateWorkspaceVoiceBindingHint()` 仍被调用

---

## 11. restore 后状态复核

**结论**: ✅ 通过

Workspace restore 链路（`sample_sidebar.js` 第 856-867 行）：

```javascript
providerEl.value = context.provider || '';
dispatchInputChange(providerEl);  // 触发 provider change handler

profileEl.value = context.profile_id || '';
dispatchInputChange(profileEl);    // 触发 profile change handler
```

触发的事件：

| 事件 | 触发的处理 |
|---|---|
| provider change | `refreshWorkspaceProfileAvailability()` + `checkBindingStatus()` |
| profile change | `checkBindingStatus()` + `updateWorkspaceBindingUiState()` |

- ✅ restore 后重新校验 binding
- ✅ 不直接信任历史 context 的 binding_id/model
- ✅ 不自动提交

**观察**: restore 后 profile change handler 的 `updateWorkspaceBindingUiState()` 使用可能暂旧的 `workspaceBindingAvailable`，但最终由 `checkBindingStatus()` 完成后的调用修正。

---

## 12. Mock 场景复核

**结论**: ✅ 通过

- ✅ Provider=mock 时不 fallback minimax
- ✅ mock 下无 binding 时 profile 标记"未绑定当前 Provider"
- ✅ mock 下无 binding 时参数区和生成按钮禁用
- ✅ handleGenerate guard 仍阻止请求

---

## 13. 越界修改复核

**结论**: ✅ 通过

- ✅ 未修改 `app/models/*`、`app/repositories/*`、`app/services/*`、`app/api/*`
- ✅ 未新增 model 下拉
- ✅ 未越界进入 Capability UI
- ✅ 未修改 Batch/Script/Clone/Design/Audition

---

## 14. 测试结果

### B2 静态测试

```bash
$ python -m pytest tests/test_provider_binding_ui_static.py -q
............................
28 passed in 0.45s
```

### 回归测试

```bash
$ python -m pytest tests/test_provider_model_binding_static.py -q
..................................................
63 passed in 0.58s

$ python -m pytest tests/test_provider_mock_boundary_static.py -q
..................................................
37 passed in 0.52s

$ python -m pytest tests/test_workspace_restore_static.py tests/test_sample_sidebar_static.py -q
..................................................
152 passed, 1 failed (pre-existing)
```

**Pre-existing failure**: `test_safePushWorkspaceSample_writes_context_id_to_sample` 在 `tests/test_workspace_restore_static.py` 中，与 B2 修改无关（`_voiceBindMap` 缓存问题与该测试失败原因不同）。

### 额外测试

```bash
$ python -m pytest tests/test_cancel_confirmation_static.py -q
................................
26 passed in 0.38s
```

---

## 15. 阻塞问题

**无阻塞问题**

---

## 16. 非阻塞观察项

### OBS-1: refreshWorkspaceProfileAvailability 标记可能不准确

**描述**: `_voiceBindMap` 不是全量缓存，`refreshWorkspaceProfileAvailability()` 可能将实际有 binding 的 profile 错误标记为"未绑定当前 Provider"。

**影响**: UI 显示不准确，但不导致错误生成（guard 保护）。

**建议**: 后续考虑在 workspace tab 加载时调用 `loadAllBindings()` 预填充全量 binding，或将标记限制为仅针对当前 profile。

### OBS-2: profileSelect change 未 await checkBindingStatus

**描述**: `profileSelect` change handler 调用 `checkBindingStatus()` 时未使用 `await`，导致 `updateWorkspaceBindingUiState()` 可能先于 `checkBindingStatus()` 返回执行。

**影响**: 按钮/参数区状态可能短暂不准确，最终由 `checkBindingStatus()` 完成后的调用修正。

**建议**: 如需严格状态同步，可在 profile change handler 中 `await checkBindingStatus()` 后再调用 `updateWorkspaceBindingUiState()`。

---

## 17. 复核结论

**✅ 通过**

满足以下通过条件：

1. ✅ 修改范围符合 B2 边界
2. ✅ Workspace 已 Provider-first
3. ✅ profile 下拉标记未绑定当前 Provider（存在 OBS-1）
4. ✅ 无 binding 时参数区禁用
5. ✅ 无 binding 时生成按钮禁用
6. ✅ handleGenerate guard 保留
7. ✅ 未修改后端/API/schema/resolve_binding
8. ✅ 未新增 model 下拉
9. ✅ 未越界进入 Capability UI
10. ✅ _voiceBindMap 判断误伤风险已评估为非阻塞（guard 保护）

---

## 18. 后续阶段建议

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-PROVIDER-BINDING-UI-B2-CLOSE | close provider-first profile/binding UI phase | B2-CHECK 完成 |
| P16-PROVIDER-CAPABILITY-UI-B1 | capability-driven provider/model UI | B2-CLOSE 后评估 |
| P16-VARIANTS-UX-FIX1 | add visible waiting state for voice variants | 可后置 |
| P17-CREATION-RECORD-A0 | design server-side creation record and restore API | Backlog |
| P13-HISTORY-SECURITY-FIX1 | escape history text snippet | 小型安全债 |
| P15-STATS-B1 | local statistics panel | Backlog |
| P15-SERVER-STATS-A0 | server-side statistics | Backlog |
