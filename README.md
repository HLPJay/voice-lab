# Voice Lab 本地 AI 音频创作工作台

Voice Lab 是一个基于 MiniMax 音频能力构建的本地 AI 音频创作工作台，当前面向单用户、本地 Web App、个人创作者音频生产场景。

**当前不是**：多人 SaaS / 高并发多人使用 / 开放 API 平台 / 含登录系统的产品
**当前是**：本地 Web App / 单用户 / 个人创作者音频工作台

```
文案 → VoiceProfile → RenderPlan → Provider Adapter → MiniMax / Mock
                                                    ↓
                                    音频资产 + 字幕时间轴 + 生成记录
```

## 当前主导航

- 创作工作台
- 长文本
- 剧本
- 音色
- 历史
- 高级

## 已支持的 MiniMax 接口

| 功能 | MiniMax API | Voice Lab API |
|------|-------------|---------------|
| 同步 T2A | `POST /v1/t2a_v2` | `POST /api/voice/render` |
| 异步 T2A | `POST /v1/t2a_async_v2` | `POST /api/voice/render/async` |
| 异步状态查询 | `GET /v1/query/t2a_async_query_v2` | `GET /api/voice/render/async/{job_id}/status` |
| **WebSocket 流式 T2A** | `WebSocket /v1/t2a_v2` | `WebSocket /api/voice/render/stream` |
| 文件上传 | `POST /v1/files/upload` | `POST /api/voice/clone/upload` |
| 声音克隆 | `POST /v1/voice_clone` | `POST /api/voice/clone/create` |
| 声音设计 | `POST /v1/voice_design` | `POST /api/voice/design/create` |
| 声音删除 | `POST /v1/delete_voice` | `POST /api/voice/voices/delete` |
| 音色列表 | `POST /v1/get_voice` | `GET /api/voice/provider-voices` |
| 文件下载 | `GET /v1/files/retrieve` | 内部调用（异步 T2A 完成时自动下载） |

## 当前已支持能力

### 语音生成

- 同步 T2A（短文本即时返回）
- 异步 T2A（长文本，返回 job_id）
- WebSocket 流式 T2A（实时流式返回）
- 多版本试音（多组参数批量生成）
- 字幕生成（json + srt 成对输出）
- 音频本地保存
- 音频下载

### 长文本与剧本

- 长文本分段生成（自动分句）
- 批量任务（多段并行提交）
- 多角色剧本生成
- 失败段重试
- 成功段复用（避免重复生成）
- 音频合并
- 字幕合并
- partial / failed / completed 状态追踪

### 音色与声音资产

- VoiceProfile（声音人设）
- ProviderVoice（provider 层音色）
- VoiceBinding（人设与音色绑定）
- 音色试听（WebSocket 流式）
- 音色绑定与解绑
- 绑定状态展示
- provider voice 缓存（避免重复请求）
- 删除音色后本地 provider_voice / binding 软失效

### 历史与资产

- 历史任务查询
- 历史播放
- 历史下载
- 任务详情
- 音频资产查询（AudioAsset）
- 字幕资产查询（SubtitleAsset）
- 历史任务软删除
- localStorage 最近任务恢复

### 成本与安全保护

- Cost Guard（成本追踪）
- 高消费动作二次确认
- Resource Guard 友好提示
- Provider 调用日志
- Admin 统计面板
- ProviderVoice 状态校验
- Mock Provider 完整闭环测试

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

访问 http://127.0.0.1:8000/static/index.html 打开 Voice Lab。

## API 一览

### 语音生成

```
POST /api/voice/render              # 同步 T2A（短文本，即时返回音频）
POST /api/voice/render/async        # 异步 T2A（长文本，返回 job_id）
GET  /api/voice/render/async/{id}/status  # 轮询异步任务状态
WS   /api/voice/render/stream       # WebSocket 流式 T2A
POST /api/voice/variants/render     # 多版本试音（多组参数批量生成）
```

### 声音管理

```
POST /api/voice/clone/upload        # 上传克隆/Prompt 音频文件
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

### 全量测试

```bash
python -m pytest tests/ -x -q
```

当前测试基线：

tests/: 496 passed, 6 skipped

**新增能力里程碑：**

- P8-SEG1 已新增"每行一段"长文本分段策略（line segment strategy）
- P8-VALIDATION2-A 已完成后端 Schema 收紧与 TextSegmentService 硬切兜底
- P8-VALIDATION2-B 已完成前端高风险输入约束补齐（maxlength、正整数校验、200 行剧本限制）
- P8-VALIDATION2-C 已完成 422 字段级错误提示中文化
- 当前仍不是多人 SaaS，不是开放 API 平台，不适合直接公网暴露

### 资产清理专项测试

```bash
python -m pytest tests/test_cleanup_assets_dry_run.py -q        # 31 passed
python -m pytest tests/test_cleanup_assets_quarantine.py -q     # 24 passed
```

### E2E 真实 API 测试

需要在 `.env` 中配置有效的 `MINIMAX_API_KEY`：

```bash
python -m pytest tests/ -m e2e -x -v
```

## 资产清理运维工具

**当前不是自动任务。** 项目启动后不会自动 dry-run、不会自动 quarantine、不会自动 purge、不会自动删除任何文件、不会自动修改数据库。

### 当前支持的手动命令

**dry-run（只生成计划，不移动/删除文件）：**

```bash
python scripts/cleanup_assets.py \
  --dry-run \
  --kind orphan \
  --min-age-days 7 \
  --max-files 1000
```

**quarantine（将候选文件隔离到 quarantine/，生成 manifest.json）：**

```bash
python scripts/cleanup_assets.py \
  --quarantine \
  --plan docs/generated/asset_cleanup_dry_run.json \
  --confirm QUARANTINE
```

**restore（从 manifest.json 恢复 quarantine 文件）：**

```bash
python scripts/cleanup_assets.py \
  --restore \
  --manifest storage/quarantine/<timestamp>/manifest.json \
  --confirm RESTORE
```

### 资产清理原则

- **DB 引用资产** = 用户资产，默认永久保留，清理工具禁止处理
- **orphan 文件** = 系统残留候选，只能先 dry-run，不直接删除
- **subtitle 必须 json + srt 成对处理**，不能只删其中一个
- **quarantine 使用 move 语义**，不是 copy（源文件被移走）
- **restore 可恢复** quarantine 文件（move 回原始位置）
- **purge 当前未实现**，作为后续 P8-BE3E 或更后阶段
- **purge 需要 30 天隔离观察期** 后再考虑

### 后续可接入方向

以下为后续方向，**不是当前已实现**：

- Admin 页面展示 dry-run 报告
- 每周定时自动 dry-run，只读生成报告
- Admin 手动确认后执行 quarantine
- quarantine 满 30 天后考虑 purge
- purge 必须单独阶段实现，不能混入其他阶段

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
6. **文件清理必须先 dry-run、再 quarantine、再考虑 purge**，不能跳过阶段

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
  audio/YYYY-MM-DD/              # 音频文件
  subtitles/YYYY-MM-DD/           # 字幕文件（JSON + SRT 成对）
  metadata/YYYY-MM-DD/            # 元数据
  temp/                          # 临时文件（清理时优先）
  quarantine/<timestamp>/         # 隔离文件 + manifest.json
```

- 数据库只保存路径、参数、任务记录和元数据，不保存音频二进制
- quarantine 下保存被隔离文件和 manifest.json，支持 restore

## 配置说明

所有配置通过 `.env` 文件管理，关键项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MINIMAX_API_KEY` | — | MiniMax API 密钥，缺失时仅 mock 可用 |
| `MINIMAX_BASE_URL` | `https://api.minimaxi.com` | MiniMax API 基地址 |
| `MINIMAX_DEFAULT_MODEL` | `speech-2.8-hd` | 默认语音模型 |
| `MINIMAX_TIMEOUT_SECONDS` | `120` | API 请求超时 |
| `DEFAULT_AUDIO_FORMAT` | `mp3` | 默认音频格式 |
| `CLONE_AUDIO_MAX_SIZE_MB` | `20` | 克隆音频最大文件大小 |
| `CLONE_AUDIO_MIN_DURATION_SEC` | `10` | 克隆音频最短时长 |
| `CLONE_AUDIO_MAX_DURATION_SEC` | `300` | 克隆音频最长时长 |

## 当前边界

**当前不支持：**

- 多人 SaaS / 高并发多人使用
- 登录系统 / 用户体系
- BYOK（Bring Your Own Key）
- 开放 API 平台
- Redis / PostgreSQL / worker 队列
- 自动资产清理（当前为手动运维工具）
- 自动 purge
- 多设备同步

## 输入约束与错误提示

Voice Lab 当前已建立三层输入约束机制：

1. **后端 Schema 兜底**：限制文本长度、枚举值、正整数 ID、分段策略等，非法参数在进入核心链路前被拒绝。
2. **前端输入防护**：根据后端约束补齐 maxlength、min、pattern、按钮 disabled 和行级提示，减少用户提交非法请求。
3. **422 字段级错误提示**：当 FastAPI/Pydantic 返回参数校验错误时，前端会将字段路径和错误类型翻译为中文提示，例如"file_id：必须大于 0。"、"第 1 行台词：不能为空。"。

这套机制是后续 Provider Capability Registry 的前置基础，未来会进一步演进为按 Provider / Model 能力动态约束前端和后端请求。

## Provider Capability Registry

Voice Lab 通过只读能力注册表声明各 Provider 支持的能力，不走数据库，不调用 Provider 真实接口，不作为健康探测。

### 接口

```
GET /api/voice/capabilities                    # 返回所有 provider 能力列表
GET /api/voice/capabilities?provider=minimax  # 返回指定 provider 能力
```

### 能力维度

| 维度 | 说明 |
|------|------|
| `tts` | 同步/异步/流式 TTS 支持的模型、文本长度、音频格式、字幕、流式、情绪参数范围 |
| `batch` | 长文本批量支持的策略、每段最大字数、段间静音范围 |
| `script` | 剧本批量支持的策略（当前固定为 line） |
| `voice_clone` | 克隆支持的状态、voice_id 约束、降噪/音量标准化、文件大小限制 |
| `voice_design` | 声音设计支持的状态、prompt 最大长度、voice_id 约束 |
| `provider_voices` | 音色列表、删除、导入的支持状态 |

第一版能力声明来自代码配置（`app/providers/mock_capabilities.py` / `app/providers/minimax_capabilities.py`）。后续 P9-CAPABILITY2 会基于能力声明实现 CapabilityValidator，在进入 Provider Adapter 前拒绝不支持的参数；P9-CAPABILITY3 会让前端根据能力动态限制输入。

## 后续路线

1. **P9-CAPABILITY1：Provider Capability Registry**：定义 Product Contract / Capability Contract / Provider Capability / Adapter Protocol Contract；为 mock / minimax 声明能力；增加 `/api/voice/capabilities` 查询接口；前端未来可根据 provider/model 能力动态限制输入；后端未来可通过 CapabilityValidator 在进入 Provider Adapter 前拒绝不支持的参数。
2. **Project / 作品概念**：将每次创作归档为独立 Project
2. **创作模板入口**：情绪独白、长文本朗读、多角色剧本
3. **历史记录升级为资产库**：重命名、收藏、标签、搜索
4. **手机端 H5 快速创作**：轻量入口
5. **Audio Capability Gateway 抽象**：统一音频能力接口，支持更多 Provider
6. **资产清理后续接入**：Admin dry-run 报告 → 人工确认 quarantine → 30 天后 purge
7. **更多 Provider**：OpenAI TTS、Azure Speech、ElevenLabs、本地 CosyVoice / GPT-SoVITS

## 文档索引

- [PROJECT_HEALTH_CHECK.md](docs/PROJECT_HEALTH_CHECK.md) — 项目健康检查与当前状态
- [P8_BE3D_ASSET_QUARANTINE.md](docs/P8_BE3D_ASSET_QUARANTINE.md) — 资产 quarantine/restore 工具说明
- [CONTROL_AND_SAFETY.md](docs/CONTROL_AND_SAFETY.md) — 测试策略与安全控制
- [MINIMAX_OFFICIAL_REFERENCES.md](docs/MINIMAX_OFFICIAL_REFERENCES.md) — MiniMax 官方 API 参考
- [HANDOFF.md](docs/HANDOFF.md) — 接手说明与当前状态

以下为历史文档（已部分过时，仅作参考）：

- ARCHITECTURE.md — 早期架构说明
- PROJECT_STRUCTURE.md — 早期目录结构
- IMPLEMENTATION_PLAN.md — 早期实现计划（P0-P2）
