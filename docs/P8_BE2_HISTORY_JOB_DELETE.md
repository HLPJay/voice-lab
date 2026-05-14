# P8-BE2 历史任务删除接口

## 1. 背景

P8-FIX4 已提供历史删除操作位，但按钮 disabled（调用 `showHistoryDeleteUnsupported()` 提示后端未支持）。P8-BE1 已补充历史任务音频资产字段。本阶段补充后端删除接口。

---

## 2. 当前代码事实

### 2.1 VoiceJob 当前字段

`app/models/voice_job.py` 中 `VoiceJob` 包含 `id`, `job_type`, `status`, `provider`, `model` 等基础字段，无 `deleted_at` / `is_deleted` 字段。

### 2.2 当前数据库创建方式

项目使用 `SQLModel.metadata.create_all(engine)` 创建表，无 Alembic 迁移体系。

### 2.3 当前 voice_job_repo

已有 `get_job`, `create_job`, `update_job`, `list_jobs`，无 `delete_job` / `soft_delete_job`。

### 2.4 当前 jobs API

已有 `GET /jobs` 和 `GET /jobs/{job_id}`，无 `DELETE /jobs/{job_id}`。

---

## 3. 方案判断

本阶段选择 `status="deleted"` 状态软删除。

不选择给 `VoiceJob` 新增 `deleted_at` / `is_deleted` 字段：
- 当前无迁移体系
- `create_all` 不会自动给已有表新增列
- 本地已有 SQLite 表结构不会自动升级

不物理删除：
- 不删除 `VoiceJob` 数据库行
- 不删除 `AudioAsset` / `SubtitleAsset` 行
- 不删除音频文件
- 真实资产清理进入 P8-BE3

---

## 4. 修改内容

### 4.1 VoiceJobDeleteResponse

`app/domain/schemas.py` 新增：

```python
class VoiceJobDeleteResponse(BaseModel):
    job_id: str
    deleted: bool = True
    status: str = "deleted"
    message: str = "历史任务已删除"
```

### 4.2 voice_job_repo 新增 soft_delete_job

`app/repositories/voice_job_repo.py` 新增：

```python
def soft_delete_job(session: Session, job: VoiceJob) -> VoiceJob:
    job.status = "deleted"
    job.updated_at = utc_now_iso()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
```

`list_jobs()` 修改：默认排除 `status != "deleted"` 的任务（除非显式传 `status` 参数）。

### 4.3 DELETE /api/voice/jobs/{job_id}

`app/api/voice_jobs.py` 新增：

```python
@router.delete("/jobs/{job_id}", response_model=VoiceJobDeleteResponse)
async def delete_job(job_id: str, session: Session = Depends(get_session)):
    job = voice_job_repo.get_job(session, job_id)
    if not job:
        raise JobNotFound("Voice job not found", job_id=job_id)
    if job.status == "deleted":
        return VoiceJobDeleteResponse(job_id=job.id, deleted=True, status="deleted", message="历史任务已删除")
    job = voice_job_repo.soft_delete_job(session, job)
    return VoiceJobDeleteResponse(job_id=job.id, deleted=True, status=job.status, message="历史任务已删除")
```

### 4.4 GET /jobs/{job_id} 对 deleted 返回 404

`get_job` 改为：

```python
if not job or job.status == "deleted":
    raise JobNotFound("Voice job not found", job_id=job_id)
```

---

## 5. 删除语义说明

- DELETE 是软删除，将 `VoiceJob.status` 改为 `"deleted"`
- 重复 DELETE 幂等，返回成功
- 不存在任务返回 404
- 默认历史列表不再返回 `deleted` 任务
- 显式 `status=deleted` 可用于调试查询
- 不影响资产下载接口
- 前端删除按钮仍 disabled（留给 P8-FE5 接入）

---

## 6. API endpoint 说明

### 新增

```
DELETE /api/voice/jobs/{job_id}
```

**返回 200：**

```json
{
  "job_id": "job_xxx",
  "deleted": true,
  "status": "deleted",
  "message": "历史任务已删除"
}
```

**返回 404（job 不存在）：**

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Voice job not found"
  }
}
```

### GET /api/voice/jobs

行为变化：
- 默认（无 status 参数）不返回 `status=deleted` 的任务
- `?status=deleted` 可列出已删除任务

---

## 7. 兼容性说明

- GET `/jobs` 外层结构不变
- GET `/jobs` 默认不返回 deleted
- GET `/jobs?status=deleted` 可查 deleted
- GET `/jobs/{job_id}` 对 deleted 返回 404
- 未改资产接口
- 前端按钮仍 disabled（将在 P8-FE5 接入）

---

## 8. 未处理事项

- P8-FE5：前端删除按钮接入后端 DELETE
- P8-BE3：历史任务与资产物理清理
- P8-UX1：桌面宽屏布局
- P8-5：localStorage 最近任务恢复

---

## 9. 验证命令

### 9.1 不改模型检查

```bash
python - <<'PY'
from pathlib import Path
text = Path("app/models/voice_job.py").read_text(encoding="utf-8")
forbidden = ["deleted_at", "is_deleted", "audio_asset_id", "subtitle_asset_id"]
found = [x for x in forbidden if x in text]
if found: raise SystemExit(f"FAIL: {found}")
print("PASS")
PY
```

### 9.2 Schema 检查

```bash
python - <<'PY'
from pathlib import Path
text = Path("app/domain/schemas.py").read_text(encoding="utf-8")
required = ["class VoiceJobDeleteResponse", "deleted: bool = True", 'status: str = "deleted"']
missing = [x for x in required if x not in text]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 9.3 Repo 检查

```bash
python - <<'PY'
from pathlib import Path
text = Path("app/repositories/voice_job_repo.py").read_text(encoding="utf-8")
required = ["def soft_delete_job", 'job.status = "deleted"', "utc_now_iso", 'VoiceJob.status != "deleted"']
missing = [x for x in required if x not in text]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 9.4 API 检查

```bash
python - <<'PY'
from pathlib import Path
text = Path("app/api/voice_jobs.py").read_text(encoding="utf-8")
required = ['@router.delete("/jobs/{job_id}"', "VoiceJobDeleteResponse", "voice_job_repo.soft_delete_job", 'job.status == "deleted"']
missing = [x for x in required if x not in text]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 9.5 禁止物理删除检查

```bash
python - <<'PY'
from pathlib import Path
targets = [Path("app/api/voice_jobs.py"), Path("app/repositories/voice_job_repo.py")]
content = "\n".join(p.read_text(encoding="utf-8") for p in targets)
forbidden = ["session.delete", ".unlink(", "os.remove", "Path.unlink", "delete_audio_asset", "delete_subtitle_asset"]
found = [x for x in forbidden if x in content]
if found: raise SystemExit(f"FAIL: {found}")
print("PASS")
PY
```

---

## 10. 验证结果

- pytest: **384 passed, 6 skipped** (新增 5 个测试)
- 静态检查：全部通过

---

## 11. 阶段结论

**P8-BE2 已完成。** 后端已新增历史任务删除接口，采用 `status="deleted"` 状态软删除，不新增数据库字段，不删除音频资产和文件。默认历史列表会排除 `deleted` 任务，重复删除保持幂等。前端删除按钮仍 disabled，将在 P8-FE5 阶段接入。

---

## 12. 不执行真实 MiniMax smoke test

本阶段只新增历史任务删除接口，使用已有 mock 测试，不涉及真实 MiniMax 调用，不消耗额度。
