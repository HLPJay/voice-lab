# P13-CREATION-B5-A0：batch sample_store 接入字段核验与方案设计

> **本文档经 P13-CREATION-B5-A0-CODE-CHECK-FIX 修正，以真实代码为唯一事实源。**
> 上次版本存在多处字段级错误（DOM id、payload 字段、函数签名、status 口径）。

---

## 1. 背景

B4 已完成 sample_sidebar UI + workspace/audition sample_store 接入。B5 目标是将 batch_longtext / batch_script 的生成结果接入 sample_store。本阶段（A0）只做代码审查和文档设计，不实现 B5。

---

## 2. 当前 batch_longtext 代码路径

```
window.handleBatchLongtextSubmit (onclick)
  → 读取 #batchText
  → 读取 #batchProfile (profile_id)
  → 读取 #batchProvider
  → 读取 #batchStrategy
  → 读取 #batchMaxChars
  → 读取 #batchSilence
  → 读取 #batchOutputFormat
  → 读取 #batchNeedSubtitle
  → 读取 #batchSpeed / #batchVol / #batchPitch / #batchEmotion (组装为 params)
  → guardedJsonFetch('/api/voice/batch/submit', {
      mode: 'longtext',
      text,
      profile_id,
      provider,
      segment_strategy: strategy,
      max_segment_chars: maxChars,
      silence_between_ms: silence,
      output_format: 'hex',
      audio_format: outputFormat,
      params,
      need_subtitle,
      confirm_cost: false,
    })
  → data.batch_id 存入 _currentBatchId
  → showBatchProgress(data.batch_id)
  → startBatchPoll(data.batch_id)
  → pollBatchStatus → renderBatchStatus → renderBatchResultPlayer
```

### 2.1 重要结论：longtext 无 voice_id / voice_name / model / profile_name

当前 longtext submit 代码**没有**以下字段：

- `voice_id` — 不存在
- `voice_name` — 不存在
- `model` — 不存在
- `selectedVoiceId` — 不存在
- `selectedVoiceName` — 不存在
- `selectedModel` — 不存在
- `selectedProfileName` — 不存在
- `textarea#batchLongtextText` — DOM id 是 `#batchText`，不是 `batchLongtextText`

**B5-MVP1 不得伪造这些字段。**

---

## 3. 当前 batch_script 代码路径

```
window.handleBatchScriptSubmit (onclick)
  → 同步 DOM 到 _scriptRows：
      scriptRole_{id} → state.role
      scriptText_{id} → state.text
      scriptProfile_{id} → state.profileId
  → 遍历 _scriptRows，过滤空行，组装 lines[]：
      { role, text, profile_id, params: {} }
  → 读取 #batchScriptProvider
  → 读取 #batchScriptSilence
  → 读取 #batchScriptOutputFormat
  → 读取 #batchScriptNeedSubtitle
  → guardedJsonFetch('/api/voice/batch/submit', {
      mode: 'script',
      script: lines,
      provider,
      silence_between_ms: silence,
      output_format: 'hex',
      audio_format: outputFormat,
      need_subtitle,
      confirm_cost: false,
    })
  → data.batch_id 存入 _currentBatchId
  → showBatchProgress(data.batch_id, 'batchScriptProgressPanel')
  → startBatchPoll(data.batch_id, 'batchScriptProgressPanel')
  → pollBatchStatus → renderBatchStatus → renderBatchResultPlayer
```

### 3.1 重要结论：script 无全局 voice_id / voice_name / model / profile_name

当前 script submit 代码**没有**以下字段：

- `voice_id` — 不存在
- `voice_name` — 不存在
- `model` — 不存在
- `selectedVoiceId` — 不存在
- `selectedVoiceName` — 不存在
- `selectedModel` — 不存在
- `selectedProfileName` — 不存在
- `textarea#batchScriptText.value.split('\n')` — 不是这种数据来源

每行有独立的 `profile_id`（来自 `scriptProfile_{id}`），但没有全局 voice/model 信息。

---

## 4. 共享轮询与结果渲染路径

### 4.1 函数签名（真实代码）

```javascript
function startBatchPoll(batchId, targetPanelId = 'batchProgressPanel')
async function pollBatchStatus(batchId, targetPanelId = 'batchProgressPanel')
function renderBatchStatus(data, targetPanelId = 'batchProgressPanel')
function renderBatchResultPlayer(data, targetPanelId = 'batchProgressPanel')
function showBatchProgress(batchId, targetPanelId = 'batchProgressPanel')
```

> 注意：`renderBatchResultPlayer(data, targetPanelId)` — 参数顺序是 `data` 在先，`targetPanelId` 在后。

### 4.2 pollBatchStatus — 轮询入口（真实代码）

```javascript
async function pollBatchStatus(batchId, targetPanelId = 'batchProgressPanel') {
  try {
    const resp = await fetch(`/api/voice/batch/${batchId}/status`);
    if (!resp.ok) return;
    const data = await resp.json();
    renderBatchStatus(data, targetPanelId);
  } catch (e) {}
}
```

**关键事实**：`pollBatchStatus` 不判断 overall `data.status`，直接调用 `renderBatchStatus`。进度由 `renderBatchStatus` 中的 `completed_segments / total_segments` 驱动。

### 4.3 renderBatchStatus — 段状态渲染

渲染每个 segment 的状态卡片，segment status 取值：

```javascript
const statusMap = {
  pending: '等待',
  running: '生成中',
  success: '成功',
  failed: '失败',
};
```

### 4.4 renderBatchResultPlayer — 合并音频播放器（真实代码）

```javascript
function renderBatchResultPlayer(data, targetPanelId = 'batchProgressPanel') {
  const dom = getBatchPanelDom(targetPanelId);
  if (!data.merged_audio) {
    dom.playerDiv.style.display = 'none';
    return;
  }
  // 播放器
  audio.src = data.merged_audio.url;
  // 下载链接（优先级）
  let downloadHref = data.merged_audio.url;
  if (data.batch_id) {
    downloadHref = `/api/voice/batch/${encodeURIComponent(data.batch_id)}/download`;
  } else if (data.merged_audio.id) {
    downloadHref = `/api/voice/assets/${encodeURIComponent(data.merged_audio.id)}/download`;
  }
  downloadAudio.href = downloadHref;
}
```

---

## 5. BatchStatus 口径（来自 app/domain/enums.py）

```python
class BatchStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    partial = "partial"   # 部分段失败
    failed = "failed"
```

**没有 `completed` 状态**。`renderBatchResultPlayer` 也不检查 `data.status`，只检查 `data.merged_audio` 是否存在。

---

## 6. merged_audio 字段核验

### 6.1 merged_audio 出现时机

- `merged_audio` 在 batch status 返回且非 null 时出现
- 实际场景中：`status === 'success'` 时有 `merged_audio`
- `status === 'partial'` 时可能有 `merged_audio`（部分合并）
- `status === 'failed'` 时 `merged_audio` 可能为 null
- `status === 'pending' / 'running'` 时 `merged_audio` 不存在

### 6.2 merged_audio 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| url | string | 合并音频 URL（可能是 `/api/voice/assets/{id}/download` 格式，不一定是 `blob:`） |
| id | string | 合并音频 asset_id |

### 6.3 URL 安全

- batch API 返回的 URL 不太可能是 `blob:`（是服务端 asset URL）
- 但仍应用 `isSafeAudioUrl()` 过滤，防止 `javascript:` / `data:` 等危险 scheme
- 下载 URL 策略见第 8 节

---

## 7. segment audio 字段核验

### 7.1 segment 何时可用

- 每个 segment 独立生成，独立状态
- `segment.status` 取值：`pending` | `running` | `success` | `failed`
- `segment.url` / `segment.audio_asset_id` 在 `status === 'success'` 后可用

### 7.2 segment 数量

- longtext：按字数或语义切分，数量不固定
- script：每行一个，数量 = lines.length

### 7.3 是否写入 sample

**B5-MVP1 结论：不按 segment 粒度写入。**

原因：
1. segment 数量多，不适合 sidebar 观察场景
2. 用户目标是合并后的完整音频
3. 后续可在 B5 后续阶段中扩展

---

## 8. 播放 URL vs 下载 URL

### 8.1 播放器 audio.src

```javascript
audio.src = data.merged_audio.url;  // 直接用 merged_audio.url
```

### 8.2 下载按钮 href

```javascript
let downloadHref = data.merged_audio.url;
if (data.batch_id) {
  downloadHref = `/api/voice/batch/${encodeURIComponent(data.batch_id)}/download`;
} else if (data.merged_audio.id) {
  downloadHref = `/api/voice/assets/${encodeURIComponent(data.merged_audio.id)}/download`;
}
```

**下载 URL 优先级**：
1. `batch_id` 存在 → `/api/voice/batch/{batch_id}/download`（服务端合并音频）
2. `merged_audio.id` 存在 → `/api/voice/assets/{merged_audio.id}/download`
3. fallback → `merged_audio.url`

### 8.3 sample_store download_url 策略

B5-MVP1 的 `download_url` 写入应使用**持久化下载入口**：

```
1. data.batch_id 存在 → /api/voice/batch/{batch_id}/download
2. 否则 data.merged_audio.id 存在 → /api/voice/assets/{merged_audio.id}/download
3. 否则 data.merged_audio.url 存在且安全 → data.merged_audio.url
```

> 注意：这是 sample_store 的持久化下载入口策略，不等同于当前播放器 `audio.src` 逻辑（播放器直接用 `merged_audio.url`）。

---

## 9. B5-MVP1 推荐策略

**一次 batch 成功结果 → 写入 1 条 `batch_longtext_merged` / `batch_script_merged` sample**

### 9.1 sample 字段定义（代码核实版）

```javascript
source: 'batch_longtext_merged'      // 或 'batch_script_merged'
job_id: data.batch_id
batch_id: data.batch_id
segment_id: null                    // merged audio，无 segment
asset_id: data.merged_audio?.id || null
download_url: buildBatchMergedDownloadUrl(data)  // 见 8.3 节策略
text_preview:
  - longtext: 从提交上下文保存的 batch text 截断前 100 字
  - script: 从提交上下文保存的 lines 拼接前 100 字
  - fallback: data.segments?.[0]?.text_preview || '批量文本'
provider:
  - longtext: #batchProvider
  - script: #batchScriptProvider
model: null                         // 代码中不存在
voice_id: null                      // 代码中不存在
voice_name: null                    // 代码中不存在
profile_id:
  - longtext: #batchProfile
  - script: 如果所有有效行 profile_id 相同则填该值，否则 null
profile_name: null                  // 代码中不存在
duration_ms: data.total_duration_ms || null
audio_format:
  - longtext: #batchOutputFormat
  - script: #batchScriptOutputFormat
status: 'completed'                  // 这是 sample 的 status 字段，口径固定
tags: ['batch', 'merged']
created_at: Date.now()
```

### 9.2 写入前置条件

```
IF merged_audio 不存在 → 不写 sample
IF merged_audio.id 不存在 → 不写 sample
IF merged_audio.url 不安全 (blob: / javascript: / data:) → 不写 sample
IF data.batch_id 不存在 → 不写 sample  （因为 download_url 需要 batch_id）
```

### 9.3 接入点

`renderBatchResultPlayer(data, targetPanelId)` 内，在确认 `data.merged_audio` 存在且 `data.batch_id` 存在后调用 `safePushBatchSample(source, data, extra)`。

---

## 10. 样本写入策略候选

### 10.1 策略 A：只写 merged audio（推荐 B5-MVP1）

一次 batch → 写入 1 条 merged sample。

**优点**：简单，符合 sidebar 快速回放需求
**缺点**：不保存各 segment

### 10.2 策略 B：写 merged + 每个成功 segment

一次 batch → 写入 1 + N 条 sample。

**优点**：不丢失任何可用音频
**缺点**：sidebar 展示量翻倍

---

## 11. B5 实现边界

### 11.1 B5-MVP1 范围内

- [ ] 新增 `safePushBatchSample(source, data, extra)` — fail-safe 封装
- [ ] `safePushBatchSample` 只通过 `SampleStore.pushSample` 写入
- [ ] `safePushBatchSample` 拒绝 blob: / javascript: / data: URL
- [ ] `safePushBatchSample` 在 `data.batch_id` 或 `merged_audio.id` 缺失时不写入
- [ ] batch_longtext 成功后写入 `batch_longtext_merged` sample
- [ ] batch_script 成功后写入 `batch_script_merged` sample
- [ ] sourceLabel map 新增 `batch_longtext_merged` / `batch_script_merged` 条目
- [ ] sourceLabel map 预留 `batch_longtext_segment` / `batch_script_segment`（暂不实现）

### 11.2 B5-MVP1 范围外

- [ ] 不按 segment 粒度保存
- [ ] 不保存失败段（`status === 'partial'` 或 `'failed'` 不写 sample）
- [ ] 不接轮询进度
- [ ] 不伪造 voice_id / voice_name / model / profile_name
- [ ] 不修改 sample_store.js（schema 已支持）
- [ ] 不修改 sample_sidebar.js（除非后续 sourceLabel 需要补）
- [ ] 不修改后端 API
- [ ] 不修改数据库

---

## 12. B5 测试计划

### 12.1 静态契约测试

**新增** `tests/test_sample_store_batch_integration_static.py`：

| 测试项 | 验证内容 |
|---|---|
| `safePushBatchSample` 函数存在 | `function safePushBatchSample` 存在 |
| `safePushBatchSample` 是 fail-safe | `SampleStore.pushSample` 调用被 try/catch 包裹 |
| `safePushBatchSample` 不直接读写 localStorage | body 内无 `localStorage.getItem/setItem` |
| `safePushBatchSample` 拒绝 blob URL | `isSafeAudioUrl(blobUrl)` 返回 false |
| `safePushBatchSample` 允许 https URL | `isSafeAudioUrl(httpsUrl)` 返回 true |
| `batch_id` 缺失时不写入 | 条件判断存在 |
| `merged_audio.id` 缺失时不写入 | 条件判断存在 |
| `source` 使用 `batch_longtext_merged` | 函数体内有该字符串 |
| `source` 使用 `batch_script_merged` | 函数体内有该字符串 |
| `batch_id` 作为 job_id 写入 | `job_id: batch_id` |
| `segment_id` 写入 null | `segment_id: null` |
| `tags` 包含 `batch` 和 `merged` | `['batch', 'merged']` |
| `download_url` 使用 batch download API | 包含 `/api/voice/batch/` |
| `sourceLabel` 包含 `batch_longtext_merged` | map 内有该 key |
| `sourceLabel` 包含 `batch_script_merged` | map 内有该 key |
| `sourceLabel` 预留 `batch_longtext_segment` | map 内有该 key（注释或空条目） |
| `sourceLabel` 预留 `batch_script_segment` | map 内有该 key（注释或空条目） |

### 12.2 E2E 测试

**mock success E2E**（mock MiniMax，不调用真实 API）：

- `test_batch_longtext_sample_stored_on_success` — 提交 longtext batch，mock 成功响应，验证 sample_store 内有 `batch_longtext_merged` sample
- `test_batch_script_sample_stored_on_success` — 提交 script batch，mock 成功响应，验证 sample_store 内有 `batch_script_merged` sample

**error / edge case E2E**：

- `test_batch_blob_url_not_stored` — mock 返回 blob: URL，验证 sample 未写入
- `test_batch_no_batch_id_not_stored` — mock 无 batch_id，验证 sample 未写入

---

## 13. 是否建议进入 B5-MVP1

**是。** 理由：

1. B5-A0 字段核验已完成，merged audio 字段清晰
2. sample_store.js schema 已支持 `batch_id` / `segment_id`，无需修改
3. B5-MVP1 策略简单（只写 merged audio），风险低
4. 不按 segment 保存，sidebar 展示量可控
5. 与现有 `safePushWorkspaceSample` / `safePushAuditionSample` 模式一致
6. voice_id / voice_name / model / profile_name 字段缺失问题已明确，B5-MVP1 不伪造

**B5-MVP1 推荐命名**：`batch_longtext_merged` / `batch_script_merged`

**后续可扩展方向**：
- B5-MVP2：支持 segment 粒度保存（`batch_longtext_segment` / `batch_script_segment`）
- B5-MVP3：支持 partial 状态保存
- B5-MVP4：支持 batch 进度 sample（显示"生成中 X/Y 段"）

---

## 14. A0-CODE-CHECK 问题处理表

> 上次文档存在多处代码事实级错误，已在本版本中修正。下表记录修正历史。

| # | 问题 | 代码事实 | 原文档错误 | 处理方式 | 是否阻塞 B5-MVP1 |
|---|---|---|---|---|---|
| 1 | longtext DOM id | `#batchText` | 写成 `textarea#batchLongtextText` | 修文档 | 是 |
| 2 | longtext payload 字段 | `segment_strategy`, `max_segment_chars`, `silence_between_ms`, `output_format: 'hex'`, `params` | 缺失或写成 `selectedVoiceId/model` | 修文档 | 是 |
| 3 | longtext voice_id/model 假设 | 代码中不存在 `voice_id` / `voice_name` / `model` | 假设 `selectedVoiceId/model` | 修文档，B5-MVP1 不写这些字段 | 是 |
| 4 | script 数据来源 | `_scriptRows` + `scriptText_{id}` + `scriptProfile_{id}` | 写成 `textarea.split('\n')` | 修文档 | 是 |
| 5 | script payload 字段 | `role`, `text`, `profile_id`, `params`（per-row），无全局 voice/model | 假设全局 `selectedVoiceId/model` | 修文档，B5-MVP1 不写这些字段 | 是 |
| 6 | renderBatchResultPlayer 签名 | `renderBatchResultPlayer(data, targetPanelId)` | 写成 `renderBatchResultPlayer(batchId, data)` | 修文档 | 是 |
| 7 | pollBatchStatus 签名 | `pollBatchStatus(batchId, targetPanelId)` | 写成 `pollBatchStatus(batchId)` | 修文档 | 是 |
| 8 | renderBatchStatus 签名 | `renderBatchStatus(data, targetPanelId)` | 未记录参数顺序 | 修文档 | 是 |
| 9 | startBatchPoll 签名 | `startBatchPoll(batchId, targetPanelId)` | 未记录 targetPanelId 参数 | 修文档 | 是 |
| 10 | BatchStatus 口径 | `pending/running/success/partial/failed` | 写成 `completed/failed` | 修文档 | 是 |
| 11 | 播放器 audio.src | `audio.src = merged_audio.url` | 未区分播放 vs 下载 URL | 拆分说明 | 是 |
| 12 | 下载 URL 策略 | batch_id 优先，其次 merged_audio.id | 未说明 download_url 优先级 | 修文档 | 是 |
| 13 | merged_audio 出现时机 | `status === 'success'` 时有值，`partial` 时可能有 | 写成 `status === 'completed'` | 修文档 | 是 |
| 14 | script profile_id | per-row `scriptProfile_{id}`，不是全局 `selectedProfileName` | 假设全局 `selectedProfileName` | 修文档 | 是 |
