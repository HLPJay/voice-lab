# Voice Lab 架构标准

## 总体分层

```text
产品应用层
  旁白试音台 / 音色库 / 情绪 MV / 播客

对外 API 层
  /api/voice/render
  /api/voice/variants/render
  /api/voice/profiles
  /api/voice/assets
  /api/voice/jobs

业务调度层
  选择人设 / 选择模型 / 生成计划 / 任务编排

标准协议层
  VoiceProfile / VoiceBinding / RenderPlan
  VoiceJob / AudioAsset / SubtitleAsset

Provider Adapter 层
  MiniMaxSpeechAdapter
  MockSpeechAdapter
  未来 OpenAI / ElevenLabs / Azure / LocalTTS

模型服务层
  MiniMax speech-2.8-hd
```

## 模块职责

### API 层

只负责请求校验、依赖注入、调用服务层和返回响应。

API 层禁止：

- 拼接 MiniMax 请求体
- 直接保存音频文件
- 直接操作 Provider 返回结构

### 业务调度层

负责把业务请求转成内部任务：

1. 查询 `VoiceProfile`
2. 查询 `VoiceBinding`
3. 文本预处理
4. 生成 `RenderPlan`
5. 创建 `VoiceJob`
6. 调用 Provider Adapter
7. 保存资产
8. 更新任务状态

### 标准协议层

标准协议层是系统内部统一语义，不是外部 API。

所有 Provider 都必须接收 `RenderPlan`，返回标准 `ProviderRenderResult`。

### Provider Adapter 层

Provider Adapter 是厂商翻译器。

职责只有两个：

1. 把内部 `RenderPlan` 翻译成厂商请求参数。
2. 把厂商返回结果翻译成内部资产结果。
3. （Voice Catalog）把厂商音色列表翻译成内部 `ProviderVoice` 列表。

Provider Adapter 禁止：

- 查询业务数据库
- 决定声音人设
- 处理上层业务场景
- 泄露 API Key 到日志

## 核心对象标准

### VoiceProfile

产品级声音人设。

示例：

```json
{
  "id": "deep_night_programmer",
  "name": "深夜程序员",
  "description": "低沉、克制、疲惫但不崩溃，适合深夜独白",
  "scene_tags": ["deep_night_monologue", "emotional_mv"]
}
```

### VoiceBinding

Provider 绑定。

```json
{
  "profile_id": "deep_night_programmer",
  "provider": "minimax",
  "model": "speech-2.8-hd",
  "provider_voice_id": "English_expressive_narrator",
  "params": {
    "speed": 0.88,
    "vol": 1,
    "pitch": 0,
    "emotion": "sad"
  }
}
```

### RenderPlan

内部标准生成计划。任何 Provider 调用前都必须先生成它。

```json
{
  "text": "原始文案",
  "processed_text": "适合朗读的文案<#0.5#>",
  "profile_id": "deep_night_programmer",
  "provider": "minimax",
  "model": "speech-2.8-hd",
  "provider_voice_id": "English_expressive_narrator",
  "voice_params": {},
  "audio_params": {},
  "subtitle": {
    "enabled": true,
    "type": "sentence"
  },
  "output_format": "hex",
  "language_boost": "auto"
}
```

### ProviderVoice

Provider 音色目录项。Voice Lab 中台级音色只读视图，上层业务不直接依赖 MiniMax voice_id。

示例：

```json
{
  "id": "pv_xxx",
  "provider": "minimax",
  "provider_voice_id": "English_expressive_narrator",
  "voice_type": "system",
  "name": "English Expressive Narrator",
  "description": "Expressive English narration voice",
  "language": "en",
  "gender": "female",
  "status": "available",
  "provider_created_time": "2024-01-15T10:00:00Z",
  "metadata_json": "{}",
  "synced_at": "2026-05-11T12:00:00Z",
  "created_at": "2026-05-11T12:00:00Z",
  "updated_at": "2026-05-11T12:00:00Z"
}
```

VoiceType 枚举：

- `system`：系统音色
- `voice_cloning`：克隆音色
- `voice_generation`：生成音色

## 错误标准

所有错误统一返回：

```json
{
  "error": {
    "code": "PROVIDER_ERROR",
    "message": "MiniMax request failed",
    "detail": "...",
    "job_id": "job_xxx"
  }
}
```

错误码：

- `VALIDATION_ERROR`
- `PROFILE_NOT_FOUND`
- `BINDING_NOT_FOUND`
- `UNSUPPORTED_PROVIDER` (400)
- `PROVIDER_NOT_CONFIGURED`
- `PROVIDER_ERROR`
- `AUDIO_SAVE_ERROR`
- `SUBTITLE_SAVE_ERROR`
- `JOB_NOT_FOUND`
- `ASSET_NOT_FOUND`

## 领域枚举

系统级枚举定义在 `app/domain/enums.py`：

- `JobStatus`：pending / running / success / failed
- `JobType`：sync_render
- `BindingStatus`：available / deprecated
- `Provider`：mock / minimax

VoiceBinding.status 和相关查询必须使用 `BindingStatus` 枚举常量，禁止魔法字符串。
Provider 校验在 render 入口前置执行，未知 provider 返回 `UNSUPPORTED_PROVIDER`。

## 声音参数白名单

RenderPlan 对 voice_params 执行白名单过滤，仅允许以下 key：
`speed`、`vol`、`pitch`、`emotion`、`timber_weights`。

任何不在白名单中的 key 会在 RenderPlan 构造时被静默丢弃，防止 params_json 中的意外数据注入到 Provider API 请求中。

## 文件资产标准

所有音频、字幕和 metadata 都必须落地到本地 `storage/`：

```text
storage/audio/YYYY-MM-DD/audio_xxx.mp3
storage/subtitles/YYYY-MM-DD/subtitle_xxx.json
storage/subtitles/YYYY-MM-DD/subtitle_xxx.srt
storage/metadata/YYYY-MM-DD/job_xxx.json
```

MiniMax URL 输出有效期有限，因此不得把临时 URL 当成长期资产。

## 日志标准

每次生成必须记录：

- `job_id`
- `provider`
- `model`
- `profile_id`
- `text_length`
- `status`
- `duration_ms`
- `usage_characters`
- `provider_trace_id`
- `error_message`

日志禁止输出：

- `MINIMAX_API_KEY`
- `Authorization`
- 完整敏感请求头
