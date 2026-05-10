# Completeness Review

检查时间：2026-05-11

本文档记录当前 Voice Lab P0 的完整性检查结果、已发现遗漏和下一步修复优先级。

## 当前总体判断

项目已经具备 P0 的主要目录和代码骨架：

- `app/main.py` 已存在。
- `app/api/` 已存在。
- `app/models/` 已存在。
- `app/services/` 已存在。
- `app/providers/` 已存在。
- `tests/` 已存在。
- 设计文档已覆盖目标、架构、目录、实现计划和安全控制。

但当前还不能判定为 P0 完成交付，因为 pytest 尚未通过。

## 已执行检查

执行命令：

```bash
pytest -q
```

结果摘要：

```text
4 failed, 7 passed, 3 errors
```

## 阻断问题

### 1. Python 版本与 `StrEnum` 不兼容

失败位置：

```text
app/domain/enums.py
```

错误：

```text
ImportError: cannot import name 'StrEnum' from 'enum'
```

原因：

当前运行环境是 Python 3.10，而 `enum.StrEnum` 是 Python 3.11+ 才可用。

修复策略二选一：

1. 保持 README 的 Python 3.11+ 要求，并在当前环境升级 Python。
2. 为了兼容 Python 3.10，把枚举改成：

```python
from enum import Enum


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
```

推荐：

P0 阶段优先兼容当前环境，使用 `str, Enum`，这样其他模块更容易跑通。

### 2. Windows 下临时 SQLite 文件未释放

失败位置：

```text
tests/conftest.py
```

错误：

```text
PermissionError: [WinError 32] another process is using this file
```

原因：

测试 teardown 时 `os.unlink(path)` 删除临时 SQLite 文件，但 SQLAlchemy engine 可能仍持有连接。

修复策略：

在删除文件前调用：

```python
engine.dispose()
```

并在 `os.unlink(path)` 前确认所有 session 已关闭。

## 结构检查结果

### 已具备

- `app/main.py`
- `app/api/__init__.py`
- `app/api/health.py`
- `app/api/voice_profiles.py`
- `app/api/voice_render.py`
- `app/api/voice_variants.py`
- `app/api/voice_jobs.py`
- `app/api/voice_assets.py`
- `tests/conftest.py`
- `tests/test_health.py`
- `tests/test_render_plan.py`
- `tests/test_mock_adapter.py`
- `tests/test_api_render.py`
- `tests/test_text_preprocess.py`

### 仍建议补齐或复核

- `app/core/logging.py` 尚未看到，P0 可暂缓，但后续应补统一日志。
- `app/repositories/voice_job_repo.py` 尚未看到，P0 可暂缓，但如果 service 复杂度上升应补。
- `app/repositories/voice_asset_repo.py` 尚未看到，P0 可暂缓。
- `app/repositories/voice_variant_repo.py` 尚未看到，P0 可暂缓。
- `app/services/job_service.py` 尚未看到，P0 可暂缓。
- `storage/` 目录可能由程序启动时自动创建，不要求提前提交。

## 安全检查结果

搜索项：

- `Authorization`
- `voice_setting`
- `audio_setting`
- `provider_voice_id`
- `Redis`
- `Celery`
- `Voice Clone`
- `Voice Design`

结论：

- `Authorization` 只在 MiniMax Adapter 请求头构造和文档约束中出现，未发现日志输出。
- `voice_setting` / `audio_setting` 出现在 MiniMax Adapter 和文档中，未发现 API 层直接构造。
- `Redis` / `Celery` / `Voice Clone` / `Voice Design` 只作为禁止项或后续计划出现在文档中，未发现 P0 代码实现范围外功能。

## 下一步优先级

### P0 修复优先级 1

修复测试阻断：

1. 将 `StrEnum` 改为兼容 Python 3.10 的 `str, Enum`。
2. 在测试临时 SQLite teardown 前释放 engine。
3. 重新运行 `pytest -q`。

### P0 修复优先级 2

验证 Mock render 闭环：

1. `POST /api/voice/render` 使用 `provider=mock`。
2. 确认返回 `status=success`。
3. 确认 `storage/audio/YYYY-MM-DD/` 生成文件。
4. 确认数据库写入 job 和 audio asset。

### P0 修复优先级 3

验证资产下载：

1. 查询 asset。
2. 下载 asset。
3. 文件不存在返回 `ASSET_NOT_FOUND`。
4. 不允许用户通过路径参数下载任意文件。

## 是否可以进入下一阶段

暂不建议进入 P1。

进入 P1 的最低前提：

- `pytest -q` 通过。
- Mock render 真实跑通。
- Asset download 真实跑通。
- MiniMax Key 缺失时错误明确。

