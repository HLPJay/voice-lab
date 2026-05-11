# P4 规范：T2A WebSocket 流式语音生成

## 目标

实现 MiniMax WebSocket 流式 T2A，让客户端在语音生成过程中实时接收音频片段，而非等待整个音频生成完毕。适用于实时对话、直播、交互式有声内容等场景。

## MiniMax WebSocket 协议总结

### 连接

```
WSS: wss://api.minimaxi.com/ws/v1/t2a_v2
认证: Bearer token（通过连接参数或 header 传递）
超时: 120 秒无消息自动断开
```

### 消息流（三阶段）

```
Client                          MiniMax
  |                                |
  |-------- [WebSocket连接] ------>|
  |<--- connected_success --------|
  |                                |
  |-------- task_start ----------->|  (model, voice_setting, audio_setting)
  |<--- task_started --------------|
  |                                |
  |-------- task_continue -------->|  (text, 可多次发送)
  |<--- task_continued [chunk1] ---|  (hex音频 + extra_info)
  |<--- task_continued [chunk2] ---|
  |<--- task_continued [chunkN] ---|  (is_final=true)
  |                                |
  |-------- task_finish ---------->|
  |<--- task_finished -------------|
  |                                |
```

### 音频格式
- 音频片段以 **hex 编码**返回
- 支持 mp3/pcm/flac/wav/opus
- 每个 chunk 包含 `extra_info`（audio_length, audio_size, usage_characters）

### 关键参数
- `model`: speech-2.8-hd / speech-2.8-turbo（turbo 更快）
- `text`: 单次 < 10000 字符
- `is_final`: true 时表示当次 text 的音频全部发完

---

## 架构设计

### 方案选择：Voice Lab WebSocket 端点

Voice Lab 对外提供 WebSocket 端点，内部连接 MiniMax WebSocket：

```
Client (Browser/App)
    |
    | WebSocket
    |
Voice Lab Server (/api/voice/ws/render)
    |
    | WebSocket (MiniMax WSS)
    |
MiniMax API (wss://api.minimaxi.com/ws/v1/t2a_v2)
```

**为什么不让客户端直连 MiniMax？**
1. API Key 隔离（不暴露给前端）
2. 统一 RenderPlan 协议（Voice Lab 语义，不暴露 MiniMax 字段）
3. 审计日志和用量统计
4. 未来切换 Provider 对客户端透明

### Voice Lab WebSocket 协议

**客户端 → Voice Lab**：

```json
// 1. 开始（必须第一条消息）
{
  "event": "start",
  "text": "要合成的文本内容",
  "provider": "minimax",
  "profile_id": "deep_night_programmer",
  "output_format": "mp3",
  "need_subtitle": false
}

// 2. 追加文本（可选，用于分段推送）
{
  "event": "continue",
  "text": "追加的文本片段"
}

// 3. 结束（通知服务端文本发送完毕）
{
  "event": "finish"
}
```

**Voice Lab → 客户端**：

```json
// 连接确认
{"event": "connected", "request_id": "req_xxx"}

// 任务开始
{"event": "started", "job_id": "job_xxx", "provider": "minimax", "model": "speech-2.8-turbo"}

// 音频片段（核心消息，多次推送）
{
  "event": "audio_chunk",
  "chunk_index": 0,
  "audio_base64": "SGVsbG8gV29ybGQ=",
  "duration_ms": 500,
  "is_final": false
}

// 生成完成
{
  "event": "completed",
  "job_id": "job_xxx",
  "total_chunks": 15,
  "total_duration_ms": 7500,
  "total_characters": 200,
  "audio_asset": {
    "id": "audio_xxx",
    "url": "/api/voice/assets/audio_xxx/download"
  }
}

// 错误
{
  "event": "error",
  "code": "PROVIDER_ERROR",
  "message": "MiniMax connection failed"
}
```

**关键设计决策**：

1. **hex → base64 转换**：MiniMax 返回 hex 编码音频，Voice Lab 转为 base64 推送给客户端（base64 更通用，浏览器原生支持）
2. **音频合并保存**：流式推送的同时，服务端拼接所有 chunk，完成后保存为 AudioAsset
3. **VoiceJob 记录**：WebSocket 连接创建 job，完成后更新状态
4. **审计记录**：WebSocket 连接视为一次 Provider 调用，写入 provider_call_logs

---

## 模块拆解

### P4-A：Provider 基类 + MiniMax WebSocket Adapter

**新增/修改文件**：

| 文件 | 操作 |
|------|------|
| `app/providers/base.py` | 修改（新增流式方法签名） |
| `app/providers/minimax_speech_adapter.py` | 修改（新增 `render_stream` 方法） |
| `app/providers/mock_speech_adapter.py` | 修改（新增 mock 流式实现） |
| `app/core/config.py` | 修改（新增 WebSocket 配置） |

#### base.py 新增

```python
from typing import AsyncGenerator

class StreamAudioChunk(BaseModel):
    """Single audio chunk from streaming T2A."""
    chunk_index: int
    audio_data: bytes              # 原始二进制音频
    duration_ms: int | None = None
    is_final: bool = False
    usage_characters: int | None = None
    trace_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class SpeechProvider(ABC):
    # ... 现有方法 ...

    async def render_stream(
        self, plan: RenderPlan
    ) -> AsyncGenerator[StreamAudioChunk, None]:
        """Stream audio chunks from T2A provider. Yields StreamAudioChunk objects."""
        raise NotImplementedError
        yield  # make it an async generator
```

#### minimax_speech_adapter.py 新增

`render_stream()` 方法：
1. 建立 WebSocket 连接到 `wss://api.minimaxi.com/ws/v1/t2a_v2`
2. 发送 `task_start`（model, voice_setting, audio_setting）
3. 等待 `task_started`
4. 发送 `task_continue`（text）
5. 发送 `task_finish`
6. 循环接收 `task_continued` 消息，hex 解码为 bytes，yield `StreamAudioChunk`
7. 收到 `task_finished` 后结束

使用 `websockets` 库（需新增依赖）。

#### mock_speech_adapter.py 新增

Mock 流式：将静音 wav 拆分为 3 个 chunk，逐个 yield，模拟流式推送。

#### config.py 新增

```python
minimax_ws_url: str = "wss://api.minimaxi.com/ws/v1/t2a_v2"
minimax_ws_model: str = "speech-2.8-turbo"   # WebSocket 推荐用 turbo（更快）
minimax_ws_timeout_seconds: int = 120
```

### P4-B：WebSocket Service

**新增文件**：

| 文件 | 操作 |
|------|------|
| `app/services/stream_render_service.py` | 新建 |

Service 职责：
1. 验证 profile + binding（与 sync render 逻辑一致）
2. 构建 RenderPlan
3. 创建 VoiceJob（job_type = `stream_render`，status = `running`）
4. 调用 `adapter.render_stream(plan)` 获取 AsyncGenerator
5. 遍历 chunk，逐个 yield 给调用方
6. 同时拼接所有 chunk 的 audio_data
7. 完成后保存 AudioAsset（合并后的完整音频）
8. 更新 VoiceJob 状态为 success
9. 写入审计记录

```python
class StreamRenderService:
    async def render_stream(
        self, session: Session, request: StreamRenderRequest
    ) -> AsyncGenerator[dict, None]:
        # ... 验证、plan 构建、job 创建 ...
        
        all_audio_data = bytearray()
        chunk_count = 0
        total_duration = 0
        
        async for chunk in adapter.render_stream(plan):
            all_audio_data.extend(chunk.audio_data)
            chunk_count += 1
            total_duration += chunk.duration_ms or 0
            
            yield {
                "event": "audio_chunk",
                "chunk_index": chunk.chunk_index,
                "audio_base64": base64.b64encode(chunk.audio_data).decode(),
                "duration_ms": chunk.duration_ms,
                "is_final": chunk.is_final,
            }
        
        # 保存完整音频为资产
        audio_asset = self._save_complete_audio(session, job, bytes(all_audio_data), ...)
        
        yield {
            "event": "completed",
            "job_id": job.id,
            "total_chunks": chunk_count,
            "total_duration_ms": total_duration,
            "audio_asset": {"id": audio_asset.id, "url": audio_asset.file_url},
        }
```

### P4-C：WebSocket API 端点

**新增/修改文件**：

| 文件 | 操作 |
|------|------|
| `app/api/ws_render.py` | 新建 |
| `app/api/__init__.py` | 修改（注册 ws router） |
| `app/domain/schemas.py` | 修改（新增 StreamRenderRequest） |
| `app/domain/enums.py` | 修改（新增 JobType.stream_render） |

```python
# app/api/ws_render.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from app.core.database import get_session

router = APIRouter()

@router.websocket("/ws/render")
async def ws_render(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # 1. 接收 start 消息
        start_msg = await websocket.receive_json()
        if start_msg.get("event") != "start":
            await websocket.send_json({"event": "error", "code": "INVALID_EVENT", "message": "First message must be 'start'"})
            await websocket.close()
            return
        
        # 2. 发送 connected 确认
        await websocket.send_json({"event": "connected", "request_id": request_id})
        
        # 3. 调用 service.render_stream()
        async for msg in service.render_stream(session, request):
            await websocket.send_json(msg)
        
    except WebSocketDisconnect:
        logger.info("ws_disconnect", extra={"request_id": request_id})
    except Exception as exc:
        await websocket.send_json({"event": "error", "code": "INTERNAL_ERROR", "message": str(exc)[:200]})
    finally:
        await websocket.close()
```

**WebSocket 路由注册**：

```python
# app/api/__init__.py
from app.api import ws_render
api_router.include_router(ws_render.router, prefix="/api/voice", tags=["ws_render"])
```

最终端点：`ws://host/api/voice/ws/render`

### P4-D：前端 WebSocket 播放器

**修改文件**：

| 文件 | 操作 |
|------|------|
| `app/static/index.html` | 修改（T2A Tab 新增"流式生成"模式） |

在 T2A 生成 Tab 的模式选择中新增第三个选项：

```
○ 同步生成  ○ 异步生成  ○ 流式生成
```

流式生成 UI：
- 点击"生成"后建立 WebSocket 连接
- 实时显示接收到的 chunk 数量和已接收时长
- 使用 Web Audio API 或 MediaSource Extensions 实现边接收边播放
- 生成完成后显示完整音频播放器和下载链接
- 连接断开/错误时显示错误信息

简化方案（推荐）：
- 收集所有 base64 chunk，拼接后转为 Blob URL 播放
- 进度条显示"已接收 X 个片段 / Y ms"
- 不要求实时播放（技术复杂度高），完成后一次性播放

### P4-E：测试

**新增文件**：

| 文件 | 操作 |
|------|------|
| `tests/test_ws_render.py` | 新建 |

```python
# 测试用例：

def test_ws_connect_and_start(test_app):
    """WebSocket 连接并发送 start 消息"""
    
def test_ws_receives_audio_chunks(test_app, seed_profile):
    """流式生成返回 audio_chunk 消息"""
    
def test_ws_completed_with_asset(test_app, seed_profile):
    """生成完成后返回 completed 消息含 audio_asset"""
    
def test_ws_invalid_first_message(test_app):
    """第一条消息非 start 返回错误"""
    
def test_ws_empty_text_rejected(test_app, seed_profile):
    """空文本被拒绝"""
    
def test_ws_mock_provider_stream(test_app, seed_profile):
    """Mock provider 流式返回多个 chunk"""
```

---

## 分轮实施计划

| 轮次 | 编号 | 内容 | 改动范围 |
|------|------|------|----------|
| 1 | A | Provider 基类 + MiniMax/Mock WebSocket 适配 | `base.py`, adapters, `config.py`, `requirements.txt` |
| 2 | B | StreamRenderService | `stream_render_service.py`(新) |
| 3 | C | WebSocket API 端点 | `ws_render.py`(新), `schemas.py`, `enums.py`, `__init__.py` |
| 4 | D | 前端流式播放器 | `index.html` |
| 5 | E | 测试 | `test_ws_render.py`(新) |

每轮交付包含对应测试 + `pytest -q` 全量通过。

---

## 新增依赖

```
websockets>=13.0        # WebSocket 客户端（连接 MiniMax）
```

FastAPI 自带 WebSocket 服务端支持，无需额外依赖。

---

## 文件变更汇总

| 文件 | 操作 | 所属轮次 |
|------|------|----------|
| `app/providers/base.py` | 修改 | A |
| `app/providers/minimax_speech_adapter.py` | 修改 | A |
| `app/providers/mock_speech_adapter.py` | 修改 | A |
| `app/core/config.py` | 修改 | A |
| `requirements.txt` | 修改 | A |
| `app/services/stream_render_service.py` | 新建 | B |
| `app/api/ws_render.py` | 新建 | C |
| `app/api/__init__.py` | 修改 | C |
| `app/domain/schemas.py` | 修改 | C |
| `app/domain/enums.py` | 修改 | C |
| `app/static/index.html` | 修改 | D |
| `tests/test_ws_render.py` | 新建 | E |

---

## 安全约束

- WebSocket 连接不暴露 MiniMax API Key
- MiniMax voice_setting / audio_setting 字段只在 Adapter 内部构造
- 客户端推送的文本经过长度校验（< 10000 字符）
- WebSocket 端点在 P4 暂无鉴权（与 REST API 一致）
- 日志中不记录音频 base64 数据

---

## 与现有架构的关系

```
现有同步 T2A:  POST /api/voice/render      → adapter.render_sync()    → 一次性返回
现有异步 T2A:  POST /api/voice/render/async → adapter.create_async_task() → 轮询
新增流式 T2A:  WS   /api/voice/ws/render   → adapter.render_stream() → 流式推送
```

三种模式共享：VoiceProfile → VoiceBinding → RenderPlan → Provider Registry。
流式模式新增：StreamAudioChunk 中间对象、WebSocket 端点、音频拼接保存。
