# Voice Lab 架构级 Guard 审计报告

## 1. 审计目标

系统排查所有 Provider 调用路径，识别 Cost Guard 和 Resource Guard 覆盖盲区，建立 P0/P1/P2 分级整改计划。

---

## 2. Guard 矩阵

> 📅 **文档更新日期**：2026-05-12（P0 Cost Guard 统一入口整改第一批完成后）

### 2.0 统一入口（CostGuardService.require_confirmed）

所有高风险操作的 Cost Guard 统一通过 `CostGuardService.require_confirmed(provider, operation, confirm_cost)` 校验：

```python
# Providers that incur real costs
COST_PROVIDER_SET = frozenset({"minimax"})

# High-risk operations that always require explicit cost confirmation
HIGH_RISK_OPERATIONS = frozenset({
    "voice_design", "voice_clone", "provider_voice_preview",
    "provider_voice_import_verify", "binding_voice_preview",
    "voice_variants", "batch_longtext", "batch_script",
    "async_render", "stream_render",
})
```

规则：
- `provider == "mock"`：永远不要求 confirm_cost
- `provider in COST_PROVIDER_SET` 且 `operation in HIGH_RISK_OPERATIONS` 且 `confirm_cost != True`：抛 `ValidationError` (422)

每个 Provider 调用路径按以下字段评估：

| 字段 | 说明 |
|------|------|
| confirm_cost 入口 | 请求/调用入口是否支持 `confirm_cost` 字段 |
| confirm_cost 校验 | 入口是否校验 `confirm_cost`（针对 minimax/mimo 等付费 provider） |
| CostGuard 日志 | 是否记录 billing_chars / estimated_cost |
| usage_characters 回填 | ProviderCallLog 是否回填 usage_characters |
| provider_voice 状态校验 | 调用前是否校验 ProviderVoice.status == available |
| ResourceGuard | 是否有并发/资源限制 |

### 2.1 已 Guarded（Cost Guard 覆盖）

| 路径 | confirm_cost 入口 | 入口校验 | CostGuard 日志 | usage 回填 | voice 校验 |
|------|-----------------|---------|----------------|-----------|-----------|
| `voice_render_service.render_voice` (T2A) | ✅ `VoiceRenderRequest` | ✅ `CostGuardService` | ✅ | ✅ | ✅ |
| `provider_voice_preview_service.preview` (直接试听) | ✅ `ProviderVoicePreviewRequest` | ✅ `CostGuardService` | ❌ | ❌ | ✅ |
| `voice_design_service.design_voice` | ✅ `VoiceDesignRequest` | ✅ `CostGuardService` | ❌ | ❌ | N/A |
| `voice_clone_service.clone_voice` | ✅ `VoiceCloneRequest` | ✅ `CostGuardService` | ❌ | ❌ | N/A |
| `batch_orchestration_service.submit_longtext` | ✅ `LongtextBatchRequest` | ✅ `CostGuardService` | ✅ | ❌ | ✅ |
| `batch_orchestration_service.submit_script` | ✅ `ScriptBatchRequest` | ✅ `CostGuardService` | ✅ | ❌ | ✅ |
| `stream_render_service.render_stream` (WebSocket) | ✅ `StreamRenderRequest` | ✅ `CostGuardService` | ❌ | ❌ | ✅ |
| `async_render_service.submit_task` | ✅ `AsyncRenderRequest` | ✅ `CostGuardService` | ❌ | ❌ | ✅ |
| `voice_variant_service.render_variants` | ✅ `VoiceVariantRenderRequest` | ✅ `CostGuardService` | ❌ | ❌ | ✅ |
| `provider_voice_import_service.import_voice(verify=True)` | ✅ `ProviderVoiceImportRequest` | ✅ `CostGuardService` | ❌ | ❌ | ✅ |
| `voice_preview_service.preview` (binding-based) | ✅ `ProviderVoicePreviewRequest` | ✅ `CostGuardService` | ❌ | ❌ | ✅ |

### 2.2 未 Guarded（Cost Guard 盲区）— 第一批整改后全部 P0 已修复

| 路径 | 问题根因 | 风险等级 | 状态 |
|------|---------|---------|------|
| `voice_variant_service.render_variants` 循环调用 `render_voice` 最多 5 次 | `VoiceVariantRenderRequest` 无 confirm_cost | **P0** | ✅ 已修复：增加 `confirm_cost` 字段 + guard |
| `async_render_service` 路径 | `AsyncRenderRequest` 无 `confirm_cost` 字段 | **P0** | ✅ 已修复：增加 `confirm_cost` 字段 + guard |
| `StreamRenderRequest`（WebSocket） | 无 `confirm_cost` 字段 | **P0** | ✅ 已修复：增加 `confirm_cost` 字段 + guard |
| `VoiceVariantRenderRequest` | 无 `confirm_cost` 字段 | **P0** | ✅ 已修复 |
| `provider_voice_import_service.import_voice(verify=True)` | 调用路径问题 + 无 confirm_cost | **P0** | ✅ 已修复：`ValidationError` 穿透 + `confirm_cost` 传入 preview |

### 2.3 已 Guarded（ProviderVoice 状态校验覆盖）

| 路径 | voice 状态校验 |
|------|--------------|
| `voice_render_service.render_voice` | ✅ `validate_binding_provider_voice` |
| `provider_voice_preview_service.preview` | ✅ `validate_provider_voice_available` |
| `batch_orchestration_service` segment 级生成 | ✅ 每 segment 生成前校验 |
| `voice_delete_service.delete_voice` | ✅ 调用 `validate_provider_voice_available` |
| `provider_voice_preview_service.preview` | ✅ 同上 |

### 2.4 未 Guarded（ProviderVoice 状态校验盲区）

| 路径 | 问题根因 | 风险等级 |
|------|---------|---------|
| `voice_design_service.design_voice` | 不依赖已有 `provider_voice_id`，直接创建远端音色，无状态校验 | **P1** |
| `voice_clone_service.clone_voice` | 同上，直接创建远端音色 | **P1** |
| `provider_voice_import_service.import_voice(verify=False)` | skip verify 时直接 upsert，不校验远端 voice 是否真实存在 | **P1** |
| `voice_catalog_service.refresh=True` | 调用 `adapter.list_voices()` 拉取远端列表，无状态校验，但也不触发生成 | **P1** |

### 2.5 Resource Guard 现状

**完全缺失。** 当前系统无任何并发控制、流量限制、预算预占机制。

---

## 3. P0 必修（Cost Guard V1 补漏）

> ✅ **第一批整改完成（2026-05-12）** — 以下所有 P0 均已修复。

### P0-1：`VoiceVariantRenderRequest` 无 `confirm_cost` ✅ 已修复

**文件**: `app/domain/schemas.py`、`app/services/voice_variant_service.py`
**修复**: `VoiceVariantRenderRequest` 增加 `confirm_cost: bool = False`；`voice_variant_service.render_variants` 入口统一校验 `CostGuardService.require_confirmed(provider, "voice_variants", confirm_cost)`。

### P0-2：`AsyncRenderRequest` 无 `confirm_cost` ✅ 已修复

**文件**: `app/domain/schemas.py`、`app/services/async_render_service.py`
**修复**: `AsyncRenderRequest` 增加 `confirm_cost: bool = False`；`async_render_service.submit_task` 入口调用 `CostGuardService.require_confirmed(provider, "async_render", confirm_cost)`。

### P0-3：`StreamRenderRequest` 无 `confirm_cost` ✅ 已修复

**文件**: `app/domain/schemas.py`、`app/services/stream_render_service.py`
**修复**: `StreamRenderRequest` 增加 `confirm_cost: bool = False`；`stream_render_service.render_stream` 入口调用 `CostGuardService.require_confirmed(provider, "stream_render", confirm_cost)`。

### P0-4：`provider_voice_import_service.import_voice(verify=True)` 绕过 Cost Guard ✅ 已修复

**文件**: `app/domain/schemas.py`、`app/services/provider_voice_import_service.py`
**修复**:
1. `ProviderVoiceImportRequest` 增加 `confirm_cost: bool = False`
2. `provider_voice_import_service` 调用 `CostGuardService.require_confirmed(provider, "provider_voice_import_verify", confirm_cost)` 后再构造 preview 请求
3. `confirm_cost` 透传给 `ProviderVoicePreviewRequest`
4. `except ValidationError: raise` 确保 ValidationError 穿透，不被转换为 ProviderError (400)

### P0-5：`voice_preview_service.py`（binding-based）无 Cost Guard ✅ 已修复

**文件**: `app/services/voice_preview_service.py`
**修复**: `VoicePreviewService.preview` 调用 `CostGuardService.require_confirmed(request.provider, "binding_voice_preview", request.confirm_cost)`。

---

## 4. P1 优化（下一迭代）

### P1-1：`voice_design_service` / `voice_clone_service` 无 usage 回填

当前 `design_voice` 和 `clone_voice` 成功后将 `update_call_log` 托付给 adapter 内部，但未显式调用。
建议：显式在 service 层调用 `adapter.update_call_log(job_id=..., usage_characters=..., provider_trace_id=...)`。

### P1-2：`voice_catalog_service` refresh 调用远端 list_voices

当前 `refresh=True` 调用 `adapter.list_voices()` 无并发控制。
建议：接入 Resource Guard 控制 `list_voices` 并发。

### P1-3：`provider_voice_import_service` verify=False 直接 upsert

跳过 verify 时直接 upsert provider_voice，不检查远端 voice 是否真实存在。
建议：verify=False 时记录警告日志；verify=True 时（已修复）保持校验。

### P1-4：`stream_render_service` 无 usage 回填

`render_stream` 成功后未回填 `usage_characters`。
建议：流式完成后累加 usage 并调用 `update_call_log`。

### P1-5：`async_render_service` 无 usage 回填

异步任务回调更新时未补录 `usage_characters`。
建议：任务完成时回填。

---

## 5. P2 规划（中长期）

### P2-1：Resource Guard 第一版

当前完全无并发控制。参见 `docs/NEXT_ACTION_PLAN.md` 阶段 2。

### P2-2：`voice_variant_service` 循环无单独 guard

`render_variants` 内部循环 5 次 `render_voice`，每次独立拿到 `VoiceRenderRequest`。虽然 `VoiceRenderRequest` 有 `confirm_cost`，但 `VoiceVariantRenderRequest` 无统一拦截，批量生成多声线场景可绕过单次生成的确认逻辑。

### P2-3：`voice_delete_service` 缺少资源保护

删除音色是高风险操作，当前无 ResourceGuard 层面的保护（删除操作串行化）。

### P2-4：ProviderCallLog usage 回填覆盖不全

当前只有 `render_sync` 成功路径回填了 `usage_characters`；`stream_render`、`async_render`、`design_voice`、`clone_voice` 均缺失。

---

## 6. 隐式 Provider 调用（不易察觉）

| 调用路径 | 触发条件 | 风险 |
|---------|---------|------|
| `preview_service.preview()` → `adapter.render_sync()` | API `/api/voice/preview` 或 import verify | 真实费用，无 confirm_cost |
| `voice_catalog_service` refresh=True → `adapter.list_voices()` | 用户刷新音色列表 | 拉取远端音色列表，无并发控制 |
| `batch_orchestration_service` segment 循环 | 批量长文本生成，每段一次 `render_sync` | 费用放大，无统一 confirm_cost |
| `voice_variant_service.render_variants` 循环 | 多声线生成，最多 5 次 `render_voice` | 费用放大，无统一 confirm_cost |

---

## 7. 架构依赖关系

```
VoiceRenderRequest.confirm_cost
├── ✅ voice_render_service.render_voice
├── ✅ batch_orchestration_service (longtext/script submit)
├── ⚠️ voice_variant_service.render_variants (入口无字段，下层传 confirm_cost=False)
└── ❌ async_render_service (AsyncRenderRequest 无此字段)

ProviderVoicePreviewRequest.confirm_cost
├── ✅ provider_voice_preview_service.preview (直接试听)
└── ✅ provider_voice_import_service.import_voice(verify=True) → 透传 confirm_cost

StreamRenderRequest / AsyncRenderRequest
└── ✅ 两者均有 confirm_cost 字段

VoiceDesignRequest / VoiceCloneRequest
└── ✅ 有 confirm_cost 字段，service 层有 guard

VoiceVariantRenderRequest
└── ✅ 有 confirm_cost 字段，service 层统一 guard
```

---

## 8. 整改计划（四批次）

### 第一批次 ✅：补齐 P0 Schema 漏洞

1. ✅ `VoiceVariantRenderRequest` 增加 `confirm_cost: bool = False`
2. ✅ `AsyncRenderRequest` 增加 `confirm_cost: bool = False`
3. ✅ `StreamRenderRequest` 增加 `confirm_cost: bool = False`
4. ✅ `ProviderVoiceImportRequest` 增加 `confirm_cost: bool = False`

### 第二批次 ✅：补齐 P0 Service 层校验

1. ✅ `voice_variant_service.render_variants`：入口 `require_confirmed("voice_variants")`
2. ✅ `async_render_service.submit_task`：入口 `require_confirmed("async_render")`
3. ✅ `stream_render_service.render_stream`：入口 `require_confirmed("stream_render")`
4. ✅ `provider_voice_import_service.import_voice`：guard + `ValidationError` 穿透

### 第三批次：补齐 P1 Service 层优化（下一迭代）

1. `voice_design_service.design_voice`：显式 `update_call_log` 回填
2. `voice_clone_service.clone_voice`：显式 `update_call_log` 回填
3. `stream_render_service.render_stream`：成功后 `update_call_log`
4. `voice_catalog_service`：refresh 时增加 ResourceGuard 占位（未来接入）

### 第四批次：Resource Guard 第一版（与前三批不并行）

参见 `docs/NEXT_ACTION_PLAN.md` 阶段 2。

---

## 9. 测试覆盖（本次新增）

| 测试 | 覆盖 |
|------|------|
| `test_minimax_high_risk_without_confirm_cost_rejected` | P0-1~P0-5 统一入口 |
| `test_minimax_import_verify_without_confirm_cost_rejected` | P0-4 |
| `test_minimax_variants_without_confirm_cost_rejected` | P0-1 |
| `test_minimax_async_without_confirm_cost_rejected` | P0-2 |
| `test_stream_render_request_accepts_confirm_cost` | P0-3 |

---

## 10. 总结

| 等级 | 数量 | 状态 |
|------|------|------|
| P0 必修 | 5 | ✅ 全部修复（2026-05-12） |
| P1 优化 | 5 | 未修复 |
| P2 规划 | 4 | 未开始 |

**本次整改成果**：Cost Guard 从"点状判断"升级为"统一操作策略入口" `CostGuardService.require_confirmed()`，覆盖全部 10 个高风险操作路径。

**仍有风险**：Resource Guard 完全缺失；usage_characters 回填不完整；Provider 抽象仍偏 MiniMax voice_id 模式。

**下一步**：Resource Guard 第一版（P2-1），或 P1 优化（usage 回填）
