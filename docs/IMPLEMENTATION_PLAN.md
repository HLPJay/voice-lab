# Voice Lab 实现计划

## 开发原则

P0 只做模块化单体，不做微服务、用户系统、计费系统、复杂前端、队列 Worker 或 Redis。

开发顺序必须先保证 Mock Provider 跑通，再接 MiniMax 真实调用。

## P0 任务拆解

### 1. 项目启动骨架 ✅ 已完成

目标：

- 创建 `app/main.py`
- 注册 FastAPI 应用
- 注册错误处理器
- 启动时创建数据库表
- 启动时写入默认 seed profile 和 binding

验收：✅

```text
uvicorn app.main:app --reload
GET /health -> {"status": "ok"}
```

### 2. API 路由 ✅ 已完成

目标：

- `app/api/health.py`
- `app/api/voice_profiles.py`
- `app/api/voice_render.py`
- `app/api/voice_variants.py`
- `app/api/voice_jobs.py`
- `app/api/voice_assets.py`

验收：✅

- API 层只调用 service，不直接拼 Provider 请求。
- 所有响应遵守 README 中的结构。

### 3. 数据库与必要 Repository ✅ 已完成

目标：

- P0 所需数据库表已创建。
- P0 已实现 `voice_profile_repo.py`，job、asset、variant 当前由 service/API 直接使用 SQLModel session。
- 保持业务逻辑主要在 service 层。
- 所有 JSON 字段统一用 `json.dumps(..., ensure_ascii=False)` 存储。

验收：✅

- seed 数据只在数据库为空时写入。
- 不重复创建默认 profile。
- job、asset、variant repository 可在 P1 或服务复杂度上升时补齐。

### 4. 单条语音生成 ✅ 已完成

目标：

- `POST /api/voice/render`
- 使用 `VoiceRenderService`
- 支持 `provider=mock`
- 支持显式 `provider=minimax`
- 保存 `AudioAsset`
- 可选保存 `SubtitleAsset`
- 更新 `VoiceJob` 状态

验收：✅

- Mock 请求成功返回 `job_id` 和 `audio_asset.url`。
- profile 不存在返回 `PROFILE_NOT_FOUND`。
- text 为空返回统一 `VALIDATION_ERROR` 格式。
- MiniMax API Key 缺失且请求 MiniMax 返回 `PROVIDER_NOT_CONFIGURED`。

### 5. 多版本试音 ✅ 已完成

目标：

- `POST /api/voice/variants/render`
- 默认串行生成。
- 默认组合：
  - `speed=0.85, emotion=sad`
  - `speed=0.92, emotion=calm`
  - `speed=1.00, emotion=neutral`

验收：✅

- 返回 `group_id`。
- 每个 variant 都有对应 `job_id`、`audio_asset_id`、`audio_url`。

### 6. 资产下载 ✅ 已完成

目标：

- `GET /api/voice/assets/{asset_id}`
- `GET /api/voice/assets/{asset_id}/download`
- 支持 audio asset 和 subtitle asset。

验收：✅

- 文件不存在返回 `ASSET_NOT_FOUND`（已修复 500 -> 404）。
- 下载接口返回文件流。

### 7. pytest ✅ 已完成

最低测试：

- `GET /health` ✅
- 文本预处理能插入停顿 ✅
- `RenderPlan` 能正确生成 ✅
- `MockSpeechAdapter` 能返回假音频资产 ✅
- `POST /api/voice/render` 使用 mock provider 成功 ✅
- profile 不存在返回错误 ✅
- text 为空返回错误 ✅

测试要求：✅

- 不依赖真实 MiniMax API。
- 测试数据库使用临时 SQLite。
- 测试 storage 使用临时目录。

pytest -q 结果：`11 passed`

## P1 计划

- MiniMax Voice Management 获取音色列表。
- 支持同步保存可用 `voice_id`。
- 支持 MiniMax `output_format=url` 时自动下载并落地。
- 支持字幕 JSON / SRT 更完整解析。
- 增加简单旁白试音台前端。
- 增加 Provider 能力注册表。

## P2 计划

- Voice Design。
- 异步长文本 T2A。
- Voice Clone。
- 多用户。
- 额度统计。
- API Key 管理。
- 对象存储。
- 队列 Worker。
- 评测反馈系统。
- 视频模块集成。

## 禁止事项

- 不要把 MiniMax API Key 写死在代码里。
- 不要让上层业务直接传 MiniMax `voice_setting`。
- 不要跳过 `RenderPlan`。
- 不要删除 Mock Provider。
- 不要把音频二进制塞进数据库。
- 不要让测试依赖真实外部 API。
- 不要在日志中打印 Authorization。
