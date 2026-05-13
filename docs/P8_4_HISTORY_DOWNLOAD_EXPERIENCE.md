
# P8-4 历史记录和下载体验

## 1. 当前基线

- 仓库：HLPJay/voice-lab
- 分支：dev
- 前置阶段：P8-3F 已完成
- 最新提交：3669598 p8-3f close result display acceptance
- 当前目标：进入 P8-4，但 P8-4A 只做审查

## 2. P8-4 产品目标

P8-4 的目标是把历史记录整理为更适合创作工作台使用的历史任务找回、音频播放、下载和筛选体验。

目标用户流程：

```
生成音频
↓
离开当前结果区
↓
进入历史记录
↓
找到过去任务
↓
播放音频
↓
下载音频
↓
查看字幕 / 状态 / 错误
↓
必要时加载更多历史任务
```

## 3. 当前历史记录 DOM id

| DOM id | 用途 | 当前风险 |
|---|---|---|
| `tab-history` | 历史 tab 内容容器，DOM id 为 `tab-history`，位于 tab 切换体系中 | 与 P8-1 定义的 tab 体系一致，风险低 |
| `historyCard` | 包裹整个历史区域的 card 容器，`<div class="card" id="historyCard">` | 仅作为外层容器，风险低 |
| `historyToggle` | 可点击的 card-title 区域，点击触发 `toggleHistory()`，标题文字显示 "历史记录 ▾" 或 "历史记录 ▴" | 折叠/展开状态依赖 innerHTML 更新标题符号，但无状态变量标记展开状态 |
| `historyArea` | 历史记录列表的实际可见区域，初始 `display:none`，展开后显示 | 初始隐藏，用户必须主动点击展开；无自动展开逻辑 |
| `historyList` | 历史记录列表容器，用于渲染历史任务条目 | 直接 innerHTML 替换，无虚拟滚动或分片渲染 |
| `loadMoreHistory` | "加载更多"按钮，初始 `display:none`，有更多数据时显示 | 仅显示/隐藏切换，无"没有更多了"提示文本 |

### 其他历史相关 DOM id

当前未发现其他历史记录相关的附加 DOM id。

## 4. 当前历史记录 JS 函数

### 历史专用函数

| 函数 | 用途 | 依赖 DOM | 风险 |
|---|---|---|---|
| `toggleHistory()` | 展开/收起历史区域。展开时如果 `_historyOffset` 为 0，自动调用 `loadHistory(0)` | `historyArea`, `historyToggle` | 展开状态通过 `isOpen = area.style.display !== 'none'` 判定，非独立状态变量 |
| `loadHistory(offset)` | 异步加载历史记录列表。参数 offset 为分页偏移量。首次加载时清空列表并显示"加载中…"。请求 `/api/voice/jobs?limit=10&offset={offset}`，成功后将 jobs 渲染为纯文本行。 | `historyList`, `loadMoreHistory`, `_historyOffset`, `_historyTotal`, `_historyLoading` | 列表为纯 div 行，非任务 card 结构；不使用 P8-3 的 `audioPlayerHtml` / `downloadBtnHtml` / `resultStatusHintHtml` 等 helper；加载失败仅显示"加载失败"文本 |
| `loadMoreHistory()` | 点击"加载更多"按钮触发，调用 `loadHistory(_historyOffset)` | `_historyOffset`, `_historyLoading` | 直接调用 loadHistory，无额外保护 |

### 全局/通用变量

| 变量 | 用途 | 风险 |
|---|---|---|
| `_historyOffset` | 当前已加载的历史记录数量（即下次加载的 offset） | 在 loadHistory 中维护，与 `_historyTotal` 比较决定是否还有更多 |
| `_historyTotal` | 服务器返回的总记录数 | 从 API 响应 `data.total` 获取 |
| `_historyLoading` | 加载锁，防止重复请求 | 粒度较粗，页面初始化时自动调用一次 |

### 通用函数复用情况

| 函数 | 是否被历史记录复用 | 说明 |
|---|---|---|
| `audioPlayerHtml(assetId)` | **否** | 历史记录列表当前没有音频播放功能 |
| `downloadBtnHtml(assetId)` | **否** | 历史记录列表当前没有下载入口 |
| `timelineTable(timeline)` | **否** | 历史记录列表当前没有字幕/timeline 展示 |
| `statusLabel(s)` | **否** | 历史记录使用 `job.status` 直接展示状态文本（英文），未使用 `statusLabel` 的映射 |
| `statusClass(s)` | **否** | 历史记录使用 `<span class="job-status status-${job.status}">` 直接输出 status 英文 |
| `renderApiError(err, options)` | **否** | 历史记录加载失败仅显示纯文本"加载失败"，未使用 `renderApiError` |
| `resultDiagnosticHtml(message)` | **否** | 历史记录中失败任务不展示诊断信息 |
| `resultStatusHintHtml(status)` | **否** | 历史记录列表不展示状态提示文本 |
| `resultSectionLabel(text)` | **否** | 历史记录列表不使用 section label |
| `isResultSuccessStatus(status)` | **否** | 历史记录列表不使用状态语义 helper |
| `isResultFailedStatus(status)` | **否** | 同上 |
| `isResultProcessingStatus(status)` | **否** | 同上 |
| `esc(s)` | **是** | 用于转义文本 |

## 5. 当前历史记录 API endpoint 依赖

| 功能 | endpoint / URL | 调用函数 | 是否高风险 |
|---|---|---|---|
| 历史记录列表 | `/api/voice/jobs?limit=10&offset={offset}` | `loadHistory()` | 低 - 只读 GET 请求 |
| 历史记录分页 | 同上，通过 `offset` 和 `limit=10` 参数 | `loadHistory()` | 低 |
| 历史任务详情 | 未发现直接调用 | - | - |
| 音频 asset 播放 | `/api/voice/assets/{assetId}/download`（通过 `audioPlayerHtml` 生成） | `renderAsyncResult`, `renderResults`, `renderStreamResult` | 低 - 用于当前结果，非历史记录 |
| 音频 asset 下载 | `/api/voice/assets/{assetId}/download`（通过 `downloadBtnHtml` 生成） | `renderAsyncResult`, `renderResults`, `renderStreamResult` | 低 - 同上 |
| 字幕 asset 下载 | `/api/voice/assets/{subId}/download` | 批量模块 `handleBatchPlay`, `renderBatchResultPlayer` | 低 - 仅用于批量结果 |
| 历史记录删除 | 未发现直接调用 | - | - |

### 说明

- 历史记录列表使用 `/api/voice/jobs` 接口，每次请求 `limit=10` 条，通过 `offset` 参数分页。
- 历史记录列表本身不提供播放、下载、字幕展示等能力。
- `audioPlayerHtml` 和 `downloadBtnHtml` 只用于**当前任务结果**（`resultsArea`）和批量结果，**不被历史记录复用**。
- 当前没有历史记录详情 endpoint。
- 当前没有历史记录删除 endpoint。

## 6. 当前用户路径

### 6.1 历史记录入口路径

1. 用户点击导航 tab 中的"历史"按钮（`data-tab="history"`）。
2. 页面显示 `#tab-history` 内容区，包含 `#historyCard`。
3. `#historyArea` 初始为 `display:none`，用户需点击 `#historyToggle`（标题"历史记录 ▾"）展开。
4. 点击展开后，标题变为"历史记录 ▴"。
5. 如果是首次展开（`_historyOffset === 0`），自动调用 `loadHistory(0)` 加载数据。
6. 页面初始化时（`loadHistory(0)` 在第 1849 行被调用），但 `#historyArea` 默认隐藏，因此渲染结果不可见。

**注意点**：
- 历史区域默认折叠。
- 每次切换 tab 离开再回来，历史区域状态会重置为隐藏。
- 页面初始化时已加载历史数据（`loadHistory(0)` 被调用），但由于 `display:none`，用户无法立即看到。

### 6.2 历史记录加载路径

1. 调用 `loadHistory(offset)`。
2. 传入 offset，默认 `limit=10`。
3. 发送 GET 请求 `/api/voice/jobs?limit=10&offset={offset}`。
4. 响应格式：`{ total: number, jobs: array }`。
5. **加载成功**：
   - offset === 0 时清空列表。
   - 对每个 job 创建一个 div，包含：时间、类型标签（单条/异步/流式）、状态标签、文本片段（前 30 字符）、provider。
   - 列表行使用 `document.createDocumentFragment()` 追加。
   - 更新 `_historyOffset = offset + jobs.length`。
   - 如果 `_historyOffset < _historyTotal`，显示"加载更多"按钮。
6. **加载失败**：
   - 仅显示纯文本 `<div style="font-size:0.82rem;color:#c53030">加载失败</div>`。
   - 不使用 `renderApiError`，不展示技术详情。
7. **加载更多**：
   - 点击"加载更多"按钮触发 `loadMoreHistory()`。
   - 调用 `loadHistory(_historyOffset)`。
   - 更多数据以 `appendChild` 方式追加到列表末尾。
   - 无数据时按钮隐藏。
   - 无"没有更多了"提示文本。

### 6.3 历史任务播放路径

**当前状态：历史记录中未发现音频播放入口。**

- 历史记录列表仅展示文本行（时间、类型、状态、文本片段、provider）。
- 没有 `audio` 元素，没有 `audioPlayerHtml` 调用。
- 没有 asset / URL / HEX / blob 播放方式。
- 用户无法在历史记录中直接播放历史任务的音频。
- 如果用户想播放历史任务的音频，目前没有提供该能力。

### 6.4 历史任务下载路径

**当前状态：历史记录中未发现下载入口。**

- 历史记录列表没有下载按钮。
- 没有 `downloadBtnHtml` 调用。
- 没有调用 `/api/voice/assets/{assetId}/download`。
- 用户无法在历史记录中下载历史任务的音频。
- 当前下载入口仅存在于当前任务结果区（`resultsArea`）和批量结果区。

### 6.5 历史任务状态路径

**当前状态：历史记录使用英文状态标签，未复用 P8-3 状态 helper。**

历史记录列表中状态展示方式：
- `<span class="job-status status-${job.status}">${esc(job.status)}</span>`
- 直接输出后端返回的 status 原文（英文，如 `success`, `failed`, `running`, `pending`, `processing`）。
- 使用 CSS class `status-{status}` 控制颜色（通过 `.job-status.status-failed` 等样式）。
- 未使用 `statusLabel(s)` 的中文映射。
- 未使用 `statusClass(s)`。
- 未使用 `resultStatusHintHtml(status)`。
- 未使用 `isResultSuccessStatus` / `isResultFailedStatus` / `isResultProcessingStatus` helper。
- 失败任务不展示诊断信息（未调用 `resultDiagnosticHtml`）。

### 6.6 历史字幕 / timeline 路径

**当前未发现历史记录字幕展示。**

- 历史记录列表不展示字幕时间轴。
- 未调用 `timelineTable`。
- 当前字幕展示仅存在于以下位置：
  - `renderAsyncResult`（当前异步任务结果）
  - `renderResults`（当前同步任务结果）
  - 批量结果区

### 6.7 历史空状态路径

1. **没有历史记录时**：
   - 当 offset === 0 且 jobs 为空数组时，显示：
     `<div style="font-size:0.82rem;color:#718096">暂无历史记录</div>`
   - 隐藏"加载更多"按钮。
   - 这是一个简单的灰色文本提示，没有卡片或插画等视觉设计。

2. **分页到底时**：
   - "加载更多"按钮隐藏。
   - 无"没有更多了"等提示文本。
   - 用户无法区分是"加载失败"还是"没有更多记录"。

### 6.8 历史错误路径

1. **历史列表加载失败**：
   - 显示纯文本：`<div style="font-size:0.82rem;color:#c53030">加载失败</div>`
   - 仅 offset === 0 时显示。
   - 未使用 `renderApiError`。
   - 无技术详情。
   - 无 Resource Guard 友好提示。

2. **历史中的失败任务**：
   - 状态显示为 "failed" 或 "error" 英文标签。
   - 无错误诊断信息。
   - 无 `resultDiagnosticHtml` 调用。

## 7. 当前问题与风险

### 7.1 历史记录仍偏工程列表

历史记录当前为纯文本行列表（时间、类型、状态、文本片段、provider），每行用 flex 布局 + border-bottom 分隔。这更像是测试面板时期的工程任务列表，而非创作工作台的历史任务卡片。

### 7.2 历史记录缺少任务 card 结构

对比 P8-3 已 productize 的当前任务结果 card（包含音频播放、下载、字幕、状态 helper、诊断信息），历史记录没有任何 card 结构：

- 无 `resultSectionLabel` 区段划分
- 无 `audioPlayerHtml` 音频播放
- 无 `downloadBtnHtml` 下载入口
- 无 `timelineTable` 字幕展示
- 无 `resultStatusHintHtml` 状态提示
- 无 `resultDiagnosticHtml` 诊断信息

### 7.3 历史记录与 P8-3 当前任务结果 card 不一致

| 能力 | P8-3 当前结果 card | 历史记录 |
|---|---|---|
| 音频播放 | `audioPlayerHtml`, `audio` | 无 |
| 音频下载 | `downloadBtnHtml` | 无 |
| 字幕/timeline | `timelineTable` | 无 |
| 状态标签 | `statusLabel`（中文） | 直接输出英文 status |
| 状态语义 | `isResultSuccessStatus` 等 | 无 |
| 状态提示 | `resultStatusHintHtml` | 无 |
| 诊断信息 | `resultDiagnosticHtml` | 无 |
| 错误展示 | `renderApiError` | "加载失败"文本 |
| Resource Guard | 橙色提示 card | 无 |
| 空状态 | 简单文本 | 简单文本 |

### 7.4 历史播放/下载入口不清楚

- 历史记录中完全没有音频播放入口。
- 历史记录中完全没有下载入口。
- 用户离开当前结果区后，无法找回历史任务的音频。

### 7.5 历史记录不能区分 asset / URL / HEX / blob

- 历史记录列表不涉及任何音频数据处理。
- 当前结果区支持：asset_id（服务端播放/下载）、blob URL（流式缓存）、HEX（音色试听）、URL（供应商直链）。
- 历史记录的 asset 数据仍需后端返回。

### 7.6 历史记录不支持字幕/timeline 展示

历史记录列表完全不涉及字幕数据。

### 7.7 历史记录空状态不友好

- "暂无历史记录"为简单灰色文本，无视觉设计。
- 分页到底后无提示文本，用户无法区分是"加载失败"还是"没有更多记录"。
- 加载更多按钮仅隐藏，无"没有更多了"文案。

### 7.8 历史记录加载失败不产品化

- 仅显示"加载失败"文本。
- 无 `renderApiError` 使用。
- 无错误详情展示。
- 无 Resource Guard 区分。
- 无重试提示。

### 7.9 历史记录分页/加载更多不够友好

- "加载更多"按钮为简单按钮，无加载动画。
- 分页到末尾后按钮直接消失，无"没有更多了"结束提示。
- offset/limit 分页逻辑偏工程化。

### 7.10 历史记录需要搜索/筛选

当前历史记录无搜索或筛选功能。随着任务数量增加，用户可能需要：
- 按状态筛选（成功/失败/处理中）
- 按时间段筛选
- 按生成类型筛选（同步/异步/流式/多版本）
- 按文本关键词搜索

### 7.11 历史记录适合进入 P8-4B 做 UI 层整理

当前历史记录作为工程列表，基础功能（加载、分页、空状态、错误处理）已实现，但展示形式偏工程化。适合在 P8-4B 做信息架构整理，不改变后端 API。

### 7.12 P8-4 不应改后端 API

P8-4 专注于前端展示层优化，不应改动后端 API。当前 `/api/voice/jobs` 接口返回的数据结构（total, jobs, job.status, job.audio_asset, job.subtitle_asset）已足够支持历史任务卡片化。

### 7.13 P8-4 不应改下载接口

当前下载接口 `/api/voice/assets/{assetId}/download` 正常工作，P8-4 不应修改。

### 7.14 P8-4 需要复用 P8-3 的 helper

P8-4B 建议复用以下 P8-3 helper：
- `audioPlayerHtml` / `downloadBtnHtml`：用于历史任务音频播放和下载
- `resultStatusHintHtml`：用于历史任务状态提示
- `resultDiagnosticHtml`：用于历史失败任务的诊断信息
- `resultSectionLabel`：用于历史任务 card 区段划分
- `statusLabel` / `statusClass`：用于历史任务状态标签统一
- `timelineTable`：用于历史任务字幕展示
- 可能需要新增历史记录专用的 `renderHistoryItemCard` 或 `renderHistoryCard` 函数

### 7.15 桌面宽屏布局问题

桌面宽屏布局问题应继续作为 P8-UX1 遗留，不夹在 P8-4A 中处理。详见第 9 节。

## 8. P8-4 分阶段建议

建议：

| 阶段 | 目标 |
|---|---|
| P8-4A | 历史记录和下载体验现状审查 |
| P8-4B | 历史记录信息架构整理 |
| P8-4C | 历史任务卡片化 |
| P8-4D | 历史播放 / 下载入口产品化 |
| P8-4E | 历史筛选 / 搜索 / 空状态优化 |
| P8-4F | P8-4 验收与健康检查收口 |

说明：

- P8-UX1 桌面宽屏布局与响应式适配作为独立遗留阶段，不夹在 P8-4A 中处理。
- 前端静态文件拆分也应作为独立工程化阶段处理，不夹在 P8-4 中处理。

### P8-4B 建议工作内容

基于 P8-4A 审查结果，P8-4B 建议：
1. 将历史记录从纯文本行列表改为任务 card 列表。
2. 每个历史任务 card 包含：时间、类型、状态、文本内容。
3. 复用 P8-3 的 `statusLabel` / `statusClass` 统一状态展示。
4. 复用 P8-3 的 `resultStatusHintHtml` 展示状态提示。
5. 失败任务显示 `resultDiagnosticHtml` 诊断信息。
6. 保留加载更多分页能力。
7. 改进空状态和加载失败展示。
8. 不改后端 API，不改 JS 业务逻辑。

## 9. P8-UX1 遗留项记录

当前 `app/static/index.html` 仍使用偏测试面板时期的窄版单列布局：

- `.container { max-width: 800px; }`
- 桌面宽屏下页面只占用中间较窄区域
- 横向空间利用不足
- 创作工作台、音色列表、结果卡片在桌面端可以进一步双栏化或宽屏化
- 当前已有基础移动端适配，但还不是完整的桌面宽屏工作台布局

该问题不在 P8-4A 处理，也不夹在 P8-4 中处理。

后续单独进入：

**P8-UX1：桌面宽屏布局与响应式适配**

P8-UX1 目标：
- 桌面端容器从 800px 扩展到 1120px / 1200px / 1280px 级别
- 创作工作台在桌面端支持左右分区
- 音色列表充分利用宽屏
- 手机端继续保持单列
- 不改后端 API
- 不改 JS 业务逻辑
- 不拆 React / Vue
- 不引入构建工具

## 10. P8-4A 执行记录

以下为 P8-4A 实际执行过的命令记录：

### 10.1 基线准备

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -20
```

结果：
- 当前分支：dev
- 工作区干净（仅 docs/prompts/ 未跟踪目录，不影响）
- 最近提交验证通过：
  ```
  3669598 p8-3f close result display acceptance
  bcb1448 p8-3e productize errors guards and downloads
  6e57590 p8-3d unify stream and variant result display
  1d1fb2e p8-3c1 align result status semantics
  488eca3 p8-3c refine sync async result cards
  d5d0655 p8-3b reorganize results area information architecture
  ```

### 10.2 DOM 扫描

```bash
findstr /n "tab-history historyCard historyToggle historyArea historyList loadMoreHistory" app/static/index.html
```

扫描结果见第 3 节。

### 10.3 函数扫描

```bash
findstr /n "function toggleHistory function loadHistory function loadMoreHistory function renderHistory function renderHistoryItem historyOffset historyLimit historyLoaded historyExpanded" app/static/index.html
```

合并补充搜索：
```bash
findstr /n "history History records loadMore page offset limit" app/static/index.html
```

扫描结果见第 4 节。

### 10.4 API endpoint 扫描

```bash
findstr /n "apiJson( guardedJsonFetch( fetch(" app/static/index.html
```

扫描结果见第 5 节。

### 10.5 下载入口扫描

```bash
findstr /n "downloadBtnHtml audioPlayerHtml /api/voice/assets/ download 下载音频 audio_asset audio_asset_id asset_id blobUrl audio_url audio_hex" app/static/index.html
```

### 10.6 音频播放入口扫描

```bash
findstr /n "audioPlayerHtml audio-player <audio audio_asset audio_asset_id audio_url audio_hex hex-player" app/static/index.html
```

### 10.7 字幕/timeline 扫描

```bash
findstr /n "timelineTable timeline subtitle 字幕 subtitle_asset subtitle_url" app/static/index.html
```

### 10.8 状态与错误展示扫描

```bash
findstr /n "statusLabel statusClass resultStatusHintHtml renderApiError resultDiagnosticHtml error failed RESOURCE_LIMIT_EXCEEDED history" app/static/index.html
```

### 10.9 搜索/筛选/空状态扫描

```bash
findstr /n "historySearch searchHistory filterHistory empty 暂无 无历史 历史记录为空" app/static/index.html
```

### 10.10 P8-3 result helper 扫描

```bash
findstr /n "resultSectionLabel resultStatusHintHtml resultDiagnosticHtml isResultSuccessStatus isResultFailedStatus isResultProcessingStatus downloadBtnHtml audioPlayerHtml timelineTable" app/static/index.html
```

### 10.11 文档差异检查

```bash
git diff --check
git diff --stat
```

### 10.12 测试执行

```bash
python -m pytest tests/ -x -q
```

## 11. P8-4A 验收结果

### 测试结果

```text
375 passed, 6 skipped
```

### diff 检查

```text
git diff --check: 无 whitespace error
```

### 文档标记检查

```text
P8-4A documentation marker check passed
```

### 是否执行真实 MiniMax smoke test

**未执行**（P8-4A 是审查与文档阶段，不涉及后端 API 改造，避免消耗额度）

## 12. P8-4A 结论

P8-4A 只完成历史记录和下载体验现状审查和文档化，不修改前端，不修改后端。下一阶段建议进入 P8-4B：历史记录信息架构整理。
