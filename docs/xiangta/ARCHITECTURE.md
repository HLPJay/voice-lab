# 想Ta了系统架构

## 架构原则

1. 产品层不暴露 provider 参数。
2. 用户端不暴露 Core `profile_id`。
3. TtsOrchestrator 不直接查配置表。
4. VoiceLabGateway 是 XiangTa 调用 Core 的唯一边界。
5. A0-A2 的服务骨架保留，替换早期临时声线映射抽象。

## 分层

```text
┌────────────────────────────────────────────┐
│ Mobile App / H5 / PWA                      │
│ voicePresetId, tone, recipient, scene      │
└──────────────────────┬─────────────────────┘
                       │ HTTP JSON
┌──────────────────────▼─────────────────────┐
│ XiangTa Backend                            │
│ routes → ProductService → 子服务 → Gateway │
│                                            │
│ VoicePresetMappingService:                 │
│   voicePresetId → coreProfileId            │
│                                            │
│ TonePresetService / ConfigRepository:      │
│   tone → style hints / render overrides    │
└──────────────────────┬─────────────────────┘
                       │ 内部 HTTP 或服务调用
┌──────────────────────▼─────────────────────┐
│ Voice Lab Core                             │
│ profiles / bindings / render / assets      │
│ runtime status / capabilities              │
└────────────────────────────────────────────┘
```

## TTS 调用流程

```text
POST /api/xiangta/tts
  { text, voicePresetId, tone, recipient, scene }
        ↓
TtsOrchestrator.generate()
  1. 校验 text
  2. VoicePresetMappingService.resolve(voicePresetId)
       → ProductVoiceMapping(coreProfileId, providerPolicy, overrides)
  3. TonePresetService.resolve(tone)
       → toneHint, speed/pitch/emotion 等高层参数
  4. 组装 CoreRenderTarget
  5. VoiceLabGateway.generate_tts(text, target, metadata)
       → Core POST /api/voice/render
  6. 组装产品响应
        ↓
{ taskId, status, audioUrl, durationMs, voicePresetId, tone }
```

## 关键内部对象

```python
@dataclass
class ProductVoiceMapping:
    voice_preset_id: str
    label: str
    core_profile_id: str
    provider_policy: str | None = None
    enabled: bool = True
    render_overrides: dict[str, object] = field(default_factory=dict)


@dataclass
class CoreRenderTarget:
    profile_id: str
    provider: str | None = None
    need_subtitle: bool = True
    output_format: str = "url"
    audio_format: str = "mp3"
    speed: float | None = None
    vol: float | None = None
    pitch: int | None = None
    emotion: str | None = None
```

`ProductVoiceMapping` 属于 XiangTa 产品配置层。`CoreRenderTarget` 属于 Gateway 边界层，用于把内部目标明确传给 Core。

## 服务职责

| 模块 | 职责 |
|---|---|
| `routes.py` | 暴露产品 API，只接受产品语义字段 |
| `schemas.py` | 用户端请求/响应模型，移除 `core_binding_key` |
| `ProductService` | 产品服务门面，协调子服务 |
| `BootstrapService` | 聚合用户端启动配置 |
| `TtsOrchestrator` | 校验、映射、调用 Gateway、组装响应 |
| `VoicePresetMappingService` | `voicePresetId` 到 Core `profile_id` 的独立映射服务 |
| `VoiceLabGateway` | 调用 Core API，隐藏 Core 技术细节 |
| `ErrorTranslator` | Core 技术错误转成产品友好错误 |

## 与 A0-A2 的差异

| 维度 | A0-A2 临时方案 | 修正后方案 |
|---|---|---|
| 声线来源 | `voice_presets.json` 静态定义 | `voice_mappings` 产品配置，映射 Core profiles |
| 映射 key | `core_binding_key` | 用户端 `voicePresetId`，服务端 `coreProfileId` |
| 映射服务 | `PresetMapper.resolve_binding()` | `VoicePresetMappingService.resolve()` |
| tone | 与声线一起被 `PresetMapper` 处理 | XiangTa 自有产品配置，可映射 render overrides |
| Gateway 输入 | `core_binding_key` 字符串 | `CoreRenderTarget` |
| Core 调用 | dry-run 为主 | `POST /api/voice/render` |

