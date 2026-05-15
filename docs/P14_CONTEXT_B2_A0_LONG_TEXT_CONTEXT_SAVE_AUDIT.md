# P14-CONTEXT-B2-A0：长文本 context 保存与详情查看接入前置审查

**日期：2026-05-16**
**前提：P14-CONTEXT-B1-CLOSE 完成**

## 1. 背景

P14-CONTEXT-B1 已完成 `context_store.js` 基础模块，但尚未接入任何生成链路。本阶段审查长文本 context 保存与详情查看的前置条件，输出可进入 P14-CONTEXT-B2 的设计决策和代码改动清单。

P14-CONTEXT-B2-A0 只做审查文档，不实现代码。

## 2. 当前代码事实

### 2.1 当前 batch_longtext → SampleStore 调用链

```
handleBatchLongtextSubmit() [batch_longtext.js]
  → 提交成功后
  → window._batchSampleContextById[data.batch_id] = { source, mode, text_preview, provider, ... }
  → showBatchProgress() → startBatchPoll()
  → polling 完成 → renderBatchResultPlayer() [index.html]
  → safePushBatchSample(batchSource, data, batchExtra)
  → SampleStore.pushSample({ source, job_id, batch_id, ..., provider, profile_id, ... })
```

关键事实：
- `batch_longtext.js` 只保存到内存 `_batchSampleContextById`，页面刷新丢失
- `_batchSampleContextById[data.batch_id]` 包含 `text_preview`（完整文本），但不含 `full_text`（也是完整文本，相同值）
- 提交成功后**未调用** `ContextStore.pushContext()`
- `SampleStore.normalizeSample` 当前**无** `context_id` 字段
- `safePushBatchSample` 当前**未接收** `context_id` 参数

### 2.2 `_batchSampleContextById[data.batch_id]` 当前结构

```javascript
{
  source: 'batch_longtext_merged',
  mode: 'longtext',
  text_preview: text,          // 完整长文本，等于 full_text
  provider: provider,
  profile_id: profileId || null,
  profile_name: null,
  audio_format: outputFormat || null,
  model: null,
  voice_id: null,
  voice_name: null,
}
```

### 2.3 `safePushBatchSample` 当前行为

当前 `safePushBatchSample`（index.html line 5098）：

```javascript
function safePushBatchSample(source, data, extra = {}) {
  // ...
  const sample = window.SampleStore.pushSample({
    source: source,
    job_id: batchId,
    batch_id: batchId,
    segment_id: null,
    asset_id: audio.id,
    download_url: downloadUrl,
    text_preview: textPreview,        // extra.text_preview || firstSegmentText
    provider: extra.provider || null,
    model: null,
    voice_id: null,
    voice_name: null,
    profile_id: extra.profile_id || null,
    profile_name: null,
    duration_ms: data.total_duration_ms || null,
    audio_format: extra.audio_format || null,
    status: 'completed',
    tags: ['batch', 'merged'],
  });
  // ...
}
```

缺失字段：
- `context_id`：未传递
- `batch_id` 在 SampleStore 中存在（job_id = batch_id = batchId）但未作为独立字段传入

### 2.4 `SampleStore.normalizeSample` 当前结构

```javascript
{
  sample_id,     // 自动生成
  created_at,
  source,
  job_id,
  batch_id,
  segment_id,
  asset_id,
  download_url,
  text_preview,    // 100字符截断
  profile_id,
  profile_name,
  provider,
  model,
  voice_id,
  voice_name,
  duration_ms,
  audio_format,
  status,
  tags,
}
```

**无** `context_id` 字段。

### 2.5 `ContextStore` 当前加载状态

`context_store.js` **未加载**到 `index.html`。

Script 加载顺序（index.html lines 1864-1899）：

```
provider_capabilities.js
runtime_status.js
history.js
product_hints.js
audition_records.js
batch_longtext.js      ← 在 sample_store.js 之前
sample_store.js
sample_sidebar.js
```

`context_store.js` 未出现在此列表中。

### 2.6 `ContextStore.pushContext` 当前签名

```javascript
window.ContextStore.pushContext({
  context_id,          // 优先 input.context_id
  type: 'longtext',
  source: 'batch_longtext_merged',
  full_text,
  provider,
  profile_id,
  segment_strategy,
  max_segment_chars,
  silence_between_ms,
  output_format,
  audio_format,
  need_subtitle,
  params: { speed, vol, pitch, emotion },
  batch_id,
  created_at,
})
```

## 3. 前置条件审查

### 3.1 前置条件 1：`context_store.js` 未加载

**现状**：`context_store.js` 不在 `index.html` 的 script 加载列表中。

**影响**：无法调用 `ContextStore.pushContext()`。

**解决方案**：
在 `index.html` 的 script 加载列表中，在 `batch_longtext.js` 之前添加：

```html
<script src="/static/js/context_store.js"></script>
```

建议加载位置：`sample_store.js` 之后，`batch_longtext.js` 之前（或 `sample_sidebar.js` 之后）。

### 3.2 前置条件 2：`SampleStore.normalizeSample` 无 `context_id`

**现状**：`normalizeSample` 返回的对象不包含 `context_id` 字段。

**影响**：`SampleStore` 条目无法通过 `context_id` 关联到 `ContextStore` 条目。

**P14-CONTEXT-B0 结论**：`context_id = sample.sample_id`（v1 简化策略）。

**解决方案**：

`normalizeSample` 中增加：

```javascript
context_id: input.context_id != null ? String(input.context_id) : null,
```

`safePushBatchSample` 中增加传入：

```javascript
const sample = window.SampleStore.pushSample({
  // ...existing fields...
  context_id: extra.context_id || null,
});
```

### 3.3 前置条件 3：`_batchSampleContextById` 未保存到 ContextStore

**现状**：`batch_longtext.js` 提交成功后只保存到内存 `_batchSampleContextById`。

**影响**：页面刷新后 context 丢失，无法进行详情查看和回填。

**解决方案**：

在 `batch_longtext.js` 提交成功逻辑中，保存到 `ContextStore`：

```javascript
// 在 window._batchSampleContextById 保存之后、showBatchProgress 之前
if (window.ContextStore && typeof window.ContextStore.pushContext === 'function') {
  var contextId = data.batch_id;  // 使用 batch_id 作为 context_id
  window.ContextStore.pushContext({
    context_id: contextId,
    type: 'longtext',
    source: 'batch_longtext_merged',
    full_text: text,
    provider: provider,
    profile_id: profileId || null,
    segment_strategy: strategy,
    max_segment_chars: maxChars,
    silence_between_ms: silence,
    output_format: 'hex',
    audio_format: outputFormat,
    need_subtitle: needSubtitle,
    params: params,
    batch_id: data.batch_id,
  });
  // 将 context_id 存入 _batchSampleContextById，供 safePushBatchSample 使用
  window._batchSampleContextById[data.batch_id].context_id = contextId;
}
```

注：使用 `batch_id` 作为 `context_id` 可简化 v1 关联逻辑（一个 batch_id 对应一个 context_id）。

### 3.4 前置条件 4：`safePushBatchSample` 未传递 `context_id`

**现状**：`safePushBatchSample` 不接收也不传递 `context_id`。

**影响**：`SampleStore.pushSample` 收不到 `context_id`。

**解决方案**：

`safePushBatchSample` 增加从 `extra` 读取 `context_id`：

```javascript
context_id: extra.context_id || null,
```

`extra.context_id` 来自 `_batchSampleContextById[data.batch_id].context_id`（已在 3.3 中设置）。

### 3.5 前置条件 5：SampleSidebar 尚无详情按钮

**现状**：`sample_sidebar.js` 的 `buildCard` 中只有 play/download/copy/fill/delete 按钮，无详情按钮。

**影响**：无法触发详情弹层。

**解决方案**（P14-CONTEXT-B2 范围，不在本 A0 范围内）：
- 在 `sample_sidebar.js` 的卡片操作按钮区增加"详情"按钮
- 点击后从 `ContextStore.getContext(sample.context_id)` 获取完整 context
- 渲染只读详情弹层（长文本显示 `full_text` 完整内容）
- `context_id` 不存在时按钮置灰

## 4. 调用时序设计

### P14-CONTEXT-B2 目标调用时序

```
1. 用户在长文本 tab 填写内容，点击提交
2. handleBatchLongtextSubmit() 提交
3. 后端返回 success，batch_id = "xxx"
4. [新增] 调用 ContextStore.pushContext({ context_id: "xxx", type: 'longtext', full_text, ... })
5. _batchSampleContextById["xxx"] 保存 batch context（含新增的 context_id）
6. 启动 polling
7. polling 完成后 renderBatchResultPlayer()
8. [新增] safePushBatchSample(source, data, batchExtra) 其中 batchExtra.context_id = "xxx"
9. SampleStore.pushSample({ ..., context_id: "xxx" })
10. [新增] SampleSidebar.refresh() 显示含 context_id 的样本卡
```

## 5. 代码改动清单

### 5.1 `app/static/index.html`

| 改动 | 类型 | 说明 |
|------|------|------|
| 新增 `<script src="/static/js/context_store.js">` | 追加 | 放在 `sample_store.js` 之后、`batch_longtext.js` 之前 |
| `safePushBatchSample` 增加 `context_id: extra.context_id \|\| null` | 修改 | 透传 context_id 到 SampleStore |

### 5.2 `app/static/js/batch_longtext.js`

| 改动 | 类型 | 说明 |
|------|------|------|
| 提交成功后调用 `window.ContextStore.pushContext(...)` | 新增 | 保存完整长文本 context |
| 保存 `context_id` 到 `_batchSampleContextById[data.batch_id]` | 新增 | 供后续 `safePushBatchSample` 使用 |

### 5.3 `app/static/js/sample_store.js`

| 改动 | 类型 | 说明 |
|------|------|------|
| `normalizeSample` 增加 `context_id: input.context_id != null ? String(input.context_id) : null` | 修改 | 支持 context_id 持久化 |

### 5.4 `app/static/js/sample_sidebar.js`（P14-CONTEXT-B2 范围）

| 改动 | 类型 | 说明 |
|------|------|------|
| 卡片增加"详情"按钮 | 新增 | 调用 ContextStore.getContext |
| 详情弹层渲染 `full_text` | 新增 | 长文本完整内容只读展示 |
| `context_id` 不存在时按钮置灰 | 新增 | graceful fallback |

## 6. 注意事项

### 6.1 anti-duplicate 机制

`safePushBatchSample` 使用 `_batchSamplePushedByKey[pushKey]` 防重复写入。

ContextStore 的 `pushContext` 使用 upsert 逻辑（同 `context_id` 替换旧记录），天然 anti-duplicate。

因此：
- 多次调用 `renderBatchResultPlayer` 不会重复创建 SampleStore 条目
- 多次调用 `ContextStore.pushContext` 也不会重复，只会 upsert

### 6.2 已有样本的 context_id

P14-CONTEXT-B2 实现之前已存在的 batch 样本：
- `SampleStore` 条目无 `context_id`（为 null）
- `ContextStore` 中无对应记录

这些样本的详情/回填按钮应置灰，不应尝试读取不存在的 context。

### 6.3 QuotaExceededError 处理

`ContextStore.pushContext` 使用 `safeSetItem`，写入失败时静默忽略。

如果 ContextStore 写失败：
- SampleStore 仍正常写入
- 样本卡片显示，但详情/回填不可用
- 不阻塞生成流程

### 6.4 不修改 batch_longtext submit payload

`ContextStore.pushContext` 是在后端返回成功后、前端 polling 启动前调用的，**不改变**后端 API payload。

## 7. 阶段边界

```
B2-A0 只做审查
B2-A0 不修改代码
B2-A0 不加载 context_store.js 到 index.html
B2-A0 不修改 safePushBatchSample
B2-A0 不修改 batch_longtext.js
B2-A0 不修改 SampleStore
B2-A0 不修改 SampleSidebar
B2-A0 不实现详情弹层
B2-A0 不实现回填
```

## 8. B2 阶段拆分建议

```
P14-CONTEXT-B2：接入 longtext context 保存
  - index.html 加载 context_store.js
  - batch_longtext.js 调用 ContextStore.pushContext
  - safePushBatchSample 传递 context_id
  - SampleStore.normalizeSample 增加 context_id 字段

P14-CONTEXT-B2-CHECK：复核 longtext context 保存接入

P14-CONTEXT-B3：长文本一键回填
  - 回填按钮调用 ContextStore.getContext
  - 恢复字段到长文本 tab 表单
  - 不自动提交
```

## 9. B0 结论

### 前置条件确认

- `context_store.js` 未加载 → 需在 index.html 追加 script 标签
- `SampleStore.normalizeSample` 无 `context_id` → 需增加字段
- `_batchSampleContextById` 未保存到 ContextStore → 需在 batch_longtext.js 提交成功逻辑中新增调用
- `safePushBatchSample` 未传递 `context_id` → 需增加 extra.context_id 透传
- SampleSidebar 无详情按钮 → P14-CONTEXT-B2 范围

### 简化策略

- v1 使用 `batch_id` 作为 `context_id`（一一对应，简化实现）
- ContextStore upsert 天然 anti-duplicate
- ContextStore 写入失败静默，不阻塞生成流程

### 阶段状态

B2-A0 完成，建议进入 P14-CONTEXT-B2 实现。
