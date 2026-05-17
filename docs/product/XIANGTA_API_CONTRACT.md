# 想Ta了 · API Contract 草案

> 本文档只定义协议，不实现。实现在 `src/xiangta/api/routes.py`。
> 版本：v0（草案阶段，P17-XIANGTA-INIT-A0）

---

## 通用约定

- Base path：`/api/xiangta`
- 请求体：JSON（Content-Type: application/json）
- 响应体：JSON
- 错误结构：

```json
{
  "ok": false,
  "errorKind": "quota | no_provider | tts_failed | llm_failed | not_found | bad_request",
  "message": "对用户友好的中文说明",
  "retryable": true
}
```

- 成功结构：

```json
{
  "ok": true,
  "data": { ... }
}
```

---

## GET /api/xiangta/bootstrap

启动时拉取配置快照，前端缓存后使用。

**Request**：无参数

**Response 200**：

```json
{
  "ok": true,
  "data": {
    "recipients": [
      { "id": "lover",  "label": "恋人" },
      { "id": "family", "label": "父母" },
      { "id": "friend", "label": "朋友" },
      { "id": "self",   "label": "自己" }
    ],
    "scenes": [
      { "id": "miss",    "label": "想念" },
      { "id": "sorry",   "label": "道歉" },
      { "id": "thanks",  "label": "感谢" },
      { "id": "comfort", "label": "安慰" },
      { "id": "night",   "label": "晚安" }
    ],
    "voicePresets": [
      { "id": "female-gentle", "name": "温柔女声", "desc": "清晰、靠近、稍慢" },
      { "id": "male-gentle",   "name": "温柔男声", "desc": "低、安静" },
      { "id": "female-bright", "name": "清亮女声", "desc": "年轻，适合朋友" },
      { "id": "male-mature",   "name": "成熟男声", "desc": "稳，适合父母" }
    ],
    "tonePresets": [
      { "id": "restrained", "label": "克制" },
      { "id": "gentle",     "label": "温柔" },
      { "id": "sincere",    "label": "真诚" },
      { "id": "whisper",    "label": "轻声" },
      { "id": "bedtime",    "label": "睡前" }
    ],
    "provider": {
      "kind": "ok",
      "label": "已连接",
      "detail": "MiniMax · speech-2.5-hd"
    }
  }
}
```

---

## POST /api/xiangta/suggestions

根据用户输入生成 3 条风格文案建议。

**Request**：

```json
{
  "recipient": "lover",
  "scene": "miss",
  "rawText": "今天下雨了，突然想起我们一起淋雨那次，那时候没说，其实挺幸福的。"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| recipient | string | ✅ | lover / family / friend / self |
| scene | string | ✅ | miss / sorry / thanks / comfort / night |
| rawText | string | ✅ | 用户原始输入，4–500 字 |

**Response 200**：

```json
{
  "ok": true,
  "data": {
    "summary": "\"你读到的是 TA 在雨天想起一段温柔的回忆，想让对方知道那一刻的幸福。\"",
    "intent": "想念 + 轻轻的告白，不带索取",
    "suggestions": [
      {
        "style": "restrained",
        "styleLabel": "克制版",
        "fitsFor": "想说，但不想给对方压力",
        "text": "今天又下雨了。突然想起我们一起淋雨的那天 —— 那时候没说，但其实挺幸福的。",
        "charCount": 35
      },
      {
        "style": "gentle",
        "styleLabel": "温柔版",
        "fitsFor": "想让对方感觉到温度",
        "text": "下了一天的雨，路过那条街的时候，又想起跟你一起淋雨那次。那天我没说，但站在你旁边的时候，我心里其实很满。",
        "charCount": 55
      },
      {
        "style": "sincere",
        "styleLabel": "真诚版",
        "fitsFor": "想认真表达，不绕弯",
        "text": "今晚下雨，让我想起跟你一起淋雨那一天。我那时候没告诉你，那一刻我觉得跟你在一起好幸福。我不一定要你回什么，只是想让你知道，这个雨夜，我想到的人是你。",
        "charCount": 81
      }
    ]
  }
}
```

**Error 422**：rawText 过短

**Error 503**：LLM Provider 不可用

---

## POST /api/xiangta/tts

对选定文案生成语音。

**Request**：

```json
{
  "text": "今天又下雨了。突然想起我们一起淋雨的那天 —— 那时候没说，但其实挺幸福的。",
  "voicePreset": "female-gentle",
  "tone": "restrained",
  "recipient": "lover",
  "scene": "miss"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| text | string | ✅ | 要朗读的文案（选定的那条） |
| voicePreset | string | ✅ | 声线预设 ID |
| tone | string | ✅ | 语气预设 ID |
| recipient | string | ✅ | 用于日志 / 统计 |
| scene | string | ✅ | 用于日志 / 统计 |

**Response 200**：

```json
{
  "ok": true,
  "data": {
    "taskId": "tts_abc123",
    "audioUrl": "/api/xiangta/audio/tts_abc123.mp3",
    "durationSecs": 8.4,
    "charCount": 35,
    "voicePreset": "female-gentle",
    "tone": "restrained"
  }
}
```

**Error 402**：配额耗尽（errorKind: "quota"）

**Error 503**：TTS Provider 不可用（errorKind: "no_provider"）

---

## POST /api/xiangta/letters

保存一封信笺（服务端存储，MVP 可先返回 201 + 本地 ID）。

**Request**：

```json
{
  "recipient": "lover",
  "scene": "miss",
  "style": "restrained",
  "rawText": "今天下雨了……",
  "finalText": "今天又下雨了。突然想起……",
  "voicePreset": "female-gentle",
  "tone": "restrained",
  "audioUrl": "/api/xiangta/audio/tts_abc123.mp3",
  "durationSecs": 8.4,
  "title": null
}
```

**Response 201**：

```json
{
  "ok": true,
  "data": {
    "letterId": "L_abc123_xyz",
    "createdAt": "2026-05-17T14:30:00Z"
  }
}
```

---

## GET /api/xiangta/letters

获取当前用户信笺列表（MVP 阶段服务端不做，前端用 localStorage）。

**Response 200**：

```json
{
  "ok": true,
  "data": {
    "letters": [ { "letterId": "...", "title": "...", "createdAt": "...", "favorited": false } ],
    "total": 3
  }
}
```

---

## GET /api/xiangta/provider/status

实时查询底层 Provider 状态，供前端状态栏显示。

**Response 200**：

```json
{
  "ok": true,
  "data": {
    "kind": "ok",
    "label": "已连接",
    "detail": "MiniMax · speech-2.5-hd",
    "quotaPct": 0.72
  }
}
```

`kind` 取值：`ok` | `degraded` | `quota` | `error`
