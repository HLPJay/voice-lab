# 想Ta了后续路线

## 当前阶段

P17-XIANGTA-PRODUCT-CONFIG-A0：只做文档和架构校正，不改业务代码。

已确认：

- A0-A2 骨架保留
- `voice_presets.json` 作为真实声线来源的定位废弃
- `core_binding_key` 废弃
- 用户端不暴露 `profile_id`
- tone 是 XiangTa 自有配置
- 映射逻辑必须独立成 `VoicePresetMappingService`
- Gateway 使用 `CoreRenderTarget` 调 Core render

## B1：配置模型落地

目标：在不接真实前端的前提下，把声线映射从静态 `voice_presets.json` 迁移到产品配置仓储。

B1 不实现真实 Provider 接入，不调用真实 Provider，不读取真实 API key。它只落地产品配置模型和映射服务边界。

建议任务：

1. 优先实现 `ProductConfigRepository`
2. 新增 `VoicePresetMappingService`，必须从配置映射读取 `coreProfileId`
3. 新增 `TonePresetService`
4. 新增 `CoreRenderTarget`
5. 调整 `BootstrapService` 的 `voicePresets` 数据源
6. 调整 `TtsOrchestrator` 依赖映射服务
7. 更新测试 mock 和边界断言

验收：

- 用户端 bootstrap 不含 `core_binding_key`、`profile_id`、`provider`
- TTS dry-run 或测试链路使用 `voicePresetId → coreProfileId`
- `coreProfileId` 必须来自 Core profiles 选择结果
- `TtsOrchestrator` 不直接查配置文件或配置表

## B2：Gateway 接 Core render

目标：让 XiangTa `/tts` 调用 Core `POST /api/voice/render`。

建议任务：

1. `VoiceLabGateway.generate_tts()` 接收 `CoreRenderTarget`
2. 组装 Core `VoiceRenderRequest`
3. 调用 Core 对外 API 或等价 high-level facade
4. 转换 Core `VoiceRenderResponse` 为产品响应
5. 音频 URL 复用 Core assets 下载地址
6. 保留 dry-run 测试方法用于合约测试

验收：

- mock provider 下可生成可下载音频
- 用户端响应仍不暴露 Core 技术字段
- Core 错误经 `ErrorTranslator` 翻译
- 不直接调用 `app.repositories`、`app.providers`、`get_provider()`、`RenderPlan` 或 adapter

## B3：Provider 状态接入

目标：`GET /api/xiangta/provider/status` 读取 Core runtime status。

建议任务：

1. Gateway 新增 `GET /api/voice/runtime/status` 调用
2. `ProviderStatusService` 映射 Core 状态
3. bootstrap 使用真实 providerStatus
4. 增加 quota/auth/network/unknown 等测试

## B4：Admin 配置页面 / API

目标：管理 `voice_mappings`、tone、scenes、recipients、limits。

建议任务：

1. 管理端 voice mappings CRUD
2. 管理端读取 Core profiles 和 bindings
3. 配置校验：profile 是否存在、是否有可用 binding
4. 配置预览：用户端 bootstrap 投影预览

## B5：文案与信笺

目标：补齐产品核心体验。

建议任务：

1. `POST /suggestions` 调文案生成服务
2. `POST /letters` 保存信笺
3. `GET /letters` 列表
4. 本地保存策略和隐私边界

## 不进入当前 MVP

- 用户声音克隆
- 自动发送消息
- 多轮聊天
- 情感诊断
- WebSocket 流式生成
- 批量长文本生成
- 多用户 SaaS 权限系统
