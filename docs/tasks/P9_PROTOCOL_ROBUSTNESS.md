# P9: 协议合规 + 健壮性修复

## 背景

对照 MiniMax 官方 WebSocket / HTTP 协议文档审计，发现 WebSocket 时序、参数语义、Provider 解析、任务一致性等多处问题。本轮集中修复，不加新功能。

## 修改范围

后端 Python 文件，涉及 providers / services / api / domain / core 层。前端无改动。

---

## Round A：P0 协议与参数修复（必修）

### A1. WebSocket task_started 严格校验

**文件**：`app/providers/minimax_speech_adapter.py`，`render_stream()` 方法（约第 719-727 行）

**当前问题**：发送 `task_start` 后只检查 `task_failed`，没有验证返回的 `event == "task_started"`，不符合 MiniMax 官方协议。

**修改**：

```python
# 发送 task_start 后
msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=recv_timeout))
if msg.get("event") == "task_failed":
    error_info = msg.get("data", {})
    raise ProviderError(
        "WebSocket task_start failed",
        error_info.get("message", str(msg)),
    )
if msg.get("event") != "task_started":
    raise ProviderError(
        "WebSocket protocol error: expected task_started",
        f"got event={msg.get('event')}, msg={str(msg)[:200]}",
    )
# 只有确认 task_started 后才发送 task_continue
await ws.send(_json.dumps({"event": "task_continue", "text": plan.processed_text}))
```

### A2. WebSocket 端点传递 speed/vol/pitch/emotion

**文件**：`app/api/ws_render.py`，约第 60-66 行

**当前问题**：构造 `StreamRenderRequest` 时只传了 `text, profile_id, provider, output_format, need_subtitle`，前端发送的 `speed/vol/pitch/emotion` 被丢弃。

**修改**：

```python
request = StreamRenderRequest(
    text=text,
    profile_id=start_msg.get("profile_id", "deep_night_programmer"),
    provider=start_msg.get("provider"),
    output_format=start_msg.get("output_format", "mp3"),
    need_subtitle=start_msg.get("need_subtitle", False),
    speed=start_msg.get("speed"),
    vol=start_msg.get("vol"),
    pitch=start_msg.get("pitch"),
    emotion=start_msg.get("emotion"),
)
```

### A3. 拆分 output_format 和 audio_format

**文件**：`app/domain/schemas.py`

**当前问题**：`VoiceRenderRequest.output_format` 和 `StreamRenderRequest.output_format` 是自由字符串，混合了「API 返回格式」和「音频编码格式」两种语义。`voice_render_service.py` 用 `"mp3" → "hex"` 做隐式转换。

**修改 schemas.py**：

```python
from typing import Literal

class VoiceRenderRequest(BaseModel):
    ...
    output_format: Literal["hex", "url"] = "hex"        # MiniMax API 返回格式
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"  # 音频编码格式
    ...

class StreamRenderRequest(BaseModel):
    ...
    audio_format: Literal["mp3"] = "mp3"  # 流式固定 mp3
    ...
    # 删除 output_format 字段（流式只有 hex 返回）
```

**修改 voice_render_service.py**：
- 删除 `output_format="hex" if request.output_format == "mp3" else request.output_format` 转换逻辑
- 直接使用 `request.output_format`（现在已经是 Literal["hex","url"]）
- `audio_format` 传入 `RenderPlan.audio_params` 的 `format` 字段

**修改 stream_render_service.py**：
- 删除同样的转换逻辑
- 流式固定使用 `output_format="hex"`

**修改前端** `app/static/index.html`：
- 将 T2A 表单中的 output_format 下拉改为只有 `hex` / `url` 两个选项
- 新增 audio_format 下拉（`mp3` / `wav` / `flac`），默认 `mp3`
- 调整表单提交逻辑，发送两个字段

### A4. 使用 resolve_binding 返回的 resolved_provider

**文件**：
- `app/services/voice_render_service.py`（约第 40 行）
- `app/services/stream_render_service.py`（约第 48 行）
- `app/services/async_render_service.py`（约第 45 行）
- `app/services/batch_orchestration_service.py`（约第 402 行）

**当前问题**：4 个 service 都调用 `resolve_binding()` 获取 `(binding, resolved_provider)` 但随后忽略 `resolved_provider`，继续用原始 `provider` 调用 `get_provider()`，导致 fallback 场景下 binding 和 adapter 不匹配。

**修改模式**（每个文件统一）：

```python
binding, resolved_provider = resolve_binding(session, request.profile_id, provider)
provider = resolved_provider  # 使用解析后的 provider
adapter = get_provider(provider)
```

确保后续 `RenderPlan.provider`、`VoiceJob.provider`、`Asset.provider` 都记录 `resolved_provider`。

### A5. 克隆上传增加音频类型和时长校验

**文件**：`app/api/voice_clone.py` 上传端点 + `app/services/voice_clone_service.py`

**当前问题**：只检查文件大小，不检查 MIME 类型、文件扩展名、音频时长。

**修改**：

在 `voice_clone_service.py` 的 `upload_audio()` 方法中增加校验：

```python
import mimetypes
from app.utils.audio import probe_audio_duration  # 需新增或复用

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
ALLOWED_MIMES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/aac", "audio/flac"}

def _validate_audio_upload(self, filename: str, file_data: bytes, purpose: str):
    # 1. 扩展名检查
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise VoiceLabError("不支持的音频格式", f"支持: {', '.join(ALLOWED_EXTENSIONS)}, 收到: {ext}")

    # 2. MIME 检查
    mime, _ = mimetypes.guess_type(filename)
    if mime and mime not in ALLOWED_MIMES:
        raise VoiceLabError("不支持的音频 MIME 类型", f"收到: {mime}")

    # 3. 时长检查（可选，需 ffprobe 或 pydub）
    # 如果环境中有 pydub/ffprobe 可用则启用，否则跳过
    # duration_sec = probe_audio_duration(file_data)
    # if purpose == "voice_clone" and (duration_sec < 10 or duration_sec > 300):
    #     raise VoiceLabError("音频时长不符合要求", f"voice_clone 需要 10-300 秒，当前 {duration_sec:.1f} 秒")
```

注意：时长校验依赖 ffprobe / pydub，如果当前环境没有安装则先只做扩展名 + MIME 校验，时长校验标记为 TODO。

---

## Round B：P1 健壮性修复

### B1. 异步任务先落库再调 Provider

**文件**：`app/services/async_render_service.py`，`submit_task()` 方法

**当前问题**：先调 `adapter.create_async_task(plan)` 远程创建任务，再创建本地 `VoiceJob`。如果远程成功但本地落库失败，产生孤儿任务。

**修改顺序**：

```python
# 1. 先创建本地 job（status=pending）
job = VoiceJob(
    id=new_id("voice_job"),
    profile_id=request.profile_id,
    provider=provider,
    status="pending",
    ...
)
session.add(job)
session.commit()

# 2. 再调 Provider
try:
    task_result = await adapter.create_async_task(plan)
    job.provider_task_id = task_result.provider_task_id
    job.status = "processing"
    job.trace_id = task_result.trace_id
    session.commit()
except Exception as exc:
    job.status = "failed"
    job.error_message = str(exc)[:500]
    session.commit()
    raise
```

### B2. TextSegmentService._split_by_comma 使用 max_chars

**文件**：`app/services/text_segment_service.py`，约第 43-52 行

**当前问题**：`_split_by_comma()` 方法签名有 `max_chars` 参数但内部硬编码 `2000`。

**修改**：

```python
def _split_by_comma(self, text: str, max_chars: int) -> list[str]:
    ...
    if len(current) + len(part) > max_chars and current:  # 原为 2000
        ...
```

确保所有调用处传入 `max_chars` 参数。

### B3. VoiceDesignRequest.voice_id 增加正则校验

**文件**：`app/domain/schemas.py`，`VoiceDesignRequest` 类（约第 231 行）

**当前问题**：`voice_id: str | None = None` 无约束，但会拼入文件路径 `storage_path("audio", f"{voice_id}_trial.mp3")`。

**修改**：

```python
class VoiceDesignRequest(BaseModel):
    ...
    voice_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=256,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$",
    )
    ...
```

与 `VoiceCloneRequest.voice_id` 的约束保持一致。

### B4. 共享 httpx client 在应用关闭时释放

**文件**：
- `app/providers/minimax_speech_adapter.py`：新增关闭函数
- `app/main.py`：在 lifespan 中调用

**修改 minimax_speech_adapter.py**：

```python
async def close_shared_http_client():
    global _shared_http_client
    if _shared_http_client is not None:
        await _shared_http_client.aclose()
        _shared_http_client = None
```

**修改 app/main.py lifespan**：

```python
from app.providers.minimax_speech_adapter import close_shared_http_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_shared_http_client()
```

### B5. README 测试数更新

**文件**：`README.md`

将测试通过数从 `116 passed, 6 skipped` 更新为当前实际值（执行 `python -m pytest tests/ -x -q` 获取最新数据）。

---

## 不在本轮范围内（记录但不修改）

| 编号 | 内容 | 原因 |
|------|------|------|
| #2 | Base URL 区域核对 | 非代码问题，用户需在 MiniMax 控制台确认 |
| #7 | 批量任务可恢复/持久化队列 | 超出 MVP 范围，需引入 Celery/Arq，归入后续 P-future |

---

## 测试要求

### 新增测试

1. **A1 测试**：mock WebSocket 返回 `event != "task_started"` 时应抛出 ProviderError
2. **A3 测试**：验证 `VoiceRenderRequest(output_format="wav")` 被 pydantic 拒绝（Literal 校验）
3. **A4 测试**：mock fallback 场景，验证 resolved_provider 被传给 get_provider
4. **A5 测试**：上传 `.txt` 文件应被拒绝，上传 `.mp3` 应通过
5. **B1 测试**：mock adapter.create_async_task 抛异常，验证本地 job 状态为 failed
6. **B2 测试**：`_split_by_comma("a,b,c,...", max_chars=10)` 不应产生超过 10 字符的段
7. **B3 测试**：`VoiceDesignRequest(voice_id="../etc/passwd")` 应被 pydantic 拒绝

### 已有测试不可回归

```bash
python -m pytest tests/ -x -q
# 期望：所有已有测试继续通过
```

## 验证清单

- [ ] A1: WebSocket task_started 不是 task_started 时抛错
- [ ] A2: 前端通过 WS 发送 speed=0.8 → 服务端 StreamRenderRequest.speed=0.8
- [ ] A3: `output_format="mp3"` 被 pydantic Literal 拒绝
- [ ] A4: fallback 场景 binding 来自 minimax 但 adapter 也用 minimax（不再不匹配）
- [ ] A5: 上传 .txt 文件 → 400 错误提示不支持的格式
- [ ] B1: 远程任务失败 → 本地 job 记录 status=failed
- [ ] B2: max_chars=500 时逗号切分不超过 500
- [ ] B3: voice_id 含路径字符 → 422 校验失败
- [ ] B4: 应用关闭时 httpx client 正常释放
- [ ] B5: README 测试数已更新
