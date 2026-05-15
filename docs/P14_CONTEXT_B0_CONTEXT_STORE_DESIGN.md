# P14-CONTEXT-B0：可恢复创作上下文 ContextStore 设计

**日期：2026-05-15**
**前提：P14-SCRIPT-UX-B1-CLOSE 完成**

## 1. 背景

P13 已完成最近样本系统（SampleStore + SampleSidebar），P14 已完成长文本和剧本主生产入口的生成前提示（UX hints）。下一步需要支持样本复用：查看完整文本 / 剧本内容，并一键回填到对应生产入口。

当前 `_batchSampleContextById` 仅存在于内存，页面刷新后丢失。SampleStore 只能存储 100 字符截断预览，不保存完整配置。无法满足：
- 查看长文本完整内容
- 查看剧本完整台词行
- 一键回填到长文本 / 剧本 tab

P14-CONTEXT-B0 只做设计文档，不实现代码。

## 2. P13 SampleStore 当前边界

### 存储结构

```javascript
// sample_store.js
var STORAGE_KEY = 'voice_lab_recent_samples_v1';
var MAX_SAMPLES = 200;
var TEXT_PREVIEW_MAX = 100;
```

SampleStore 保存字段（来自 `normalizeSample`）：

```javascript
{
  sample_id,           // random UUID 或 Date.now+random
  created_at,          // ISO string
  source,              // 'batch_longtext_merged' | 'batch_script_merged' | ...
  job_id,
  batch_id,
  segment_id,
  asset_id,
  download_url,        // blob: URL 被丢弃，置 null
  text_preview,        // 最多 100 字符，超出截断加省略号
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

**SampleStore 不保存：**

```text
- full_text（完整长文本，最多 50000 字）
- segment_strategy
- max_segment_chars
- silence_between_ms
- params（speed/vol/pitch/emotion）
- lines 数组（剧本行完整结构）
- context_id 字段（当前未链接到 ContextStore）
```

### 当前 `_batchSampleContextById` 内存缓存

`batch_longtext.js` 在 submit 成功后保存到 `window._batchSampleContextById[data.batch_id]`：

```javascript
{
  source: 'batch_longtext_merged',
  mode: 'longtext',
  text_preview: text,           // 完整文本，MINIMAX 未截断
  provider: provider,
  profile_id: profileId || null,
  profile_name: null,
  audio_format: outputFormat || null,
  model: null,
  voice_id: null,
  voice_name: null,
}
```

`batch_script.js` 在 submit 成功后保存：

```javascript
{
  source: 'batch_script_merged',
  mode: 'script',
  text_preview: buildScriptTextPreview(lines),  // role + text 拼接
  provider: provider,
  profile_id: getSingleProfileId(lines),
  profile_name: null,
  audio_format: outputFormat || null,
  model: null,
  voice_id: null,
  voice_name: null,
}
```

**问题**：
- 这是内存变量，页面刷新丢失
- 缺少 `context_id` 链接字段
- 缺少 `full_text` / `lines` 完整配置

## 3. 为什么不能把完整内容塞进 SampleStore

```
1. SampleStore.text_preview 硬编码为最多 100 字符截断
2. 长文本 full_text 最多 50000 字，塞入 SampleStore 会：
   - 单条消耗 ~100KB JSON
   - 50 条长文本 context 消耗 ~5MB
   - 接近 localStorage 5～10MB 上限
3. 剧本 lines 数组结构复杂（role/text/profile_id/params），每条可能 1～10KB
4. SampleStore 的设计目标是"轻量索引"，不是"内容仓库"
5. 塞入完整内容会让 SampleStore.getSamples() 变慢（每次需解析大 JSON）
```

## 4. ContextStore 的产品目标

```
目标：保存可恢复上下文，支持查看完整文本 / 完整剧本，支持一键回填。
```

## 5. ContextStore 与 SampleStore 的关系

```
SampleStore 负责"轻量样本卡片索引"。
ContextStore 负责"完整上下文内容"。

关联方式：
SampleStore.sample.context_id → ContextStore[context_id]

context_id 在保存样本时生成，
可以是 sample_id 本身，或独立的 UUID。
```

**建议 v1 策略**：context_id = sample_id（同值），这样 SampleStore 条目和 ContextStore 条目一一对应，简化实现。

## 6. ContextStore 数据结构设计

### Storage key

```javascript
var CONTEXT_STORAGE_KEY = 'voice_lab_sample_context_v1';
```

### Storage value

```javascript
{
  version: 1,
  contexts: [
    { context_id, type, source, ...fields, created_at },
    ...
  ]
}
```

### 限制

```
最多保存 50 条 context（可配置）
按 created_at LRU 淘汰（新的在前，超量时截断）
```

## 7. Longtext context 字段设计

### 字段

```javascript
{
  context_id,              // 关联 SampleStore.sample.context_id
  type: 'longtext',
  source: 'batch_longtext_merged',

  // 核心内容
  full_text,               // 完整长文本，最多 50000 字

  // 生成参数
  provider,
  profile_id,
  segment_strategy,         // 'auto' | 'paragraph' | 'sentence' | 'line'
  max_segment_chars,       // 100～5000，默认 2000
  silence_between_ms,       // 0～3000，默认 300
  output_format,           // 'hex' | 'url'
  audio_format,            // 'mp3' | 'wav' | 'flac'
  need_subtitle,           // boolean

  // params
  params: {
    speed,                 // 0.5～2.0
    vol,                   // 0.1～10.0
    pitch,                 // -12～12
    emotion,               // string
  },

  // 关联信息
  batch_id,                // 用于构建 download_url
  created_at,               // ISO string
}
```

### 不保存

```
- text_preview（由 SampleStore 保存）
- asset_id / download_url（由 SampleStore 保存）
- duration_ms（由 SampleStore 保存）
```

### source 字段说明

```
source 用于区分样本来源，与 ContextStore type 配合使用。
ContextStore.type = 'longtext' 时，source = 'batch_longtext_merged'
ContextStore.type = 'script' 时，source = 'batch_script_merged'
```

## 8. Script context 字段设计

### 字段

```javascript
{
  context_id,              // 关联 SampleStore.sample.context_id
  type: 'script',
  source: 'batch_script_merged',

  // 核心内容
  lines: [                // 只保存有效台词行（text.trim() 非空）
    {
      role,               // string（可为空）
      text,               // string（非空）
      profile_id,         // string
      params: {}          // 空对象（v1 每行无独立 params）
    },
    ...
  ],

  // 生成参数
  provider,
  silence_between_ms,      // 0～3000，默认 500
  output_format,           // 'hex' | 'url'
  audio_format,            // 'mp3' | 'wav' | 'flac'
  need_subtitle,           // boolean

  // 关联信息
  batch_id,
  created_at,
}
```

### 空文本行处理

```
v1 建议：只保存有效台词行（text.trim() 非空）。
空文本行不参与生成，不需要恢复。
如需保留空行结构（未来扩展），可调整设计。
```

### 每行 params

```
v1 结论：lines 中每行 params 为空对象 {}。
后续如需保存 per-line speed/vol/pitch，可扩展。
```

## 9. 存储限制与淘汰策略

### localStorage 限制

```
浏览器 localStorage 上限约 5～10MB（因浏览器而异）
超过时会抛出 QuotaExceededError

ContextStore v1 建议上限：50 条
单条 longtext context 估算：
  - full_text: 最多 50000 字 × 2 字节/字符 = ~100KB
  - 其他字段: ~2KB
  - 合计: ~102KB per context

50 条 longtext context 估算: ~5MB（接近上限）
50 条 script context 估算: ~1MB（每条 lines 约 1～10KB）

长文本和剧本混合时，50 条上限基本安全。
```

### 淘汰策略

```
按 created_at 降序排列（最新在前）。
超过 50 条时，trimContexts() 截断旧记录。
SampleStore 和 ContextStore 独立淘汰，互不干扰。
```

### Storage full 处理

```
写入 ContextStore 时 catch QuotaExceededError：
- 如果是 push 新 context 失败，放弃写入该 context
- SampleStore 仍可正常写入（两者独立）
- 返回的 sample 中 context_id 仍生成，但 ContextStore 写入可能失败
- 后续详情 / 回填按钮检测 context_id 对应记录是否存在，不存在则置灰
```

### context 缺失时的行为

```
SampleStore 记录存在，但 ContextStore 中无对应 context_id：
- 卡片仍可播放（SampleStore 有 download_url）
- 卡片仍可下载
- 卡片仍可复制 text_preview（SampleStore 有）
- 详情按钮：置灰或提示"完整上下文不可用"
- 回填按钮：置灰或提示"配置不可恢复"
```

## 10. 安全与隐私边界

```
ContextStore 是 localStorage，存储在用户本地浏览器。
不跨设备同步。
不经过服务器。
不适合多人 SaaS 共享场景。

用户可见风险：
- 其他使用同一浏览器的人可以看到样本内容
- 清空浏览器数据会丢失所有 context
- 无密码保护

清空样本时的行为（待实现阶段决定）：
- clearSamples() 是否同时清理关联 context？
- 建议：deleteSample 只删 SampleStore，clearSamples 同时清理两者
```

## 11. 与 SampleSidebar 的交互关系

### 当前 SampleSidebar 行为

```javascript
// sample_sidebar.js
window.SampleSidebar = {
  init, render, refresh,
  playSample, deleteSample, clearSamples,
  copyText, fillTextInput,
};
```

`fillTextInput(text)` 硬编码写入 `#textInput`（workspace 文本框），不支持长文本和剧本恢复。

### 升级后的交互

```
SampleSidebar 展示卡片（来自 SampleStore）。
点击"详情"按钮：
  → 从 ContextStore 查找 context_id 对应记录
  → 渲染详情弹层（full_text 或 lines 完整内容）

点击"回填"按钮：
  → 从 ContextStore 查找 context_id 对应记录
  → 切换到对应 tab（长文本 / 剧本）
  → 恢复字段值
  → 不自动提交
```

### 新增 SampleSidebar 按钮

```
在现有 [▶] [⇩] [复制] [回填] [✕] 基础上，
在长文本和剧本卡片中增加 [详情] 按钮。

示例卡片布局：
[长文合并]           3′24″
这是一个关于人工智能的
文章摘要开头文本…       Provider: minimax
张三 · 2026/5/15 14:32

[▶] [⇩] [详情] [复制] [回填] [✕]
```

### ContextStore 缺失时的按钮状态

```
ContextStore 中无 context_id 对应记录：
- 详情按钮：置灰，title="完整上下文不可用"
- 回填按钮：置灰，title="配置不可恢复"
```

## 12. 一键回填行为边界

### Longtext 回填

```
点击"回填"按钮：
1. 切换到长文本 tab
2. 填入 #batchText = context.full_text
3. 恢复 #batchProfile = context.profile_id
4. 恢复 #batchProvider = context.provider
5. 恢复 #batchOutputFormat = context.audio_format
6. 恢复 #batchNeedSubtitle = context.need_subtitle
7. 恢复 #batchStrategy = context.segment_strategy（如实现）
8. 恢复 #batchMaxChars = context.max_segment_chars（如实现）
9. 恢复 #batchSilence = context.silence_between_ms（如实现）
10. 恢复 #batchSpeed / #batchVol / #batchPitch / #batchEmotion = context.params（如实现）
11. 不自动生成
12. 用户确认后手动点击"提交批量任务"
```

**必须明确：回填不是自动重新生成，回填只是恢复编辑状态。**

### Script 回填

```
点击"回填"按钮：
1. 切换到剧本 tab
2. 弹确认对话框：
   "当前剧本内容将被替换，是否继续？"
   - 确认 → 继续
   - 取消 → 不操作
3. 如确认：
   a. 清空当前 #scriptLines container
   b. 清空 _scriptRows 数组
   c. 重建剧本行：
      - 遍历 context.lines
      - 对每行调用 addScriptLine(role, text, profileId)
      - 恢复 role / text / profile_id
   d. 恢复 #batchScriptProvider = context.provider
   e. 恢复 #batchScriptOutputFormat = context.audio_format
   f. 恢复 #batchScriptNeedSubtitle = context.need_subtitle
   g. 恢复 #batchScriptSilence = context.silence_between_ms（如实现）
4. 不自动生成
5. 用户确认后手动点击"提交批量任务"
```

### 回填不触发的操作

```
回填时禁止：
- 自动提交
- 自动播放
- 自动下载
- 修改 SampleStore
- 删除 ContextStore
```

## 13. 不做事项

```
B0 不实现代码
B0 不创建 context_store.js
B0 不实现详情弹层
B0 不实现一键回填
B0 不修改 SampleStore
B0 不修改 SampleSidebar
B0 不实现长文本回填
B0 不实现剧本回填
B0 不调用真实 MiniMax
B0 不实现跨 tab 状态同步
```

## 14. 后续阶段建议

### 阶段拆分

```
P14-CONTEXT-B1：实现 context_store.js 基础模块
  - STORAGE_KEY = 'voice_lab_sample_context_v1'
  - pushContext / getContext / deleteContext / trimContexts
  - 与 SampleStore 独立
  - 50 条上限，LRU 淘汰
  - fail-safe（QuotaExceededError 处理）

P14-CONTEXT-B2：长文本 context 保存与详情查看
  - handleBatchLongtextSubmit 成功后保存 context
  - SampleStore.sample.context_id = sample.sample_id
  - 详情弹层（只读 full_text）
  - context 缺失时详情按钮置灰

P14-CONTEXT-B3：长文本一键回填
  - 回填按钮调用 ContextStore.getContext
  - 恢复 #batchText / profile / provider / format / subtitle 等字段
  - 不自动提交

P14-CONTEXT-C1：剧本 context 保存与详情查看
  - handleBatchScriptSubmit 成功后保存 context
  - 详情弹层（只读 lines 完整内容）
  - context 缺失时详情按钮置灰

P14-CONTEXT-C2：剧本一键回填
  - 回填按钮调用 ContextStore.getContext
  - 弹确认对话框
  - 重建剧本行
  - 恢复 provider / format / subtitle 等字段
  - 不自动提交

P14-PRODUCT-B0：全局 SampleSidebar 可见性方案设计
  - Sidebar 在所有 tab 可见性
  - 触发方式（按钮 / 自动）
  - 与其他 UI 的关系
```

### 阶段顺序建议

```
B1（基础模块）→ B2（长文保存+详情）→ B3（长文回填）
                      ↓
               C1（剧本保存+详情）→ C2（剧本回填）

PRODUCT-B0 可在任何时间并行。
```

## 15. 测试计划（B1 实现后）

```python
# context_store.js 基础模块
1. ContextStore.pushContext 保存成功
2. ContextStore.getContext(context_id) 返回正确记录
3. ContextStore.deleteContext(context_id) 删除记录
4. 50 条上限时 LRU 淘汰
5. QuotaExceededError 时 fail-safe
6. context_id 不存在时 getContext 返回 null

# 与 SampleStore 关联
7. batch_longtext submit 后 SampleStore 条目有 context_id
8. batch_script submit 后 SampleStore 条目有 context_id

# 详情弹层
9. 长文本样本点击详情显示 full_text
10. 剧本样本点击详情显示 lines 完整内容
11. context 不存在时详情按钮置灰

# 回填（长文本）
12. 点击回填切换到长文本 tab
13. #batchText 填入 full_text
14. profile/provider/format/subtitle 恢复
15. 不自动提交

# 回填（剧本）
16. 点击回填弹出确认对话框
17. 确认后清空当前剧本行
18. lines 正确重建
19. role / text / profile_id 正确恢复
20. 不自动提交

# 边界
21. context 缺失时播放/下载仍可用
22. context 缺失时详情/回填置灰
23. 不调用真实 MiniMax
24. 不修改 SampleStore 结构
```

## 16. B0 结论

### 确认事实

- SampleStore `text_preview` 硬编码 100 字符截断，不适合存完整内容
- `_batchSampleContextById` 是内存变量，页面刷新丢失
- `batch_longtext.js` 当前保存 `text_preview = text`（完整文本），但没有 `context_id`
- `batch_script.js` 当前保存 `text_preview = buildScriptTextPreview(lines)`，没有完整 lines 结构
- SampleSidebar `fillTextInput` 只写 `#textInput`，不支持长文本 / 剧本回填
- localStorage 上限约 5～10MB，长文本 full_text 最多 ~100KB/条

### 设计结论

- ContextStore 使用独立 key `voice_lab_sample_context_v1`
- SampleStore.sample.context_id = sample.sample_id（v1 简化关联）
- ContextStore 最多 50 条，按 created_at LRU 淘汰
- longtext context 保存 `full_text` + 生成参数
- script context 保存 `lines`（有效台词行）+ 生成参数
- context 缺失时播放/下载/复制仍可用，详情/回填置灰
- 回填只恢复编辑状态，不自动生成
- 不把完整内容塞进 SampleStore

### 阶段状态

B0 完成，建议进入 P14-CONTEXT-B1（实现 context_store.js 基础模块）。
