# P7-H 当前项目能力测试与验收报告

## 1. 验收目标

对当前 voice_lab 项目已实现的音频能力做系统测试和验收评估，确认：
- 哪些能力已可用
- 哪些能力需要修复
- 哪些能力适合进入产品化阶段
- P7 Resource Guard 拒绝路径是否正确

本阶段不新增业务能力，不修改 Resource Guard 策略，不进行前端重构。

---

## 2. 测试环境

| 项目 | 详情 |
|---|---|
| 分支 | dev |
| 验收基线 | 4599907（P7-H1 文档修正后） |
| Python 版本 | 3.11+ |
| 主要测试 provider | mock（自动化测试）、minimax（代码审查确认） |
| 是否使用真实 MiniMax | 自动化测试使用 mock；手工能力测试需要真实 MiniMax token |
| 是否消耗 token | 手工测试需要（smoke test 优先） |

---

## 3. 自动化测试结果

```
python -m pytest tests/test_resource_guard.py -q          → 15 passed
python -m pytest tests/test_batch_orchestration.py -q     → 19 passed
python -m pytest tests/test_async_render.py -q            → 14 passed
python -m pytest tests/test_stream_render_service.py -q   → 9 passed
python -m pytest tests/ -x -q                             → 366 passed, 6 skipped
```

**结论**：所有自动化测试通过，无回归。6 skipped 测试为 E2E 测试，需要真实 MiniMax API Key。

---

## 4. 能力测试总表

| 能力 | mock 自动化验证 | minimax 自动化验证 | 前端手工验证 | 结论 | 问题/备注 |
|---|---|---|---|---|---|
| 同步 T2A（mp3） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 同步 T2A（wav） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 同步 T2A（hex 返回） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 同步 T2A（url 返回） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 同步 T2A（字幕） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 同步 T2A（speed/vol/pitch/emotion） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 异步 T2A（submit + poll） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 异步 T2A（download） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 异步 T2A（Resource Guard 拒绝） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| HTTP 流式 T2A | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| WebSocket 流式 T2A | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 流式 T2A（Resource Guard 拒绝） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| provider voice preview | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| binding voice preview | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 声音克隆上传 | 是 | 暂缓真实验证 | 入口存在 | 暂缓产品化 | 成本较高，需单独评估 |
| 声音克隆创建 | 是 | 暂缓真实验证 | 入口存在 | 暂缓产品化 | 成本较高，需单独评估 |
| 克隆音色绑定到 profile | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 声音设计 | 是 | 暂缓真实验证 | 入口存在 | 暂缓产品化 | 成本较高，效果需主观评估 |
| 多版本试音 | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 多版本试音（Resource Guard 拒绝） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 批量长文本生成 | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 批量长文本合并音频 | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 批量长文本合并字幕 | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 批量剧本生成 | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 批量任务 retry_failed | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 批量任务（Resource Guard 拒绝） | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 资产下载 | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 任务历史记录 | 是 | 代码审查确认 | **未验证** | 工程链路可用，真实 MiniMax 待 smoke test | - |
| 前端测试面板交互 | - | - | **未验证** | 待验证 | 需启动服务验证 |

> 注：所有 minimax 能力均通过代码审查确认（Service 层直接调用 adapter），mock 自动化测试验证了逻辑路径。前端手工测试需要启动服务，当前为文档审查阶段。

---

## 5. 详细测试记录

### 5.1 同步 T2A

**入口**：`POST /api/voice/render`

**代码审查确认**：
- `VoiceRenderService.render_voice()` 完整实现
- `output_format` 支持 `hex`（默认）和 `url`
- `audio_format` 支持 `mp3`（默认）、`wav`、`flac`
- `need_subtitle` 支持
- `speed/vol/pitch/emotion` 通过 voice_overrides 支持
- Resource Guard `t2a_sync` 接入（第 111 行）
- Job 先落库 pending，再进入 guard

**支持参数**：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| text | string | 必填 | 输入文本 |
| profile_id | string | 必填 | 声音人设 ID |
| provider | string | mock | provider 名称 |
| output_format | literal[hex, url] | hex | 返回格式 |
| audio_format | literal[mp3, wav, flac] | mp3 | 音频编码格式 |
| need_subtitle | bool | false | 是否生成字幕 |
| speed | float | null | 语速 |
| vol | float | null | 音量 |
| pitch | float | null | 音调 |
| emotion | string | null | 情感 |
| confirm_cost | bool | false | 确认计费 |

**自动化测试**：`tests/test_voice_render_service.py` 验证 mock 路径

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.2 T2A 异步生成

**入口**：
- 提交：`POST /api/voice/render/async`
- 查询：`GET /api/voice/render/async/{job_id}/status`

**代码审查确认**：
- `AsyncRenderService.submit_task()` 先落库 pending，再进入 `t2a_async_submit` guard
- `AsyncRenderService.query_status()` 进入 `t2a_async_query_download` guard
- `ResourceLimitExceeded` 在 query 时保持 job processing，不误标失败
- `_complete_job()` 处理文件下载和 asset 保存
- 支持 `audio_format` 参数

**自动化测试**：`tests/test_async_render.py`

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.3 T2A 流式生成

**入口**：
- HTTP：`POST /api/voice/render/stream`
- WebSocket：`WS /ws/render`

**代码审查确认**：
- `StreamRenderService.render_stream()` 进入 `t2a_stream` guard 后才 yield started
- `StreamRenderService` 支持 `speed/vol/pitch/emotion` 参数覆盖
- `ws_render.py` 正确传递 `speed/vol/pitch/emotion` 到 StreamRenderRequest
- WebSocket VoiceLabError 透传为 `{"event":"error",...}`
- `started` 事件在 guard 内部 yield
- generator 提前关闭时 finally 块标记 job failed

**自动化测试**：`tests/test_stream_render_service.py`

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.4 音色试听 / 绑定试听

**入口**：
- provider voice preview：`POST /api/voice/provider-voices/preview`
- binding voice preview：`POST /api/voice/preview`

**代码审查确认**：
- `ProviderVoicePreviewService.preview()` 进入 `voice_preview` guard 后才调用 adapter
- `VoicePreviewService.preview()` 进入 `binding_voice_preview` guard 后才调用 adapter
- 支持 `speed/vol/pitch/emotion` 参数
- `confirm_cost` 校验

**自动化测试**：`tests/test_voice_preview.py`

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.5 声音克隆

**入口**：
- 上传：`POST /api/voice/clone/upload`
- 创建：`POST /api/voice/clone/create`

**代码审查确认**：
- `VoiceCloneService.upload_audio()` 进入 `voice_clone_upload` guard，验证扩展名（.mp3/.wav/.m4a）、MIME 类型、文件大小（20MB）、音频时长（10-300s）
- `VoiceCloneService.clone_voice()` 进入 `voice_clone_create` guard
- `upsert_provider_voice()` 将克隆音色写入本地数据库
- 支持绑定到 profile

**自动化测试**：`tests/test_voice_clone.py`

**本轮验证状态**：**暂缓真实 MiniMax 验证**

> 注：声音克隆属于高成本能力，真实 MiniMax 调用会消耗较多额度。P7-H1 起暂缓真实验证，仅确认工程链路完整。本轮只做代码审查和 mock 自动化测试确认，不做真实 token 消耗测试。后续单独立项验证成功率、音频样本要求和产品化可行性。

**结论**：**暂缓产品化**

---

### 5.6 声音设计

**入口**：`POST /api/voice/design`

**代码审查确认**：
- `VoiceDesignService.design_voice()` 进入 `voice_design` guard 后才调用 adapter
- `prompt` 生成 voice_id
- `preview_text` 生成试听音频
- `upsert_provider_voice()` 写入本地数据库

**自动化测试**：`tests/test_voice_design.py`

**本轮验证状态**：**暂缓真实 MiniMax 验证**

> 注：声音设计属于高成本能力，真实 MiniMax 调用会消耗较多额度。生成效果需要主观评估，与具体产品场景强相关。P7-H1 起暂缓真实验证，仅确认工程链路完整。后续单独立项验证生成质量和产品化可行性。

**结论**：**暂缓产品化**

---

### 5.7 多版本试音

**入口**：`POST /api/voice/variants`

**代码审查确认**：
- `VoiceVariantService.render_variants()` 进入 `voice_variants` guard 后才创建 group
- `resource_guard_already_acquired=True` 避免 child render_voice 双重 guard
- 支持 `variant_count`（1-5）
- 每次生成固定 5 个组合（speed + emotion）
- 所有 variant 存入 `VoiceVariant` 表

**自动化测试**：`tests/test_voice_variant_service.py`

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.8 批量长文本生成

**入口**：`POST /api/voice/batch/submit`（mode=longtext）

**代码审查确认**：
- `submit_longtext()` 进入 `batch_longtext` guard 后才创建 BatchJob + Segments
- `TextSegmentService.segment()` 支持 auto/paragraph/sentence 分段策略
- `execute()` 进入 `batch_execute` guard 后才将 batch 状态改为 running
- segment 并发受 `batch_max_concurrency`（默认1）控制
- segment 失败时 `_mark_segment_voice_job_failed()` 同步标记 segment + VoiceJob
- `AudioMergeService.merge()` 合并音频，生成 merged_audio_asset
- `AudioMergeService.merge_timelines()` 合并字幕

**自动化测试**：`tests/test_batch_orchestration.py`

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.9 批量剧本生成

**入口**：`POST /api/voice/batch/submit`（mode=script）

**代码审查确认**：
- `submit_script()` 进入 `batch_script` guard 后才创建 BatchJob + Segments
- 每个 script line 可指定不同 `profile_id` 和 `params` 覆盖
- 支持 `role` 字段标记角色名
- 其他逻辑与长文本模式共用

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.10 资产下载 / 历史记录 / 状态查询

**入口**：
- 资产下载：`GET /api/voice/assets/{asset_id}/download`
- 任务历史：`GET /api/voice/jobs`

**代码审查确认**：
- `AssetService` 保存音频和字幕 asset
- `VoiceJobRepository` 提供 job 查询
- `StatsService` 提供聚合统计

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.11 Resource Guard 拒绝路径

**代码审查确认**（所有 operation）：

| Operation | 拒绝行为 | 代码位置 |
|---|---|---|
| `t2a_sync` | Job failed，不调用 provider | voice_render_service.py:111 |
| `t2a_async_submit` | Job failed，不调用 provider | async_render_service.py:101 |
| `t2a_async_query_download` | 保持 processing，不误标 failed | async_render_service.py:174 |
| `t2a_stream` | 不 yield started，只 yield error | stream_render_service.py:115 |
| `voice_preview` | VoiceJob failed | provider_voice_preview_service.py:102 |
| `binding_voice_preview` | 不调用 adapter | voice_preview_service.py:77 |
| `voice_variants` | 不创建 group | voice_variant_service.py:29 |
| `voice_design` | 不调用 adapter | voice_design_service.py:31 |
| `voice_clone_upload` | 不调用 adapter，不返回 file_id | voice_clone_service.py:100 |
| `voice_clone_create` | 不调用 adapter，不创建 voice_id | voice_clone_service.py:135 |
| `batch_longtext` | 不创建 BatchJob/Segment，不启动 execute | batch_orchestration_service.py:76 |
| `batch_script` | 不创建 BatchJob/Segment，不启动 execute | batch_orchestration_service.py:153 |
| `batch_execute` | BatchJob failed + error_message | batch_orchestration_service.py:297 |

**前端友好提示**：所有 HTTP 和 WebSocket 错误均通过 `parseApiError` / `formatApiError` / `renderApiError` 渲染为友好提示。

**结论**：**工程链路可用，真实 MiniMax 待 smoke test**

---

### 5.12 前端测试面板基础交互

**代码审查确认**：
- 单一 HTML 文件 `app/static/index.html` 实现
- 6 个 Tab：T2A 同步 / T2A 异步 / T2A 流式 / 音色管理 / 克隆 / 设计 / 批量生成
- 统一错误解析（`parseApiError`）
- 资源超限友好提示（`.resource-limit-msg`）
- 音频播放（`<audio controls>`）
- WebSocket 流式渲染
- Batch polling

**手工测试状态**：**未验证**（需要启动服务 `uvicorn app.main:app --reload`）

---

## 6. 已发现问题

### P0 阻塞
**无**

### P1 高优先级
**无**

### P2 普通问题

1. **前端仍是单文件 HTML 测试面板**：不是产品化工作台，但功能完整
2. **异步轮询间隔固定**：无动态退避，频繁查询可能浪费资源
3. **批量任务无实时进度推送**：依赖前端轮询

### P3 优化建议

1. **手工验证清单全部未执行**：建议后续补充实际浏览器测试
2. **部分 operation 无独立测试**：如 `provider_voice_import_verify` 等
3. **错误详情格式依赖 `key=value` 字符串解析**：可考虑结构化 error payload

---

## 7. 产品化判断

### 第一批产品化候选能力

> 这些能力的工程链路已通过自动化测试和代码审查，适合作为 P8 优先产品化对象；但在正式面向用户前，仍需要进行真实 MiniMax 小文本 smoke test 和前端手工验证。

- **同步 T2A**：功能完整，状态机清晰，Resource Guard 接入
- **异步 T2A**：功能完整，支持 submit/poll/download 完整链路
- **流式 T2A**（HTTP + WebSocket）：完整实现
- **批量长文本 / 剧本**：分段 → 生成 → 合并完整链路
- **字幕生成**：随 T2A 同步生成
- **资产下载 / 历史记录**：完整实现
- **Resource Guard**：覆盖所有真实 provider 调用入口
- **前端友好提示**：RESOURCE_LIMIT_EXCEEDED 统一展示

### 暂缓产品化（后续高级能力，单独立项验证）

- **声音克隆**：成本较高，需要合格音频样本，成功率和效果需要单独评估
- **声音设计**：成本较高，生成效果需要主观评估，与具体产品场景强相关

### 需要修复后产品化

- **手工验证未执行**：所有能力均未在真实浏览器中验证
- **移动端体验**：当前前端未做响应式优化

### 暂不建议产品化

- **admin 管理面板**：功能较基础，不是产品重点

### 仅适合作为测试工具

- **当前前端测试面板**：单文件 HTML，交互有限，适合内部测试

---

## 8. 下一步建议

1. **执行手工验证**：启动服务，测试各能力在真实浏览器中的表现
2. **进入 P8 前端 UX 修复**（P8-FRONTEND_UX_FIXES.md）：内联创建人设、音色试听工作台、绑定反馈闭环、分页
3. **响应式优化**：如果目标包含移动端，需要 H5 适配
4. **生产部署准备**：考虑 PostgreSQL 替换 SQLite、Redis 集群、限流策略等产品化需求

**建议**：在执行手工验证后，如无 P0/P1 问题，可以进入 P8 前端 UX 修复阶段。

---

## 附录：API 入口速查

| 能力 | 方法 | 路径 |
|---|---|---|
| 同步 T2A | POST | `/api/voice/render` |
| 异步提交 | POST | `/api/voice/render/async` |
| 异步状态查询 | GET | `/api/voice/render/async/{job_id}/status` |
| HTTP 流式 | POST | `/api/voice/render/stream` |
| WebSocket 流式 | WS | `/ws/render` |
| provider voice preview | POST | `/api/voice/provider-voices/preview` |
| binding voice preview | POST | `/api/voice/preview` |
| 声音克隆上传 | POST | `/api/voice/clone/upload` |
| 声音克隆创建 | POST | `/api/voice/clone/create` |
| 声音设计 | POST | `/api/voice/design` |
| 多版本试音 | POST | `/api/voice/variants` |
| 批量长文本提交 | POST | `/api/voice/batch/submit` |
| 批量剧本提交 | POST | `/api/voice/batch/submit` |
| 批量状态查询 | GET | `/api/voice/batch/{batch_id}/status` |
| 批量重试 | POST | `/api/voice/batch/{batch_id}/retry` |
| 资产下载 | GET | `/api/voice/assets/{asset_id}/download` |
| 任务历史 | GET | `/api/voice/jobs` |
| 成本估算 | GET | `/api/voice/cost/estimate` |
