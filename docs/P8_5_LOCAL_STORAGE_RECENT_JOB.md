# P8-5 localStorage 最近任务恢复

## 1. 背景

页面刷新后 resultsArea 会丢失当前任务展示。历史页虽然可查，但用户需要手动切换和查找。本阶段通过 localStorage 保存轻量最近任务摘要。

## 2. 安全边界

- 不保存 API Key
- 不保存 Token
- 不保存请求头
- 不保存完整输入文本
- 不保存完整剧本
- 不保存音频 blob/base64/hex
- 只保存 job_id 和轻量摘要

## 3. 数据结构

localStorage key：

```
voice_lab_recent_job_v1
```

字段：

```
version: 1
saved_at: ISO 时间戳
job_id: 后端任务 ID
job_type: single | async | stream | variants
status: 任务状态
provider: 供应商
model: 模型
text_preview: 最多 80 字预览文本
audio_asset_id: 可选，音频资产 ID
```

## 4. 修复内容

- 新增 `saveRecentJob(data, fallback)` — 生成成功后保存最近任务摘要
- 新增 `loadRecentJob()` — 读取本地缓存，损坏时自动清除
- 新增 `clearRecentJob()` — 清除本地缓存
- 新增 `renderRecentJobRestore()` — 渲染恢复入口卡片
- 新增 `restoreRecentJob()` — 调用 GET /api/voice/jobs/{job_id} 拉取最新详情
- 新增 `renderRecoveredJob(job)` — 展示恢复的任务结果
- 新增 `recentJobRestore` DOM 容器在 resultsArea 前
- 同步生成成功、异步提交成功、异步轮询成功、流式完成时均调用 saveRecentJob
- 页面初始化时调用 renderRecentJobRestore()

## 5. 恢复逻辑说明

- 页面加载时只显示恢复入口卡片，不自动请求后端
- 用户点击"恢复"后调用 GET /api/voice/jobs/{job_id}
- 显示服务端最新状态
- 失败时显示错误卡片
- 清除按钮只清本地缓存，不请求后端

## 6. API endpoint 不变说明

- 未新增后端接口
- 使用已有 GET /api/voice/jobs/{job_id}
- 未改生成接口
- 未改历史接口
- 未改下载接口

## 7. 未处理事项

- 未做离线音频缓存
- 未做多任务恢复列表
- 未做 P8-BE3（历史任务与资产物理清理）
- 未拆分 index.html

## 8. 验证命令

### 8.1 localStorage helper 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for marker in ["RECENT_JOB_STORAGE_KEY", "voice_lab_recent_job_v1",
    "function saveRecentJob", "function loadRecentJob", "function clearRecentJob",
    "function restoreRecentJob", "function renderRecentJobRestore"]:
    assert marker in html, f"Missing {marker}"
print("PASS")
PY
```

### 8.2 敏感字段检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function buildRecentJobPayload")
end = html.find("function saveRecentJob", start)
block = html[start:end]
forbidden = ["audio_hex", "audio_base64", "blob", "Authorization", "api_key", "token", "headers", "response_json"]
found = [x for x in forbidden if x in block]
if found: raise SystemExit(f"Forbidden fields: {found}")
print("PASS")
PY
```

### 8.3 恢复接口检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for marker in ["function restoreRecentJob", "/api/voice/jobs/", "renderRecoveredJob"]:
    assert marker in html, f"Missing {marker}"
print("PASS")
PY
```

### 8.4 UI 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for marker in ['id="recentJobRestore"', "最近任务", "恢复", "清除"]:
    assert marker in html, f"Missing {marker}"
print("PASS")
PY
```

## 9. 验证结果

- localStorage helper 检查: PASS
- 敏感字段检查: PASS
- 恢复接口检查: PASS
- UI 检查: PASS
- pytest: 384 passed, 6 skipped

## 10. 阶段结论

**P8-5 已完成。** 前端已支持通过 localStorage 保存最近任务轻量摘要，刷新页面后可显示恢复入口；用户点击恢复时会通过 GET /api/voice/jobs/{job_id} 拉取服务端最新任务详情。未保存音频内容、完整文本或敏感信息，未改后端 API。