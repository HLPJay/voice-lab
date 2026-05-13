
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

---

# P8-4B 历史记录信息架构整理

## 13. P8-4B 执行背景

- P8-4A 已完成现状审查。
- 当前历史记录是纯文本工程列表。
- 当前历史记录缺少任务 card 结构。
- 当前历史记录没有播放/下载入口。
- 本阶段先做历史记录信息架构整理。
- 本阶段不改后端、不改 API、不改下载接口。

---

## 14. P8-4B 本阶段目标

- 历史记录从纯文本行改为历史任务 card。
- 状态展示复用 P8-3 helper。
- 失败任务展示诊断信息。
- 空状态更友好。
- 加载失败更友好。
- 加载更多/到底提示更清楚。
- 保留 DOM id。
- 保留 JS function 行为。
- 不改 API。

---

## 15. P8-4B 问题与风险分析

1. 历史记录当前为纯文本行，信息层级弱。
2. 历史记录当前直接输出英文 status。
3. 历史记录当前加载失败只显示"加载失败"。
4. 历史记录当前分页到底无提示。
5. 历史记录当前没有播放/下载入口。
6. 本阶段如果强行新增播放/下载，可能依赖后端数据字段，风险较高。
7. 本阶段应先完成信息架构整理，再进入 P8-4C/P8-4D。
8. 本阶段不能改 `/api/voice/jobs`。
9. 本阶段不能改下载接口。

---

## 16. P8-4B 方案判断

- 采用前端展示层整理方案。
- 新增或调整历史 card helper。
- 复用 `statusLabel` / `statusClass`。
- 复用 `resultStatusHintHtml`。
- 失败任务复用 `resultDiagnosticHtml`。
- 不新增播放/下载入口。
- 不新增搜索/筛选。
- 不改 `loadHistory(offset)` 请求语义。
- 不改分页状态。
- 不改后端 API。

---

## 17. P8-4B 修改范围

记录实际修改：

- `app/static/index.html` — 历史记录 card 化、新增 helper 函数
- `docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md` — 追加 P8-4B 章节
- `docs/PROJECT_HEALTH_CHECK.md` — 更新当前最新状态摘要

---

## 18. P8-4B 历史任务 card 结构说明

调整后的 card 结构：

1. 历史任务标题
2. 类型 / 状态 / 时间
3. 生成文本片段（80字符截断）
4. 任务信息（provider / job_id）
5. 状态说明（resultStatusHintHtml）
6. 失败诊断信息（resultDiagnosticHtml，如有）
7. 后续播放/下载入口提示

---

## 19. P8-4B 状态展示统一说明

- 历史任务状态展示从英文原文改为 `statusLabel(job.status)`。
- 状态 class 使用 `statusClass(job.status)`。
- 状态说明使用 `resultStatusHintHtml(job.status)`。
- 是否改变状态语义：否。

---

## 20. P8-4B 空状态与错误展示说明

- 无历史记录：`historyEmptyStateHtml()` 返回"暂无历史记录"+"完成一次音频生成后，历史任务会出现在这里。"
- 加载失败：`historyLoadErrorHtml(message)` 返回"历史记录加载失败"+"请确认本地服务仍在运行，稍后再试。"
- 分页到底：`historyEndStateHtml()` 返回"没有更多历史记录了。"
- 是否新增 API：否。
- 是否新增重试：否。

---

## 21. P8-4B 播放/下载入口处理说明

- 本阶段未新增完整播放入口。
- 本阶段未新增完整下载入口。
- 原因：P8-4B 聚焦信息架构整理，播放/下载产品化留给 P8-4C/P8-4D。
- 未改 `/api/voice/assets/{assetId}/download`。
- 未伪造不存在的下载入口。

---

## 22. P8-4B DOM id 保留说明

静态检查结果：所有关键 DOM id 仍存在。

- `tab-history` — 存在
- `historyCard` — 存在
- `historyToggle` — 存在
- `historyArea` — 存在
- `historyList` — 存在
- `loadMoreHistory` — 存在

---

## 23. P8-4B JS function 行为保留说明

静态检查结果：所有关键函数仍存在。

| 函数 | 用途 | API 调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `toggleHistory` | 展开/收起历史记录 | 无 | DOM 状态 | 无 |
| `loadHistory(offset)` | 加载历史记录 | `/api/voice/jobs` | `_historyOffset/_historyTotal/_historyLoading` | 渲染逻辑改为 card |
| `loadMoreHistory` | 加载更多 | 调用 loadHistory | 同上 | 无 |
| `statusLabel(s)` | 状态中文 label | 无 | 无 | 无 |
| `statusClass(s)` | 状态 CSS class | 无 | 无 | 无 |
| `resultStatusHintHtml(status)` | 状态说明 HTML | 无 | 无 | 无 |
| `resultDiagnosticHtml(message)` | 诊断信息 HTML | 无 | 无 | 无 |
| `isResultFailedStatus(status)` | 判断失败状态 | 无 | 无 | 无 |
| `extractErrorMessage(data)` | 提取错误信息 | 无 | 无 | 无 |
| `esc(s)` | HTML 转义 | 无 | 无 | 无 |
| `apiJson` | API JSON helper | 无 | 无 | 无 |

新增 helper（P8-4B）：

| 函数 | 用途 | API 调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `historyJobCardHtml(job)` | 渲染单条历史 job card | 无 | 无 | 仅返回 HTML 字符串 |
| `historyEmptyStateHtml()` | 空状态 HTML | 无 | 无 | 仅返回 HTML 字符串 |
| `historyLoadErrorHtml(message)` | 加载失败 HTML | 无 | 无 | 仅返回 HTML 字符串 |
| `historyEndStateHtml()` | 到底提示 HTML | 无 | 无 | 仅返回 HTML 字符串 |

---

## 24. P8-4B API endpoint 不变说明

- 历史记录列表 endpoint 未变：`/api/voice/jobs`
- 分页参数未变：`limit=10&offset={offset}`
- 下载 endpoint 未变：`/api/voice/assets/`
- 未新增 API。
- 未删除 API。

---

## 25. P8-4B 未处理事项

必须写明：

- 未新增历史播放入口
- 未新增历史下载入口
- 未新增历史字幕/timeline 展示
- 未新增历史详情页
- 未新增历史搜索
- 未新增历史筛选
- 未新增历史删除
- 未改后端 API
- 未改下载接口
- 未处理桌面宽屏 P8-UX1
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-4C

---

## 26. P8-4B 执行命令记录

### 基线检查

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -20
```

### 静态检查

```bash
grep -n "tab-history\|historyCard\|historyToggle\|historyArea\|historyList\|loadMoreHistory" app/static/index.html
grep -n "function toggleHistory\|function loadHistory\|function loadMoreHistory\|_historyOffset\|_historyTotal\|_historyLoading" app/static/index.html
grep -n "/api/voice/jobs\|limit=10\|offset=" app/static/index.html
grep -n "function statusLabel\|function statusClass\|function resultStatusHintHtml\|function resultDiagnosticHtml\|function resultSectionLabel\|function esc" app/static/index.html
```

### 文档标记检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM/display marker check passed")
PY
```

---

## 27. P8-4B 验证命令记录

### DOM marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4B DOM/display marker check passed")
PY
```

### JS function 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = ["function toggleHistory","function loadHistory","function loadMoreHistory","function statusLabel","function statusClass","function resultStatusHintHtml","function resultDiagnosticHtml","function isResultFailedStatus","function extractErrorMessage","function esc","function apiJson"]
missing = [x for x in required_functions if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4B JS function check passed")
PY
```

### History helper 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_any = ["historyJobCardHtml","历史任务","resultStatusHintHtml","resultDiagnosticHtml"]
missing = [x for x in required_any if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4B history helper/card check passed")
PY
```

### API marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_api_markers = ["/api/voice/jobs","limit=10","offset=","apiJson","/api/voice/assets/"]
missing = [x for x in required_api_markers if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4B API marker check passed")
PY
```

### loadHistory 语义保留检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function loadHistory")
end = html.find("function loadMoreHistory", start)
block = html[start:end]
required = ["/api/voice/jobs","limit=10","offset=","_historyOffset","_historyTotal","_historyLoading"]
missing = [x for x in required if x not in block]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4B loadHistory semantic retention check passed")
PY
```

### 不新增播放/下载入口检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function historyJobCardHtml")
end_candidates = [html.find("function loadMoreHistory", start), html.find("function toggleHistory", start)]
end_candidates = [x for x in end_candidates if x > start]
end = max(end_candidates) if end_candidates else start + 12000
block = html[start:end]
forbidden = ["audioPlayerHtml(","downloadBtnHtml(","<audio"]
found = [x for x in forbidden if x in block]
if found: raise SystemExit(f"Should not add: {found}")
print("P8-4B no playback/download entry check passed")
PY
```

### 全量测试

```bash
python -m pytest tests/ -x -q
```

---

## 28. P8-4B 验证结果

### git 检查

```
## dev...origin/dev
 M app/static/index.html
app/static/index.html | 99 +++++++++++++++++++++++++++++++++++++++++++--------
1 file changed, 85 insertions(+), 14 deletions(-)
```

### DOM marker 检查

```
P8-4B DOM/display marker check passed
```

### JS function 检查

```
P8-4B JS function check passed
```

### History helper 检查

```
P8-4B history helper/card check passed
```

### API marker 检查

```
P8-4B API marker check passed
```

### loadHistory 语义保留检查

```
P8-4B loadHistory semantic retention check passed
```

### 不新增播放/下载入口检查

```
P8-4B no playback/download entry check passed
```

### 测试结果

```
pytest: 375 passed, 6 skipped
```

---

## 29. P8-4B 阶段结论

P8-4B 已完成。历史记录已从纯文本工程列表整理为历史任务 card 列表。状态展示已复用 P8-3 helper（statusLabel/statusClass/resultStatusHintHtml/resultDiagnosticHtml）。空状态、加载失败、到底提示已产品化。未新增播放/下载入口。下一阶段建议进入 P8-4C：历史任务卡片播放入口整理。

---

## 30. P8-4B 下一阶段建议

建议 P8-4C 聚焦：

- 历史任务音频播放入口
- 根据 `/api/voice/jobs` 当前返回字段判断是否可复用 `audioPlayerHtml`
- 若存在 `audio_asset` / `audio_asset_id`，在历史 card 中加入播放器
- 不改后端 API

---

# P8-4C 历史任务卡片播放入口整理

## 31. P8-4C 执行背景

- P8-4A 已完成现状审查。
- P8-4B 已完成历史记录信息架构整理。
- 当前历史任务已是 card 结构。
- 当前历史任务仍缺少播放入口。
- 本阶段尝试基于 `/api/voice/jobs` 当前返回字段整理播放入口。
- 本阶段不改后端、不改 API、不改下载接口。

---

## 32. P8-4C 本阶段目标

记录：

- 审查历史 job 是否有可播放音频字段。
- 支持服务端 asset 播放入口。
- 有 asset 时复用 `audioPlayerHtml(assetId)`。
- 无 asset 时展示清晰提示。
- 不新增下载入口。
- 不处理 URL / HEX / blob 历史播放。
- 保留 DOM id。
- 保留 JS function 行为。
- 不改 API。

---

## 33. P8-4C 问题与风险分析

必须记录：

1. 历史任务 card 已完成，但尚无播放入口。
2. 播放入口依赖 `/api/voice/jobs` 返回的音频字段。
3. 如果 job 没有 `audio_asset` / `audio_asset_id` / `asset_id`，不能伪造播放入口。
4. URL / HEX / blob 历史播放语义需要单独确认。
5. 本阶段不能改 `/api/voice/jobs` 返回结构。
6. 本阶段不能改 `/api/voice/assets/{assetId}/download`。
7. 本阶段不能新增下载按钮。
8. 本阶段只能做展示层播放入口。

---

## 34. P8-4C 方案判断

必须记录：

- 采用服务端 asset 优先方案。
- 新增 `getHistoryAudioAssetId(job)`，从 job 中读取已有 asset 字段。
- 新增 `historyAudioPlaybackHtml(job)`。
- 有 asset 时复用 `audioPlayerHtml(assetId)`。
- 无 asset 时展示"当前历史记录未返回可播放音频资产。"
- 不处理 URL / HEX / blob。
- 不改 `loadHistory(offset)`。
- 不改 `/api/voice/jobs`。
- 不改下载接口。

---

## 35. P8-4C 修改范围

记录实际修改：

- `app/static/index.html` — 新增播放 helper、修改 historyJobCardHtml
- `docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md` — 追加 P8-4C 章节
- `docs/PROJECT_HEALTH_CHECK.md` — 更新状态摘要

---

## 36. P8-4C 历史播放入口说明

记录：

- 播放入口如何判断 asset：检查 `job.audio_asset.id`、`job.audio_asset_id`、`job.asset_id` 字段。
- `/api/voice/jobs` 返回的 `VoiceJobRead` 模型**不包含** `audio_asset` 或 `audio_asset_id` 字段。
- 因此 `getHistoryAudioAssetId(job)` 始终返回 `null`。
- 当前实现展示"当前历史记录未返回可播放音频资产。"
- 这是安全降级方案，不修改后端 API。
- 未来后端若在历史 job 中增加音频字段，可直接启用播放能力。
- 是否调用 API：否。
- 是否改变历史加载逻辑：否。

---

## 37. P8-4C URL / HEX / blob 处理说明

必须记录：

- 本阶段未实现 URL 历史播放。
- 本阶段未实现 HEX 历史播放。
- 本阶段未实现 blob 历史恢复。
- 原因：需要确认历史记录保存语义，不在 P8-4C 中处理。
- 后续可单独进入历史播放增强阶段。

---

## 38. P8-4C 下载入口处理说明

必须记录：

- 本阶段未新增下载入口。
- 未调用 `downloadBtnHtml(assetId)`。
- 下载入口留给 P8-4D。
- 下载接口未改。
- 未伪造不存在的下载入口。
- 提示文案从"播放和下载入口..."改为"下载入口将在后续阶段补充。"

---

## 39. P8-4C DOM id 保留说明

记录静态检查结果，确认关键 DOM id 仍存在。

- `tab-history` — 存在
- `historyCard` — 存在
- `historyToggle` — 存在
- `historyArea` — 存在
- `historyList` — 存在
- `loadMoreHistory` — 存在

---

## 40. P8-4C JS function 行为保留说明

记录静态检查结果，确认关键函数仍存在。

| 函数 | 用途 | API 调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `toggleHistory` | 展开/收起历史记录 | 无 | DOM 状态 | 无 |
| `loadHistory(offset)` | 加载历史记录 | `/api/voice/jobs` | `_historyOffset/_historyTotal/_historyLoading` | 无 |
| `loadMoreHistory` | 加载更多 | 调用 loadHistory | 同上 | 无 |
| `historyJobCardHtml(job)` | 渲染历史 job card | 无 | 无 | 新增播放区 |
| `historyEmptyStateHtml()` | 空状态 HTML | 无 | 无 | 无 |
| `historyLoadErrorHtml(message)` | 加载失败 HTML | 无 | 无 | 无 |
| `historyEndStateHtml()` | 到底提示 HTML | 无 | 无 | 无 |
| `audioPlayerHtml(assetId)` | 音频播放器 HTML | 无 | 无 | 无 |
| `statusLabel(s)` | 状态中文 label | 无 | 无 | 无 |
| `statusClass(s)` | 状态 CSS class | 无 | 无 | 无 |
| `resultStatusHintHtml(status)` | 状态说明 HTML | 无 | 无 | 无 |
| `resultDiagnosticHtml(message)` | 诊断信息 HTML | 无 | 无 | 无 |
| `isResultFailedStatus(status)` | 判断失败状态 | 无 | 无 | 无 |
| `extractErrorMessage(data)` | 提取错误信息 | 无 | 无 | 无 |
| `esc(s)` | HTML 转义 | 无 | 无 | 无 |
| `apiJson` | API JSON helper | 无 | 无 | 无 |

新增 helper（P8-4C）：

| 函数 | 用途 | API 调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `getHistoryAudioAssetId(job)` | 提取 job 中的 asset ID | 无 | 无 | 仅返回 null 或 asset ID |
| `historyAudioPlaybackHtml(job)` | 渲染播放区 HTML | 无 | 无 | 仅返回 HTML 字符串 |

---

## 41. P8-4C API endpoint 不变说明

必须记录：

- 历史记录列表 endpoint 未变：`/api/voice/jobs`
- 分页参数未变：`limit=10&offset={offset}`
- asset 播放 endpoint 未变：`/api/voice/assets/{assetId}/download`
- 下载 endpoint 未变：`/api/voice/assets/{assetId}/download`
- 未新增 API。
- 未删除 API。

---

## 42. P8-4C 未处理事项

必须写明：

- 未新增历史下载入口
- 未新增历史字幕 / timeline 展示
- 未新增历史详情页
- 未新增历史搜索
- 未新增历史筛选
- 未新增历史删除
- 未处理 URL 历史播放
- 未处理 HEX 历史播放
- 未处理 blob 历史恢复
- 未改后端 API
- 未改 `/api/voice/jobs`
- 未改下载接口
- 未处理桌面宽屏 P8-UX1
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-4D

---

## 43. P8-4C 执行命令记录

### 基线检查

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -20
```

### 静态检查

```bash
grep -n "tab-history\|historyCard\|historyToggle\|historyArea\|historyList\|loadMoreHistory" app/static/index.html
grep -n "function toggleHistory\|function loadHistory\|function loadMoreHistory" app/static/index.html
grep -n "function audioPlayerHtml\|<audio\|audio_asset\|audio_asset_id\|asset_id" app/static/index.html
grep -n "历史任务\|生成文本\|任务信息\|historyJobCardHtml" app/static/index.html
```

### 文档标记检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息","音频播放"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM/display marker check passed")
PY
```

---

## 44. P8-4C 验证命令记录

### DOM marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息","音频播放"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4C DOM/display marker check passed")
PY
```

### JS function 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = ["function toggleHistory","function loadHistory","function loadMoreHistory","function historyJobCardHtml","function historyEmptyStateHtml","function historyLoadErrorHtml","function historyEndStateHtml","function audioPlayerHtml","function statusLabel","function statusClass","function resultStatusHintHtml","function resultDiagnosticHtml","function isResultFailedStatus","function extractErrorMessage","function esc","function apiJson"]
missing = [x for x in required_functions if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4C JS function check passed")
PY
```

### History playback helper 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["function getHistoryAudioAssetId","function historyAudioPlaybackHtml","audioPlayerHtml(assetId)","当前历史记录未返回可播放音频资产"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4C history playback helper check passed")
PY
```

### API marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_api_markers = ["/api/voice/jobs","limit=10","offset=","apiJson","/api/voice/assets/"]
missing = [x for x in required_api_markers if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4C API marker check passed")
PY
```

### loadHistory 语义保留检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function loadHistory")
end = html.find("function loadMoreHistory", start)
block = html[start:end]
required = ["/api/voice/jobs","limit=10","offset=","_historyOffset","_historyTotal","_historyLoading"]
missing = [x for x in required if x not in block]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4C loadHistory semantic retention check passed")
PY
```

### 不新增下载入口检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function historyJobCardHtml")
end = html.find("function historyEmptyStateHtml", start)
block = html[start:end]
forbidden = ["downloadBtnHtml(","下载音频"]
found = [x for x in forbidden if x in block]
if found: raise SystemExit(f"Should not add: {found}")
print("P8-4C no download entry check passed")
PY
```

### 全量测试

```bash
python -m pytest tests/ -x -q
```

---

## 45. P8-4C 验证结果

### git 检查

```
## dev...origin/dev
 M app/static/index.html
app/static/index.html | 35 +++++++++++++++++++++++++++++++++--
1 file changed, 33 insertions(+), 2 deletions(-)
```

### DOM marker 检查

```
P8-4C DOM/display marker check passed
```

### JS function 检查

```
P8-4C JS function check passed
```

### History playback helper 检查

```
P8-4C history playback helper check passed
```

### API marker 检查

```
P8-4C API marker check passed
```

### loadHistory 语义保留检查

```
P8-4C loadHistory semantic retention check passed
```

### 不新增下载入口检查

```
P8-4C no download entry check passed
```

### 测试结果

```
pytest: 375 passed, 6 skipped
```

---

## 46. P8-4C 阶段结论

P8-4C 已完成历史任务卡片播放入口整理。经审查，`/api/voice/jobs` 返回的 `VoiceJobRead` 模型不包含 `audio_asset` 或 `audio_asset_id` 字段，因此历史播放入口采用安全降级方案：展示"当前历史记录未返回可播放音频资产。"提示。`getHistoryAudioAssetId(job)` 和 `historyAudioPlaybackHtml(job)` 已就位，待后端在历史 job 中增加音频字段时可立即启用播放能力。未新增下载入口。下一阶段建议进入 P8-4D：历史任务下载入口产品化。

---

## 47. P8-4C 下一阶段建议

建议 P8-4D 聚焦：

- 历史任务下载入口
- 根据 `getHistoryAudioAssetId(job)` 判断是否可复用 `downloadBtnHtml(assetId)`
- 有 asset 时加入下载按钮
- 无 asset 时展示下载不可用提示
- 不改后端 API
- 不改下载接口

---

# P8-4D 历史任务下载入口产品化

## 48. P8-4D 执行背景

- P8-4A 已完成现状审查。
- P8-4B 已完成历史记录信息架构整理。
- P8-4C 已完成历史任务播放入口整理。
- 当前历史任务 card 已有播放区，但下载入口仍未产品化。
- 本阶段基于 `getHistoryAudioAssetId(job)` 整理下载入口。
- 本阶段不改后端、不改 API、不改下载接口。

---

## 49. P8-4D 本阶段目标

记录：

- 为历史任务 card 增加下载入口区域。
- 有 asset 时复用 `downloadBtnHtml(assetId)`。
- 无 asset 时展示清晰提示。
- 明确当前 `/api/voice/jobs` 不返回音频资产字段。
- 不处理 URL / HEX / blob 下载。
- 保留 DOM id。
- 保留 JS function 行为。
- 不改 API。

---

## 50. P8-4D 问题与风险分析

必须记录：

1. P8-4C 已新增播放区，但下载入口仍只是提示文案。
2. 下载入口依赖 `/api/voice/jobs` 返回的音频资产字段。
3. 当前 `VoiceJobRead` 不包含 `audio_asset` / `audio_asset_id`。
4. 如果没有 asset，不能伪造下载入口。
5. URL / HEX / blob 下载语义需要单独确认。
6. 本阶段不能改 `/api/voice/jobs` 返回结构。
7. 本阶段不能改 `/api/voice/assets/{assetId}/download`。
8. 本阶段只能做展示层下载入口。

---

## 51. P8-4D 方案判断

必须记录：

- 采用服务端 asset 优先方案。
- 复用 `getHistoryAudioAssetId(job)`。
- 新增 `historyDownloadEntryHtml(job)`。
- 有 asset 时复用 `downloadBtnHtml(assetId)`。
- 无 asset 时展示 `当前历史记录未返回可下载音频资产。`
- 不处理 URL / HEX / blob。
- 不改 `loadHistory(offset)`。
- 不改 `/api/voice/jobs`。
- 不改下载接口。

---

## 52. P8-4D 修改范围

记录实际修改：

- `app/static/index.html` — 新增下载 helper、修改 historyJobCardHtml
- `docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md` — 追加 P8-4D 章节
- `docs/PROJECT_HEALTH_CHECK.md` — 更新状态摘要

---

## 53. P8-4D 历史下载入口说明

记录：

- 下载入口如何判断 asset：检查 `job.audio_asset.id`、`job.audio_asset_id`、`job.asset_id` 字段。
- `/api/voice/jobs` 返回的 `VoiceJobRead` 模型**不包含** `audio_asset` 或 `audio_asset_id` 字段。
- 因此 `getHistoryAudioAssetId(job)` 始终返回 `null`。
- 当前实现展示"当前历史记录未返回可下载音频资产。"
- 这是安全降级方案，不修改后端 API。
- 未来后端若在历史 job 中增加音频字段，可直接启用下载能力。
- 是否调用 API：否。
- 是否改变历史加载逻辑：否。
- 是否改变下载接口：否。

---

## 54. P8-4D 当前后端字段限制说明

必须记录：

- 当前 `/api/voice/jobs` 返回的 `VoiceJobRead` 不包含 `audio_asset` / `audio_asset_id`。
- 因此当前历史下载入口通常展示不可下载提示。
- 这不是前端 bug，而是当前历史列表接口字段限制。
- 后续若要真正支持历史下载，需要后端在历史 job 中返回可下载 asset 字段。
- 可作为后续后端阶段：`P8-BE1：历史任务返回音频资产字段`。

---

## 55. P8-4D URL / HEX / blob 下载处理说明

必须记录：

- 本阶段未实现 URL 历史下载。
- 本阶段未实现 HEX 历史下载。
- 本阶段未实现 blob 历史恢复 / 下载。
- 原因：需要确认历史记录保存语义，不在 P8-4D 中处理。
- 后续可单独进入历史下载增强阶段。

---

## 56. P8-4D DOM id 保留说明

记录静态检查结果，确认关键 DOM id 仍存在。

- `tab-history` — 存在
- `historyCard` — 存在
- `historyToggle` — 存在
- `historyArea` — 存在
- `historyList` — 存在
- `loadMoreHistory` — 存在

---

## 57. P8-4D JS function 行为保留说明

记录静态检查结果，确认关键函数仍存在。

| 函数 | 用途 | API 调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `toggleHistory` | 展开/收起历史记录 | 无 | DOM 状态 | 无 |
| `loadHistory(offset)` | 加载历史记录 | `/api/voice/jobs` | `_historyOffset/_historyTotal/_historyLoading` | 无 |
| `loadMoreHistory` | 加载更多 | 调用 loadHistory | 同上 | 无 |
| `historyJobCardHtml(job)` | 渲染历史 job card | 无 | 无 | 新增下载区 |
| `historyEmptyStateHtml()` | 空状态 HTML | 无 | 无 | 无 |
| `historyLoadErrorHtml(message)` | 加载失败 HTML | 无 | 无 | 无 |
| `historyEndStateHtml()` | 到底提示 HTML | 无 | 无 | 无 |
| `getHistoryAudioAssetId(job)` | 提取 job 中的 asset ID | 无 | 无 | 无 |
| `historyAudioPlaybackHtml(job)` | 渲染播放区 HTML | 无 | 无 | 无 |
| `historyDownloadEntryHtml(job)` | 渲染下载区 HTML | 无 | 无 | 新增函数 |
| `audioPlayerHtml(assetId)` | 音频播放器 HTML | 无 | 无 | 无 |
| `downloadBtnHtml(assetId)` | 下载按钮 HTML | 无 | 无 | 无 |
| `statusLabel(s)` | 状态中文 label | 无 | 无 | 无 |
| `statusClass(s)` | 状态 CSS class | 无 | 无 | 无 |
| `resultStatusHintHtml(status)` | 状态说明 HTML | 无 | 无 | 无 |
| `resultDiagnosticHtml(message)` | 诊断信息 HTML | 无 | 无 | 无 |
| `isResultFailedStatus(status)` | 判断失败状态 | 无 | 无 | 无 |
| `extractErrorMessage(data)` | 提取错误信息 | 无 | 无 | 无 |
| `esc(s)` | HTML 转义 | 无 | 无 | 无 |
| `apiJson` | API JSON helper | 无 | 无 | 无 |

新增 helper（P8-4D）：

| 函数 | 用途 | API 调用 | 状态读写 | 业务行为改变 |
|---|---|---|---|---|
| `historyDownloadEntryHtml(job)` | 渲染下载区 HTML | 无 | 无 | 仅返回 HTML 字符串 |

---

## 58. P8-4D API endpoint 不变说明

必须记录：

- 历史记录列表 endpoint 未变：`/api/voice/jobs`
- 分页参数未变：`limit=10&offset={offset}`
- asset 下载 endpoint 未变：`/api/voice/assets/{assetId}/download`
- 未新增 API。
- 未删除 API。

---

## 59. P8-4D 未处理事项

必须写明：

- 未新增历史字幕 / timeline 展示
- 未新增历史详情页
- 未新增历史搜索
- 未新增历史筛选
- 未新增历史删除
- 未处理 URL 历史下载
- 未处理 HEX 历史下载
- 未处理 blob 历史恢复
- 未改后端 API
- 未改 `/api/voice/jobs`
- 未改下载接口
- 未处理 `/api/voice/jobs` 不返回音频资产字段的问题
- 未处理桌面宽屏 P8-UX1
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-4E

---

## 60. P8-4D 执行命令记录

### 基线检查

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -20
```

### 静态检查

```bash
grep -n "tab-history\|historyCard\|historyToggle\|historyArea\|historyList\|loadMoreHistory" app/static/index.html
grep -n "function toggleHistory\|function loadHistory\|function loadMoreHistory\|function historyJobCardHtml" app/static/index.html
grep -n "function downloadBtnHtml\|/api/voice/assets/\|下载音频" app/static/index.html
grep -n "历史任务\|生成文本\|任务信息\|音频播放\|下载入口\|historyJobCardHtml" app/static/index.html
```

---

## 61. P8-4D 验证命令记录

### DOM marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息","音频播放","下载入口"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4D DOM/display marker check passed")
PY
```

### JS function 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = ["function toggleHistory","function loadHistory","function loadMoreHistory","function historyJobCardHtml","function historyEmptyStateHtml","function historyLoadErrorHtml","function historyEndStateHtml","function getHistoryAudioAssetId","function historyAudioPlaybackHtml","function downloadBtnHtml","function audioPlayerHtml","function statusLabel","function statusClass","function resultStatusHintHtml","function resultDiagnosticHtml","function isResultFailedStatus","function extractErrorMessage","function esc","function apiJson"]
missing = [x for x in required_functions if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4D JS function check passed")
PY
```

### History download helper 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["function historyDownloadEntryHtml","getHistoryAudioAssetId(job)","downloadBtnHtml(assetId)","当前历史记录未返回可下载音频资产"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4D history download helper check passed")
PY
```

### API marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_api_markers = ["/api/voice/jobs","limit=10","offset=","apiJson","/api/voice/assets/"]
missing = [x for x in required_api_markers if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4D API marker check passed")
PY
```

### loadHistory 语义保留检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function loadHistory")
end = html.find("function loadMoreHistory", start)
block = html[start:end]
required = ["/api/voice/jobs","limit=10","offset=","_historyOffset","_historyTotal","_historyLoading"]
missing = [x for x in required if x not in block]
if missing: raise SystemExit(f"Missing: {missing}")
print("P8-4D loadHistory semantic retention check passed")
PY
```

### 不改 API / 不新增复杂下载检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function historyDownloadEntryHtml")
end_candidates = [html.find("function historyEmptyStateHtml", start), html.find("function historyLoadErrorHtml", start), html.find("function historyEndStateHtml", start)]
end_candidates = [x for x in end_candidates if x > start]
end = min(end_candidates) if end_candidates else start + 6000
block = html[start:end]
required = ["downloadBtnHtml(assetId)","当前历史记录未返回可下载音频资产"]
missing = [x for x in required if x not in block]
if missing: raise SystemExit(f"Missing: {missing}")
forbidden = ["fetch(","apiJson(","guardedJsonFetch(","audio_url","audio_hex","blobUrl"]
found = [x for x in forbidden if x in block]
if found: raise SystemExit(f"Should not add: {found}")
print("P8-4D no extra download logic check passed")
PY
```

### 全量测试

```bash
python -m pytest tests/ -x -q
```

---

## 62. P8-4D 验证结果

### git 检查

```
## dev...origin/dev
 M app/static/index.html
app/static/index.html | 19 +++++++++++++++++--
1 file changed, 17 insertions(+), 2 deletions(-)
```

### DOM marker 检查

```
P8-4D DOM/display marker check passed
```

### JS function 检查

```
P8-4D JS function check passed
```

### History download helper 检查

```
P8-4D history download helper check passed
```

### API marker 检查

```
P8-4D API marker check passed
```

### loadHistory 语义保留检查

```
P8-4D loadHistory semantic retention check passed
```

### 不改 API / 不新增复杂下载检查

```
P8-4D no extra download logic check passed
```

### 测试结果

```
pytest: 375 passed, 6 skipped
```

---

## 63. P8-4D 阶段结论

P8-4D 已完成历史任务下载入口产品化。`historyDownloadEntryHtml(job)` 已就位，有 asset 时复用 `downloadBtnHtml(assetId)`，无 asset 时展示"当前历史记录未返回可下载音频资产。"提示。`/api/voice/jobs` 当前不返回音频资产字段，因此下载区现阶段为安全降级展示。下一阶段建议进入 P8-4E：历史筛选 / 搜索 / 空状态优化。

---

## 64. P8-4D 下一阶段建议

建议 P8-4E 聚焦：

- 历史记录搜索
- 历史记录筛选
- 历史记录空状态进一步优化
- 加载更多体验优化
- 不改后端 API

同时记录后端遗留：

    P8-BE1：历史任务返回音频资产字段


