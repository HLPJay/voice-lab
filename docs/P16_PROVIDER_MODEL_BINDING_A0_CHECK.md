# P16-PROVIDER-MODEL-BINDING-A0-CHECK：Provider / Model / VoiceBinding 全链路审查复核

## 1. 阶段背景

- **复核 commit**：`77e4c67` ("docs: audit provider model binding full chain")
- **分支**：`p16/real-usage-issues`
- **目标**：验证 A0 结论与代码事实是否一致，修正不准确项

## 2. 远端提交核验

修改文件仅包含：

```
docs/P16_PROVIDER_MODEL_BINDING_A0.md
docs/PROJECT_HEALTH_CHECK.md
docs/agent/NEXT_TASKS.md
```

未越界修改 `app/*`、`tests/*` ✅

## 3. 代码事实复核

### 3.1 VoiceBinding schema ✅

确认 `VoiceBinding` 包含 `id / profile_id / provider / model / provider_voice_id / params_json / priority / status / created_at / updated_at`。A0 结论准确。

### 3.2 ProviderVoice schema ✅

确认 `ProviderVoice` 无 `model` 字段（仅 `provider / provider_voice_id / voice_type / name / status / metadata_json`）。A0 结论准确。

### 3.3 VoiceBinding 创建与排重 ✅

`VoiceBindingCreate` 包含 `model`；`find_duplicate_binding` 按四字段排重；`update_binding` 不允许修改 `provider/model`。A0 结论准确。

### 3.4 resolve_binding ✅

确认签名 `resolve_binding(session, profile_id, provider)` 无 `model`/`binding_id` 参数，按 `priority + created_at` 排序。A0 结论准确。

### 3.5 执行层 ✅

确认 `VoiceRenderService` / `AsyncRenderService` 使用 `binding.model` 和 `binding.id`；`VoiceJob` 保存 `model` 和 `binding_id`；`AudioAsset` 保存 `model`。A0 结论准确。

### 3.6 Provider voice 删除 ⚠️

确认 `deprecate_bindings_by_provider_voice` 只按 `provider + provider_voice_id`。A0 结论基本准确，但需注意：如果同一 `provider_voice_id` 在不同 `model` 下的 binding 全被 deprecated，这是当前设计的实际行为，不一定是 bug。

## 4. 横向入口表复核

### 4.1 修正项 1：SampleStore model 覆盖不一致

**A0 表述**："SampleStore 有 model"

**实际情况**：`normalizeSample` schema 确实支持 `model / voice_id / voice_name` 字段，但：
- `binding_id` 不在 SampleStore schema 中（从未保存）
- workspace sample 通过 `buildWorkspaceSampleContext` 从 `_voiceBindMap` 推导 model
- batch sample 在 `batch_longtext.js` 和 `batch_script.js` 中均保存 `model: null`

**修正**：SampleStore schema 支持 model，但不同写入入口覆盖不一致；binding_id 未被保存。

### 4.2 修正项 2：ContextStore workspace 不保存 model/binding_id

**A0 表述**："workspace context 保存 model" / "buildWorkspaceSampleContext 有 model"

**实际情况**：
- `buildWorkspaceSampleContext` 推导出 `ctx.model = b.model`，但这只是**写入 SampleStore 用的 sample context**，不是 ContextStore 的 restore context
- `buildWorkspaceRestoreContext`（用于 ContextStore）调用时只传 `{job_id, asset_id}`，`model: extra.model || null` = `null`
- **ContextStore workspace 不保存 binding_id**（`context_store.js` 中无 `binding_id` 字段）

**修正**：ContextStore workspace 不保存 binding_id；restore 时 model 为 null（从 extra 传入，但调用处未传 model）。

### 4.3 修正项 3：ContextStore longtext/script model 为 null

**A0 表述**："longtext context 不保存 model/binding_id"

**实际情况**：确认 `batch_longtext.js` 和 `batch_script.js` 均保存 `model: null`，无 binding_id。

**结论**：A0 表述准确。

### 4.4 修正项 4：History/Admin 不展示 model

**A0 表述**："History/Admin 已展示 model（VoiceJob 字段）✅"

**实际情况**：`VoiceJob` 确实有 `model` 字段，`history.js` 在搜索过滤时使用 `job.model`（第 211 行），但 `historyJobCardHtml` 中**不渲染 model 字段**。

**修正**：History/Admin 有 model 字段但 UI 不展示；History 搜索可命中 model。

### 4.5 修正项 5：Clone / Design / Import 不使用 binding.model

**A0 表述**："clone/design/import 使用 binding.model"

**实际情况**：
- `voice_clone.js`：preview payload 中 `model` 来自 `document.getElementById('cloneModel')`（用户输入）；绑定时 `bindModel` 来自 `cloneBindModel` 输入框
- `voice_design.js`：绑定时 `model` 来自 `document.getElementById('designBindModel')`（用户输入）
- `voice_import.js`：绑定时 `bindModel` 来自 `importBindModel`（用户输入）

**修正**：Clone / Design / Import 的 model 来源是用户输入框，不是 binding.model。

### 4.6 修正项 6：Audition model 来源

**A0 表述**："audition model 与 binding model 可能不一致"

**实际情况**：`provider_capabilities.js` 行 291：`updateSelectOptions('auditionModel', tts.models || ['speech-2.8-hd'])`，audition model 下拉来自 capability 的 `tts.models`，不是来自 binding。

**修正**：Audition model 来源是 capability 系统，不是 binding.model。RISK-003 成立。

### 4.7 修正项 7：Audition workstation 文件不存在

**A0 表述**："audition_workstation.js"

**实际情况**：该文件不存在；audition 功能在 `audition_records.js`。audition_records.js 的 normalizeAuditionRecord 包含 model 字段（第 74 行），但这是保存已有 audition 记录，不是 audition 本身的 model 来源。

## 5. 字段流转表复核

主要修正：

- **SampleStore.model**：schema 支持，但 binding_id 不保存；batch sample model 为 null
- **ContextStore.binding_id**：不保存（context_store.js 无此字段）
- **ContextStore.model**：workspace restore 时为 null（调用处未传）
- **History model UI 展示**：VoiceJob 有字段，前端不展示（仅搜索可用）

## 6. 风险清单复核

| RISK | 复核结论 | 修正 |
|---|---|---|
| RISK-001 | ✅ 成立 | — |
| RISK-002 | ✅ 成立 | — |
| RISK-003 | ✅ 成立，需修正描述 | Audition model 来自 capability，不来自 binding；clone/design/import model 来自用户输入 |
| RISK-004 | ✅ 成立 | batch script per-line 确实无 provider/model/binding_id |
| RISK-005 | ✅ 成立，需加强 | ContextStore 确实不保存 binding_id；workspace restore 时 model 为 null |
| RISK-006 | ✅ 成立 | — |
| RISK-007 | ✅ 成立 | — |
| RISK-008 | ✅ 成立（当前行为描述准确） | 但需注意：这可能是设计意图，不是 bug |

## 7. B1 最小实现范围复核

### A0 推荐 B1 范围

```
1. workspace binding hint 升级展示 model
2. SampleStore/ContextStore 保存 binding_id + model
3. restore 展示 binding 详情
4. history/admin 展示 model
5. audition model 来源统一
```

### CHECK 评估

**范围过大**，建议修正为：

**必须纳入（B1 核心）**：
1. workspace binding hint 升级展示 `provider + model + voice_name`（binding hint 当前只显示 `provider + voice_id`）
2. `buildWorkspaceRestoreContext` 补充 `binding_id` 和 `model`（通过 `_voiceBindMap` 查找当前 binding）
3. ContextStore workspace 保存 `binding_id`（当前完全没有）
4. SampleStore workspace sample 已有 model（✅），确认 batch sample model 为 null 是否可接受

**可选纳入**：
5. history/admin 展示 model（VoiceJob 字段已存在，前端改动小）

**后置（B2 或后续）**：
- audition model 来源统一（涉及 capability 和 binding 两个来源的语义统一）
- Batch script per-line binding_id（涉及 payload 结构变更）
- Batch longtext context model（当前 null，需要评估是否值得改）

### CHECK 建议 B1 更加收敛

```
P16-PROVIDER-MODEL-BINDING-B1 范围（修正后）：
1. workspace binding hint 展示 model（✅ 有 _voiceBindMap 数据）
2. buildWorkspaceRestoreContext 保存 binding_id（✅ 缺口明确）
3. ContextStore workspace 保存 binding_id（✅ 无此字段）
4. batch sample model 为 null 是否接受（需决策）
5. history/admin 展示 model（可选，前端小改动）
```

## 8. 修正项汇总

| # | 位置 | A0 原文 | 修正后 |
|---|---|---|---|
| 1 | 横向表 / SampleStore | "SampleStore 有 model" | "SampleStore schema 支持 model/voice_id/voice_name，但 binding_id 不保存；batch sample model 为 null" |
| 2 | 横向表 / ContextStore workspace | "workspace context 保存 model/binding_id" | "buildWorkspaceSampleContext（SampleStore 用）有 model；ContextStore workspace 不保存 binding_id；restore 时 model 为 null" |
| 3 | 横向表 / History/Admin | "已展示 model ✅" | "VoiceJob 有 model 字段，但 history UI 不展示（仅搜索可用）" |
| 4 | 横向表 / Clone/Design/Import | "使用 binding.model" | "model 来自用户输入框，不是 binding.model" |
| 5 | 横向表 / Audition | 提到 audition_workstation.js | 文件不存在，audition 在 audition_records.js；model 来源是 capability |
| 6 | RISK-003 | "voices/audition/clone/design model 来源不统一" | 准确，但需明确：audition 来自 capability，clone/design/import 来自用户输入 |
| 7 | RISK-005 | "SampleStore/ContextStore 不保存 binding_id" | ContextStore 确认不保存 binding_id；SampleStore 确认不保存 binding_id（normalizeSample 无此字段） |

## 9. 非阻塞观察项

- `P16-MODEL-BINDING-OBS-BATCH-MODEL`：batch longtext/script merged sample 保存 `model: null`，当前行为是否可接受需产品确认
- `P16-MODEL-BINDING-OBS-AUDITION-MODEL`：audition model 来源 capability 而非 binding，两者语义不同（capability model 是能力描述，binding model 是实际执行 model），是否需要统一
- `P16-MODEL-BINDING-OBS-DELETE-SCOPE`：deprecate_bindings_by_provider_voice 可能是设计意图（voice_id 跨 model 通用），需产品确认

## 10. 复核结论

**通过（带修正项）✅**

A0 对核心数据模型（VoiceBinding/ProviderVoice/resolve_binding/执行层）的结论准确。

主要需要修正的是横向入口表中部分描述过于乐观：
- SampleStore schema 支持 model 但 binding_id 不保存，batch sample model 为 null
- ContextStore workspace 不保存 binding_id，restore 时 model 为 null
- History/Admin 有 model 字段但 UI 不展示
- Clone/Design/Import 的 model 来自用户输入，不是 binding.model
- Audition model 来源是 capability

这些修正不影响 B1 核心方向：workspace binding hint 展示 model、ContextStore/SampleStore 保存 binding_id 是真实缺口，B1 方向正确。

### 当前阶段

```
P16-PROVIDER-MODEL-BINDING-A0-CHECK：Provider / Model / VoiceBinding 全链路审查复核 ✅
```

### 下一阶段建议

**P16-PROVIDER-MODEL-BINDING-B1-A0**（B1 前置设计），理由：B1 涉及 `buildWorkspaceRestoreContext`/`ContextStore`/`binding hint`/`SampleStore` 多处前端存储和 UI，需先做实现边界审查再动手。

