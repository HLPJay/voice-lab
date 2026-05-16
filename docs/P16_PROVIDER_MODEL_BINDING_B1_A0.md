# P16-PROVIDER-MODEL-BINDING-B1-A0：最小 model/binding 可见性与恢复增强前置设计

## 1. 阶段背景

- **分支**：`p16/real-usage-issues`
- **目标**：为 B1 实现确定最小范围、文件边界、数据字段、测试策略
- **性质**：纯设计文档，不修改功能代码

## 2. A0-CHECK 结论输入

| 发现项 | CHECK 修正 |
|---|---|
| VoiceBinding 数据层完整 | ✅ A0 结论准确 |
| ProviderVoice 无 model 字段 | ✅ A0 结论准确 |
| resolve_binding 无 model/binding_id 参数 | ✅ A0 结论准确 |
| 执行层 VoiceJob 有 model + binding_id | ✅ A0 结论准确 |
| SampleStore schema 支持 model，但不保存 binding_id | ⚠️ 修正：batch sample model 为 null |
| ContextStore workspace 不保存 binding_id，restore 时 model 为 null | ⚠️ 修正：确认 binding_id 字段完全缺失 |
| History/Admin 后端有 model 字段但 UI 不展示 | ⚠️ 修正：VoiceJob 有字段，前端不渲染 |
| Clone/Design/Import model 来自用户输入 | ⚠️ 修正：不是 binding.model |
| Audition model 来源 capability（tts.models） | ⚠️ 修正：不是 binding.model |

## 3. B1 最小目标

**B1 是前端本地可见性与恢复增强，不是后端 binding 解析重构。**

B1 核心目标：
1. 让 workspace 用户看到当前实际使用的 binding 的 model / voice_name
2. 让 workspace SampleStore / ContextStore 能保存 binding_id + model
3. 让 workspace restore 时展示当时的 binding 信息

**B1 不改变**：resolve_binding 行为、生成 payload、后端 binding 解析链路。

## 4. 必须纳入范围

### 4.1 纳入 1：Workspace binding hint 展示 model

**目标**：在现有 bindingStatus 区域增加 model 展示，让用户可见当前实际使用的 model。

**当前状态**：
- `checkBindingStatus()` 的 bound 分支显示 `✓ 已绑定: ${b.provider_voice_id} (${b.model})`
- `_voiceBindMap` 中每条 binding 有 `model` 字段

**缺口**：UI 显示的 `b.model` 来自 binding hint，但 workspace 主区域没有额外展示。

**B1 改动**：
- 不新增 model 下拉
- 不改变 binding 选择逻辑
- 只在 binding hint 或当前音色提示区增加一行 model 展示

**推荐展示**：
```
已绑定 {voice_name || provider_voice_id} · {provider}/{model}
```

### 4.2 纳入 2：buildWorkspaceRestoreContext 保存 binding_id + model + provider_voice_id + voice_name

**目标**：让 ContextStore 能保存完整的 binding 信息，restore 时可展示。

**当前状态**：
- `buildWorkspaceRestoreContext()` 保存 `provider / profile_id / profile_name`，model 来自 `extra.model`，调用处传 `null`
- `buildWorkspaceSampleContext()`（用于 SampleStore）从 `_voiceBindMap` 推导 model，但这两个函数是独立的

**缺口**：
- `buildWorkspaceRestoreContext` 不保存 binding_id
- `buildWorkspaceRestoreContext` 调用处未传 model

**B1 改动**：
- 新增 `getCurrentWorkspaceBindingInfo()` helper，从 `_voiceBindMap` 获取当前 provider/profile 的默认 binding
- 将 `binding_id / model / provider_voice_id / voice_name` 写入 context
- 不发 API，不依赖后端

**示例**：
```javascript
function getCurrentWorkspaceBindingInfo() {
  const provider = providerSelect?.value || "mock";
  const profileId = profileSelect?.value || "";
  const bindings = Array.isArray(window._voiceBindMap?.[profileId])
    ? window._voiceBindMap[profileId]
    : [];
  const matched = bindings.filter(b =>
    b.provider === provider && b.status === "available"
  );
  const binding = matched[0] || null;
  return {
    binding_id: binding?.id || null,
    provider,
    model: binding?.model || null,
    provider_voice_id: binding?.provider_voice_id || null,
    voice_name: binding?.name || binding?.voice_name || null,
    profile_id: profileId || null,
    profile_name: getSelectedProfileName(),
  };
}
```

### 4.3 纳入 3：ContextStore workspace context 增加 binding_id 字段

**目标**：让 ContextStore 的 workspace context 能保存 binding_id。

**当前状态**：`context_store.js` 的 `normalizeWorkspaceContext` 没有 binding_id 字段。

**B1 改动**：
- `normalizeWorkspaceContext` 增加 `binding_id / provider_voice_id / voice_name` 字段
- 旧 context 没有这些字段时降级处理，不报错

### 4.4 纳入 4：SampleStore workspace sample 增加 binding_id

**目标**：让 SampleStore 的 workspace sample 能保存 binding_id。

**当前状态**：`normalizeSample` 支持 `model / voice_id / voice_name`，但无 `binding_id` 字段。

**B1 改动**：
- `normalizeSample` 增加 `binding_id` 字段
- workspace sample 写入时传入 `binding_id`
- 旧 sample 无 `binding_id` 时不影响展示

## 5. 可选纳入范围

### 5.1 History/Admin 展示 model

- VoiceJob 已有 model 字段
- history UI 不渲染 model，只在搜索过滤时使用
- 如果改动成本极小（加一行），可纳入 B1
- 如果影响历史 UI 布局，后置

## 6. 不纳入范围

| 项 | 原因 |
|---|---|
| model 下拉 | B1 不改变用户选择 model 的方式 |
| resolve_binding 重构 | 不改后端 binding 解析逻辑 |
| binding_id 精确执行 | B1 只做可见性和保存，不做 binding_id 执行校验 |
| VoiceBinding schema 改 | 数据层已完整 |
| ProviderVoice schema 加 model | 需先确认 MiniMax 语义 |
| Batch longtext/script 重构 | B1 聚焦 workspace |
| Batch sample model=null | 暂不处理 |
| Audition model 来源统一 | 涉及 capability vs binding 语义，需单独评估 |
| Clone/Design/Import model 输入改 | 用户输入是当前设计，不强制绑定到 binding |
| Capability UI | 后续 P16-PROVIDER-CAPABILITY-UI-B1 |
| 多版本等待态 | P16-VARIANTS-UX-FIX1 |
| 服务端创作记录 | P17-CREATION-RECORD-A0 |

## 7. 实现文件边界

### B1 可修改文件

| 文件 | 改动内容 |
|---|---|
| `app/static/index.html` | `getCurrentWorkspaceBindingInfo()` helper、`checkBindingStatus` 展示 model、`buildWorkspaceRestoreContext` 写入 binding info |
| `app/static/js/context_store.js` | `normalizeWorkspaceContext` 增加 binding_id/provider_voice_id/voice_name 字段 |
| `app/static/js/sample_store.js` | `normalizeSample` 增加 binding_id 字段 |
| `app/static/js/sample_sidebar.js` | restore 后展示 binding model/info（可选） |
| `tests/test_provider_model_binding_static.py` | 新增静态测试 |

### B1 禁止修改文件

```
app/models/*         — 不改数据模型
app/repositories/*    — 不改 resolve_binding
app/services/*       — 不改后端逻辑
app/api/*            — 不改 API
app/providers/*      — 不改 Provider Adapter
app/domain/*         — 不改 schema
VoiceBinding schema  — 不改
ProviderVoice schema — 不改
resolve_binding      — 不改签名/逻辑
provider_capabilities.js — 不改
batch_shared.js     — 不改
profile_binding.js   — 不改
audition_records.js — 不改
voice_clone.js       — 不改
voice_design.js      — 不改
voice_import.js     — 不改
```

## 8. 推荐实现策略

### 8.1 getCurrentWorkspaceBindingInfo()

在 `index.html` 新增，不影响现有逻辑：

```javascript
// B1-PROVIDER-MODEL-BINDING: 获取当前 workspace 的有效 binding 信息
function getCurrentWorkspaceBindingInfo() {
  const provider = providerSelect?.value || "mock";
  const profileId = profileSelect?.value || "";
  if (!profileId || !provider) {
    return { binding_id: null, provider, model: null, provider_voice_id: null, voice_name: null, profile_id: null, profile_name: null };
  }
  const bindings = Array.isArray(window._voiceBindMap?.[profileId]) ? window._voiceBindMap[profileId] : [];
  const matched = bindings.filter(b => b.provider === provider && b.status === "available");
  const binding = matched[0] || null;
  return {
    binding_id: binding?.id || null,
    provider,
    model: binding?.model || null,
    provider_voice_id: binding?.provider_voice_id || null,
    voice_name: binding?.name || binding?.voice_name || null,
    profile_id: profileId || null,
    profile_name: getSelectedProfileName(),
  };
}
```

要求：
- 只读 `_voiceBindMap`，不发 API
- 不改变 `checkBindingStatus` 逻辑
- 不引入后端依赖

### 8.2 checkBindingStatus 展示 model

当前 bound 分支已有 model 显示，B1 只需确认格式足够清晰：

```
已绑定：{voice_name || provider_voice_id} · {model} · {provider}
```

或：

```
已绑定 {voice_name || provider_voice_id}
模型：{model}
Provider：{provider}
```

### 8.3 buildWorkspaceRestoreContext 接入 binding info

```javascript
// 在 buildWorkspaceRestoreContext 结尾合并 binding info
const bindingInfo = getCurrentWorkspaceBindingInfo();
return {
  // ... 现有字段 ...
  binding_id: bindingInfo.binding_id,
  model: bindingInfo.model,
  provider_voice_id: bindingInfo.provider_voice_id,
  voice_name: bindingInfo.voice_name,
};
```

**关键**：修复调用处传入 `extra.model` 为 `null` 的问题。

### 8.4 ContextStore normalizeWorkspaceContext 增加字段

在 workspace context 分支：
```javascript
binding_id: ctx.binding_id || null,
provider_voice_id: ctx.provider_voice_id || null,
voice_name: ctx.voice_name || null,
// model 已有，确认不被覆盖为 null
```

### 8.5 SampleStore normalizeSample 增加字段

```javascript
binding_id: input.binding_id != null ? input.binding_id : null,
// 现有 model/voice_id/voice_name 保留
```

### 8.6 sample_sidebar restore 展示 binding 详情（可选）

在 workspace restore 后的详情展示中增加：
```
模型：{model}
音色：{voice_name || provider_voice_id}
```

不执行，不依赖 binding_id 查后端。

## 9. 数据字段设计

### ContextStore workspace context（B1 目标）

| 字段 | 来源 | 说明 |
|---|---|---|
| binding_id | getCurrentWorkspaceBindingInfo() | 当前默认 binding 的 id，可为 null |
| model | getCurrentWorkspaceBindingInfo() | 当前默认 binding 的 model，可为 null |
| provider_voice_id | getCurrentWorkspaceBindingInfo() | 当前默认 binding 的 voice id |
| voice_name | getCurrentWorkspaceBindingInfo() | 当前默认 binding 的 name |
| provider | providerSelect.value | 用户选择的 provider |
| profile_id | profileSelect.value | 用户选择的 profile |
| profile_name | getSelectedProfileName() | profile 名称 |
| full_text | DOM textInput.value | 完整文本 |
| audio_format | audioFormatSelect.value | 音频格式 |

### SampleStore workspace sample（B1 目标）

| 字段 | 来源 | 说明 |
|---|---|---|
| binding_id | getCurrentWorkspaceBindingInfo() | 新增字段 |
| model | getCurrentWorkspaceBindingInfo() | 已有字段 |
| provider_voice_id | getCurrentWorkspaceBindingInfo() | 已有字段（voice_id） |
| voice_name | getCurrentWorkspaceBindingInfo() | 已有字段 |

## 10. 兼容策略

| 场景 | 策略 |
|---|---|
| 旧 ContextStore workspace context 无 binding_id | 不报错，binding_id 为 null |
| 旧 SampleStore sample 无 binding_id | 不报错，展示不受影响 |
| 旧 context 有 model=null | 展示"模型未知"或不显示 model 行 |
| 当前找不到 binding（unbound） | binding_id/model/voice_name 均为 null，不阻塞 |
| binding 变更（restore 后） | 展示"当时"的 binding 信息，不阻塞用户 |

## 11. 测试策略

### 新增测试文件

```
tests/test_provider_model_binding_static.py
```

### 必须覆盖的测试用例

| # | 测试 | 验证内容 |
|---|---|---|
| 1 | `getCurrentWorkspaceBindingInfo` 存在 | `typeof window.getCurrentWorkspaceBindingInfo === 'function'` |
| 2 | 返回字段完整 | 返回对象含 binding_id / model / provider / provider_voice_id / voice_name / profile_id |
| 3 | unbound 时返回 null 字段 | profileId 或 provider 为空时各字段为 null |
| 4 | `buildWorkspaceRestoreContext` 写入 binding_id | context 对象含 binding_id（非 undefined） |
| 5 | `buildWorkspaceRestoreContext` 写入 model | context 对象含 model（非 undefined） |
| 6 | `normalizeWorkspaceContext` 保存 binding_id | 旧 context 无 binding_id 时不报错 |
| 7 | `normalizeSample` 支持 binding_id | 写入 binding_id 不被过滤 |
| 8 | binding hint 展示 model | bound 分支 textContent 含 model 字符串 |
| 9 | 不修改 resolve_binding | 代码中 resolve_binding 仍无 model 参数 |
| 10 | 不新增 model 下拉 | providerSelect 外无 modelSelect |

### 回归测试

```bash
python -m pytest tests/test_provider_model_binding_static.py -q
python -m pytest tests/test_workspace_restore_static.py tests/test_sample_sidebar_static.py -q
python -m pytest tests/test_provider_mock_boundary_static.py -q
```

## 12. 下一阶段建议

B1-A0 完成 → B1 实现 → B1-CHECK → Capability-UI-B1

**B1 实现注意事项**：
1. 先改 `getCurrentWorkspaceBindingInfo()`，再依次接入各调用点
2. `buildWorkspaceRestoreContext` 和 `buildWorkspaceSampleContext` 是两个不同函数，不要混淆
3. `ContextStore.normalizeWorkspaceContext` 是 context_store.js 中的 normalize，不是 buildWorkspaceRestoreContext
4. `sample_sidebar` 的 restore 展示是可选的，先聚焦前 4 项必须纳入
