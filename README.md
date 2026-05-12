# Voice Lab 声音中台

Voice Lab 是一个可扩展的声音生成中台，支持 MiniMax T2A（Text-to-Audio）全系列接口，同时通过 Provider Adapter 模式保持上层业务与具体厂商解耦。

```
文案 → VoiceProfile → RenderPlan → Provider Adapter → MiniMax / Mock / 未来厂商
                                                          ↓
                                              音频资产 + 字幕时间轴 + 生成记录
```

## 已支持的 MiniMax 接口

| 功能 | MiniMax API | Voice Lab API |
|------|-------------|---------------|
| 同步 T2A | `POST /v1/t2a_v2` | `POST /api/voice/render` |
| 异步 T2A | `POST /v1/t2a_async_v2` | `POST /api/voice/render/async` |
| 异步状态查询 | `GET /v1/query/t2a_async_query_v2` | `GET /api/voice/render/async/{job_id}/status` |
| 文件上传 | `POST /v1/files/upload` | `POST /api/voice/clone/upload` |
| 声音克隆 | `POST /v1/voice_clone` | `POST /api/voice/clone/create` |
| 声音设计 | `POST /v1/voice_design` | `POST /api/voice/design/create` |
| 声音删除 | `POST /v1/delete_voice` | `POST /api/voice/voices/delete` |
| 音色列表 | `POST /v1/get_voice` | `GET /api/voice/provider-voices` |
| 文件下载 | `GET /v1/files/retrieve` | 内部调用（异步T2A完成时自动下载） |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入 MiniMax API Key：

```env
MINIMAX_API_KEY=your_real_api_key_here
```

如果没有 API Key，可以使用 `provider=mock` 运行全部流程。

### 3. 启动服务

```bash
uvicorn app.main:app --reload
```

访问 http://127.0.0.1:8000/static/index.html 打开测试面板（4个Tab：T2A生成 / 音色管理 / 声音克隆 / 声音设计）。

## API 一览

### 语音生成

```
POST /api/voice/render              # 同步T2A（短文本，即时返回音频）
POST /api/voice/render/async        # 异步T2A（长文本，返回job_id）
GET  /api/voice/render/async/{id}/status  # 轮询异步任务状态
POST /api/voice/variants/render     # 多版本试音（多组参数批量生成）
```

### 声音管理

```
POST /api/voice/clone/upload        # 上传克隆/Prompt音频文件
POST /api/voice/clone/create        # 执行声音克隆
POST /api/voice/design/create       # 文字描述生成声音
POST /api/voice/voices/delete       # 删除克隆/设计声音
GET  /api/voice/provider-voices     # 查询音色列表（支持缓存+刷新）
```

### Profile & Binding

```
GET  /api/voice/profiles            # 查询声音人设
POST /api/voice/profiles            # 创建声音人设
GET  /api/voice/profiles/{id}/bindings  # 查询绑定列表
POST /api/voice/profiles/{id}/bindings  # 创建绑定
PATCH /api/voice/bindings/{id}      # 更新绑定
DELETE /api/voice/bindings/{id}     # 删除绑定（软删除）
```

### 任务与资产

```
GET  /api/voice/jobs/{job_id}            # 查询任务详情
GET  /api/voice/assets/{asset_id}        # 查询资产元信息
GET  /api/voice/assets/{asset_id}/download  # 下载音频/字幕文件
```

## 调用示例

### 同步 T2A（Mock）

```bash
curl -X POST http://127.0.0.1:8000/api/voice/render \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是一段测试语音。",
    "provider": "mock",
    "need_subtitle": true
  }'
```

### 异步 T2A（MiniMax）

```bash
# 1. 提交任务
curl -X POST http://127.0.0.1:8000/api/voice/render/async \
  -H "Content-Type: application/json" \
  -d '{"text": "这是一段较长的文本...", "provider": "minimax"}'

# 2. 轮询状态（用返回的 job_id）
curl http://127.0.0.1:8000/api/voice/render/async/job_xxx/status
```

### 声音克隆（MiniMax）

```bash
# 1. 上传音频文件
curl -X POST http://127.0.0.1:8000/api/voice/clone/upload \
  -F "file=@sample.mp3" \
  -F "purpose=voice_clone" \
  -F "provider=minimax"

# 2. 执行克隆（用返回的 file_id）
curl -X POST http://127.0.0.1:8000/api/voice/clone/create?provider=minimax \
  -H "Content-Type: application/json" \
  -d '{"voice_id": "my_cloned_voice", "file_id": "xxx"}'
```

## 测试

### Mock 测试（无需 API Key）

```bash
python -m pytest tests/ -x -q
```

当前：235 passed, 6 skipped

### E2E 真实 API 测试

需要在 `.env` 中配置有效的 `MINIMAX_API_KEY`：

```bash
python -m pytest tests/ -m e2e -x -v
```

覆盖 6 个端到端场景：同步T2A、异步T2A轮询、音色列表、声音设计、克隆上传、声音删除。

## 架构设计

### 三层架构

```
┌─────────────────────────────────┐
│  User API Layer (Voice Lab)     │  ← 产品语义，不含厂商字段
├─────────────────────────────────┤
│  Provider Adapter Layer         │  ← 厂商协议翻译
├─────────────────────────────────┤
│  MiniMax / Mock / Future        │  ← 底层大模型 API
└─────────────────────────────────┘
```

### 核心原则

1. **上层业务只关心场景、人设、文案**，不感知 MiniMax `voice_id`、`voice_setting` 等字段
2. **所有生成任务必须经过 RenderPlan**，标准化输入参数后交给 Provider
3. **所有生成结果保存为本地资产**，不依赖 MiniMax 24小时临时 URL
4. **Provider 通过 Registry 注册和验证**，上层无 Provider 特定逻辑
5. **Mock Provider 完整闭环**，开发和测试不依赖真实 API

### 技术栈

| 组件 | 选型 |
|------|------|
| 后端框架 | FastAPI |
| 语言 | Python 3.11+ |
| HTTP 客户端 | httpx |
| 数据库 | SQLite |
| ORM | SQLModel |
| 配置管理 | pydantic-settings + `.env` |
| 文件存储 | 本地 `storage/` |
| 测试 | pytest |

## 存储结构

```
storage/
  audio/YYYY-MM-DD/       # 音频文件
  subtitles/YYYY-MM-DD/   # 字幕文件（JSON + SRT）
  metadata/YYYY-MM-DD/    # 元数据
  temp/                   # 临时文件
```

数据库只保存路径、参数、任务记录和元数据，不保存音频二进制。

## 配置说明

所有配置通过 `.env` 文件管理，关键项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MINIMAX_API_KEY` | — | MiniMax API密钥，缺失时仅 mock 可用 |
| `MINIMAX_BASE_URL` | `https://api.minimaxi.com` | MiniMax API 基地址 |
| `MINIMAX_DEFAULT_MODEL` | `speech-2.8-hd` | 默认语音模型 |
| `MINIMAX_TIMEOUT_SECONDS` | `120` | API 请求超时 |
| `DEFAULT_AUDIO_FORMAT` | `mp3` | 默认音频格式 |
| `CLONE_AUDIO_MAX_SIZE_MB` | `20` | 克隆音频最大文件大小 |
| `CLONE_AUDIO_MIN_DURATION_SEC` | `10` | 克隆音频最短时长 |
| `CLONE_AUDIO_MAX_DURATION_SEC` | `300` | 克隆音频最长时长 |

## 文档索引

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — 架构标准与核心对象
- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) — 项目目录结构与层边界
- [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) — 分阶段实现计划（P0-P2）
- [MINIMAX_OFFICIAL_REFERENCES.md](docs/MINIMAX_OFFICIAL_REFERENCES.md) — MiniMax 官方 API 参考
- [HANDOFF.md](docs/HANDOFF.md) — 当前状态与接手说明
- [CONTROL_AND_SAFETY.md](docs/CONTROL_AND_SAFETY.md) — 测试策略与安全控制
