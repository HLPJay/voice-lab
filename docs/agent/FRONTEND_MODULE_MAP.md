# Frontend Module Map

## index.html（仍在 index.html 的职责）

| 职责 | 说明 | 可抽离性 |
|---|---|---|
| Shell / tab / subtab | 所有 tab/subtab 切换逻辑、visibility 状态 | ❌ 不应抽 |
| Shared helpers | `guardedJsonFetch`, `parseApiError`, `formatApiError`, `friendlyErrorMessage`, `esc`, `renderApiError`, `renderValidationError` | ⚠️ 收益小，不急 |
| Profile / binding helpers | `loadProfiles`, `populateProfileSelect`, `renderInlineCreateProfile`, `bindVoiceToProfile`, `refreshVoiceBindStatus` | ❌ 依赖太广 |
| Voice list | `handleListVoices`, `renderVoiceTable`, `filterVoiceList`, `loadVoices`, pagination | ✅ 可抽 |
| Audition workstation | `renderAuditionWorkstation`, `updateAuditionSelected`, `setupAuditionWorkstation`, `handleGenerateAudition` | ❌ 强耦合生成链路 |
| Shared batch 状态 | `_batchPollTimer`, `_currentBatchId`, `_currentBatchPanelId`, `_batchTimeline` | ❌ 不应动 |
| Shared batch 函数 | `showBatchProgress`, `startBatchPoll`, `stopBatchPoll`, `pollBatchStatus`, `renderBatchStatus` 等 | ❌ 两批量共用 |
| highRisk confirm | `confirmHighCostVoiceAction` | ❌ 不应动 |
| Error helpers | `renderApiError`, `renderValidationError`, `friendlyErrorMessage` 等 | ⚠️ 可抽但收益小 |
| 单条生成链路 | `handleGenerate`, `startStreamGenerate`, `renderStreamResult`, `startAsyncPolling` 等 | ❌ 强耦合 tab 切换 |
| Script line 管理 | `addScriptLine`, `removeScriptLine`, `updateScriptLineLimitState`, `_scriptRows` | ❌ 强耦合事件委托 |

## 已抽离模块

### provider_capabilities.js
- **职责**：Provider capability 加载 / 切换 / 失败降级
- **window exports**：能力约束入口（`applyVoiceCloneCapability` 等）
- **依赖 helper**：无
- **对应 E2E**：`test_provider_capability_loaded`

### runtime_status.js
- **职责**：顶部用量状态条
- **window exports**：无直接入口
- **依赖 helper**：无
- **对应 E2E**：由其他 E2E 间接覆盖

### history.js
- **职责**：历史任务渲染 / 刷新 / 删除
- **window exports**：无直接入口
- **依赖 helper**：无
- **对应 E2E**：`test_history_tab_loads`, `test_history_delete_job`

### audition_records.js
- **职责**：试听记录渲染 / 删除
- **window exports**：无直接入口
- **依赖 helper**：无
- **对应 E2E**：`test_audition_records_render`, `test_audition_records_delete`

### batch_longtext.js
- **职责**：长文本批量任务提交
- **window exports**：`window.handleBatchLongtextSubmit`
- **依赖 helper**：`guardedJsonFetch`, `esc`
- **对应 E2E**：`test_batch_longtext_module_is_loaded_and_submit_validation_works`, `test_batch_longtext_mock_submit_success_starts_progress`

### batch_script.js
- **职责**：剧本科本批量任务提交
- **window exports**：`window.handleBatchScriptSubmit`
- **依赖 helper**：`guardedJsonFetch`, `esc`
- **对应 E2E**：`test_batch_script_module_is_loaded_and_submit_validation_still_works`, `test_batch_script_mock_submit_success_starts_progress`

### voice_clone.js
- **职责**：声音克隆入口 / 提交 / 快速试听 / 快速绑定
- **window exports**：`handleUploadAudio`, `handleCloneAutoId`, `updateCloneBtnState`, `handleCloneVoice`
- **依赖 helper**：`window.loadProfiles`, `window.populateProfileSelect`, `window.renderInlineCreateProfile`, `window.bindVoiceToProfile`, `window.refreshVoiceBindStatus`, `guardedJsonFetch`, `parseApiError`, `esc`
- **对应 E2E**：`test_voice_clone_module_is_loaded_and_exports_available`, `test_voice_clone_mock_submit_success`, `test_voice_clone_error_insufficient_balance`

### voice_import.js
- **职责**：远端音色导入，同时服务 clone import 和 design import
- **window exports**：`handleImportRemoteVoice`
- **依赖 helper**：`window.loadProfiles`, `window.populateProfileSelect`, `window.renderInlineCreateProfile`, `window.bindVoiceToProfile`, `window.refreshVoiceBindStatus`, `window.handleListVoices`, `guardedJsonFetch`, `parseApiError`, `formatApiError`, `friendlyErrorMessage`, `esc`, `renderValidationError`
- **对应 E2E**：`test_voice_import_module_is_loaded_and_exports_available`, `test_voice_import_clone_mock_success`

### voice_design.js
- **职责**：声音设计入口 / 提交 / 快速试听 / 快速绑定
- **window exports**：`handleDesignVoice`
- **依赖 helper**：`window.isValidVoiceId`, `window.hexToBlobUrl`, `window.handleListVoices`, `window.populateProfileSelect`, `window.renderInlineCreateProfile`, `window.bindVoiceToProfile`, `window.refreshVoiceBindStatus`, `guardedJsonFetch`, `parseApiError`, `formatApiError`, `friendlyErrorMessage`, `esc`, `renderApiError`, `renderValidationError`
- **对应 E2E**：`test_voice_design_mock_submit_success`

## 下一候选模块（按 P9-FE2-A0 审查）

### voice_list.js（优先级 1，可小步抽离）
- **职责**：voice 列表查询 / 渲染 / 过滤 / 分页
- **window exports**：`handleListVoices`, `loadVoices`
- **DOM prefix**：`voiceProvider` / `voiceType` / `voiceSearch` / `listVoicesBtn` / `voiceListResults`
- **依赖 helper**：`window.loadProfiles`, `window.populateProfileSelect`, `window.bindVoiceToProfile`, `window.refreshVoiceBindStatus`, `guardedJsonFetch`, `esc`
- **状态**：`window._voicePagination`, `_cachedVoices`
- **API**：`GET /api/voice/provider-voices?provider=...`
- **风险**：中等（`_cachedVoices` 被 voice_clone.js 等多处引用）
- **对应 E2E**：无（`test_audition_records_module_and_voices_tab_open` 仅覆盖 tab 打开）
- **建议**：先补 `test_voice_list_loads` E2E，再小步迁移 `handleListVoices`

### profile_binding.js（优先级 3，不建议抽）
- **原因**：`populateProfileSelect` 被 batch_script.js 行管理、`addScriptLine`、clone/design/import result panel 共用；强行拆出导致所有调用方都要改；`_cachedProfiles` 是隐含依赖
- **当前 window 出口**：`loadProfiles`, `populateProfileSelect`, `renderInlineCreateProfile`, `bindVoiceToProfile`, `refreshVoiceBindStatus` — 已够用

### error_helpers.js（优先级 4，收益小）
- **职责**：错误解析、格式化、渲染
- **风险**：中等（12+ call sites）
- **建议**：当前 shared helpers 够用，迁移收益覆盖不了风险

### batch_shared.js（优先级 5，shared state 冲突）
- **风险**：极高（`_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` 被两批量共用）
- **建议**：需统一状态管理设计，当前阶段不应动

### audition_workstation.js（优先级 2，不建议单独抽）
- **原因**：`renderAuditionWorkstation` 强耦合 `handleGenerate` 单条生成链路，单独抽离 voice 无关部分价值不大
- **audition_generation 链路**：`handleGenerateAudition` → `handleGenerate` → `startStreamGenerate` / `startAsyncPolling`，全部强耦合
- **建议**：audition workstation 和单条生成链路需整体考虑，不应单独抽

## 严禁迁移（当前不宜动）

- `profile_binding.js` — 依赖太广，强行拆出会导致循环依赖
- `batch_shared.js` — shared batch state 风险高
- `error_helpers.js` — 被多处引用，迁移成本大，收益小
- `provider_capabilities.js` — 已稳定，无充分理由动
- tab/subtab switching — 涉及所有 Tab DOM visibility 状态
- `handleGenerate` 及单条生成链路 — 强耦合 tab 切换
- `addScriptLine` / `removeScriptLine` / `_scriptRows` — 强耦合事件委托
