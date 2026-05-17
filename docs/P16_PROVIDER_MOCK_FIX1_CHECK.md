# P16-PROVIDER-MOCK-FIX1-CHECK：验证 mock/provider boundary fixes

## 1. 阶段背景

- **复核 commit**：`b2e57d0` ("fix: repair mock provider fallback and cost boundary")
- **分支**：`p16/real-usage-issues`
- **复核目标**：验证 `P16-PROVIDER-MOCK-FIX1` 是否正确修复 RISK-001、RISK-002、RISK-006

## 2. 远端提交核验

### 2.1 修改文件清单

```
app/core/config.py                          | 2 +-
app/services/voice_variant_service.py       | 5 +-
app/static/index.html                       | 25 +++
docs/PROJECT_HEALTH_CHECK.md                | 86 +++++++++-
docs/agent/NEXT_TASKS.md                    | 3 +-
tests/test_provider_mock_boundary_static.py  | 223 +++++++++++++++++++++++++++
```

**确认**：未越界修改 `app/providers/*`、`app/repositories/*`、`app/api/*`、`app/services/cost_guard_service.py`、`app/static/js/provider_capabilities.js`。

### 2.2 未修改范围确认

| 文件 | 未修改 | 说明 |
|---|---|---|
| `app/providers/*` | ✅ | 未动 |
| `app/repositories/*` | ✅ | voice_profile_repo.py 未改 |
| `app/api/*` | ✅ | 未动 |
| `app/services/cost_guard_service.py` | ✅ | 未动 |
| `app/static/js/provider_capabilities.js` | ✅ | 未动 |
| `voice_clone.js` | ✅ | 未动 |
| `voice_design.js` | ✅ | 未动 |
| `voice_import.js` | ✅ | 未动 |

## 3. RISK-001 修复复核

**风险**：mock 无 binding 时自动 fallback 到 minimax，导致用户在不知情情况下触发真实 MiniMax API 调用并产生费用。

### 3.1 config.py 变更

```python
# 修改前
mock_fallback_provider: str | None = "minimax"

# 修改后（b2e57d0）
mock_fallback_provider: str | None = None  # None = mock is pure test, no auto-fallback
```

**结论**：✅ 默认值已改为 `None`。

### 3.2 resolve_binding() 逻辑复核

`voice_profile_repo.py` 中 `resolve_binding()` 逻辑未修改，保留原有的 fallback 条件：

```python
if provider == "mock" and settings.mock_fallback_provider:  # 只有 None 时不触发
    binding = get_binding(session, profile_id, settings.mock_fallback_provider)
```

由于 `settings.mock_fallback_provider` 默认 `None`，条件永不为真。

### 3.3 行为推演

| 场景 | 结果 |
|---|---|
| provider=mock，profile 有 minimax binding，无 mock binding，默认配置 | → 抛 `BindingNotFound`，不 fallback |
| provider=mock，profile 有 minimax binding，无 mock binding，显式设置 `mock_fallback_provider=minimax` | → fallback minimax，需 CostGuard 确认 |

**结论**：✅ RISK-001 已修复。

## 4. RISK-002 修复复核

**风险**：`VoiceVariantService.render_variants()` 使用 `request.provider=mock` 调用 `CostGuard.require_confirmed()`，导致 mock 绕过费用确认。

### 4.1 voice_variant_service.py 变更

```python
# 修改前
provider = request.provider or "mock"
self.cost_guard.require_confirmed(provider, "voice_variants", request.confirm_cost)

# 修改后（b2e57d0）
requested_provider = request.provider or "mock"
_binding, provider = resolve_binding(session, request.profile_id, requested_provider)
self.cost_guard.require_confirmed(provider, "voice_variants", request.confirm_cost)
```

### 4.2 导入确认

```python
from app.repositories.voice_profile_repo import resolve_binding
```

✅ 已导入。

### 4.3 调用顺序确认

| 顺序 | 操作 | 正确性 |
|---|---|---|
| 1 | `requested_provider = request.provider or "mock"` | ✅ |
| 2 | `_binding, provider = resolve_binding(...)` | ✅ 在 CostGuard 之前 |
| 3 | `self.cost_guard.require_confirmed(provider, ...)` | ✅ 使用 resolved_provider |
| 4 | `VoiceRenderRequest(provider=provider, ...)` | ✅ 子调用也用 resolved_provider |

### 4.4 行为推演

| 场景 | 结果 |
|---|---|
| request.provider=mock，profile 无 mock binding，默认配置 | → `resolve_binding()` 抛 `BindingNotFound`，不进入 CostGuard |
| request.provider=mock，profile 有 mock binding | → `provider=mock`，`require_confirmed(mock, ...)` 直接通过（mock 无费用） |
| request.provider=mock，profile 有 minimax binding，`mock_fallback_provider=minimax` | → `provider=minimax`，`require_confirmed(minimax, ...)` 要求确认 |

**结论**：✅ RISK-002 已修复。

### 4.5 重复 binding resolve 记录

`render_variants()` 先调用 `resolve_binding()` 用于 CostGuard，子公司调用 `render_voice()` 内部又会再次解析 binding。

**记录**：`P16-PROVIDER-OBS-DUP-RESOLVE`：存在一次重复 binding resolve，当前可接受，后续可优化。

## 5. RISK-006 修复复核

**风险**：前端 workspace 在 binding unbound 时仍允许点击生成，导致无效请求。

### 5.1 index.html 变更清单

1. **全局变量**：`let workspaceBindingAvailable = false;`（初始安全默认值）
2. **辅助函数**：`function isWorkspaceBindingAvailable() { return workspaceBindingAvailable === true; }`
3. **checkBindingStatus() 四分支赋值**：
   - `!profileId || !provider` → `workspaceBindingAvailable = false`
   - `matched.length > 0` → `workspaceBindingAvailable = true`
   - `matched.length === 0` → `workspaceBindingAvailable = false`
   - `catch` → `workspaceBindingAvailable = false`
4. **handleGenerate() guard block**：
   ```javascript
   if (!isWorkspaceBindingAvailable()) {
     resultsArea.innerHTML = `<div class="card" style="border-left:4px solid #dd6b20">...</div>`;
     return;
   }
   ```

### 5.2 guard 顺序复核

| 行 | 操作 | 在 guard 之后？ |
|---|---|---|
| 3335-3346 | `isWorkspaceBindingAvailable()` guard → return | — |
| 3348-3351 | `confirmHighRiskOperation()` | ✅ 在 guard 之后 |
| 3353-3355 | `stopAsyncPolling()`, `pollTimer` 清理 | ✅ 在 guard 之后 |
| 3356 | `setLoading(true)` | ✅ 在 guard 之后 |
| 3357-3358 | `resultsArea.classList.remove('visible')`, `resultsArea.innerHTML = ''` | ✅ 在 guard 之后 |
| 3360+ | `buildWorkspaceSampleContext()`, `fetch()` | ✅ 在 guard 之后 |

**结论**：✅ guard 在所有 side effects 之前。

### 5.3 profile/provider 切换触发复核

```javascript
// index.html 行 2409-2410
providerSelect.addEventListener('change', () => { checkBindingStatus(); ... });
profileSelect.addEventListener('change', () => { checkBindingStatus(); ... });
```

✅ `providerSelect` 和 `profileSelect` 的 `change` 事件均触发 `checkBindingStatus()`。

### 5.4 页面初始化触发复核

```javascript
// index.html 行 2114, 2388
checkBindingStatus();
```

✅ 初始化流程中有调用 `checkBindingStatus()`。

**结论**：✅ RISK-006 已修复。

## 6. 潜在问题复核

### 6.1 页面初始化状态

`workspaceBindingAvailable` 初始值为 `false`。若用户页面加载后立即点击生成，会被 guard 阻止。

**结论**：安全优先，可接受。

### 6.2 workspace restore 后状态刷新

workspace restore 后 provider/profile 通过 `change` 事件触发 `checkBindingStatus()` 更新 `workspaceBindingAvailable`。

**记录**：`P16-PROVIDER-OBS-RESTORE-BINDING`：workspace restore 后 binding status 依赖 change 事件触发，当前代码中 profileSelect/providerSelect 的 change 监听器已覆盖，无需额外处理。

### 6.3 重复 binding resolve（见 4.5）

当前可接受，本阶段不重构。

## 7. 测试复核

### 7.1 静态测试

```
python -m pytest tests/test_provider_mock_boundary_static.py -q
```

**结果**：12 passed ✅

覆盖：
- `TestMockFallbackConfig` × 2
- `TestVoiceVariantServiceCostGuard` × 4
- `TestWorkspaceBindingGuard` × 6

### 7.2 回归测试

```
python -m pytest tests/test_cancel_confirmation_static.py tests/test_workspace_restore_static.py -q
```

**结果**：65 passed ✅

### 7.3 行为测试缺失记录

**记录**：`P16-PROVIDER-OBS-TEST-001`：
当前为静态契约测试，缺少以下行为测试：
1. mock 无 binding 不 fallback minimax 的行为测试
2. variants request.provider=mock 且 fallback 显式启用时，CostGuard 使用 resolved_provider 的行为测试

**判断**：不阻塞本阶段。代码事实已通过静态测试覆盖关键契约，行为测试可作为后续 P16-PROVIDER-MOCK-CLOSE 收口后补充。

## 8. 手工验证结果

未执行（当前环境无浏览器）。

建议后续手动验证：
1. provider=mock + 无 mock binding profile → 前端阻止，显示"无法生成"警告
2. provider=minimax + 有 minimax binding → 正常显示 CostGuard 确认
3. 多版本 mock 无 binding → 前端阻止

## 9. 非阻塞观察项

| 观察项 | 说明 |
|---|---|
| `P16-PROVIDER-OBS-DUP-RESOLVE` | `render_variants()` 中存在一次重复 binding resolve（第一次用于 CostGuard，第二次在 `render_voice()` 内部），当前可接受，后续可优化 |
| `P16-PROVIDER-OBS-RESTORE-BINDING` | workspace restore 后 binding status 依赖 change 事件触发，当前 `providerSelect`/`profileSelect` change 监听器已覆盖 |
| `P16-PROVIDER-OBS-TEST-001` | 静态契约测试已覆盖关键路径，行为测试可后补 |

## 10. 复核结论

**通过 ✅**

| 条件 | 状态 |
|---|---|
| mock_fallback_provider 默认 None | ✅ |
| mock 默认不再 fallback minimax | ✅ |
| VoiceVariantService require_confirmed 使用 resolved_provider | ✅ |
| VoiceVariantService 不再以 request.provider=mock 绕过 CostGuard | ✅ |
| workspace unbound 时 handleGenerate 前置阻止 | ✅ |
| guard 在 confirm/setLoading/fetch 前 | ✅ |
| 未修改 Provider Registry / Capability Registry / CostGuardService | ✅ |
| 测试通过 | ✅（12 static + 65 regression） |
| 无真实 MiniMax 调用 | ✅ |

### RISK 修复状态

| RISK | 状态 |
|---|---|
| RISK-001：mock fallback minimax | ✅ 已修复 |
| RISK-002：VoiceVariantService CostGuard 绕过 | ✅ 已修复 |
| RISK-006：前端 unbound 阻止生成 | ✅ 已修复 |

### 当前阶段

```
P16-PROVIDER-MOCK-FIX1-CHECK：验证 mock/provider boundary fixes ✅
```

### 下一阶段

```
P16-PROVIDER-MOCK-CLOSE：Provider mock boundary 阶段收口
```
