# P16-XIAOMI-MIMO-TTS-B1：实现 Xiaomi MiMo Chat TTS 最小可行路径

## 1. 阶段目标

基于 P16-ADAPTER-PLUGIN-DISCOVERY-B1 机制，实现 Xiaomi MiMo Chat TTS 最小可行接入路径。

**本阶段只实现**：
- Xiaomi MiMo Chat TTS adapter
- render_sync（mimo-v2.5-tts 模型）
- wav 非流式输出
- 静态预置音色 list_voices
- base64 音频解析
- mock transport 单元测试
- provider 默认 disabled

**本阶段不实现**：
- design_voice / clone_voice
- render_stream / async task
- delete_voice / subtitle
- batch / script / UI 改造

## 2. 实际新增文件

| 文件 | 用途 |
|---|---|
| `app/providers/xiaomi_mimo_chat_tts_adapter.py` | XiaomiMiMoChatTTSAdapter 实现 |
| `config/adapters/xiaomi_mimo_chat_tts.yaml` | AdapterConfig（含 plugin.import_path） |
| `tests/test_xiaomi_mimo_chat_tts_adapter.py` | 32 项测试覆盖 |

## 3. 实际修改文件

| 文件 | 改动 |
|---|---|
| `config/providers.yaml` | 新增 disabled xiaomi_mimo provider entry |

## 4. 未修改文件（禁止项）

| 文件 | 状态 |
|---|---|
| `app/providers/__init__.py` | **未修改** |
| `app/providers/adapter_type_registry.py` | **未修改** |

Xiaomi adapter 通过 `config/adapters/xiaomi_mimo_chat_tts.yaml` 中的 `plugin.import_path` 自动发现，无需修改注册表源码。

## 5. Xiaomi MiMo Chat TTS Adapter 说明

**类名**：`XiaomiMiMoChatTTSAdapter`
**provider_name**：`xiaomi_mimo`
**基类**：`SpeechProvider`

### 5.1 请求映射（render_sync）

**请求 URL**：`POST https://api.xiaomimimo.com/v1/chat/completions`

**Header**：`api-key: $MIMO_API_KEY`（不是 `Authorization: Bearer`）

**请求体**：
```json
{
  "model": "mimo-v2.5-tts",
  "messages": [
    {"role": "assistant", "content": "要合成的文本"}
  ],
  "audio": {"format": "wav", "voice": "冰糖"}
}
```

**关键映射规则**：
- `plan.model` 或默认 `mimo-v2.5-tts` → payload.model
- `plan.provider_voice_id` 或默认 `mimo_default` → payload.audio.voice
- `plan.processed_text` 优先（无则用 `plan.text`）→ messages[role=assistant].content
- 输出格式固定 `wav`

### 5.2 响应解析

**响应格式**：
```json
{
  "choices": [{
    "message": {
      "audio": {"data": "<base64 wav>", "format": "wav"}
    }
  }]
}
```

**解析步骤**：
1. 验证 `choices` 非空
2. 提取 `choices[0].message.audio.data`（base64 字符串）
3. `base64.b64decode()` 解码为 WAV bytes
4. 保存到 `storage_path("audio", "{id}.wav")`
5. 返回 `ProviderRenderResult`

### 5.3 错误处理

| 错误场景 | 抛出异常 |
|---|---|
| MIMO_API_KEY 缺失或 "replace_me" | `ProviderNotConfigured` |
| HTTP 4xx/5xx | `ProviderError`（status code 在消息中） |
| choices 为空 | `ProviderError`("missing choices") |
| audio.data 缺失 | `ProviderError`("missing audio data") |
| base64 解码失败 | `ProviderError`("audio decode failed") |
| audio bytes 为空 | `ProviderError`("audio is empty") |

**错误信息不包含 API key。**

## 6. AdapterConfig 说明

**文件**：`config/adapters/xiaomi_mimo_chat_tts.yaml`

```yaml
adapter_type: "xiaomi_mimo_chat_tts"

plugin:
  import_path: "app.providers.xiaomi_mimo_chat_tts_adapter.XiaomiMiMoChatTTSAdapter"

default_base_url: "https://api.xiaomimimo.com"

tts:
  supported: true
  models: ["mimo-v2.5-tts"]
  default_model: "mimo-v2.5-tts"
  max_text_chars: 5000
  audio_formats: ["wav"]
  supports_subtitle: false
  supports_streaming: false
  supports_emotion: true

batch:
  supported: false

voice_clone:
  supported: false

voice_design:
  supported: false
```

**关键设计决策**：
- `supports_streaming: false` — Xiaomi MiMo 的流式是"兼容模式"，推理完成后一次返回，不是低延迟流式
- `models` 只有 `mimo-v2.5-tts`，不包含 voicedesign/voiceclone 模型（B1 范围外）
- `audio_formats` 只有 `wav`（非流式只支持 wav）

## 7. ProviderConfig 说明

**文件**：`config/providers.yaml`

```yaml
- name: "xiaomi_mimo"
  display_name: "Xiaomi MiMo"
  enabled: false
  adapter_type: "xiaomi_mimo_chat_tts"
  real_cost: true
  api_key_env: "MIMO_API_KEY"
  tts:
    enabled: true
  batch:
    enabled: false
  voice_clone:
    enabled: false
  voice_design:
    enabled: false
```

**关键决策**：
- `enabled: false` — provider 默认 disabled，不影响现有系统
- `real_cost: true` — 真实计费 provider
- `api_key_env: "MIMO_API_KEY"` — 从环境变量读取 API key

## 8. plugin discovery 接入方式

Xiaomi adapter 通过 `config/adapters/xiaomi_mimo_chat_tts.yaml` 中的 `plugin.import_path` 被自动发现和注册：

1. `get_adapter_type_adapter("xiaomi_mimo_chat_tts")` 被调用
2. `load_adapter_plugins_from_config()` 扫描 `config/adapters/*.yaml`
3. 找到 `xiaomi_mimo_chat_tts.yaml` 的 `plugin.import_path`
4. `register_adapter_type_from_import_path()` 动态导入 `XiaomiMiMoChatTTSAdapter` 类
5. 注册到 `ADAPTER_TYPE_REGISTRY`

**无需修改任何注册表源码。**

## 9. 静态 list_voices

Xiaomi MiMo 预置音色列表（不调用远端 API）：

| Voice ID | Name | Language | Gender |
|---|---|---|---|
| mimo_default | MiMo-默认 | zh | neutral |
| 冰糖 | 冰糖 | zh | female |
| 茉莉 | 茉莉 | zh | female |
| 苏打 | 苏打 | zh | male |
| 白桦 | 白桦 | zh | male |
| Mia | Mia | en | female |
| Chloe | Chloe | en | female |
| Milo | Milo | en | male |
| Dean | Dean | en | male |

## 10. 为什么 B1 不实现 design_voice

- Xiaomi MiMo voice design 需要 `mimo-v2.5-tts-voicedesign` 模型
- 这是另一个模型体系，与 B1 最小可行路径不同
- 后续 P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 分析语义映射

## 11. 为什么 B1 不实现 clone_voice

- Xiaomi MiMo voice cloning 需要 `mimo-v2.5-tts-voiceclone` 模型
- 需要音频文件上传，复杂度高于 B1 范围
- 后续 P16-XIAOMI-MIMO-TTS-VOICE-CLONE-A0 分析

## 12. 为什么 supports_streaming=false

Xiaomi MiMo 的流式是"兼容模式"：
- `stream=true` 时，所有推理完成后以流式格式返回一次
- 不是低延迟实时流式
- 不适合当前系统的低延迟 streaming 场景
- B1 专注同步 TTS

## 13. 测试结果

| 测试套件 | 结果 |
|---|---|
| test_xiaomi_mimo_chat_tts_adapter.py | 32 passed ✅ |
| test_adapter_plugin_discovery.py | 44 passed ✅ |
| test_adapter_config_loader.py | 51 passed ✅ |
| test_provider_config_dynamic.py | 47 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |
| **总计** | **257 passed** |

### 测试覆盖

- plugin discovery（xiaomi_mimo_chat_tts 通过 YAML 发现）
- ProviderConfig（xiaomi_mimo disabled、real_cost=true、api_key_env=MIMO_API_KEY）
- AdapterConfig（tts supported、streaming=false、wav format）
- render_sync 请求构造（URL、headers、body）
- render_sync 响应解析（base64 decode、WAV 保存）
- list_voices（9 个预置音色、不发 HTTP）
- 错误处理（缺 API key、缺 audio data、无效 base64、HTTP 500）
- 无真实外部 API 调用

## 14. 剩余风险

无阻塞风险。

**非阻塞观察项**：
- B1 未验证真实 API 调用（需要真实 MIMO_API_KEY）
- voice design / voice clone 语义映射待分析
- `supports_emotion: true` 但实际通过文本描述控制，效果待验证

## 15. 下一阶段建议

### 推荐：P16-XIAOMI-MIMO-TTS-B1-CHECK

**目标**：验证 Xiaomi MiMo Chat TTS B1 实现

**验证内容**：
- `get_provider("xiaomi_mimo")` 在 enabled=true 时返回 `XiaomiMiMoChatTTSAdapter` 实例
- 集成测试（需要真实或 mock MIMO_API_KEY）
- capability API 暴露 xiaomi_mimo（enabled=true 时）

### 备选

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 | 分析 MiMo voicedesign 语义映射 | B1-CHECK 后 |
| P16-XIAOMI-MIMO-TTS-VOICE-CLONE-A0 | 分析 MiMo voiceclone 语义映射 | B1-CHECK 后 |
| P16-OPENAI-COMPATIBLE-TTS-A0 | 设计通用 OpenAI-compatible TTS adapter | 可后置 |

## 16. 明确未做

- **未调用真实小米 API** — 所有测试使用 mock/fake transport
- **未实现 design_voice / clone_voice / render_stream / async task**
- **未改 RenderPlan / VoiceBinding / ProviderVoice / VoiceProfile schema**
- **未改 resolve_binding**
- **未修改 app/providers/__init__.py**
- **未修改 app/providers/adapter_type_registry.py**
- **未做 UI 改造**
