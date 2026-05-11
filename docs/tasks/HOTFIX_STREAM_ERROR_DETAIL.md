# Hotfix：流式生成错误信息丢失 MiniMax 原始错误详情

## 问题

流式生成失败时，MiniMax 返回的 `base_resp.status_msg` 被传入 `ProviderError.detail`，但日志和前端消息只使用了 `exc.message`（固定字符串 "WebSocket task failed"），导致无法定位 MiniMax 侧的具体失败原因。

## 涉及文件

| 文件 | 操作 |
|------|------|
| `app/services/stream_render_service.py` | 修改（日志 + error 事件补充 detail） |
| `app/api/ws_render.py` | 修改（error 事件补充 detail） |
| `app/providers/minimax_speech_adapter.py` | 修改（补充 adapter 层日志） |

## 修复内容

### 1. `app/services/stream_render_service.py`

**第 183 行**，日志补充 `exc.detail`：

```python
# 原：
logger.error("stream_render_failed job=%s error=%s", job.id, exc.message)

# 改为：
logger.error("stream_render_failed job=%s error=%s detail=%s", job.id, exc.message, getattr(exc, 'detail', None))
```

**第 185 行**，error 事件 message 拼接 detail：

```python
# 原：
yield {"event": "error", "code": error_code, "message": exc.message}

# 改为：
detail = getattr(exc, 'detail', None)
full_message = f"{exc.message}: {detail}" if detail else exc.message
yield {"event": "error", "code": error_code, "message": full_message}
```

### 2. `app/api/ws_render.py`

**第 82-86 行**，VoiceLabError 处理同样补充 detail：

```python
# 原：
logger.error("ws_error request_id=%s error=%s", request_id, exc.message)
await websocket.send_json({
    "event": "error",
    "code": error_code,
    "message": exc.message,
})

# 改为：
detail = getattr(exc, 'detail', None)
full_message = f"{exc.message}: {detail}" if detail else exc.message
logger.error("ws_error request_id=%s error=%s detail=%s", request_id, exc.message, detail)
await websocket.send_json({
    "event": "error",
    "code": error_code,
    "message": full_message,
})
```

### 3. `app/providers/minimax_speech_adapter.py`

两处 task_failed 处理（约第 706-708 行和第 739-741 行），在 raise 之前补充日志：

```python
# task_start 阶段的 task_failed（约第 706 行）：
if msg.get("event") == "task_failed":
    base_resp = msg.get("base_resp", {})
    status_msg = base_resp.get("status_msg", str(msg))
    _provider_logger.error("ws_task_start_failed status_msg=%s base_resp=%s", status_msg, base_resp)
    raise ProviderError("WebSocket task_start failed", status_msg)

# 流式阶段的 task_failed（约第 739 行）：
elif event == "task_failed":
    base_resp = msg.get("base_resp", {})
    status_msg = base_resp.get("status_msg", str(msg))
    _provider_logger.error("ws_task_failed status_msg=%s base_resp=%s", status_msg, base_resp)
    raise ProviderError("WebSocket task failed", status_msg)
```

## 验收标准

1. `python -m pytest tests/ -x -q` 全部通过
2. 使用 mock provider 流式生成正常工作
3. 当 MiniMax 返回 task_failed 时：
   - 日志中可以看到 `status_msg=xxx` 和 `base_resp={...}` 的完整内容
   - 前端收到的 error 消息包含 MiniMax 原始错误详情（如 "WebSocket task failed: insufficient quota"）
4. 不影响非流式生成的功能

## 不要做的事

- 不要修改 VoiceLabError 基类
- 不要修改测试文件
- 不要修改前端文件
