# P16-PROVIDER-MODEL-BINDING-A0：Provider / Model / VoiceBinding 全链路审查

## 1. 阶段背景

- **分支**：`p16/real-usage-issues`
- **目标**：审查所有音色绑定、选择音色、使用音色、恢复音色配置的入口，统一 Provider / Model / ProviderVoice / VoiceBinding 的数据关系和业务规则

## 2. 当前代码事实

### 2.1 VoiceBinding 数据结构

```python
class VoiceBinding(SQLModel, table=True):
    id: str                    # 主键
    profile_id: str             # 索引
    provider: str               # 提供商
    model: str                  # 模型 ← 存在于数据层
    provider_voice_id: str      # 提供商音色 ID
    params_json: str = "{}"    # 音色参数
    priority: int = 1          # 优先级
    status: str                 # available/deprecated
    created_at: str
    updated_at: str
```

**结论**：✅ VoiceBinding 数据层已是 `profile_id + provider + model + provider_voice_id` 四元组，`model` 是一等字段。

### 2.2 ProviderVoice 数据结构

```python
class ProviderVoice(SQLModel, table=True):
    id: str
    provider: str               # 索引
    provider_voice_id: str      # 索引
    voice_type: str              # 索引
    name: str | None = None
    description: str | None = None
    language: str | None = None
    gender: str | None = None
    status: str = available     # 索引
    metadata_json: str = "{}"
    # ← 无 model 字段
```

**结论**：❌ ProviderVoice **没有 model 字段**。`provider + provider_voice_id` 唯一约束，但同一个 `provider_voice_id` 可能可跨 model 使用（需验证 MiniMax 语义）。

### 2.3 绑定创建与排重

**VoiceBindingCreate schema**：
```python
class VoiceBindingCreate(BaseModel):
    provider: str
    model: str          # ← 必填
    provider_voice_id: str
    params: dict = {}
    priority: int = 1
```

**find_duplicate_binding** 使用：
```python
.profile_id + .provider + .model + .provider_voice_id
```

**结论**：✅ 绑定创建层已把 model 当成一等字段，排重覆盖全部四字段。

**update_binding** 签名：
```python
def update_binding(session, binding, *,
    provider_voice_id: str | None = None,  # ← 可换 voice_id
    params: dict | None = None,
    priority: int | None = None,
    status: str | None = None,
    # ← 不允许换 provider/model
)
```

**结论**：❌ 更换绑定只换 `provider_voice_id`，不允许换 `provider/model`。如需换 model，需删除重建绑定。

### 2.4 Binding 解析逻辑

```python
def resolve_binding(session: Session, profile_id: str, provider: str) -> tuple[VoiceBinding, str]:
    # ← 无 model 参数，无 binding_id 参数
    binding = get_binding(session, profile_id, provider)  # 按 priority + created_at 排序取第一条
```

**结论**：❌ 解析层是 `provider` 粒度，不是 `provider + model` 粒度。如果同一 `profile + provider` 下有多个 available binding（不同 model），当前按 priority 取第一条，结果不透明。

### 2.5 执行层使用

**VoiceRenderService.render_voice()** 和 **AsyncRenderService.submit_task()**：
```python
binding, resolved_provider = resolve_binding(session, request.profile_id, provider)
# ...
plan = RenderPlan(
    provider=provider,
    model=binding.model,              # ← 使用 binding.model
    provider_voice_id=binding.provider_voice_id,
    voice_params=json.loads(binding.params_json),
)
job = VoiceJob(
    provider=provider,
    model=binding.model,
    binding_id=binding.id,           # ← VoiceJob 保存 binding_id
    profile_id=binding.profile_id,
)
```

**结论**：✅ 执行层使用 `binding.model` 和 `binding.id`。VoiceJob 保存 binding_id。

### 2.6 Provider voice 删除逻辑

```python
def deprecate_bindings_by_provider_voice(session, *, provider, provider_voice_id) -> int:
    # ← 只按 provider + provider_voice_id，忽略 model
    VoiceBinding.provider == provider
    VoiceBinding.provider_voice_id == provider_voice_id
    → 全部 deprecated
```

**结论**：❌ 如果同一 `provider + provider_voice_id` 在不同 model 下有多个 binding，删除时会全部 deprecated。ProviderVoice 无 model 字段，无法精确区分 model scope。

## 3. 数据模型定义

### 3.1 概念定义

| 概念 | 定义 |
|---|---|
| **Provider** | 模型供应商 Adapter（minimax / mock / openai / azure / elevenlabs） |
| **Model** | Provider 下的具体 TTS 模型（speech-2.8-hd / speech-2.8-turbo / gpt-4o-mini-tts） |
| **ProviderVoice** | Provider 音色资源，标识音色 ID、名称、类型；**当前无 model 字段**，同一 voice_id 可能跨 model 可用 |
| **VoiceProfile** | Voice Lab 内部人设（用户创建的音色角色） |
| **VoiceBinding** | VoiceProfile 在 `provider + model + provider_voice_id` 上的绑定记录 |
| **RenderPlan** | 最终执行计划：包含 `provider + model + provider_voice_id + voice_params + audio_params` |

### 3.2 推荐关系

```
Provider
  └── Model
        └── ProviderVoice (无 model 字段 ← 缺口)
              └── VoiceBinding ← profile_id + provider + model + provider_voice_id
                    └── VoiceProfile
```

### 3.3 当前关键缺口

| 层次 | 字段 | 状态 |
|---|---|---|
| ProviderVoice | `model` | ❌ 不存在 |
| resolve_binding | `model` 参数 | ❌ 不存在 |
| Batch longtext context | `model` | ❌ 固定为 null |
| Batch script per-line context | `model` | ❌ 不存在 |
| Workspace binding hint | `model`（从 _voiceBindMap） | ⚠️ 有值但不展示 |
| SampleStore | `model` | ⚠️ 有值（可保存） |
| ContextStore workspace | `binding_id` | ❌ 不存在 |
| Batch longtext context | `binding_id` | ❌ 不存在 |
| Batch script per-line | `binding_id` | ❌ 不存在 |

## 4. VoiceBinding 创建 / 解析 / 执行链路

### 4.1 创建链路

```
前端选择 provider + provider_voice_id
前端输入 model（或从 API 回填）
→ VoiceBindingCreate(provider, model, provider_voice_id, params, priority)
→ find_duplicate_binding(profile_id, provider, model, provider_voice_id)
→ create_binding(...)
→ VoiceBinding 记录(profile_id, provider, model, provider_voice_id, params_json, priority)
```

### 4.2 解析链路

```
前端传 profile_id + provider（无 model 参数）
→ resolve_binding(session, profile_id, provider)
  → get_binding(session, profile_id, provider) 按 priority + created_at 排序
  → 返回第一条 available binding（binding.model 已确定）
→ binding.model + binding.provider_voice_id + binding.params_json
```

**风险**：如果同一 profile+provider 有多个 model binding，用户无法指定使用哪个。

### 4.3 执行链路

```
RenderPlan(provider, model, provider_voice_id, voice_params, audio_params)
→ Provider Adapter.render_sync/async(plan)
→ VoiceJob(provider, model, binding_id, profile_id)
→ AudioAsset(provider, model)
```

## 5. ProviderVoice 与 model 关系

当前 ProviderVoice **无 model 字段**。

**需要确认的 MiniMax 语义**：
- `provider_voice_id` 是否在某 model 下创建后，只能在该 model 下使用？
- 还是同一 `provider_voice_id` 可跨 model 使用？

**当前 workaround**：
- VoiceBinding 的 `model` 字段记录了"创建此 binding 时使用的 model"
- 但 ProviderVoice 本身不知道它属于哪个 model

**风险**：如果 provider_voice_id 只能用于单一 model，则 binding 的 model 字段和 ProviderVoice 强关联；如果可跨 model，则当前设计合理。

## 6. 使用音色入口横向审查表

### 6.1 Workspace 系列

| 入口 | 前端文件 | 后端 | 选择 provider | 选择 model | 使用 profile_id | 使用 binding_id | 使用 provider_voice_id | 调用 resolve_binding | 保存 model | 恢复 model | 当前问题 | 建议 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Workspace sync 生成 | index.html | voice_render_service | ✅ | ❌ | ✅ | ✅（VoiceJob） | ✅ | ✅ | ⚠️（binding.model） | ❌ | workspace UI 无 model 下拉，hint 不展示 model | 先展示 model |
| Workspace async 生成 | index.html | async_render_service | ✅ | ❌ | ✅ | ✅（VoiceJob） | ✅ | ✅ | ⚠️（binding.model） | ❌ | 同上 | 同上 |
| Workspace stream 生成 | index.html | voice_render_service | ✅ | ❌ | ✅ | ✅（VoiceJob） | ✅ | ✅ | ⚠️（binding.model） | ❌ | 同上 | 同上 |
| Workspace variants | index.html | voice_variant_service | ✅ | ❌ | ✅ | ✅（VoiceJob） | ✅ | ✅ | ⚠️（binding.model） | ❌ | 同上 | 同上 |
| Workspace binding hint | index.html | checkBindingStatus | ✅ | ⚠️（从 _voiceBindMap） | ✅ | ❌ | ⚠️（从 _voiceBindMap） | ✅ | ⚠️ | ❌ | hint 只显示 provider+voice_id，不展示 model | 升级 hint 展示 model |
| Workspace SampleStore | sample_store.js | — | ✅ | ✅ | ✅ | ❌ | ✅ | — | ✅ | ⚠️（workspace 有；batch sample 为 null） | binding_id 未保存（schema 无此字段） | 保存 binding_id |
| ContextStore workspace | context_store.js | — | ✅ | ❌（restore 时为 null） | ✅ | ❌ | ❌ | — | ✅ | ❌ | ContextStore 无 binding_id 字段；restore 时 model 为 null（调用处未传） | 保存 binding_id + model |

### 6.2 Batch 系列

| 入口 | 前端文件 | 后端 | 选择 provider | 选择 model | 使用 profile_id | 使用 binding_id | 使用 provider_voice_id | 调用 resolve_binding | 保存 model | 恢复 model | 当前问题 | 建议 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Batch longtext submit | index.html | batch_orchestration_service | ✅ | ❌ | ✅ | ✅（per-segment VoiceJob） | ✅ | ✅ | ⚠️（binding.model） | ❌ | context 不保存 model/binding_id | context 保存 binding_id+model |
| ContextStore longtext | context_store.js | — | ✅ | ❌ | ✅ | ❌ | ❌ | — | ❌ | ❌ | 不保存 model/binding_id | 保存 binding_id+model |
| Batch script submit | index.html | batch_orchestration_service | ✅（全局） | ❌ | ✅（per-line） | ✅（per-segment VoiceJob） | ✅ | ✅（per-segment） | ⚠️（binding.model） | ❌ | per-line 无 model/binding/provider；多角色无法指定不同 provider | per-line 保存 binding_id+model |
| ContextStore script | context_store.js | — | ✅（全局） | ❌ | ✅（per-line） | ❌ | ❌ | — | ❌ | ❌ | per-line 无 model/binding/provider | per-line 保存 binding_id |

### 6.3 Voices / ProviderVoice 系列

| 入口 | 前端文件 | 后端 | 选择 provider | 选择 model | 使用 profile_id | 使用 binding_id | 使用 provider_voice_id | 调用 resolve_binding | 保存 model | 恢复 model | 当前问题 | 建议 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Voices 音色查询 | index.html | voice_catalog_service | ✅ | ❌ | — | — | — | — | — | — | 按 provider 过滤 voice list，无 model 过滤 | A0 评估是否需要 model 过滤 |
| Voices 音色试音 | index.html | voice_render_service | ✅ | ⚠️（auditionModel select） | — | — | ✅ | ✅ | ✅ | — | audition model 下拉与 binding model 可能不一致 | 统一 model 来源 |
| Voices 绑定到人设 | profile_binding.js | voice_binding_service | ✅ | ✅（model 输入） | ✅ | — | ✅ | — | ✅（binding） | — | model 由用户手输，可能与实际可用 model 不符 | 从 ProviderVoice 或 binding 推导 model |
| Voices 更换绑定 | profile_binding.js | voice_binding_service | ✅ | ❌（继承） | ✅ | ✅ | ✅（可换） | — | ✅（binding） | — | 换 voice_id 时不换 model（合理），但 UI 不展示 model | 展示 model |
| Binding management | index.html | voice_bindings API | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | 展示完整 binding 详情 | — |
| Provider voice 导入 | voice_import.js | voice_catalog_service | ✅ | ❌ | — | — | ✅ | — | — | — | 导入时无 model 字段 | 评估是否需要 |
| Provider voice 删除 | voice_delete_service | voice_delete_service | ✅ | ❌ | — | — | ✅ | — | — | — | deprecate_bindings_by_provider_voice 忽略 model，同 voice_id 多 model binding 全删 | A0 评估 |

### 6.4 其他模块

| 入口 | 前端文件 | 后端 | 选择 provider | 选择 model | 使用 profile_id | 使用 binding_id | 使用 provider_voice_id | 调用 resolve_binding | 保存 model | 恢复 model | 当前问题 | 建议 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Audition workstation | audition_records.js | voice_render_service | ✅ | ⚠️（capability tts.models） | ✅ | — | ✅ | ✅ | ✅ | — | model 来源是 capability（tts.models），不是 binding.model；可能与 binding 不一致 | 评估是否需要与 binding 统一 |
| Voice clone preview | voice_clone.js | voice_clone API | ✅ | ⚠️（用户输入 cloneModel） | — | — | ✅ | — | ⚠️ | — | model 来自用户输入框，不是 binding.model；bind 用 cloneBindModel | 统一 model 来源 |
| Voice design preview | voice_design.js | voice_design API | ✅ | ⚠️（用户输入 designBindModel） | — | — | ✅ | — | ⚠️ | — | model 来自用户输入框，不是 binding.model | 统一 model |
| Voice import | voice_import.js | voice_catalog_service | ✅ | ⚠️（用户输入 importBindModel） | ✅（bind 时） | — | ✅ | — | ✅ | — | model 来自用户输入框，不是 binding.model | 统一 model |
| History / Admin | history.js | admin API | ✅ | ✅（搜索过滤） | ✅ | ✅ | — | — | ✅ | — | VoiceJob 有 model 字段，但 history UI 不展示（仅搜索过滤可用） | 展示 model |

## 7. 字段流转表

| 字段 | 来源 | 请求 payload | VoiceBinding | RenderPlan | VoiceJob | AudioAsset | SampleStore | ContextStore | UI 展示 | 缺口 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| provider | 前端选择 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| resolved_provider | resolve_binding | — | — | ✅ | ✅ | ✅ | — | — | — | — |
| model | binding.model | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️（workspace 有） | ⚠️（workspace 有） | ⚠️（部分展示） | UI 缺展示；ContextStore/Batch 不保存 |
| provider_voice_id | binding.provider_voice_id | — | ✅ | ✅ | — | — | ✅ | ⚠️（workspace 有） | ⚠️（部分展示） | hint 不展示 voice_name |
| binding_id | binding.id | — | ✅ | — | ✅ | — | ❌ | ❌ | ❌ | SampleStore/ContextStore 不保存 |
| params_json | binding.params_json | — | ✅ | ✅（voice_params） | — | — | — | — | — | — |
| voice_name | ProviderVoice.name | — | — | — | — | — | ✅ | ⚠️（workspace 有） | ⚠️（binding hint） | hint 不展示 voice_name |
| profile_name | 前端选择 | — | — | — | — | — | ✅ | ✅ | ✅ | — |
| profile_id | 前端选择 | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — |
| audio_format | 前端选择 | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | — |
| output_format | 前端选择 | ✅ | — | ✅ | — | — | — | ✅ | — | — |
| need_subtitle | 前端选择 | ✅ | — | ✅ | — | — | — | ✅ | — | — |

## 8. 风险清单

### P16-MODEL-BINDING-RISK-001
**严重性**：中
**描述**：model 已存在于 VoiceBinding，但 workspace 主流程没有显式 model 选择。用户不知道当前使用的是哪个 model。
**当前状态**：binding.model 来自 resolve_binding 的 priority 排序，结果不透明。
**建议**：B1 先在 binding hint 中展示 model，让用户可见。

### P16-MODEL-BINDING-RISK-002
**严重性**：高
**描述**：resolve_binding 当前按 profile+provider 取第一条 available binding，如果同一 profile+provider 下有多个 model binding，结果依赖 priority，不对用户透明。
**当前状态**：用户无法指定使用哪个 model。
**建议**：B1 评估是否需要 model 下拉或 binding_id 精确指定。

### P16-MODEL-BINDING-RISK-003
**严重性**：中
**描述**：Voices tab 试音 model 与绑定 model 可能不一致；clone/design/import 的 model 输入由用户手输，缺少统一约束。
**当前状态**：audition model 来源是 capability（`tts.models`）；clone model 来源是用户输入 `cloneModel`；design/import bind model 来源是用户输入 `designBindModel`/`importBindModel`。三者来源独立，无统一约束。
**建议**：统一 model 来源，从 binding 或 ProviderVoice 推导。

### P16-MODEL-BINDING-RISK-004
**严重性**：高
**描述**：Batch script 多角色场景只表达 profile_id per line，不表达 provider/model/binding_id。同一 provider 下不同 role 可能需要不同的 model 或 binding。
**当前状态**：backend 按 provider + per-line profile_id resolve_binding，每行单独解析。
**建议**：A0 确认 per-line 是否需要 provider/model/binding_id；B1 context 保存 per-line binding_id。

### P16-MODEL-BINDING-RISK-005
**严重性**：高
**描述**：SampleStore 和 ContextStore 不保存 binding_id，恢复时无法精确还原当时使用的绑定。
**当前状态**：只保存 provider + model + voice_id，恢复时重新 resolve_binding，结果可能与当初不同。
**建议**：B1 在 SampleStore/ContextStore 中保存 binding_id。

### P16-MODEL-BINDING-RISK-006
**严重性**：高
**描述**：新增 Provider（如 OpenAI/Azure）后，如果同一 Provider 下有多个模型，现有 provider-only UI 会误导用户——用户以为选了 provider 就能用任何 model。
**当前状态**：workspace/batch 只有 provider 下拉，无 model 下拉。
**建议**：后续 Capability-UI-B1 阶段处理，当前 A0 记录为前提条件。

### P16-MODEL-BINDING-RISK-007
**严重性**：中
**描述**：provider_voice_id 是否跨 model 可用未定义。如果 MiniMax 语义是 voice_id 绑定到特定 model，则当前 VoiceBinding.model 和 ProviderVoice 无 model 字段的组合可能合法但执行失败。
**当前状态**：ProviderVoice 无 model 字段；VoiceBinding.model 记录的是 binding 创建时的 model，但 provider_voice 本身是否只属于该 model 无法验证。
**建议**：A0 阶段确认 MiniMax API 语义，必要时给 ProviderVoice 加 model 字段。

### P16-MODEL-BINDING-RISK-008
**严重性**：中
**描述**：Provider voice 删除时 deprecate_bindings_by_provider_voice 只按 provider+provider_voice_id，忽略 model 维度。如果同一 provider+provider_voice_id 在不同 model 下有多个 binding，全会被 deprecated。
**当前状态**：ProviderVoice 无 model 字段，无法精确控制删除范围。
**建议**：如果 voice_id 跨 model 通用，当前行为合理；如果 voice_id 绑定特定 model，需加 model 条件。

## 9. 后续 B1 最小实现建议

### 9.1 推荐 B1 范围（收敛）

**名称**：P16-PROVIDER-MODEL-BINDING-B1：最小 model/binding 可见性与恢复增强

**不修改**：
- VoiceBinding schema
- ProviderVoice schema
- resolve_binding 签名
- Batch script per-line payload

**纳入**：

1. **Workspace binding hint 升级**：展示 `provider + model + voice_name`（当前只展示 provider + voice_id）

2. **Workspace SampleStore 保存 binding_id**：sample_store.js 的 `normalizeSample` schema 无 binding_id 字段，需补充；model 已有

3. **Workspace ContextStore 保存 binding_id**：`buildWorkspaceRestoreContext` 当前无 binding_id；buildWorkspaceRestoreContext 调用处需补充传入 binding_id；model 在 restore 时为 null（extra.model 未传）

4. **Workspace restore 展示 binding 详情**：restore 后 UI 展示 binding 的 model 和 voice_name（当前 restore 时 model 为 null）

5. **History/Admin model 展示**：VoiceJob 已有 model 字段，history UI 不展示（仅搜索过滤用），可选小改动展示

6. **Audition model 统一**：audition model 下拉来源改为从当前 profile 的 resolved binding model 回填

### 9.2 不纳入 B1

- 不新增 model 下拉（Workspace / Batch）
- 不修改 resolve_binding 签名
- 不修改 VoiceBinding schema
- 不修改 ProviderVoice schema
- 不重构 Batch script per-line binding
- 不做 Capability UI
- 不新增 Provider
- 后置：audition model 来源统一（涉及 capability 语义，需 A0 评估后决定）

### 9.3 后续 B2 考虑

- resolve_binding 支持 model 或 binding_id 精确解析
- Batch script per-line 支持 provider/model/binding_id

### 9.4 后续 Capability-UI-B1

- Provider 下拉动态生成
- Model 下拉动态生成
- 根据 capability 禁用 streaming/subtitle/emotion/audio_format
- ProviderVoice 根据 provider+model 过滤

## 10. 不纳入范围

明确本阶段（A0）和后续 B1 不处理：

- 完整 Capability 动态 UI（P16-PROVIDER-CAPABILITY-UI-B1）
- 新增 OpenAI / Azure / ElevenLabs Provider
- Provider Registry 重构
- Capability Registry 重构
- ProviderVoice schema 加 model 字段（需先确认 MiniMax API 语义）
- Batch script per-line binding 重构（需 A0 评估后决定）
- 普通 sync T2A 后端 require_confirmed 强校验（RISK-003，后置）
- 多版本等待态（P16-VARIANTS-UX-FIX1）
- 服务端创作记录（P17-CREATION-RECORD-A0）
- 统计模块（P15-STATS-B1 / P15-SERVER-STATS-A0）

## 11. 审查结论

**Provider / Model / VoiceBinding 数据关系**：
- 数据层（VoiceBinding）完整表达 `profile_id + provider + model + provider_voice_id`
- 创建层（create_binding）已把 model 当成一等字段
- 执行层（RenderPlan / VoiceJob）已使用 model 和 binding_id
- **缺口**：解析层（resolve_binding）无 model 参数；UI 层（workspace/batch）无 model 选择和展示；恢复层（ContextStore/SampleStore）不保存 binding_id；Clone/Design/Import 的 model 来自用户输入而非 binding

**横向一致性（CHECK 修正后）**：
- workspace：UI 无 model 下拉；SampleStore schema 支持 model 但无 binding_id；ContextStore workspace 不保存 binding_id，restore 时 model 为 null
- batch：longtext/script context 不保存 model/binding_id
- voices/audition：model 来源不一（capability 或用户输入），均不经过 binding
- clone/design/import：model 来自用户输入，不使用 binding.model
- history：admin：有 model 字段但 UI 不展示

**下一阶段**：A0-CHECK 复核后进入 B1（最小可见性与恢复增强）。
