# P8-BE1 历史任务返回音频资产字段

## 1. 背景

P8-FIX4 已完成历史页前端交互修复，历史行操作位已包含播放/下载/复制ID/删除按钮。

但前端 `getHistoryAudioAssetId(job)` 始终返回 `null`，因为后端 `/api/voice/jobs` 返回的 `VoiceJobRead` 不包含音频资产字段，导致历史页播放/下载按钮始终置灰。

根因：`AudioAsset` 已通过 `job_id` 与 `VoiceJob` 关联，但 jobs API 未返回该字段。

---

## 2. 当前代码事实

### 2.1 AudioAsset 已有 job_id 关联

`app/models/voice_asset.py` 中 `AudioAsset` 已包含：
- `id` (primary key)
- `job_id` (indexed)
- `file_url`
- `duration_ms`
- `format`

`AssetService.save_assets()` 已设置 `AudioAsset.job_id`。

### 2.2 VoiceJobRead 当前缺少资产字段

`app/domain/schemas.py` 中 `VoiceJobRead` 只有基础任务字段，无 `audio_asset` / `subtitle_asset`。

### 2.3 jobs API 未查资产

`app/api/voice_jobs.py` 的 `GET /jobs` 和 `GET /jobs/{job_id}` 只从 `voice_jobs` 表读取，不查 `audio_assets`。

---

## 3. 方案判断

选择方案 B：通过 `AudioAsset.job_id` 反查音频资产。

不选择方案 A（给 VoiceJob 新增 audio_asset_id 字段）：因为需要数据库迁移、修改所有生成链路、引入历史数据回填问题。当前已有 `AudioAsset.job_id`，无需重复存储。

---

## 4. 修改内容

### 4.1 VoiceJobRead 新增资产字段

`app/domain/schemas.py` - `VoiceJobRead` 新增：

```python
audio_asset: AudioAssetResponse | None = None
subtitle_asset: SubtitleAssetResponse | None = None
```

`AudioAssetResponse` 和 `SubtitleAssetResponse` 已定义在 `VoiceJobRead` 之前，可直接引用。

### 4.2 voice_asset_repo 新增查询方法

`app/repositories/voice_asset_repo.py` 新增：

```python
def get_latest_audio_asset_for_job(session: Session, job_id: str) -> AudioAsset | None:
    statement = (
        select(AudioAsset)
        .where(AudioAsset.job_id == job_id)
        .order_by(AudioAsset.created_at.desc())
    )
    return session.exec(statement).first()

def get_latest_subtitle_asset_for_job(session: Session, job_id: str) -> SubtitleAsset | None:
    statement = (
        select(SubtitleAsset)
        .where(SubtitleAsset.job_id == job_id)
        .order_by(SubtitleAsset.created_at.desc())
    )
    return session.exec(statement).first()
```

### 4.3 voice_jobs API 使用 helper 返回带资产的 job

`app/api/voice_jobs.py` 新增 helper：

```python
def _audio_asset_response(asset) -> AudioAssetResponse | None:
    if not asset:
        return None
    return AudioAssetResponse(
        id=asset.id,
        url=asset.file_url,
        duration_ms=asset.duration_ms,
        format=asset.format,
    )

def _subtitle_asset_response(asset) -> SubtitleAssetResponse | None:
    if not asset:
        return None
    return SubtitleAssetResponse(
        id=asset.id,
        url=f"/api/voice/assets/{asset.id}/download",
        timeline=[],
    )

def _job_read_with_assets(session: Session, job) -> VoiceJobRead:
    audio_asset = voice_asset_repo.get_latest_audio_asset_for_job(session, job.id)
    subtitle_asset = voice_asset_repo.get_latest_subtitle_asset_for_job(session, job.id)
    return VoiceJobRead(
        ...,
        audio_asset=_audio_asset_response(audio_asset),
        subtitle_asset=_subtitle_asset_response(subtitle_asset),
        ...,
    )
```

`GET /jobs` 和 `GET /jobs/{job_id}` 改用 `_job_read_with_assets()` 返回。

### 4.4 新增测试

`tests/test_voice_jobs_assets.py` 包含 4 个测试：
- `test_list_jobs_returns_audio_asset` - 列表接口返回 audio_asset
- `test_get_job_returns_audio_asset` - 详情接口返回 audio_asset
- `test_job_without_audio_asset_returns_null_audio_asset` - 无资产时返回 null
- `test_list_jobs_returns_null_audio_asset_for_jobs_without_assets` - 列表中无资产业务返回 null

---

## 5. 返回结构说明

有资产的 job：

```json
{
  "job_id": "job_xxx",
  "job_type": "sync_render",
  "status": "success",
  "provider": "mock",
  "audio_asset": {
    "id": "audio_xxx",
    "url": "/api/voice/assets/audio_xxx/download",
    "duration_ms": 1234,
    "format": "mp3"
  },
  "subtitle_asset": {
    "id": "sub_xxx",
    "url": "/api/voice/assets/sub_xxx/download",
    "timeline": []
  }
}
```

无资产的 job：

```json
{
  "job_id": "job_yyy",
  "job_type": "sync_render",
  "status": "failed",
  "provider": "mock",
  "audio_asset": null,
  "subtitle_asset": null
}
```

---

## 6. 兼容性说明

- 旧字段不删除
- `/jobs` 外层结构不变（`jobs`, `total`, `limit`, `offset`）
- 查询参数不变（`job_type`, `status`, `profile_id`, `limit`, `offset`）
- 前端 `getHistoryAudioAssetId(job)` 可识别 `job.audio_asset.id`

---

## 7. API endpoint 不变说明

- 未新增 endpoint
- `/api/voice/jobs` - 只补充返回字段
- `/api/voice/jobs/{job_id}` - 只补充返回字段
- `/api/voice/assets/{asset_id}/download` - 未改

---

## 8. 未处理事项

- P8-BE2：历史任务删除接口
- P8-UX1：桌面宽屏布局
- P8-5：localStorage 最近任务恢复
- 批量任务（batch）历史资产展示

---

## 9. 验证命令

### 9.1 Schema 检查

```bash
python - <<'PY'
from pathlib import Path
text = Path("app/domain/schemas.py").read_text(encoding="utf-8")
required = ["class VoiceJobRead", "audio_asset: AudioAssetResponse | None = None",
    "subtitle_asset: SubtitleAssetResponse | None = None"]
missing = [x for x in required if x not in text]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 9.2 Repo 检查

```bash
python - <<'PY'
from pathlib import Path
text = Path("app/repositories/voice_asset_repo.py").read_text(encoding="utf-8")
required = ["select", "def get_latest_audio_asset_for_job",
    "AudioAsset.job_id == job_id", "order_by(AudioAsset.created_at.desc())"]
missing = [x for x in required if x not in text]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 9.3 Jobs API 检查

```bash
python - <<'PY'
from pathlib import Path
text = Path("app/api/voice_jobs.py").read_text(encoding="utf-8")
required = ["voice_asset_repo", "_job_read_with_assets", "audio_asset=_audio_asset_response"]
missing = [x for x in required if x not in text]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

---

## 10. 验证结果

- pytest: **379 passed, 6 skipped** (新增 4 个测试)
- 静态检查：全部通过

---

## 11. 阶段结论

**P8-BE1 已完成。** 历史任务接口现在会通过 `AudioAsset.job_id` 返回对应音频资产字段，前端历史页在存在音频资产时可以启用播放/下载按钮。未新增数据库字段，未修改资产保存链路。

---

## 12. 不执行真实 MiniMax smoke test

本阶段只补充历史任务接口返回字段，并使用 mock provider 测试，不涉及真实 MiniMax 调用，不消耗额度。
