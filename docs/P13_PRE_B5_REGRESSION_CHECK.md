# P13-PRE-B5-REGRESSION-CHECK：已有功能回归自检

## 背景

B4 引入 sample sidebar UI 后曾出现 tab-workspace 闭合结构缺失，导致其他 tab 无法打开。进入 B5 前，需要对已有功能做一次集中回归自检，确认 P13-B1 到 B4 没有破坏基础功能。

## 自检结论

### 1. Tab 导航 — 通过

- 6 个 tab-content div 全部存在且互为兄弟节点
- tab-longtext / tab-script / tab-voices / tab-history / tab-advanced 不嵌套在 tab-workspace 内
- sampleSidebarRoot 只在 tab-workspace 内（不在其他 5 个 tab 内）
- 6 个 tab-btn data-tab 全部有对应 tab-content

**验证文件**：`tests/test_tab_layout_static.py`（22 项）+ `tests/test_existing_function_regression_static.py`（13 项 tab 测试）

### 2. Workspace 基础能力 — 通过

- `#textInput` 存在，maxlength=9500 ✅
- `#charCount` / `#costHint` / `#profileSelect` / `#providerSelect` / `#audioFormat` / `#outputFormat` / `#generateBtn` / `#resultsArea` 全部存在 ✅
- 四种生成模式（single / async / stream / variants）全部存在 ✅

**验证文件**：`tests/test_existing_function_regression_static.py`（10 项 workspace 限制 + 4 项生成模式）

### 3. Workspace sample 接入隔离 — 通过

- `safePushWorkspaceSample` 只在有 asset_id 时写入（`if (!assetId) return null`）✅
- stream 不保存 blob URL（只保存 asset.id 存在时的服务端 URL）✅
- variants 每个 audio_asset_id 独立 sample（forEach 遍历，每个非空才 push）✅
- workspace 失败分支不写 sample（assetId 为空直接返回）✅

**验证文件**：`tests/test_existing_function_regression_static.py`（4 项 workspace sample 集成测试）

### 4. 长文本 batch 表单 — 通过

- `#batchText` maxlength=50000 ✅
- `#batchProfile` / `#batchProvider` / `#batchStrategy` / `#batchMaxChars` / `#batchSilence` / `#batchOutputFormat` / `#batchNeedSubtitle` / `#batchLongtextSubmit` / `#batchProgressPanel` / `#batchResultPlayer` / `#batchMergedAudio` / `#batchDownloadAudio` 全部存在 ✅

**验证文件**：`tests/test_existing_function_regression_static.py`（14 项 batch longtext DOM 测试）

### 5. 剧本 batch 表单 — 通过

- `#batchScriptProvider` / `#batchScriptSilence` / `#batchScriptOutputFormat` / `#batchScriptNeedSubtitle` / `#scriptLines` / `#scriptAddLineBtn` / `#batchScriptSubmit` / `#batchScriptProgressPanel` / `#batchScriptMergedAudio` / `#batchScriptDownloadAudio` 全部存在 ✅

**验证文件**：`tests/test_existing_function_regression_static.py`（11 项 batch script DOM 测试）

### 6. Audition 试听 — 通过

- `#auditionText` maxlength=1000 ✅
- `#auditionModel` / `#auditionGenBtn` / `#auditionResult` / `#auditionRecordsPanel` 全部存在 ✅
- `window.safePushAuditionSample` 存在（index.html inline）✅
- `safePushAuditionSample` 只在 `if (data.audio_asset && data.audio_asset.url)` 成功分支调用 ✅
- `safePushAuditionSample` 拒绝 blob: URL ✅

**验证文件**：`tests/test_existing_function_regression_static.py`（6 项 audition DOM + 3 项 sample 集成测试）

### 7. History 历史模块 — 通过

- `window.loadHistory` / `window.refreshHistory` / `window.loadMoreHistory` / `window.toggleHistoryAudio` / `window.deleteHistoryJob` / `window.copyJobId` 全部存在 ✅
- `toggleHistoryAudio` 调用 `audioEl.play()` ✅
- `play()` Promise 有 `.catch()` 处理浏览器阻止自动播放 ✅
- 历史下载 URL 使用 `/api/voice/assets/{assetId}/download` ✅
- 删除历史使用 `DELETE /api/voice/jobs/{jobId}` ✅

**验证文件**：`tests/test_history_play_static.py`（10 项）+ `tests/test_existing_function_regression_static.py`（10 项 history 测试）

### 8. sample sidebar 隔离 — 通过

- `sample_sidebar.js` 只通过 `SampleStore.getSamples()` 读取样本 ✅
- 不直接 localStorage.getItem ✅
- 不直接 JSON.parse ✅
- 不调用 fetch / guardedJsonFetch ✅
- 不引用 batch_longtext / batch_script ✅
- 不引用 history sample_store ✅
- 不改 workspace / audition sample 写入逻辑 ✅

**验证文件**：`tests/test_sample_sidebar_static.py`（85 项）+ `tests/test_existing_function_regression_static.py`（7 项 sidebar 隔离测试）

### 9. localStorage 隔离 — 通过

- SampleStore 使用 `voice_lab_recent_samples_v1` ✅
- SampleStore 不读写 `recentJobs`（仅在注释中说明"不读写"，无实际代码引用）✅
- sample sidebar 不读写 `recentJobs` ✅
- workspace sample 不读写 `recentJobs` ✅
- audition sample 不读写 `recentJobs` ✅

**验证文件**：`tests/test_sample_store_static.py`（25 项）+ `tests/test_existing_function_regression_static.py`（3 项 localStorage 隔离测试）

## 手动验收清单

| # | 验收项 | 状态 |
|---|---|---|
| 1 | 打开页面，Console 无红色错误 | 待手动验证 |
| 2 | 逐个点击 6 个 tab，内容均显示 | 待手动验证 |
| 3 | Workspace 输入 100 字，字数统计正常 | 待手动验证 |
| 4 | Workspace 粘贴超过 9500 字，输入受限 | 待手动验证 |
| 5 | 长文本 tab 可输入，batchText 50000 限制存在 | 待手动验证 |
| 6 | 剧本 tab 可添加 / 删除台词行 | 待手动验证 |
| 7 | 音色 tab 可打开 audition 面板 | 待手动验证 |
| 8 | History tab 可加载列表 | 待手动验证 |
| 9 | History 播放按钮点击后自动播放 | 待手动验证 |
| 10 | sample sidebar 只在 Workspace 出现 | 待手动验证 |
| 11 | sample sidebar 刷新 / 清空 / 删除按钮存在 | 待手动验证 |
| 12 | 切换 tab 后页面不报错 | 待手动验证 |

## 测试结果

- `tests/test_sample_store_static.py` — 25 项，全部通过 ✅
- `tests/test_sample_store_workspace_integration_static.py` — 36 项，全部通过 ✅
- `tests/test_sample_store_audition_integration_static.py` — 25 项，全部通过 ✅
- `tests/test_history_play_static.py` — 10 项，全部通过 ✅
- `tests/test_sample_sidebar_static.py` — 85 项，全部通过 ✅
- `tests/test_tab_layout_static.py` — 22 项，全部通过 ✅
- `tests/test_existing_function_regression_static.py` — 92 项，全部通过 ✅

**总计：295 项测试，全部通过。**

## 阶段边界

- 不实现 B5
- 不调用真实 MiniMax
- 不改后端 API / 数据库
- 不改 index.html / JS / sample_store.js / sample_sidebar.js / history.js
- 发现问题先记录，不扩大修复范围

## 发现的问题

无。

## 阶段状态

P13-PRE-B5-REGRESSION-CHECK 自检通过，建议进入 P13-CREATION-B5-MVP1。
