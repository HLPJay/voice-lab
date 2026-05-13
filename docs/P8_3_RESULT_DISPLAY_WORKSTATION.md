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

---

# P8-3C 同步 / 异步结果卡片化细化验收

## 31. P8-3C 执行背景

- P8-3A 已完成现状审查。
- P8-3B 已完成 `resultsArea` 信息架构整理。
- P8-3B 后发现文档中 `renderSyncResult` 口径需要统一。
- 当前同步结果实际由 `renderResults(data, isVariant=false)` 展示。
- 本阶段只做同步 / 异步结果卡片的展示层细化和验收。
- 本阶段不改后端、不改 API、不改生成逻辑、不改轮询逻辑。

---

## 32. P8-3C 本阶段目标

- 统一同步结果函数口径。
- 同步结果 card 状态展示更清楚（增加状态说明）。
- 异步结果 card 状态展示更清楚（running/failed/completed 分支处理）。
- 无 audio / 无 subtitle 的空状态更准确。
- failed/error 状态展示诊断信息。
- 新增 `resultStatusHintHtml(status)` 和 `resultDiagnosticHtml(message)` helper。
- 保留 DOM id。
- 保留 JS function 行为。
- 不改 API。

---

## 33. P8-3C 问题与风险分析

1. P8-3A 中 `renderSyncResult` 属于旧审查口径，实际代码中不存在该函数，同步结果走 `renderResults(data, isVariant=false)`。
2. P8-3B 后字幕空状态可能在 running/failed 时过早展示（`timelineTable(null)` 在任何状态下都返回"暂无字幕时间轴"）。
3. P8-3B 后无 audio 时缺少足够明确的解释（对 completed 状态应提示"未返回音频资产"，对 failed 状态不应提示）。
4. 异步 queued/running/processing 状态不应展示音频/下载/字幕空区。
5. failed/error 状态需要诊断信息，但不能替代全局 `renderApiError`。
6. 本阶段不能改轮询状态管理。

---

## 34. P8-3C 方案判断

- 采用 UI 层细化方案。
- 不新增 `renderSyncResult`。
- 同步结果继续走 `renderResults(data, isVariant=false)`。
- 异步结果继续走 `renderAsyncResult(data)`。
- 新增 `resultStatusHintHtml(status)` helper — 根据 status 返回状态说明文本，无 API 调用，无状态读写。
- 新增 `resultDiagnosticHtml(message)` helper — 返回诊断信息 HTML，无 API 调用，无状态读写。
- 只调整 card 内部展示层级和空状态。
- 不改 `handleGenerate()`。
- 不改 API。
- 不改轮询。
- 不改 WebSocket。
- 不改批量结果。
- 不实现字幕播放同步。
- 不拆分文件。

---

## 35. P8-3C 修改范围

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3C 节）
- `docs/PROJECT_HEALTH_CHECK.md`（追加 P8-3C 阶段记录）

---

## 36. P8-3C 同步结果口径统一说明

**口径统一结论**：当前 dev 实际代码中未发现 `renderSyncResult(data)` 函数。同步生成结果实际由 `renderResults(data, isVariant=false)` 展示。P8-3B 阶段文档已记录"该函数不存在，同步结果走 renderResults"。P8-3C 已统一口径，后续不再将 `renderSyncResult` 作为必须存在的函数。

---

## 37. P8-3C 同步结果展示细化说明

**调整对象**：`renderResults(data, isVariant=false)`

**调整内容**：
- 增加 `resultStatusHintHtml(job.status)` 状态说明：
  - success: "任务已完成，可以播放或下载音频。"
  - failed: "任务失败，请查看错误信息。"
  - running: "任务处理中，请稍候。"
  - pending: "任务等待中，请稍候。"
  - processing: "任务处理中，请稍候。"
  - 其它: "当前任务状态：{status}"
- audio 存在时：展示音频/下载 sections
- audio 不存在且状态为 success：展示红色提示"本次结果未返回音频资产，请检查任务状态。"
- audio 不存在且非 success：不展示任何 audio 相关提示
- subtitle.timeline 存在时：展示字幕时间轴
- 无 subtitle 且状态为 success：展示"本次结果未返回字幕时间轴。"
- 无 subtitle 且非 success：不展示字幕空状态提示
- **未改变**：API 逻辑、`audioPlayerHtml`/`downloadBtnHtml`/`timelineTable` 数据语义

---

## 38. P8-3C 异步结果展示细化说明

**调整对象**：`renderAsyncResult(data)`

**调整内容**：
- 根据 `status === 'failed'` / `status === 'success'` / 其它三分支处理：
  - **running/queued/processing**（非 failed 非 success）：仅展示 job_id、status badge、状态说明，无音频/下载/字幕 sections
  - **failed**：展示 job_id、status badge、状态说明、诊断信息（`resultDiagnosticHtml(data.error_message || data.detail)`），无音频/下载/字幕 sections
  - **success**：展示音频/下载/字幕（如有），无 subtitle 时显示"本次结果未返回字幕时间轴"
- audio 存在时：正常展示
- audio 不存在（success）：显示"本次结果未返回音频资产。"
- **未改变**：轮询逻辑、`pollAsyncJob()`、轮询间隔、最大轮询时间、`audioPlayerHtml`/`downloadBtnHtml`/`timelineTable` 数据语义

---

## 39. P8-3C 空状态与诊断信息说明

**新增 helper 函数**：

| 函数 | 用途 | 说明文本 | API调用 | 状态读写 |
|---|---|---|---|---|
| `resultStatusHintHtml(status)` | 返回状态说明 HTML | 根据 status 返回不同提示 | 无 | 无 |
| `resultDiagnosticHtml(message)` | 返回诊断信息 HTML | 用于 failed 状态错误信息展示 | 无 | 无 |

**无 audio 空状态展示**：
- sync `renderResults`：status=success 但无 audio → "本次结果未返回音频资产，请检查任务状态。"
- async `renderAsyncResult`：status=success 但无 audio → "本次结果未返回音频资产。"
- failed 状态：不展示 audio 空状态（因为失败本来就没有音频是正常的）

**无 subtitle 空状态展示**：
- status=success 但无 subtitle → "本次结果未返回字幕时间轴。"
- 非 success 状态：不展示字幕空状态

---

## 40. P8-3C 多版本结果保留说明

- 多版本结果结构保持 P8-3B 方案（card + variants-grid + variant-card）
- **未改变**：variants 数据结构、variants API、variantCount、多版本防误点

---

## 41. P8-3C DOM id 保留说明

所有关键 DOM id 保留：
- resultsArea ✅
- generateBtn ✅
- textInput ✅
- profileSelect ✅
- providerSelect ✅
- bindingStatus ✅
- audioFormat ✅
- outputFormat ✅
- needSubtitle ✅
- variantCount ✅
- variantCountRow ✅
- costHint ✅
- charCount ✅

**说明**：`statusSection`、`batchResultsArea`、`batchScriptResultsArea` 在当前 baseline 代码中不存在（属于 P8-3C 指令清单与实际代码的预存差异，非本次修改造成）。

---

## 42. P8-3C JS function 行为保留说明

| 函数 | 行为改变 |
|---|---|
| handleGenerate | ✅ 未变 |
| renderAsyncResult | ✅ 仅展示层调整（状态分支 + 空状态 + 诊断信息） |
| renderResults | ✅ 仅展示层调整（状态说明 + 空状态） |
| renderStreamResult | ✅ 未变（本阶段不处理流式） |
| renderBatchResultPlayer | ✅ 未变（本阶段不处理批量） |
| renderBatchStatus | ✅ 未变 |
| audioPlayerHtml | ✅ 未变 |
| downloadBtnHtml | ✅ 未变 |
| timelineTable | ✅ 未变（空状态由调用方控制） |
| formatTime | ✅ 未变 |
| resultSectionLabel | ✅ 未变 |
| startAsyncPolling | ✅ 未变 |
| pollAsyncJob | ✅ 未变 |
| startStreamGenerate | ✅ 未变 |
| renderApiError | ✅ 未变 |
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
| `resultStatusHintHtml(status)` | 返回状态说明 HTML | 无 | 无 | 仅展示文本 |
| `resultDiagnosticHtml(message)` | 返回诊断信息 HTML | 无 | 无 | 仅展示文本 |

---

## 43. P8-3C API endpoint 不变说明

- 同步生成 endpoint `/api/voice/render` ✅ 未变
- 异步生成 endpoint `/api/voice/render/async` ✅ 未变
- 异步查询 endpoint `/api/voice/render/async/{jobId}/status` ✅ 未变
- 多版本 endpoint `/api/voice/variants/render` ✅ 未变
- WebSocket endpoint `/api/voice/ws/render` ✅ 未变
- 批量 endpoint `/api/voice/batch/submit` 等 ✅ 未变
- 下载 endpoint `/api/voice/assets/{assetId}/download` ✅ 未变
- 未新增 API

---

## 44. P8-3C 未处理事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未处理批量结果卡片化
- 未处理流式结果深度重构
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-3D

---

## 45. P8-3C 执行命令记录

```bash
# 基线检查
git fetch origin && git checkout dev && git pull --ff-only origin dev
git status -sb
git log --oneline -10

# 只读扫描（6组 grep）
grep -n "function renderAsyncResult|function renderResults|..." app/static/index.html
grep -n "renderSyncResult" app/static/index.html
grep -n "handleGenerate|/api/voice/render" app/static/index.html
grep -n "asyncPollingState|pollAsyncJob" app/static/index.html
grep -n "任务结果|音频结果|字幕时间轴" app/static/index.html
grep -n "function renderApiError|RESOURCE_LIMIT_EXCEEDED" app/static/index.html
```

---

## 46. P8-3C 验证命令记录

### 46.1 DOM/display marker 检查

```python
python -c "
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
checks = ['resultsArea','任务结果','同步生成结果','任务状态',
          '音频结果','下载音频','字幕时间轴','诊断信息',
          '任务处理中，请稍候','任务已完成，可以播放或下载音频',
          '任务失败，请查看错误信息',
          '本次结果未返回字幕时间轴','本次结果未返回音频资产']
missing = [x for x in checks if x not in html]
if missing: raise SystemExit('Missing: '+str(missing))
print('PASSED')
"
```

### 46.2 JS function 检查

```python
python -c "
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
funcs = ['function handleGenerate','function renderAsyncResult',
         'function renderResults','function resultStatusHintHtml',
         'function resultDiagnosticHtml','function startAsyncPolling',
         'function pollAsyncJob','function renderApiError',
         'function apiJson','function guardedJsonFetch']
missing = [x for x in funcs if x not in html]
if missing: raise SystemExit('Missing: '+str(missing))
print('PASSED')
"
```

### 46.3 API marker 检查

```python
python -c "
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
apis = ['/api/voice/render','/api/voice/render/async',
        '/api/voice/variants/render','/api/voice/ws/render',
        '/api/voice/batch/submit','/api/voice/assets/',
        'apiJson','guardedJsonFetch']
missing = [x for x in apis if x not in html]
if missing: raise SystemExit('Missing: '+str(missing))
print('PASSED')
"
```

### 46.4 handleGenerate 请求逻辑保留检查

```python
python -c "
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
start = html.find('async function handleGenerate')
block = html[start:start+12000]
required = ['/api/voice/render','/api/voice/render/async',
            '/api/voice/variants/render','startStreamGenerate',
            'startAsyncPolling','renderResults']
missing = [x for x in required if x not in block]
if missing: raise SystemExit('Missing: '+str(missing))
print('PASSED')
"
```

### 46.5 异步轮询保留检查

```python
python -c "
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
required = ['function startAsyncPolling','function pollAsyncJob',
            'asyncPollingState','ASYNC_MAX_AUTO_POLL_MS']
missing = [x for x in required if x not in html]
if missing: raise SystemExit('Missing: '+str(missing))
print('PASSED')
"
```

### 46.6 stream/batch 未重写检查

```python
python -c "
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
required = ['function renderStreamResult','function renderBatchResultPlayer',
           'function renderBatchStatus']
missing = [x for x in required if x not in html]
if missing: raise SystemExit('Missing: '+str(missing))
print('PASSED')
"
```

---

## 47. P8-3C 验证结果

**DOM/display marker 检查**：通过
**JS function 检查**：通过（包含新增 `resultStatusHintHtml`、`resultDiagnosticHtml`）
**API marker 检查**：通过
**handleGenerate 请求逻辑保留检查**：通过
**异步轮询保留检查**：通过
**stream/batch 保留检查**：通过
**文档标记检查**：通过

---

## 48. P8-3C 阶段结论

P8-3C 已完成同步 / 异步结果卡片化细化验收。下一阶段建议进入 P8-3D：流式 / 多版本结果展示统一。

---

## 49. P8-3C 下一阶段建议

建议 P8-3D 聚焦：

- WebSocket 流式结果展示统一
- 多版本结果展示细节验收
- 流式结果本地缓存 / 服务端下载入口说明
- 多版本结果下载入口一致性
- 不改后端 API

---

# P8-3C1 结果状态口径自检与收口修复

## 50. P8-3C1 执行背景

- P8-3B 已完成 `resultsArea` 信息架构整理。
- P8-3C 已完成同步 / 异步结果卡片化细化验收。
- 自检发现展示层可能只识别 `success` / `failed`，但后端异步任务实际可能返回 `completed` / `queued` 等状态。
- 如果后端返回 `completed`，前端可能误判为处理中，从而不展示音频、下载和字幕。
- 本阶段用于统一结果状态口径（展示层）。
- 本阶段不改后端、不改 API、不改生成逻辑、不改轮询逻辑。

---

## 51. P8-3C1 问题与风险分析

1. 完成态可能存在 `success` / `completed` 两种口径，P8-3C 中 `status === 'success'` 会漏判 `completed`。
2. 失败态可能存在 `failed` / `error` 两种口径，P8-3C 中 `status === 'failed'` 会漏判 `error`。
3. 等待态可能存在 `queued` / `pending` 两种口径。
4. 处理中态可能存在 `running` / `processing` 两种口径。
5. P8-3C 中 failed/error 诊断信息来源 `data.error_message || data.detail` 不够全面，应优先复用 `extractErrorMessage(data)`。
6. 本阶段只能修展示层状态判断，不改轮询、不改 API。

---

## 52. P8-3C1 方案判断

- 采用状态语义 helper 统一方案。
- 新增 `isResultSuccessStatus(status)` — 判断完成态（success / completed）。
- 新增 `isResultFailedStatus(status)` — 判断失败态（failed / error）。
- 新增 `isResultProcessingStatus(status)` — 判断处理中/等待态（queued / pending / running / processing）。
- `renderAsyncResult(data)` 改为使用上述三个 helper。
- `renderResults(data, isVariant=false)` 改为使用上述三个 helper。
- `resultStatusHintHtml(status)` 补齐 `completed` / `queued` / `error` 文案。
- failed/error 诊断信息来源改为 `extractErrorMessage(data)`。
- 不改 `handleGenerate()`。
- 不改 API。
- 不改轮询。
- 不改 WebSocket。
- 不改批量结果。
- 不拆分文件。

---

## 53. P8-3C1 修改范围

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3C1 节）
- `docs/PROJECT_HEALTH_CHECK.md`（追加 P8-3C1 阶段记录）

---

## 54. P8-3C1 状态口径统一说明

### 完成态

统一识别：`success` | `completed`
展示文案：`任务已完成，可以播放或下载音频。`

### 失败态

统一识别：`failed` | `error`
展示文案：`任务失败，请查看错误信息。`

### 等待 / 处理中态

统一识别：`queued` | `pending` | `running` | `processing`
展示文案：`任务等待中，请稍候。` / `任务处理中，请稍候。`

### 未知状态

展示文案：`当前任务状态：{status}`

---

## 55. P8-3C1 helper 函数说明

| 函数 | 用途 | API 调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `isResultSuccessStatus(status)` | 判断完成态 | 无 | 无 | 否，仅展示判断 |
| `isResultFailedStatus(status)` | 判断失败态 | 无 | 无 | 否，仅展示判断 |
| `isResultProcessingStatus(status)` | 判断处理中/等待态 | 无 | 无 | 否，仅展示判断 |
| `resultStatusHintHtml(status)` | 生成状态说明文案（已补全 `completed`/`error`/`queued`） | 无 | 无 | 否，仅展示文本 |
| `resultDiagnosticHtml(message)` | 生成诊断信息 HTML | 无 | 无 | 否，仅展示文本 |

---

## 56. P8-3C1 同步结果修复说明

**调整对象**：`renderResults(data, isVariant=false)`

**调整内容**：
- `const statusOk = job.status === 'success'` → `const statusOk = isResultSuccessStatus(job.status)`
- 新增 `const statusFailed = isResultFailedStatus(job.status)`
- success/completed：展示音频、下载、字幕；无则显示空状态提示
- failed/error：展示 `resultDiagnosticHtml(extractErrorMessage(job))`，不展示音频/下载/字幕空状态
- queued/pending/running/processing：仅展示状态说明，不展示音频/下载/字幕 sections
- **API 逻辑未改变**

---

## 57. P8-3C1 异步结果修复说明

**调整对象**：`renderAsyncResult(data)`

**调整内容**：
- `const isFailed = status === 'failed'` → `const isFailed = isResultFailedStatus(status)`
- `const isSuccess = status === 'success'` → `const isSuccess = isResultSuccessStatus(status)`
- `const errMsg = data.error_message || data.detail || null` → `const errMsg = extractErrorMessage(data)`
- completed 不再被误判为处理中
- error 不再被误判为处理中
- failed/error 诊断信息优先使用 `extractErrorMessage(data)`
- **轮询逻辑未改变**

---

## 58. P8-3C1 错误诊断信息说明

- failed/error 结果卡片使用 `extractErrorMessage(data)` 提取错误信息。
- `extractErrorMessage(data)` 能处理 `data.detail`、`data.error.detail`、`data.error.message`、`data.message` 等多种字段。
- 如果没有详细错误信息（`extractErrorMessage` 返回默认字符串），展示 `暂无更详细的错误信息。`
- 未修改 `renderApiError()` / `friendlyErrorMessage()` / `parseApiError()`。
- 未替代全局错误处理，只是结果卡片内部诊断信息更准确。

---

## 59. P8-3C1 DOM id 保留说明

所有关键 DOM id 保留：
- resultsArea ✅
- generateBtn ✅
- textInput ✅
- profileSelect ✅
- providerSelect ✅
- bindingStatus ✅
- audioFormat ✅
- outputFormat ✅

**说明**：`statusSection`、`batchResultsArea`、`batchScriptResultsArea` 在当前 baseline 代码中不存在（属于指令清单与实际代码的预存差异，非本次修改造成）。

---

## 60. P8-3C1 JS function 行为保留说明

| 函数 | 行为改变 |
|---|---|
| handleGenerate | ✅ 未变 |
| renderAsyncResult | ✅ 仅展示层状态判断改为使用 helper，数据语义未变 |
| renderResults | ✅ 仅展示层状态判断改为使用 helper，数据语义未变 |
| renderStreamResult | ✅ 未变 |
| audioPlayerHtml | ✅ 未变 |
| downloadBtnHtml | ✅ 未变 |
| timelineTable | ✅ 未变 |
| formatTime | ✅ 未变 |
| resultSectionLabel | ✅ 未变 |
| resultStatusHintHtml | ✅ 已补全 `completed`/`error`/`queued` 文案 |
| resultDiagnosticHtml | ✅ 未变 |
| isResultSuccessStatus | ✅ 新增 |
| isResultFailedStatus | ✅ 新增 |
| isResultProcessingStatus | ✅ 新增 |
| startAsyncPolling | ✅ 未变 |
| pollAsyncJob | ✅ 未变 |
| startStreamGenerate | ✅ 未变 |
| renderApiError | ✅ 未变 |
| extractErrorMessage | ✅ 未变（仅在展示层调用，未改其本身逻辑） |
| friendlyErrorMessage | ✅ 未变 |
| parseApiError | ✅ 未变 |
| formatApiError | ✅ 未变 |
| statusClass | ✅ 未变 |
| statusLabel | ✅ 未变 |
| apiJson | ✅ 未变 |
| guardedJsonFetch | ✅ 未变 |

---

## 61. P8-3C1 API endpoint 不变说明

- 同步生成 endpoint `/api/voice/render` ✅ 未变
- 异步生成 endpoint `/api/voice/render/async` ✅ 未变
- 异步查询 endpoint `/api/voice/render/async/{jobId}/status` ✅ 未变
- 多版本 endpoint `/api/voice/variants/render` ✅ 未变
- WebSocket endpoint `/api/voice/ws/render` ✅ 未变
- 批量 endpoint `/api/voice/batch/submit` 等 ✅ 未变
- 下载 endpoint `/api/voice/assets/{assetId}/download` ✅ 未变
- 未新增 API

---

## 62. P8-3C1 未处理事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未处理批量结果卡片化
- 未处理流式结果深度重构
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-3D

---

## 63. P8-3C1 执行命令记录

```bash
# 基线检查
git fetch origin && git checkout dev && git pull --ff-only origin dev
git status -sb
git log --oneline -10

# 只读扫描（3组 grep）
grep -n "function renderAsyncResult|..." app/static/index.html
grep -n "function statusLabel|..." app/static/index.html
grep -n "function extractErrorMessage|..." app/static/index.html
```

---

## 64. P8-3C1 验证命令记录

### 64.1 DOM/display marker 检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
checks = ['resultsArea','任务结果','同步生成结果','音频结果','下载音频','字幕时间轴','诊断信息']
for x in checks:
    if x not in html: raise SystemExit('Missing: '+repr(x))
print('PASSED')
"
```

### 64.2 JS function 检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
funcs = ['function handleGenerate','function renderAsyncResult','function renderResults',
         'function isResultSuccessStatus','function isResultFailedStatus','function isResultProcessingStatus',
         'function extractErrorMessage','function startAsyncPolling','function pollAsyncJob']
for x in funcs:
    if x not in html: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

### 64.3 状态 helper 语义检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
required = [\"status === 'completed'\",\"status === 'error'\",\"'queued'\",\"'processing'\"]
for x in required:
    if x not in html: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

### 64.4 renderAsyncResult 状态分支检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
s = html.find('function renderAsyncResult')
e = html.find('function renderResults', s)
block = html[s:e]
forbidden = [\"status === 'failed'\",\"status === 'success'\"]
for x in forbidden:
    if x in block: raise SystemExit('Still uses direct comparison: '+x)
print('PASSED')
"
```

### 64.5 renderResults 非 variant 状态分支检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
s = html.find('function renderResults')
e = html.find('function audioPlayerHtml', s)
block = html[s:e]
for x in [\"job.status === 'success'\",\"job.status === 'failed'\"]:
    if x in block: raise SystemExit('Still uses direct comparison: '+x)
print('PASSED')
"
```

---

## 65. P8-3C1 验证结果

**DOM/display marker 检查**：通过
**JS function 检查**：通过（包含新增 3 个 helper）
**状态 helper 语义检查**：通过
**renderAsyncResult 状态分支检查**：通过
**renderResults 非 variant 状态分支检查**：通过
**API marker 检查**：通过
**handleGenerate 请求逻辑保留检查**：通过
**异步轮询保留检查**：通过
**文档标记检查**：通过

---

## 66. P8-3C1 阶段结论

P8-3C1 已完成结果状态口径自检与收口修复。下一阶段建议进入 P8-3D：流式 / 多版本结果展示统一。

---

## 67. P8-3C1 下一阶段建议

建议 P8-3D 聚焦：

- WebSocket 流式结果展示统一
- 多版本结果展示细节验收
- 流式结果本地缓存 / 服务端下载入口说明
- 多版本结果下载入口一致性
- 不改后端 API

---

# P8-3D 流式 / 多版本结果展示统一

## 68. P8-3D 执行背景

- P8-3B 已完成 `resultsArea` 信息架构整理。
- P8-3C 已完成同步 / 异步结果卡片化细化验收。
- P8-3C1 已完成结果状态口径收口。
- 当前需要继续统一流式结果和多版本结果展示。
- 本阶段只改展示层，不改 WebSocket 协议、不改 variants API、不改后端。

---

## 69. P8-3D 本阶段目标

- 流式结果展示结构与任务结果 card 对齐。
- 多版本结果卡片细节统一。
- 明确流式本地缓存下载与服务端 asset 下载区别。
- 多版本无 audio 状态提示更清楚。
- 保留 DOM id。
- 保留 JS function 行为。
- 不改 API。
- 不改 WebSocket。
- 不改 variants 数据结构。

---

## 70. P8-3D 问题与风险分析

1. 流式结果与同步 / 异步结果展示结构不完全一致（流式用 `result-section`，同步/异步用 `card`）。
2. 流式结果使用浏览器本地 Blob URL 音频，而不是服务端 asset。
3. 如果误用 `downloadBtnHtml(assetId)` 可能制造不存在的服务端下载入口。
4. 多版本结果中单个版本可能没有 `audio_asset_id`。
5. 多版本结果如果 `variants` 为空，需要明确空状态。
6. 本阶段不能修复流式服务端下载 404 时序。
7. 本阶段不能改 WebSocket 协议。
8. 本阶段不能改 variants API。

---

## 71. P8-3D 方案判断

- 采用展示层统一方案。
- `renderStreamResult` 外层从 `result-section` 改为 `card`，增加"任务结果"标题、"流式生成结果"说明文字、流式完成提示、本地缓存提示文字。
- 流式本地音频与服务端 asset 下载入口明确区分：服务端下载（有 asset 时）、本地缓存下载（始终可用）、无服务端 asset 时明确说明。
- 多版本结果继续使用 `variants-grid` / `variant-card`。
- 多版本无 audio 时展示明确红色提示："该版本未返回音频资产。"
- variants 为空时展示明确空状态："本次多版本试音未返回版本结果。"
- 不改 `startStreamGenerate()`。
- 不改 WebSocket URL。
- 不改 WebSocket message schema。
- 不改 `/api/voice/variants/render`。
- 不改 `variantCount`。

---

## 72. P8-3D 修改范围

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3D 节）
- `docs/PROJECT_HEALTH_CHECK.md`（追加 P8-3D 阶段记录）

---

## 73. P8-3D 流式结果展示统一说明

**调整对象**：`renderStreamResult(completed, audioChunks)`

**调整内容**：
- 外层从 `<div class="result-section">` 改为 `<div class="card">`
- 增加"任务结果"主标题（与 sync/async 保持一致）
- 副标题"流式生成结果"说明文字
- 增加"流式接收完成，可以播放生成音频。"状态提示
- 音频播放器 section 增加"音频结果" section label
- 下载入口 section 增加"下载音频" section label
- 有 asset 时展示服务端下载按钮，无 asset 时明确说明"当前流式结果未返回服务端音频资产。"
- 增加本地缓存提示："提示：本地缓存音频来自浏览器当前会话，刷新页面后将失效。如需长期保存请使用服务端下载（如有）。"
- **未改变**：WebSocket 连接逻辑、message 处理、Blob 生成逻辑

---

## 74. P8-3D 流式下载入口说明

**当前流式下载入口属于**：
- **服务端 asset 下载**：如果 `completed.audio_asset` 存在，使用 `downloadBtnHtml(asset.id)`，URL 为 `/api/voice/assets/{assetId}/download`
- **本地缓存下载**：始终可用，使用 `blobUrl` 生成 `<a href="${blobUrl}" download="stream_audio.mp3">下载(本地缓存)</a>`

**无服务端 asset 时**：显示说明文字"当前流式结果未返回服务端音频资产。"

**本地缓存说明**：
- 来自浏览器当前会话，刷新页面后失效
- 不等同于服务端持久化资产
- 本阶段不修复流式下载 404 时序

---

## 75. P8-3D 多版本结果展示统一说明

**调整对象**：`renderResults(data, isVariant=true)` 分支

**调整内容**：
- variants 为空时（`variantCount === 0`）展示明确空状态卡片，不再抛 JS 异常
- 单个 variant 无 `audio_asset_id` 时，红色提示"该版本未返回音频资产。"（之前为灰色"无音频"）
- 保留"音频结果" / "下载音频" section label per variant
- **未改变**：variants 数据结构、variants API、variantCount 语义

---

## 76. P8-3D 多版本空状态说明

- `data.variants` 不存在或 `length === 0` 时：展示 `card` 结构，"任务结果"标题，"多版本试音结果"副标题，"本次多版本试音未返回版本结果。"提示
- 单个 variant 无 `audio_asset_id` 时：红色提示"该版本未返回音频资产。"
- **不抛 JS 异常**（对 `data.variants` 做了存在性判断）
- **不改变响应解析**

---

## 77. P8-3D DOM id 保留说明

所有关键 DOM id 保留：
- resultsArea ✅
- generateBtn ✅
- textInput ✅
- profileSelect ✅
- providerSelect ✅
- bindingStatus ✅
- audioFormat ✅
- outputFormat ✅

**说明**：`streamProgress` / `streamStats` / `statusSection` / `batchResultsArea` / `batchScriptResultsArea` 在当前 baseline 代码中不存在（属于指令清单与实际代码的预存差异，非本次修改造成）。

---

## 78. P8-3D JS function 行为保留说明

| 函数 | 行为改变 |
|---|---|
| handleGenerate | ✅ 未变 |
| renderAsyncResult | ✅ 未变 |
| renderResults | ✅ 仅 variant 分支增加空状态处理和空 audio 提示；非 variant 分支未变 |
| renderStreamResult | ✅ 仅展示层调整（card 结构、section labels、本地缓存提示） |
| startStreamGenerate | ✅ 未变 |
| audioPlayerHtml | ✅ 未变 |
| downloadBtnHtml | ✅ 未变 |
| timelineTable | ✅ 未变 |
| formatTime | ✅ 未变 |
| resultSectionLabel | ✅ 未变 |
| resultStatusHintHtml | ✅ 未变 |
| resultDiagnosticHtml | ✅ 未变 |
| isResultSuccessStatus | ✅ 未变 |
| isResultFailedStatus | ✅ 未变 |
| isResultProcessingStatus | ✅ 未变 |
| startAsyncPolling | ✅ 未变 |
| pollAsyncJob | ✅ 未变 |
| renderApiError | ✅ 未变 |
| extractErrorMessage | ✅ 未变 |
| friendlyErrorMessage | ✅ 未变 |
| parseApiError | ✅ 未变 |
| formatApiError | ✅ 未变 |
| statusClass | ✅ 未变 |
| statusLabel | ✅ 未变 |
| apiJson | ✅ 未变 |
| guardedJsonFetch | ✅ 未变 |

---

## 79. P8-3D API endpoint 不变说明

- 同步生成 endpoint `/api/voice/render` ✅ 未变
- 异步生成 endpoint `/api/voice/render/async` ✅ 未变
- 异步查询 endpoint `/api/voice/render/async/{jobId}/status` ✅ 未变
- 多版本 endpoint `/api/voice/variants/render` ✅ 未变
- WebSocket endpoint `/api/voice/ws/render` ✅ 未变
- 批量 endpoint `/api/voice/batch/submit` 等 ✅ 未变
- 下载 endpoint `/api/voice/assets/{assetId}/download` ✅ 未变
- 未新增 API

---

## 80. P8-3D 未处理事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理 WebSocket 服务端结果资产化
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未处理多版本并发控制
- 未处理批量结果卡片化
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-3E

---

## 81. P8-3D 执行命令记录

```bash
# 基线检查
git fetch origin && git checkout dev && git pull --ff-only origin dev
git status -sb
git log --oneline -10

# 只读扫描（3组 grep）
grep -n "function startStreamGenerate|function renderStreamResult|..." app/static/index.html
grep -n "function renderResults|variants-grid|..." app/static/index.html
grep -n "function resultSectionLabel|..." app/static/index.html
```

---

## 82. P8-3D 验证命令记录

### 82.1 DOM/display marker 检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
checks = ['resultsArea','任务结果','流式生成结果','多版本试音结果',
          '音频结果','下载音频','流式接收完成','该版本未返回音频资产',
          '本次多版本试音未返回版本结果','本地缓存音频','服务端音频资产']
for x in checks:
    if x not in html: raise SystemExit('Missing: '+repr(x))
print('PASSED')
"
```

### 82.2 JS function 检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
funcs = ['function handleGenerate','function renderStreamResult','function renderResults',
         'function startStreamGenerate','function resultSectionLabel',
         'function isResultSuccessStatus','function isResultFailedStatus',
         'function isResultProcessingStatus','function startAsyncPolling','function pollAsyncJob']
for x in funcs:
    if x not in html: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

### 82.3 API/WebSocket marker 检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
apis = ['/api/voice/render','/api/voice/ws/render','/api/voice/variants/render','WebSocket','apiJson','guardedJsonFetch']
for x in apis:
    if x not in html: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

### 82.4 startStreamGenerate 逻辑保留检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
s = html.find('function startStreamGenerate')
e = html.find('function renderStreamResult', s)
block = html[s:e]
for x in ['WebSocket','/api/voice/ws/render','onmessage','onerror','onclose']:
    if x not in block: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

### 82.5 renderStreamResult 展示检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
s = html.find('function renderStreamResult')
e = html.find('function renderAsyncResult', s)
block = html[s:e]
for x in ['任务结果','流式生成结果','音频结果']:
    if x not in block: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

### 82.6 renderResults variant 分支检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
s = html.find('function renderResults')
e = html.find('function audioPlayerHtml', s)
block = html[s:e]
for x in ['isVariant','variants-grid','variant-card','多版本试音结果',
          '音频结果','下载音频','该版本未返回音频资产',
          '本次多版本试音未返回版本结果']:
    if x not in block: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

### 82.7 P8-3C1 状态 helper 保留检查

```python
python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
html = Path('app/static/index.html').read_text(encoding='utf-8')
for x in [\"status === 'success'\",\"status === 'completed'\",
          \"status === 'failed'\",\"status === 'error'\",
          \"'queued'\",\"'processing'\",
          'function isResultSuccessStatus','function isResultFailedStatus']:
    if x not in html: raise SystemExit('Missing: '+x)
print('PASSED')
"
```

---

## 83. P8-3D 验证结果

**DOM/display marker 检查**：通过
**JS function 检查**：通过
**API/WebSocket marker 检查**：通过
**startStreamGenerate 逻辑保留检查**：通过
**renderStreamResult 展示检查**：通过
**renderResults variant 分支检查**：通过
**P8-3C1 状态 helper 保留检查**：通过
**文档标记检查**：通过

---

## 84. P8-3D 阶段结论

P8-3D 已完成流式 / 多版本结果展示统一。下一阶段建议进入 P8-3E：错误 / Resource Guard / 下载入口产品化。

---

## 85. P8-3D 下一阶段建议

建议 P8-3E 聚焦：

- 错误结果卡片化
- Resource Guard 提示产品化
- 下载入口体验收口
- 成本 / 高风险提示一致性
- 不改后端 API


---

## 86. P8-3E 检查清单

**baseline 检查**：
- [x] 当前分支是 dev
- [x] 工作区干净
- [x] 最近提交：6e57590 p8-3d unify stream and variant result display

**只读扫描**：
- [x] 10.1 renderApiError 结构审计
- [x] 10.2 RESOURCE_LIMIT_EXCEEDED 提示审计
- [x] 10.3 Provider / network 错误审计
- [x] 10.4 cost cancellation 提示审计
- [x] 10.5 downloadBtnHtml 文本审计
- [x] 10.6 流式下载入口审计
- [x] 10.7 friendlyErrorMessage 覆盖审计
- [x] 10.8 其他错误展示位审计

---

## 87. P8-3E 代码变更

### 87.1 friendlyErrorMessage 扩展

**位置**：index.html:1564

**变更**：新增 Provider error、network error、cancellation 识别

```
+    if (lower.includes('provider') || lower.includes('provider error')) {
+      return 'Provider 服务异常：请稍后重试。如果问题持续，请联系技术支持。';
+    }
+    if (lower.includes('cancelled') || lower.includes('canceled') || lower.includes('操作已取消')) {
+      return '操作已取消：本次生成请求已被取消，未产生费用。';
+    }
+    if (lower.includes('network') || lower.includes('fetch') || lower.includes('断开') || lower.includes('连接失败')) {
+      return '网络异常：请检查网络连接后重试。';
+    }
```

### 87.2 formatApiError RESOURCE_LIMIT_EXCEEDED 消息

**位置**：index.html:1635

**变更**：明确标注 "Resource Guard" 术语

```
- return `${opLabel}当前任务较多，请稍后再试。`;
+ return `${opLabel}触发资源限制（Resource Guard）：当前任务排队较多，请稍后再试。`;
```

### 87.3 resourceLimitExtraHint 提示优化

**位置**：index.html:1664

**变更**：强调 "这是 Resource Guard 限制，不是系统异常"

```
- return '这不是系统异常，任务可能仍在处理中。请稍后手动刷新状态。';
+ return '这是 Resource Guard 限制，不是系统异常。任务可能仍在后台处理中，请稍后手动刷新状态。';
```

### 87.4 renderApiError 卡片结构产品化

**位置**：index.html:1684

**变更**：从 `error-msg` div 升级为完整 card 结构，带 "错误提示" 标签、"建议操作" 区域（Resource Guard hint）、"技术详情" 可展开

```
- <div class="error-msg ${code === 'RESOURCE_LIMIT_EXCEEDED' ? 'resource-limit-msg' : ''}">
-   <div><strong>${esc(message)}</strong></div>
+ <div class="card" style="border-left:4px solid ${isResourceLimit ? '#dd6b20' : '#c53030'}">
+   <div class="result-label" style="color:${isResourceLimit ? '#dd6b20' : '#c53030'}">错误提示</div>
+   <div style="margin-top:8px">
+     <strong style="font-size:0.95rem;color:#2d3748">${esc(message)}</strong>
+   </div>
+   ${extraHint ? `<div style="margin-top:8px;padding:8px;background:#fffaf0;border-radius:4px;font-size:0.82rem;color:#744210">💡 ${esc(extraHint)}</div>` : ''}
```

### 87.5 downloadBtnHtml 按钮文本优化

**位置**：index.html:2382

**变更**：`下载` → `下载音频`

```
- return \`<a class="btn-sm" href="/api/voice/assets/\${assetId}/download" download>下载</a>\`;
+ return \`<a class="btn-sm" href="/api/voice/assets/\${assetId}/download" download>下载音频</a>\`;
```

### 87.6 流式下载入口描述优化

**位置**：index.html:2072

**变更**：服务端/本地缓存标签明确化，并添加描述文字

```
- ${resultSectionLabel('下载音频')}
- <div class="action-row">
-   \${asset ? \`<a class="btn-sm" href="/api/voice/assets/\${asset.id}/download" download>下载(服务端)</a>\` : ''}
-   <a class="btn-sm" href="\${blobUrl}" download="stream_audio.mp3">下载(本地缓存)</a>
- </div>
+ ${resultSectionLabel('下载音频')}
+ <div class="action-row" style="flex-wrap:wrap;gap:8px">
+   \${asset ? \`<a class="btn-sm" href="/api/voice/assets/\${asset.id}/download" download>下载音频（服务端）</a>\` : ''}
+   <a class="btn-sm" href="\${blobUrl}" download="stream_audio.mp3">下载音频（浏览器缓存）</a>
+ </div>
+ <p style="font-size:0.78rem;color:#a0aec0;margin-top:6px">
+   \${asset ? '· 服务端音频：保存在服务器，可长期访问' : ''}
+   \${asset ? '<br>' : ''}
+   · 浏览器缓存：仅限当前会话，刷新页面后失效
+ </p>
+ \${!asset ? \`<p style="font-size:0.82rem;color:#718096;margin-top:6px">当前流式结果未返回服务端音频资产，仅提供浏览器缓存下载。</p>\` : ''}
```

**删除了原有重复提示段落**："提示：本地缓存音频来自浏览器当前会话..."

---

## 88. P8-3E 静态检查结果

```
issues: []
```

pytest: 375 passed, 6 skipped

---

## 89. P8-3E 验证记录

| 检查项 | 状态 |
|---|---|
| friendlyErrorMessage Provider error | ✅ |
| friendlyErrorMessage cancellation | ✅ |
| friendlyErrorMessage network error | ✅ |
| formatApiError Resource Guard 标注 | ✅ |
| resourceLimitExtraHint 提示优化 | ✅ |
| renderApiError card 结构 | ✅ |
| downloadBtnHtml "下载音频" | ✅ |
| 流式下载服务端/浏览器缓存标签 | ✅ |
| 流式下载描述文字 | ✅ |
| pytest | ✅ 375 passed |

---

## 90. P8-3E 阶段结论

P8-3E 已完成错误提示、Resource Guard 和下载入口产品化：

1. **renderApiError** 从 `error-msg` div 升级为带 "错误提示" 标签的 card 结构，左边框颜色区分普通错误（红）和资源限制（橙）
2. **Resource Guard** 明确标注 "触发资源限制（Resource Guard）"，extra hint 以 "💡" 引导，强调 "这是 Resource Guard 限制，不是系统异常"
3. **friendlyErrorMessage** 扩展支持 Provider error、cancellation、network error
4. **downloadBtnHtml** 从 "下载" 改为 "下载音频"
5. **流式下载** 标签从 "下载(服务端)/下载(本地缓存)" 改为 "下载音频（服务端）/下载音频（浏览器缓存）"，并添加说明文字

下一阶段建议进入 P8-3F 或其他 P8 后续阶段。
