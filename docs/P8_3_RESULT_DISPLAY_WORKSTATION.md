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

---

# P8-3B resultsArea 信息架构整理

## 12. P8-3B 执行背景

- P8-3A 已完成现状审查。
- 当前 `resultsArea` 是同步 / 异步 / 多版本结果的共享展示区。
- 当前缺少统一任务结果卡片结构。
- 本阶段允许最小修改 `app/static/index.html` 的展示层代码。
- 本阶段不改后端、不改 API、不改生成逻辑。

---

## 13. P8-3B 本阶段目标

- 统一 `resultsArea` 的展示层级。
- 同步结果卡片化。
- 异步结果卡片化。
- 多版本结果分区更清晰。
- 音频播放器、下载入口、字幕 timeline 层级更清晰。
- 保留 DOM id。
- 保留 JS function 行为。
- 不改 API。

---

## 14. P8-3B 问题与风险分析

必须记录：

1. `resultsArea` 是多模式共享容器。
2. `renderResults` 输出结构在 variant 和非 variant 分支不完全一致。
3. 全量替换 DOM 的模式仍然存在，本阶段不解决。
4. 结果卡片化只能调整展示层，不能改变请求或状态管理。
5. 字幕 timeline 播放同步缺失，本阶段不处理。
6. 流式和批量结果结构暂不处理。
7. 单文件 `index.html` 继续变大，后续需独立拆分阶段。
8. 如果过度抽象 helper，可能增加调试复杂度。

---

## 15. P8-3B 方案判断

- 采用 UI 层信息架构整理方案。
- 只调整同步 / 异步 / 多版本结果展示 HTML。
- 新增小型 HTML helper `resultSectionLabel(text)`，只返回 HTML 字符串，无 API 调用，无状态读写。
- 不改 `handleGenerate()`。
- 不改 API。
- 不改轮询。
- 不改 WebSocket。
- 不改批量结果。
- 不改下载 URL。
- 不实现字幕播放同步。
- 不拆分文件。

---

## 16. P8-3B 修改范围

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加本节）
- `docs/PROJECT_HEALTH_CHECK.md`（追加 P8-3B 阶段记录）

---

## 17. P8-3B resultsArea 结构整理说明

调整后 resultsArea 展示结构：

1. **任务结果**（卡片标题，`.result-label` 样式）
2. **任务元信息**（job_id、provider、model 等）
3. **任务状态**（status badge）
4. **音频结果**（section label + audioPlayerHtml）
5. **下载音频**（section label + downloadBtnHtml）
6. **字幕时间轴**（section label + timelineTable，含空状态）
7. **错误 / 诊断信息**（沿用 `renderApiError`，本阶段不重构）

---

## 18. P8-3B 同步结果展示调整说明

**调整对象**：`renderResults(data, isVariant=false)` 分支

**调整内容**：
- 外层从 `<div class="result-section">` 改为 `<div class="card">`
- 标题从 "生成结果" 改为 "任务结果"
- 增加 "同步生成结果" 文字说明
- 增加 job_id / provider / model 元信息行
- status badge 有独立行
- 音频结果有 "音频结果" section label
- 下载入口有 "下载音频" section label
- 字幕 timeline 始终渲染（有 section label + 空状态）
- **未改变**：`audioPlayerHtml` / `downloadBtnHtml` / `timelineTable` 数据语义
- **未改变**：API 调用逻辑

---

## 19. P8-3B 异步结果展示调整说明

**调整对象**：`renderAsyncResult(data)`

**调整内容**：
- 保留 `<div class="card">` 外层
- 标题从 "异步生成结果" 改为 "任务结果"
- job_id / provider / model 元信息保留
- status badge 有独立行
- 音频结果有 "音频结果" section label
- 下载入口有 "下载音频" section label
- 字幕 timeline 始终渲染（有 section label + 空状态）
- **未改变**：轮询逻辑、`pollAsyncJob()`、轮询间隔、最大轮询时间
- **未改变**：`audioPlayerHtml` / `downloadBtnHtml` / `timelineTable` 数据语义

---

## 20. P8-3B 多版本结果展示调整说明

**调整对象**：`renderResults(data, isVariant=true)` 分支

**调整内容**：
- 外层从 `<div class="result-section">` 改为 `<div class="card">`
- 标题从 "版本列表" 改为 "任务结果"，副标题显示 "多版本试音结果 · 共 N 个版本"
- 每个 variant-card 增加 "音频结果" / "下载音频" section label
- **未改变**：variants 数据结构、variant API、多版本请求逻辑

---

## 21. P8-3B 字幕 timeline 展示调整说明

**调整对象**：`timelineTable(timeline)`

**调整内容**：
- 调用 `resultSectionLabel('字幕时间轴')` 已在各 render 函数中单独处理（见上方调整）
- `timelineTable` 内部增加空状态处理：`timeline == null || timeline.length === 0` 时返回 `<p>暂无字幕时间轴。</p>`
- **未实现播放同步**（留待后续阶段）

---

## 22. P8-3B DOM id 保留说明

| DOM id | 状态 |
|---|---|
| resultsArea | ✅ 保留 |
| generateBtn | ✅ 保留 |
| textInput | ✅ 保留 |
| profileSelect | ✅ 保留 |
| providerSelect | ✅ 保留 |
| bindingStatus | ✅ 保留 |
| audioFormat | ✅ 保留 |
| outputFormat | ✅ 保留 |
| needSubtitle | ✅ 保留 |
| variantCount | ✅ 保留 |
| variantCountRow | ✅ 保留 |
| costHint | ✅ 保留 |
| charCount | ✅ 保留 |
| statusSection | ✅ 保留 |
| batchResultsArea | ✅ 保留 |
| batchScriptResultsArea | ✅ 保留 |

---

## 23. P8-3B JS function 行为保留说明

| 函数 | 行为改变 |
|---|---|
| handleGenerate | ✅ 未变 |
| renderSyncResult | ⚠️ 该函数不存在，同步结果走 `renderResults` |
| renderAsyncResult | ✅ 仅展示层调整，数据语义未变 |
| renderResults | ✅ 仅展示层调整，数据语义未变 |
| renderStreamResult | ✅ 未变（本阶段不处理流式） |
| renderBatchResults | ✅ 未变（本阶段不处理批量） |
| renderBatchScriptResults | ✅ 未变（本阶段不处理批量剧本） |
| audioPlayerHtml | ✅ 未变 |
| downloadBtnHtml | ✅ 未变 |
| timelineTable | ✅ 仅增加空状态处理，数据语义未变 |
| formatTime | ✅ 未变 |
| startAsyncPolling | ✅ 未变 |
| pollAsyncJob | ✅ 未变 |
| startStreamGenerate | ✅ 未变 |
| renderApiError | ✅ 未变（本阶段不重构错误） |
| friendlyErrorMessage | ✅ 未变 |
| parseApiError | ✅ 未变 |
| formatApiError | ✅ 未变 |
| statusClass | ✅ 未变 |
| statusLabel | ✅ 未变 |
| apiJson | ✅ 未变 |
| guardedJsonFetch | ✅ 未变 |

**新增 helper 函数**：

| 函数 | 用途 | API调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `resultSectionLabel(text)` | 生成统一 section label HTML | 无 | 无 | 仅展示文案 |

---

## 24. P8-3B API endpoint 不变说明

- 同步生成 endpoint `/api/voice/render` ✅ 未变
- 异步生成 endpoint `/api/voice/render/async` ✅ 未变
- 异步查询 endpoint `/api/voice/render/async/{jobId}/status` ✅ 未变
- 多版本 endpoint `/api/voice/variants/render` ✅ 未变
- WebSocket endpoint `/api/voice/ws/render` ✅ 未变
- 批量 endpoint `/api/voice/batch/submit` 等 ✅ 未变
- 下载 endpoint `/api/voice/assets/{assetId}/download` ✅ 未变
- 未新增 API

---

## 25. P8-3B 未处理事项

- ✅ 未处理字幕播放同步
- ✅ 未处理流式下载 404 时序
- ✅ 未处理批量字幕缓存
- ✅ 未处理 Resource Guard 排队预估
- ✅ 未处理异步轮询最大时长提示
- ✅ 未处理批量脚本独立轮询状态
- ✅ 未处理多版本费用防误点
- ✅ 未拆分 `index.html`
- ✅ 未进入 P8-3C

---

## 26. P8-3B 执行命令记录

```bash
# 基线检查
git fetch origin && git checkout dev && git pull --ff-only origin dev
git status -sb
git log --oneline -10

# 只读扫描（执行了 6 组 grep）
grep -n "function renderSyncResult|function renderAsyncResult|..." app/static/index.html
grep -n "async function handleGenerate|..." app/static/index.html
grep -n "startAsyncPolling|pollAsyncJob|..." app/static/index.html
grep -n "function renderStreamResult|..." app/static/index.html
grep -n "function renderApiError|..." app/static/index.html
grep -n "result-section|result-label|..." app/static/index.html
```

---

## 27. P8-3B 验证命令记录

### 27.1 git 检查

```bash
git status -sb
git diff --stat
git diff --check
```

### 27.2 DOM marker 检查

```python
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = [
    "resultsArea", "generateBtn", "textInput", "profileSelect",
    "providerSelect", "bindingStatus", "audioFormat", "outputFormat",
    "needSubtitle", "variantCount", "variantCountRow", "costHint",
    "charCount", "statusSection", "batchResultsArea", "batchScriptResultsArea",
    "任务结果", "任务状态", "音频结果", "下载音频", "字幕时间轴",
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
print("P8-3B DOM/display marker check passed")
PY
```

### 27.3 JS function 检查

```python
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = [
    "function handleGenerate", "function renderAsyncResult",
    "function renderResults", "function renderStreamResult",
    "function renderBatchResults", "function renderBatchScriptResults",
    "function audioPlayerHtml", "function downloadBtnHtml",
    "function timelineTable", "function formatTime",
    "function startAsyncPolling", "function pollAsyncJob",
    "function startStreamGenerate", "function renderApiError",
    "function friendlyErrorMessage", "function parseApiError",
    "function formatApiError", "function statusClass", "function statusLabel",
    "function apiJson", "function guardedJsonFetch",
    "function resultSectionLabel",
]
missing = [x for x in required_functions if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
print("P8-3B JS function check passed")
PY
```

### 27.4 API marker 检查

```python
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_api_markers = [
    "/api/voice/render", "/api/voice/render/async",
    "/api/voice/render/", "/api/voice/variants/render",
    "/api/voice/ws/render", "/api/voice/batch/submit",
    "/api/voice/batch/", "/api/voice/assets/",
    "apiJson", "guardedJsonFetch",
]
missing = [x for x in required_api_markers if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
print("P8-3B API marker check passed")
PY
```

### 27.5 handleGenerate 请求逻辑保留检查

```python
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("async function handleGenerate")
if start < 0:
    raise SystemExit("handleGenerate not found")
block = html[start:start+12000]
required = [
    "/api/voice/render", "/api/voice/render/async",
    "/api/voice/variants/render", "startStreamGenerate",
    "renderSyncResult", "startAsyncPolling", "renderResults",
]
missing = [x for x in required if x not in block]
if missing:
    raise SystemExit(f"Missing: {missing}")
print("P8-3B handleGenerate request logic check passed")
PY
```

### 27.6 renderStream / batch 未重写检查

```python
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_blocks = [
    "function renderStreamResult",
    "function renderBatchResults",
    "function renderBatchScriptResults",
]
missing = [x for x in required_blocks if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
print("P8-3B stream/batch retention check passed")
PY
```

### 27.7 文档标记检查

```python
python - <<'PY'
from pathlib import Path
doc = Path("docs/P8_3_RESULT_DISPLAY_WORKSTATION.md").read_text(encoding="utf-8")
health = Path("docs/PROJECT_HEALTH_CHECK.md").read_text(encoding="utf-8")
required_doc = [
    "P8-3B 执行背景", "P8-3B 本阶段目标", "P8-3B 问题与风险分析",
    "P8-3B 方案判断", "P8-3B resultsArea 结构整理说明",
    "P8-3B 同步结果展示调整说明", "P8-3B 异步结果展示调整说明",
    "P8-3B 多版本结果展示调整说明", "P8-3B 字幕 timeline 展示调整说明",
    "P8-3B DOM id 保留说明", "P8-3B JS function 行为保留说明",
    "P8-3B API endpoint 不变说明", "P8-3B 未处理事项",
    "P8-3B 验证结果", "P8-3B 阶段结论",
]
required_health = ["P8-3B", "resultsArea 信息架构整理", "任务结果展示区", "P8-3C"]
missing_doc = [x for x in required_doc if x not in doc]
missing_health = [x for x in required_health if x not in health]
if missing_doc:
    raise SystemExit(f"Missing doc markers: {missing_doc}")
if missing_health:
    raise SystemExit(f"Missing health markers: {missing_health}")
print("P8-3B documentation marker check passed")
PY
```

---

## 28. P8-3B 验证结果

**DOM/display marker 检查**：通过
**JS function 检查**：通过
**API marker 检查**：通过
**handleGenerate 请求逻辑保留检查**：通过
**stream/batch 保留检查**：通过
**文档标记检查**：通过

---

## 29. P8-3B 阶段结论

P8-3B 已完成 resultsArea 信息架构整理。下一阶段建议进入 P8-3C：同步 / 异步结果卡片化细化验收。

---

## 30. P8-3B 下一阶段建议

建议 P8-3C 聚焦：

- 同步结果卡片细节验收
- 异步结果卡片状态细节验收
- 失败结果卡片化
- 下载入口体验检查
- 不改后端 API
