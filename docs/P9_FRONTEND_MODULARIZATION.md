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
| test_frontend_capabilities.py | 主页面加载、capability 控件、provider 切换、失败降级、Admin 页面、Admin 矩阵、剧本 Tab 回归、history.js 模块加载、History Tab 打开与刷新、audition_records.js 模块加载、Voices Tab 打开、audition_records.js 渲染与删除、长文本批量结果 helper 暴露、batch_longtext.js 加载与校验、长文本批量 mock 提交成功启动进度、剧本批量提交校验、batch_script.js 模块加载与校验、剧本批量 mock 提交成功启动进度、声音克隆 insufficient balance 错误展示、声音设计 mock submit success、voice helper window exports（共 21 个 E2E） |

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

**25 个 E2E**（tests/e2e/test_frontend_capabilities.py）

重点覆盖链路：
- Provider capability 加载 / 切换 / 失败降级
- History Tab 加载 / 刷新 / 删除
- Audition Records 渲染 / 删除
- 剧本批量 Tab 打开 / 提交校验（空文本、空 profile）
- batch_script.js 模块加载
- 剧本批量 mock 提交成功 + 进度面板 + 按钮恢复
- 长文本批量 mock 提交成功 + 进度面板 + 按钮恢复
- 声音克隆 insufficient balance 错误展示
- 声音克隆 mock submit success + audio player + quick bind/preview 面板 + 按钮恢复
- 声音设计 mock submit success
- voice helper window exports
- voice_clone.js 模块加载 + 4 个 window 函数导出
- voice import clone mock success + audio player + quick bind 面板 + 按钮恢复
- voice_import.js 模块加载 + window.handleImportRemoteVoice 导出
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

## P9-FE1-G0：voice_clone_design.js 抽离前边界审查

**审查时间：** 2026-05-15

### 音色高级能力相关 DOM id 清单

**Clone Tab（`subtab-clone`，index.html 第 1254 行）：**

| DOM id | 类型 | 用途 |
|---|---|---|
| `cloneProvider` | select | Provider 选择 |
| `clonePurpose` | select | 用途（voice_clone） |
| `cloneFile` | file input | 音频文件上传 |
| `cloneFileHint` | div | file input hint（capability） |
| `uploadBtn` | button | 上传按钮（`handleUploadAudio()`） |
| `uploadResult` | div | 上传结果展示 |
| `cloneVoiceId` | input text | voice_id 输入 |
| `cloneAutoIdBtn` | button | 生成 voice_id（`handleCloneAutoId()`） |
| `cloneVoiceIdHint` | div | voice_id 格式错误提示 |
| `cloneFileId` | input number | file_id（上传后自动填入） |
| `clonePromptFileId` | input number | prompt file_id（可选） |
| `clonePromptText` | input text | prompt text（可选） |
| `clonePreviewText` | input text | 试听文本 |
| `cloneModel` | input text | model（preview 有值时必填） |
| `needNoiseReduction` | checkbox | 降噪选项 |
| `needVolumeNormalization` | checkbox | 音量标准化选项 |
| `cloneBtn` | button | 克隆提交（`handleCloneVoice()`） |
| `cloneBtnHint` | div | cloneBtn 禁用提示 |
| `cloneCapabilityHint` | div | capability 不足提示（由 provider_capabilities.js 控制） |
| `cloneResult` | div | 克隆结果 HTML |

**Design Tab（`subtab-design`，index.html 第 1378 行）：**

| DOM id | 类型 | 用途 |
|---|---|---|
| `designProvider` | select | Provider 选择 |
| `designVoiceId` | input text | voice_id（可选） |
| `designPrompt` | textarea | 音色描述 prompt |
| `designPreviewText` | textarea | 试听文本 |
| `designBtn` | button | 设计提交（`handleDesignVoice()`） |
| `designCapabilityHint` | div | capability 不足提示（由 provider_capabilities.js 控制） |
| `designResult` | div | 设计结果 HTML |

**Import（Clone + Design sub-tabs）：**

| DOM id | 类型 | 用途 |
|---|---|---|
| `importCloneProvider` / `importDesignProvider` | select | Import Provider |
| `importCloneVoiceId` / `importDesignVoiceId` | input text | 远端 voice_id |
| `importCloneName` / `importDesignName` | input text | 名称（可选） |
| `importCloneModel` / `importDesignModel` | select | model |
| `importClonePreviewText` / `importDesignPreviewText` | input text | 试听文本 |
| `importCloneVerify` / `importDesignVerify` | checkbox | 是否验证试听 |
| `importCloneBtn` / `importDesignBtn` | button | 验证并导入（`handleImportRemoteVoice('clone'/'design')`) |
| `importCloneResult` / `importDesignResult` | div | 导入结果 HTML |

**Voice List Tab：**

| DOM id | 类型 | 用途 |
|---|---|---|
| `voiceProvider` | select | Provider |
| `voiceType` | select | voice_type 过滤 |
| `voiceSearch` | input | 关键词搜索 |
| `listVoicesBtn` | button | 查询音色（`handleListVoices()`） |
| `voiceListResults` | div | 音色列表表格 |

**Audition Workstation（仍在 index.html）：**

| DOM id | 类型 | 用途 |
|---|---|---|
| `auditionSelectedBanner` | div | 选中音色高亮条 |
| `auditionSelected` | span | 选中音色名称 |
| `auditionProfileSelectWrap` | div | profile 选择器包裹 |
| `auditionProfileSelect` | select | 试听用 profile |
| `auditionText` | textarea | 试听文本 |
| `auditionCostHint` | div | 字数提示 |
| `auditionModel` | select | 模型选择 |
| `auditionGenBtn` | button | 生成试听 |
| `auditionResult` | div | 试听结果 |
| `auditionRecordsPanel` | div | 记录面板（调用 audition_records.js） |
| `auditionCount` | span | 记录数量 |
| `auditionClearBtn` | button | 清空记录 |
| `auditionRecordsTable` | div | 记录表格 |

**Shared result panel DOM（动态创建，clone/design/import 成功结果中）：**

| DOM id 前缀 | 用途 |
|---|---|
| `cloneProfileWrap` / `designProfileWrap` / `importCloneProfileWrap` | 绑定人设 select 包裹 |
| `cloneBindProfile` / `designBindProfile` / `importCloneBindProfile` | 人设 select（动态创建） |
| `cloneBindModel` / `designBindModel` / `importCloneBindModel` | 模型 select |
| `cloneBindBtn` / `designBindBtn` / `importCloneBindBtn` | 绑定按钮（inline onclick） |
| `cloneBindResult` / `designBindResult` / `importCloneBindResult` | 绑定结果 |
| `cloneQuickText` / `designQuickText` | 试听文本输入 |
| `cloneQuickBtn` / `designQuickBtn` | 快速试听按钮（inline onclick） |
| `cloneQuickResult` / `designQuickResult` | 快速试听结果 |

### 音色高级能力相关状态变量清单

| 变量 | 类型 | 位置 | 用途 |
|---|---|---|---|
| `_cachedProfiles` | array | index.html inline script | 全局 profile 缓存（被所有模块共用） |
| `_cachedVoices` | object | index.html inline script | per-provider voice 缓存 |
| `_loadedVoices` | array | index.html inline script | 当前已加载音色列表 |
| `_voiceBindMap` | object | index.html inline script | voice binding 状态映射 |
| `_voicePagination` | object | index.html inline script | 音色列表分页状态 |
| `_auditionSelectedVoiceId` | string | index.html inline script | 当前选中试听音色 ID |
| `_auditionSelectedVoiceName` | string | index.html inline script | 当前选中试听音色名称 |
| `_auditionDelegated` | boolean | index.html inline script | 试听事件委托守卫 |
| `_OPERATION_MESSAGES` | object | index.html inline script | highRisk 操作确认文案 |

### 函数清单

**核心业务函数（可迁移候选）：**

| 函数 | 行号 | 用途 | API |
|---|---|---|---|
| `handleUploadAudio` | 3918 | 音频文件上传 | `POST /api/voice/clone/upload` |
| `handleCloneAutoId` | 3972 | 生成 voice_id | — |
| `updateCloneBtnState` | 3991 | 克隆按钮状态校验 | — |
| `handleCloneVoice` | 4020 | 克隆创建 | `POST /api/voice/clone/create` |
| `handleDesignVoice` | 4370 | 声音设计创建 | `POST /api/voice/design/create` |
| `handleImportRemoteVoice` | 4232 | 远端音色导入 | `POST /api/voice/provider-voices/import` |

**辅助/渲染函数（必须留在 index.html）：**

| 函数 | 行号 | 用途 | 依赖 |
|---|---|---|---|
| `populateProfileSelect` | 1708 | 填充 profile select | `_cachedProfiles` |
| `loadProfiles` | 1692 | 加载 profile 列表 | `_cachedProfiles` |
| `bindVoiceToProfile` | 1748 | 绑定 voice 到 profile | `/api/voice/profiles/${id}/bindings` |
| `refreshVoiceBindStatus` | 3231 | 刷新音色绑定状态 | `loadAllBindings` |
| `renderInlineCreateProfile` | 3719 | 动态创建内联人设表单 | `populateProfileSelect`, `_cachedProfiles` |
| `handleListVoices` | 3540 | 查询音色列表 | `/api/voice/provider-voices` |
| `filterVoiceList` | 3586 | 过滤音色列表 | `_loadedVoices` |
| `renderVoiceTable` | 3610 | 渲染音色列表表格 | `_voicePagination`, `_voiceBindMap` |
| `renderAuditionWorkstation` | 3274 | 渲染试听工作站 HTML | audition generation |
| `hexToBlobUrl` | 2147 | hex → blob URL（音频播放） | — |

**Provider capability 驱动函数（在 provider_capabilities.js 中）：**

| 函数 | 行号 | 用途 |
|---|---|---|
| `applyVoiceCloneCapability` | 307 | 设置 clone capability hint 和按钮状态 |
| `applyVoiceDesignCapability` | 371 | 设置 design capability hint 和按钮状态 |

### API endpoint 清单

| Endpoint | Method | 用途 |
|---|---|---|
| `/api/voice/clone/upload` | POST | 上传克隆音频文件 |
| `/api/voice/clone/create` | POST | 创建克隆音色 |
| `/api/voice/design/create` | POST | 创建设计音色 |
| `/api/voice/provider-voices` | GET | 查询远端音色列表 |
| `/api/voice/provider-voices/import` | POST | 导入远端音色 |
| `/api/voice/profiles/${profileId}/bindings` | POST | 绑定音色到人设 |
| `/api/voice/profiles` | GET/POST | 查询/创建 profile |
| `/api/voice/voices/delete` | POST | 删除远端音色 |
| `/api/voice/render` | POST | 快速试听（clone result panel 内 inline fetch） |

### provider capability 依赖

**clone：**
- `applyVoiceCloneCapability()` 在 `provider_capabilities.js` 第 307 行
- 检查 `cap.voice_clone.supported`
- 设置 `cloneCapabilityHint`（第 315 行）和 `cloneBtn` disabled 状态
- 从 capability 填充 `preview_text_max`、`voice_id.min_length/max_length/pattern/hint`
- provider 切换时触发 `bindProviderCapabilityEvents` → `applyVoiceCloneCapability()`

**design：**
- `applyVoiceDesignCapability()` 在 `provider_capabilities.js` 第 371 行
- 检查 `cap.voice_design.supported`
- 设置 `designCapabilityHint`（第 379 行）和 `designBtn` disabled 状态
- 从 capability 填充 `prompt_max`、`preview_text_max`
- provider 切换时触发 `bindProviderCapabilityEvents` → `applyVoiceDesignCapability()`

**结论：** clone/design 表单的 capability hint 和按钮状态完全由 `provider_capabilities.js` 控制。voice_clone_design.js 迁移后仍需调用 `applyVoiceCloneCapability()` / `applyVoiceDesignCapability()` 或让 `provider_capabilities.js` 暴露对应 window 入口。

### highRisk confirm 依赖

以下操作使用 `guardedJsonFetch(..., { ..., highRisk: true })`：

| 操作 | operation key | confirm 提示 |
|---|---|---|
| `handleCloneVoice` | `voice_clone` | `voice_clone: '声音克隆会调用云端模型，可能产生费用，是否继续？'` |
| `handleDesignVoice` | `voice_design` | `voice_design: '声音设计会调用云端模型，可能产生费用，是否继续？'` |
| voice preview（audition） | `provider_voice_preview` | 试听确认 |
| provider voice import | `provider_voice_import_verify` | 导入确认 |

**E2E 影响：** 使用 `provider=mock` 可绕过 `guardedJsonFetch` 的 highRisk 确认框；使用 `provider=minimax` 且无 mock 时会触发 `confirmHighCostVoiceAction` 对话框。

### 错误展示依赖

| 错误处理 | 使用方式 |
|---|---|
| `parseApiError(resp)` | 第 2331 行，所有 API 错误先经过此函数解析 |
| `formatApiError(err)` | 第 2401 行，格式化错误消息 |
| `friendlyErrorMessage(message)` | 第 2213 行，生成友好错误消息（含 insufficient balance 特殊处理） |
| `renderApiError(err)` | 第 2445 行，渲染 API 错误（RESOURCE_LIMIT_EXCEEDED 时使用） |
| `renderValidationError(msg)` | 内联，`err.code === 'VALIDATION_ERROR'` 时使用 |
| `esc()` | 第 2100 行，HTML 转义 |

**insufficient balance 特殊处理：** `friendlyErrorMessage` 第 2217 行专门处理 MiniMax voice_design / voice_clone / preview 接口的余额不足错误，提示切换到 `provider=mock` 测试。

**现状：** clone 和 design 的 `err.code === 'RESOURCE_LIMIT_EXCEEDED'` 分支均调用 `renderApiError(err)`（正确）；其他错误使用 `friendlyErrorMessage(formatApiError(err))`（正确）。

### 与 audition_records.js 的关系

**audition_records.js 已迁出：**
- `window.renderAuditionRecords` — 渲染试听记录列表
- `window.deleteAuditionRecord` — 删除单条记录
- `window.clearAuditionRecords` — 清空全部记录
- `window._auditionRecords` — 记录数组状态

**仍在 index.html：**
- `renderAuditionWorkstation()` — 试听工作站 HTML 渲染（第 3274 行）
- `hexToBlobUrl(hex, mime)` — hex 字符串转 Blob URL（第 2147 行）
- audition generation 逻辑（`handleAuditionGen` 相关，第 3445 行起）
- audition 快速试听生成（clone/design result panel 内的 inline onclick，第 4193 行）
- `_auditionSelectedVoiceId` / `_auditionSelectedVoiceName` — 选中音色状态
- `_auditionDelegated` — 事件委托守卫

**voice_clone_design.js 如果迁移后：** clone/design result panel 内的快速试听功能（inline onclick）会直接调用 `/api/voice/render`，不经过 audition workstation。这意味着 `hexToBlobUrl` 或类似的 hex → audio URL 转换需要在 index.html 保留，或者作为共享 helper 单独暴露。

### 可迁移到 voice_clone_design.js 的候选内容

按独立性从高到低排序：

1. **`handleCloneVoice`** — clone 创建核心逻辑，独立性强，依赖清晰（`guardedJsonFetch`、API endpoint、DOM ids）
2. **`handleDesignVoice`** — design 创建核心逻辑，独立性强
3. **`handleUploadAudio`** — 文件上传，独立性强
4. **`handleCloneAutoId`** — voice_id 生成，完全独立
5. **`updateCloneBtnState`** — clone 按钮状态校验，依赖 clone tab DOM，独立性中等
6. **`handleImportRemoteVoice`** — 远端导入，依赖较复杂（verify vs no-verify 两种行为）

### 暂不迁移的共享内容

以下内容依赖过广，强行迁入 voice_clone_design.js 会造成循环依赖或强耦合：

| 内容 | 原因 |
|---|---|
| `populateProfileSelect` / `loadProfiles` / `_cachedProfiles` | clone/design/import/voice list/batch/audition 全部依赖 profile 系统 |
| `bindVoiceToProfile` | 被 clone result、design result、import result、voice list 四处调用 |
| `renderInlineCreateProfile` | 被 clone、design、import、voice list quick bind 四处调用 |
| `refreshVoiceBindStatus` | voice list 依赖，且依赖 `loadAllBindings` |
| `handleListVoices` / `renderVoiceTable` | voice list 独立模块，需要单独审查 |
| `renderAuditionWorkstation` / audition generation | 与 `_auditionSelectedVoiceId` 状态耦合 |
| `hexToBlobUrl` | 被 design result 和 audition generation 共用 |

### 需要先提取为 window.* 的 helper

| helper | 当前状态 | 建议 |
|---|---|---|
| `isValidVoiceId(value)` | inline function（第 3987 行） | 暴露为 `window.isValidVoiceId` 供 voice_clone_design.js 调用 |
| `bindVoiceToProfile(voiceId, provider, profileId, model)` | inline function（第 1748 行） | 暴露为 `window.bindVoiceToProfile` — 已有潜在需求，voice_clone_design.js 迁移后需此入口 |
| `renderInlineCreateProfile(container, selectEl, idPrefix)` | inline function（第 3719 行） | 暴露为 `window.renderInlineCreateProfile` |
| `populateProfileSelect(selectEl, selectedId)` | inline function（第 1708 行） | 暴露为 `window.populateProfileSelect` |
| `loadProfiles(forceRefresh)` | inline function（第 1692 行） | 暴露为 `window.loadProfiles` |
| `hexToBlobUrl(hex, mime)` | inline function（第 2147 行） | 暴露为 `window.hexToBlobUrl` — design result 需要 |

### 需要先补的 E2E

当前 E2E 对 voice clone/design/import 覆盖为零（没有任何相关测试）。建议按优先级补：

| 优先级 | E2E | 验证内容 |
|---|---|---|
| 高 | `test_voice_clone_error_insufficient_balance` | clone 余额不足错误展示，mock `POST /api/voice/clone/create` 返回 RESOURCE_LIMIT_EXCEEDED，验证 renderApiError 正确渲染 |
| 高 | `test_voice_design_mock_submit_success` | design mock 提交成功，mock `POST /api/voice/design/create` 返回成功，验证成功消息和 demo_audio_url |
| 中 | `test_voice_clone_mock_submit_success` | clone mock 提交成功，mock `POST /api/voice/clone/create` 返回成功，验证成功消息和 demo_audio_url |
| 中 | `test_voice_import_mock_success` | import mock 验证成功，mock `POST /api/voice/provider-voices/import` 返回成功 |
| 低 | `test_voice_list_loads` | 验证音色列表加载，mock `GET /api/voice/provider-voices` |

### 风险点

1. **inline onclick 注入风险**：clone/design/import 成功结果 HTML 中动态创建的元素（`cloneBindBtn`、`cloneQuickBtn` 等）使用 `btn.onclick = async () => { ... }` 直接注入事件处理器，而非事件委托。这些处理器依赖闭包中的 `data`（API 返回结果）。如果将此 HTML 生成逻辑迁入独立 JS 文件，需要处理 HTML 模板和事件绑定的分离。

2. **highRisk confirm 阻塞**：clone/design/import 操作使用 `highRisk: true`，E2E 必须使用 `provider=mock` 绕过确认框才能完成自动化测试。

3. **profile 系统耦合**：`populateProfileSelect` / `loadProfiles` / `bindVoiceToProfile` 被 clone/design/import/voice list/batch 多处共用。如果 voice_clone_design.js 需要这些函数，必须先将它们暴露为 window 入口，否则只能继续留在 index.html。

4. **provider capability 联动**：clone/design 表单的 hint 和按钮启用状态由 `provider_capabilities.js` 控制。模块迁出后需要确保 `applyVoiceCloneCapability()` / `applyVoiceDesignCapability()` 在 provider 切换时仍能被调用。

5. **hexToBlobUrl 依赖**：design 创建成功返回 `trial_audio_hex`，需要 `hexToBlobUrl` 转换为可播放音频。`hexToBlobUrl` 在 index.html 中，且被 audition generation 也使用。

### P9-FE1-G1 建议

**结论：不建议一次性抽离 voice_clone_design.js，建议拆分为多个阶段。**

**建议的最小安全第一步（voice_clone.js）：**

可独立迁移到 `voice_clone.js` 的内容：
- `handleUploadAudio` — 文件上传
- `handleCloneAutoId` — voice_id 生成
- `updateCloneBtnState` — 按钮状态
- `handleCloneVoice` — clone 创建（但需处理 inline onclick 部分）

先决条件：
- 将 `isValidVoiceId` 暴露为 `window.isValidVoiceId`
- 保留 `handleCloneVoice` 成功结果 HTML 中的 inline onclick 绑定逻辑（或重构为事件委托）
- 确保 `applyVoiceCloneCapability()` 仍可在 provider 切换时被调用

**不建议拆分 voice_design.js 的原因：**
- design 和 clone 共享 `handleImportRemoteVoice(source)` 统一处理 import
- import 面板的 clone/design 两个入口高度相似
- 强行拆分为 voice_clone.js / voice_design.js 会导致 `handleImportRemoteVoice` 重复

**建议的第二步（voice_import.js）：**
- `handleImportRemoteVoice(source)` — 统一导入处理
- 需要先确保 `bindVoiceToProfile` 已暴露为 window 入口

**建议的第三步（voice_design.js）：**
- `handleDesignVoice` — design 创建
- 需处理 `hexToBlobUrl` 依赖

**P9-FE1-G1 已完成 ✅：** `test_voice_clone_error_insufficient_balance_is_displayed` 已新增，验证 `POST /api/voice/clone/create` 返回 insufficient balance 时页面正确展示错误提示。

**P9-FE1-G2 已完成 ✅：** `test_voice_design_mock_submit_success` 已新增，验证 mock `POST /api/voice/design/create` 返回成功时页面展示"设计成功"和 voice_id，按钮正确恢复。

**P9-FE1-G3 已完成 ✅：** 暴露 `window.isValidVoiceId` / `window.loadProfiles` / `window.populateProfileSelect` / `window.bindVoiceToProfile` / `window.renderInlineCreateProfile` / `window.hexToBlobUrl`，供后续 `voice_clone.js` 等模块迁移时调用。

**P9-FE1-G4 已完成 ✅：** `app/static/js/voice_clone.js` 已抽离，IIFE 包装，4 个函数（handleUploadAudio / handleCloneAutoId / updateCloneBtnState / handleCloneVoice）全部 export 为 `window.*`；index.html 移除迁移函数体，保留原 onclick 属性；`batch_script.js` 后新增 script 标签引入；补回 `isValidVoiceId` standalone 实现；E2E `test_voice_clone_module_is_loaded_and_exports_available` 新增，22 passed。

**P9-FE1-G4-FIX 已完成 ✅：** 新增 `test_voice_clone_mock_submit_success` E2E，mock clone/create 返回成功 + demo_audio_url，验证成功文案、voice_id、audio 标签、快速绑定面板、快速试听面板、按钮恢复；mock provider-voices 避免 handleListVoices 产生真实请求；23 passed。

**下一步：** voice_clone.js 成功链路 E2E 已补齐，23 E2E passed。可进入 voice_import.js 边界审查和前置 E2E（import 链路仍待补充）。

**建议暂缓的原因：**
1. 没有任何 voice clone/design/import 相关 E2E，贸然迁移无法验证正确性（已改善：clone E2E 已建立）
2. 共享 helper（`populateProfileSelect`、`bindVoiceToProfile`、`renderInlineCreateProfile`）未暴露为 window 入口（已解决）
3. inline onclick 事件绑定方式需要重构为事件委托才能安全迁移
4. `hexToBlobUrl` 等共享 utility 需要先提取（已解决）

**下一步行动：**
1. **已完成**：voice clone/error + voice design/success + helper window exports + voice_clone.js 抽离 + clone success E2E
2. **下一步**：voice_import.js 边界审查 + 前置 E2E
3. **后续迁移**：voice_import.js → voice_design.js

### P9-FE1-H0：voice_import.js 抽离前边界审查（文档记录）

**审查时间：** 2026-05-15

**审查结论：**

**候选迁移内容：**
- `handleImportRemoteVoice(source)` — 约 134 行，同时服务 clone 和 design 两个 subtab，通过 `source` 参数切换 DOM prefix

**暂不迁移内容（共享 helpers / cache 状态）：**
- `loadProfiles` / `populateProfileSelect` / `renderInlineCreateProfile` / `bindVoiceToProfile` / `refreshVoiceBindStatus` / `handleListVoices` — 全部已为 window 导出
- `guardedJsonFetch` / `parseApiError` / `formatApiError` / `friendlyErrorMessage` / `esc` — 共享 helpers
- `_OPERATION_MESSAGES['provider_voice_import_verify']` — confirm 文案
- 快速绑定面板 HTML 模板（内联 onclick，与 voice_clone.js 模式一致）

**关键发现：**
- `POST /api/voice/provider-voices/import`，request 含 `provider / provider_voice_id / voice_type / name / verify / model / preview_text`
- `provider=mock` bypass highRisk confirm（同 clone/design）
- `verify=true` 时内部调用 preview 服务（Python 内，非 HTTP 请求，E2E 无需额外 mock）
- 导入成功后渲染 audio_player + 快速绑定面板 + 调用 `handleListVoices(true)`
- 共享 DOM id：`importProfileWrap` / `importBindModel` / `importBindBtn`（两个 subtab 共用同一 DOM）
- `setTimeout(0)` 内创建 `importBindProfile` select 并调用 `populateProfileSelect` + `renderInlineCreateProfile`

**迁移建议：**
- 建议先补 import mock success E2E（clone import 方向），再迁移 voice_import.js
- 迁移后可参照 voice_clone.js 模式：IIFE 包装 + window.handleImportRemoteVoice 导出 + onclick 属性保持不变
- 快速绑定面板绑定功能暂不需在 E2E 覆盖，focus 在 import 本身

**下一步 P9-FE1-H1：** 补 import mock success E2E（clone import 方向）

**P9-FE1-H1 已完成 ✅：** 新增 `test_voice_import_clone_mock_success` E2E，mock provider-voices/import 返回成功 + audio_asset.url，验证"导入成功"文案、provider_voice_id、audio 标签、快速绑定面板（importProfileWrap / importBindProfile / importBindModel / importBindBtn）、按钮恢复；mock profiles / capabilities / provider-voices 避免真实请求；24 passed。

**下一步：** import 链路 E2E 已建立，24 E2E passed。可进入 voice_import.js 抽离（仅迁移 handleImportRemoteVoice）。

**P9-FE1-H2 已完成 ✅：** 创建 `app/static/js/voice_import.js`，IIFE 包装，`window.handleImportRemoteVoice` 导出；G3 helpers（loadProfiles/populateProfileSelect/renderInlineCreateProfile/bindVoiceToProfile/refreshVoiceBindStatus/handleListVoices）使用 `window.*` 调用；shared helpers 直接使用；index.html 添加 script 标签（位于 voice_clone.js 之后）；删除 index.html 中的 empty function stub；保留 Migration comment；E2E `test_voice_import_module_is_loaded_and_exports_available` 新增；25 passed。

**下一步 P9-FE1-I0：** voice_design.js 快速边界审查（审查 `handleDesignVoice` 依赖边界，判断是否可独立迁移）

**P9-FE1-I0 已完成 ✅：** 审查结论：可独立迁移。

- `handleDesignVoice` DOM prefix `design*`，与 clone（`clone*`）/import（`importClone*`/`importDesign*`）无重叠
- API：`POST /api/voice/design/create?provider={provider}`，payload `{ prompt, preview_text, confirm_cost, voice_id? }`，与 clone/design import 均不同
- highRisk：`guardedJsonFetch(..., { operation: 'voice_design', highRisk: true })`，`provider=mock` 绕过 confirm
- quick preview：`fetch('/api/voice/render', ...)` raw fetch，不用 guardedJsonFetch，无 highRisk
- 依赖的 window helpers 全部已暴露：`isValidVoiceId`、`hexToBlobUrl`、`populateProfileSelect`、`renderInlineCreateProfile`、`bindVoiceToProfile`、`refreshVoiceBindStatus`、`handleListVoices`
- shared helpers（guardedJsonFetch / parseApiError / formatApiError / friendlyErrorMessage / esc / renderApiError / renderValidationError）直接使用
- provider capability 不在 `handleDesignVoice` 内部检查，由 `provider_capabilities.js` 的 `applyVoiceDesignCapability()` 控制按钮状态
- quick bind 面板和 quick preview 面板均为 setTimeout 内动态创建，与 clone/design import 结构一致
- `test_voice_design_mock_submit_success` 已覆盖成功链路，可作为 I1 迁移回归保护
- I1 允许修改范围：仅迁移 `handleDesignVoice`，不动其他任何函数

**下一步 P9-FE1-I1：** voice_design.js 抽离（仅迁移 `handleDesignVoice`，参照 voice_import.js 模式）

**P9-FE1-I1 已完成 ✅：** 创建 `app/static/js/voice_design.js`，IIFE 包装，`window.handleDesignVoice` 导出；G3 helpers 使用 `window.*` 调用；shared helpers 直接使用；script 标签位于 voice_import.js 之后；index.html 添加 Migration comment；E2E `test_voice_design_mock_submit_success` 验证成功链路。

**P9-FE1-CHECK 已完成 ✅：** voice advanced stage 收口检查通过。

- script 加载顺序正确：voice_clone.js → voice_import.js → voice_design.js → inline script
- index.html 无同名函数声明覆盖，无空函数 stub
- onclick 入口可用：`onclick="handleDesignVoice()"` 等
- E2E 25 passed
- 已更新文档：NEXT_TASKS.md、FRONTEND_MODULE_MAP.md、P9_FRONTEND_MODULARIZATION.md（本文档）、PROJECT_HEALTH_CHECK.md
