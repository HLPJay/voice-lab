# P18-XIANGTA-TTS-TASK-MVP-C7

## 实现内容

- 新增 `TtsTaskService`（`src/xiangta/services/tts_task_service.py`）：进程内内存任务管理
- 新增 `POST /api/xiangta/tts/tasks`：同步执行 TTS，保存 completed/failed 状态
- 新增 `GET /api/xiangta/tts/tasks/{taskId}`：轮询任务状态
- 新增 task schemas（`TtsTaskCreateData/TtsTaskCreateResponse/TtsTaskData/TtsTaskStatusResponse`）
- `ProductService` 接入 `TtsTaskService`，`create_product_service()` 自动装配
- business error 转为 failed task（HTTP 200 + failed status），不 500
- `clear_tts_tasks_for_tests()` 支持测试状态清理

## 测试覆盖

`tests/xiangta/test_tts_task_api.py`：9 个测试
- POST 返回 200/ok=true/taskId/status/pollUrl
- POST 后 GET 返回 completed task（含 audioUrl/durationMs/charCount/voicePreset/tone）
- GET missing task 返回 404 flat error（无 detail）
- task 响应无 forbidden provider/core 字段
- business error 创建 failed task（不 500）
- failed task GET 返回 errorKind/message/retryable
- `clear_tts_tasks_for_tests` 清理状态
- 旧 POST /tts 同步接口未受影响

## 未实现

- Redis / Celery / 后台 worker
- 真异步队列
- SQLite task 表
- task 持久化
- 取消/重试/进度流（SSE/WebSocket）
- 多用户 user_id 隔离
- H5 task 页面接入

## 下一步

P18-XIANGTA-COPYWRITING-LLM-MVP-C8
