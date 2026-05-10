# Voice Lab 声音中台

Voice Lab 是一个可扩展的声音生成中台，第一阶段面向 MiniMax `speech-2.8-hd` 同步 T2A 能力，但上层业务不直接依赖 MiniMax 字段。

目标不是写一个 `minimax_tts.py` 调用脚本，而是沉淀一套可被多个产品模块复用的声音服务：

```text
文案
-> 声音人设 VoiceProfile
-> 标准生成计划 RenderPlan
-> Provider Adapter
-> MiniMax / Mock / 未来其他模型
-> 音频资产 + 字幕时间轴 + 生成记录
```

## 当前状态

本仓库 P0 后端已达到可运行基线（commit `5b8d731`）。

已落地：

- FastAPI 应用入口 `app/main.py`
- API 路由目录 `app/api/`（health、profiles、render、variants、jobs、assets）
- SQLModel 数据模型
- 标准协议对象 `RenderPlan`
- `MockSpeechAdapter`（完整本地闭环）
- `MiniMaxSpeechAdapter`（同步 T2A，需真实 API Key）
- 文本预处理服务
- 单条生成与多版本生成服务层
- 资产保存服务
- pytest 测试（11 passed）
- 错误处理与 FastAPI exception handler
- 资产下载接口

P0 可运行基线验收通过：

- `GET /health` ✅
- `GET /api/voice/profiles` ✅ / `POST /api/voice/profiles` ✅
- `POST /api/voice/render` (provider=mock) ✅
- `POST /api/voice/variants/render` (provider=mock) ✅
- `GET /api/voice/jobs/{job_id}` ✅
- `GET /api/voice/assets/{asset_id}` ✅
- `GET /api/voice/assets/{asset_id}/download` ✅
- 错误边界：PROFILE_NOT_FOUND / PROVIDER_NOT_CONFIGURED / JOB_NOT_FOUND / ASSET_NOT_FOUND / VALIDATION_ERROR ✅

## 架构原则

1. 上层业务只关心场景、人设、文案、是否需要字幕和生成版本数。
2. MiniMax `voice_id`、`voice_setting`、`audio_setting` 等字段只允许出现在 Provider Adapter 内部。
3. `VoiceProfile` 是产品资产，`provider_voice_id` 只是某个 Provider 下的绑定实现。
4. 所有生成任务必须先形成内部标准协议 `RenderPlan`。
5. 所有生成结果必须保存为本地资产，不能长期依赖 MiniMax 24 小时临时 URL。
6. 测试必须使用 Mock Provider，不能依赖真实 MiniMax API Key。

## 推荐技术栈

- 后端：FastAPI
- 语言：Python 3.11+
- HTTP 客户端：httpx
- 数据库：SQLite
- ORM：SQLModel
- 配置：pydantic-settings + `.env`
- 文件存储：本地 `storage/`
- 测试：pytest

## 配置

复制配置文件：

```bash
cp .env.example .env
```

关键配置：

```env
VOICE_PROVIDER=minimax
MINIMAX_API_KEY=replace_me
MINIMAX_BASE_URL=https://api.minimax.io
MINIMAX_T2A_PATH=/v1/t2a_v2
MINIMAX_DEFAULT_MODEL=speech-2.8-hd
ENABLE_MOCK_PROVIDER=false
```

如果没有 `MINIMAX_API_KEY`，系统必须允许使用 `provider=mock` 跑通流程；但当显式请求 `provider=minimax` 时，必须返回明确的 `PROVIDER_NOT_CONFIGURED` 错误。

## P0 API 目标

P0 需要实现以下接口：

```text
GET  /health
GET  /api/voice/profiles
POST /api/voice/profiles
POST /api/voice/render
POST /api/voice/variants/render
GET  /api/voice/jobs/{job_id}
GET  /api/voice/assets/{asset_id}
GET  /api/voice/assets/{asset_id}/download
```

## Mock 调用示例

```bash
curl -X POST http://127.0.0.1:8000/api/voice/render \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我一直以为，是生活太难。后来才发现，真正让我害怕的是那个一直在逃避的自己。",
    "profile_id": "deep_night_programmer",
    "provider": "mock",
    "need_subtitle": true
  }'
```

目标返回：

```json
{
  "job_id": "job_xxx",
  "status": "success",
  "audio_asset": {
    "id": "audio_xxx",
    "url": "/api/voice/assets/audio_xxx/download",
    "duration_ms": 12345,
    "format": "wav"
  },
  "subtitle_asset": {
    "id": "subtitle_xxx",
    "url": "/api/voice/assets/subtitle_xxx/download",
    "timeline": []
  },
  "provider": "mock",
  "model": "speech-2.8-hd"
}
```

## 存储约定

生成文件必须保存到：

```text
storage/
  audio/YYYY-MM-DD/
  subtitles/YYYY-MM-DD/
  metadata/YYYY-MM-DD/
  temp/
```

数据库只保存路径、参数、任务记录和元数据，不保存音频二进制。

## 文档索引

- `docs/VOICE_LAB_GOALS.md`：目标归档与产品边界
- `docs/ARCHITECTURE.md`：架构标准与核心对象
- `docs/PROJECT_STRUCTURE.md`：项目目录结构、层边界与新增文件规则
- `docs/IMPLEMENTATION_PLAN.md`：分阶段实现计划
- `docs/CONTROL_AND_SAFETY.md`：完整性检查、测试策略与安全控制
- `docs/COMPLETENESS_REVIEW.md`：当前项目完整性检查结果与阻断问题
- `docs/HANDOFF.md`：当前未完成事项与接手说明
