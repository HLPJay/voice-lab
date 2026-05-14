# P9 前端模块化说明

## 1. 当前目标

P9-FE1 目标不是引入前端框架，而是在保持静态 HTML 架构的前提下，把高内聚 JS 逻辑从 index.html 中逐步抽离为普通 script 文件。

## 2. 当前已抽离模块

### provider_capabilities.js

**文件：** `app/static/js/provider_capabilities.js`

**职责：**
- 加载 `/api/voice/capabilities`
- 缓存 Provider 能力数据（`_providerCapabilities`、`_providerCapabilitiesByName`）
- 根据能力动态调整控件（maxLength、min/max、disabled 状态、select options）
- 绑定 provider 切换事件
- 暴露 window 全局入口供 inline script 和 E2E 调用

**window 入口：**
- `window.loadProviderCapabilities` — 加载能力数据
- `window.getProviderCapability(provider)` — 查询指定 provider 能力
- `window.applyAllProviderCapabilities()` — 应用所有 tab 的能力约束
- `window.bindProviderCapabilityEvents()` — 绑定 provider 切换事件
- `window.updateProviderSelectOptions(selectId)` — 动态更新 select 选项
- `window.setControlDisabled(id, disabled, title)` — 设置控件 disabled 状态

**E2E 兼容 state：**
- `window._providerCapabilities`
- `window._capabilitiesLoaded`
- `window._capabilitiesLoadFailed`
- `window._capabilitiesLoadAttempted`
- `window._capabilitiesFailureNotified`

### runtime_status.js

**文件：** `app/static/js/runtime_status.js`

**职责：**
- 加载 `/api/voice/runtime/status`
- 更新顶部 runtime chips（chipProvider、chipModel、chipToday、chipMonth）
- 显示 Provider 调用状态（available/warning/error/unknown）
- 支持 60 秒定时刷新
- 失败可点击重试，可点击跳转到 admin.html

**window 入口：**
- `window.loadRuntimeStatus` — 加载并更新 runtime 状态
- `window.scheduleRuntimeStatusRefresh` — 启动 60 秒定时刷新

**E2E 兼容 state：**
- `window._runtimeStatusTimer`
- `window._runtimeStatusErrorNotified`

### history.js

**文件：** `app/static/js/history.js`

**职责：**
- 加载 `/api/voice/jobs` 历史任务列表
- 管理 `_historyJobs`、`_historyOffset`、`_historyTotal` 等状态
- 历史列表渲染（分页、筛选、搜索）
- 播放器展开/收起（同一时间最多一个）
- 历史任务软删除（DELETE /api/voice/jobs/{job_id}）
- 复制 job_id
- 刷新历史、加载更多

**window 入口：**
- `window.loadHistory(offset)` — 加载历史任务
- `window.loadMoreHistory()` — 加载更多（分页）
- `window.refreshHistory()` — 强制从第一页刷新
- `window.renderHistoryList()` — 重新渲染列表
- `window.filterHistoryJobs(jobs)` — 本地筛选
- `window.handleHistorySearchInput()` — 搜索输入处理
- `window.handleHistoryStatusFilterChange()` — 状态下拉处理
- `window.clearHistoryFilters()` — 清空筛选
- `window.updateHistoryFilterHint()` — 更新筛选提示
- `window.toggleHistoryAudio(assetId, jobId, row)` — 展开/收起播放器
- `window.deleteHistoryJob(jobId, row)` — 软删除历史
- `window.copyJobId(jobId, btnEl)` — 复制 job_id

**E2E 兼容 state：**
- `window._historyJobs`
- `window._historyOffset`
- `window._historyTotal`
- `window._historyLoading`
- `window._historySearch`
- `window._historyStatusFilter`
- `window._activeHistoryAudioRow`

**设计特点：**
- 本地 helper 函数避免对 index.html 加载顺序的依赖
- `showToast` 通过 `typeof window.showToast === 'function'` 存在性判断
- IIFE 末尾自动调用 `window.loadHistory(0)` 完成页初始化加载

### audition_records.js

**文件：** `app/static/js/audition_records.js`

**职责：**
- 管理 `_auditionRecords` 状态（试听记录列表）
- 渲染记录到 `#auditionRecordsTable`
- 单条删除、清空所有记录

**window 入口：**
- `window.renderAuditionRecords()` — 渲染列表到 DOM
- `window.deleteAuditionRecord(idx)` — 删除指定记录
- `window.clearAuditionRecords()` — 清空所有记录

**E2E 兼容 state：**
- `window._auditionRecords`

**设计特点：**
- IIFE 避免全局污染
- `arEsc()` HTML 转义辅助
- 渲染目标 `#auditionRecordsTable` 为 `voiceAuditionPanel` 子元素，由 `renderVoiceTable()` 动态生成

### batch_longtext.js

**文件：** `app/static/js/batch_longtext.js`

**职责：**
- 长文本批量提交入口（`handleBatchLongtextSubmit`）
- 读取长文本 Tab 表单参数
- 调用 `POST /api/voice/batch/submit`，`mode='longtext'`
- 调用共享进度函数 `showBatchProgress` / `startBatchPoll`
- 使用 `window.showBatchLongtextResult` / `window.clearBatchLongtextResult` 展示前置校验和错误

**window 入口：**
- `window.handleBatchLongtextSubmit` — 长文本批量提交入口

**E2E 覆盖：**
- `test_batch_longtext_module_is_loaded_and_submit_validation_works`

**设计特点：**
- IIFE 避免全局污染
- 函数定义而非立即执行，onclick 触发时所有全局 helper 已就绪
- 共享进度轮询函数（`showBatchProgress` 等）仍在 `index.html`，由本模块调用

**仍留在 index.html 的批量共享逻辑：**
- `showBatchProgress` / `startBatchPoll` / `stopBatchPoll` / `pollBatchStatus`
- `renderBatchStatus` / `renderBatchResultPlayer` / `renderBatchSubtitleList` / `updateBatchSubtitleHighlight`
- `handleBatchPlay` / `handleBatchRetry` / `getBatchPanelDom`
- `_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline`
- `window._batchPlayerInitialized` / `window._batchSubtitleCache`

## 3. 当前仍留在 index.html 的逻辑

- Tab 切换
- 表单提交与校验
- 单条生成（同步/异步/流式）
- 长文本批量（`handleBatchLongtextSubmit` 已迁入 batch_longtext.js；共享轮询/渲染函数暂留）
- 剧本批量
- 音色试听
- 克隆 / 声音设计 / 导入
- 错误展示与 toast
- 播放器渲染
- profile 缓存与 populateProfileSelect（脚本 Tab 共用 batchProfile select）
- 高消费确认

## 4. 模块化原则

- 不使用 ES module
- 不引入 webpack / vite / rollup 等构建工具
- 不引入 npm 前端依赖
- 普通 script 文件，通过 IIFE 包装
- 必要函数挂载到 `window.*` 供 index.html inline script 调用
- 不改变已有 DOM id
- 每拆一个模块，必须运行 `tests/e2e` 验证
- 每拆一个模块，优先补充一个对应 E2E 回归测试
- 只做 JS 逻辑迁移，不改变 UI 结构和业务逻辑

## 5. 下一步可拆模块（建议顺序）

### 5.0 P9-FE1-E0：长文本批量模块抽离前边界审查（已完成）

#### 长文本批量函数清单

**长文本批量独有函数（可迁移）：**
- `handleBatchLongtextSubmit()` (line ~4815) — 提交长文本批量任务，唯一引用 `batchText`、`batchProfile`、`batchProvider`、`batchStrategy`、`batchMaxChars`、`batchSilence`、`batchSpeed/Vol/Pitch/Emotion` 等长文本专属 DOM id

**长文本批量内部嵌套 helper（需先提取为独立函数才能迁移）：**
- `showBatchLongtextResult(html)` — 定义在 `handleBatchLongtextSubmit` 内部（闭包引用 `batchLongtextResult` DOM），被多处 catch/finally 块引用，需先提取为 `window.showBatchLongtextResult = function(html)` 才能迁入模块
- `clearBatchLongtextResult()` — 同上

**长文本批量共享函数（不可单独迁移）：**
- `showBatchProgress(batchId, targetPanelId)` — 同时服务长文本和剧本批量，通过 `targetPanelId` 区分
- `startBatchPoll(batchId, targetPanelId)` — 同上
- `stopBatchPoll()` — 同上
- `pollBatchStatus(batchId, targetPanelId)` — 同上
- `renderBatchStatus(data, targetPanelId)` — 同上
- `renderBatchResultPlayer(data, targetPanelId)` — 同上
- `renderBatchSubtitleList(targetPanelId, timeline)` — 同上
- `updateBatchSubtitleHighlight(targetPanelId)` — 同上
- `handleBatchPlay()` — 调用 `batchMergedAudio`，两批量共用
- `handleBatchRetry()` — 调用 `_currentBatchId` + `_currentBatchPanelId`，两批量共用
- `getBatchPanelDom(targetPanelId)` — 返回两批量各自 DOM 引用集合

#### 长文本批量状态变量

- `_batchPollTimer` — 轮询 timer（共享，两批量共用）
- `_currentBatchId` — 当前 batch id（共享，两批量共用）
- `_currentBatchPanelId` — 当前 panel id，默认为 `'batchProgressPanel'`（共享）
- `_batchTimeline` — 当前 timeline 数组（共享，两批量共用）
- `window._batchPlayerInitialized` — 播放器初始化标记（共享）
- `window._batchSubtitleCache` — 字幕缓存（共享）

#### 长文本批量 DOM id

**长文本 Tab 独有：**
- `#batchText` — 长文本输入
- `#batchProvider` / `#batchStrategy` / `#batchMaxChars` / `#batchSilence`
- `#batchSpeed` / `#batchVol` / `#batchPitch` / `#batchEmotion`
- `#batchOutputFormat` / `#batchNeedSubtitle`
- `#batchLongtextSubmit` — 提交按钮
- `#batchLongtextResult` — 结果展示区

**共享 DOM id（长文本和剧本批量共用同一个 id）：**
- `#batchProgressPanel` — 长文本进度面板
- `#batchProgressTitle` / `#batchProgressFill` / `#batchProgressStats`
- `#batchSegmentTable`
- `#batchResultPlayer` / `#batchMergedAudio` / `#batchCurrentSubtitle` / `#batchSubtitleList`
- `#batchDownloadAudio` / `#batchDownloadSubtitle` / `#batchRetryBtn`

#### 长文本批量 API endpoint

- `POST /api/voice/batch/submit` — mode=`'longtext'`
- `GET /api/voice/batch/{batchId}/status` — 状态轮询（与剧本批量共用）
- `POST /api/voice/batch/{batchId}/retry` — 重试失败段（与剧本批量共用）

#### 可迁移到 batch_longtext.js 的候选内容

- `handleBatchLongtextSubmit()` 函数整体

**前提条件：** 需先将 `showBatchLongtextResult` 和 `clearBatchLongtextResult` 从嵌套函数提取为 `window.showBatchLongtextResult(html)` 和 `window.clearBatchLongtextResult()`，使模块可调用。

#### 暂不迁移的共享内容

以下函数暂时必须留在 `index.html`，因为它们同时服务长文本和剧本批量：

- `showBatchProgress` / `startBatchPoll` / `stopBatchPoll` / `pollBatchStatus`
- `renderBatchStatus` / `renderBatchResultPlayer` / `renderBatchSubtitleList` / `updateBatchSubtitleHighlight`
- `handleBatchPlay` / `handleBatchRetry` / `getBatchPanelDom`
- 状态变量：`_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline`

#### 风险点

1. **共享轮询状态**：`_batchPollTimer` 等为批量模块共用，长文本提交后启动的 timer 会同时被 `pollBatchStatus` 和 `renderBatchStatus` 处理剧本批量结果。如果剧本批量先提交，长文本后提交，timer 会指向后者，前者可能丢失进度更新。
2. **共享 DOM id**：`#batchProgressPanel` 等被两批量共用，`targetPanelId` 是区分逻辑的唯一手段，但 `startBatchPoll` 写入 `_currentBatchPanelId`，`handleBatchRetry` 读取它，两批量交替提交时状态可能串台。
3. **嵌套 helper 提取**：`showBatchLongtextResult` 目前是闭包内函数，迁移前必须先提取为 `window` 全局，否则模块无法调用。

#### 下一步 P9-FE1-E 建议

**必须先做（index.html 改造）：**
1. 将 `showBatchLongtextResult(html)` 从 `handleBatchLongtextSubmit` 内部提取为 `window.showBatchLongtextResult = function(html)`
2. 将 `clearBatchLongtextResult()` 提取为 `window.clearBatchLongtextResult = function()`
3. 在所有引用处（catch/finally 块内）改为 `window.showBatchLongtextResult(...)`

**可随 batch_longtext.js 迁移：**
- `handleBatchLongtextSubmit` 整体

**必须保留在 index.html：**
- 所有共享轮询/渲染函数
- 所有共享状态变量

### P9-FE1-E1（已完成）：长文本批量结果 helper 提取

**完成时间：** P9-FE1-E1 阶段

**实现：**
- `showBatchLongtextResult(html)` 已从 `handleBatchLongtextSubmit` 内部闭包提取为 `window.showBatchLongtextResult = function(html)`
- `clearBatchLongtextResult()` 已提取为 `window.clearBatchLongtextResult = function()`
- `handleBatchLongtextSubmit` 内部所有调用已更新为 `window.showBatchLongtextResult(...)` 和 `window.clearBatchLongtextResult()`
- 原有行为完全保持不变（`style.display = ''` 当有内容，`style.display = 'none'` 当清空）

**window 入口：**
- `window.showBatchLongtextResult(html)` — 显示结果到 `#batchLongtextResult`
- `window.clearBatchLongtextResult()` — 清空并隐藏 `#batchLongtextResult`

**E2E 覆盖：**
- `test_batch_longtext_result_helpers_are_exposed`（共 13 个 E2E）

**下一步：** P9-FE1-E2 可正式迁移 `handleBatchLongtextSubmit()` 到 `batch_longtext.js`

### 5.1 batch_longtext.js（已完成 ✅）

**完成阶段：** P9-FE1-E2

**前提（已完成 E0 + E1）：**
- ✅ `showBatchLongtextResult` / `clearBatchLongtextResult` 已提取为 `window.*`
- ✅ `handleBatchLongtextSubmit` 已迁移到 `app/static/js/batch_longtext.js`

**文件：** `app/static/js/batch_longtext.js`

**应迁移：**
- ✅ `handleBatchLongtextSubmit()` 已迁移

**不可迁移（留在 index.html）：**
- 共享轮询函数（`showBatchProgress` 等）
- 共享状态变量
- 共享 DOM 渲染函数

**下一步建议：**
- P9-FE1-F：剧本批量审查（batch_script.js 边界设计）
- 或补 batch_longtext 成功提交 mock E2E


### 5.2 batch_script.js（建议下一步）

**理由：** 剧本批量状态复杂（`scriptRows` 数组、角色/台词状态），建议有更多 E2E 覆盖后再拆。

**应迁移：**
- 剧本 Tab 的 `handleBatchScriptSubmit()`
- `scriptRows` 状态管理
- 进度轮询和结果渲染

### 5.3 voice_clone_design.js

**理由：** 克隆/设计/导入逻辑交织，且依赖 provider_capabilities.js 的能力约束，建议最后拆。

**应迁移：**
- `handleCloneSubmit()`、`handleDesignSubmit()`
- `bindVoiceToProfile()`
- 导入音色相关逻辑

## 6. 当前测试覆盖

| 测试文件 | 覆盖范围 |
|---|---|
| test_frontend_capabilities.py | 主页面加载、capability 控件、provider 切换、失败降级、Admin 页面、Admin 矩阵、剧本 Tab 回归、history.js 模块加载、History Tab 打开与刷新、audition_records.js 模块加载、Voices Tab 打开、audition_records.js 渲染与删除、长文本批量结果 helper 暴露、batch_longtext.js 加载与校验（共 14 个 E2E） |

**E2E fixture 注意事项：**
- `e2e_base_url` 为 function-scope，每个测试用独立端口启动 server
- `browser` 和 `page` 为 function-scope，避免 HTTP/2 连接复用问题
- 使用 `wait_until="commit"` 避免 `networkidle` 超时
- `console_errors` fixture 过滤 favicon 404 和预期 500 错误

## 7. 已知风险

1. **index.html 仍约 4100+ 行**：history.js 抽离后约减少 870 行，但单文件仍较大，建议继续按节奏拆解。
2. **批量状态分散**：长文本和剧本批量各有独立状态变量，未统一管理。
3. **profile 加载逻辑耦合**：loadProfiles 和 populateProfileSelect 散落在多处，未来可考虑合并。
4. **无前端集成测试**：目前仅有 E2E 浏览器测试，无单元测试覆盖 JS 模块逻辑。
5. **批量共享轮询状态风险**：`_batchPollTimer`、`_currentBatchId`、`_currentBatchPanelId` 为长文本和剧本批量共用。详见 5.0 节风险分析；P9-FE1-E2 已将 `handleBatchLongtextSubmit` 迁出，共享状态风险暂未解决。
6. **E0/E1/E2 均已完成**：`showBatchLongtextResult` / `clearBatchLongtextResult` 已提取，`handleBatchLongtextSubmit` 已迁入 `batch_longtext.js`。
