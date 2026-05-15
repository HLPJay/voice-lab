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

### batch_script.js

**文件：** `app/static/js/batch_script.js`

**职责（Phase 1）：**
- 剧本批量提交入口（`handleBatchScriptSubmit`）
- 读取 `_scriptRows` 中的剧本行状态
- 构建 mode='script' 的 `/api/voice/batch/submit` 请求
- 调用共享进度函数 `showBatchProgress` / `startBatchPoll`
- 本地 `bsEsc()` 辅助函数，避免依赖 index.html 的 `esc`

**window 入口：**
- `window.handleBatchScriptSubmit` — 剧本批量提交入口

**E2E 覆盖：**
- `test_batch_script_module_is_loaded_and_submit_validation_still_works`
- `test_batch_script_mock_submit_success_starts_progress`

**设计特点：**
- IIFE 避免全局污染
- `esc` 替换为本地 `bsEsc()`，不依赖 index.html 的 `esc` 函数
- `handleBatchScriptSubmit` 定义在 IIFE 内，通过 `window.handleBatchScriptSubmit` 暴露
- 共享进度轮询函数（`showBatchProgress` 等）仍在 `index.html`，由本模块调用

**仍留在 index.html 的剧本批量逻辑：**
- `addScriptLine` / `removeScriptLine` / `updateScriptLineLimitState`
- `_scriptRows` / `_scriptLineCount` / `MAX_SCRIPT_LINES`
- scriptLines 事件委托（`input` / `change` / `click` 监听器）
- `populateProfileSelect` / `loadProfiles` / `_cachedProfiles`
- 共享批量轮询和渲染函数（`showBatchProgress` 等）
- 共享批量状态变量（`_batchPollTimer` 等）
- `window.renderApiError`（由 index.html 暴露）

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


### 5.2 P9-FE1-F0：剧本批量模块抽离前边界审查（已完成）

**完成时间：** P9-FE1-F0 阶段

**性质：** 审查与文档记录，不迁移代码

#### 剧本批量 DOM id 清单

**剧本 Tab 独有 DOM id：**
- `#batchScriptProvider` — Provider 选择
- `#batchScriptSilence` — 段间静音（ms）
- `#batchScriptOutputFormat` — 音频格式
- `#batchScriptNeedSubtitle` — 生成字幕 checkbox
- `#batchScriptSubmit` — 提交按钮（onclick="handleBatchScriptSubmit()"）
- `#batchScriptResult` — 结果展示区
- `#batchScriptProgressPanel` — 进度面板容器
- `#batchScriptProgressTitle` / `#batchScriptProgressFill` / `#batchScriptProgressStats` — 进度条各部分
- `#batchScriptSegmentTable` — 段落状态表
- `#batchScriptResultPlayer` — 结果播放器区
- `#batchScriptMergedAudio` — 合并音频 audio 元素
- `#batchScriptCurrentSubtitle` — 当前字幕显示
- `#batchScriptSubtitleList` — 字幕时间线列表
- `#batchScriptDownloadAudio` / `#batchScriptDownloadSubtitle` — 下载链接
- `#scriptLines` — 台词行容器（事件委托根）
- `#scriptAddLineBtn` — 添加行按钮（onclick="addScriptLine()"）
- `#scriptLine_${id}` — 单行容器
- `#scriptRole_${id}` — 角色名输入
- `#scriptText_${id}` — 台词文本输入
- `#scriptProfile_${id}` — 人设下拉选择

**共享 DOM id（长文本和剧本批量各自独立，不共用）：**
- 长文本进度：`#batchProgressPanel` / `#batchProgressTitle` / `#batchProgressFill` / `#batchProgressStats` / `#batchSegmentTable`
- 剧本进度：`#batchScriptProgressPanel` / `#batchScriptProgressTitle` / `#batchScriptProgressFill` / `#batchScriptProgressStats` / `#batchScriptSegmentTable`
- 注意：两批量有各自独立进度 DOM id，通过 `targetPanelId` 参数区分

#### 剧本批量状态变量清单

- `_scriptLineCount` — 行 ID 自增计数器
- `_scriptRows` — 台词行状态数组，每项 `{id, role, text, profileId}`
- `MAX_SCRIPT_LINES` — 最大行数 200

**共享状态变量（两批量共用，见"暂不迁移的共享内容"节）：**
- `_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline`

#### 剧本批量函数清单

**剧本批量独有函数：**
- `addScriptLine(role, text, profileId)` (line ~4733) — 添加一行台词 DOM + 状态
- `removeScriptLine(id)` (line ~4768) — 删除一行 DOM + 状态
- `updateScriptLineLimitState()` (line ~4724) — 更新添加按钮 disabled 状态
- `handleBatchScriptSubmit()` (line ~4834) — 提交剧本批量任务

**剧本批量内部嵌套 helper：**
- 无（与长文本不同，`handleBatchScriptSubmit` 内无嵌套独立 helper）

**事件委托处理函数（管理 _scriptRows 状态）：**
- 监听 `input` 事件（role / text 字段）同步 `_scriptRows` 状态
- 监听 `change` 事件（profile 字段）同步 `_scriptRows.profileId`
- 监听 `click` 事件（`.script-remove-btn`）触发 `removeScriptLine`

**共享函数（两批量共用，必须留在 index.html）：**
- `showBatchProgress(batchId, targetPanelId)` — 通过 `targetPanelId === 'batchScriptProgressPanel'` 分支
- `startBatchPoll(batchId, targetPanelId)` — 启动轮询 timer
- `stopBatchPoll()` — 停止轮询 timer
- `pollBatchStatus(batchId, targetPanelId)` — 轮询状态 API
- `renderBatchStatus(data, targetPanelId)` — 渲染状态表，**含剧本独有逻辑**：`isScriptPanel` 时额外输出"角色"列
- `renderBatchResultPlayer(data, targetPanelId)` — 渲染结果播放器
- `renderBatchSubtitleList(targetPanelId, timeline)` — 渲染字幕时间线
- `updateBatchSubtitleHighlight(targetPanelId)` — 更新字幕高亮
- `getBatchPanelDom(targetPanelId)` — 返回对应 panel 的 DOM 引用集合
- `handleBatchPlay()` — 仅引用 `batchMergedAudio`（长文本）
- `handleBatchRetry()` — 引用 `_currentBatchId` + `_currentBatchPanelId`
- `formatTime(sec)` — 时间格式化

#### 剧本批量 API endpoint

- `POST /api/voice/batch/submit` — mode=`'script'`，payload 含 `script: [{role, text, profile_id, params}]`
- `GET /api/voice/batch/{batchId}/status` — 状态轮询（与长文本批量共用）
- `POST /api/voice/batch/{batchId}/retry` — 重试失败段（与长文本批量共用）

#### 依赖的 index.html 全局 helper / 状态

- `esc(s)` — HTML 转义
- `guardedJsonFetch(url, payload, options)` — 带确认的 fetch 封装
- `parseApiError(resp)` — API 错误解析
- `formatApiError(err)` — 错误格式化
- `window.renderApiError(err)` — 错误渲染（RESOURCE_LIMIT_EXCEEDED 时调用）
- `loadProfiles(forceRefresh)` — 加载人设列表
- `populateProfileSelect(selectEl, selectedId)` — 填充人设下拉
- `_cachedProfiles` — 人设全局缓存（addScriptLine 内部使用）

#### 可迁移到 batch_script.js 的候选内容

**可直接迁移（无前置依赖）：**
- `handleBatchScriptSubmit()` — 整体迁移，但调用共享函数需通过 `window.*`

**可在解决依赖后迁移：**
- `addScriptLine()` — 需先确保 `populateProfileSelect` 已暴露为 `window.populateProfileSelect`，且 `_cachedProfiles` 已初始化
- `removeScriptLine(id)` — 独立函数，可随 `addScriptLine` 一起迁移
- `updateScriptLineLimitState()` — 依赖 `#scriptAddLineBtn` DOM，可随行管理函数迁移

**不可单独迁移（强 DOM 耦合）：**
- `_scriptLineCount` — 行 ID 自增，需与 `addScriptLine` / `removeScriptLine` 整体迁移
- `_scriptRows` 状态 — 与 DOM 事件委托紧耦合，迁移需同时迁移事件委托逻辑
- 事件委托代码 — 依赖 `_scriptRows` 和 `scriptLine_*` DOM id，迁移需完整迁移行管理

#### 暂不迁移的共享内容

**共享轮询函数（必须留在 index.html，两批量共用）：**
- `showBatchProgress` / `startBatchPoll` / `stopBatchPoll` / `pollBatchStatus`
- `renderBatchStatus`（含剧本特殊逻辑 `isScriptPanel` 输出"角色"列）
- `renderBatchResultPlayer` / `renderBatchSubtitleList` / `updateBatchSubtitleHighlight`
- `handleBatchPlay` / `handleBatchRetry` / `getBatchPanelDom`
- `formatTime`

**共享状态变量（两批量共用）：**
- `_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline`
- `window._batchPlayerInitialized` / `window._batchSubtitleCache`

#### 需要先提取为 window.* 的 helper / 状态

1. **`window.populateProfileSelect`** — `addScriptLine` 在初始化每行下拉时调用此函数。若 `batch_script.js` 独立加载时 `populateProfileSelect` 尚未就绪，会导致下拉为空。建议通过 `typeof window.populateProfileSelect === 'function'` 判断后调用，或在 `addScriptLine` 内部 `loadProfiles()` 后再调用。
2. **`window._cachedProfiles`** — `addScriptLine` 内部通过 `_cachedProfiles` 判断是否直接调用 `populateProfileSelect`，还是 `await loadProfiles()` 后调用。若独立模块在 profiles 缓存前初始化，行为不变（会自动 fetch），但建议确保 `loadProfiles()` 可被调用。
3. **`esc`** — `handleBatchScriptSubmit` 使用，用于 HTML 转义。可在模块内部定义本地 `esc` 辅助函数（复制一份），避免依赖 index.html 中的 `esc`。
4. **`window.renderApiError`** — `handleBatchScriptSubmit` 的 catch 块中调用，需确认已暴露为 `window.renderApiError`。

#### 风险点

1. **addScriptLine 与 populateProfileSelect 紧耦合**：每添加一行都调用 `populateProfileSelect`，而该函数依赖全局 `_cachedProfiles`。独立模块在 profiles 未加载时添加行会导致下拉为空，但现有逻辑（fallback 到 `loadProfiles()`）已处理此场景。

2. **renderBatchStatus 含剧本特殊逻辑**：`isScriptPanel` 判断在共享函数内部，无法分离。若未来剧本批量独立模块化，`renderBatchStatus` 仍需保留在 index.html，或重构为通过 callback 注入差异逻辑。

3. **事件委托与 _scriptRows 强耦合**：`_scriptRows` 状态的同步完全依赖事件委托，迁移行管理函数时必须同时迁移事件绑定代码，否则状态将不再更新。

4. **批量共享状态冲突**：`_currentBatchId` / `_currentBatchPanelId` / `_batchPollTimer` 为两批量共用。剧本批量提交后，长文本批量再提交会覆盖这些状态，反之亦然。风险与长文本批量相同，但剧本批量目前无 E2E 覆盖，风险更高。

5. **handleBatchScriptSubmit 内部使用多个 index.html 全局函数**：提交流程依赖 `guardedJsonFetch`、`parseApiError`、`formatApiError`、`esc`、`window.renderApiError` 等。迁移时需确保这些在 index.html 中已加载，或在模块内部实现等效版本。

#### 下一步 P9-FE1-F1 建议

**是否建议立即抽离 batch_script.js：** 否，建议分阶段迁移。

**建议迁移步骤：**

**Phase 1：第一批（低风险，依赖简单）**
- 将 `handleBatchScriptSubmit()` 迁移到 `batch_script.js`
- 在 index.html 中定义 `window.handleBatchScriptSubmit = async function() { ... }`（复制现有实现）
- 将 `esc` 作为本地 `arEsc` 辅助函数复制到模块内（不依赖 index.html 的 `esc`）
- 共享轮询函数（`showBatchProgress` 等）继续保留在 index.html
- 事件委托代码暂时保留在 index.html

**Phase 2：第二批（中等风险，需处理 populateProfileSelect 依赖）**
- 迁移 `addScriptLine` / `removeScriptLine` / `_scriptLineCount` / `_scriptRows` / `updateScriptLineLimitState` / 事件委托代码
- 需先确认 `populateProfileSelect` 已作为 `window.populateProfileSelect` 暴露，或在模块内实现等效人设填充逻辑
- `MAX_SCRIPT_LINES` 可直接迁移

**是否需要先补 E2E：** 是。

建议 Phase 1 之前补：
- 剧本行增删 E2E（添加行、删除行、验证行数上限 200）
- 剧本批量提交校验 E2E（空文本、无 profile 场景）

建议 Phase 2 之前补：
- 剧本批量 mock 提交成功 E2E（参考 `test_batch_longtext_mock_submit_success_starts_progress`）

**暂不应迁移内容：**
- 所有共享轮询函数（`showBatchProgress` 等）
- 所有共享状态变量（`_batchPollTimer` 等）
- `renderBatchStatus`（含剧本差异逻辑）
- `populateProfileSelect` / `loadProfiles` / `_cachedProfiles`（人设系统，独立模块）

---

### 5.2 P9-FE1-F1：剧本批量提交校验 E2E（已完成 ✅）

**完成时间：** P9-FE1-F1 阶段

**实现：** `test_batch_script_submit_validation_works` E2E，覆盖剧本批量提交空台词时 `"请至少填写一行台词"` 校验错误展示，并验证 `/api/voice/batch/submit` 未被调用。

**P9-FE1-F2 Phase 1 已完成 ✅：** `handleBatchScriptSubmit` 已迁移到 `batch_script.js`（见 5.3 节），E2E `test_batch_script_module_is_loaded_and_submit_validation_still_works` + `test_batch_script_mock_submit_success_starts_progress` 验证模块加载和提交流程正常。

**下一步：** P9-FE1-F2 Phase 2（行管理函数和 `_scriptRows` 状态迁移）。

**P9-FE1-F2-FIX 已完成 ✅：** 新增 E2E `test_batch_script_mock_submit_success_starts_progress`，验证 mock 批量剧本提交成功后正确显示成功提示、显示进度面板、恢复提交按钮。修复了 per-row 校验时 row 1/2 DOM 文本为空导致的提前返回问题。

**下一步：** P9-FE1-F2 Phase 2（行管理函数和 `_scriptRows` 状态迁移）。

### 5.3 batch_script.js Phase 1（已完成 ✅）

**完成时间：** P9-FE1-F2 阶段 Phase 1

**迁移内容：**
- `handleBatchScriptSubmit()` 函数整体已迁移到 `app/static/js/batch_script.js`
- `esc()` 调用替换为本地 `bsEsc()` 辅助函数（不依赖 index.html）
- `window.handleBatchScriptSubmit` 通过 IIFE 暴露

**仍在 index.html（Phase 2 待迁）：**
- 台词行管理函数（`addScriptLine` / `removeScriptLine` / `updateScriptLineLimitState`）
- `_scriptLineCount` / `_scriptRows` / `MAX_SCRIPT_LINES`
- scriptLines 事件委托逻辑
- `populateProfileSelect` / `loadProfiles` / `_cachedProfiles`
- 共享批量轮询/渲染函数

**Phase 2 应迁移：**
- `addScriptLine` / `removeScriptLine` / `updateScriptLineLimitState`
- `_scriptLineCount` / `_scriptRows` / `MAX_SCRIPT_LINES`
- 事件委托代码（`input` / `change` / `click` 监听器）

### 5.4 voice_clone_design.js

**理由：** 克隆/设计/导入逻辑交织，且依赖 provider_capabilities.js 的能力约束，建议最后拆。

**应迁移：**
- `handleCloneSubmit()`、`handleDesignSubmit()`
- `bindVoiceToProfile()`
- 导入音色相关逻辑

## 6. 当前测试覆盖

| 测试文件 | 覆盖范围 |
|---|---|
| test_frontend_capabilities.py | 主页面加载、capability 控件、provider 切换、失败降级、Admin 页面、Admin 矩阵、剧本 Tab 回归、history.js 模块加载、History Tab 打开与刷新、audition_records.js 模块加载、Voices Tab 打开、audition_records.js 渲染与删除、长文本批量结果 helper 暴露、batch_longtext.js 加载与校验、长文本批量 mock 提交成功启动进度、剧本批量提交校验、batch_script.js 模块加载与校验、剧本批量 mock 提交成功启动进度（共 18 个 E2E） |

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
6. **E0/E1/E2/E2-FIX 均已完成**：`showBatchLongtextResult` / `clearBatchLongtextResult` 已提取，`handleBatchLongtextSubmit` 已迁入 `batch_longtext.js`；E2-FIX 添加了 mock 提交成功的 E2E 测试 `test_batch_longtext_mock_submit_success_starts_progress`。
7. **P9-FE1-F0 审查已完成**：`handleBatchScriptSubmit` 可迁移，但 `addScriptLine` / `removeScriptLine` 与 `populateProfileSelect` 紧耦合；`_scriptRows` 与 DOM 事件委托强耦合，不建议单独迁移；剧本批量 E2E 仅覆盖 Tab 打开（1个），缺少行增删和提交校验 E2E。详见 5.2 P9-FE1-F0 节。
8. **剧本批量行管理函数紧耦合**：`addScriptLine` 每行调用 `populateProfileSelect`，后者依赖全局 `_cachedProfiles`。独立模块需确保 `loadProfiles()` 可被调用或 `populateProfileSelect` 已暴露为 `window.populateProfileSelect`。

## P9-FE1-CHECK：当前阶段收口状态

**检查时间：** 2026-05-15（P9-FE1-F2-FIX 完成后）

### 已抽离模块清单（6 个）

| 模块 | 状态 | 入口函数 |
|---|---|---|
| `provider_capabilities.js` | ✅ 已迁移 | `loadProviderCapabilities`, `applyAllProviderCapabilities`, `setControlDisabled`, `updateProviderSelectOptions`, `getProviderCapability` |
| `runtime_status.js` | ✅ 已迁移 | `loadRuntimeStatus`, `scheduleRuntimeStatusRefresh` |
| `history.js` | ✅ 已迁移 | `loadHistory`, `loadMoreHistory`, `refreshHistory`, `toggleHistoryAudio`, `deleteHistoryJob`, `copyJobId`, `handleHistorySearchInput`, `handleHistoryStatusFilterChange`, `clearHistoryFilters`, `filterHistoryJobs` |
| `audition_records.js` | ✅ 已迁移 | `renderAuditionRecords`, `deleteAuditionRecord`, `clearAuditionRecords` |
| `batch_longtext.js` | ✅ 已迁移 | `handleBatchLongtextSubmit` |
| `batch_script.js` | ✅ 已迁移 | `handleBatchScriptSubmit` |

### script 加载顺序

```
provider_capabilities.js   ← index.html 第 1587 行
runtime_status.js         ← index.html 第 1588 行
history.js                ← index.html 第 1589 行
audition_records.js       ← index.html 第 1590 行
batch_longtext.js         ← index.html 第 1591 行
batch_script.js           ← index.html 第 1592 行
inline script             ← index.html 第 1593 行开始
```

### window 全局入口清单

**provider_capabilities.js：**
- `window.loadProviderCapabilities`
- `window.applyAllProviderCapabilities`
- `window.setControlDisabled`
- `window.updateProviderSelectOptions`
- `window.getProviderCapability`
- `window.bindProviderCapabilityEvents`
- `window._providerCapabilities` / `._providerCapabilitiesByName` / `._capabilitiesLoaded` 等状态

**runtime_status.js：**
- `window.loadRuntimeStatus`
- `window.scheduleRuntimeStatusRefresh`
- `window._runtimeStatusTimer` / `._runtimeStatusErrorNotified` 等状态

**history.js：**
- `window.loadHistory`
- `window.loadMoreHistory`
- `window.refreshHistory`
- `window.toggleHistoryAudio`
- `window.deleteHistoryJob`
- `window.copyJobId`
- `window.handleHistorySearchInput`
- `window.handleHistoryStatusFilterChange`
- `window.clearHistoryFilters`
- `window.renderHistoryList`
- `window.filterHistoryJobs`
- `window._historyJobs` / `._historyOffset` / `._historyTotal` / `._activeHistoryAudioRow` 等状态

**audition_records.js：**
- `window.renderAuditionRecords`
- `window.deleteAuditionRecord`
- `window.clearAuditionRecords`
- `window._auditionRecords` 状态

**batch_longtext.js：**
- `window.handleBatchLongtextSubmit`

**batch_script.js：**
- `window.handleBatchScriptSubmit`

### 当前 E2E 覆盖数量

**18 个 E2E**（tests/e2e/test_frontend_capabilities.py）

重点覆盖链路：
- Provider capability 加载 / 切换 / 失败降级
- History Tab 加载 / 刷新 / 删除
- Audition Records 渲染 / 删除
- 剧本批量 Tab 打开 / 提交校验（空文本、空 profile）
- batch_script.js 模块加载
- 剧本批量 mock 提交成功 + 进度面板 + 按钮恢复
- 长文本批量 mock 提交成功 + 进度面板 + 按钮恢复
- Admin 页面和矩阵

### 当前仍留在 index.html 的高风险逻辑

| 逻辑 | 所在位置 | 风险 |
|---|---|---|
| Tab 切换 | inline script | 涉及所有 Tab DOM 和 visibility 状态 |
| profile 加载 | `populateProfileSelect` / `loadProfiles` / `_cachedProfiles` | 剧本/长文本行管理均依赖此函数 |
| 剧本行管理 | `addScriptLine` / `removeScriptLine` / `updateScriptLineLimitState` | 与 `populateProfileSelect` 紧耦合 |
| 剧本行状态 | `_scriptRows` / `_scriptLineCount` / `MAX_SCRIPT_LINES` | 与 DOM 事件委托强耦合 |
| scriptLines 事件委托 | inline script scriptLines listener | 管理 `_scriptRows` DOM 同步 |
| 共享 batch 轮询函数 | `showBatchProgress` / `startBatchPoll` / `stopBatchPoll` / `pollBatchStatus` | 长文本和剧本批量共用，拆分需统一状态管理 |
| 共享 batch 状态 | `_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline` | 多模块共用，直接迁移有状态冲突风险 |
| `renderBatchStatus` | inline script | 共享批量渲染，依赖 `_batchTimeline` |
| voice clone/design/import | `handleCloneSubmit` / `handleDesignSubmit` / `bindVoiceToProfile` | 依赖 provider_capabilities.js 能力约束 |
| 单条生成链路 | inline script | 与 Tab 切换、result player 耦合 |
| API 共享 helper | `esc` / `guardedJsonFetch` / `parseApiError` / `formatApiError` / `renderApiError` | 被所有模块依赖，暂不建议迁移 |

### 当前高风险区域（不建议继续拆）

1. **共享 batch 状态**（`_batchPollTimer` 等）：长文本和剧本批量均引用同变量，拆出去会导致两模块争用状态。当前方案：两模块各自调用同一批共享函数，不迁移共享状态变量本身。
2. **populateProfileSelect / loadProfiles**：剧本行增删依赖此函数，拆出行管理模块需先确保 profile 相关逻辑独立或已暴露为 window 入口。
3. **voice_clone_design.js**：克隆/设计/导入逻辑交织，且依赖 `provider_capabilities.js` 的能力约束，建议最后拆。

### 下一步建议

- **暂不迁移共享 batch 状态**：`_batchPollTimer` / `_currentBatchId` 等变量继续保留在 index.html，待 batch 模块 Phase 2 统一考虑。
- **Phase 2 行管理迁移需单独任务**：需先审查 `addScriptLine` / `removeScriptLine` 与 `populateProfileSelect` 的耦合点，不建议在当前阶段直接迁移。
- **voice_clone_design.js 建议先审查再拆**：克隆/设计逻辑依赖 provider capability，建议完成 Phase 2 后再评估。
- **batch_shared.js 暂缓**：共享轮询状态统一管理可作为独立后续任务。
