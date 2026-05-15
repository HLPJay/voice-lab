# P12-USAGE-FIX4-A0：音频下载失败审查

**审查时间：** 2026-05-15

---

## 1. 当前下载路径总览表

| 场景 | 前端函数 | 下载按钮 DOM | href 来源 | 使用 asset API | 是否可能失效 | 风险等级 | 备注 |
|---|---|---|---|---|---|---|---|
| 单条同步生成 | `renderResults` | `#resultsArea` 内 `downloadBtnHtml` | `/api/voice/assets/${assetId}/download` | ✅ 是 | 否 | **低** | 正确使用 asset download |
| 异步轮询生成 | `renderAsyncResult` | `#resultsArea` 内 `downloadBtnHtml` | `/api/voice/assets/${assetId}/download` | ✅ 是 | 否 | **低** | 正确使用 asset download |
| 流式生成 | `renderStreamResult` | 两个下载按钮 | (1) `/api/voice/assets/${assetId}/download`<br>(2) `blobUrl` | ✅/⚠️ 混合 | blob 仅当前会话 | **中** | 正确标注了浏览器缓存限制 |
| 批量长文本 | `renderBatchResultPlayer` | `#batchDownloadAudio` | 优先 `/api/voice/batch/{batch_id}/download`，fallback `merged_audio.id` → `merged_audio.url` | ✅ 是 | 否 | **低（FIX4 规范化）** | FIX4 优先 batch 语义化 endpoint |
| 批量剧本 | `renderBatchResultPlayer` | `#batchScriptDownloadAudio` | 同上 | ✅ 是 | 否 | **低（FIX4 规范化）** | 同上，batch_longtext/script 共用同一函数 |
| 批量字幕 | `renderBatchResultPlayer` | `#batchDownloadSubtitle` | `/api/voice/assets/${subId}/download` | ✅ 是 | 否 | **低** | 正确使用 asset API；FIX4 不改变 subtitle 逻辑 |
| 最近任务恢复 | `renderRecoveredJob` | `#resultsArea` 内 `downloadBtnHtml` | `/api/voice/assets/${assetId}/download` | ✅ 是 | 否 | **低** | 正确使用 asset API |
| 历史任务 | `renderHistoryItem` | 复用 `audioPlayerHtml` | `/api/voice/assets/${assetId}/download` | ✅ 是 | 否 | **低** | 正确使用 asset API |

---

## 2. 下载失败可能原因排序

### 原因 1（已排除）：batch merged_audio.url 直接作为下载链接

**原问题（FIX4-A0 初步判断）：**
- 认为 `data.merged_audio.url` 是 MiniMax provider 返回的临时 URL
- 认为批量下载未走 asset API

**FIX4-B0 复查结论：**
- ✅ 后端已创建 `AudioAsset`，`merged_audio.url = /api/voice/assets/{id}/download`
- ✅ URL 格式与单条/异步下载完全一致
- ⚠️ 但前端下载按钮仍直接依赖 status 返回字段，耦合不够理想

**FIX4 修复（normalize batch download href）：**
- 批量下载按钮优先使用语义化 endpoint：`/api/voice/batch/{batch_id}/download`
- 播放 `audio.src` 保持使用 `data.merged_audio.url`，不影响播放链路
- fallback 链：`batch_id` → `merged_audio.id` → `merged_audio.url`
- 真实下载失败根因仍需 Network 证据确认；本次修复只做下载入口语义规范化

---

### 原因 2（中等风险）：流式 blob URL 刷新后失效

**代码位置：** `renderStreamResult()`，line 2813、2839：
```javascript
const blobUrl = URL.createObjectURL(blob);
window._streamBlobUrl = blobUrl;
// ...
<a href="${blobUrl}" download="stream_audio.mp3">下载音频（浏览器缓存）</a>
```

**问题：**
- blob URL 仅在当前会话有效，刷新页面后失效
- recent job / history 中恢复流式任务时，blob URL 已不存在
- 任务描述和 UX2 设计中已有"浏览器缓存，仅限当前会话"的提示，属于已知限制

**注意：** 流式结果如果包含 `audio_asset`，则有服务端下载选项（`/api/voice/assets/${assetId}/download`），这是正确做法。

---

### 原因 3（中等风险）：asset_id 字段提取不统一

**代码位置：** `extractAudioAssetId()`，line 1945：
```javascript
function extractAudioAssetId(data) {
    if (data?.audio_asset?.id) return data.audio_asset.id;
    if (data?.audio_asset_id) return data.audio_asset_id;
    if (data?.asset_id) return data.asset_id;
    return null;
}
```

**问题：**
- `audio_asset.id`、`audio_asset_id`、`asset_id` 三个字段名混用
- 如果 API 返回结构中字段名不匹配，`extractAudioAssetId` 返回 null
- recent job 恢复时 `audio_asset_id` 可能为空（取决于 saveRecentJob 时记录的字段）
- `buildRecentJobPayload` 记录的是 `extractAudioAssetId(data) || fallback.audio_asset_id || null`

---

### 原因 4（较低风险）：后端 download 接口响应头

**代码位置：** `app/api/voice_assets.py`，line 67-96：
```python
@router.get("/assets/{asset_id}/download")
async def download_asset(asset_id: str, session: Session = Depends(get_session)):
    # ...
    return FileResponse(
        path,
        media_type={"mp3": "audio/mpeg", ...}.get(audio.format, "application/octet-stream"),
        filename=f"{asset_id}.{audio.format}",
    )
```

**潜在问题：**
- `Content-Disposition` 头可能不完整，导致浏览器不知道下载文件名
- 部分浏览器对 `application/octet-stream` 的处理不一致
- 字幕下载时 `media_type` 为 `application/json` 或 `text/srt`，需确认 SRT 文件 Content-Type 是否正确

---

### 原因 5（较低风险）：字幕和音频下载路径不同

**代码位置：** `renderBatchResultPlayer()`，line 4436-4451：
```javascript
downloadSubtitle.href = `/api/voice/assets/${encodeURIComponent(subId)}/download`;
```

**观察：**
- 字幕下载使用 asset API ✅
- 音频下载使用 `merged_audio.url` 直接暴露 ❌
- 路径不一致，且音频下载缺乏统一错误处理

---

## 3. 建议修复方向

### 方向 A（推荐）：统一使用 asset API 下载批量音频

**前提：** 批量合并后的音频应存储为本服务 asset，返回 `asset_id` 而非暴露原始 URL。

**修改位置：** `renderBatchResultPlayer()`

**现状：**
```javascript
downloadAudio.href = data.merged_audio.url;  // 直接暴露 URL
audio.src = data.merged_audio.url;
```

**目标：**
- 如果 `data.merged_audio.asset_id` 存在：
  ```javascript
  downloadAudio.href = `/api/voice/assets/${data.merged_audio.asset_id}/download`;
  audio.src = `/api/voice/assets/${data.merged_audio.asset_id}/download`;
  ```
- 如果 `data.merged_audio.url` 是临时 URL 但没有 asset_id：
  - 前端上传 blob 到 asset service 获取 asset_id（复杂）
  - 或明确标注"该链接为临时链接，请尽快下载"

**优点：** 复用现有 asset download 基础设施，错误处理一致，长期有效。

---

### 方向 B（次选）：区分下载按钮文案，标注链接类型

**如果 `merged_audio.url` 是本服务生成的稳定 URL（如 OSS/COS URL）：**

**修改位置：** `renderBatchResultPlayer()`

```javascript
if (data.merged_audio.url.startsWith('/api/')) {
    // 已经是 asset API URL，原样使用
    downloadAudio.href = data.merged_audio.url;
} else if (data.merged_audio.asset_id) {
    // 有 asset_id，优先使用 asset API
    downloadAudio.href = `/api/voice/assets/${data.merged_audio.asset_id}/download`;
} else {
    // 临时 URL，标注风险
    downloadAudio.href = data.merged_audio.url;
    downloadAudio.download = ''; // 不强制 download 属性
}
```

---

### 方向 C：recent job / history 中的 blob URL 处理

**问题：** 流式任务恢复后，原 blob URL 已失效，但 UI 仍尝试显示/下载。

**修改位置：** `renderRecoveredJob()` 或 `restoreRecentJob()`

**建议：** 恢复任务时检查 `audio_asset.id` 是否存在：
- 如果有 → 使用 `audioPlayerHtml(assetId)` → asset API 下载
- 如果没有 → 显示"该任务为浏览器缓存，刷新后无法恢复，请重新生成"

---

## 4. FIX4 实际修复方案（normalize batch download href）

**修复时间：** 2026-05-15

**修复内容：**

`renderBatchResultPlayer()` 中 `downloadAudio.href` 赋值逻辑改为：
```javascript
let downloadHref = data.merged_audio.url;
if (data.batch_id) {
  downloadHref = `/api/voice/batch/${encodeURIComponent(data.batch_id)}/download`;
} else if (data.merged_audio.id) {
  downloadHref = `/api/voice/assets/${encodeURIComponent(data.merged_audio.id)}/download`;
}
downloadAudio.href = downloadHref;
downloadAudio.setAttribute('download', '');
```

**优先级：**
1. `batch_id` 存在时 → `/api/voice/batch/{batch_id}/download`（语义化 endpoint）
2. `merged_audio.id` 存在时 → `/api/voice/assets/{id}/download`（asset API）
3. 最后 fallback → `data.merged_audio.url`

**不变更：**
- `audio.src` 保持 `data.merged_audio.url`，不影响播放链路
- subtitle 下载逻辑不变
- batch status polling 不变

---

## 5. 审查结论

**FIX4-A0 初步结论（已纠偏）：**
- 原判断：批量下载高风险，`merged_audio.url` 是 provider 临时 URL
- 纠偏后：`merged_audio.url` 已是 asset API URL，格式正确

**FIX4 实际风险：**
- 下载入口耦合问题（直接依赖 status 返回字段）→ 已通过 normalize to batch endpoint 修复
- 真实下载失败根因仍需 Network 证据确认

**已确认低风险：**
- 单条/异步生成下载：正确使用 asset API ✅
- 字幕下载：正确使用 asset API ✅
- recent job 恢复：正确使用 asset API ✅
- 流式 blob URL：刷新后失效（已知限制，可接受）

**已排除的后端问题（FIX4-B0 确认）：**
- ✅ 批量音频已保存为 AudioAsset
- ✅ `merged_audio.id` 就是 asset_id
- ✅ `merged_audio.url` 格式正确
- ❓ 真实下载失败根因仍需 Network 证据


---

## P12-USAGE-FIX4-B0：后端批量 merged_audio asset_id 审查

**审查时间：** 2026-05-15

---

### 1. 后端相关文件列表

| 文件 | 相关函数 / endpoint | 作用 | 是否涉及 merged_audio | 是否涉及 asset 保存 |
|---|---|---|---|---|
| `app/api/batch.py` | `POST /batch/submit`<br>`GET /batch/{batch_id}/status`<br>`GET /batch/{batch_id}/download` | 批量任务提交<br>批量状态查询<br>批量合并音频下载 | ✅ status 返回 merged_audio<br>✅ download 用 merged_audio_asset_id | ✅ download 使用 asset_repo |
| `app/services/batch_orchestration_service.py` | `submit_longtext()`<br>`submit_script()`<br>`get_status()`<br>`_update_status()` | 提交长文本/剧本任务<br>查询状态<br>更新任务状态 | ✅ `get_status()` 返回 merged_audio dict<br>✅ `_update_status()` 创建 AudioAsset | ✅ 创建 AudioAsset 并保存 merged_audio_asset_id |
| `app/domain/schemas.py` | `BatchStatusResponse`<br>`BatchSegmentStatus` | 批量状态响应结构定义 | ✅ `merged_audio: dict \| None`<br>`merged_audio.id` = asset_id<br>`merged_audio.url` = 下载 URL | ❌ 仅定义结构 |
| `app/models/batch_job.py` | `BatchJob`<br>`BatchSegment` | 批量任务数据库模型 | ✅ `merged_audio_asset_id`<br>`merged_subtitle_asset_id` | ❌ 仅存储 ID |
| `app/services/audio_merge_service.py` | `AudioMerger.merge()` | 合并多个音频文件 | ❌ 只做音频合并 | ❌ 不保存 asset |
| `app/api/voice_assets.py` | `GET /assets/{asset_id}/download` | 通用资产下载接口 | ❌ 通用接口，被批量下载复用 | ❌ 通用下载 |

---

### 2. merged_audio 当前结构

**BatchStatusResponse 返回值（app/domain/schemas.py，line 411）：**
```python
merged_audio: dict | None = None  # {"id": "audio_xxx", "url": "/api/voice/assets/xxx/download"}
```

**实际填充逻辑（app/services/batch_orchestration_service.py，lines 638-645）：**
```python
if batch_job.merged_audio_asset_id:
    merged_audio = {
        "id": batch_job.merged_audio_asset_id,  # ← 这就是 asset_id！
        "url": f"/api/voice/assets/{batch_job.merged_audio_asset_id}/download",  # ← 已经是正确 URL
    }
    merged_asset = session.get(AudioAsset, batch_job.merged_audio_asset_id)
    if merged_asset:
        total_duration_ms = merged_asset.duration_ms
```

**结论：`merged_audio` 当前结构包含：**
- `id` = `merged_audio_asset_id`（这就是 asset_id）
- `url` = `/api/voice/assets/{merged_audio_asset_id}/download`（已经是正确下载 URL）
- **无** `asset_id` 字段名，但 `id` 就是 asset_id

---

### 3. 批量合并音频保存判断

**Q1：批量合并音频是否已经保存为 voice_asset？**

✅ 是。

在 `batch_orchestration_service.py` 的 `_update_status()` 中（lines 395-409）：
```python
merged_audio_asset = AudioAsset(
    id=merged_audio_id,
    job_id=batch_job_id,
    provider=provider,
    file_path=merged_audio_path,  # 本地文件路径
    file_url=f"/api/voice/assets/{merged_audio_id}/download",  # 下载 URL
    format=audio_format,
    duration_ms=...,
    created_at=now,
)
voice_asset_repo.create_audio_asset(session, merged_audio_asset)
batch_job.merged_audio_asset_id = merged_audio_id  # ← 保存到 BatchJob
```

**Q2：如果已保存，asset_id 在哪里？**

- `BatchJob.merged_audio_asset_id` = `merged_audio_id`（即 AudioAsset.id）
- `BatchStatusResponse.merged_audio.id` = `merged_audio_id`（即 AudioAsset.id）
- **这就是 asset_id！**

**Q3：当前 url 是什么来源？**

- `merged_audio.url` = `/api/voice/assets/{merged_audio_asset_id}/download`
- 这是后端生成的稳定 URL，指向 `/assets/{id}/download` 接口
- 与单条/异步生成的下载 URL 格式完全一致

**Q4：为什么会导致下载失败？**

根据代码审查，URL 格式是正确的。但下载可能失败的原因：
1. **合并失败但状态未正确更新**：`audio_merger.merge()` 抛出异常但 `batch_job.status` 可能未正确反映失败
2. **文件路径问题**：`merged_audio_path` 可能指向不存在的位置
3. **文件合并不完整**：部分 segment 成功后 merge 失败

**实际最可能原因：**
用户报告"部分音频下载失败"——如果是批量完成后下载失败，很可能是 merge 过程中有异常但任务状态没有正确反映为 failed，导致前端认为 merged_audio 已就绪但实际文件不存在。

---

### 4. FIX4 执行结果

**已实施修复（normalize batch download href）：**
- ✅ 前端 `renderBatchResultPlayer` `downloadAudio.href` 优先使用 `/api/voice/batch/{batch_id}/download`
- ✅ `audio.src` 保持 `data.merged_audio.url`，播放链路不变
- ✅ fallback 链：`batch_id` → `merged_audio.id` → `merged_audio.url`

**未涉及：**
- 后端 batch.py、BatchOrchestrationService、voice_assets.py 均未改
- batch payload 未改
- 播放链路未改

**真实下载失败根因：**
- ❓ 仍需 Network 证据确认
- 可能是 merge 异常导致文件不完整，或文件路径问题

---

### 5. 风险和范围

**已确认安全：**
- ✅ 批量音频已保存为 voice_asset
- ✅ merged_audio.url 格式正确
- ✅ merged_audio.id 就是 asset_id

**需进一步排查（如有用户报告）：**
- ❓ 合并过程中异常处理是否导致文件不完整但状态显示成功
- ❓ 文件路径 `merged_audio_path` 是否正确
- ❓ 真实使用中"部分下载失败"的具体 Network 错误信息

**不改范围（FIX4）：**
- 不改后端 API
- 不改生成链路
- 不改 batch payload
- 不改播放链路
- 不调用真实 MiniMax
