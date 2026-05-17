# 想Ta了 API 契约设计

## 用户端 API

用户端 API 只使用产品语义字段。

### GET /api/xiangta/bootstrap

返回前端启动配置。

```json
{
  "ok": true,
  "data": {
    "recipients": [
      { "id": "lover", "label": "恋人", "hint": "想对亲密的人说的话", "enabled": true }
    ],
    "scenes": [
      { "id": "miss", "label": "想念", "hint": "适合表达惦记和牵挂", "enabled": true }
    ],
    "styles": [
      { "id": "restrained", "label": "克制", "desc": "不过度煽情", "enabled": true }
    ],
    "voicePresets": [
      {
        "id": "female-gentle",
        "label": "温柔女声",
        "desc": "适合想念、晚安、轻声表达",
        "genderStyle": "female",
        "suitableRecipients": ["lover", "friend"],
        "recommendedScenes": ["miss", "night"],
        "defaultTone": "gentle",
        "enabled": true
      }
    ],
    "tonePresets": [
      {
        "id": "gentle",
        "label": "温柔",
        "desc": "轻声、柔和、不过分用力",
        "enabled": true
      }
    ],
    "limits": {
      "maxRawTextChars": 500,
      "maxTtsChars": 500,
      "maxSuggestions": 3
    },
    "providerStatus": {
      "kind": "ok",
      "label": "可生成",
      "detail": "当前语音服务正常",
      "quotaPct": 0.35
    }
  }
}
```

### POST /api/xiangta/tts

请求：

```json
{
  "text": "我今天又想起你了。",
  "voicePresetId": "female-gentle",
  "tone": "gentle",
  "recipient": "lover",
  "scene": "miss"
}
```

兼容说明：当前代码里字段名是 `voicePreset`。B1 实现时建议改为 `voicePresetId`，或短期同时兼容两者，最终文档以 `voicePresetId` 为准。

响应：

```json
{
  "ok": true,
  "data": {
    "taskId": "job_xxx",
    "status": "completed",
    "audioUrl": "/api/voice/assets/audio_xxx/download",
    "durationMs": 4200,
    "charCount": 9,
    "voicePresetId": "female-gentle",
    "tone": "gentle",
    "message": null
  }
}
```

用户端响应不返回：

- `profile_id`
- `provider`
- `model`
- `provider_voice_id`
- `params_json`
- `binding_id`
- API key

### GET /api/xiangta/provider/status

响应：

```json
{
  "ok": true,
  "data": {
    "kind": "ok",
    "label": "可生成",
    "detail": "当前语音服务正常",
    "quotaPct": 0.35
  }
}
```

状态映射：

| XiangTa `kind` | Core 来源 |
|---|---|
| `ok` | `provider_status.state = available` |
| `degraded` | rate limit、timeout、warning |
| `quota` | `category = quota` |
| `error` | auth、network、server、validation、provider |
| `unknown` | 无调用记录或状态不可判断 |

## 管理端 API

管理端 API 后续可挂在 `/api/xiangta/admin`。

### GET /api/xiangta/admin/voice-mappings

返回产品声线映射，包括 Core 字段。

```json
{
  "ok": true,
  "data": [
    {
      "id": "female-gentle",
      "label": "温柔女声",
      "enabled": true,
      "coreProfileId": "<core_profile_id_from_core_profiles>",
      "providerPolicy": "default",
      "bindingStatus": "available",
      "renderOverrides": {
        "speed": 0.95,
        "audio_format": "mp3"
      }
    }
  ]
}
```

### PUT /api/xiangta/admin/voice-mappings/{id}

保存产品声线映射。

```json
{
  "label": "温柔女声",
  "desc": "适合想念、晚安、轻声表达",
  "enabled": true,
  "coreProfileId": "<core_profile_id_from_core_profiles>",
  "providerPolicy": "default",
  "renderOverrides": {
    "speed": 0.95
  }
}
```

### GET /api/xiangta/admin/core/profiles

代理或聚合 Core `GET /api/voice/profiles`，用于配置页面选择 Core profile。

### GET /api/xiangta/admin/core/profiles/{profile_id}/bindings

代理或聚合 Core `GET /api/voice/profiles/{profile_id}/bindings`，用于判断 profile 是否可生成。

管理端可以展示 `coreProfileId`、`bindingStatus`、`providerPolicy` 等配置字段，但这些字段不得进入普通用户端 API。`coreProfileId` 必须来自 Core `GET /api/voice/profiles` 的真实返回值，不得由开发者手写猜测。

## Gateway 到 Core 契约

`VoiceLabGateway` 是唯一允许接触 Core 调用细节的 XiangTa 模块。`routes.py`、`ProductService`、`TtsOrchestrator` 不得直接 import `app.repositories`、`app.providers`、`app.models`、`app.domain.render_plan` 或 provider adapter。

Gateway 可以选择 HTTP 调用 Core API，也可以选择等价的进程内 high-level facade；无论哪种方式，都必须维持与 Core 对外 API 等价的请求/响应契约。

### VoiceLabGateway.generate_tts

内部输入：

```python
await gateway.generate_tts(
    text=text,
    target=CoreRenderTarget(
        profile_id="<core_profile_id_from_core_profiles>",
        provider=None,
        need_subtitle=True,
        output_format="url",
        audio_format="mp3",
        speed=0.95,
        emotion="gentle",
    ),
    tone="gentle",
    scene="miss",
    metadata={"recipient": "lover", "voicePresetId": "female-gentle"},
)
```

Core 请求：

```json
{
  "text": "我今天又想起你了。",
  "profile_id": "<core_profile_id_from_core_profiles>",
  "provider": null,
  "need_subtitle": true,
  "output_format": "url",
  "audio_format": "mp3",
  "speed": 0.95,
  "emotion": "gentle"
}
```

Core 响应转产品响应：

| Core 字段 | XiangTa 字段 |
|---|---|
| `job_id` | `taskId` |
| `status` | `status` |
| `audio_asset.id` | 内部保存，可拼下载 URL |
| `audio_asset.url` | `audioUrl` |
| `audio_asset.duration_ms` | `durationMs` |
| `provider` | 内部 metadata/admin，不给用户端 |
| `model` | 内部 metadata/admin，不给用户端 |
