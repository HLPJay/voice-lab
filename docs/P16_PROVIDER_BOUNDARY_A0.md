# P16-PROVIDER-BOUNDARY-A0：Provider / Mock / Capability / 新大模型接入边界审查

## 1. 阶段背景

用户真实测试发现：选择 Mock 后仍然可以生成，页面提示 mock 下无可用绑定，但点击生成仍可能得到结果。

本阶段对 Provider / Mock / Capability / CostGuard / Binding / 前端适配 / 新大模型接入边界做系统性架构审查。

## 2. 用户真实发现的问题

1. 选择 Mock 后仍可能生成
2. Mock provider 无绑定时可能 fallback 到 MiniMax
3. 前端显示的 provider 与后端实际 resolved provider 可能不一致
4. Provider 能力差异未完全驱动前端 UI

## 3. 当前 Provider 架构现状

```
前端请求 provider=mock
         ↓
VoiceRenderService.render_voice()
  provider = request.provider or settings.voice_provider
  get_provider(provider)  ← 验证 provider 存在（mock 存在）
  binding, resolved_provider = resolve_binding(session, profile_id, provider)
         ↓
  如果 provider=mock 且无 mock binding
  → resolve_binding() fallback 到 mock_fallback_provider (默认 minimax)
  → 返回 (binding, "minimax")
         ↓
  provider = resolved_provider  ← 覆盖原始 request.provider
  adapter = get_provider(provider)  ← minimax adapter
  self.cost_guard.estimate_t2a_cost(provider, ...)  ← 以 minimax 计费日志
         ↓
  minimax adapter.render_sync()  ← 真实 MiniMax 调用
```

**关键问题**：request.provider="mock" 可以触发真实的 minimax 调用，CostGuard 在 binding 解析之前已放行。

## 4. 前端 Provider 适配现状

### 4.1 HTML 静态下拉

`index.html` 中所有 Provider select 静态硬编码：

```html
<option value="mock">mock（模拟）</option>
<option value="minimax">minimax（正式）</option>
```

涉及：providerSelect / batchProvider / batchScriptProvider / voiceProvider / cloneProvider / designProvider / importCloneProvider / importDesignProvider / newBindingProvider / deleteProvider

### 4.2 ?dev=1 隐藏机制

运行时 `index.html:2261-2264`：

```javascript
const showMock = new URLSearchParams(location.search).has('dev');
if (!showMock) {
  document.querySelectorAll('select option[value="mock"]').forEach(opt => opt.remove());
}
```

非 dev 用户看不到 mock 选项，但 HTML 源码中仍存在。

### 4.3 provider_capabilities.js 动态能力

`provider_capabilities.js` 通过 `/api/voice/capabilities` 动态加载能力：

- `loadProviderCapabilities()` → `window._providerCapabilities` + `window._providerCapabilitiesByName`
- `updateProviderSelectOptions(selectId)` → 从 API 能力动态重建下拉选项
- `applyWorkspaceCapability()` → TTS 能力应用到 workspace
- `applyLongtextCapability()` / `applyScriptCapability()` / `applyVoiceCloneCapability()` / `applyVoiceDesignCapability()` / `applyImportVoiceCapability()` / `applyProviderVoiceCapability()`

**现状**：
- `provider_capabilities.js` 具备完整的 capability 驱动 UI 能力
- 但如果 API 加载失败，静态 HTML 硬编码的 mock/minimax 选项仍然存在
- 能力加载失败时，所有 `apply*()` 函数默认 fallback 到 `getSelectValue(..., 'mock')`

### 4.4 Binding 状态显示

`index.html:4040-4086`：

```javascript
const matched = (bindings || []).filter(b => b.provider === provider && b.status === 'available');
if (matched.length > 0) {
  statusEl.className = 'binding-status-inline bound';  // 显示绑定状态
} else {
  statusEl.className = 'binding-status-inline unbound';  // 只显示状态，不阻止生成
}
```

**问题**：前端显示 binding 状态，但不会禁用生成按钮。用户仍可点击生成，触发 mock fallback 到 minimax。

## 5. Provider Registry 审查

### 5.1 Provider 注册

`app/providers/registry.py`：

```python
PROVIDER_REGISTRY = {
    "mock": MockSpeechProvider,
    "minimax": MiniMaxSpeechProvider,
}
```

- 只包含 mock 和 minimax
- `get_provider(name)` 只做 adapter class 查找，不做能力校验
- 新增 Provider 需要同时注册 Adapter

### 5.2 Capability 注册

`app/providers/capability_registry.py`：

```python
PROVIDER_CAPABILITY_REGISTRY = {
    "mock": MOCK_CAPABILITY,
    "minimax": build_minimax_capability(),
}
```

- 只包含 mock 和 minimax
- `/api/voice/capabilities` 返回所有已注册 Provider 的能力矩阵

## 6. Capability Registry 审查

### 6.1 Capability 模型

`app/domain/capabilities.py`：

```python
class TTSCapability(BaseModel):
    supports_streaming: bool = False
    supports_subtitle: bool = False
    supports_emotion: bool = False
    audio_formats: list[str] = ["mp3"]
    speed_range: tuple[float, float] = (0.5, 2.0)
    vol_range: tuple[float, float] = (0.1, 10.0)
    pitch_range: tuple[int, int] = (-12, 12)

class BatchCapability(BaseModel):
    supported: bool = False
    max_text_chars: int = 200000
    max_segments: int = 50

class ProviderCapability(BaseModel):
    provider: str
    enabled: bool = True
    display_name: str
    tts: TTSCapability | None = None
    batch: BatchCapability | None = None
    voice_clone: VoiceCloneCapability | None = None
    voice_design: VoiceDesignCapability | None = None
    provider_voices: ProviderVoicesCapability | None = None
```

### 6.2 Mock Capabilities

`app/providers/mock_capabilities.py`：

- `supports_streaming=True`
- `supports_subtitle=True`
- `supports_emotion=True`
- `voice_clone.supported=True`
- `voice_design.supported=True`
- `provider_voices.supported=True`

### 6.3 MiniMax Capabilities

`app/providers/minimax_capabilities.py`：同样全部为 True（能力矩阵与 mock 完全相同）

### 6.4 能力缺口

- **缺少 async / variants 显式 capability**：当前只有 TTS streaming，没有 async 独立能力字段
- **variants 是系统编排能力**，不是 Provider 原生能力，由 VoiceVariantService 内部编排多个 TTS 调用
- **缺少 clone/design 显式的 streaming/subtitle 限制**：没有表达 clone 不支持 streaming 的能力

## 7. Mock Fallback 审查

### 7.1 Fallback 逻辑

`app/repositories/voice_profile_repo.py:29-51`：

```python
def resolve_binding(session: Session, profile_id: str, provider: str) -> tuple[VoiceBinding, str]:
    profile = get_profile(session, profile_id)
    if not profile:
        raise ProfileNotFound("Voice profile not found", profile_id)

    binding = get_binding(session, profile_id, provider)
    if binding:
        return binding, provider

    settings = get_settings()
    if provider == "mock" and settings.mock_fallback_provider:
        binding = get_binding(session, profile_id, settings.mock_fallback_provider)
        if binding:
            return binding, settings.mock_fallback_provider  # ← 返回 minimax binding

    raise BindingNotFound(
        "No available voice binding found",
        f"profile={profile_id}, provider={provider}",
    )
```

### 7.2 config.py 默认值

`app/core/config.py`：

```python
mock_fallback_provider: str = "minimax"  # 默认 minimax
```

### 7.3 Fallback 风险分析

**P16-PROVIDER-RISK-001：Mock fallback 到 minimax 导致用户选择 Mock 但实际调用真实 Provider**

- request.provider="mock" → binding resolved to minimax → minimax adapter.render_sync()
- CostGuard 已对 mock 放行 → 高风险操作（voice_variants/batch/async）无需 confirm_cost
- 日志中 provider_trace_id 是 minimax trace_id，但用户操作记录中 provider="mock"
- 用户体验：以为在用 mock 测试，实际产生真实费用

**无可见性**：
- resolve_binding() 没有日志记录 fallback 事件
- 用户看不到提示"您的 mock 请求已 fallback 到 minimax"
- 没有 BINDING_NOT_FOUND 错误返回给用户

## 8. CostGuard 成本确认审查

### 8.1 CostGuard 规则

`app/services/cost_guard_service.py`：

```python
COST_PROVIDER_SET = frozenset({"minimax"})
HIGH_RISK_OPERATIONS = frozenset({
    "voice_design", "voice_clone", "provider_voice_preview",
    "provider_voice_import_verify", "binding_voice_preview",
    "voice_variants", "batch_longtext", "batch_script",
    "async_render", "stream_render",
})

def require_confirmed(self, provider: str, operation: str, confirm_cost: bool) -> None:
    if provider == "mock":  # ← mock 直接放行
        return
    if provider in COST_PROVIDER_SET and operation in HIGH_RISK_OPERATIONS and not confirm_cost:
        raise ValidationError("需要确认成本后才能执行该操作", ...)
```

### 8.2 CostGuard 调用位置

| 入口 | CostGuard 调用时机 | Provider 来源 |
|---|---|---|
| VoiceRenderService.render_voice | 在 resolve_binding 之后用 `provider`（已覆盖） | resolved_provider |
| VoiceVariantService.render_variants | **在 resolve_binding 之前** | request.provider（未覆盖） |
| voice_clone / voice_design quick preview | API 入口层调用 | request.provider |
| provider_voice_preview | API 入口层调用 | request.provider |

### 8.3 风险分析

**P16-PROVIDER-RISK-002：VoiceVariantService CostGuard 使用 request.provider 而非 resolved_provider**

```python
# voice_variant_service.py:19-20
provider = request.provider or "mock"
self.cost_guard.require_confirmed(provider, "voice_variants", request.confirm_cost)
# provider="mock" → CostGuard 直接放行
# 后续 render_voice() 内部 resolve_binding() fallback 到 minimax
```

**P16-PROVIDER-RISK-003：普通 t2a 同步渲染不在 HIGH_RISK_OPERATIONS 中**

当前 t2a 同步（`voice_render`）不要求 confirm_cost，只有 t2a stream 在 HIGH_RISK 中。这在 P16-CANCEL-FIX1 修复前端确认后属于可接受的短期策略，但后端缺少二次防护。

## 9. Binding 解析边界审查

### 9.1 解析链路

```
resolve_binding(session, profile_id, "mock")
  → get_binding(session, profile_id, "mock") → None
  → mock_fallback_provider = "minimax"
  → get_binding(session, profile_id, "minimax") → binding or None
  → if binding: return (binding, "minimax")
  → else: raise BindingNotFound
```

### 9.2 Binding 状态 UI

`index.html:4040-4086`：bindingStatus 只显示 `.bound` / `.unbound` CSS 类，不阻止生成按钮点击。

### 9.3 后端拦截

`voice_render_service.py:48-49`：

```python
binding, resolved_provider = resolve_binding(session, request.profile_id, provider)
provider = resolved_provider  # 覆盖原始 provider
```

如果 binding 不存在且无 fallback，`resolve_binding` 会抛出 `BindingNotFound`，后端会拦截。

**问题**：mock fallback 使得本应返回 BINDING_NOT_FOUND 的情况变成了成功调用 minimax。

## 10. CapabilityValidator 覆盖范围

`app/services/capability_validator.py`：

| 验证方法 | 覆盖能力 | 状态 |
|---|---|---|
| `validate_tts` | streaming / subtitle / emotion / audio_format / speed / vol / pitch / text_length | ✅ |
| `validate_batch` | batch.supported / max_text_chars / segment_strategy | ✅ |
| `validate_script` | script 能力 | ✅ |
| `validate_voice_clone` | voice_clone.supported | ✅ |
| `validate_voice_design` | voice_design.supported | ✅ |
| `validate_provider_voice_preview` | provider_voices.supported | ✅ |
| `validate_provider_voice_import` | provider_voices.remote_import | ✅ |

**缺口**：
- 缺少 `validate_async` 显式验证（async 没有独立 capability 字段）
- 缺少 `validate_variants` 显式验证（variants 是编排能力，不是 Provider 能力）
- `validate_tts` 中 `require_streaming` 为 True 但 Provider 不支持 streaming 时，默认行为是静默忽略还是报错需要确认

## 11. 生成入口横向审查表

| 入口 | 前端文件 | 后端API | request.provider 来源 | CostGuard | binding 解析 | mock fallback | 真实调用 |
|---|---|---|---|---|---|---|---|
| 单条 T2A sync | index.html | voice_render_service | request.provider | ✅ resolved_provider | ✅ | ✅ 可触发 | ✅ |
| T2A stream | index.html | voice_render_service | request.provider | ✅ resolved_provider | ✅ | ✅ 可触发 | ✅ |
| T2A async | index.html | voice_render_service | request.provider | ✅ resolved_provider | ✅ | ✅ 可触发 | ✅ |
| 多版本 variants | index.html | voice_variant_service | **request.provider** ⚠️ | ⚠️ request.provider | ✅ | ✅ 可触发 | ✅ |
| 批量长文本 | index.html | voice_batch_service | request.provider | ✅ resolved_provider | ✅ | ✅ 可触发 | ✅ |
| 批量剧本 | index.html | voice_batch_service | request.provider | ✅ resolved_provider | ✅ | ✅ 可触发 | ✅ |
| clone quick preview | voice_clone.js | voice_render_service | request.provider | ⚠️ request.provider | ✅ | ✅ 可触发 | ✅ |
| design quick preview | voice_design.js | voice_render_service | request.provider | ⚠️ request.provider | ✅ | ✅ 可触发 | ✅ |

## 12. Provider 能力缺失处理原则

**当前问题**：没有明确的"能力不支持时如何处理"原则。

建议原则：
1. **Provider 不支持某能力时，不允许静默 fallback 到其他 Provider**
2. **默认应返回 UNSUPPORTED_CAPABILITY / VALIDATION_ERROR**
3. 如要降级，必须用户显式确认

具体规则：
- `supports_streaming=false` → 禁用流式生成，不自动变成同步
- `supports_subtitle=false` → 不静默忽略字幕请求
- `supports_emotion=false` → 不悄悄丢掉 emotion 参数
- `audio_formats` → 限制前端 audioFormat 下拉
- `speed_range` / `vol_range` / `pitch_range` → 动态设置 min/max

## 13. 新 Provider 接入 Checklist

```
1. 新增 Provider Adapter (app/providers/ 目录)
2. 注册 PROVIDER_REGISTRY (app/providers/registry.py)
3. 新增 ProviderCapability (app/providers/<name>_capabilities.py)
4. 注册 capability_registry (app/providers/capability_registry.py)
5. 配置 CostGuard：是否真实计费（加入 COST_PROVIDER_SET）
6. 明确支持 sync / async / stream / variants / batch / script
7. 明确支持 subtitle / emotion / speed / vol / pitch / audio_format
8. 明确支持 voice clone / voice design / provider voices
9. 明确 voice_id 格式和验证规则
10. 明确 binding 规则
11. 前端 Provider 下拉接入 /api/voice/capabilities 动态生成
12. 前端功能入口按 capability 禁用
13. 后端所有入口调用 CapabilityValidator
14. provider + profile 无 binding 时前后端均拦截
15. 成本确认以后端 resolved_provider 为准
16. 测试 mock 不触发真实 provider
17. 测试不支持能力时返回错误
```

## 14. 风险清单

| ID | 风险 | 严重性 | 优先级 |
|---|---|---|---|
| P16-PROVIDER-RISK-001 | Mock fallback 到 minimax，用户选 mock 实际调用 minimax，无日志无提示 | 高 | P0 |
| P16-PROVIDER-RISK-002 | VoiceVariantService CostGuard 用 request.provider 而非 resolved_provider，可绕过确认 | 高 | P0 |
| P16-PROVIDER-RISK-003 | 普通 t2a sync 不在 HIGH_RISK_OPERATIONS，后端无二次成本防护 | 中 | P1 |
| P16-PROVIDER-RISK-004 | 前端 Provider 下拉硬编码，不适合新增 Provider | 中 | P1 |
| P16-PROVIDER-RISK-005 | provider_capabilities.js API 加载失败时降级为静态 mock/minimax | 中 | P1 |
| P16-PROVIDER-RISK-006 | Binding 状态显示但不阻止生成，用户可触发 mock fallback | 中 | P1 |
| P16-PROVIDER-RISK-007 | 缺少 async / variants 显式 capability | 低 | P2 |
| P16-PROVIDER-RISK-008 | 新增 Provider 需要多处注册，缺少统一 checklist | 低 | P2 |

## 15. 后续修复阶段建议

### P16-PROVIDER-MOCK-FIX1（高优先级 P0/P1）

纳入：
1. 禁用 `mock_fallback_provider` 默认 minimax，改为 None 或独立 mock binding
2. mock 无 binding 时返回 BINDING_NOT_FOUND，不触发 fallback
3. 后端成本确认以 resolved_provider 为准（修复 VoiceVariantService 等入口）
4. binding 解析时记录 fallback 日志，供审计
5. 增加 mock 不触发 minimax 真实调用的集成测试

### P16-PROVIDER-CAPABILITY-UI-B1（中优先级 P1）

纳入：
1. provider_capabilities.js API 加载失败时禁用生成按钮而非降级到 mock
2. Binding 状态 unbound 时禁用生成按钮
3. 前端 Provider 下拉由 capabilities API 动态生成（当前已具备条件，缺健壮性）
4. 不支持的能力在前端隐藏/禁用

### P16-PROVIDER-RISK-003 补充（低优先级 P2）

纳入：
1. 评估是否将 t2a sync 加入 HIGH_RISK_OPERATIONS
2. 或在 VoiceRenderService 层面增加 resolve_provider 后二次 CostGuard 检查

## 16. 审查结论

**P16-PROVIDER-BOUNDARY-A0 审查完成。**

核心发现：
1. **Mock fallback 风险 P0**：用户选 mock → 后端 fallback minimax → CostGuard 绕过 → 真实 MiniMax 调用
2. **VoiceVariantService CostGuard 绕过 P0**：request.provider="mock" 直接放行，后续实际 minimax 调用无确认
3. **前端下拉硬编码 P1**：新增 Provider 需要多处修改
4. **Capability 模型已有雏形**，但 API 失败时降级策略不健壮
5. **Binding 状态显示不阻止生成**：用户可触发 mock fallback 无感知

本阶段只做审查，未修改功能代码。
