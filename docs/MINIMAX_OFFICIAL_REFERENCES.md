# MiniMax 官方文档索引

本文档整理 Voice Lab 项目所涉及的 MiniMax 官方 API 参考索引、能力归属和安全约束。

官方基础 URL：`https://platform.minimaxi.com/docs/api-reference/`

---

## 1. 能力分组

### Speech T2A（Text-to-Audio）

| 接口 | 路径 | 说明 | Voice Lab 归属 |
|------|------|------|--------------|
| 同步 T2A HTTP | `/speech-t2a-http` | 同步生成音频，返回 hex 或 url | P0 已实现基础（`MiniMaxSpeechAdapter.render_sync`） |
| T2A WebSocket | `/speech-t2a-websocket` | WebSocket 流式生成 | P2 暂不实现 |
| 异步 T2A 创建任务 | `/speech-t2a-async-create` | 提交长文本异步任务 | P2 ✅ 已实现（`AsyncRenderService.submit_task`） |
| 异步 T2A 查询任务 | `/speech-t2a-async-query` | 查询异步任务状态和结果 | P2 ✅ 已实现（`AsyncRenderService.query_status`） |

### Voice Management

| 接口 | 路径 | 说明 | Voice Lab 归属 |
|------|------|------|--------------|
| Get Voice（音色列表） | `/voice-management-get` | 获取可用音色列表 | P1 ✅ 已实现（`VoiceCatalogService`） |
| Delete Voice | `/voice-management-delete` | 删除音色 | P2 ✅ 已实现（`VoiceDeleteService`） |

### Voice Design

| 接口 | 路径 | 说明 | Voice Lab 归属 |
|------|------|------|--------------|
| Voice Design | `/voice-design-design` | 创建声音设计 | P2 ✅ 已实现（`VoiceDesignService`） |

### Voice Clone

| 接口 | 路径 | 说明 | Voice Lab 归属 |
|------|------|------|--------------|
| 上传复刻音频 | `/voice-cloning-uploadcloneaudio` | 上传待克隆音频 | P2 ✅ 已实现（`VoiceCloneService.upload_audio`） |
| 上传 Prompt 音频 | `/voice-cloning-uploadprompt` | 上传参考音频 | P2 ✅ 已实现（purpose=prompt_audio） |
| 创建克隆 | `/voice-cloning-clone` | 执行克隆任务 | P2 ✅ 已实现（`VoiceCloneService.clone_voice`） |

---

## 2. Voice Lab 阶段归属

### P0（已实现或已有基础）

- **同步 T2A HTTP**：`MiniMaxSpeechAdapter.render_sync` 已实现，调用 `POST /v1/t2a_v2`
  - 支持 `model=speech-2.8-hd`
  - 支持 `output_format=hex` 和 `url`
  - 支持 `subtitle_enable=true`
  - 字幕真实结构已验证（commit `0e5177a`）

### P1 T2A HTTP 增强（已完成）

- **同步 T2A HTTP 增强**（commit `0e5177a fix: harden minimax t2a response parsing`）
  - `output_format=url` 模式下优先使用 `audio_url` 下载
  - `data.audio` hex 回退逻辑（奇长度 hex 不崩溃，抛 ProviderError）
  - `data.subtitle_file` URL 下载并解析 JSON timeline（支持 sentences/items/timeline/words 字段）
  - `data.audio` 为 http/https URL 时直接下载
  - 真实 T2A 响应结构已验证

### P1（推荐实现顺序依次）

1. **Voice Management Get** → Provider Voice Catalog
   - 端点：`POST /v1/get_voice`
   - 设计已落地（见 `docs/IMPLEMENTATION_PLAN.md` P1 部分）
   - 官方参数：`voice_type=system/voice_cloning/voice_generation/all`

2. **Voice Management Delete**（P1 后期）
   - 端点：`POST /v1/delete_voice`
   - 请求体：`{"voice_type": "voice_cloning", "voice_id": "..."}`
   - 约束：只允许删除 `voice_cloning` 和 `voice_generation` 类型，`system` 音色不可删除
   - 删除后 `voice_id` 不可复用
   - 必须增加授权确认步骤

### P2（主体已完成）

1. **异步 T2A**（长文本）✅ 已实现
   - 创建：`POST /v1/t2a_async_v2`
   - 查询：`GET /v1/query/t2a_async_query_v2?task_id=...`
   - 状态：`processing` / `success` / `failed` / `expired`
   - 成功后通过 `file_url` 下载并保存资产

2. **Voice Design** ✅ 已实现
   - 端点：`POST /v1/voice_design`
   - 返回 `voice_id` 和 `trial_audio_hex`

3. **Voice Clone** ✅ 已实现
   - 三步：上传音频 → 上传 prompt（可选）→ 创建克隆
   - 上传：`POST /v1/files/upload`
   - 克隆：`POST /v1/voice_clone`

4. **Voice Delete** ✅ 已实现
   - 端点：`POST /v1/delete_voice`
   - 只允许删除 `voice_cloning` 和 `voice_generation` 类型

5. **T2A WebSocket**（未实现）
   - 流式生成，用于实时场景
   - 不在 P2 主体范围

---

## 3. 当前推荐开发顺序

```
1. Voice Management Get
   -> Provider Voice Catalog (GET /api/voice/provider-voices)
   -> P1 第 1-4 轮

2. 同步 T2A 增强 ✅ 已完成
   -> output_format=url 自动下载 ✅（commit `0e5177a`）
   -> 字幕完整解析 ✅（commit `0e5177a`）
   -> P1/P2 过渡期 ✅

3. Voice Management Delete
   -> DELETE /api/voice/provider-voices/{provider_voice_id}
   -> P2 前期（需授权确认）

4. 异步 T2A
   -> POST /v1/t2a_async_v2
   -> GET /v1/query/t2a_async_query_v2?task_id=...
   -> P2 中期

5. Voice Design / Voice Clone
   -> P2 后期

6. T2A WebSocket
   -> 不在 P1/P2 近期计划内
```

---

## 4. 明确安全 / 架构约束

### MiniMax 字段隔离

- `voice_setting`、`audio_setting`、`subtitle_enable`、`voice_id` 等 MiniMax 专有字段**只允许**出现在 `app/providers/minimax_speech_adapter.py` 内部
- API 层不得接受用户传入的 MiniMax 专有参数
- `RenderPlan` 是内部标准协议，不直接映射 MiniMax 字段

### Voice Management Delete 安全约束

- **只允许删除** `voice_type=voice_cloning` 和 `voice_generation` 的音色
- `voice_type=system`（系统音色）**禁止删除**
- 删除前必须通过 `VoiceBinding` 检查该 voice_id 是否被任何 profile 绑定
- 必须记录删除操作日志

### Voice Clone 安全约束

- 必须增加用户授权确认步骤（API 请求需附带 `user_acknowledged=true` 或类似标识）
- 克隆前应明确告知用户音频处理的数据合规性

### 测试约束

- **自动测试不得请求真实 MiniMax API**
- 使用 `MockSpeechAdapter` 和 `unittest.mock.patch`
- 所有 MiniMax 适配器测试用 mock 响应

### WebSocket 约束

- T2A WebSocket 不在 P1/P2 近期计划
- 实现前需额外架构设计（连接管理、流式响应）

---

## 5. 官方文档缺口说明

以下信息在当前官方文档中**未明确**，实现前需验证：

| 缺口 | 说明 |
|------|------|
| **音色 language/gender 字段** | Get Voice 返回中是否已有 language 和 gender？目前设计中假设可能不存在，需从 name/description 推断 |
| **音色唯一性约束** | `voice_type=all` 时三个分组的 voice_id 是否可能重复？需确认 UNIQUE(provider, provider_voice_id) 是否安全 |
| **Delete Voice 权限要求** | T2A API Key 是否有 Delete Voice 权限？403 时返回什么错误码？ |
| **Voice Clone 结果获取方式** | 克隆任务是同步还是异步？结果如何查询？ |
| **异步 T2A 任务超时** | 异步任务最大等待时间？超时后如何处理？ |
| **Voice Clone详细参数** | ✅ 已实现：file_id / prompt_file_id / prompt_text / preview_text / need_noise_reduction / need_volume_normalization |
| **Voice Design完整流程** | ✅ 已实现：prompt / preview_text / 可选 voice_id |
| **字幕完整结构** | ✅ 已验证：T2A 返回 `data.subtitle_file`（URL），下载后 JSON 结构含 `sentences`/`items`/`timeline`/`words` 字段，timeline item 含 text/pronounce_text/time_begin/time_end/text_begin/text_end/pronounce_text_begin/pronounce_text_end/is_final_segment |
| **错误码完整列表** | MiniMax API 完整错误码文档未找到，实现时需逐个处理未知错误 |

以下内容**确认不实现**，不追查：

- T2A WebSocket 文档（不在近期计划）
- 多用户、额度统计、API Key 管理、对象存储、队列 Worker、评测反馈、视频模块

---

## 6. 官方文档链接索引

### Speech T2A

- 同步 HTTP：https://platform.minimaxi.com/docs/api-reference/speech-t2a-http
- WebSocket：https://platform.minimaxi.com/docs/api-reference/speech-t2a-websocket
- 异步创建：https://platform.minimaxi.com/docs/api-reference/speech-t2a-async-create
- 异步查询：https://platform.minimaxi.com/docs/api-reference/speech-t2a-async-query

### Voice Management

- Get Voice：https://platform.minimaxi.com/docs/api-reference/voice-management-get
- Delete Voice：https://platform.minimaxi.com/docs/api-reference/voice-management-delete

### Voice Design

- Voice Design：https://platform.minimaxi.com/docs/api-reference/voice-design-design

### Voice Clone

- 上传复刻音频：https://platform.minimaxi.com/docs/api-reference/voice-cloning-uploadcloneaudio
- 上传 Prompt 音频：https://platform.minimaxi.com/docs/api-reference/voice-cloning-uploadprompt
- 创建克隆：https://platform.minimaxi.com/docs/api-reference/voice-cloning-clone
