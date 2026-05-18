# 想Ta了系统架构

## 架构原则

1. 产品层不暴露 provider 参数。
2. 用户端不暴露 Core `profile_id`。
3. TtsOrchestrator 不直接查配置表。
4. VoiceLabGateway 是 XiangTa 调用 Core 的唯一边界。
5. B9 阶段：XiangTa 只通过 Core HTTP 上层 API 使用底座能力，不 import Core 内部模块。

## 分层

```text
┌────────────────────────────────────────────┐
│ Mobile App / H5 / PWA                      │
│ voicePresetId, tone, recipient, scene      │
└──────────────────────┬─────────────────────┘
                       │ HTTP JSON
┌──────────────────────▼─────────────────────┐
│ XiangTa Backend (src/xiangta)              │
│ routes → ProductService → 子服务 → Gateway  │
│                                             │
│ VoicePresetMappingService:                  │
│   voicePresetId → coreProfileId            │
│                                             │
│ TonePresetService / ConfigRepository:       │
│   tone → style hints / render overrides    │
└──────────────────────┬─────────────────────┘
                       │ HTTP (CoreHttpClient)
┌──────────────────────▼─────────────────────┐
│ Voice Lab Core (app/**)                    │
│ profiles / bindings / render / assets      │
│ runtime status / capabilities              │
│ Provider adapters / Repository / Service   │
└────────────────────────────────────────────┘
```

## 架构总览

### app/\*\* = Voice Lab Core

- 音频能力底座
- profile / binding / provider / render / asset / job
- HTTP API 层：`app/api/voice_profiles.py`、`app/api/voice_render.py`
- 不修改 Core

### src/xiangta/\*\* = XiangTa 产品服务层

- 产品语义 API
- 通过 `VoiceLabGateway` + `CoreHttpClient` 调用 Core HTTP API
- 不直接调用 Provider / Repository / Core Service
- 不 import `app.providers.*`、`app.repositories.*`、`app.services.*`

### apps/xiangta-h5/\*\* = XiangTa H5 前端

- 用户输入、选择人设、生成语音、播放音频
- 纯静态 HTML/JS，无构建工具

### apps/xiangta_runtime/\*\* = XiangTa 本地 runtime

- 挂载 H5 静态页面与 `/api/xiangta/*`
- 不承载核心业务逻辑
- apps 是应用壳，src/xiangta 是产品服务层，app 是音频能力底座

---

## 当前 B9 调用链

```text
Browser
  → apps/xiangta_runtime (port 5174)
  → apps/xiangta-h5 (static)
  → POST /api/xiangta/tts {profileId, text, ...}
  → src/xiangta/api/routes.py
  → ProductService.generate_tts(profile_id=...)
  → TtsOrchestrator.generate(profile_id=...)
  → VoiceLabGateway.generate_tts(target=CoreRenderTarget(...))
  → CoreHttpClient.post("/api/voice/render", ...)
  → Core HTTP API (port 8000)
  → app/api/voice_render.py
  → Core Provider → Core Asset
  → Core 返回 {audio_asset: {url: "/api/voice/assets/.../download"}}
  → CoreHttpClient.absolute_url() → "http://127.0.0.1:8000/api/voice/assets/.../download"
  → XiangTa audioUrl → H5
  → <audio controls src="http://127.0.0.1:8000/...">
```

Profiles 读取链路：

```text
Browser → GET /api/xiangta/core/profiles
  → VoiceLabGateway.list_profiles()
  → CoreHttpClient.get("/api/voice/profiles")
  → Core HTTP API → Core profiles
  → VoiceLabGateway._filter_profile() 过滤 forbidden fields
  → H5 coreProfileSelect
```

---

## Core 边界

XiangTa **不修改** Core。
XiangTa **不 import** 以下模块：

```
app.providers.*
app.repositories.*
app.services.*
app.main
```

XiangTa **不读取**真实 Provider API key：

```
MINIMAX_API_KEY
MIMO_API_KEY
OPENAI_API_KEY
DEEPSEEK_API_KEY
```

XiangTa **只通过**以下 Core HTTP 上层 API 使用底座能力：

| API | 用途 |
|---|---|
| `GET /api/voice/profiles` | 读取 Core 已有人设 |
| `POST /api/voice/render` | 发起 TTS 生成 |
| `GET /api/voice/runtime/status` | 查询 Provider 状态 |

---

## 产品语义边界

H5 和普通用户端**不应该**感知：

```
provider_voice_id
binding_id
params_json
model_id
api_key
provider
```

H5 当前允许直接选择 Core profile（`profileId`）是 **B9 链路验证阶段的临时路径**。
后续应产品化为 `voicePreset` → `coreProfileId` 映射，通过 Admin 接口配置。

---

## TTS 调用流程

```text
POST /api/xiangta/tts
  { text, voicePresetId, tone, recipient, scene, profileId? }
        ↓
TtsOrchestrator.generate()
  情况 A（传 profileId）：
    1. TonePresetService.resolve(tone)
    2. 组装 CoreRenderTarget(profile_id=profileId, provider=None)
  情况 B（未传 profileId）：
    1. VoicePresetMappingService.resolve(voicePresetId)
         → ProductVoiceMapping(coreProfileId, providerPolicy, overrides)
    2. TonePresetService.resolve(tone)
    3. 组装 CoreRenderTarget(profile_id=coreProfileId, provider=providerPolicy)
  4. VoiceLabGateway.generate_tts(text, target, metadata)
       → Core POST /api/voice/render
  5. CoreHttpClient.absolute_url() 转换音频路径
  6. 组装产品响应
        ↓
{ taskId, status, audioUrl, durationMs, voicePresetId, tone }
```

---

## 关键内部对象

```python
@dataclass(frozen=True)
class CoreRenderTarget:
    profile_id: str
    provider: str | None = None  # None/default/mock/minimax/xiaomi_mimo
    need_subtitle: bool = True
    output_format: str = "url"
    audio_format: str = "mp3"
    speed: float | None = None
    vol: float | None = None
    pitch: int | None = None
    emotion: str | None = None
```

---

## 服务职责

| 模块 | 职责 |
|---|---|
| `routes.py` | 暴露产品 API，只接受产品语义字段 |
| `schemas.py` | 用户端请求/响应模型，过滤 Core forbidden fields |
| `ProductService` | 产品服务门面，协调子服务 |
| `BootstrapService` | 聚合用户端启动配置 |
| `TtsOrchestrator` | 校验、映射、调用 Gateway、组装响应 |
| `VoicePresetMappingService` | `voicePresetId` 到 Core `profile_id` 的独立映射服务 |
| `VoiceLabGateway` | 调用 Core HTTP API，隐藏 Core 技术细节 |
| `CoreHttpClient` | 封装对 Core HTTP 上层 API 的 GET/POST |
| `ErrorTranslator` | Core 技术错误转成产品友好错误 |

---

## Concurrency & Scalability Boundary

### 当前承诺

- 本地单用户 / 轻量多浏览器验证
- `POST /api/xiangta/tts` 是**同步链路**（Core render 完成才返回）
- 不承诺多人 SaaS、高并发、任务恢复、任务取消、后台队列

### Core 负责什么

```
Core 负责 Provider 级能力：
- provider adapter（MiniMax / Xiaomi MiMo / OpenAI 等）
- binding resolution（音色绑定解析）
- render job（渲染任务）
- asset save/download（音频资产存储）
- cost guard（成本守卫）
- resource guard（资源守卫）
- provider call log（调用日志）
```

### XiangTa 后续应该负责什么

```
XiangTa 产品层后续应负责：
- 产品级 task 状态
- 防重复点击
- 同一用户并发限制
- taskId 查询
- 失败重试策略
- 用户可理解错误
- 前端轮询
- 保存历史
```

### 后续演进方向

后续建议引入异步 task 架构：

```
POST /api/xiangta/tts/tasks  → 立即返回 taskId + status=pending
GET  /api/xiangta/tts/tasks/{taskId}  → 查询状态 + audioUrl（完成时）

TtsTaskService：
  - create_task() → 生成 taskId，状态 pending
  - poll_task() → 查询 Core render 状态
  - 返回产品友好结果
```

但本阶段（B9）**不实现**异步 task，仍为同步链路。

---

## 当前不做事项

```
不做持久化（letters 目前为进程内内存）
不接 LLM（suggestions 目前为模板版）
不做登录
不做多用户权限
不做 Redis / Celery / 队列
不做自动发送
不修改 Core Provider
不修改 Core Repository
不修改 Core Service
不修改 Core 配置
不暴露 provider_voice_id / binding_id / params_json / api_key
```

---

## 与早期 A0-A2 的差异

| 维度 | A0-A2 临时方案 | 修正后方案（B9） |
|---|---|---|
| 声线来源 | `voice_presets.json` 静态定义 | `voice_mappings` 产品配置，映射 Core profiles |
| 映射 key | `core_binding_key` | 用户端 `voicePresetId`，服务端 `coreProfileId` |
| 映射服务 | `PresetMapper.resolve_binding()` | `VoicePresetMappingService.resolve()` |
| tone | 与声线一起被 `PresetMapper` 处理 | XiangTa 自有 TonePresetService |
| Gateway 输入 | `core_binding_key` 字符串 | `CoreRenderTarget` dataclass |
| Core 调用 | dry-run 为主 | `POST /api/voice/render` + CoreHttpClient |
| 音频路径 | 无 | `CoreHttpClient.absolute_url()` 转换相对路径 |
| profiles | 无 | `GET /api/voice/profiles` 实时读取 |
