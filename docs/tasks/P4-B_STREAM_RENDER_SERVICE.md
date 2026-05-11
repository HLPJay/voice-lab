# P4-B 任务：StreamRenderService

## 目标

新建 `app/services/stream_render_service.py`，实现 WebSocket 流式语音生成的 Service 层。该 Service 负责验证请求、构建 RenderPlan、创建 VoiceJob、调用 adapter.render_stream() 获取音频流、拼接完整音频保存为 AudioAsset、更新 Job 状态。

## 前置条件

P4-A 已完成：
- `StreamAudioChunk` 模型在 `app/providers/base.py`
- `render_stream()` 方法在 MiniMax 和 Mock adapter 中已实现
- WebSocket 配置项在 `app/core/config.py`

## 需要修改的文件

| 文件 | 操作 |
|------|------|
| `app/services/stream_render_service.py` | **新建** |
| `app/domain/schemas.py` | 修改（新增 `StreamRenderRequest`） |
| `app/domain/enums.py` | 修改（新增 `JobType.stream_render`） |
| `tests/test_stream_render_service.py` | **新建** |

## 详细规范

### 1. `app/domain/enums.py` 修改

在 `JobType` 枚举中新增一个值：

```python
class JobType(str, Enum):
    sync_render = "sync_render"
    async_render = "async_render"
    stream_render = "stream_render"   # 新增
```

### 2. `app/domain/schemas.py` 新增

在文件末尾（`VoiceDeleteResponse` 之后）新增：

```python
class StreamRenderRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    profile_id: str = "deep_night_programmer"
    provider: str | None = None
    output_format: str = "mp3"
    need_subtitle: bool = False
```

字段说明：
- `text`: 要合成的文本，1-10000 字符
- `profile_id`: 声音人设 ID
- `provider`: 不传则用默认 provider
- `output_format`: 输出音频格式（mp3/pcm/flac/wav），传给 RenderPlan
- `need_subtitle`: 流式模式暂不支持字幕，默认 false

### 3. `app/services/stream_render_service.py` 新建

```python
import base64
import json
from typing import AsyncGenerator

from sqlmodel import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.errors import BindingNotFound, ProfileNotFound, ProviderError, VoiceLabError
from app.core.time import utc_now_iso
from app.domain.enums import JobStatus, JobType
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import StreamRenderRequest
from app.models.voice_job import VoiceJob
from app.providers.registry import get_provider
from app.repositories.voice_profile_repo import get_binding, get_profile
from app.services.asset_service import AssetService
from app.services.text_preprocess_service import TextPreprocessService
from app.utils.files import storage_path
from app.utils.id_generator import new_id

logger = get_logger("stream_render")
```

#### 类结构

```python
class StreamRenderService:
    def __init__(self):
        self.preprocessor = TextPreprocessService()
        self.asset_service = AssetService()

    async def render_stream(
        self, session: Session, request: StreamRenderRequest
    ) -> AsyncGenerator[dict, None]:
        """
        流式语音生成。yield dict 消息给调用方（WebSocket 端点）。

        消息类型：
        - {"event": "started", ...}
        - {"event": "audio_chunk", ...}  （多次）
        - {"event": "completed", ...}
        - {"event": "error", ...}
        """
```

#### 详细流程

**Step 1: 验证 + 构建 RenderPlan**

与 `VoiceRenderService.render_voice()` 的验证逻辑一致：
1. 获取 settings，确定 provider（`request.provider or settings.voice_provider`）
2. 检查 provider 存在（`get_provider(provider)`）
3. 查找 profile（`get_profile(session, request.profile_id)`），不存在抛 `ProfileNotFound`
4. 查找 binding（`get_binding(session, request.profile_id, provider)`），支持 mock fallback，不存在抛 `BindingNotFound`
5. 文本预处理（`self.preprocessor.preprocess(request.text)`）
6. 构建 voice_params 和 audio_params（与 sync render 相同逻辑）
7. 构建 `RenderPlan`（subtitle 设为 `SubtitlePlan(enabled=False)`，output_format 按请求传入）

**Step 2: 创建 VoiceJob**

```python
job = VoiceJob(
    id=new_id("job"),
    job_type=JobType.stream_render,
    status=JobStatus.running,       # 流式直接进 running
    provider=provider,
    model=plan.model,
    profile_id=profile.id,
    binding_id=binding.id,
    input_text=request.text,
    processed_text=processed_text,
    render_plan_json=plan.model_dump_json(),
    created_at=utc_now_iso(),
    updated_at=utc_now_iso(),
)
session.add(job)
session.commit()
```

**Step 3: yield started 消息**

```python
yield {
    "event": "started",
    "job_id": job.id,
    "provider": provider,
    "model": plan.model,
}
```

**Step 4: 调用 adapter.render_stream() 并 yield audio_chunk**

```python
adapter = get_provider(provider)
all_audio_data = bytearray()
chunk_count = 0
total_duration_ms = 0
total_characters = 0

async for chunk in adapter.render_stream(plan):
    all_audio_data.extend(chunk.audio_data)
    chunk_count += 1
    if chunk.duration_ms:
        total_duration_ms += chunk.duration_ms
    if chunk.usage_characters:
        total_characters = chunk.usage_characters  # 取最后一个（累计值）

    yield {
        "event": "audio_chunk",
        "chunk_index": chunk.chunk_index,
        "audio_base64": base64.b64encode(chunk.audio_data).decode(),
        "duration_ms": chunk.duration_ms,
        "is_final": chunk.is_final,
    }
```

**Step 5: 保存完整音频为 AudioAsset**

所有 chunk 收完后：

```python
# 拼接后的完整音频写文件
audio_id = new_id("audio")
fmt = request.output_format or "mp3"
audio_path = storage_path("audio", f"{audio_id}.{fmt}")
audio_path.write_bytes(bytes(all_audio_data))

# 创建 AudioAsset 记录
from app.models.voice_asset import AudioAsset
audio_asset = AudioAsset(
    id=audio_id,
    job_id=job.id,
    provider=provider,
    model=plan.model,
    file_path=str(audio_path),
    file_url=f"/api/voice/assets/{audio_id}/download",
    format=fmt,
    duration_ms=total_duration_ms or None,
    usage_characters=total_characters or None,
    created_at=utc_now_iso(),
)
from app.repositories import voice_asset_repo
voice_asset_repo.create_audio_asset(session, audio_asset)
```

**Step 6: 更新 VoiceJob 状态**

```python
job.status = JobStatus.success
job.updated_at = utc_now_iso()
session.add(job)
session.commit()
```

**Step 7: yield completed 消息**

```python
yield {
    "event": "completed",
    "job_id": job.id,
    "total_chunks": chunk_count,
    "total_duration_ms": total_duration_ms,
    "total_characters": total_characters,
    "audio_asset": {
        "id": audio_asset.id,
        "url": audio_asset.file_url,
    },
}
```

**错误处理**

用 try/except 包裹 Step 3-7：

```python
try:
    # ... yield started, audio_chunk, completed ...
except VoiceLabError as exc:
    job.status = JobStatus.failed
    job.error_message = exc.message
    job.updated_at = utc_now_iso()
    session.add(job)
    session.commit()
    logger.error("stream_render_failed job=%s error=%s", job.id, exc.message)
    yield {"event": "error", "code": exc.error_code or "PROVIDER_ERROR", "message": exc.message}
except Exception as exc:
    job.status = JobStatus.failed
    job.error_message = str(exc)[:500]
    job.updated_at = utc_now_iso()
    session.add(job)
    session.commit()
    logger.error("stream_render_failed job=%s error=%s", job.id, str(exc))
    yield {"event": "error", "code": "INTERNAL_ERROR", "message": str(exc)[:200]}
```

注意：验证阶段（Step 1-2）的异常不在 try 内，让它直接向上抛给 WebSocket 端点处理。只有流式生成阶段的异常需要转为 error 事件 yield 出去。

**日志**

- render_stream 开始时：`logger.info("stream_render_start job=%s profile=%s provider=%s text_length=%d", ...)`
- 每个 chunk 不需要日志（太多）
- 完成时：`logger.info("stream_render_success job=%s chunks=%d duration_ms=%d characters=%d", ...)`
- 失败时：`logger.error("stream_render_failed job=%s error=%s", ...)`

### 4. `tests/test_stream_render_service.py` 新建

测试使用 mock provider（它会 yield 3 个 StreamAudioChunk）。

```python
import pytest
from app.domain.schemas import StreamRenderRequest
from app.services.stream_render_service import StreamRenderService


@pytest.fixture
def service():
    return StreamRenderService()


@pytest.fixture
def stream_request():
    return StreamRenderRequest(
        text="流式测试文本",
        profile_id="deep_night_programmer",
        output_format="mp3",
    )
```

#### 测试用例（6 个）

**test_stream_yields_started_event**
- 调用 `service.render_stream(session, stream_request)`
- 收集所有 yield 的消息
- 第一条消息 event == "started"，包含 job_id、provider、model

**test_stream_yields_audio_chunks**
- 收集所有 yield 的消息
- 过滤 event == "audio_chunk" 的消息
- 数量 >= 1
- 每个 chunk 都有 chunk_index、audio_base64（非空字符串）、is_final
- base64 可以正确解码为 bytes

**test_stream_yields_completed_event**
- 最后一条消息 event == "completed"
- 包含 job_id、total_chunks > 0、audio_asset（含 id 和 url）

**test_stream_creates_job_and_asset**
- 调用完成后，查数据库
- VoiceJob 存在，job_type == "stream_render"，status == "success"
- AudioAsset 存在，file_path 文件实际存在且非空

**test_stream_invalid_profile_raises**
- `StreamRenderRequest(text="test", profile_id="nonexistent")`
- 调用 render_stream 应抛 ProfileNotFound
- 注意：因为是 AsyncGenerator，需要用 `async for` 或 `anext()` 触发执行

**test_stream_empty_text_rejected**
- `StreamRenderRequest(text="")` 应触发 Pydantic 校验错误（min_length=1）
- 这是 schema 级别的校验，用 `pytest.raises(ValidationError)` 测试

#### 测试辅助

所有测试使用现有的 `test_app` / `seed_profile` fixture（参考 `conftest.py` 中已有的 fixture）。如果 `conftest.py` 没有合适的 async 测试支持，可以用以下方式收集 async generator 结果：

```python
async def collect_events(gen):
    events = []
    async for event in gen:
        events.append(event)
    return events
```

在同步测试中通过 `asyncio.run()` 或 `pytest-asyncio` 调用。参考项目现有测试风格决定。

## 验收标准

1. `python -m pytest tests/ -x -q` 全部通过（含新增 6 个测试）
2. `StreamRenderService.render_stream()` 对 mock provider yield 出 started → audio_chunk(s) → completed 三种消息
3. 完成后数据库中有 VoiceJob（stream_render / success）和 AudioAsset
4. 错误时 yield error 事件并更新 job 状态为 failed
5. 不创建新的 API 端点（P4-C 负责）

## 不要做的事

- 不要修改 `app/providers/` 下的任何文件
- 不要创建 WebSocket 端点（P4-C 的任务）
- 不要修改 `app/api/` 下的任何文件
- 不要修改现有测试文件
