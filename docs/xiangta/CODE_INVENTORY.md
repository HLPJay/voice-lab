# 想Ta了现有代码保留 / 调整 / 废弃清单

## 总结

A0-A2 的架构骨架保留。需要调整的是数据来源和映射语义，不是重写整个产品层。

| 类别 | 处置 |
|---|---|
| 保留 | API 层、服务分层、产品模型、prompts、错误翻译、测试体系 |
| 调整 | bootstrap 数据源、TTS 映射服务、Gateway 调用 Core render |
| 废弃 | `voice_presets.json` 作为真实声线来源、`core_binding_key`、PresetMapper 的声线映射职责 |
| 迁移 | `tone_presets.json` 进入产品配置管理，不从 Core 读取 |

## 保留不动

| 文件 | 理由 |
|---|---|
| `src/xiangta/__init__.py` | 包标记和产品层说明 |
| `src/xiangta/api/__init__.py` | 包标记 |
| `src/xiangta/services/__init__.py` | 声明服务边界 |
| `src/xiangta/models/*.py` | 产品层数据模型，与 Core 声线映射无直接冲突 |
| `src/xiangta/prompts/*.md` | XiangTa 自有文案模板 |
| `src/xiangta/configs/recipients.json` | 可先保留，后续迁移配置管理 |
| `src/xiangta/configs/scenes.json` | 可先保留，后续迁移配置管理 |
| `src/xiangta/services/error_translator.py` | 错误翻译层方向正确 |
| `src/xiangta/services/copywriting_service.py` | TODO 骨架保留 |
| `src/xiangta/services/letter_service.py` | TODO 骨架保留 |

## 保留结构，调整实现

| 文件 | 当前问题 | 调整方向 |
|---|---|---|
| `src/xiangta/api/schemas.py` | `VoicePresetItem` 暴露 `core_binding_key`，`TtsContract` 回显 `coreBindingKey` | 用户端改为 `voicePresetId`，去掉 Core 字段 |
| `src/xiangta/api/routes.py` | 路由结构正确，注释仍以 dry-run 为主 | 后续接真实 Gateway，但用户端契约保持产品语义 |
| `src/xiangta/services/product_service.py` | 工厂仍组装 `PresetMapper` | 改为组装 `VoicePresetMappingService` 和 tone 配置服务 |
| `src/xiangta/services/bootstrap_service.py` | 从 `voice_presets.json` 读声线 | 从产品配置 `voice_mappings` 聚合用户端 `voicePresets` |
| `src/xiangta/services/tts_orchestrator.py` | 依赖 `PresetMapper.resolve_binding()` 和 `core_binding_key` | 依赖 `VoicePresetMappingService.resolve()`，组装 `CoreRenderTarget` |
| `src/xiangta/services/voice_lab_gateway.py` | 公共方法接收 `core_binding_key` | 改为接收 `CoreRenderTarget`，调用 Core `POST /api/voice/render` |
| `src/xiangta/services/provider_status_service.py` | 固定 `not_integrated` | 读取 Core `GET /api/runtime/status` 后翻译 |
| `src/xiangta/config/loader.py` | 读取 `voice_presets.json` | 保留 JSON loader 能力，但声线来源改为配置仓储 |
| `src/xiangta/config/bootstrap_config.py` | 静态 limits/styles 可用 | 后续迁移到产品配置管理 |

## 废弃或替换

| 文件 / 概念 | 处置 | 替代 |
|---|---|---|
| `src/xiangta/configs/voice_presets.json` | 不再作为真实声线来源 | `voice_mappings` 产品配置 |
| `core_binding_key` | 废弃 | 内部 `coreProfileId` / `profile_id` |
| `PresetMapper.resolve_binding()` 的声线映射职责 | 废弃 | `VoicePresetMappingService.resolve()` |

## 迁移而非废弃

| 文件 | 处置 |
|---|---|
| `src/xiangta/configs/tone_presets.json` | 保留为 XiangTa 自有产品配置，后续迁移到 DB 或 Admin 可编辑 JSON |

tone 不是 Core profile。它描述的是产品表达风格，可以映射到：

- copywriting prompt style
- render `emotion`
- render `speed`
- render `pitch`
- voice mapping override

## 测试处置

| 测试 | 处置 |
|---|---|
| `tests/xiangta/test_bootstrap_api.py` | 保留，更新 bootstrap mock 数据 |
| `tests/xiangta/test_bootstrap_service.py` | 保留，更新 voicePresets 数据源断言 |
| `tests/xiangta/test_tts_api.py` | 保留，更新请求/响应字段 |
| `tests/xiangta/test_tts_orchestrator.py` | 保留，mock `VoicePresetMappingService` |
| `tests/xiangta/test_voice_lab_gateway_contract.py` | 保留，改为 `CoreRenderTarget` 合约 |
| `tests/xiangta/test_boundary_contract.py` | 保留，禁止泄漏字段从 `core_binding_key` 调整为 `profile_id/provider/model/provider_voice_id` 等 |
| `tests/xiangta/test_preset_mapper.py` | 声线部分退役；tone 部分可迁移为 tone 配置服务测试 |

