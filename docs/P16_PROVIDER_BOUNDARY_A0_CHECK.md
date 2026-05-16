# P16-PROVIDER-BOUNDARY-A0-CHECK：Provider 边界审查复核

## 1. 阶段背景

复核 P16-PROVIDER-BOUNDARY-A0 审查文档（提交 `0de1f3a`）是否完全符合当前代码事实。

## 2. 远端提交核验

```
0de1f3a docs: audit provider boundary and mock semantics (P16-PROVIDER-BOUNDARY-A0)
```

## 3. Mock fallback 复核

### 代码事实

`app/core/config.py`：`mock_fallback_provider: str | None = "minimax"`

`app/repositories/voice_profile_repo.py:29-51`：
- `resolve_binding()` 先查 `get_binding(session, profile_id, provider="mock")`
- 无 binding 时查 `get_binding(session, profile_id, settings.mock_fallback_provider)`
- 若找到 binding，返回 `(binding, resolved_provider="minimax")`
- 若找不到，抛出 `BindingNotFound`

### 复核结论

**P16-PROVIDER-RISK-001 表述准确** ✅

用户选择 mock，但 `resolve_binding()` fallback 到 minimax binding，返回 `resolved_provider="minimax"`，实际调用 minimax adapter。

## 4. request.provider / resolved_provider 复核

### VoiceRenderService 代码事实

`app/services/voice_render_service.py:46-49`：

```python
provider = request.provider or settings.voice_provider
get_provider(provider)  # 验证 provider 存在
binding, resolved_provider = resolve_binding(session, request.profile_id, provider)
provider = resolved_provider  # ← 覆盖原始 request.provider
adapter = get_provider(provider)  # minimax adapter
```

`voice_render_service.py` 中 CostGuard 调用：
- **无 `require_confirmed()` 调用**
- 只有 `estimate_t2a_cost(provider, plan.model, request.text)`（line 95）—— 这是成本估算，不是成本校验

**A0 文档误述**：第 11 节横向审查表中，`voice_render_service` 行写的是 `✅ resolved_provider`（CostGuard 列），这是错误的。`VoiceRenderService.render_voice()` 实际不做 `require_confirmed()` 强制校验，只做成本估算。

### VoiceVariantService 代码事实

`app/services/voice_variant_service.py:19-20`：

```python
provider = request.provider or "mock"  # ← 使用 request.provider
self.cost_guard.require_confirmed(provider, "voice_variants", request.confirm_cost)
# provider="mock" → CostGuard 直接放行
```

然后内部调用 `render_service.render_voice()`，后者内部 `resolve_binding()` 可能 fallback 到 minimax。

**P16-PROVIDER-RISK-002 表述准确** ✅

### 复核结论

- `VoiceRenderService` 使用 `resolved_provider` 做真实调用 ✅
- `VoiceRenderService` 不调用 `require_confirmed()`，只有 `estimate_t2a_cost`（估算，不是强制校验）⚠️ A0 文档需修正
- `VoiceVariantService` 在 `resolve_binding()` 之前用 `request.provider` 调 `require_confirmed()`，可绕过 ✅ P16-PROVIDER-RISK-002 成立

## 5. CostGuard 复核

### 代码事实

`app/services/cost_guard_service.py:107-121`：

```python
def require_confirmed(self, provider: str, operation: str, confirm_cost: bool) -> None:
    if provider == "mock":  # ← mock 直接放行
        return
    if provider in COST_PROVIDER_SET and operation in HIGH_RISK_OPERATIONS and not confirm_cost:
        raise ValidationError(...)
```

`COST_PROVIDER_SET = frozenset({"minimax"})`
`HIGH_RISK_OPERATIONS` 包含 `voice_variants / async_render / stream_render / batch_longtext / batch_script`，**不包含普通 t2a sync**。

### 复核结论

- CostGuard 对 `provider=="mock"` 直接 return ✅
- **普通 t2a sync 不在 HIGH_RISK_OPERATIONS**，后端无 `require_confirmed` 强制校验 ✅ P16-PROVIDER-RISK-003 成立

## 6. 前端 Provider UI 复核

### 代码事实

`app/static/index.html`：所有 Provider select 静态硬编码 `mock/minimax`。

运行时 `index.html:2261-2264`：`?dev=1` 隐藏 mock 选项。

`app/static/js/provider_capabilities.js`：`loadProviderCapabilities()` 从 `/api/voice/capabilities` 动态加载能力，API 失败时 `getSelectValue(..., 'mock')` 作为默认值。

`index.html:4040-4086`：bindingStatus 显示 `.bound` / `.unbound`，但生成按钮不禁用。

### 复核结论

- 前端 Provider 下拉硬编码 ✅（A0 结论准确）
- `?dev=1` 隐藏 mock ✅
- API 失败时 fallback 到 mock ✅
- binding unbound 不阻止生成 ✅

## 7. Capability 模型复核

### 代码事实

`app/domain/capabilities.py`：`TTSCapability` 含 `supports_streaming/subtitle/emotion/audio_formats/speed_range/vol_range/pitch_range`；`BatchCapability` / `VoiceCloneCapability` / `VoiceDesignCapability` / `ProviderVoicesCapability` 均存在。

`app/services/capability_validator.py`：`validate_tts/validate_batch/validate_script/validate_voice_clone/validate_voice_design/validate_provider_voice_preview` 均存在。

缺少 `validate_async` / `validate_variants` 显式验证。

### 复核结论

- Capability 模型完整 ✅
- async / variants 无显式 capability 字段 ✅（variants 是编排能力，不是 Provider 原生能力）

## 8. 生成入口横向审查复核

### A0 文档修正

第 11 节表格中 `voice_render_service` 行的 CostGuard 列应修正为：

| 入口 | CostGuard 调用 | Provider 来源 | 备注 |
|---|---|---|---|
| 单条 T2A sync | `estimate_t2a_cost()` ⚠️ 非 require_confirmed | resolved_provider | 不在 HIGH_RISK，后端无强制校验 |

原 A0 文档写 `✅ resolved_provider`（CostGuard 列），应修正为：
- 真实调用：`✅ resolved_provider`（adapter 使用 resolved_provider）
- 成本估算：`✅ resolved_provider`（`estimate_t2a_cost(provider, ...)`）
- 强制校验：`❌ 无 require_confirmed`（普通 sync 不在 HIGH_RISK）

### 复核结论

- `VoiceRenderService` 表述需修正（A0 误写成有 CostGuard 链路）
- `VoiceVariantService` 风险准确（P16-PROVIDER-RISK-002 成立）
- clone/design quick preview 在 API 入口层以 `request.provider` 调用 `require_confirmed` ⚠️ 有绕过风险

## 9. A0 文档修正点

需修正 1 处：

**第 11 节表格 - `voice_render_service` 行**

原文：
```
VoiceRenderService.render_voice | voice_render_service | request.provider | ✅ resolved_provider | ✅ | ✅ 可触发 | ✅
```

修正为：
```
VoiceRenderService.render_voice | voice_render_service | request.provider | ⚠️ estimate_t2a_cost (非 require_confirmed) | ✅ | ✅ 可触发 | ✅
```

理由：`VoiceRenderService.render_voice()` 不调用 `require_confirmed()`，只调用 `estimate_t2a_cost(provider, plan.model, text)` 做成本估算。普通 t2a sync 不在 HIGH_RISK_OPERATIONS 中，后端无强制成本确认。

## 10. 后续 FIX1 范围

**P16-PROVIDER-MOCK-FIX1 建议范围（高优先级 P0/P1）：**

1. 禁用 `mock_fallback_provider` 默认 minimax，改为 `None`
2. mock 无 binding 时返回 `BindingNotFound`，不触发 fallback
3. **修复 VoiceVariantService**：在 `resolve_binding()` 之后才调 `CostGuard.require_confirmed()`，以 `resolved_provider` 为准
4. binding unbound 时前端阻止生成按钮
5. 增加测试：mock 不得触发 minimax 真实调用

**明确不纳入 FIX1：**
- 完整 Capability 动态 UI 改造（→ P16-PROVIDER-CAPABILITY-UI-B1）
- 新增 Provider（需先完成 FIX1）
- 服务端创作记录
- 统计模块

## 11. 复核结论

**通过 — A0 审查结论总体准确，发现 1 处表述需修正**

- P16-PROVIDER-RISK-001 ✅ 准确
- P16-PROVIDER-RISK-002 ✅ 准确
- P16-PROVIDER-RISK-003 ✅ 准确
- 前端 Provider 硬编码 ✅ 准确
- Capability 模型 ✅ 准确

需修正 1 处：`VoiceRenderService` 的 CostGuard 表述（调用的是 `estimate_t2a_cost` 不是 `require_confirmed`）。

无新增阻塞问题。
