# P4-E 任务：WebSocket 流式生成集成测试

## 目标

补充 WebSocket 流式生成的端到端集成测试，覆盖 P4 新增功能的完整链路。同时为所有 P4 新增模块补充边界条件测试。

## 前置条件

- P4-A ~ P4-D 全部完成
- 现有测试：`test_ws_provider.py`（5 个，provider 层）、`test_stream_render_service.py`（6 个，service 层）、`test_ws_render.py`（6 个，endpoint 层）

## 需要修改的文件

| 文件 | 操作 |
|------|------|
| `tests/test_ws_integration.py` | **新建** |

## 详细规范

### 测试文件：`tests/test_ws_integration.py`

集成测试关注完整链路的正确性和边界情况，与现有单元测试互补。

```python
import base64
import json
from pathlib import Path

from sqlmodel import select
from starlette.testclient import TestClient

from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob
```

### 测试用例（8 个）

#### 1. test_ws_stream_creates_job_with_correct_type
**目的**：验证 WebSocket 流式生成在数据库中创建 `stream_render` 类型的 VoiceJob。

- 通过 WebSocket 发送 start 消息，收集全部消息直到 completed
- 查数据库 VoiceJob，验证：
  - `job_type == "stream_render"`
  - `status == "success"`
  - `provider == "mock"`
  - `input_text` 包含发送的文本
  - `render_plan_json` 非空

#### 2. test_ws_stream_saves_audio_asset_on_disk
**目的**：验证完成后音频文件实际写入磁盘。

- 通过 WebSocket 完成流式生成
- 从 completed 消息获取 `audio_asset.id`
- 查数据库 AudioAsset，获取 `file_path`
- 验证文件存在且大小 > 0

#### 3. test_ws_stream_audio_chunks_decodable
**目的**：验证所有 audio_chunk 的 base64 数据可正确解码且拼接后的音频有效。

- 收集所有 audio_chunk 消息
- 每个 `audio_base64` 都能 `base64.b64decode()` 成功
- 拼接后的总字节数 > 0
- chunk_index 从 0 开始递增
- 最后一个 chunk 的 is_final == True

#### 4. test_ws_stream_completed_totals_match_chunks
**目的**：验证 completed 消息中的统计与实际收到的 chunk 一致。

- 收集全部消息
- `completed.total_chunks` == 实际收到的 audio_chunk 数量
- `completed.total_duration_ms` >= 0

#### 5. test_ws_stream_nonexistent_profile
**目的**：验证不存在的 profile_id 返回 error 事件。

- 发送 start 消息，`profile_id` 设为 `"nonexistent_xyz"`
- 收到 error 消息（不一定是第一条，可能在 connected 之后）
- error 消息的 code 包含 "NOT_FOUND" 或 message 包含 "not found"（不区分大小写）

#### 6. test_ws_stream_text_exceeds_limit
**目的**：验证超长文本被拒绝。

- 发送 start 消息，text 为 "a" * 10001
- 收到 error 消息，code == "INVALID_REQUEST"

#### 7. test_ws_stream_message_order
**目的**：验证消息顺序严格正确。

- 收集所有消息的 event 类型
- 顺序必须是：`connected` → `started` → `audio_chunk`(s) → `completed`
- 不允许 started 出现在 connected 之前
- 不允许 completed 出现在任何 audio_chunk 之前

#### 8. test_ws_stream_multiple_sequential_sessions
**目的**：验证同一个 TestClient 可以连续发起多次 WebSocket 流式生成，互不干扰。

- 连续发起 2 次完整的 WebSocket 流式生成（第二次在第一次完成后）
- 两次的 job_id 不同
- 两次都成功收到 completed
- 数据库中有 2 条 stream_render 类型的 VoiceJob

### 测试辅助

```python
def collect_ws_events(client, text="测试文本", provider="mock", profile_id="deep_night_programmer"):
    """通过 WebSocket 完成一次流式生成，返回所有事件列表。"""
    events = []
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "start",
            "text": text,
            "provider": provider,
            "profile_id": profile_id,
            "output_format": "mp3",
        })
        while True:
            msg = ws.receive_json()
            events.append(msg)
            if msg["event"] in ("completed", "error"):
                break
    return events
```

所有测试使用 `test_app` + `seed_mock_binding` fixture。

## 验收标准

1. `python -m pytest tests/ -x -q` 全部通过（含新增 8 个测试，总计 206+）
2. 新增测试覆盖完整链路：WebSocket → Service → Provider → DB → 文件系统
3. 边界条件覆盖：不存在的 profile、超长文本、消息顺序、多次会话

## 不要做的事

- 不要修改后端任何文件
- 不要修改前端文件
- 不要修改现有测试文件
- 不要添加 E2E 标记（这些测试用 mock provider，不需要真实 API Key）
