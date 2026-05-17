# P16-FRONTEND-PROVIDER-CAPABILITY-AUDIT-A0：前端 Provider 能力接入事实归档与处理方案

## 1. 当前事实

本轮问题不是单一字段遗漏，而是前端多个模块各自实现 provider / model / voice / audio_format / 参数控件，导致同一条业务链路中出现 Provider 语义域混用。

已确认现象：

1. UI 可选择 `xiaomi_mimo`，但部分链路仍提交 MiniMax 模型 `speech-2.8-hd`。
2. 主渲染链路 `/api/voice/render` 已出现：
   - `provider=xiaomi_mimo`
   - `model=speech-2.8-hd`
   - `operation=t2a_sync`
   - 请求实际进入 `https://api.xiaomimimo.com/v1/chat/completions`
3. 这说明 provider 已经传对，但绑定数据里的 model 错误。
4. 当前 401 `invalid_key` 不能单独归因为 API key，因为请求进入 MiMo 前模型已经错误。
5. 声音库 preview 链路曾存在 provider body 丢失问题；但当前最新日志指向的是主渲染绑定链路。
6. 绑定管理、快捷绑定、导入克隆、导入设计、导入后快速绑定等入口均存在 model 选择一致性风险。

## 2. 根因定义

根因不是 Xiaomi MiMo adapter 单点失败，而是：

> 前端没有把 Provider Capability 作为统一协议源接入所有 model / voice / audio_format / 参数控件，导致各模块用自己的默认值、硬编码模型和局部刷新逻辑。

具体表现：

1. `model` 被当成全局字段，而不是 provider 下的字段。
2. `provider_voice_id` 被当成全局 voice_id，而不是 provider 下的 voice_id。
3. `audio_format` 被当成全局格式，而不是 provider 下的格式。
4. 人设绑定 `VoiceBinding` 本质是 `provider + model + provider_voice_id + params` 的组合，但前端创建绑定时没有统一约束这四者。
5. import / clone / design / quick bind / binding management 使用不同 UI 代码路径，容易出现遗漏。

## 3. 现有架构边界

本问题必须依赖当前已有架构处理，不新增一套模型注册中心或前端协议。

已有可依赖结构：

| 层级 | 现有模块 | 责任 |
|---|---|---|
| Provider 配置 | `config/providers.yaml` | provider 是否启用、adapter_type、default_model、real_cost |
| Adapter 能力配置 | `config/adapters/*.yaml` | tts.models、tts.default_model、audio_formats、clone/design/provider_voices 能力 |
| 能力合成 | `app/providers/capability_registry.py` | 合成 `ProviderCapability` |
| 能力 API | `/api/voice/capabilities` | 向前端暴露 enabled providers 与能力 |
| 前端能力缓存 | `window._providerCapabilitiesByName` | capability 查询缓存 |
| 前端能力工具 | `provider_capabilities.js` | provider 变化时更新控件能力 |
| 后端校验 | `CapabilityValidator` | 校验 provider/model/audio_format/参数范围 |
| 绑定服务 | `VoiceBindingService` | 写入 `VoiceBinding` 的服务边界 |

处理原则：

1. 不新增独立 provider-model 映射表。
2. 不在前端硬编码 Xiaomi/MiniMax 专用映射，除非作为 capability 加载失败时的兼容 fallback。
3. 不扩展主渲染协议。
4. 不把 voice_clone / voice_design 专用模型混入普通 TTS 绑定模型。
5. 所有 UI 默认值优先来自 `/api/voice/capabilities`。

## 4. 标准数据关系

### 4.1 Provider Capability

前端应以 `/api/voice/capabilities` 返回的数据为唯一事实源：

```text
provider
  enabled
  display_name
  default_model
  metadata.real_cost
  tts
    models
    default_model
    audio_formats
    supports_subtitle
    supports_streaming
    supports_emotion
    speed / vol / pitch
  provider_voices
  voice_clone
  voice_design
  batch
  script
```

### 4.2 绑定数据

人设绑定必须保持同一 provider 语义域：

```text
VoiceBinding
  profile_id
  provider
  model
  provider_voice_id
  params
  priority
```

有效绑定必须满足：

1. `provider` 已启用。
2. `model` 属于该 provider 的 `tts.models`。
3. `provider_voice_id` 属于同一 provider 的可用音色。
4. `params` 只包含该 provider 支持的参数。

### 4.3 关键字段关联

这些字段不能独立选择：

```text
provider + model
provider + provider_voice_id
provider + audio_format
provider + need_subtitle
provider + speed / vol / pitch / emotion
profile + provider -> binding
binding -> provider/model/provider_voice_id
```

## 5. 前端控件关系审计范围

必须统一排查以下控件和入口。

### 5.1 工作台生成

```text
providerSelect
  -> profileSelect
  -> resolved binding
  -> model from binding
  -> audioFormat from provider.tts.audio_formats
  -> needSubtitle / emotion / speed / vol / pitch
  -> /api/voice/render payload
```

风险：

1. audio_format / subtitle / params 是否完全按 provider capability 限制。
2. 生成时使用的 model 来自 binding，若 binding 脏则主渲染继续错误。

### 5.2 声音库试听

```text
voiceProvider
  -> provider voice list
  -> auditionModel from provider.tts.models
  -> audition audio_format from provider.tts.audio_formats
  -> selected provider_voice_id
  -> /api/voice/provider-voices/preview payload
```

已知问题：

1. 曾经 preview body 漏传 provider。
2. audition model 仍有 MiniMax-first 历史风险。
3. audio_format 不能永远默认 `mp3`，MiMo 当前只支持 `wav`。

### 5.3 快捷绑定

```text
voice row provider
  -> quickBindModelSel from provider.tts.models
  -> profile
  -> create binding payload
```

风险：

1. 不得默认 `speech-2.8-hd` 给所有 provider。
2. MiMo voice `Chloe` 绑定时只能使用 MiMo TTS model。

### 5.4 绑定管理

```text
newBindingProvider
  -> newBindingModel from provider.tts.models
  -> newBindingVoiceId from provider voices
  -> create binding payload
```

风险：

1. `newBindingModel` 当前历史上是 MiniMax 模型集合。
2. provider 切换时必须同时刷新 model 和 voice list。

### 5.5 导入克隆 / 导入设计

```text
importCloneProvider / importDesignProvider
  -> importCloneModel / importDesignModel
  -> verify preview payload
  -> importBindModel
  -> create binding payload
```

风险：

1. verify model 和 bind model 不能混用 MiniMax 默认。
2. 如果 verify 本质走 TTS preview，则 model 应来自 `tts.models`。
3. 如果某 provider 的 clone/design 有专用模型，应由对应 adapter / capability 语义承载，不能混入普通绑定 model。

### 5.6 批量长文 / 剧本

```text
batchProvider / batchScriptProvider
  -> capability.batch/script
  -> audio_format from provider.tts.audio_formats
  -> subtitle availability
  -> profile binding
  -> submit payload
```

风险：

1. batch/script 能力不能只看 provider 存在。
2. audio_format / subtitle / segment 参数要按 provider capability 限制。

## 6. 已知问题清单

| 编号 | 问题 | 影响 |
|---|---|---|
| F1 | 前端多个 model 下拉硬编码 MiniMax 模型 | 新 provider 接入后模型错配 |
| F2 | 快捷绑定默认 `speech-2.8-hd` | MiMo 绑定写入 MiniMax model |
| F3 | 绑定管理 model 未完全 provider-aware | 手动创建脏绑定 |
| F4 | 导入克隆 / 导入设计 verify model 硬编码 | 导入验证可能走错模型 |
| F5 | 导入后快速绑定 `importBindModel` 硬编码 | 导入成功后仍可创建脏绑定 |
| F6 | preview audio_format 仍有 `mp3` 默认风险 | MiMo 只支持 `wav` 时被拒绝 |
| F7 | 现有数据库可能已有脏绑定 | 主渲染继续使用错误 model |
| F8 | capability helper 未统一，模块各自读结构 | 后续扩展 provider 容易遗漏 |

## 7. 处理方案

### 阶段 A：事实审计，不改业务逻辑

目标：建立前端控件事实表。

审计字段：

```text
控件 ID
所在模块
字段类型
当前来源
是否硬编码
是否依赖 provider
payload 字段
应接 capability helper
风险等级
```

建议搜索：

```text
speech-2.8-hd
speech-2.8-turbo
speech-2.6
mock-tts
audio_format: 'mp3'
id="*Model"
Provider
provider_voice_id
needSubtitle
paramSpeed
paramVol
paramPitch
emotion
```

交付物：

1. 前端控件审计表。
2. 标注每个控件属于 TTS binding model、verify preview model、clone/design 专用 model 还是 batch/script 参数。

### 阶段 B：整理 capability helper

只整理现有 `provider_capabilities.js`，不新增 API。

建议暴露统一 helper：

```text
getProviderCapability(provider)
getEnabledProviders()
getTtsModels(provider)
getDefaultTtsModel(provider)
getAudioFormats(provider)
getDefaultAudioFormat(provider)
supportsSubtitle(provider)
supportsEmotion(provider)
getParamRange(provider, key)
renderModelOptions(provider, selected)
renderAudioFormatOptions(provider, selected)
```

要求：

1. helper 不直接绑定某个具体页面 DOM。
2. 各模块自己调用 helper 更新自己的控件。
3. `getModelOptionsHtml(provider)` 可保留，但应成为上述 helper 的薄包装。

### 阶段 C：逐模块接入

优先顺序：

1. 绑定管理：`newBindingProvider/newBindingModel/newBindingVoiceId`
2. 快捷绑定：`quickBindModelSel`
3. 导入克隆 / 导入设计：`importCloneModel/importDesignModel/importBindModel`
4. 声音库试听：`auditionModel/audio_format`
5. 工作台参数：`audioFormat/needSubtitle/speed/vol/pitch/emotion`
6. batch / script：`audio_format/subtitle/segment params`

每个模块只做三件事：

1. provider change 时刷新本模块控件。
2. payload 使用控件值。
3. 不再硬编码 MiniMax 默认模型。

### 阶段 D：后端兜底

继续使用已有 `CapabilityValidator`。

必须校验：

1. 创建绑定：`provider/model` 必须匹配。
2. 创建绑定：`provider/provider_voice_id` 必须匹配。
3. preview：`provider/model/audio_format` 必须匹配。
4. import verify：`provider/model/audio_format` 必须匹配。
5. render 前：可增加脏 binding 检测，避免历史数据进入 provider adapter。

### 阶段 E：脏数据处理

先只读报告，不自动修复。

报告字段：

```text
binding_id
profile_id
provider
model
provider_voice_id
status
problem_type
suggested_action
```

问题类型：

```text
MODEL_NOT_IN_PROVIDER_TTS_MODELS
VOICE_NOT_IN_PROVIDER
PROVIDER_DISABLED
VOICE_DEPRECATED
```

修复策略：

1. 对 `xiaomi_mimo + speech-*` 绑定，建议删除后重建。
2. 不自动把 model 改成 `mimo-v2.5-tts`，除非确认 voice_id 属于 MiMo 且业务同意。
3. 修复脚本必须显式 dry-run / apply 两阶段。

## 8. 验收标准

1. 前端主要 model 下拉不再散落 MiniMax 硬编码作为业务默认值。
2. 新 provider 只要 capability 正确，UI 就能显示正确模型、格式和参数范围。
3. `xiaomi_mimo` 不显示 MiniMax TTS model。
4. `minimax` 不显示 MiMo TTS model。
5. 绑定创建无法写入 `provider/model` 错配。
6. 导入克隆、导入设计、导入后快速绑定均使用同一套 capability 模型来源。
7. 参数控件根据 provider 自动启用、禁用、限制范围。
8. 不通过真实 API 验收，只验证 payload、UI 控件状态和后端本地校验。

## 9. 禁止事项

1. 不真实调用 MiniMax / Xiaomi MiMo API。
2. 不把 `401 invalid_key` 单独归因于 API key，必须先确认 provider/model/voice/audio_format 语义域一致。
3. 不把 `Chloe` 改成 MiniMax voice_id 绕过问题。
4. 不把 `speech-2.8-hd` 当成全局默认模型。
5. 不新增独立 provider-model 常量表。
6. 不让通用 capability loader 直接耦合具体业务控件。

## 10. 当前建议下一步

下一步不应直接改 UI，而是先完成阶段 A 的控件审计表。

建议新阶段名：

```text
P16-FRONTEND-PROVIDER-CAPABILITY-AUDIT-B1
```

目标：

1. 全量列出前端 provider/model/audio_format/voice/params 控件。
2. 标注硬编码 MiniMax 的位置。
3. 标注每个控件应接入的 capability helper。
4. 输出最小修改顺序，避免再次散点修复。
