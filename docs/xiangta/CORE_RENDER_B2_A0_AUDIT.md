# XiangTa Core Render B2-A0 Audit

## 1. 审查范围

本次只读审查覆盖：

- Core render API:
  - `app/api/voice_render.py`
  - `app/domain/schemas.py`
  - `app/services/voice_render_service.py`
- Core mock provider / provider registry:
  - `app/providers/mock_speech_adapter.py`
  - `app/providers/registry.py`
  - `app/providers/base.py`
  - `app/core/config.py`
  - `config/providers.yaml`
  - `config/adapters/mock.yaml`
- Profile / binding / provider voice / DB:
  - `app/api/voice_profiles.py`
  - `app/api/voice_bindings.py`
  - `app/repositories/voice_profile_repo.py`
  - `app/repositories/voice_binding_repo.py`
  - `app/repositories/provider_voice_repo.py`
  - `app/models/voice_profile.py`
  - `app/models/voice_binding.py`
  - `app/models/provider_voice.py`
  - `app/core/database.py`
- Asset / download:
  - `app/api/voice_assets.py`
  - `app/services/asset_service.py`
- XiangTa current boundary:
  - `src/xiangta/services/voice_lab_gateway.py`
  - `src/xiangta/services/tts_orchestrator.py`
  - `src/xiangta/services/error_translator.py`
  - `src/xiangta/configs/voice_mappings.json`

## 2. 当前 XiangTa B1 状态

当前 XiangTa 已完成：

- `ProductConfigRepository` 落地
- `BootstrapService` 接入产品配置仓储
- `VoicePresetMappingService` / `TonePresetService` 落地
- `TtsOrchestrator` 已从 `PresetMapper` 切到 `VoicePresetMappingService + TonePresetService`
- `VoiceLabGateway.generate_tts_dry_run()` 已提供安全 dry-run contract
- 用户端已不暴露 `coreBindingKey / profile_id / provider / model / provider_voice_id`

当前仍未完成：

- `VoiceLabGateway.generate_tts()` 尚未接 Core render
- XiangTa 仍未真正生成音频
- `ProviderStatusService` 仍是产品层 `not_integrated` 占位

## 3. Core render public API

| 项 | 结论 |
|---|---|
| API path | `POST /api/voice/render` |
| Request schema | `VoiceRenderRequest` |
| Response schema | `VoiceRenderResponse` |
| 是否需要 DB session | 需要。路由通过 `Depends(get_session)` 注入 `sqlmodel.Session` |
| 是否会触发 Provider | 会。`VoiceRenderService.render_voice()` 内部会 `get_provider(provider).render_sync(plan)` |
| 是否支持 mock | 支持。`provider="mock"` 时会走 `MockSpeechAdapter`，前提是 profile/binding/provider_voice 条件满足 |

补充结论：

- HTTP method/path 已稳定：`POST /api/voice/render`
- 路由层先执行 `capability_validator.validate_tts(...)`
- 然后调用 `VoiceRenderService.render_voice(session, request, voice_overrides=...)`
- `VoiceRenderService` 会：
  - 解析 provider
  - 解析 binding
  - 校验 binding 对应 `provider_voice`
  - 生成 `RenderPlan`
  - 调用 provider adapter
  - 保存 `VoiceJob` / `AudioAsset` / `SubtitleAsset`

### 3.1 Request 字段

`VoiceRenderRequest` 当前字段：

- 必填：
  - `text: str`
- 有默认值但在 XiangTa B2-B1 中应显式传入：
  - `profile_id: str = "deep_night_programmer"`
  - `need_subtitle: bool = True`
  - `output_format: Literal["hex", "url"] = "hex"`
  - `audio_format: Literal["mp3", "wav", "flac"] = "mp3"`
  - `confirm_cost: bool = False`
- 可选：
  - `provider: str | None`
  - `speed: float | None`
  - `vol: float | None`
  - `pitch: int | None`
  - `emotion: str | None`

### 3.2 Response 字段

`VoiceRenderResponse` 当前字段：

- `job_id: str`
- `status: str`
- `audio_asset: AudioAssetResponse | None`
- `subtitle_asset: SubtitleAssetResponse | None`
- `provider: str`
- `model: str`

其中：

- `audio_asset.id`
- `audio_asset.url`
- `audio_asset.duration_ms`
- `audio_asset.format`

对 XiangTa B2-B1 最关键。

### 3.3 错误路径

Core render 相关错误主要来自：

- Pydantic / FastAPI request validation -> `422 VALIDATION_ERROR`
- `capability_validator.validate_tts(...)` -> `422 VALIDATION_ERROR`
- `resolve_binding(...)`
  - `PROFILE_NOT_FOUND` -> 404
  - `BINDING_NOT_FOUND` -> 404
- `validate_binding_provider_voice(...)`
  - `VALIDATION_ERROR` -> 422
- provider registry / provider execution
  - `UNSUPPORTED_PROVIDER` -> 400 或经 validator 转 422
  - `PROVIDER_ERROR` -> 400
- 未处理异常 -> 500 `INTERNAL_ERROR`

### 3.4 XiangTa B2-B1 应调用 HTTP API 还是进程内 facade

结论：

- **首选：HTTP API `POST /api/voice/render`**
- **不建议 B2-B1 直接进程内调用 `VoiceRenderService.render_voice()`**

原因：

1. `VoiceRenderService.render_voice()` 不是当前完整 public contract。
   - 路由层还有 `capability_validator.validate_tts(...)`
   - 直接调 service 会绕过这一层
2. HTTP 路径天然保持与 Core public API 等价
3. 更符合 XiangTa 作为“Core public API 产品化包装层”的定位

如果未来必须做进程内调用，则需要 **新增一个等价 high-level facade**，把下面两步一起封装：

1. `capability_validator.validate_tts(...)`
2. `VoiceRenderService.render_voice(...)`

当前代码库里，**还没有一个现成的、完全等价于 `POST /api/voice/render` 的进程内 facade**。

### 3.5 哪些对象绝对不能直接调用

XiangTa 不得直接调用：

- `app.repositories.*`
- `app.providers.*`
- `get_provider()`
- `RenderPlan`
- `VoiceBinding` / `VoiceProfile` ORM
- `adapter.render_sync()`

即使未来选择进程内方式，也只能在 `VoiceLabGateway` 内调用 Core public API 或等价 high-level facade，不能越级。

## 4. Core request / response 字段映射

| XiangTa 内部字段 | Core 字段 | 说明 |
|---|---|---|
| `text` | `text` | 直接映射 |
| `CoreRenderTarget.profile_id` | `profile_id` | 来自 `ProductVoiceMapping.core_profile_id` |
| `CoreRenderTarget.provider` | `provider` | B2-B1 测试路径应显式传 `mock`，不能留空 |
| `CoreRenderTarget.need_subtitle` | `need_subtitle` | 直接映射 |
| `CoreRenderTarget.output_format` | `output_format` | XiangTa B2-B1 应使用 `url` |
| `CoreRenderTarget.audio_format` | `audio_format` | 直接映射，推荐 `mp3` |
| `CoreRenderTarget.speed` | `speed` | 来自 voice/tone `render_overrides` |
| `CoreRenderTarget.vol` | `vol` | 来自 `render_overrides` |
| `CoreRenderTarget.pitch` | `pitch` | 来自 `render_overrides` |
| `CoreRenderTarget.emotion` | `emotion` | 来自 `render_overrides` |
| Core `job_id` | XiangTa `taskId` | 直接映射 |
| Core `status=success` | XiangTa `status=completed` | 建议做产品层归一化，保持 XiangTa schema 语义 |
| Core `audio_asset.url` | XiangTa `audioUrl` | 可直接使用 |
| Core `audio_asset.duration_ms` | XiangTa `durationMs` | 直接映射 |
| `len(text)` | XiangTa `charCount` | 仍由 XiangTa 计算更稳定 |
| Core `provider` | 不返回给用户端 | 可留在日志 / admin / debug |
| Core `model` | 不返回给用户端 | 可留在日志 / admin / debug |

## 5. Mock provider 策略

### 5.1 Core mock provider 是否存在

存在：

- adapter 类：`app.providers.mock_speech_adapter.MockSpeechAdapter`
- provider name：`mock`
- provider config：`config/providers.yaml`
- adapter config：`config/adapters/mock.yaml`

### 5.2 mock provider 是否生成可下载音频

是。

`MockSpeechAdapter.render_sync(plan)` 会：

- 生成本地 silent WAV 文件
- 返回 `ProviderRenderResult(audio_path=...)`
- `AssetService.save_assets(...)` 再把它保存成 `AudioAsset`
- 最终 `VoiceRenderResponse.audio_asset.url` 形如：
  - `/api/voice/assets/{audio_id}/download`

因此 B2-B1 使用 mock provider 也能拿到可下载 `audioUrl`。

### 5.3 mock provider 是否需要 API key

不需要。

证据：

- `config/providers.yaml` 中 `mock.api_key_env = null`
- `mock.real_cost = false`
- `config/adapters/mock.yaml` 仅声明 mock 能力，不依赖真实 endpoint

### 5.4 B2-B1 如何强制 mock provider

结论：**B2-B1 测试必须显式强制 `provider="mock"`。**

不要依赖：

- `provider=None`
- `providerPolicy="default"`
- Core 全局默认 provider

原因：

- `VoiceRenderService.render_voice()` 中：
  - `provider = request.provider or settings.voice_provider`
- `app/core/config.py` 默认 `settings.voice_provider = "minimax"`

如果 XiangTa B2-B1 不显式传 `mock`，就可能回落到 `minimax`。

### 5.5 B2-B1 推荐 mock 策略

测试路径建议：

1. `VoicePresetMappingService` 解析到一个已存在的 `core_profile_id`
2. `VoiceLabGateway.generate_tts()` 发送/组装 Core render 请求时显式设置：
   - `provider="mock"`
   - `output_format="url"`
3. 不读取真实 API key
4. 不调用 minimax/xiaomi_mimo/openai

结论：

- **B2-B1 的测试策略必须使用 mock provider**
- **真实 Provider 调用不属于 B2-B1**

## 6. Profile / Binding 前置条件

### 6.1 Core render 对 profile / binding 的要求

Core render 不是只要有 `profile_id` 就能跑。

它要求：

1. `profile_id` 对应 `VoiceProfile` 存在且 `is_active=True`
2. 对应 provider 有 `VoiceBinding(status=available)`
3. 该 binding 对应的 `ProviderVoice` 记录存在且 `status=available`

否则会失败：

- profile 不存在 -> `PROFILE_NOT_FOUND`
- 无可用 binding -> `BINDING_NOT_FOUND`
- binding 指向的 provider voice 缺失/废弃 -> `VALIDATION_ERROR`

### 6.2 当前默认 seed 是否足够

`app/core/database.py::seed_defaults()` 当前会创建：

- `VoiceProfile(id="deep_night_programmer")`
- `VoiceBinding(provider="minimax", ...)`
- `VoiceBinding(provider="mock", ...)`

但它**没有同时创建对应的 `ProviderVoice` 记录**。

这意味着：

- 仅依赖默认 seed，mock binding 不一定能通过 `validate_binding_provider_voice()`

测试里现有可用路径来自 `tests/conftest.py::seed_mock_binding`，它会额外创建：

- `ProviderVoice(provider="mock", provider_voice_id="mock_voice", status="available")`

### 6.3 `<core_profile_id_from_core_profiles>` 占位在 B2-B1 如何处理

当前 `src/xiangta/configs/voice_mappings.json` 中 `coreProfileId` 仍是占位：

- `<core_profile_id_from_core_profiles>`

这在 B2-B1 测试中不能直接使用。

### 6.4 B2-B1 mock 策略选项

#### 选项 A：测试中创建临时 Core profile + mock binding + provider voice

优点：

- 最独立
- 不依赖默认 seed

缺点：

- XiangTa 测试要重复构造更多 Core fixture
- 维护成本更高

#### 选项 B：使用已有 seed profile + 再补 mock binding / provider voice

优点：

- 贴近现有 Core 测试习惯
- 与 `tests/conftest.py::seed_profile + seed_mock_binding` 一致

缺点：

- 仍需要 XiangTa 端把 `coreProfileId` 指向 seed profile

#### 选项 C：XiagTa fixture 中把 `voice_mappings` 指向已有 Core profile

优点：

- XiangTa 改动最小
- 不用改 repo 内正式 `voice_mappings.json`
- 可以通过 fixture / monkeypatch / fake repository 精准控制

缺点：

- 仍需要 Core 测试环境提供 mock binding + provider voice

### 6.5 推荐方案

**推荐：C 为主，结合 B。**

即：

1. XiangTa B2-B1 测试里，不直接使用仓库中的占位 `coreProfileId`
2. 改用测试 fixture / fake repository / monkeypatch，让 `voicePresetId -> core_profile_id="deep_night_programmer"`
3. 同时使用现有 Core 测试基建中的 `seed_mock_binding`，确保：
   - profile 存在
   - mock binding 存在
   - provider voice 存在且 available

原因：

- 改动最小
- 不污染正式产品配置
- 复用已有 Core 测试习惯
- 能稳定强制 mock path

## 7. Asset / audioUrl 映射策略

### 7.1 Core render 返回什么

Core `VoiceRenderResponse` 直接返回：

- `job_id`
- `status`
- `audio_asset`
  - `id`
  - `url`
  - `duration_ms`
  - `format`

`audio_asset.url` 当前已经是下载地址：

- `/api/voice/assets/{audio_id}/download`

### 7.2 XiangTa 应如何映射

建议：

- `TtsData.taskId` <- Core `job_id`
- `TtsData.audioUrl` <- Core `audio_asset.url`
- `TtsData.durationMs` <- Core `audio_asset.duration_ms`
- `TtsData.charCount` <- `len(text)`
- `TtsData.status`
  - dry-run 时：`dry_run`
  - Core 成功返回时：建议归一化成 `completed`

### 7.3 是否需要包装 download URL

结论：**B2-B1 不需要额外包装。**

直接复用 Core `audio_asset.url` 即可，因为它本身就是稳定下载 URL。

后续如果产品层需要自有 CDN / 鉴权包装，可以在更后面的阶段再做，不属于 B2-B1 最小范围。

## 8. 错误翻译策略

### 8.1 Core 可能抛出的错误

从当前 render 路径看，XiagTa Gateway 需要关注：

- `VALIDATION_ERROR` (422)
  - request schema 校验失败
  - capability 校验失败
  - binding 对应 provider voice 无效
- `PROFILE_NOT_FOUND` (404)
- `BINDING_NOT_FOUND` (404)
- `UNSUPPORTED_PROVIDER` (400/422)
- `PROVIDER_ERROR` (400)
- `INTERNAL_ERROR` (500)

### 8.2 XiangTa Gateway 建议映射

建议在 Gateway 内捕获 Core error envelope 后，映射到 XiangTa 产品错误：

| Core error code | XiangTa errorKind | 说明 |
|---|---|---|
| `VALIDATION_ERROR` | `invalid_input` / `tts_failed` | 用户输入问题优先映射 `invalid_input`；binding/provider_voice 之类可映射 `tts_failed` |
| `PROFILE_NOT_FOUND` | `preset_not_found` | 说明 voice mapping 指向的 Core profile 不可用 |
| `BINDING_NOT_FOUND` | `preset_not_found` 或 `no_provider` | B2-B1 更建议 `preset_not_found`，因为是映射不可用 |
| `UNSUPPORTED_PROVIDER` | `no_provider` | provider 策略错误或测试没强制 mock |
| `PROVIDER_ERROR` | `tts_failed` | 生成失败但不暴露 provider 细节 |
| `INTERNAL_ERROR` | `unknown` / `tts_failed` | 统一产品友好消息 |

### 8.3 不得泄露的内容

用户端错误响应不得暴露：

- Core stack trace
- `provider`
- `model`
- `provider_voice_id`
- `binding_id`
- `params_json`
- API key / env var 名称
- 原始 provider request/response

错误细节如果需要保留，只能进：

- XiangTa 服务端日志
- admin/debug 视图
- Core 日志

## 9. B2-B1 最小实现建议

### 9.1 推荐目标

`P17-XIANGTA-CORE-RENDER-B2-B1` 只做：

- `VoiceLabGateway.generate_tts()` 接 Core render **mock path**
- 保留 `generate_tts_dry_run()`
- `TtsOrchestrator` 切到真实 `generate_tts()`，或保留可开关 dry-run mode
- 测试强制 `provider="mock"`
- 用户端继续隐藏 `profile_id / provider / model / provider_voice_id`

### 9.2 B2-B1 推荐修改文件

建议仅修改：

- `src/xiangta/services/voice_lab_gateway.py`
- `src/xiangta/services/tts_orchestrator.py`
- `src/xiangta/services/product_service.py`（如果需要装配开关）
- `src/xiangta/services/error_translator.py`
- `tests/xiangta/test_tts_orchestrator.py`
- `tests/xiangta/test_tts_api.py`
- `tests/xiangta/test_voice_lab_gateway_contract.py`
- `tests/xiangta/test_boundary_contract.py`

必要时可增加少量 XiangTa 测试 fixture，但不要改 Core 业务代码。

### 9.3 B2-B1 推荐调用方式

推荐顺序：

1. `VoicePresetMappingService.resolve()`
2. `TonePresetService.resolve()`
3. 组装 `CoreRenderTarget`
4. `VoiceLabGateway.generate_tts()`
5. Gateway 通过 **HTTP** 调 `POST /api/voice/render`
6. 测试路径显式把 `provider="mock"`
7. 映射 Core 响应到 XiangTa `TtsData`

### 9.4 B2-B1 禁止事项

- 不得接真实 MiniMax / Xiaomi MiMo
- 不得读取真实 API key
- 不得让 `provider=None` 回落到默认 `minimax`
- 不得让 XiangTa 直接 import `app.repositories.*`
- 不得让 XiangTa 直接 import `app.providers.*`
- 不得在 XiangTa 中构造或操作 `RenderPlan`
- 不得把 `profile_id / provider / model / provider_voice_id` 暴露到用户端

## 10. B2-B1 禁止事项

- 不直接调用 `VoiceRenderService.render_voice()` 作为 XiangTa 首个实现路径，除非 Core 先补一个等价 facade
- 不直接依赖 `seed_defaults()` 作为 mock path 唯一前提
- 不继续使用 `voice_mappings.json` 里的 `<core_profile_id_from_core_profiles>` 占位做真调用
- 不把 `providerPolicy="default"` 直接用于 B2-B1 mock 测试
- 不在 B2-B1 中推进真实 Provider 接入

## 11. Open Gaps

| Gap ID | 问题 | 影响 | 建议处理 |
|---|---|---|---|
| GAP-B2-001 | `voice_mappings.json` 里的 `coreProfileId` 仍是 `<core_profile_id_from_core_profiles>` 占位 | B2-B1 测试无法直接真调 Core render | XiangTa 测试 fixture 中把 mapping 指向 `deep_night_programmer` |
| GAP-B2-002 | `providerPolicy="default"` 若不覆写，Core 可能回落到 `settings.voice_provider=minimax` | B2-B1 测试可能误走真实 Provider | B2-B1 测试路径强制 `provider="mock"` |
| GAP-B2-003 | 当前没有一个与 `POST /api/voice/render` 完全等价的进程内 high-level facade；路由层还有 `capability_validator.validate_tts(...)` | 如果 B2-B1 选择进程内调用，容易绕过 public contract | B2-B1 优先走 HTTP；若未来想走进程内，先在 Core 增加 facade |
| GAP-B2-004 | `seed_defaults()` 虽有 mock binding，但没有同时 seed `ProviderVoice` 记录 | 仅靠默认 seed，`validate_binding_provider_voice()` 可能失败 | B2-B1 测试复用 `seed_mock_binding` 或补建 provider voice fixture |

## 12. 审查结论

结论如下：

1. Core public render path 已具备 XiangTa B2-B1 接入所需的最小能力：
   - `POST /api/voice/render`
   - `VoiceRenderRequest`
   - `VoiceRenderResponse`
   - mock provider
   - asset download URL
2. **B2-B1 推荐通过 `VoiceLabGateway` 调用 HTTP API，而不是直接进程内调 service**
3. B2-B1 的测试路径必须：
   - 强制 `provider="mock"`
   - 使用真实存在的 `core_profile_id`
   - 准备好可用 mock binding 和 provider voice
4. 用户端仍应保持产品层字段，不暴露 Core 内部信息

最终判断：

**未发现阻塞 B2-B1 mock provider 接入的 Core render gap。**

但在进入 B2-B1 前，必须先按本审查文档处理 `coreProfileId` 占位、mock provider 强制、以及 provider voice fixture 这几个前置条件。
