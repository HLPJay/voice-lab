# P9 Provider Capability 架构说明

## 1. 设计目标

P9-CAPABILITY 的目标是把 Voice Lab 从"固定 MiniMax 参数封装"升级为"多 Provider 能力驱动的音频中间层"。

核心目标：

- 用统一 Product Contract 描述 Voice Lab 标准能力。
- 用 Capability Registry 声明不同 Provider 支持什么。
- 用 CapabilityValidator 在后端进入 Provider Adapter 前拒绝不支持的请求。
- 用前端 capabilities 动态调整控件，减少用户撞 422。
- 保持 Provider Adapter 只做协议翻译和真实调用。
- 第一版不走数据库，不做 Admin 可编辑配置。

## 2. 当前架构分层

### Settings

文件：`app/core/config.py`

职责：管连接配置、API key、base_url、默认 provider、默认模型、timeout、storage 路径、并发参数。

一句话：Settings 负责"怎么连接和运行"。

### Provider Registry

文件：`app/providers/registry.py`

职责：provider 名称到 Adapter 的映射，例如 mock → MockSpeechAdapter、minimax → MiniMaxSpeechAdapter。

一句话：Provider Registry 负责"怎么调用"。

### Capability Registry

文件：`app/providers/capability_registry.py`

职责：provider 名称到 ProviderCapability 的映射；mock / minimax 支持哪些能力；暴露 GET /api/voice/capabilities。

一句话：Capability Registry 负责"支持什么"。

### CapabilityValidator

文件：`app/services/capability_validator.py`

职责：请求进入 Service / Provider Adapter 前校验当前 Provider 是否支持该能力；不支持则返回 422 VALIDATION_ERROR；不调用真实 Provider。

一句话：CapabilityValidator 负责"这个请求能不能执行"。

### Provider Adapter

文件：`app/providers/*_speech_adapter.py`

职责：把 Voice Lab 标准参数翻译成厂商 API 参数；调用 MiniMax / Mock / 未来 Provider；处理 Provider 返回结果。

一句话：Provider Adapter 负责"协议翻译和真实调用"。

## 3. 业务调度流

```
前端 UI
  ↓
API 路由层
  ↓
Pydantic Schema 参数校验
  ↓
CapabilityValidator 能力校验
  ↓
Service 业务编排
  ↓
Repository / Storage
  ↓
Provider Registry 获取 Adapter
  ↓
Provider Adapter 调用真实 Provider
  ↓
保存 AudioAsset / SubtitleAsset / VoiceJob / BatchJob
  ↓
返回结果
```

- **前端 UI**：用户交互入口，不感知 Provider 协议细节。
- **API 路由层**：接收请求，路由分发到对应 Service。
- **Pydantic Schema 参数校验**：验证字段类型、必填、格式、数值范围，不涉及 Provider 能力。
- **CapabilityValidator 能力校验**：根据 Provider Capability 声明校验当前 Provider 是否支持该能力，不支持则 422 拒绝，不进入下游。
- **Service 业务编排**：组合 Repository、Storage、Provider 调用，不直接做协议翻译。
- **Repository / Storage**：持久化任务记录、资产文件。
- **Provider Registry**：根据 provider 名称返回对应 Adapter 实例。
- **Provider Adapter**：协议翻译 + 真实 API 调用。

## 4. 参数校验 vs 能力校验

**参数校验**：这个字段值本身是否合法，由 `app/domain/schemas.py` 负责。

例子：

- `file_id > 0`
- `voice_id` 格式正确
- `text` 不超过 `max_length`
- `segment_strategy` 必须是 `auto / paragraph / sentence / line`

**能力校验**：当前 Provider / Model 是否支持这件事，由 `CapabilityValidator` 负责。

例子：

- Provider 是否支持字幕
- Provider 是否支持 flac
- Provider 是否支持流式
- Provider 是否支持声音克隆
- Provider 的 speed / vol / pitch 范围

两者的核心区别：参数校验问的是"值对不对"，能力校验问的是"这个 Provider 能不能"。

## 5. P9 当前完成状态

### P9-CAPABILITY1 已完成

- 新增 ProviderCapability 数据结构。
- 新增 mock / minimax 能力声明。
- 新增 capability_registry。
- 新增 GET /api/voice/capabilities。
- 不走数据库。
- 不调用真实 Provider。

### P9-CAPABILITY1-FIX 已完成

- NumericRange min <= max。
- VoiceIdConstraint 正则可编译。
- TTSCapability default_model 必须在 models 中。
- BatchCapability segment_strategies 不能为空。
- ProviderCapability metadata 防止 API key 泄露（精确 key 匹配，`api_key_configured` 通过，`minimax_api_key` 被拦截）。
- 测试保护能力声明不被写错。

### P9-CAPABILITY2 已完成

- 新增 CapabilityValidator。
- 接入单条 TTS、异步 TTS、流式 TTS、长文本批量、剧本批量、声音克隆、声音设计、Provider 音色试听、远端音色导入。
- 不支持能力时返回 422 VALIDATION_ERROR。
- 不进入 Provider Adapter。

### P9-CAPABILITY2-FIX 已完成

- verify=true 的远端音色导入会校验 TTS 能力和 model。
- verify=false 只做登记导入能力校验。

### P9-CAPABILITY3 已完成

- 前端启动加载 /api/voice/capabilities。
- 缓存 provider capabilities。
- 动态调整文本长度、格式、字幕、流式、情绪、参数范围、批量策略、克隆/设计约束。
- capabilities 加载失败时降级为静态配置。

### P9-CAPABILITY3-FIX 已完成

- setControlDisabled() 改为 `el.title = title || ''`，避免 Provider 能力恢复后旧提示残留。
- 新增 _capabilitiesFailureNotified，capabilities 加载失败 toast 只提示一次。
- capabilities 加载成功后同步已有 provider select 选项。

## 6. 当前不做什么

- 不走数据库配置。
- 不做 Admin 可编辑能力配置。
- 不做 Provider 健康探测。
- 不接 OpenAI / Azure / ElevenLabs。
- 不把 capability 当作实时可用性状态。
- 不让 Adapter 承担主要能力判断。
- 不开放多人 SaaS。
- 不承诺公网多租户部署。

## 7. 后续路线

### P9-CAPABILITY4：Admin 能力矩阵只读展示

目标：Admin 页面展示 mock / minimax 能力矩阵；展示 TTS、流式、字幕、克隆、设计、音频格式、文本长度、参数范围；只读，不允许编辑。

### P9-FE1：前端 JS 模块化

目标：拆分 index.html 中的大型 JS；将 capability、history、batch、voices、advanced 等模块分离；降低后续维护风险。

### P9-E2E1：关键路径浏览器测试

目标：用 Playwright 或类似工具验证前端关键路径；覆盖单条生成、长文本、剧本、能力加载失败降级、provider 切换。

### P10-CONFIG：Admin 系统配置中心

目标：后期考虑数据库 override；只允许编辑安全配置项；必须有校验、审计、回滚；不直接编辑底层 Provider 协议。

## 8. 关键风险与防护

风险 1：capability 被误认为健康检查
防护：capability 只描述理论能力，runtime status 负责调用状态。

风险 2：能力声明写错
防护：Pydantic model_validator + tests/test_capabilities.py。

风险 3：前端和后端规则不一致
防护：前端和后端都从 /api/voice/capabilities / Capability Registry 获取同一份能力声明。

风险 4：Provider Adapter 变胖
防护：Adapter 只做协议翻译，能力判断在 CapabilityValidator。

风险 5：前端 DOM ID 不匹配
防护：P9-CAPABILITY3 使用 null-check，后续需要 JS 模块化和 E2E 测试。

## 9. 当前测试基线

572 passed, 6 skipped
