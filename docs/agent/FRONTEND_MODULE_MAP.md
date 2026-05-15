# Frontend Module Map

## index.html（仍在 index.html 的职责）

| 职责 | 说明 |
|---|---|
| Shell / tab / subtab | 所有 tab/subtab 切换逻辑 |
| Shared helpers | `guardedJsonFetch`, `parseApiError`, `formatApiError`, `friendlyErrorMessage`, `esc`, `renderApiError`, `renderValidationError` |
| Profile / binding helpers | `loadProfiles`, `populateProfileSelect`, `renderInlineCreateProfile`, `bindVoiceToProfile`, `refreshVoiceBindStatus` |
| Voice list | `handleListVoices`, `renderVoiceTable`, `filterVoiceList` |
| Audition workstation | `renderAuditionWorkstation` |
| Voice design | `handleDesignVoice` |
| Shared batch | batch 状态管理，被 longtext/script 共用 |
| highRisk confirm | `confirmHighCostVoiceAction` |
| Error helpers | `renderApiError`, `renderValidationError` 等 |

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
- **职责**：长文本批量任务提交 / 进度
- **window exports**：`window.handleBatchLongtextSubmit`
- **依赖 helper**：`guardedJsonFetch`, `esc`
- **对应 E2E**：`test_batch_longtext_module_is_loaded_and_submit_validation_works`, `test_batch_longtext_mock_submit_success_starts_progress`

### batch_script.js
- **职责**：剧本科本批量任务提交 / 进度
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

## 下一候选模块

### voice_design.js（I0 审查完成，可迁移）
- **职责**：声音设计入口 / 提交 / 快速试听 / 快速绑定
- **window exports**：`window.handleDesignVoice`
- **依赖 helper**：
  - `window.isValidVoiceId`（voice_id 格式校验）
  - `window.hexToBlobUrl`（hex 音频解析）
  - `window.handleListVoices`
  - `window.populateProfileSelect`
  - `window.renderInlineCreateProfile`
  - `window.bindVoiceToProfile`
  - `window.refreshVoiceBindStatus`
  - shared helpers: `guardedJsonFetch`, `parseApiError`, `formatApiError`, `friendlyErrorMessage`, `esc`, `renderApiError`, `renderValidationError`
- **DOM prefix**：`design*`（designProvider / designVoiceId / designPrompt / designPreviewText / designResult / designBtn）
- **动态创建的 DOM ids**：`designProfileWrap`, `designBindProfile`, `designBindModel`, `designBindBtn`, `designBindResult`, `designQuickText`, `designQuickBtn`, `designQuickResult`
- **API**：`POST /api/voice/design/create?provider={provider}`，payload `{ prompt, preview_text, confirm_cost, voice_id? }`
- **highRisk**：是（`guardedJsonFetch(..., { highRisk: true })`），`provider=mock` 绕过 confirm
- **quick preview**：`fetch('/api/voice/render', ...)` 不用 `guardedJsonFetch`，无 highRisk confirm
- **response 字段**：`voice_id`, `message`, `trial_audio_hex`, `trial_audio_url`
- **对应 E2E**：`test_voice_design_mock_submit_success`（已有成功链路）
- **I1 迁移允许范围**：仅迁移 `handleDesignVoice`，不动 `handleDesignVoice` 以外的任何函数
- **I1 必须测试**：voice design E2E（已有 `test_voice_design_mock_submit_success`）

## 严禁迁移（当前不宜动）

- `profile_binding.js` — 依赖太广，强行拆出会导致循环依赖
- `batch_shared.js` — shared batch state 风险高
- `error_helpers.js` — 被多处引用，迁移成本大
- `provider_capabilities.js` — 已稳定，暂无充分理由动
