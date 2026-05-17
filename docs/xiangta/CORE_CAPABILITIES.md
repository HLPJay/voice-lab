# Voice Lab Core 能力归档

基于当前 `app/` 源码审计，XiangTa 应复用 Core 的公开 API 能力，不重新实现音频底座。

## XiangTa 需要的最小 Core 子集

| 用途 | Core API | XiangTa 使用方式 |
|---|---|---|
| 获取可映射声线 | `GET /api/voice/profiles` | Admin 配置页读取 profile 列表 |
| 查看声线绑定 | `GET /api/voice/profiles/{profile_id}/bindings` | Admin 检查 profile 是否可 render |
| 生成 TTS | `POST /api/voice/render` | 用户端 `/tts` 经 Gateway 调用 |
| 下载音频 | `GET /api/voice/assets/{asset_id}/download` | 生成后把下载 URL 包装给用户端 |
| 获取 asset 详情 | `GET /api/voice/assets/{asset_id}` | 可选，用于历史记录和状态展示 |
| 运行状态 | `GET /api/voice/runtime/status` | provider status、健康检查、额度提示 |
| Provider 能力 | `GET /api/voice/capabilities` | Admin 配置和前端能力提示 |

## Core Render 请求

Core `VoiceRenderRequest` 当前字段：

| 字段 | 类型 | XiangTa 来源 |
|---|---|---|
| `text` | string | 用户最终文案 |
| `profile_id` | string | `VoicePresetMappingService` 解析出的 `coreProfileId` |
| `provider` | string or null | 可由 `providerPolicy` 决定，默认不传 |
| `need_subtitle` | bool | XiangTa 默认配置 |
| `output_format` | `"hex"` or `"url"` | XiangTa 应使用 `"url"` |
| `audio_format` | `"mp3"`, `"wav"`, `"flac"` | XiangTa MVP 使用 `"mp3"` |
| `speed` | float, 0.5-2.0 | tone 或 voice mapping overrides |
| `vol` | float, 0.1-10.0 | tone 或 voice mapping overrides |
| `pitch` | int, -12 到 12 | tone 或 voice mapping overrides |
| `emotion` | string or null | tone 配置 |
| `confirm_cost` | bool | 高成本确认场景，MVP 默认 false |

## Core Render 响应

Core `VoiceRenderResponse` 当前字段：

| 字段 | 说明 |
|---|---|
| `job_id` | Core 生成任务 ID |
| `status` | 任务状态 |
| `provider` | 实际使用的 provider |
| `model` | 实际使用的模型 |
| `audio_asset` | `{ id, url, duration_ms, format }` |
| `subtitle_asset` | `{ id, url, timeline }` 或 null |

XiangTa 用户端响应应只暴露必要结果，如 `taskId`、`audioUrl`、`durationMs`、`status`。`provider` 和 `model` 可进入内部 metadata 或 admin 日志，不进入普通用户端主契约。

## Core Profiles

`GET /api/voice/profiles` 返回 `VoiceProfileRead`：

- `id`
- `name`
- `description`
- `gender_style`
- `age_style`
- `tone_style`
- `emotion_style`
- `speed_style`
- `pause_style`
- `scene_tags`
- `is_active`

XiangTa Admin 选择 Core profile 时应展示这些字段；用户端 bootstrap 不直接返回 `profile_id`。

## Core Bindings

`GET /api/voice/profiles/{profile_id}/bindings` 返回 `VoiceBindingRead`：

- `id`
- `profile_id`
- `provider`
- `model`
- `provider_voice_id`
- `provider_voice_name`
- `params`
- `priority`
- `status`
- `created_at`
- `updated_at`

XiangTa 可以用 binding 状态判断某个 `voicePresetId` 是否可用。用户端只看到 `enabled` 和产品化说明。

## Runtime Status

`GET /api/voice/runtime/status` 当前返回：

- `current.default_provider`
- `current.default_model`
- `current.default_ws_model`
- `current.default_audio_format`
- `today.job_count`
- `today.success_count`
- `today.failed_count`
- `today.usage_characters`
- `month.*`
- `last_call.*`
- `provider_status.state/category/label/detail/action_hint`

XiangTa 的 `/provider/status` 应把这些字段翻译为产品层状态：

- `ok`
- `degraded`
- `quota`
- `error`
- `unknown`

## 不纳入 XiangTa MVP 的 Core 能力

这些能力可以保留为后续扩展，不进入当前产品配置模型：

- voice clone
- voice design
- WebSocket streaming render
- batch render
- variants
- provider voice import
- cost estimate 独立 API
