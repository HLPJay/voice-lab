# P13-CREATION-B5-A0：batch sample_store 接入字段核验与方案设计

## 1. 背景

B4 已完成 sample_sidebar UI + workspace/audition sample_store 接入。B5 目标是将 batch_longtext / batch_script 的生成结果接入 sample_store。本阶段（B5-A0）只做代码审查和文档设计，不实现 B5。

---

## 2. 当前 batch_longtext 代码路径

```
用户提交 batchLongtextSubmit (onclick)
  → guardedJsonFetch('/api/voice/batch/submit', {
      mode: 'longtext',
      text: batchText,        // 完整长文本
      voice_id, voice_name,
      provider, model,
      profile_id, profile_name,
    })
  → 成功：_currentBatchId = data.batch_id
  → showBatchProgress + startBatchPoll
  → 轮询：pollBatchStatus(_currentBatchId)
  → renderBatchStatus  // 渲染每段状态
  → renderBatchResultPlayer  // 渲染合并音频播放器
```

**提交参数**（来自 index.html `batchLongtextSubmit`）：
- `text`: textarea#batchLongtextText.value
- `voice_id`: selectedVoiceId
- `voice_name`: selectedVoiceName
- `provider`: selectedProvider
- `model`: selectedModel
- `profile_id`: selectedProfileId
- `profile_name`: selectedProfileName

---

## 3. 当前 batch_script 代码路径

```
用户提交 batchScriptSubmit (onclick)
  → guardedJsonFetch('/api/voice/batch/submit', {
      mode: 'script',
      script: lines[],        // 每行文本数组
      voice_id, voice_name,
      provider, model,
      profile_id, profile_name,
    })
  → 成功：_currentBatchId = data.batch_id
  → showBatchProgress + startBatchPoll
  → 轮询：pollBatchStatus(_currentBatchId)
  → renderBatchStatus  // 渲染每段状态
  → renderBatchResultPlayer  // 渲染合并音频播放器
```

**提交参数**（来自 index.html `batchScriptSubmit`）：
- `script`: textarea#batchScriptText.value.split('\n').filter(l => l.trim())
- `voice_id`: selectedVoiceId
- `voice_name`: selectedVoiceName
- `provider`: selectedProvider
- `model`: selectedModel
- `profile_id`: selectedProfileId
- `profile_name`: selectedProfileName

---

## 4. 共享轮询与结果渲染路径

### 4.1 pollBatchStatus — 轮询入口

```javascript
async function pollBatchStatus(batchId) {
  const data = await guardedJsonFetch(`/api/voice/batch/${batchId}/status`);
  // data = { batch_id, status, total_duration_ms, segments[], merged_audio }
  renderBatchStatus(batchId, data);
  if (data.status === 'completed' || data.status === 'failed') {
    hideBatchProgress();
    renderBatchResultPlayer(batchId, data);
  } else {
    setTimeout(() => pollBatchStatus(batchId), 2000);
  }
}
```

### 4.2 renderBatchStatus — 段状态渲染

渲染每个 segment 的状态卡片：
- `segment.index` — 段序号（1-based）
- `segment.status` — 'pending' | 'processing' | 'completed' | 'failed'
- `segment.text_preview` — 该段文本预览
- `segment.error_message` — 失败原因
- `segment.duration_ms` — 该段时长
- `segment.url` — 该段音频 URL（可能为 null）
- `segment.id` — 该段音频 asset_id（可能为 null）

### 4.3 renderBatchResultPlayer — 合并音频播放器

```javascript
function renderBatchResultPlayer(batchId, data) {
  // data.merged_audio = { url, id }
  // data.total_duration_ms
  // data.segments = [{index, status, text_preview, ...}, ...]
}
```

---

## 5. batch_longtext 字段核验

### 5.1 提交时可用字段

| 字段 | 来源 | 示例值 |
|---|---|---|
| mode | 固定 | 'longtext' |
| text | textarea#batchLongtextText | '这是一段很长的文本...' |
| voice_id | selectedVoiceId | 'mock-voice-001' |
| voice_name | selectedVoiceName | '旁白音色' |
| provider | selectedProvider | 'minimax' |
| model | selectedModel | 'speech-02' |
| profile_id | selectedProfileId | 'profile-xxx' |
| profile_name | selectedProfileName | '我的音色' |

### 5.2 返回数据 batch_id

成功响应：`{ batch_id: 'batch-xxx', ... }`

### 5.3 轮询返回 segments

```json
{
  "batch_id": "batch-xxx",
  "status": "completed",
  "total_duration_ms": 123000,
  "segments": [
    {
      "index": 1,
      "status": "completed",
      "text_preview": "第一段文本...",
      "error_message": null,
      "duration_ms": 30000,
      "url": "https://...",
      "id": "asset-001"
    },
    {
      "index": 2,
      "status": "completed",
      "text_preview": "第二段文本...",
      "error_message": null,
      "duration_ms": 25000,
      "url": "https://...",
      "id": "asset-002"
    }
  ],
  "merged_audio": {
    "url": "https://...",
    "id": "merged-asset-xxx"
  }
}
```

---

## 6. batch_script 字段核验

### 6.1 提交时可用字段

| 字段 | 来源 | 示例值 |
|---|---|---|
| mode | 固定 | 'script' |
| script | lines[] | ['第一句台词', '第二句台词', ...] |
| voice_id | selectedVoiceId | 'mock-voice-001' |
| voice_name | selectedVoiceName | '角色音色' |
| provider | selectedProvider | 'minimax' |
| model | selectedModel | 'speech-02' |
| profile_id | selectedProfileId | 'profile-xxx' |
| profile_name | selectedProfileName | '我的音色' |

### 6.2 返回数据 batch_id

同 batch_longtext。

### 6.3 轮询返回 segments

同 batch_longtext 结构。script 每行对应一个 segment。

---

## 7. merged audio 字段核验

### 7.1 merged_audio 出现时机

- `merged_audio` 只在 `status === 'completed'` 时有值
- `status === 'failed'` 时 `merged_audio` 可能为 null 或空对象
- `status === 'processing'` 时 `merged_audio` 不存在

### 7.2 merged_audio 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| url | string | 合并音频下载 URL（可能是 blob: 或 https:） |
| id | string | 合并音频 asset_id |

### 7.3 URL 安全问题

- `blob:` URL 不得写入 sample（blob URL 会失效且有 XSS 风险）
- `javascript:` / `data:` URL 不得写入 sample
- 使用 `isSafeAudioUrl(url)` 过滤

### 7.4 total_duration_ms

- 合并音频总时长
- 可能不存在或为 null

---

## 8. segment audio 字段核验

### 8.1 segment 何时可用

- 每个 segment 独立生成，独立状态
- segment.url / segment.id 在该 segment `status === 'completed'` 后可用
- 失败 segment 的 url / id 可能为 null

### 8.2 segment 数量

- longtext：按字数或语义切分，数量不固定
- script：每行一个，数量 = lines.length

### 8.3 是否写入 sample

**B5-MVP1 结论：不按 segment 粒度写入。**

原因：
1. segment 数量多，不适合 sidebar 观察场景（sidebar 重在快速回放，不是逐段分析）
2. 用户目标是合并后的完整音频
3. 后续可在 B5 后续阶段中扩展

---

## 9. 样本写入策略候选

### 9.1 策略 A：只写 merged audio（推荐 B5-MVP1）

一次 batch 成功 → 写入 1 条 sample：
- `source`: `batch_longtext_merged` / `batch_script_merged`
- `job_id`: batch_id
- `asset_id`: merged_audio.id
- `download_url`: merged_audio.url
- `text_preview`: 前 100 字
- `duration_ms`: total_duration_ms
- `tags`: `['batch', 'merged']`

**优点**：简单，符合 sidebar 快速回放需求
**缺点**：不保存失败段，不保存各 segment

### 9.2 策略 B：写 merged + 每个成功 segment

一次 batch 成功 → 写入 1 + N 条 sample（merged + 每个成功 segment）

**优点**：不丢失任何可用音频
**缺点**：sidebar 展示量翻倍，segment 多时干扰观察

### 9.3 策略 C：写 merged + 用户选中的 segment

依赖用户交互选择要保存的 segment

**优点**：用户主导
**缺点**：需要额外 UI，batch 场景用户通常直接用合并结果

---

## 10. 推荐 B5 MVP 策略

**采用策略 A：只写 merged audio**

一次 batch_longtext 成功结果 → 写入 1 条 `batch_longtext_merged` sample
一次 batch_script 成功结果 → 写入 1 条 `batch_script_merged` sample

### 10.1 sample 字段定义

```javascript
source: 'batch_longtext_merged'      // 或 'batch_script_merged'
job_id: batch_id                    // 使用 batch_id 作为 job_id
batch_id: batch_id
segment_id: null                    // merged audio，无 segment
asset_id: merged_audio.id || null
download_url: merged_audio.url     // 必须通过 isSafeAudioUrl 验证
text_preview: 前100字               // longtext: batchText.slice(0,100)
                                   // script: lines.slice(0,3).join('\n').slice(0,100)
provider: selectedProvider
model: selectedModel || null
voice_id: selectedVoiceId
voice_name: selectedVoiceName
profile_id: selectedProfileId || null
profile_name: selectedProfileName || null
duration_ms: total_duration_ms || merged_audio.duration_ms || null
audio_format: null                  // batch API 未返回
status: 'completed'
tags: ['batch', 'merged']
created_at: Date.now()
```

### 10.2 写入前置条件

```
IF merged_audio.id 不存在 → 不写 sample
IF merged_audio.url 不存在 → 不写 sample
IF merged_audio.url 是 blob: → 不写 sample
IF batch status !== 'completed' → 不写 sample
```

### 10.3 接入点

`renderBatchResultPlayer` 函数内，在确认 merged_audio 可用后调用 `safePushBatchSample`。

---

## 11. B5 实现边界

### 11.1 B5-MVP1 范围内

- [ ] 新增 `safePushBatchSample(source, data, extra)` — fail-safe 封装
- [ ] `safePushBatchSample` 只通过 `SampleStore.pushSample` 写入
- [ ] `safePushBatchSample` 拒绝 blob: URL
- [ ] `safePushBatchSample` 在 merged_audio 不可用时不写入
- [ ] batch_longtext 成功后写入 `batch_longtext_merged` sample
- [ ] batch_script 成功后写入 `batch_script_merged` sample
- [ ] sourceLabel map 新增 `batch_longtext_merged` / `batch_script_merged` 条目
- [ ] sourceLabel map 预留 `batch_longtext_segment` / `batch_script_segment`（暂不实现）

### 11.2 B5-MVP1 范围外

- [ ] 不按 segment 粒度保存
- [ ] 不保存失败段
- [ ] 不接轮询进度
- [ ] 不修改 sample_store.js（无需修改，schema 已支持）
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
| merged_audio.id 不存在时不写入 | 条件判断存在 |
| merged_audio.url 是 blob: 时不写入 | 条件判断存在 |
| `source` 使用 `batch_longtext_merged` | 函数体内有该字符串 |
| `source` 使用 `batch_script_merged` | 函数体内有该字符串 |
| `batch_id` 作为 job_id 写入 | `job_id: batch_id` |
| `segment_id` 写入 null | `segment_id: null` |
| `tags` 包含 `batch` 和 `merged` | `['batch', 'merged']` |
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
- `test_batch_no_merged_audio_not_stored` — mock 无 merged_audio，验证 sample 未写入

---

## 13. 是否建议进入 B5-MVP1

**是。** 理由：

1. B5-A0 字段核验已完成，merged audio 字段清晰
2. sample_store.js schema 已支持 `batch_id` / `segment_id`，无需修改
3. B5-MVP1 策略简单（只写 merged audio），风险低
4. 不按 segment 保存，sidebar 展示量可控
5. 与现有 `safePushWorkspaceSample` / `safePushAuditionSample` 模式一致

**B5-MVP1 推荐命名**：`batch_longtext_merged` / `batch_script_merged`

**后续可扩展方向**：
- B5-MVP2：支持 segment 粒度保存（`batch_longtext_segment` / `batch_script_segment`）
- B5-MVP3：支持失败 segment 保存
- B5-MVP4：支持 batch 进度 sample（显示"生成中 X/Y 段"）
