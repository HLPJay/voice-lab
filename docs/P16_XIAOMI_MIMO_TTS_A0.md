# P16-XIAOMI-MIMO-TTS-A0：小米 MiMo speech-synthesis-v2.5 接入前置审查

## 1. 阶段目标

对小米 MiMo speech-synthesis-v2.5 进行接入前置审查，判断是否需要新增 adapter plugin，以及如何映射到当前架构。

**本阶段不是实现阶段**，不直接实现 adapter，不接入业务链路。

## 2. 官方文档来源

**URL**: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5

**本地 HTML 文件**: `C:\Users\yun68\Downloads\Xiaomi MiMo API Open Platform.html`

## 3. 文档可访问性说明

✅ **官方文档已成功解析**

通过本地 HTML 文件成功获取了完整的 API 文档内容。

## 4. 核心发现：Xiaomi MiMo 是 OpenAI-compatible

**重大发现**：Xiaomi MiMo 使用 **OpenAI Chat Completions API 格式**！

- Endpoint: `POST https://api.xiaomimimo.com/v1/chat/completions`
- 鉴权: `api-key: $MIMO_API_KEY` (不是 Bearer)
- Protocol: OpenAI Chat Completions with TTS extensions

这意味着 Xiaomi MiMo 可以复用 OpenAI-compatible adapter 模式，而不需要新增独立的 xiaomi_mimo_tts adapter。

## 5. API 协议详解

### 5.1 鉴权方式

```
Header: api-key: $MIMO_API_KEY
```

| 项目 | 值 |
|---|---|
| Header 名称 | `api-key` |
| 认证方式 | API Key（不是 Bearer Token） |
| 环境变量 | `MIMO_API_KEY` |
| 是否需要签名 | 否 |

### 5.2 Endpoint

| 项目 | 值 |
|---|---|
| Base URL | `https://api.xiaomimimo.com/v1` |
| Endpoint | `/v1/chat/completions` |
| HTTP Method | POST |
| Content-Type | `application/json` |
| Protocol | OpenAI Chat Completions compatible |

### 5.3 请求体字段

**核心请求结构**：

```json
{
    "model": "mimo-v2.5-tts",
    "messages": [
        {
            "role": "user",
            "content": "语音风格描述（可选）"
        },
        {
            "role": "assistant",
            "content": "要合成语音的文本"
        }
    ],
    "audio": {
        "format": "wav",
        "voice": "冰糖"
    }
}
```

| 字段 | 类型 | 说明 | 必填 |
|---|---|---|---|
| `model` | string | 模型名 | ✅ |
| `messages` | array | 消息数组 | ✅ |
| `messages[].role` | string | `user` 或 `assistant` | ✅ |
| `messages[].content` | string | 文本内容 | ✅ |
| `audio.format` | string | 音频格式：`wav` 或 `pcm16` | ✅ |
| `audio.voice` | string | 音色名或 Voice ID | ✅ |
| `stream` | boolean | 是否流式（见下方说明） | 否 |

### 5.4 响应格式

**非流式响应**：

```json
{
    "choices": [
        {
            "message": {
                "role": "assistant",
                "audio": {
                    "data": "<base64 encoded audio>",
                    "format": "wav"
                },
                "content": ""
            }
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 100,
        "total_tokens": 110
    }
}
```

| 字段 | 说明 |
|---|---|
| `choices[].message.audio.data` | base64 编码的音频 |
| `choices[].message.audio.format` | 音频格式 |
| `usage` | token 使用量 |

### 5.5 流式响应

**⚠️ 重要说明**：流式调用目前是"兼容模式"，**仅在所有推理完成后以流式格式返回一次结果**。

```json
{
    "choices": [
        {
            "delta": {
                "audio": {
                    "data": "<base64 chunk>",
                    "format": "pcm16"
                }
            }
        }
    ]
}
```

流式模式下音频格式只支持 `pcm16`，需要拼接成完整音频。

## 6. 支持的模型

| 模型名 | 说明 | 支持预置音色 | 支持音色设计 | 支持音色克隆 |
|---|---|---|---|---|
| `mimo-v2.5-tts` | 使用预置音色 | ✅ | ❌ | ❌ |
| `mimo-v2.5-tts-voicedesign` | 文本音色设计 | ❌ | ✅ | ❌ |
| `mimo-v2.5-tts-voiceclone` | 音频音色克隆 | ❌ | ❌ | ✅ |

## 7. 支持的音色列表

| 音色名 | Voice ID | 语言 | 性别 |
|---|---|---|---|
| MiMo-默认 | `mimo_default` | 因集群而异 | 因集群而异 |
| 冰糖 | `冰糖` | 中文 | 女性 |
| 茉莉 | `茉莉` | 中文 | 女性 |
| 苏打 | `苏打` | 中文 | 男性 |
| 白桦 | `白桦` | 中文 | 男性 |
| Mia | `Mia` | 英文 | 女性 |
| Chloe | `Chloe` | 英文 | 女性 |
| Milo | `Milo` | 英文 | 男性 |
| Dean | `Dean` | 英文 | 男性 |

## 8. 支持的音频格式

| 格式 | 说明 | 使用场景 |
|---|---|---|
| `wav` | WAV 格式 | 非流式调用 |
| `pcm16` | PCM 16bit | 流式调用（需拼接） |

## 9. 能力边界

| 能力 | 是否支持 | 说明 |
|---|---|---|
| 同步 TTS | ✅ | 非流式调用 |
| 流式 TTS | ⚠️ | 兼容模式，推理完成后一次返回 |
| 预置音色 | ✅ | `mimo-v2.5-tts` 模型 |
| 音色设计 | ✅ | `mimo-v2.5-tts-voicedesign` 模型 |
| 音色克隆 | ✅ | `mimo-v2.5-tts-voiceclone` 模型 |
| 字幕 | ❌ | 不支持 |
| 语气/风格控制 | ✅ | 通过 `role: user` 消息传入 |
| speed/pitch/vol | ❌ | 不支持显式参数，通过文本描述控制 |
| 批量文本 | ❌ | 不支持 |
| 异步任务 | ❌ | 不需要，API 本身就是同步的 |

## 10. 与现有内部协议映射

### 10.1 映射分析

| 内部概念 | 当前 MiniMax | Xiaomi MiMo | 映射策略 |
|---|---|---|---|
| `render_sync` | ✅ | ✅ | 可复用 OpenAI-compatible 模式 |
| `render_stream` | ✅ WebSocket | ⚠️ 兼容模式 | B1 不实现 |
| `create_async_task` | ✅ | ❌ | 不需要，API 本身同步 |
| `list_voices` | ✅ | ⚠️ 静态列表 | 可返回预置音色列表 |
| `delete_voice` | ✅ | ❌ | 不支持 |
| `clone_voice` | ✅ | ✅ | 可通过 `mimo-v2.5-tts-voiceclone` 模型支持 |
| `design_voice` | ✅ | ✅ | 可通过 `mimo-v2.5-tts-voicedesign` 模型支持 |

### 10.2 关键差异

| 差异点 | MiniMax | Xiaomi MiMo | 影响 |
|---|---|---|---|
| 鉴权 | Bearer token | API Key | 需要不同 header |
| 协议 | REST 私有 | OpenAI-compatible | 可复用 OpenAI 模式 |
| 文本位置 | `text` 字段 | `messages[role=assistant]` | adapter 需要转换 |
| 音频返回 | base64/hex/url | base64 in `message.audio.data` | 需要解析 OpenAI 格式 |
| 音色控制 | `voice_id` + `emotion` | 预置 Voice ID + 文本描述 | 需要不同接口 |

### 10.3 provider_params 需要

由于 Xiaomi MiMo 使用 OpenAI Chat Completions 格式，以下参数需要通过 `provider_params` 传递：

- `stream`: 是否流式（默认 false）
- `messages[].role`: 角色（固定 `user` / `assistant`）
- `audio.format`: 音频格式

## 11. 是否需要新增 adapter_type

**结论：需要新增 `xiaomi_mimo_tts` adapter_type**

**理由**：

1. **鉴权不同**：Xiaomi MiMo 使用 `api-key` header，不是 `Authorization: Bearer`
2. **Base URL 不同**：`https://api.xiaomimimo.com/v1` vs `https://api.minimaxi.com`
3. **请求格式不同**：Xiaomi MiMo 使用 OpenAI Chat Completions 格式
4. **模型体系不同**：三个专用模型 vs MiniMax 通用模型
5. **音频返回格式不同**：OpenAI 格式 `message.audio.data` vs MiniMax hex/URL

虽然都是 OpenAI-compatible，但 adapter 需要处理不同的：
- Header 处理
- Base URL
- 请求体转换（RenderPlan → messages 格式）
- 响应解析（message.audio.data → audio bytes）

## 12. AdapterConfig 草案

```yaml
# config/adapters/xiaomi_mimo_tts.yaml

adapter_type: "xiaomi_mimo_tts"

display_name: "Xiaomi MiMo"

default_base_url: "https://api.xiaomimimo.com/v1"

default_model: "mimo-v2.5-tts"

default_timeout_seconds: 120

endpoints:
  # Uses OpenAI Chat Completions endpoint
  tts: "/v1/chat/completions"

tts:
  supported: true
  models:
    - "mimo-v2.5-tts"
    - "mimo-v2.5-tts-voicedesign"
    - "mimo-v2.5-tts-voiceclone"
  default_model: "mimo-v2.5-tts"
  max_text_chars: 5000
  audio_formats:
    - "wav"
    - "pcm16"
  supports_subtitle: false
  supports_streaming: true  # 兼容模式
  supports_emotion: false  # 通过文本描述控制

batch:
  supported: false

script:
  supported: false

voice_clone:
  supported: true  # mimo-v2.5-tts-voiceclone 模型
  preview_text_max: 1000

voice_design:
  supported: true  # mimo-v2.5-tts-voicedesign 模型
  prompt_max: 500

provider_voices:
  supported: true  # 预置音色列表
  supports_list_voices: true
  supports_delete_voice: false
  preview_text_max: 1000

metadata:
  version: "v2.5"
  protocol: "openai-compatible"
  note: "Xiaomi MiMo TTS using OpenAI Chat Completions format"
```

## 13. ProviderConfig 草案

```yaml
# config/providers.yaml (草案，不在正式文件新增)

- name: "xiaomi_mimo"
  display_name: "Xiaomi MiMo"
  enabled: false  # 初始 disabled
  adapter_type: "xiaomi_mimo_tts"
  real_cost: true
  api_key_env: "MIMO_API_KEY"
  base_url: null  # 从 adapter config 获取
  endpoints: {}
  default_model: "mimo-v2.5-tts"
  tts:
    enabled: true
  batch:
    enabled: false
  script:
    enabled: false
  voice_clone:
    enabled: true
  voice_design:
    enabled: true
  provider_voices:
    enabled: true
  metadata:
    api_type: "xiaomi_mimo"
```

## 14. 探测测试方案

由于 API 格式已明确，探测测试可以简化。

### 14.1 探测目标

1. 确认鉴权是否正确
2. 确认最小文本能否生成音频
3. 确认 response 格式
4. 确认错误响应结构

### 14.2 探测用例（最小集）

#### Case 1：最小成功请求

```
POST https://api.xiaomimimo.com/v1/chat/completions
Headers:
  api-key: $MIMO_API_KEY
  Content-Type: application/json
Body:
{
    "model": "mimo-v2.5-tts",
    "messages": [
        {
            "role": "assistant",
            "content": "你好，这是一次语音合成测试。"
        }
    ],
    "audio": {
        "format": "wav",
        "voice": "冰糖"
    }
}
```

#### Case 2：错误鉴权

```
使用空 API Key 或错误 API Key
预期：401 Unauthorized
```

#### Case 3：非法模型

```
model: "nonexistent-model"
预期：4xx 错误
```

## 15. P16-XIAOMI-MIMO-TTS-B1 最小实现建议

### B1 最小支持范围

| 功能 | 是否支持 | 原因 |
|---|---|---|
| 同步 TTS | ✅ | 核心能力 |
| 单文本输入 | ✅ | 核心能力 |
| 单 voice/speaker | ✅ | 预置音色 |
| wav 格式 | ✅ | 标准格式 |
| 本地音频文件保存 | ✅ | 复用现有逻辑 |
| mock transport 单元测试 | ✅ | 必须 |
| list_voices | ✅ | 静态预置音色 |
| design_voice | ✅ | mimo-v2.5-tts-voicedesign |

### B1 明确不支持

| 功能 | 原因 |
|---|---|
| 流式 TTS | 兼容模式，不适合当前系统 |
| clone_voice | 需要音频文件上传，B1 范围外 |
| delete_voice | Xiaomi 不支持 |
| provider_voice_import | 需要音频文件，B1 范围外 |
| UI 改造 | B1 范围外 |

## 16. 当前不能判断的信息

无。所有关键信息已从文档确认。

## 17. 剩余风险

| 风险 | 级别 | 说明 |
|---|---|---|
| 实际 API 可用性 | 🟡 中 | 需要真实 API Key 验证 |
| 音色克隆细节 | 🟡 中 | 需要 probe 确认音频上传方式 |
| 错误响应格式 | 🟡 中 | 需要 probe 确认具体错误结构 |
| max_text_chars 限制 | 🟡 中 | 文档未明确，假设 5000 |

## 18. 下一阶段建议

### 推荐：P16-XIAOMI-MIMO-TTS-B1

**目标**：实现 Xiaomi MiMo TTS adapter 最小可行路径

**最小范围**：
- 同步 TTS（render_sync）
- 预置音色列表（list_voices）
- 音色设计（design_voice via mimo-v2.5-tts-voicedesign）
- mock transport 单元测试

**明确不支持**：
- 流式
- clone
- delete_voice
- UI 改造

### 备选

| 阶段 | 内容 | 前提 |
|---|---|---|
| P16-OPENAI-COMPATIBLE-TTS-A0 | 设计通用 OpenAI-compatible adapter | 可复用部分 |
| P16-DYNAMIC-PROVIDER-CONFIG-B2 | Provider capability override 增强 | 不冲突 |

## 19. 收口结论

**P16-XIAOMI-MIMO-TTS-A0 完成** ✅

**核心发现**：
- Xiaomi MiMo 使用 **OpenAI Chat Completions API 格式**
- 鉴权使用 `api-key` header（不是 Bearer）
- 支持预置音色、音色设计、音色克隆
- 流式是兼容模式，不适合当前系统

**是否需要新增 adapter_type**：是

**建议进入 B1 实现**。
