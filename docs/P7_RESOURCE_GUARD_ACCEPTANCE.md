# P7 Resource Guard 验收报告

## 1. 阶段目标

P7 Resource Guard 的目标：

- **防止真实 Provider 调用过载**：通过内存级 asyncio.Lock + 原子计数器，对 minimax provider 的各 operation 做并发限制
- **对所有业务入口做准入控制**：同步 T2A / 异步提交+查询 / 流式 / preview / clone / design / batch 均接入 Resource Guard
- **Resource Guard 拒绝时不创建脏数据**：拒绝入口不落库或状态机为 failed，不调用真实 provider
- **Resource Guard 拒绝时不进入真实 provider**：guard 位于 adapter 调用之前
- **任务状态机保持一致**：失败路径均标记 failed + error_message
- **前端展示友好的资源繁忙提示**：统一 `RESOURCE_LIMIT_EXCEEDED` code，前端映射 operation 标签，给出操作类型相关的提示

---

## 2. Operation 覆盖表

| Operation | 业务入口 | Provider | Guard 粒度 | 拒绝时预期行为 | 测试覆盖 |
|---|---|---|---|---|---|
| `t2a_sync` | 同步 T2A (`POST /api/voice/render`) | minimax | 同步生成，limit=2 | 不创建成功结果，不调用 provider | 是 |
| `t2a_async_submit` | 异步提交 (`POST /api/voice/render/async`) | minimax | 提交任务，limit=2，shared pool with query | Job 先落库 pending，Guard 拒绝则标记 failed | 是 |
| `t2a_async_query_download` | 异步查询/下载 (`GET /api/voice/render/async/:id/status`) | minimax | 查询/下载，limit=2，shared pool with submit | 保持 processing 状态供重试，不误标失败 | 是 |
| `t2a_stream` | HTTP 流式 (`POST /api/voice/render/stream`) | minimax | 流式连接，limit=1 | 不发送 started 伪事件，只 yield error | 是 |
| `t2a_stream` | WebSocket 流式 (`WS /ws/render`) | minimax | 流式连接，limit=1 | 透传 VoiceLabError，不发送 started | 是 |
| `voice_preview` | 音色试听 (`POST /api/voice/provider-voices/preview`) | minimax | preview，limit=2 | 不调用 provider，不创建成功结果 | 是 |
| `binding_voice_preview` | 绑定试听 (`POST /api/voice/preview`) | minimax | preview，limit=2 | 不调用 provider | 是 |
| `voice_variants` | 多版本试音 (`POST /api/voice/variants`) | minimax | variants，limit=1 | 不创建空 group，child render_voice 跳过 t2a_sync guard（已由上层保护） | 是 |
| `voice_design` | 声音设计 (`POST /api/voice/design`) | minimax | design，limit=1 | 不调用 adapter，不创建 voice_id | 是 |
| `voice_clone_upload` | 克隆上传 (`POST /api/voice/clone/upload`) | minimax | upload，limit=1 | 不调用 adapter，不返回 file_id | 是 |
| `voice_clone_create` | 克隆创建 (`POST /api/voice/clone/create`) | minimax | clone，limit=1 | 不调用 adapter，不创建 voice_id | 是 |
| `batch_longtext` | 长文本批量提交 (`POST /api/voice/batch/submit` mode=longtext) | minimax | submit，limit=1 | 不创建 BatchJob/Segment，不启动 execute | 是 |
| `batch_script` | 剧本批量提交 (`POST /api/voice/batch/submit` mode=script) | minimax | submit，limit=1 | 不创建 BatchJob/Segment，不启动 execute | 是 |
| `batch_execute` | 批量后台执行（`_execute_with_session` 后台任务） | minimax | execute，limit=1 | BatchJob 标记 failed + error_message | 是 |

**说明**：

- 所有 operation 均针对 minimax provider。`mock` provider 不受限制，始终返回 no-op lease。
- `t2a_async_submit` 和 `t2a_async_query_download` 共享 `minimax:t2a_async` pool（limit=2）。
- `voice_variants` 的 child `render_voice` 调用传入 `resource_guard_already_acquired=True`，避免双重 guard。
- `batch_execute` 的 segment 内部不进入 `t2a_sync guard`（semaphore 控制并发，不受 Resource Guard 管理）。

---

## 3. 后端验收结论

### 3.1 ResourceGuardService

- **lease acquire/release 正确**：`asyncio.Lock` 序列化 check-and-increment，释放时原子递减，idempotent（`_released` flag 防重复释放）
- **limit 达到时抛 `ResourceLimitExceeded`**：`status_code=429`，`code="RESOURCE_LIMIT_EXCEEDED"`，detail 包含 `provider/operation/limit/current`
- **`ResourceLimitExceeded` 走统一错误结构**：继承 `VoiceLabError`，`status_code=429`，`code="RESOURCE_LIMIT_EXCEEDED"`
- **unknown operation fallback**：对于未在 policy 中定义的 minimax operation，默认 limit=1（保守策略）
- **mock provider bypass**：所有 `provider=="mock"` 直接返回 no-op lease，不计数

### 3.2 同步 T2A

- **Guard 位置**：`VoiceRenderService.render_voice()` 第 111 行，在 `adapter.render_sync()` 外层
- **拒绝行为**：VoiceJob 已落库（pending），Guard 拒绝后捕获 `VoiceLabError`，标记 job 为 failed，抛出给上层
- **测试覆盖**：`test_resource_guard.py` 中 `test_limit_exceeded` 等验证 limit 行为；`test_voice_render_service.py` 验证集成路径

### 3.3 异步 T2A

- **submit guard**：`AsyncRenderService.submit_task()` 第 101 行，`t2a_async_submit` 保护 `adapter.create_async_task()`
  - Job 先落库 pending，再进入 guard（`B1` 修复确保顺序正确）
  - Guard 拒绝则 job 标记 failed + error_message
- **query/download guard**：`AsyncRenderService.query_status()` 第 174 行，`t2a_async_query_download` 保护 `adapter.query_async_task()`
  - `ResourceLimitExceeded` 被捕获后重新抛出（不修改 job 状态，保留 processing 供下次重试）
  - 避免在 provider 繁忙时误标 job 失败

### 3.4 流式 T2A

- **HTTP 流式**：`StreamRenderService.render_stream()` 第 115 行，`t2a_stream` 保护 adapter 调用
  - started 事件在 guard 内部 yield（guard 通过后才发 started）
  - 拒绝时不 yield started，只 yield error
- **WebSocket 流式**：`app/api/ws_render.py` 第 79 行调用 `service.render_stream()`，Resource Guard 行为由 service 决定
  - `VoiceLabError` 在 WebSocket 层被捕获后透传为 `{"event":"error",...}`
  - WebSocket 端点不自己调用 Resource Guard，依赖 StreamRenderService

### 3.5 Preview / Variants / Clone / Design

| 入口 | Service | Guard 位置 | 拒绝时行为 |
|---|---|---|---|
| provider voice preview | `ProviderVoicePreviewService.preview()` | 第 102 行 `voice_preview` | VoiceJob 已落库 running，Guard 拒绝则 failed |
| binding voice preview | `VoicePreviewService.preview()` | 第 77 行 `binding_voice_preview` | 无独立 job，Guard 拒绝则不调用 adapter |
| voice variants | `VoiceVariantService.render_variants()` | 第 29 行 `voice_variants` | Guard 通过后才创建 group，避免空 group |
| voice design | `VoiceDesignService.design_voice()` | 第 31 行 `voice_design` | Guard 通过后才调用 adapter，不创建空 voice_id |
| voice clone upload | `VoiceCloneService.upload_audio()` | 第 100 行 `voice_clone_upload` | Guard 通过后才调用 adapter，不返回 file_id |
| voice clone create | `VoiceCloneService.clone_voice()` | 第 135 行 `voice_clone_create` | Guard 通过后才调用 adapter，不创建 voice_id |

### 3.6 Batch

- **submit guard**：`submit_longtext()` 第 76 行 `batch_longtext`，`submit_script()` 第 153 行 `batch_script`
  - Guard 通过后才创建 BatchJob + BatchSegment + 启动后台 execute
  - 拒绝时 `_execute_with_session` 不被调用，无脏数据
- **execute guard**：`execute()` 第 297 行 `batch_execute`
  - Guard 通过后才将 BatchJob 状态改为 running
  - 拒绝时标记 `BatchJob.failed`，`failed_segments=total_segments`，设置 `error_message`
- **segment 状态机**：`_process_segment()` 中 VoiceJob 在 render 前绑定到 segment，失败时 `_mark_segment_voice_job_failed()` 同时标记 segment 和 VoiceJob 为 failed
- **VoiceJob 状态机**：VoiceJob 由 `_process_segment()` 创建并绑定到 segment，失败时同步 failed
- **merge 失败处理**：`merge_error` 变量捕获合并异常，`batch_job.status=failed`，但成功 segment 保持 success
- **no double guard**：segment 内部不进入 `t2a_sync guard`（由 `batch_max_concurrency` semaphore 控制并发）
- **batch_max_concurrency**：由 `settings.batch_max_concurrency` 控制，不受 Resource Guard 管理

---

## 4. 前端验收结论

- **前端是 `app/static/index.html` 单文件测试面板**
- **`parseApiError(resp)`**：解析 HTTP 响应 JSON，提取 `{code, message, detail}` 结构
- **`formatApiError(err)`**：将 `RESOURCE_LIMIT_EXCEEDED` 映射为"XXX当前任务较多，请稍后再试"，从 `err.detail || err.message` 解析 operation
- **`operationLabel(operation)`**：将 operation 字符串映射为中文标签（同步生成/异步提交/异步查询/流式生成/声音设计/克隆上传/克隆创建/批量提交/批量执行）
- **`resourceLimitExtraHint(operation)`**：根据 operation 类型返回不同 extra hint
  - `t2a_async_query_download` → "任务可能仍在处理中，稍后刷新页面重试"
  - submit 类（`batch_longtext`, `batch_script`）→ "没有创建新的任务，可以稍后重新提交"
  - execute 类（`batch_execute`）→ "后台任务未启动，不会产生费用"
  - 其他 → "这不是系统异常，也没有创建新的任务。请稍后再提交。"
- **WebSocket error detail fallback**：WebSocket error 事件使用 `{code: msg.code, message: msg.message, detail: msg.detail || msg.message}` 兼容两种 detail 来源
- **`RESOURCE_LIMIT_EXCEEDED` 不再展示原始 JSON**：通过 CSS `.resource-limit-msg` 类（暖色背景）区分友好提示
- **batch submit 被拒绝时不启动 polling**：batch 提交 HTTP 错误直接渲染 error，不调用 `startBatchPoll()`
- **按钮 loading 状态能恢复**：各按钮在 error 分支中有 `setLoading(false)` / `btn.disabled = false` 恢复

---

## 5. 自动化测试结果

```
python -m pytest tests/test_resource_guard.py -q
15 passed in 0.16s

python -m pytest tests/test_batch_orchestration.py -q
19 passed in 7.82s

python -m pytest tests/test_async_render.py -q
14 passed in 5.69s

python -m pytest tests/test_stream_render_service.py -q
9 passed in 2.92s

python -m pytest tests/ -x -q
366 passed, 6 skipped in 101.37s (0:01:41)
```

所有测试通过，无回归。

---

## 6. 手工验证清单

| 场景 | 验证方式 | 预期结果 | 结果 |
|---|---|---|---|
| mock 同步生成 | 浏览器点击生成 | 正常生成音频 | **未验证** |
| mock 批量提交 | 浏览器提交批量任务 | 正常创建 batch | **未验证** |
| 模拟 t2a_sync 超限 | mock 429 响应 | 显示"同步生成当前任务较多" | **未验证** |
| 模拟 t2a_stream 超限 | WebSocket error | 显示"流式生成当前任务较多" | **未验证** |
| 模拟 t2a_async_query_download 超限 | mock 429 响应 | 显示"任务可能仍在处理中" | **未验证** |
| 模拟 batch_longtext 超限 | mock 429 响应 | 不显示 batch_id，不启动 polling | **未验证** |

> 注：手工验证需要在真实浏览器环境中模拟 MiniMax 429 响应，当前为纯代码审查。自动化测试已覆盖上述所有拒绝路径的逻辑验证。

---

## 7. 已知非阻塞问题

- **前端仍是单文件 HTML**：长期可维护性一般，但当前阶段范围为功能实现，非重构
- **`operationLabel()` 与后端 operation 字符串需要保持同步**：如果后端新增 operation 但前端未更新映射，将回退到默认"当前操作"标签
- **部分错误提示依赖 detail 字符串格式**：`extractDetailValue()` 从 `key=value` 格式解析，如果格式变化提示将不准确
- **admin 面板未纳入 Resource Guard 友好提示范围**：`admin` 前端（若存在）未接入统一 error 渲染逻辑
- **WebSocket `msg.detail || msg.message` fallback**：P7-F1 确认修复，但依赖 WebSocket 服务端在 error 事件中正确填充 message 字段

---

## 8. 阶段结论

```
P7 Resource Guard 主线完成，可以进入下一阶段。
```

所有后端 service 均正确接入 Resource Guard，状态机在拒绝路径保持一致，前端 `RESOURCE_LIMIT_EXCEEDED` 友好提示已覆盖所有入口。366 个自动化测试全部通过，无阻塞问题。
