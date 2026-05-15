# P12-USAGE-FIX5-A0：音频时长显示审查

**审查时间：** 2026-05-15

---

## 1. 音频播放点总览表

| 场景 | 文件 / 函数 | audio src 来源 | 是否有 asset_id | 是否有 duration_ms | 是否展示总时长 | 当前风险 |
|---|---|---|---|---|---|---|
| 单条同步结果 | index.html `renderResults()` | `/api/voice/assets/${audio.id}/download` | ✅ `audio.id` | ❌ 不展示 | ❌ 依赖浏览器 metadata | 低（浏览器 metadata 不稳定） |
| 异步轮询结果 | index.html `renderAsyncResult()` | `/api/voice/assets/${audio.id}/download` | ✅ `audio.id` | ❌ 不展示 | ❌ 依赖浏览器 metadata | 低 |
| 流式生成结果 | index.html `renderStreamResult()` | `blobUrl` + `asset.id` | ✅ `asset.id` 存在时 | ⚠️ `total_duration_ms` 在 metadata 显示，但用 ms 单位 | 部分（显示在结果描述中，单位 ms） |
| 批量合并音频播放器 | index.html `renderBatchResultPlayer()` | `data.merged_audio.url` | ✅ `data.merged_audio.id` | ❌ `total_duration_ms` 有但未展示 | ❌ 依赖浏览器 metadata | **中**（total_duration_ms 有但不显示） |
| 批量进度表每行时长 | index.html `renderBatchStatus()` | — | — | ✅ `seg.duration_ms` | ✅ 显示 `(seg.duration_ms/1000).toFixed(1)+'s'` | 无（已正确展示） |
| 历史任务音频 | history.js `historyAudioPlayerHtml()` | `/api/voice/assets/${assetId}/download` | ✅ | ❌ | ❌ 依赖浏览器 metadata | 低 |
| 试听生成（Audition） | index.html `handleGenerateAudition()` | `data.audio_asset.url` | ✅ `data.audio_asset.id` | ✅ 显示 `(data.audio_asset.duration_ms/1000).toFixed(1)+'s'` | ✅ 正确展示 | 无（唯一正确展示的位置） |
| 克隆 demo 音频 | voice_clone.js | `data.demo_audio_url` | ❌ 无 asset_id | ❌ 不展示 | ❌ 依赖浏览器 metadata | 中 |
| 克隆快速试听 | voice_clone.js | `/api/voice/render` 返回的 `audio_asset.url` | ✅ `rd.audio_asset.id` | ❌ | ❌ 依赖浏览器 metadata | 中 |
| 声音设计 trial 音频 | voice_design.js | `data.trial_audio_url` | ❌ 无 asset_id | ❌ 不展示 | ❌ 依赖浏览器 metadata | 中 |
| 声音设计快速试听 | voice_design.js | `/api/voice/render` 返回的 `audio_asset.url` | ✅ | ❌ | ❌ 依赖浏览器 metadata | 中 |
| 导入验证音频 | voice_import.js | `data.audio_asset.url` | ✅ | ❌ | ❌ 依赖浏览器 metadata | 中 |
| 试听记录列表 | audition_records.js | `r.audioUrl`（localStorage） | ❌ 无 asset_id | ❌ 未保存 duration | ❌ 不展示 | 中（记录本身没有 duration 字段） |

---

## 2. 根因分析

### 2.1 audioPlayerHtml 只接受 assetId，不接受 duration_ms

**代码位置：** index.html line 3172
```javascript
function audioPlayerHtml(assetId) {
  return `<audio class="audio-player" controls preload="none">
    <source src="/api/voice/assets/${assetId}/download" type="audio/mpeg">
    您的浏览器不支持音频播放</audio>`;
}
```

**问题：** 该函数只接受 `assetId`，无法传入 `duration_ms` 作为预显示时长。

**唯一例外：** `handleGenerateAudition()` (line 3617) 展示了正确模式：
```javascript
const duration = data.audio_asset.duration_ms ? (data.audio_asset.duration_ms/1000).toFixed(1) + 's' : '-';
```

### 2.2 多个模块直接拼接 `<audio>`，没有统一播放器组件

| 位置 | audio 拼接方式 |
|---|---|
| `renderResults()` | `audioPlayerHtml(audio.id)` |
| `renderAsyncResult()` | `audioPlayerHtml(audio.id)` |
| `renderStreamResult()` | 内联 `<audio controls preload="auto">` |
| `renderBatchResultPlayer()` | DOM `audio.src = data.merged_audio.url` |
| `voice_clone.js` demo | 内联 `<audio controls preload="none">` |
| `voice_clone.js` quick preview | 内联 `<audio controls autoplay>` |
| `voice_design.js` trial | 内联 `<audio controls preload="none">` |
| `voice_design.js` quick preview | 内联 `<audio controls autoplay>` |
| `voice_import.js` | 内联 `<audio controls preload="none">` |
| `audition_records.js` | 内联 `<audio controls style="height:28px;width:160px">` |

每处都独立拼接，没有统一组件，导致：
- duration_ms 展示逻辑分散
- `preload` 属性不统一（none/metadata/auto）
- 样式不一致

### 2.3 批量结果有 total_duration_ms 但前端未展示

**后端数据可用：** `BatchStatusResponse.total_duration_ms: int | None`

**使用位置：** `renderStreamResult()` 在结果区描述中显示 `${completed.total_duration_ms} ms`（line 2855）

**未使用位置：** `renderBatchResultPlayer()` — 合并后的 `data.total_duration_ms` 完全未展示。合并音频播放器只有 `audio.src = data.merged_audio.url`，没有任何时长显示。

### 2.4 浏览器 audio metadata 显示不稳定

所有 `<audio controls>` 都依赖浏览器的 `loadedmetadata` 事件来显示总时长。不同浏览器表现不一致：
- 部分浏览器需要完整下载 metadata 才能显示时长
- blob URL 和某些 CORS 受限的 URL 可能无法获取 metadata
- 流式音频的 metadata 可能延迟加载

### 2.5 audition_records 不保存 durationMs

**代码位置：** audition_records.js line 3632-3636
```javascript
window._auditionRecords.push({
  voiceId, voiceName: voiceName || '',
  text, audioUrl: data.audio_asset.url,
  timestamp: Date.now(),
});
```

**问题：** `duration_ms` 未保存，导致试听记录列表无法显示时长。

### 2.6 历史音频使用 preload=metadata，是较好实践

**代码位置：** history.js line 119
```javascript
<audio class="audio-player" controls preload="metadata" src="...">
```

历史音频使用 `preload="metadata"`，让浏览器仅加载 metadata 而不下载完整音频，是正确做法。但仍然没有在 UI 中显式显示时长数值。

---

## 3. FIX5-B1 最小修复建议

### 3.1 扩展 audioPlayerHtml(options)

**目标：** 统一音频播放器组件，支持显式传入时长

```javascript
function audioPlayerHtml(options) {
  // options: { assetId, durationMs, label, mediaType }
  const assetId = options.assetId;
  const src = `/api/voice/assets/${assetId}/download`;
  const durationText = options.durationMs
    ? (options.durationMs / 1000).toFixed(1) + 's'
    : '';
  const label = options.label || '';
  return `<div class="audio-player-wrap">
    ${label ? `<div class="audio-player-label">${label}${durationText ? ' · ' + durationText : ''}</div>` : ''}
    <audio class="audio-player" controls preload="metadata">
      <source src="${src}" type="${options.mediaType || 'audio/mpeg'}">
      您的浏览器不支持音频播放
    </audio>
  </div>`;
}
```

### 3.2 同步 / 异步 / 多版本优先接入

`renderResults()` 和 `renderAsyncResult()` 中的 `audioPlayerHtml(audio.id)` 替换为带 duration 的版本：
```javascript
audioPlayerHtml({ assetId: audio.id, durationMs: audio.duration_ms, label: '音频结果' })
```

多版本 variants 中的 `v.duration_ms` 同样传入。

### 3.3 批量结果展示 total_duration_ms

`renderBatchResultPlayer()` 中，在 audio 元素上方或下方增加总时长显示：
```javascript
// 已知 total_duration_ms 时
const totalDurationText = data.total_duration_ms
  ? (data.total_duration_ms / 1000).toFixed(1) + 's'
  : '';
// 在 audio.src 设置后显示
if (totalDurationText) {
  // 插入时长提示元素
}
```

**注意：** `renderBatchResultPlayer()` 是 DOM 操作（`audio.src = ...`），不是 innerHTML 拼接，需要额外操作 DOM 来插入时长文本。

### 3.4 不改后端

所有 duration 数据已存在：
- `AudioAssetResponse.duration_ms`
- `VoiceVariantResponse.duration_ms`
- `BatchStatusResponse.total_duration_ms`
- `BatchSegmentStatus.duration_ms`（已在表格中正确展示）

---

## 4. FIX5-B2 后续修复建议

### 4.1 克隆 / 设计 / 导入 / quick preview 统一时长展示

三处 quick bind 面板中的 `<audio controls>` 统一增加时长显示：
- voice_clone.js demo audio：传入 `data.demo_audio_duration_ms`（如有）
- voice_design.js trial audio：同上
- voice_import.js verified audio：传入 `data.audio_asset.duration_ms`

### 4.2 audition_records 保存 durationMs

audition_records.js 的 push 记录时保存 duration：
```javascript
window._auditionRecords.push({
  voiceId, voiceName: voiceName || '',
  text, audioUrl: data.audio_asset.url,
  durationMs: data.audio_asset.duration_ms,  // 新增
  timestamp: Date.now(),
});
```

render 时展示：`${r.durationMs ? (r.durationMs/1000).toFixed(1)+'s' : '-'}`

### 4.3 formatDurationMs() helper

项目中目前没有统一的时长格式化函数。建议在 index.html 中新增：
```javascript
function formatDurationMs(ms) {
  if (!ms) return '-';
  return (ms / 1000).toFixed(1) + 's';
}
```

---

## 5. 审查结论

| 问题 | 严重程度 | 根因 | 是否本次修复 |
|---|---|---|---|
| audioPlayerHtml 不支持 duration_ms 展示 | **P1** | 函数设计缺陷 | FIX5-B1 |
| 批量结果播放器不显示 total_duration_ms | **P1** | renderBatchResultPlayer 未使用该字段 | FIX5-B1 |
| audition_records 不保存 duration_ms | P2 | push 时遗漏 durationMs 字段 | FIX5-B2 |
| 克隆/设计/导入 quick bind 面板无时长显示 | P2 | 独立拼接，无统一组件 | FIX5-B2 |
| 浏览器 metadata 依赖不稳定 | 低 | preload=none 导致 metadata 不加载 | FIX5-B1（改用 preload=metadata） |

---

## 6. FIX5-B1 实施记录

**实施时间：** 2026-05-15

**修改文件：** `app/static/index.html`

**改动点：**

1. **新增 `formatDurationMs()` helper**（line ~3172）
   - 将毫秒转为 `x.xs` 格式，空值返回空字符串

2. **扩展 `audioPlayerHtml(input)`**（line ~3175）
   - 兼容旧调用 `audioPlayerHtml(assetId)` 和新调用 `audioPlayerHtml({assetId, durationMs, label, mediaType})`
   - `preload` 从 `none` 改为 `metadata`
   - 新增 `.audio-meta` 显示标签和时长

3. **单条同步结果接入**（line ~3151）
   - `audioPlayerHtml(audio.id)` → `audioPlayerHtml({assetId: audio.id, durationMs: audio.duration_ms, label: '音频结果'})`

4. **多版本试音接入**（line ~3116）
   - `audioPlayerHtml(v.audio_asset_id)` → `audioPlayerHtml({assetId: v.audio_asset_id, durationMs: v.duration_ms, label: '版本 ' + (i+1)})`

5. **异步结果接入**（line ~3069）
   - `audioPlayerHtml(audio.id)` → `audioPlayerHtml({assetId: audio.id, durationMs: audio.duration_ms, label: '音频结果'})`

6. **批量合并音频展示 `total_duration_ms`**
   - HTML 新增 `batchMergedDuration` 和 `batchScriptMergedDuration` div
   - `getBatchPanelDom()` 增加 `durationEl`
   - `renderBatchResultPlayer()` 设置 `durationEl.textContent = '合并音频时长：' + formatDurationMs(data.total_duration_ms)`

7. **CSS 新增** `.audio-meta` / `.batch-audio-meta`

**未改：**
- 不改下载逻辑
- 不改 subtitle 下载
- 不改 batch polling
- 不改 segment 表格

---

## 7. FIX5-B2 实施记录

**实施时间：** 2026-05-15

**修改文件：**
- `app/static/js/voice_import.js`
- `app/static/js/voice_clone.js`
- `app/static/js/voice_design.js`
- `app/static/js/audition_records.js`
- `app/static/index.html`（handleGenerateAudition push 增加 durationMs）

**改动点：**

1. **voice_import.js**：导入验证音频
   - `preload="none"` → `preload="metadata"`
   - 显示 `data.audio_asset.duration_ms` 时长标签（如有）

2. **voice_clone.js**：克隆 demo 音频 + quick preview
   - demo audio 显示 `data.demo_audio_duration_ms || data.duration_ms` 时长（如有）
   - `preload="none"` → `preload="metadata"`
   - quick preview 显示 `rd.audio_asset.duration_ms` 时长（如有）

3. **voice_design.js**：设计 trial 音频 + quick preview
   - trial audio (hex blob / URL) 显示 `data.trial_audio_duration_ms || data.duration_ms` 时长（如有）
   - `preload="none"` → `preload="metadata"`
   - quick preview 显示 `rd.audio_asset.duration_ms` 时长（如有）

4. **audition_records.js**：展示 + 保存
   - 渲染时显示 `r.durationMs`（如有无显示）
   - `window._auditionRecords.push` 时新增 `durationMs: data.audio_asset.duration_ms || null`

5. **旧记录兼容**
   - `r.durationMs` 不存在时显示为空，不报错

---

## 8. FIX6-A0 关联：导入验证试听仍缺时长

**发现时间：** 2026-05-15

**问题描述：**
- FIX5-B2 前端已支持展示导入音频 `duration_ms`
- 真实使用时"导入已有克隆音色"验证试听成功后，audio 控件仍显示 `0:00 / 0:00`
- 页面没有出现"导入试听 · 时长 x.xs"

**FIX5-B2 正确实现的部分：**
- `voice_import.js` 显示 `data.audio_asset.duration_ms` 时长标签
- `handleGenerateAudition` push 保存 `durationMs`

**根因定位：**
- FIX6-A0 审查确认：链路各节点（ProviderRenderResult、AssetService、AudioAsset、AudioAssetResponse）都正确传递 duration_ms
- 问题在于 `output_format="hex"` 时 MiniMax 返回的 `audio_length` 可能为 0 或 null
- `estimate_duration_ms()` fallback 使用字符估算，但用户看到的是 0:00 而非估算值
- 真正原因可能是 MiniMax 对 hex 格式不返回 audio_length，或返回 0

**后续方向：**
- FIX6-B1：在 `AssetService.save_assets()` 中使用 `pydub` 从本地音频文件解析真实时长作为 fallback
- 详细审查报告：`docs/P12_AUDIO_DURATION_PERSISTENCE_AUDIT.md`

---

## 9. 下一步

| 任务 | 内容 | 前提 |
|---|---|---|
| FIX5-B1 | 扩展 audioPlayerHtml + 批量结果展示 total_duration_ms | FIX5-A0 完成 |
| FIX5-B2 | 克隆/设计/导入/audition_records 时长统一 | FIX5-B1 完成 |
| FIX6-B1 | fix audio asset duration persistence（使用 pydub 解析本地文件时长 fallback） | FIX6-A0 完成 |
