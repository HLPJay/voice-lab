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

## 3. 当前仍留在 index.html 的逻辑

- Tab 切换
- 表单提交与校验
- 单条生成（同步/异步/流式）
- 长文本批量
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

### 5.1 audition_records.js

**理由：** 试听记录逻辑与音色 Tab 耦合，状态为 `_auditionRecords`。

**应迁移：**
- `_auditionRecords` 状态
- `loadAuditionRecords()`、`renderAuditionRecords()`
- 试听播放器相关

### 5.3 batch_longtext.js

**理由：** 长文本批量逻辑较剧本批量简单，状态结构相对扁平。

**应迁移：**
- 长文本 Tab 的 `handleBatchSubmit()`
- 进度轮询 `showBatchProgress()`、`startBatchPoll()`、`pollBatchStatus()`
- 结果渲染 `renderBatchStatus()`

### 5.4 batch_script.js

**理由：** 剧本批量状态复杂（`scriptRows` 数组、角色/台词状态），建议有更多 E2E 覆盖后再拆。

**应迁移：**
- 剧本 Tab 的 `handleBatchScriptSubmit()`
- `scriptRows` 状态管理
- 进度轮询和结果渲染

### 5.5 voice_clone_design.js

**理由：** 克隆/设计/导入逻辑交织，且依赖 provider_capabilities.js 的能力约束，建议最后拆。

**应迁移：**
- `handleCloneSubmit()`、`handleDesignSubmit()`
- `bindVoiceToProfile()`
- 导入音色相关逻辑

## 6. 当前测试覆盖

| 测试文件 | 覆盖范围 |
|---|---|
| test_frontend_capabilities.py | 主页面加载、capability 控件、provider 切换、失败降级、Admin 页面、Admin 矩阵、剧本 Tab 回归、history.js 模块加载、History Tab 打开与刷新（共 10 个 E2E） |

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
