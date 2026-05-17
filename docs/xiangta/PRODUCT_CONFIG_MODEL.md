# P17-XIANGTA-PRODUCT-CONFIG-A0 产品配置模型设计

本任务只定义配置模型和契约，不修改业务代码。

## 配置分组

XiangTa 产品配置分为 6 类：

1. `voice_mappings`
2. `tone_presets`
3. `recipients`
4. `scenes`
5. `copywriting_config`
6. `limits`

MVP 可先使用 JSON 或数据库表，关键是服务层只依赖配置仓储接口，不把文件路径写进编排逻辑。

## voice_mappings

产品声线配置，负责把用户端 `voicePresetId` 映射到 Core `profile_id`。

`voice_mappings.coreProfileId` 必须通过管理端从 Core `GET /api/voice/profiles` 列表选择产生。不得由开发者手写猜测，不得由用户端提交，也不得假设 `xiangta_*` profile 已经存在于 Core DB。

### 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 产品声线 ID，例如 `female-gentle` |
| `label` | string | 用户端展示名 |
| `desc` | string | 用户端描述 |
| `genderStyle` | string or null | 产品展示标签 |
| `suitableRecipients` | string[] | 推荐对象 |
| `recommendedScenes` | string[] | 推荐场景 |
| `defaultTone` | string | 默认 tone |
| `enabled` | boolean | 用户端是否可选 |
| `sortOrder` | number | 排序 |
| `coreProfileId` | string | Core `profile_id`，仅 admin/internal 可见 |
| `providerPolicy` | string or null | `default`、`mock`、`configured` 等 |
| `renderOverrides` | object | 可选 render 参数覆盖 |
| `notes` | string or null | 管理备注 |

### 用户端投影

```json
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
```

### 管理端投影

```json
{
  "id": "female-gentle",
  "label": "温柔女声",
  "desc": "适合想念、晚安、轻声表达",
  "enabled": true,
  "coreProfileId": "<core_profile_id_from_core_profiles>",
  "providerPolicy": "default",
  "renderOverrides": {
    "speed": 0.95,
    "audio_format": "mp3"
  },
  "bindingStatus": "available"
}
```

## tone_presets

tone 是 XiangTa 自有产品配置，不从 Core profiles 读取，也不是 Core profile。tone 可以映射 `copywritingStyle` 和 `renderOverrides`，用于影响文案生成风格以及 Core render 的高层参数。

### 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | `restrained`、`gentle`、`sincere` 等 |
| `label` | string | 展示名 |
| `desc` | string | 展示描述 |
| `styleHint` | string | 文案和编排使用的风格提示 |
| `copywritingStyle` | string | 文案 prompt 风格 |
| `renderOverrides` | object | 可映射到 Core render 参数 |
| `enabled` | boolean | 是否可用 |
| `sortOrder` | number | 排序 |

### 示例

```json
{
  "id": "gentle",
  "label": "温柔",
  "desc": "语气柔和，适合想念、安慰和晚安",
  "styleHint": "轻声、柔和、避免强烈指责",
  "copywritingStyle": "soft",
  "renderOverrides": {
    "speed": 0.92,
    "emotion": "gentle"
  },
  "enabled": true
}
```

## recipients

表达对象配置。MVP 可继续使用现有 `recipients.json`，后续进入配置管理。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | `lover`、`family`、`friend`、`self` |
| `label` | string | 展示名 |
| `hint` | string | 输入提示 |
| `promptContext` | string | 文案生成上下文 |
| `enabled` | boolean | 是否可用 |
| `sortOrder` | number | 排序 |

## scenes

表达场景配置。MVP 可继续使用现有 `scenes.json`。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | `miss`、`sorry`、`thanks`、`comfort`、`night` |
| `label` | string | 展示名 |
| `hint` | string | 输入提示 |
| `promptTemplate` | string | prompt 模板 key |
| `defaultTone` | string | 默认语气 |
| `enabled` | boolean | 是否可用 |
| `sortOrder` | number | 排序 |

## copywriting_config

文案生成配置属于 XiangTa，不属于 Core。

| 字段 | 类型 | 说明 |
|---|---|---|
| `suggestionCount` | number | 默认生成建议数 |
| `styles` | object[] | 克制、温柔、真诚等文案风格 |
| `promptTemplates` | object | scene 到 prompt 文件或模板的映射 |
| `safetyRules` | string[] | 文案边界规则 |
| `rewritePolicy` | object | 是否保留用户原意、是否允许扩写 |

## limits

| 字段 | 类型 | 说明 |
|---|---|---|
| `maxRawTextChars` | number | 用户原始输入上限 |
| `maxTtsChars` | number | TTS 文本上限 |
| `maxSuggestions` | number | 建议数量上限 |
| `allowRealProvider` | boolean | 是否允许真实 provider |
| `defaultAudioFormat` | string | 默认音频格式 |
| `needSubtitleDefault` | boolean | 是否默认生成字幕 |

## 配置读取接口

建议新增配置仓储接口，具体存储可先 JSON 后 DB：

```python
class ProductConfigRepository:
    def list_public_voice_presets(self) -> list[dict]: ...
    def get_voice_mapping(self, voice_preset_id: str) -> dict: ...
    def list_tone_presets(self) -> list[dict]: ...
    def get_tone_preset(self, tone_id: str) -> dict: ...
    def list_recipients(self) -> list[dict]: ...
    def list_scenes(self) -> list[dict]: ...
    def get_limits(self) -> dict: ...
```

`TtsOrchestrator` 不直接依赖这个仓储，而是依赖更窄的服务：

- `VoicePresetMappingService`
- `TonePresetService`

## Bootstrap 返回

用户端 `GET /api/xiangta/bootstrap` 返回：

```json
{
  "ok": true,
  "data": {
    "recipients": [],
    "scenes": [],
    "styles": [],
    "voicePresets": [],
    "tonePresets": [],
    "limits": {},
    "providerStatus": {}
  }
}
```

`voicePresets` 中不包含：

- `coreProfileId`
- `profile_id`
- `core_binding_key`
- `provider`
- `model`
- `provider_voice_id`

## 管理端返回

管理端可以暴露 Core 映射信息：

- `coreProfileId`
- Core profile 展示字段
- binding 状态
- provider policy
- render overrides
- 最近一次校验结果

管理端用于配置，不作为普通用户端契约。
