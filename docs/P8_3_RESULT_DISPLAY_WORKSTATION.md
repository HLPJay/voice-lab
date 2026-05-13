# P8-3A 任务结果展示现状审查

**阶段目标**：仅做现状审查和文档化，不改前端、不改后端、不改 JS 逻辑。

**产出**：`docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`

---

## 1. 现状概要

当前 `app/static/index.html` 是单文件前端，所有生成模式（同步/异步/流式/多版本）的结果都通过 `resultsArea` 统一展示区渲染到页面。没有独立的任务卡片抽象，任务状态通过轮询更新 `resultsArea.innerHTML` 驱动。

**核心容器**：`resultsArea`（`id="resultsArea"`，位于 tab-workspace 主表单下方）

**结果函数**：
- `renderSyncResult(data)` — 同步 T2A 结果
- `renderAsyncResult(data)` — 异步 T2A 轮询结果
- `renderResults(data, isVariant)` — 通用结果渲染（同步轮询 + 多版本）
- `renderBatchResults(data)` — 批量任务结果
- `renderBatchScriptResults(data)` — 剧本批量结果
- `renderStreamResult(data)` — WebSocket 流式结果

---

## 2. DOM 现状

### 2.1 核心容器

| ID | 类型 | 所在区域 | 说明 |
|---|---|---|---|
| `resultsArea` | div | tab-workspace | 主结果展示区，所有模式共享 |
| `statusSection` | div | tab-workspace | 流式/状态信息区 |
| `batchResultsArea` | div | tab-longtext | 批量任务结果区 |
| `batchScriptResultsArea` | div | tab-script | 剧本批量结果区 |
| `batchDownloadAudio` | a | tab-longtext | 批量音频下载入口 |
| `batchDownloadSubtitle` | a | tab-longtext | 批量字幕下载入口 |
| `batchCurrentSubtitle` | div | tab-longtext | 当前播放字幕高亮 |
| `batchSubtitleList` | div | tab-longtext | 字幕时间轴列表 |

### 2.2 批量任务 DOM

批量结果（tab-longtext）有独立 DOM 结构，包含：
- `batchCurrentSubtitle` — 播放时字幕高亮区（时间同步驱动）
- `batchSubtitleList` — 字幕列表（可滚动）
- `batchDownloadAudio` / `batchDownloadSubtitle` — 下载链接

批量剧本（tab-script）有类似结构 `batchScriptResultsArea`。

### 2.3 流式状态 DOM

| ID | 说明 |
|---|---|
| `streamStatusCard` | 流式状态卡片容器 |
| `streamChunkCount` | 流式 chunk 计数 |
| `streamDuration` | 流式时长显示 |
| `streamProgress` | 流式进度条 |

流式结果 DOM 在 `startStreamGenerate()` 中通过模板字符串注入 `statusSection`。

---

## 3. JS 函数清单

### 3.1 结果渲染函数

| 函数 | 行号 | 用途 |
|---|---|---|
| `renderSyncResult(data)` | ~2200 | 渲染同步 T2A 结果到 resultsArea |
| `renderAsyncResult(data)` | ~2217 | 渲染异步轮询结果到 resultsArea |
| `renderResults(data, isVariant)` | ~2239 | 通用结果 + 多版本结果 |
| `renderBatchResults(data)` | ~4090 | 批量长文本任务结果 |
| `renderBatchScriptResults(data)` | ~3660 | 剧本批量任务结果 |
| `renderStreamResult(data)` | ~2040 | WebSocket 流式结果 |
| `audioPlayerHtml(assetId)` | ~2275 | 生成音频播放器 HTML |
| `downloadBtnHtml(assetId)` | ~2281 | 生成下载按钮 HTML |
| `timelineTable(timeline)` | ~2285 | 生成字幕时间轴表格 HTML |
| `formatTime(seconds)` | ~2297 | 格式化秒数为 MM:SS,mmm |

### 3.2 状态与工具函数

| 函数 | 行号 | 用途 |
|---|---|---|
| `statusLabel(status)` | ~1499 | 状态码 → 显示文字 |
| `statusClass(status)` | ~1506 | 状态码 → CSS class |
| `extractErrorMessage(data)` | ~1554 | 从响应提取错误消息 |
| `friendlyErrorMessage(message)` | ~1564 | 友好错误消息映射 |
| `parseApiError(resp)` | ~1580 | 解析 API 错误响应 |
| `formatApiError(err)` | ~1635 | 格式化错误消息（含 Resource Guard） |
| `resourceLimitExtraHint(operation)` | ~1655 | Resource Guard 额外提示 |
| `renderApiError(err, options)` | ~1675 | 渲染错误 UI |
| `extractDetailValue(text, key)` | ~1620 | 从 detail 文本提取字段值 |

---

## 4. API 端点映射

### 4.1 结果查询相关端点

| 端点 | 调用位置 | 用途 |
|---|---|---|
| `GET /api/voice/render/{jobId}/status` | `pollAsyncJob()` | 异步任务状态轮询 |
| `GET /api/voice/batch/{batchId}/status` | `pollBatchJob()` | 批量任务状态轮询 |
| `GET /api/voice/assets/{assetId}/download` | 音频播放器 src / downloadBtn | 音频文件下载 |
| `GET /api/voice/assets/{subId}/download` | 字幕下载按钮 | 字幕文件下载 |

### 4.2 生成相关端点

| 端点 | 调用位置 | 用途 |
|---|---|---|
| `POST /api/voice/render` | `handleGenerate()` | 同步 T2A |
| `POST /api/voice/render/async` | `handleGenerate()` | 异步 T2A |
| `POST /api/voice/variants/render` | `handleGenerate()` | 多版本试音 |
| `WS /api/voice/ws/render` | `startStreamGenerate()` | WebSocket 流式 |

### 4.3 批量相关端点

| 端点 | 调用位置 | 用途 |
|---|---|---|
| `POST /api/voice/batch/submit` | 批量长文本/剧本提交 | 批量任务提交 |
| `GET /api/voice/batch/{batchId}/status` | 批量轮询 | 批量状态查询 |
| `POST /api/voice/batch/{batchId}/retry` | 批量失败重试 | 重试失败任务 |

---

## 5. 用户路径分析

### 5.1 同步生成路径

```
用户点击"生成"
→ handleGenerate() [mode=sync]
→ POST /api/voice/render
→ renderSyncResult(data)
→ resultsArea.innerHTML 更新
→ 显示: 状态标签 + 音频播放器 + 下载按钮 + 字幕时间轴（如有）
```

### 5.2 异步生成路径

```
用户点击"生成"
→ handleGenerate() [mode=async]
→ POST /api/voice/render/async
→ 显示 resultsArea（loading 状态）
→ startAsyncPolling(jobId)
→ pollAsyncJob() 定时调用 GET /api/voice/render/{jobId}/status
→ renderAsyncResult(data) 每次更新 resultsArea
→ 状态变为 completed → 显示音频播放器 + 下载 + 字幕
```

### 5.3 WebSocket 流式路径

```
用户点击"生成"
→ handleGenerate() [mode=stream]
→ startStreamGenerate()
→ WebSocket 连接 /api/voice/ws/render
→ 流式 chunk 累积在 binaryParts[]
→ 完成后 new Blob → streamBlobUrl
→ renderStreamResult() 更新 statusSection
→ 显示音频播放器 + 下载(本地缓存) + 下载(服务端) + 字幕（如有）
→ 流式期间显示 streamStatusCard（chunk 计数、时长）
```

### 5.4 多版本试音路径

```
用户点击"生成"
→ handleGenerate() [mode=variants]
→ POST /api/voice/variants/render
→ renderResults(data, isVariant=true)
→ resultsArea 显示 variants-grid
→ 每个 variant 显示: variant-meta(版本号/语速/情绪) + 音频播放器 + 下载按钮
```

### 5.5 批量长文本路径

```
用户填写表单 + 点击"提交"
→ handleBatchSubmit()
→ POST /api/voice/batch/submit
→ pollBatchJob() 轮询
→ renderBatchResults(data)
→ batchResultsArea.innerHTML 更新
→ 音频播放器 + batchCurrentSubtitle(字幕高亮) + batchSubtitleList(字幕列表)
→ batchDownloadAudio / batchDownloadSubtitle 显示
```

### 5.6 批量剧本路径

```
用户填写剧本 + 点击"提交"
→ handleBatchScriptSubmit()
→ POST /api/voice/batch/submit
→ pollBatchScriptJob() 轮询
→ renderBatchScriptResults(data)
→ 独立结果区显示每个角色的音频
```

---

## 6. 问题与风险

### 6.1 字幕时间轴播放器同步缺失

**问题**：`renderBatchResults()` 中音频播放器有 `timeupdate` 事件监听 `updateBatchSubtitleHighlight()`，字幕高亮可以工作。但 `timelineTable()` 用于 `renderAsyncResult()` 和 `renderResults()` 的字幕时间轴**不参与播放同步**，用户播放音频时只能看到静态字幕表，无法跟随播放进度。

**风险**：用户体验割裂，不知道当前播放到哪句。

### 6.2 流式结果下载入口分散

**问题**：流式结果的下载按钮在 `renderStreamResult()` 中有两 个：`下载(本地缓存)`（blob URL）和 `下载(服务端)`（asset ID URL）。服务端下载依赖后端 asset 生成，如果流式结束但 asset 尚未生成，按钮可能 404。

**风险**：用户可能拿到 404 的下载链接。

### 6.3 批量字幕缓存只存 timeline

**问题**：`window._batchSubtitleCache` 只缓存 `timeline` 数组，不缓存字幕文本（.srt/.vtt 格式内容）。用户下载字幕依赖 `GET /api/voice/assets/{subId}/download` 实时请求，不存在缓存加速。

**风险**：字幕下载无本地缓存，下载按钮可能出现 404。

### 6.4 resultsArea 全量替换模式

**问题**：所有渲染函数（除流式状态卡片外）都使用 `resultsArea.innerHTML = ...` 全量替换 DOM。轮询场景下每次轮询都会重建 DOM，可能导致音频播放器状态丢失（如果用户在播放时轮询发生）。

**风险**：用户听音频时如果恰好触发轮询，播放器会重置。

### 6.5 错误渲染分散

**问题**：`renderApiError()` 在多个 call site 被调用（`guardedJsonFetch`、`handleGenerate`、`startStreamGenerate` 的多处错误处理、流式 WS 消息处理），但返回的都是同一个静态 HTML 字符串。没有重试倒计时、资源队列预估等高级信息。

**风险**：用户看到 Resource Guard 错误后不知道具体要等多久。

### 6.6 异步任务最大轮询时间硬编码

**问题**：`ASYNC_MAX_AUTO_POLL_MS = 15 * 60 * 1000` 硬编码，没有动态调整或提示。如果任务超过 15 分钟仍未完成，自动轮询停止但不会告知用户。

**风险**：超长任务用户以为还在轮询，实际已停止。

### 6.7 批量脚本结果无独立轮询状态对象

**问题**：批量剧本使用内联轮询逻辑（在 `renderBatchScriptResults` 中递归调用 `setTimeout`），没有像 `asyncPollingState` 那样的统一状态管理。没有 `stopBatchScriptPolling()` 函数。

**风险**：用户在批量剧本生成期间无法手动停止轮询。

### 6.8 variantCountInput 无防误点

**问题**：`variantCount` input（多版本试音版本数）可以输入 1-5，但如果用户快速多次点击生成，版本数可能不一致。没有在生成前锁定 input。

**风险**：多版本生成是费用较高的操作，可能被误触发多次。

---

## 7. 静态检查基线

### 7.1 核心 DOM ID（resultsArea 相关）

```
resultsArea            ✅ 存在
batchResultsArea       ✅ 存在
batchScriptResultsArea ✅ 存在
streamStatusCard       ✅ 存在
streamChunkCount       ✅ 存在
streamDuration         ✅ 存在
batchDownloadAudio     ✅ 存在
batchDownloadSubtitle  ✅ 存在
batchCurrentSubtitle   ✅ 存在
batchSubtitleList      ✅ 存在
```

### 7.2 核心 JS 函数

```
renderSyncResult       ✅ 存在 (~2200)
renderAsyncResult      ✅ 存在 (~2217)
renderResults          ✅ 存在 (~2239)
renderBatchResults     ✅ 存在 (~4090)
renderBatchScriptResults ✅ 存在 (~3660)
renderStreamResult     ✅ 存在 (~2040)
audioPlayerHtml        ✅ 存在 (~2275)
downloadBtnHtml        ✅ 存在 (~2281)
timelineTable          ✅ 存在 (~2285)
formatTime             ✅ 存在 (~2297)
statusLabel            ✅ 存在 (~1499)
statusClass            ✅ 存在 (~1506)
renderApiError         ✅ 存在 (~1675)
parseApiError          ✅ 存在 (~1580)
extractErrorMessage    ✅ 存在 (~1554)
friendlyErrorMessage   ✅ 存在 (~1564)
formatApiError         ✅ 存在 (~1635)
resourceLimitExtraHint ✅ 存在 (~1655)
```

### 7.3 API 端点

```
POST /api/voice/render                     ✅
POST /api/voice/render/async               ✅
GET  /api/voice/render/{jobId}/status      ✅
POST /api/voice/variants/render            ✅
WS   /api/voice/ws/render                  ✅
POST /api/voice/batch/submit               ✅
GET  /api/voice/batch/{batchId}/status     ✅
POST /api/voice/batch/{batchId}/retry      ✅
GET  /api/voice/assets/{assetId}/download  ✅
```

### 7.4 CSS 样式

```
.audio-player         ✅ 定义
.timeline-table       ✅ 定义（样式在 CSS 中）
.variants-grid       ✅ 定义（样式在 CSS 中）
.variant-card        ✅ 定义（样式在 CSS 中）
.error-msg           ✅ 定义
.resource-limit-msg  ✅ 定义
.stream-status-card  ✅ 定义
```

---

## 8. P8-3 后续阶段建议

基于以上审查，P8-3 后续工作建议方向（仅供参考，不作为实施承诺）：

| 方向 | 说明 |
|---|---|
| 任务卡片抽象 | 引入独立任务卡片组件（非全量替换 resultsArea），支持局部状态更新 |
| 字幕播放同步 | 将 timelineTable 升级为可同步音频播放的字幕组件 |
| 流式下载稳定性 | 明确服务端 asset 生成时序，确保下载按钮可用 |
| 批量字幕缓存 | 考虑缓存字幕文件内容，加速重复下载 |
| 轮询状态管理 | 统一 asyncPollingState / batchPollingState，支持 stopPolling |
| Resource Guard 增强 | 显示排队位置或预估等待时间 |
| 多版本防误点 | 提交前禁用 variantCountInput + 按钮防抖 |
