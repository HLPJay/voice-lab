# Project Structure

本文档定义 Voice Lab P0 的目录结构、每层职责、允许事项和禁止事项。后续实现模型必须优先遵守本文件，避免把业务逻辑、Provider 字段和存储逻辑混在一起。

## 目标目录树

```text
voice_lab/
  app/
    __init__.py
    main.py

    api/
      __init__.py
      health.py
      voice_profiles.py
      voice_bindings.py   # P1: VoiceBinding 管理
      voice_render.py
      voice_variants.py
      voice_jobs.py
      voice_assets.py
      provider_voices.py   # P1: Voice Catalog

    core/
      __init__.py
      config.py
      database.py
      errors.py
      logging.py
      time.py

    domain/
      __init__.py
      enums.py
      schemas.py
      render_plan.py

    models/
      __init__.py
      voice_profile.py
      voice_binding.py
      voice_job.py
      voice_asset.py
      voice_variant.py
      provider_voice.py       # P1: Voice Catalog

    repositories/
      __init__.py
      voice_profile_repo.py
      voice_binding_repo.py   # P1: VoiceBinding 管理
      voice_job_repo.py
      voice_asset_repo.py
      voice_variant_repo.py
      provider_voice_repo.py  # P1: Voice Catalog

    services/
      __init__.py
      voice_profile_service.py
      voice_binding_service.py  # P1: VoiceBinding 管理
      voice_render_service.py
      voice_variant_service.py
      text_preprocess_service.py
      asset_service.py
      job_service.py
      voice_catalog_service.py  # P1: Voice Catalog

    providers/
      __init__.py
      base.py
      minimax_speech_adapter.py
      mock_speech_adapter.py

    utils/
      __init__.py
      id_generator.py
      audio.py
      files.py
      srt.py

  storage/
    audio/
    subtitles/
    metadata/
    temp/

  tests/
    conftest.py
    test_health.py
    test_render_plan.py
    test_mock_adapter.py
    test_api_render.py
    test_provider_voice.py       # P1: Voice Catalog model
    test_voice_catalog.py         # P1: Voice Catalog service + API
    test_voice_binding_service.py  # P1: VoiceBinding service
    test_api_voice_bindings.py     # P1: VoiceBinding API

  docs/
    VOICE_LAB_GOALS.md
    ARCHITECTURE.md
    PROJECT_STRUCTURE.md
    IMPLEMENTATION_PLAN.md
    HANDOFF.md
    CONTROL_AND_SAFETY.md

  .env.example
  requirements.txt
  README.md
```

## 目录职责

### `app/main.py`

应用入口。

职责：

- 创建 FastAPI app。
- 注册 routers。
- 注册统一错误处理器。
- 启动时创建 SQLite 表。
- 启动时写入默认 seed 数据。
- 启动时创建 `storage/` 子目录。

禁止：

- 拼 MiniMax 请求体。
- 写业务编排逻辑。
- 直接保存音频文件。

### `app/api/`

对外 API 层。

职责：

- 定义 HTTP 路由。
- 接收和校验请求。
- 使用 `Depends(get_session)` 注入数据库 session。
- 调用 service 层。
- 返回标准 response schema。

禁止：

- 直接调用 MiniMax。
- 直接构造 `voice_setting`、`audio_setting`。
- 直接操作文件系统保存音频。
- 在路由里写复杂业务编排。

### `app/core/`

基础设施层。

职责：

- 配置读取。
- 数据库连接。
- 错误类型。
- 时间工具。
- 日志配置。

禁止：

- 放业务规则。
- 放 Provider 请求逻辑。

### `app/domain/`

标准协议层和内部语义层。

职责：

- 定义 `RenderPlan`。
- 定义内部枚举。
- 定义 API request/response schema。
- 表达 Voice Lab 自己的业务语义。

禁止：

- 依赖具体 Provider SDK。
- 把 MiniMax 字段设计成上层业务必须传入的字段。

### `app/models/`

数据库表模型。

职责：

- 使用 SQLModel 定义 SQLite 表。
- 只描述持久化结构。

禁止：

- 写业务方法。
- 写 HTTP 调用。
- 存音频二进制。

### `app/repositories/`

数据访问层。

职责：

- 封装常用查询。
- 降低 service 层里的 SQL 重复。

允许：

- 简单 create/get/list/update 查询。

禁止：

- 调用 Provider。
- 保存文件。
- 编排生成任务。

### `app/services/`

业务调度层。

职责：

- 查询声音人设和绑定。
- 文本预处理。
- 生成 `RenderPlan`。
- 创建和更新 `VoiceJob`。
- 调用 Provider Adapter。
- 保存 `AudioAsset` 和 `SubtitleAsset`。
- 返回标准响应。

这是 P0 的核心层。

禁止：

- 直接泄露 MiniMax API Key。
- 把 MiniMax 返回结构原样暴露给 API。
- 跳过 `RenderPlan` 直接调用 Provider。

### `app/providers/`

Provider Adapter 层。

职责：

- `base.py` 定义统一 Provider 接口。
- `mock_speech_adapter.py` 提供离线可测实现。
- `minimax_speech_adapter.py` 把 `RenderPlan` 翻译成 MiniMax 请求，并把 MiniMax 结果翻译成 `ProviderRenderResult`。

允许：

- 出现 MiniMax 的 `voice_setting`、`audio_setting`、`subtitle_enable` 等字段。
- 处理 MiniMax hex/url 音频返回。
- 包装 Provider 错误。

禁止：

- 查询业务数据库。
- 决定声音人设。
- 操作 `VoiceJob` 状态。
- 把 Authorization 打进日志。

### `app/utils/`

通用工具层。

职责：

- ID 生成。
- 文件路径创建。
- Mock 音频生成。
- SRT 转换。

禁止：

- 放 Provider 业务规则。
- 访问数据库。

### `storage/`

本地资产目录。

职责：

- 保存生成音频。
- 保存字幕 JSON 和 SRT。
- 保存 metadata。
- 保存临时文件。

要求：

- 可以由程序自动创建。
- 不应提交真实生成的大文件。
- 数据库只保存路径和元数据。

### `tests/`

测试目录。

职责：

- 验证 P0 闭环。
- 使用 Mock Provider。
- 使用临时 SQLite 和临时 storage。

禁止：

- 依赖真实 MiniMax API Key。
- 请求外网。
- 产生不可控大文件。

## 标准调用链

单条生成必须遵守：

```text
API Request
-> VoiceRenderService
-> VoiceProfile / VoiceBinding
-> TextPreprocessService
-> RenderPlan
-> VoiceJob pending/running
-> SpeechProvider.render_sync()
-> ProviderRenderResult
-> AssetService
-> VoiceJob success/failed
-> API Response
```

任何实现如果绕过 `RenderPlan`，都视为架构偏离。

## 新增文件放置规则

- 新路由放 `app/api/`。
- 新业务流程放 `app/services/`。
- 新数据库表放 `app/models/`。
- 新 Provider 放 `app/providers/`。
- 新配置放 `app/core/config.py`。
- 新测试放 `tests/`。
- 新设计说明放 `docs/`。

## 当前项目完整性状态

当前项目已经出现以下 P0 文件：

- `app/main.py`
- `app/api/*`
- `app/core/*`
- `app/domain/*`
- `app/models/*`
- `app/providers/*`
- `app/services/*`
- `tests/*`

仍建议后续实现者检查：

- API 是否全部注册到 `api_router`。
- `GET /health` 是否只定义一次或行为一致。
- 测试是否隔离真实数据库与真实 storage。
- Mock render 是否实际生成文件。
- MiniMax Key 缺失时是否返回明确错误。
- Asset download 是否防止路径越界。

