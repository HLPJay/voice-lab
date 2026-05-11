# P4-C 任务：WebSocket API 端点

## 目标

新建 `app/api/ws_render.py`，实现 `ws://host/api/voice/ws/render` WebSocket 端点。该端点接收客户端 `start` 消息，调用 `StreamRenderService.render_stream()` 流式推送音频 chunk 给客户端。

## 前置条件

- P4-A：`StreamAudioChunk` + adapter `render_stream()` 已实现
- P4-B：`StreamRenderService` + `StreamRenderRequest` 已实现

## 需要修改的文件

| 文件 | 操作 |
|------|------|
| `app/api/ws_render.py` | **新建** |
| `app/api/__init__.py` | 修改（注册 ws router） |
| `tests/test_ws_render.py` | **新建** |

## 详细规范

### 1. `app/api/ws_render.py` 新建

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import get_session
from app.core.errors import VoiceLabError
from app.core.logging import get_logger
from app.domain.schemas import StreamRenderRequest
from app.services.stream_render_service import StreamRenderService
from app.utils.id_generator import new_id

router = APIRouter()
logger = get_logger("ws_render")
```

#### WebSocket 端点

```python
@router.websocket("/ws/render")
async def ws_render(websocket: WebSocket):
    await websocket.accept()
    request_id = new_id("ws")
    logger.info("ws_connected request_id=%s", request_id)
    
    try:
        # 1. 接收第一条消息（必须是 start）
        start_msg = await websocket.receive_json()
        
        if start_msg.get("event") != "start":
            await websocket.send_json({
                "event": "error",
                "code": "INVALID_EVENT",
                "message": "First message must have event='start'",
            })
            await websocket.close(code=1008)
            return
        
        # 2. 验证必要字段
        text = start_msg.get("text", "").strip()
        if not text:
            await websocket.send_json({
                "event": "error",
                "code": "INVALID_REQUEST",
                "message": "text is required and must not be empty",
            })
            await websocket.close(code=1008)
            return
        
        if len(text) > 10000:
            await websocket.send_json({
                "event": "error",
                "code": "INVALID_REQUEST",
                "message": "text must be <= 10000 characters",
            })
            await websocket.close(code=1008)
            return
        
        # 3. 发送 connected 确认
        await websocket.send_json({
            "event": "connected",
            "request_id": request_id,
        })
        
        # 4. 构建 StreamRenderRequest
        request = StreamRenderRequest(
            text=text,
            profile_id=start_msg.get("profile_id", "deep_night_programmer"),
            provider=start_msg.get("provider"),
            output_format=start_msg.get("output_format", "mp3"),
            need_subtitle=start_msg.get("need_subtitle", False),
        )
        
        # 5. 调用 Service 流式渲染
        service = StreamRenderService()
        session = next(get_session())
        try:
            async for msg in service.render_stream(session, request):
                await websocket.send_json(msg)
        finally:
            session.close()
        
    except WebSocketDisconnect:
        logger.info("ws_disconnected request_id=%s", request_id)
    except VoiceLabError as exc:
        logger.error("ws_error request_id=%s error=%s", request_id, exc.message)
        try:
            await websocket.send_json({
                "event": "error",
                "code": exc.error_code or "PROVIDER_ERROR",
                "message": exc.message,
            })
        except Exception:
            pass
    except Exception as exc:
        logger.error("ws_error request_id=%s error=%s", request_id, str(exc))
        try:
            await websocket.send_json({
                "event": "error",
                "code": "INTERNAL_ERROR",
                "message": str(exc)[:200],
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
```

#### 关键设计点

1. **Session 管理**：WebSocket 端点不能用 `Depends(get_session)`（FastAPI WebSocket 不支持 Depends 的 generator 依赖自动关闭）。直接 `next(get_session())` 获取 session，在 finally 中手动 close。

2. **消息流**：
   ```
   Client → start message
   Server → connected (确认)
   Server → started (job 创建)
   Server → audio_chunk × N
   Server → completed (含 audio_asset)
   ```

3. **错误层次**：
   - start 消息格式错 → error + close(1008)
   - text 为空/超长 → error + close(1008)
   - Service 层 VoiceLabError（ProfileNotFound 等）→ error + close
   - 未知异常 → error(INTERNAL_ERROR) + close
   - 客户端断连 → 记日志，静默处理

4. **close code**：
   - 1008 (Policy Violation): 请求格式不合法
   - 默认 1000 (Normal Closure): 正常完成或服务端错误

### 2. `app/api/__init__.py` 修改

在 import 行追加 `ws_render`：

```python
from app.api import admin, async_render, health, ..., ws_render
```

在 `api_router` 注册行末尾添加：

```python
api_router.include_router(ws_render.router, prefix="/api/voice", tags=["ws_render"])
```

最终端点路径：`ws://host/api/voice/ws/render`

### 3. `tests/test_ws_render.py` 新建

使用 FastAPI 的 `TestClient` WebSocket 测试支持：

```python
from starlette.testclient import TestClient
```

TestClient 提供 `with client.websocket_connect(url) as ws:` 上下文管理器。

#### 测试用例（6 个）

**test_ws_connect_and_start**
- WebSocket 连接 `/api/voice/ws/render`
- 发送 `{"event": "start", "text": "测试文本", "provider": "mock", "profile_id": "deep_night_programmer"}`
- 接收第一条消息，验证 `event == "connected"` 且包含 `request_id`
- 接收第二条消息，验证 `event == "started"` 且包含 `job_id`

**test_ws_receives_audio_chunks**
- 发送 start 消息
- 收集所有消息直到 `event == "completed"`
- 过滤 `audio_chunk` 消息，验证数量 >= 1
- 每个 chunk 包含 `chunk_index`、`audio_base64`（非空）、`is_final`

**test_ws_completed_with_asset**
- 发送 start 消息
- 收集所有消息直到 completed
- completed 消息包含 `job_id`、`total_chunks > 0`、`audio_asset.id`、`audio_asset.url`

**test_ws_invalid_first_message**
- 连接后发送 `{"event": "something_else", "text": "..."}`
- 接收 error 消息，`code == "INVALID_EVENT"`

**test_ws_empty_text_rejected**
- 发送 `{"event": "start", "text": "", "provider": "mock"}`
- 接收 error 消息，`code == "INVALID_REQUEST"`

**test_ws_full_message_flow**
- 完整走一遍：连接 → start → 收 connected → 收 started → 收 audio_chunk(s) → 收 completed
- 验证消息顺序正确
- 验证 completed 后连接正常关闭

#### 测试 fixture

使用现有的 `test_app` fixture（来自 conftest.py），它已配置 temp DB + seed_profile。需要确保 `seed_mock_binding` fixture 也被引入（P4-B 已在 conftest.py 中添加）。

如果 `test_app` 返回的是 FastAPI app 实例，用 `TestClient(app)` 包装后调用 `.websocket_connect()`。如果返回的是 TestClient，直接调用 `.websocket_connect()`。参考 conftest.py 中 `test_app` fixture 的实际返回类型。

注意：Starlette TestClient 的 WebSocket 是同步的（不需要 async/await），在 `with ws:` 块内用 `ws.send_json()` 和 `ws.receive_json()` 即可。

## 验收标准

1. `python -m pytest tests/ -x -q` 全部通过（含新增 6 个测试）
2. WebSocket 端点 `ws://host/api/voice/ws/render` 可连接并完成流式生成
3. 消息流顺序正确：connected → started → audio_chunk(s) → completed
4. 格式错误的消息返回 error 事件并关闭连接
5. 空文本和超长文本被拒绝

## 不要做的事

- 不要修改 `app/providers/` 下的任何文件
- 不要修改 `app/services/stream_render_service.py`
- 不要修改前端文件（P4-D 的任务）
- 不要修改现有测试文件
