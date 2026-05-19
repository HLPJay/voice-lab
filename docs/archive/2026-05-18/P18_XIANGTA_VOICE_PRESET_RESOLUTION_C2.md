# P18-XIANGTA-VOICE-PRESET-RESOLUTION-C2

## 实现内容

- `VoicePresetMappingService.resolve()` 增加 `coreProfileId` 空值和占位符校验。
- 新增 `VoicePresetProfileNotConfigured` 服务层错误。
- `error_translator.translate()` 增加 `profile_not_configured` 产品错误映射。

## 测试覆盖

- 新增 `tests/xiangta/test_voice_preset_resolution.py`。
- 覆盖 unknown voicePreset、disabled voicePreset、空 `coreProfileId`、占位符、尖括号、`TODO/todo` 前缀。
- 覆盖 `VoicePresetProfileNotConfigured` 到 `profile_not_configured` 的错误翻译。

## 未实现项

- 未修改真实 `voice_mappings.json`。
- 未调用 Core profiles 校验 `coreProfileId` 是否真实存在。
- 未实现 Admin gate、Storage、TTS task、LLM copywriting 或真实 Provider 接入。

## 下一步

`P18-XIANGTA-ADMIN-GATE-C3`
