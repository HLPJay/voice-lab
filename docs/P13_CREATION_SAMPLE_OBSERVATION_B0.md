# P13-CREATION-B0：样本观察侧边栏最小实现方案设计

## 1. 背景

A0 / A0-CHECK 已完成。P13-CREATION-A0 确立了"样本观察侧边栏"的产品定义和 MVP 范围；A0-CHECK 核验并修正了字段描述，将过于确定的字段级承诺降级为"待 B0 核验"。

B0 的目标是：在 A0 基础上，把后续最小实现路径设计清楚——包括模块职责、数据结构、字段来源、接入点顺序和测试策略。

**B0 不写代码，只做设计文档。** B1 才开始实现 sample_store.js。

## 2. 当前阶段边界

- 不改业务代码
- 不新增 JS 模块（不新建 sample_store.js / sample_sidebar.js）
- 不改 index.html
- 不改后端 API
- 不改数据库结构
- 不调用真实 MiniMax
- 不进入 B1 / B2 / B3 / B4 / B5 实现

## 3. B0 设计目标

B0 需要回答：

1. `sample_store.js` 应该提供哪些接口，职责边界是什么
2. `localStorage` 数据结构如何落地，key 是什么
3. `sample` metadata 字段从哪里来（每种生成链路精确到函数级别）
4. `sample_sidebar.js` 后续如何接入，职责边界是什么
5. 哪些生成链路先接入，哪些延后
6. 如何设计测试以确保不破坏现有生成链路

## 4. 最小 MVP 架构

```
生成结果 / 试听记录 / 批量结果
        ↓
sample_store.js（数据写入）
        ↓
localStorage: voice_lab_recent_samples_v1
        ↓
sample_sidebar.js（数据读取 + UI 渲染）
        ↓
右侧最近样本面板（workspace tab 右侧，窄屏折叠为浮动面板）
```

**设计原则：**
- `sample_store.js` 只负责数据读写，不涉及 UI
- `sample_sidebar.js` 只负责 UI 渲染和交互，不涉及数据存储
- 生成链路只在结果渲染完成后调用 `SampleStore.pushSample()`
- 不改变现有 payload 结构
- 不改变现有 UI 主流程
- 不写入 `window.recentJobs` 或 `localStorage['recentJobs']`

## 5. sample_store.js 设计

### 5.1 文件路径

```
app/static/js/sample_store.js
```

### 5.2 接口设计

```js
window.SampleStore = {
  // 写入：将一个 sample 追加到 localStorage 顶部（unshift）
  pushSample(sample) {},

  // 读取：返回全部样本，按 created_at 倒序
  getSamples() {},

  // 删除：按 sample_id 删除单条
  deleteSample(sampleId) {},

  // 清空：清空全部样本
  clearSamples() {},

  // 规范化：校验字段，补默认值，截断 text_preview
  normalizeSample(input) {},

  // 容量裁剪：超过 200 条时删除最旧记录
  trimSamples(samples) {},
}
```

### 5.3 接口职责

| 方法 | 职责 | 副作用 |
|---|---|---|
| `pushSample(sample)` | 规范化 → 插入数组顶部 → 裁剪 → 写 localStorage | 写 `voice_lab_recent_samples_v1` |
| `getSamples()` | 从 localStorage 读取并解析，失败时返回 `[]` | 只读 |
| `deleteSample(sampleId)` | 过滤掉指定 id，写回 localStorage | 写 |
| `clearSamples()` | 写入 `[]` 到 localStorage | 写 |
| `normalizeSample(input)` | 校验字段、补默认值、截断 text_preview、生成 uuid | 无 |
| `trimSamples(samples)` | 如果超过 200 条，pop 最旧记录 | 无（由 pushSample 调用时再写） |

### 5.4 localStorage 策略

- **key**：`voice_lab_recent_samples_v1`
- **最大保存 200 条**，超出时删除最旧记录（按 `created_at` 升序 pop）
- **按 `created_at` 倒序**返回（最新在前）
- **`text_preview` 最大 100 字符**，超出截断加 `…`
- **不保存 audio blob**
- **不保存完整长文本**（只存 preview）
- **不保存 API key / 敏感 payload**
- **不写入 `recentJobs`**（语义隔离）
- **malformed JSON 自动恢复**为 `[]`

### 5.5 normalizeSample 规范

```js
function normalizeSample(input) {
  return {
    sample_id: input.sample_id || crypto.randomUUID(),
    created_at: input.created_at || new Date().toISOString(),
    source: input.source || 'unknown',
    job_id: input.job_id || null,
    batch_id: input.batch_id || null,
    segment_id: input.segment_id || null,
    asset_id: input.asset_id || null,
    download_url: input.download_url || null,
    text_preview: (input.text_preview || '').substring(0, 100) + ((input.text_preview || '').length > 100 ? '…' : ''),
    profile_id: input.profile_id || null,
    profile_name: input.profile_name || null,
    provider: input.provider || null,
    model: input.model || null,
    voice_id: input.voice_id || null,
    voice_name: input.voice_name || null,
    duration_ms: input.duration_ms || null,
    audio_format: 'mp3',
    status: input.status || 'completed',
    tags: Array.isArray(input.tags) ? input.tags : [],
  };
}
```

## 6. sample 数据结构

```json
{
  "sample_id": "local uuid v4",
  "created_at": "2026-05-15T10:30:00.000Z",
  "source": "workspace_sync | workspace_async | workspace_stream | workspace_variant | audition | batch_longtext | batch_script | clone_preview | design_preview | import_preview",
  "job_id": null,
  "batch_id": null,
  "segment_id": null,
  "asset_id": null,
  "download_url": null,
  "text_preview": "前 100 字符，超出截断",
  "profile_id": null,
  "profile_name": null,
  "provider": null,
  "model": null,
  "voice_id": null,
  "voice_name": null,
  "duration_ms": null,
  "audio_format": "mp3",
  "status": "completed | partial | failed",
  "tags": []
}
```

### 字段必填性与来源说明

| 字段 | 必填 | 来源说明 |
|---|---|---|
| `sample_id` | 是（自动生成） | `crypto.randomUUID()` |
| `created_at` | 是（自动生成） | `new Date().toISOString()` |
| `source` | 是（调用方指定） | 标识样本来自哪个生成链路 |
| `job_id` | 推荐 | workspace async/sync 可取；batch segment 不一定有 |
| `batch_id` | 可选 | batch_longtext/script 有 |
| `segment_id` | 可选 | batch segment 有 |
| `asset_id` | 推荐 | `audio_asset.id` 或 `audio_asset_id`；可构造 download URL |
| `download_url` | 可选 | `/api/voice/assets/{asset_id}/download`；batch 用 `/api/voice/batch/{batch_id}/download` |
| `text_preview` | 是（自动截断） | 来自原始输入 text，强制截断 100 字符 |
| `profile_id` | 推荐 | 来自 DOM 或请求上下文 |
| `profile_name` | 可选 | display only，DOM 可取 |
| `provider` | 推荐 | 请求上下文或返回结果 |
| `model` | 可选 | 返回结果可能有 |
| `voice_id` | 可选 | clone/design/import 有 |
| `voice_name` | 可选 | display only |
| `duration_ms` | 推荐 | `audio_asset.duration_ms` / `durationMs` |
| `audio_format` | 是（固定值） | 固定为 `'mp3'` |
| `status` | 是（默认 completed） | 只有 batch segment 可能为 `partial` / `failed` |
| `tags` | 是（默认空数组） | 低频功能，B4 UI 暂不实现 |

## 7. 字段来源核验（精确到函数级别）

### 7.1 workspace sync

**入口函数**：`renderResults(data, isVariant = false)`（index.html 内联）

**成功路径**：当 `isResultSuccessStatus(data.status)` 为 true 且 `data.audio_asset` 存在

**sample metadata 来源**：

| 字段 | 来源 | 备注 |
|---|---|---|
| `text_preview` | 调用方上下文（已知） | 截断 100 字符 |
| `profile_id` | 调用方上下文（已知） | from DOM `#profileSelect` |
| `provider` | 调用方上下文（已知） | from DOM `#providerSelect` |
| `model` | `data.model` | 可能有 |
| `job_id` | `data.job_id` 或 `data.id` | `extractJobId()` |
| `asset_id` | `data.audio_asset.id` | `extractAudioAssetId()` |
| `duration_ms` | `data.audio_asset.duration_ms` | |
| `download_url` | `/api/voice/assets/{asset_id}/download` | 构造 |
| `source` | `'workspace_sync'` | 调用方指定 |

**push 时机**：在 `renderResults()` 的成功分支中，result HTML 写入 `resultsArea` 后调用 `SampleStore.pushSample(...)`。

---

### 7.2 workspace async

**入口函数**：`handleGenerate()` → `startAsyncPolling(jobId)` → 轮询成功回调

**成功路径**：轮询 `/api/voice/jobs/{job_id}` 返回 `status === 'success'` 且 `audio_asset` 存在

**sample metadata 来源**：

| 字段 | 来源 | 备注 |
|---|---|---|
| `text_preview` | 调用方上下文（已知） | 截断 100 字符 |
| `profile_id` | 调用方上下文（已知） | from DOM |
| `provider` | 调用方上下文（已知） | from DOM |
| `model` | `pollData.model` | 可能有 |
| `job_id` | `jobId`（轮询变量） | 已知 |
| `asset_id` | `pollData.audio_asset.id` | 轮询返回 |
| `duration_ms` | `pollData.audio_asset.duration_ms` | |
| `download_url` | `/api/voice/assets/{asset_id}/download` | 构造 |
| `source` | `'workspace_async'` | 调用方指定 |

**push 时机**：在轮询返回 `success` 状态时，调用 `SampleStore.pushSample(...)`。

**注意**：submit 阶段不 push，只有 success 后才 push。

---

### 7.3 workspace stream

**入口函数**：`renderStreamResult(completed, audioChunks)`（index.html 内联）

**sample metadata 来源**：

| 字段 | 来源 | 备注 |
|---|---|---|
| `text_preview` | 调用方上下文（已知） | 截断 100 字符 |
| `profile_id` | 调用方上下文（已知） | from DOM |
| `provider` | `completed.provider` | 可能有 |
| `model` | `completed.model` | 可能有 |
| `job_id` | `completed.job_id` | |
| `asset_id` | `completed.audio_asset?.id` | 只有 server asset 时存在 |
| `duration_ms` | `completed.audio_asset?.duration_ms` 或 `completed.total_duration_ms` | |
| `download_url` | `completed.audio_asset?.id` → 构造 URL | 只有 server asset 时可用 |
| `source` | `'workspace_stream'` | 调用方指定 |

**blob URL vs server asset 策略（B0 决策）：**
- 流式生成的播放使用 **blob URL**（`URL.createObjectURL(blob)`），刷新页面后失效
- `renderStreamResult` 中 `completed.audio_asset` 如果存在（server 也保存了），则 `download_url` 使用 server URL
- 如果 `completed.audio_asset` 不存在，则 `asset_id = null`，`download_url = null`
- **不保存 blob URL 到 sample**（B0 明确决策：blob URL 只用于当前播放，不持久化）
- **push 时机**：`renderStreamResult()` 执行完成后，且 `completed.audio_asset` 存在时

---

### 7.4 workspace variants

**入口函数**：`renderResults(data, isVariant = true)`（index.html 内联）

**成功路径**：每个 `v.audio_asset_id` 存在的 variant 都是一个独立 sample

**sample metadata 来源**：

| 字段 | 来源 | 备注 |
|---|---|---|
| `text_preview` | 调用方上下文（已知） | 截断 100 字符 |
| `profile_id` | 调用方上下文（已知） | from DOM |
| `provider` | 调用方上下文（已知） | from DOM |
| `model` | `v.model` 或 `data.model` | 可能有 |
| `job_id` | `data.job_id`（父任务） | |
| `asset_id` | `v.audio_asset_id` | 每个 variant 独立 |
| `duration_ms` | `v.duration_ms` | |
| `download_url` | `/api/voice/assets/{v.audio_asset_id}/download` | 构造 |
| `source` | `'workspace_variant'` | 调用方指定 |

**push 时机**：在 `renderResults()` 的 variants 分支中，遍历 `data.variants`，对每个有 `audio_asset_id` 的 variant 调用一次 `SampleStore.pushSample(...)`。

**每个 variant 都是独立 sample**，variant index 可以在 `tags` 或后续扩展字段中记录（第一版 MVP 不记录）。

---

### 7.5 audition_records

**入口**：`renderResults()` 中成功分支，`window._auditionRecords.push({...})`

**audition_records.js 当前字段**（`app/static/js/audition_records.js`）：

| 字段 | 存在 | 样本可用性 |
|---|---|---|
| `text` | ✅ | 可作为 `text_preview` |
| `voiceId` | ✅ | 可作为 `voice_id` |
| `voiceName` | ✅ | 可作为 `voice_name` |
| `durationMs` | ✅ | 可作为 `duration_ms` |
| `audioUrl` | ✅ | 可作为 `download_url` |
| `timestamp` | ✅ | 可作为 `created_at` |
| `asset_id` | ❌ | 缺失 |
| `job_id` | ❌ | 缺失 |
| `provider` | ❌ | 缺失 |
| `source` | ❌ | 缺失（不知道是 clone/design/workspace） |

**audition_records 接入策略（B3）**：
- B3 阶段在 `window._auditionRecords.push({...})` 后同步调用 `SampleStore.pushSample({...})`
- `source` 字段补为 `'audition'`
- 如果 `audioUrl` 是 backend URL（以 `/api/` 或 `http` 开头），则作为 `download_url`
- 如果是 blob URL（以 `blob:` 开头），则 `download_url = null`（audition 不应使用 blob）
- `asset_id` 缺失，尝试从 `audioUrl` 提取（如果 URL 包含 asset_id 路径）

**注意**：audition_records.js 本身不变，只在调用方增加 `SampleStore.pushSample()` 调用。

---

### 7.6 batch_longtext

**B5 才接入，B0 只确认接入点。**

**关键函数**：`renderBatchStatus(data, targetPanelId)` → 在 `data.status === 'success' || data.status === 'partial'` 时

**segment 真实字段**（从 index.html 内联代码反向核验）：

| 字段 | 存在 | 样本可用性 |
|---|---|---|
| `seg.index` | ✅ | 可作为 `segment_id` |
| `seg.text_preview` | ✅ | 可作为 `text_preview` |
| `seg.status` | ✅ | 只 push `success` 状态 |
| `seg.duration_ms` | ✅ | 可作为 `duration_ms` |
| `seg.error_message` | ✅ | `failed` 时可记录 |
| `seg.role` | ❌ | longtext 无 role 字段 |
| `seg.audio_asset.id` | ❓ 待核验 | segment 级别 asset 需 B0 确认 |

**merged_audio 字段**（从 `renderBatchResultPlayer` 反向核验）：

| 字段 | 存在 | 样本可用性 |
|---|---|---|
| `data.merged_audio.url` | ✅ | 可作为 `download_url` |
| `data.merged_audio.id` | ❓ 待核验 | download URL 优先用 `/api/voice/batch/{batch_id}/download` |
| `data.total_duration_ms` | ✅ | 可作为 `duration_ms` |
| `data.batch_id` | ✅ | |

**B5 接入策略**：
- 在 `renderBatchStatus()` 成功后，遍历 `data.segments`
- 只 push `seg.status === 'success'` 的 segment
- 对每个成功 segment 调用 `SampleStore.pushSample({..., source: 'batch_longtext', batch_id: data.batch_id, segment_id: seg.index, ...})`
- `merged_audio` 单独作为一个 sample（`source: 'batch_longtext_merged'`）

---

### 7.7 batch_script

**B5 才接入，B0 只确认接入点。**

**关键函数**：同 batch_longtext，使用 `batchScriptProgressPanel`

**segment 真实字段**（从 index.html 内联代码反向核验）：

| 字段 | 存在 | 样本可用性 |
|---|---|---|
| `seg.index` | ✅ | 可作为 `segment_id` |
| `seg.text_preview` | ✅ | 可作为 `text_preview` |
| `seg.status` | ✅ | 只 push `success` 状态 |
| `seg.duration_ms` | ✅ | 可作为 `duration_ms` |
| `seg.role` | ✅ | 可记录角色信息 |
| `seg.audio_asset` | ❓ 待核验 | 同 batch_longtext |

**B5 接入策略**：
- 同 batch_longtext
- `source` 记为 `'batch_script'`
- `seg.role` 存入 `tags` 或扩展字段（第一版 `tags` 暂不使用，可考虑在 `text_preview` 前缀加角色名）

---

### 7.8 history

**结论：第一版 MVP 不从 history 反向生成 sample。**

`history.js` 从 `/api/voice/jobs` 分页获取 VoiceJob 记录，是后端持久化数据。

**为什么不进第一版**：
- history 是"追溯"入口，不是"创作过程中快速观察"入口
- history 需要翻页，不适合作为"最近样本"面板
- history 强依赖后端 API

**未来扩展方向（不进 B0-B5）**：
- 在 history tab 中增加"加入样本"按钮，用户手动将 history 记录加入样本
- 或在 B 阶段之后另立项目做作品库

---

### 7.9 clone / design / import preview audio

**入口函数**：
- `handleCloneVoice()` → `resultsEl.innerHTML = html` 成功后
- `handleDesignVoice()` → `resultsEl.innerHTML = html` 成功后
- `handleImportRemoteVoice()` → `resultsEl.innerHTML = html` 成功后

**clone_preview 字段**：

| 字段 | 来源 | 备注 |
|---|---|---|
| `voice_id` | `data.voice_id` | ✅ |
| `demo_audio_url` | `data.demo_audio_url` | ✅ server URL |
| `demo_audio_duration_ms` | `data.demo_audio_duration_ms` | ✅ |
| `text_preview` | 调用方（preview_text） | 截断 |
| `provider` | 调用方 | from DOM |
| `source` | `'clone_preview'` | 调用方指定 |

**design_preview 字段**：

| 字段 | 来源 | 备注 |
|---|---|---|
| `voice_id` | `data.voice_id` | ✅ |
| `trial_audio_url` | `data.trial_audio_url` | ✅ server URL |
| `trial_audio_duration_ms` | `data.trial_audio_duration_ms` | ✅ |
| `text_preview` | 调用方（previewText） | 截断 |
| `provider` | 调用方 | from DOM |
| `source` | `'design_preview'` | 调用方指定 |

**import_preview 字段**：

| 字段 | 来源 | 备注 |
|---|---|---|
| `voice_id` | `data.provider_voice_id` | ✅ |
| `audio_asset.url` | `data.audio_asset.url` | ✅ server URL |
| `audio_asset.duration_ms` | `data.audio_asset.duration_ms` | ✅ |
| `text_preview` | 调用方（previewText） | 截断 |
| `provider` | 调用方 | from DOM |
| `source` | `'import_preview'` | 调用方指定 |

**注意**：clone/design/import 的预览音频是在这些 tab 的"成功结果区"展示的，不是 workspace tab 中。这三个 preview 音频的样本 push 时机是：结果 HTML 写入后（`resultsEl.innerHTML = html` 成功后），立即调用 `SampleStore.pushSample(...)`。

## 8. sample_sidebar.js 设计

### 8.1 文件路径

```
app/static/js/sample_sidebar.js
```

### 8.2 职责边界

**负责**：
- 调用 `SampleStore.getSamples()` 获取样本列表
- 渲染 sample card（来源 badge、文本预览、音色、时长、创建时间）
- 播放（使用 `download_url` 作为 `<audio src>`）
- 下载（`<a href={download_url} download>`）
- 复制文本（`navigator.clipboard.writeText`）
- 回填输入框（填充 workspace 的 `#textInput`）
- 删除单条（调用 `SampleStore.deleteSample(sampleId)`，重新渲染）
- 清空列表（调用 `SampleStore.clearSamples()`，重新渲染）
- 空状态渲染

**不负责**：
- 不请求后端（只读 SampleStore）
- 不做复杂筛选/搜索（第一版 MVP 不做）
- 不做作品库
- 不做多用户同步
- 不做标签管理（`tags` 字段 B4 暂不使用）

### 8.3 UI 信息结构

每个 sample card 展示：

| 信息 | 字段 | 样式 |
|---|---|---|
| 来源类型 | `source` | 小 badge，颜色按 source 区分 |
| 文本预览 | `text_preview` | 单行，hover 显示完整 |
| 音色/人设 | `profile_name` 或 `voice_id` | 小标签 |
| 时长 | `duration_ms` | 格式 `X.Xs` |
| 创建时间 | `created_at` | 格式 `HH:mm` 或"今天 HH:mm" |
| 播放 | `download_url` | `<audio>` 控件 |
| 下载 | `download_url` | `<a download>` 按钮 |
| 复制文本 | `text_preview` | 按钮 |
| 回填输入框 | `text_preview` | 按钮 |
| 删除 | — | 按钮调用 deleteSample |

### 8.4 渲染逻辑

```js
window.renderSampleSidebar = function() {
  var samples = window.SampleStore.getSamples();
  var container = document.getElementById('sampleSidebarRoot');
  if (!container) return;
  if (samples.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无最近样本</div>';
    return;
  }
  container.innerHTML = samples.map(function(s) { return renderSampleCard(s); }).join('');
};
```

## 9. UI 容器设计

**B4 才修改 index.html。**

### 9.1 建议容器

在 index.html 的 workspace tab 内容区新增：

```html
<div id="sampleSidebarRoot"></div>
```

### 9.2 位置策略

- **桌面端（≥1200px）**：position 固定在 workspace 内容区右侧，width 约 320px，不挤压主输入区
- **窄屏（<1200px）**：隐藏 sidebar，workspace 顶部显示"最近样本"图标按钮，点击展开浮动面板（`position: fixed`，`z-index` 高于主内容）
- 不修改现有 tab 结构
- 不替代 history tab

### 9.3 样式隔离

sidebar UI 样式使用独立 class 前缀（如 `.sample-card`、`.sample-badge`），不污染全局样式。

## 10. 实施分阶段

### B1：sample_store.js

- 新建 `app/static/js/sample_store.js`
- 实现 `SampleStore` 全部方法
- 不接 UI
- 不接任何生成链路
- **测试**：E2E 验证 localStorage 读写正确、200 条容量上限、text_preview 截断、malformed JSON 自动恢复

### B2：workspace 结果接入

- 在 `renderResults()` sync 成功分支调用 `SampleStore.pushSample()`
- 在 `handleGenerate()` async 轮询成功分支调用
- 在 `renderStreamResult()` 成功且 `completed.audio_asset` 存在时调用
- 在 `renderResults()` variants 分支，对每个有 `audio_asset_id` 的 variant 调用
- **测试**：E2E behavioral 验证 pushSample 被调用

### B3：audition_records 接入

- 在 `renderResults()` 成功分支，`window._auditionRecords.push(...)` 后同步调用 `SampleStore.pushSample()`
- 保持原 audition_records 行为不变
- **测试**：E2E 验证 audition 成功后 sample 被 push

### B4：sidebar UI

- 新建 `app/static/js/sample_sidebar.js`
- 在 index.html 新增 `#sampleSidebarRoot` 容器
- 实现 `renderSampleSidebar()`
- 支持播放 / 下载 / 复制 / 回填 / 删除 / 清空
- **测试**：E2E 验证 sidebar 渲染、交互

### B5：batch_longtext / batch_script 接入

- 在 `renderBatchStatus()` 成功分支遍历 segments，push completed segment
- merged_audio 单独作为一个 sample
- **容量控制**：单个 batch 最多 push 20 个 segment sample（防止超长文本 batch 污染）
- **测试**：E2E 验证 batch 完成后 sample 被 push

### CHECK：完整验收

- 前端 E2E 全量通过
- 不引入新的 highRisk 未覆盖路径
- 不破坏现有生成链路
- 文档收口

## 11. 测试策略

### B1 测试（sample_store.js）

| 测试项 | 预期行为 |
|---|---|
| `pushSample` 写入 localStorage | key=`voice_lab_recent_samples_v1`，数组非空 |
| `getSamples` 读取 | 返回数组，按 created_at 倒序 |
| 超过 200 条 | 第 201 条 push 时，最旧一条被删除 |
| `text_preview` 截断 | 超过 100 字符的内容被截断加 `…` |
| malformed JSON | localStorage 被意外破坏时返回 `[]`，不抛错 |
| `deleteSample` | 指定 id 被删除，其余保留 |
| `clearSamples` | localStorage 写入 `[]` |

### B2 测试（workspace 接入）

| 测试项 | 预期行为 |
|---|---|
| sync 生成成功 | sidebar 出现新 sample，source=`workspace_sync` |
| async 生成成功 | sidebar 出现新 sample，source=`workspace_async` |
| stream 有 server asset | sidebar 出现新 sample，source=`workspace_stream` |
| stream 无 server asset | 不 push sample |
| variants 生成 | sidebar 出现多个 sample，每个 variant 一个 |

### B3 测试（audition 接入）

| 测试项 | 预期行为 |
|---|---|
| workspace 试听成功 | sidebar 出现新 sample，source=`audition` |

### B4 测试（sidebar UI）

| 测试项 | 预期行为 |
|---|---|
| 空状态 | 显示"暂无最近样本" |
| sample card 渲染 | 显示 source badge、text_preview、音色、时长、播放控件 |
| 播放 | 点击播放按钮，`<audio>` 开始播放 |
| 下载 | 点击下载，浏览器下载文件 |
| 复制文本 | 点击复制，clipboard 有内容 |
| 回填输入框 | 点击回填，`#textInput` 被填充 |
| 删除单条 | 点击删除，sample 从列表消失 |
| 清空列表 | 点击清空，列表为空 |

### B5 测试（batch 接入）

| 测试项 | 预期行为 |
|---|---|
| batch_longtext 成功 | 每个 success segment 生成一个 sample，merged_audio 生成一个 sample |
| batch_script 成功 | 同上，source=`batch_script` |
| 超大 batch | 最多写入 20 个 segment sample |

**B0 不跑测试，只设计测试范围。B1 开始写 E2E。**

## 12. 风险与约束

| 约束 | 原因 |
|---|---|
| 不要复用 `recentJobs` | 语义不同：恢复任务 vs 观察样本 |
| 不要保存 blob URL | blob 在页面刷新后失效，保存无意义 |
| 不要保存完整长文本 | batch_longtext 可能数万字，撑爆 localStorage |
| 不要在 B1 就动生成链路 | B1 只建 store，隔离验证 |
| 不要一次性接入 batch | batch segment 数量不确定，需要容量控制 |
| 不要直接改 history | history 是后端持久化，不适合作为"最近样本" |
| 不要让 sidebar 干扰主流程 | 窄屏折叠，不挤压输入区 |
| 不要引入后端状态 | 第一版纯前端 localStorage |
| 不要在 stream 无 server asset 时 push | 无持久化 URL 的 sample 价值低 |

## 13. B0 结论

**可以进入 B1。**

具体结论：

1. **B1 只做 sample_store.js**，不接 UI，不接任何生成链路，独立验证 localStorage 行为
2. **B2 再接 workspace**（sync / async / stream server asset / variants）
3. **B3 再接 audition_records**
4. **B4 再做 sidebar UI**（sample_sidebar.js + index.html 容器）
5. **B5 再接 batch**（batch_longtext / batch_script，容量上限 20 条/批次）
6. **history 不进入第一版 MVP**（未来可作为追溯入口）
7. **clone / design / import preview** 在 B2 阶段一并接入（它们的 preview 成功回调与 workspace 类似）

**第一版边界明确**：纯前端 localStorage、无后端依赖、不改生成链路、不做作品库、不做多用户。

---

*B0 阶段：最小实现方案设计完成，不实现功能。后续 B1 开始实现 sample_store.js。*
