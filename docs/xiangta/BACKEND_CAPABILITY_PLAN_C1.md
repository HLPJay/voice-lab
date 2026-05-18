# XiangTa Backend Capability Plan C1

## 1. 阶段定位

B9 已验证 XiangTa 能通过 Core HTTP API 调用音频能力。

但 XiangTa 仍不是产品级后端。下一阶段目标不是继续堆接口，而是补齐产品后端能力层：配置、存储、队列、LLM、安全、错误、可观测性、用户体系预留。

**当前系统定位：本地单用户 / 轻量多浏览器产品验证阶段。**
**当前不承诺多人 SaaS、高并发、多租户、正式用户系统。**

---

## 2. 当前架构基线

```
app/**
= Voice Lab Core
= 音频能力底座
= profile / binding / provider / render / asset / job

src/xiangta/**
= XiangTa 产品服务层
= 产品语义 API
= 通过 HTTP 调用 Core 上层 API
= 不直接调用 Provider / Repository / Core Service

apps/xiangta-h5/**
= XiangTa H5 前端
= 用户输入、选择、生成、播放

apps/xiangta_runtime/**
= XiangTa 本地 runtime
= 挂载 H5 静态页面与 /api/xiangta/*
```

**XiangTa 不修改 Core。**
**XiangTa 不 import app.providers / app.repositories / app.services。**
**XiangTa 不读取真实 Provider API key。**
**XiangTa 只通过 Core HTTP API 使用底座能力。**

---

## 3. Backend Capability Map

| 能力 | 当前状态 | 为什么需要 | 短期目标 | 长期目标 | 当前是否实现 |
|---|---|---|---|---|---|
| Runtime Config | 环境变量 | 手工验证用，生产需可配置化 | runtime.json + env override | 动态配置 Admin 界面 | 否 |
| Storage / Data Model | 进程内内存 | letters 重启丢失，不可查询 | SQLite 起步 | PostgreSQL 多租户 | 否 |
| TTS Task Queue | 同步调用 | 长文本/移动端/重复点击需要异步 | in-memory queue + task table | Redis + worker | 否 |
| LLM Copywriting | 模板版 | 提升文案质量和场景适配 | LLM gateway + template fallback | 多 provider 路由 | 否 |
| Profile Mapping | JSON 静态配置 | B9 直接选 profileId 不适合普通用户 | Admin 界面配置 | 自动化音色推荐 | 部分 |
| Error Contract | 散落在 ErrorTranslator | 前端无法统一处理 | 统一错误 schema + errorKind | 错误码文档 | 部分 |
| Security Baseline | 无 | 面向用户前必须 | Input validation / XSS / SQLi | CSP / CORS / RBAC | 部分 |
| Observability | 无 | 排查问题需要 | structured logging | metrics + tracing | 否 |
| User / Auth / RBAC | 无 | 多用户需要 | user_id nullable 设计 | 注册/登录/会话/RBAC | 否 |
| API Contract Governance | 无 | 前后端耦合/版本漂移 | API 文档化 + 前端稳定契约 | OpenAPI + breaking change 策略 | 部分 |

---

## 4. Runtime Config Plan

### 4.1 当前问题

当前 Core base URL 通过 `XIANGTA_CORE_BASE_URL` 环境变量配置。这适合手工 smoke，但长期不适合作为产品配置体系。

### 4.2 推荐配置优先级

```
内置默认值 → src/xiangta/configs/runtime.json → 环境变量覆盖
```

优先级：`env > runtime.json > default`

### 4.3 示例 runtime.json

```json
{
  "core": {
    "enabled": true,
    "baseUrl": "http://127.0.0.1:8000",
    "timeoutSecs": 20
  },
  "copywriting": {
    "mode": "template",
    "provider": "none",
    "timeoutSecs": 20,
    "fallbackToTemplate": true
  },
  "tts": {
    "mode": "sync",
    "maxConcurrent": 1,
    "queueEnabled": false,
    "timeoutSecs": 120
  },
  "storage": {
    "type": "sqlite",
    "databaseUrl": "sqlite:///./data/xiangta.db"
  },
  "features": {
    "devCoreProfileSelect": true,
    "lettersEnabled": true,
    "llmCopywritingEnabled": false,
    "ttsTaskEnabled": false
  }
}
```

### 4.4 Secret 边界

**允许进入 runtime.json：**

```
baseUrl
timeout
feature flag
mode
concurrency
storage path
UI/dev 开关
```

**禁止进入 runtime.json：**

```
MINIMAX_API_KEY
MIMO_API_KEY
OPENAI_API_KEY
DEEPSEEK_API_KEY
任何真实 secret
```

Core Provider API key 仍归 Core 管理。XiangTa 不读取 Core Provider key。如果 XiangTa 后续接 LLM，其 LLM API key 也不进入 repo 配置文件。

---

## 5. Storage / Data Model Plan

当前 `letters` 是进程内内存，只适合 MVP。产品化需要 SQLite 起步。后续如果进入多人 SaaS，再考虑 PostgreSQL。

### 5.1 letters

| 字段 | 类型 | 说明 |
|---|---|---|
| letter_id | TEXT PK | UUID |
| user_id | TEXT NULL | 未来用户体系预留，当前为空 |
| recipient | TEXT | lover/family/friend/self |
| scene | TEXT | miss/sorry/thanks/comfort/night |
| style | TEXT | restrained/gentle/sincere |
| raw_text | TEXT | 用户输入原文 |
| final_text | TEXT | 最终发送文案 |
| voice_preset | TEXT | female-gentle/male-gentle/... |
| profile_id | TEXT NULL | Core profile ID（B9 路径） |
| tone | TEXT | gentle/sincere/restrained/... |
| audio_url | TEXT NULL | Core audio 绝对 URL |
| duration_ms | INTEGER NULL | 音频时长 |
| title | TEXT NULL | 信笺标题 |
| favorited | INTEGER | 0/1 布尔 |
| created_at | TEXT | ISO 8601 |
| updated_at | TEXT | ISO 8601 |
| deleted_at | TEXT NULL | 软删除时间戳 |

### 5.2 tts_tasks

| 字段 | 类型 | 说明 |
|---|---|---|
| task_id | TEXT PK | UUID |
| user_id | TEXT NULL | 未来用户体系预留 |
| status | TEXT | queued/running/completed/failed/cancelled/expired |
| text | TEXT | TTS 文案 |
| recipient | TEXT | 收信人 |
| scene | TEXT | 场景 |
| voice_preset | TEXT | 音色预设 |
| profile_id | TEXT NULL | Core profile ID |
| tone | TEXT | 语调 |
| audio_url | TEXT NULL | 完成后音频 URL |
| duration_ms | INTEGER NULL | 音频时长 |
| error_kind | TEXT NULL | 错误类型 |
| error_message | TEXT NULL | 用户可理解错误信息 |
| retryable | INTEGER | 0/1 |
| created_at | TEXT | ISO 8601 |
| started_at | TEXT NULL | 开始执行时间 |
| completed_at | TEXT NULL | 完成时间 |
| failed_at | TEXT NULL | 失败时间 |
| expired_at | TEXT NULL | 过期时间 |

### 5.3 copywriting_jobs

| 字段 | 类型 | 说明 |
|---|---|---|
| request_id | TEXT PK | UUID |
| user_id | TEXT NULL | 未来用户体系预留 |
| recipient | TEXT | 收信人 |
| scene | TEXT | 场景 |
| raw_text | TEXT | 用户原文 |
| mode | TEXT | template/llm/llm_with_template_fallback |
| provider | TEXT NULL | minimax/openai/deepseek/... |
| status | TEXT | pending/success/failed |
| suggestions_json | TEXT NULL | 建议文案 JSON |
| error_kind | TEXT NULL | 错误类型 |
| error_message | TEXT NULL | 错误信息 |
| created_at | TEXT | ISO 8601 |
| completed_at | TEXT NULL | 完成时间 |

### 5.4 voice_preset_mappings

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | female-gentle/male-bright/... |
| label | TEXT | 展示名称 |
| desc | TEXT | 描述 |
| core_profile_id | TEXT | 映射到 Core profile ID |
| enabled | INTEGER | 0/1 布尔 |
| sort_order | INTEGER | 排序 |
| recommended_scenes_json | TEXT | JSON 数组 |
| suitable_recipients_json | TEXT | JSON 数组 |
| default_tone | TEXT | 默认语调 |
| provider_policy | TEXT NULL | default/mock/minimax/... |
| render_overrides_json | TEXT | JSON 对象 |
| created_at | TEXT | ISO 8601 |
| updated_at | TEXT | ISO 8601 |

### 5.5 app_settings

短期配置仍使用 JSON 文件。后续如果需要 Admin 页面动态修改配置，可引入 `app_settings` 表：

| 字段 | 类型 | 说明 |
|---|---|---|
| key | TEXT PK | 配置 key |
| value | TEXT | JSON 值 |
| updated_at | TEXT | 更新时间 |

---

## 6. TTS Task Queue Plan

### 6.1 当前同步链路问题

`POST /api/xiangta/tts` 当前同步等待 Core render。适合本地验证，不适合产品级多请求、重复点击、长文本、移动端网络波动。

### 6.2 未来 API 设计

```
POST /api/xiangta/tts/tasks
Body: { text, voicePreset, tone, recipient, scene, profileId? }
Response: { taskId, status: "queued", createdAt }

GET /api/xiangta/tts/tasks/{taskId}
Response: { taskId, status, audioUrl?, durationMs?, errorKind?, errorMessage? }

POST /api/xiangta/tts/tasks/{taskId}/cancel  # 后续可选
```

### 6.3 状态定义

```
queued    — 任务已创建，等待执行
running   — 正在调用 Core render
completed — Core render 成功，audioUrl 已返回
failed    — Core render 失败或超时
cancelled — 用户主动取消
expired   — 任务超时未完成（如 30 分钟）
```

### 6.4 最小并发策略

```
单用户同时运行 1 个 TTS task
全局同时运行 1~2 个真实 TTS 调用
队列最大长度默认 10
任务 TTL 默认 30 分钟
失败默认不自动重试，用户手动重试
```

### 6.5 实现阶段建议

**第一阶段**：不引入 Redis / Celery。先用单进程 in-memory queue 验证 API 和前端轮询。
**第二阶段**：落 SQLite task table，支持重启后任务状态恢复。
**第三阶段**：如进入多人部署，再考虑 Redis / worker。

### 6.6 Core / XiangTa 职责划分

```
Core 负责：Provider 级资源保护、cost guard、asset 保存
XiangTa 负责：产品级 task 状态、前端轮询、重复点击防护、用户可理解错误
```

---

## 7. LLM Copywriting Gateway Plan

### 7.1 当前状态

当前 `/suggestions` 是模板版。后续文案生成应接入大模型，但必须保留 template fallback。

### 7.2 推荐架构

```
CopywritingService
  → CopywritingGateway
    → TemplateCopywriter
    → LlmCopywriter
  → OutputValidator
  → fallback template
```

### 7.3 输入设计

```json
{
  "recipient": "lover",
  "scene": "miss",
  "rawText": "好想你呀今天",
  "tone": "gentle",
  "style": "sincere",
  "relationshipContext": "正在异地恋"
}
```

### 7.4 输出结构（保持前端稳定）

```json
{
  "summary": "生成 3 条文案建议",
  "intent": "想念",
  "suggestions": [
    {
      "style": "gentle",
      "styleLabel": "温柔一点",
      "text": "...",
      "fitsFor": "适合深夜独白",
      "charCount": 42
    }
  ]
}
```

### 7.5 安全策略

```
LLM 输出必须 JSON schema 校验
LLM 失败/超时/格式错误时 fallback template
不让 LLM 决定 provider、URL、API key、系统配置
用户输入和系统 prompt 分离
```

### 7.6 配置

```json
copywriting.mode = "template" | "llm" | "llm_with_template_fallback"
copywriting.provider = "none" | "minimax" | "openai" | "deepseek"
copywriting.timeoutSecs = 20
copywriting.fallbackToTemplate = true
```

**本阶段不实现 LLM 接入。**

---

## 8. Profile Mapping Plan

### 8.1 当前状态

B9 为链路验证，H5 直接选择 Core profileId。正式产品中普通用户不应直接看到 Core profileId。

### 8.2 未来结构

```
voicePreset → coreProfileId → Core render
```

示例 `voice_preset_mappings` 配置：

```json
{
  "id": "night-male",
  "label": "深夜男声",
  "desc": "低沉、克制，适合深夜想念和独白",
  "coreProfileId": "deep_night_programmer",
  "recommendedScenes": ["miss", "night", "comfort"],
  "suitableRecipients": ["lover", "self"],
  "defaultTone": "gentle",
  "enabled": true
}
```

### 8.3 API 路径

```
/api/xiangta/core/profiles  — dev/admin 可用，调试用
/api/xiangta/voice-presets  — 普通 H5 用，映射后产品语义
/api/xiangta/admin/voice-mappings  — admin 配置用
```

---

## 9. Error Contract Plan

### 9.1 统一错误响应结构

```json
{
  "ok": false,
  "errorKind": "provider_quota",
  "message": "语音生成额度暂时不可用，请稍后再试。",
  "retryable": true,
  "requestId": "req_abc123",
  "taskId": "task_xyz789"
}
```

### 9.2 错误类型

| errorKind | 说明 | retryable |
|---|---|---|
| validation_error | 输入参数校验失败 | false |
| core_unavailable | Core 服务不可达 | true |
| profile_not_found | 指定的人设不存在 | false |
| voice_binding_missing | 音色绑定缺失 | false |
| provider_quota | Provider 额度不可用 | true |
| provider_error | Provider 返回错误 | true |
| tts_timeout | TTS 生成超时 | true |
| copywriting_timeout | 文案生成超时 | true |
| copywriting_invalid_output | LLM 输出格式无效 | true |
| storage_error | 存储操作失败 | false |
| rate_limited | 请求频率超限 | true |
| unauthorized | 未授权 | false |
| forbidden | 无权限 | false |
| unknown | 未知错误 | false |

### 9.3 翻译策略

前端不应该直接处理 Core 原始错误。XiangTa 后端负责把技术错误翻译成用户可理解错误。

---

## 10. Security Baseline Plan

### 10.1 Input Validation

```
所有 API 输入必须经过 Pydantic schema
限制 text/rawText/finalText/title 长度（max 500~800）
recipient/scene/tone/voicePreset 必须枚举或配置校验
profileId 仅 dev/admin 路径允许长期暴露
```

### 10.2 SQL Injection

```
使用 ORM / SQLModel
避免 raw SQL
如果后续支持搜索/排序，字段必须 whitelist
```

### 10.3 XSS

```
用户输入不返回 HTML
H5 渲染时必须 escape
后续考虑 Content-Security-Policy
```

### 10.4 Prompt Injection

```
LLM 接入后，用户输入不能改变系统规则
Prompt 与用户输入分离
LLM 输出必须 schema 校验
不允许 LLM 输出 provider/API key/系统配置
```

### 10.5 Rate Limit / Cost Abuse

```
限制单用户/单 IP 生成频率
限制每日生成次数
限制 TTS task queue 长度
限制文本长度
保留 cost guard 失败的用户可理解提示
```

### 10.6 Path Traversal / Asset Access

```
XiangTa 不代理 Core assets 时风险较低
如果后续代理文件下载，必须校验 storage root，禁止 ../ 路径穿越
```

### 10.7 Secret Leakage

```
不在日志打印 API key
错误响应不返回 stack trace
前端不暴露 provider config
配置文件不提交真实 secret
```

### 10.8 CORS / CSRF

```
当前本地同源问题较小
如果未来前后端分离，需要 CORS whitelist
如果使用 cookie session，需要 CSRF/SameSite 策略
```

---

## 11. Observability Plan

### 11.1 结构化日志字段

```
request_id
task_id
user_id nullable
provider
profile_id
voice_preset
latency_ms
status
error_kind
retryable
```

### 11.2 日志类型

```
API access log        — 每个请求
TTS task log          — 每个 TTS 任务
LLM generation log    — 每个文案生成
Core gateway log      — Core HTTP 调用
storage log           — DB 操作
security/audit log    — 异常行为
```

### 11.3 后续 Admin 指标

```
今日生成次数
成功率
失败原因分布
平均耗时
provider 调用次数
LLM fallback 次数
用户活跃数
```

---

## 12. Future User / Auth / RBAC Plan

### 12.1 当前状态

当前不实现用户注册。当前仍是本地单用户产品验证。但数据模型应预留 `user_id nullable`。

### 12.2 后续用户体系

```
用户注册
登录（手机号/邮箱）
会话管理
用户资料
账号状态（正常/封禁）
注销
数据隔离
```

### 12.3 权限角色

```
anonymous/local  — 本地用户，未登录
user             — 注册用户，普通权限
admin            — 配置管理权限
developer        — 调试/查看 Core 状态
```

### 12.4 权限边界

```
普通用户不能看到 coreProfileId / binding / provider config
admin 可以管理 voicePreset mapping
developer 可以查看 Core profiles 和调试状态
```

---

## 13. API Contract Governance

### 13.1 当前已有 API

```
GET  /api/xiangta/bootstrap
POST /api/xiangta/suggestions
POST /api/xiangta/tts
GET  /api/xiangta/core/profiles
POST /api/xiangta/letters
GET  /api/xiangta/letters
GET  /api/xiangta/admin/config
GET  /api/xiangta/admin/voice-mappings
GET  /api/xiangta/admin/tone-presets
PUT  /api/xiangta/admin/voice-mappings/{id}
PATCH /api/xiangta/admin/voice-mappings/{id}/enabled
PUT  /api/xiangta/admin/tone-presets/{id}
PATCH /api/xiangta/admin/tone-presets/{id}/enabled
```

### 13.2 未来建议 API

```
GET  /api/xiangta/voice-presets          # 普通 H5 用，映射后产品语义
POST /api/xiangta/tts/tasks               # 异步任务创建
GET  /api/xiangta/tts/tasks/{taskId}      # 任务状态查询
POST /api/xiangta/tts/tasks/{taskId}/cancel  # 任务取消（可选）
GET  /api/xiangta/config/runtime-status   # 运行时状态
```

### 13.3 前端稳定契约原则

```
前端最终应依赖产品 API，不依赖 Core API
H5 只用 /api/xiangta/* 路径，不直连 /api/voice/*
API 响应字段必须 Pydantic schema 化
错误响应必须统一 errorKind
```

---

## 14. Implementation Roadmap

| 阶段 | 任务 | 类型 | 说明 |
|---|---|---|---|
| C1 | Backend Capability Plan | **Design** | 本文档 |
| C2 | Runtime Config Design | Design | runtime.json + env override 设计 |
| C3 | Storage Design | Design | SQLite schema + migration |
| C4 | TTS Task Orchestration Design | Design | async API + queue strategy |
| C5 | LLM Copywriting Design | Design | gateway + fallback + security |
| C6 | Error Contract Design | Design | 统一错误 schema |
| C7 | Profile Mapping Design | Design | voicePreset → coreProfileId |
| C8 | H5 Design Alignment | Design | 前端适配新 API 契约 |
| C9 | Runtime Config Implementation | Implementation | runtime.json + loader |
| C10 | Storage MVP Implementation | Implementation | SQLite + letters/tasks table |
| C11 | TTS Task MVP | Implementation | async API + in-memory queue |
| C12 | LLM Copywriting MVP | Implementation | gateway + template fallback |
| C13 | Error Contract Implementation | Implementation | 统一错误翻译 |
| C14 | Profile Mapping Implementation | Implementation | Admin 配置 + voice-presets API |
| C15 | H5 Polishing | Implementation | 接新 API + error UX |
| C16 | User/Auth Design | Design | 注册/登录/会话/RBAC |
| C17 | Multi-user Storage | Implementation | PostgreSQL + user isolation |

### 近期优先级

```
1. C2 Runtime Config Design
2. C3 Storage Design
3. C4 TTS Task Orchestration Design
4. C5 LLM Copywriting Design
5. C6 Error Contract Design
6. C7 Profile Mapping Design
7. C8 H5 Design Alignment
```

**先后端能力设计，再前端独立优化。不要直接进入 H5 实现。不要直接接 LLM。不要直接做用户系统。**

---

## 15. Key Constraints

```
不修改 Core
不新增 Core HTTP API
不读取真实 Provider API key
不实现 Redis / Celery（第一阶段）
不实现多用户（user_id 设计预留）
不实现正式登录（设计预留）
不暴露 coreProfileId / binding / provider 到普通 H5
```
