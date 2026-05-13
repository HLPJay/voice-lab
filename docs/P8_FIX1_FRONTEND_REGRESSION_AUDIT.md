# P8-FIX1A 前端回归缺陷审查

## 1. 当前分支与提交

- 分支：dev
- 最新提交：ee93d6e p8-4f close history download acceptance
- 状态：工作区干净

---

## 2. Tab 完整性检查结果

### 2.1 Tab 按钮与内容区映射

| data-tab | 对应 id | 状态 |
|---|---|---|
| `workspace` | `tab-workspace` | 存在 |
| `longtext` | `tab-longtext` | 存在 |
| `script` | `tab-script` | 存在 |
| `voices` | `tab-voices` | 存在 |
| `history` | `tab-history` | 存在 |
| `advanced` | `tab-advanced` | 存在 |

**结论：所有 6 个 tab 均有对应内容区，无缺失。**

### 2.2 长文本 / 剧本模块内容检查

`tab-longtext`（第 1156 行）和 `tab-script`（第 1264 行）均存在完整内容：

- 长文本配置区：batchText textarea、batchProfile select、batchProvider select、batchStrategy select、batchMaxChars input、batchSilence input、batchOutputFormat select、batchLongtextSubmit button
- 剧本配置区：batchScriptProvider select、batchScriptSilence input、batchScriptOutputFormat select、batchScriptNeedSubtitle checkbox、batchScriptSubmit button、addScriptLine button

**结论：长文本和剧本模块 DOM 完整，未丢失。**

### 2.3 批量 API 和 Schema 检查

后端批量相关代码仍存在：

- `LongtextBatchRequest` schema（schemas.py:343）
- `ScriptBatchRequest` schema（schemas.py:365）
- `BatchSubmitResponse` schema（schemas.py:376）
- `BatchSegmentStatus` schema（schemas.py:384）
- `BatchStatusResponse` schema（schemas.py:394）
- `/api/voice/batch/submit` endpoint（batch.py:23）
- `/api/voice/batch/{batch_id}/status` endpoint（batch.py:40）
- `/api/voice/batch/{batch_id}/download` endpoint（batch.py:49）
- `/api/voice/batch/{batch_id}/retry` endpoint（batch.py:78）

**结论：后端批量 API 和 Schema 完整，未丢失。**

---

## 3. 历史播放 / 下载问题原因分析

### 3.1 VoiceJobRead 模型字段

`VoiceJobRead`（schemas.py:139-151）包含字段：

```
job_id, job_type, status, provider, model, profile_id,
input_text, processed_text, provider_trace_id, error_message,
created_at, updated_at
```

**不包含**：`audio_asset`、`audio_asset_id`、`asset_id`

### 3.2 getHistoryAudioAssetId 实现

```javascript
function getHistoryAudioAssetId(job) {
    return job.audio_asset?.id || job.audio_asset_id || job.asset_id || null;
}
```

由于 `VoiceJobRead` 不返回音频资产字段，此函数始终返回 `null`。

### 3.3 结论

**历史播放 / 下载不可用不是前端 bug，而是后端 `/api/voice/jobs` 返回的 `VoiceJobRead` 模型不包含音频资产字段。**

这是后端字段限制，需要后端在 `VoiceJobRead` 中增加 `audio_asset` / `audio_asset_id` 字段才能真正支持历史播放/下载。这正是 P8-BE1 遗留项所指的问题。

---

## 4. 新增历史识别问题分析

### 4.1 历史加载触发条件

`toggleHistory()` 函数（index.html:1796）：

```javascript
function toggleHistory() {
    const area = document.getElementById('historyArea');
    const isOpen = area.style.display !== 'none';
    area.style.display = isOpen ? 'none' : '';
    toggle.textContent = isOpen ? '历史记录 ▾' : '历史记录 ▴';
    if (!isOpen && !_historyOffset) {
        loadHistory(0);
    }
}
```

### 4.2 问题分析

- `loadHistory(0)` 在页面初始化时调用一次（index.html:1853）
- `toggleHistory` 中只有在 **历史区域关闭 AND `_historyOffset === 0`** 时才触发 `loadHistory(0)`
- `_historyOffset` 在首次加载后变为非零值（10 +）
- 一旦 `_historyOffset > 0`，即使重新展开历史区域（关闭再打开），也不会触发刷新

**问题场景：**

1. 用户打开页面，历史在后台加载（`_historyOffset = 10`，但区域隐藏）
2. 用户展开历史，看到已有数据
3. 用户离开历史 tab（workspace 或其他 tab）
4. 用户生成新内容
5. 用户切换回历史 tab（通过 tab 按钮，不是 toggle）
6. 历史区域保持展开状态（`isOpen = true`）
7. 条件 `!isOpen && !_historyOffset` 为 `false && !10` = `false`
8. **loadHistory 不被调用，新任务不显示**

### 4.3 VoiceJob 写入验证

所有渲染服务均正确写入 `VoiceJob`：

- `voice_render_service.py:78` - 同步渲染创建 VoiceJob
- `async_render_service.py:90` - 异步渲染创建 VoiceJob
- `stream_render_service.py:84` - 流式渲染创建 VoiceJob
- `batch_orchestration_service.py:547` - 批量任务创建 VoiceJob
- `voice_variant_service.py:46-56` - 变体通过 render_service 间接创建 VoiceJob

**结论：新任务已正确写入 VoiceJob，前端问题是因为缺少"刷新历史"功能导致新任务不显示。**

### 4.4 排序验证

`voice_job_repo.py:46`：`query.order_by(VoiceJob.created_at.desc())`

历史按最新排序，正确。

---

## 5. 前端全局 DOM / JS 断点检查

### 5.1 所有 onclick/oninput/onchange 引用函数验证

以下所有函数均存在于 index.html 中：

| 函数 | 行号 |
|---|---|
| `toggleHistory` | 1796 |
| `loadHistory` | 1807 |
| `loadMoreHistory` | 1847 |
| `handleHistorySearchInput` | 2659 |
| `handleHistoryStatusFilterChange` | 2666 |
| `clearHistoryFilters` | 2673 |
| `handleGenerate` | 1855 |
| `handleListVoices` | 3155 |
| `filterVoiceList` | 3201 |
| `switchAdvancedSubtab` | 1132 |
| `handleUploadAudio` | 3528 |
| `handleCloneAutoId` | 3581 |
| `handleCloneVoice` | 3595 |
| `handleImportRemoteVoice` | 3787 |
| `handleDesignVoice` | 3921 |
| `handleCreateProfile` | 4184 |
| `handleListBindings` | 4090 |
| `handleCreateBinding` | 4136 |
| `handleDeleteVoice` | 3485 |
| `handleDeleteBinding` | 4231 |
| `handleBatchLongtextSubmit` | 4308 |
| `handleBatchScriptSubmit` | 4384 |
| `handleBatchRetry` | 4677 |
| `handleBatchPlay` | 4672 |
| `addScriptLine` | 4268 |
| `removeScriptLine` | 4293 |
| `handlePageSizeChange` | 3308 |
| `handlePrevPage` | 3314 |
| `handleNextPage` | 3321 |
| `manualRefreshAsyncJob` | 1773 |
| `handleStopAsyncPolling` | 1778 |

**所有事件处理函数均存在，无断点。**

### 5.2 getElementById 引用验证

关键 DOM id 均存在：

- `tab-workspace`、`tab-longtext`、`tab-script`、`tab-voices`、`tab-history`、`tab-advanced`
- `historyList`、`loadMoreHistory`、`historyToggle`、`historyArea`
- `historyToolbar`、`historySearch`、`historyStatusFilter`、`historyFilterHint`、`historyClearFilters`
- `batchText`、`batchProfile`、`batchProvider`、`batchStrategy`、`batchMaxChars`、`batchSilence`
- `batchScriptProvider`、`batchScriptSilence`、`batchScriptOutputFormat`
- `generateBtn`、`listVoicesBtn`
- `batchLongtextSubmit`、`batchScriptSubmit`、`batchRetryBtn`

---

## 6. 问题汇总与修复优先级

### 高优先级

| # | 问题 | 原因 | 修复方式 |
|---|---|---|---|
| 1 | 新生成的任务不在历史中显示 | `toggleHistory` 打开历史后不刷新 | 新增"刷新历史"按钮，在 loadHistory 时不清空现有数据或提供强制刷新选项 |

### 中优先级

| # | 问题 | 原因 | 修复方式 |
|---|---|---|---|
| 2 | 历史播放/下载不可用 | 后端 `VoiceJobRead` 不返回音频资产字段 | 后端 P8-BE1（增加 audio_asset 字段），前端已准备好安全降级 |

### 低优先级（已知遗留）

| # | 问题 | 状态 |
|---|---|---|
| 3 | P8-UX1 桌面宽屏布局 | 未处理，保持遗留 |
| 4 | P8-BE1 历史任务返回音频字段 | 后端问题，待处理 |

---

## 7. 前端回归缺陷审查结论

### 7.1 Tab 完整性

**无缺陷**。所有 6 个 tab（workspace/longtext/script/voices/history/advanced）均有对应内容区。

### 7.2 长文本 / 剧本模块

**无缺陷**。DOM 完整，后端 API/Schema 完整，JS 函数完整。

### 7.3 历史播放 / 下载

**非前端 bug**。后端 `VoiceJobRead` 不包含音频资产字段是预期限制，前端安全降级工作正常。

### 7.4 新增历史识别

**存在前端缺陷**。历史加载逻辑问题：只有在 `_historyOffset === 0` 时展开历史才触发加载，导致新生成任务后返回历史时无法看到新任务。

### 7.5 全局 JS 断点

**无缺陷**。所有 onclick/oninput/onchange 引用函数均存在，所有 getElementById 引用 id 均存在。

---

## 8. P8-FIX1A 阶段结论

P8-FIX1A 已完成前端回归缺陷审查。

审查结果总结：

- **Tab 完整性**：无缺陷，所有 tab 正常
- **长文本/剧本模块**：无缺陷，DOM 和 API 均完整
- **历史播放/下载不可用**：后端字段限制，非前端 bug
- **新增历史不显示**：存在前端缺陷，缺少刷新历史机制
- **全局 JS 断点**：无缺陷

建议在 P8-FIX1B 中修复"新增历史不显示"问题（新增刷新历史按钮）。

---

## 9. 下一阶段建议

**下一阶段：P8-FIX1B - 前端回归缺陷修复**

主要任务：

- 在历史工具栏（historyToolbar）中新增"刷新历史"按钮
- 刷新按钮点击后强制从 offset=0 重新加载历史
- 不修改后端 API
- 不修改 `VoiceJobRead` 模型
- 不做大规模重构

同时保留以下遗留项：

- P8-BE1：后端 VoiceJobRead 增加 audio_asset 字段（解决历史播放/下载）
- P8-UX1：桌面宽屏布局与响应式适配

---

## 附录：静态检查命令记录

### Tab 完整性

```bash
grep -n 'data-tab=' app/static/index.html
grep -n 'id="tab-' app/static/index.html
```

### 批量 API 检查

```bash
grep -n 'LongtextBatchRequest|ScriptBatchRequest|BatchSubmitResponse' app/domain/schemas.py
grep -n '/batch/submit|/batch/{batch_id}/status' app/api/batch.py
```

### 历史播放/下载问题

```bash
grep -n 'audio_asset|audio_asset_id|asset_id' app/domain/schemas.py
grep -n 'function getHistoryAudioAssetId' app/static/index.html
```

### 新增历史不显示问题

```bash
grep -n '!_historyOffset\|loadHistory(0)' app/static/index.html
```

### JS 断点检查

```bash
grep -n 'onclick=\|oninput=\|onchange=' app/static/index.html | wc -l
# 验证每个引用的函数存在
grep -c 'function xxx' app/static/index.html
```
