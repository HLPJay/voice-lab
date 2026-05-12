# Voice Lab 已知问题与遗留事项

## P0：近期必须关注

### P0-1：前端仍是测试面板

当前页面仍偏工程测试工具，用户打开后看到的是：

- T2A 生成
- 音色管理
- 声音克隆
- 声音设计
- 绑定管理
- 批量生成

这适合开发测试，但不适合产品试用。

建议后续整理为：

- 创作首页
- 声音资产
- 生成历史
- 批量任务
- 设置 / 管理

主流程应调整为：

选择场景 → 选择声音 → 输入文案 → 查看成本 → 生成试听 → 播放 / 下载 / 复用

### P0-2：缺少全局 Resource Guard

当前还没有全局资源调度机制。

缺少：

- Provider 级并发限制
- Model 级并发限制
- Operation 级并发限制
- 高风险操作串行保护
- API Key / Token 级别限制
- 预算预占
- 执行队列

风险：

- 多人同时试用时打爆云端模型
- 用户重复点击导致重复扣费
- 批量任务同时运行导致费用放大
- SQLite 写锁风险升高
- 文件写入和音频合并冲突

### P0-3：batch_max_concurrency 默认偏高

当前 batch_max_concurrency 默认值偏适合开发机验证，不适合试用环境。

建议试用阶段调整为：

- batch_max_concurrency = 1 或 2
- voice_design 并发 = 1
- voice_clone 并发 = 1
- preview 并发 = 1 或 2
- T2A 全局并发 = 2

### P0-4：Cost Guard 第一版只是防误触

2026-05-12 更新：Cost Guard 已升级为统一操作策略入口（`CostGuardService.require_confirmed`），覆盖全部 10 个高风险操作路径。但仍不是完整预算系统。

仍缺少：

- estimate_id
- 一次性确认令牌
- 预算预占
- 实际使用结算
- 每日预算
- Provider 预算
- 用户预算
- API Key 额度限制

### P0-5：已有 Cost Guard 路径的 usage 回填不完整

`voice_design_service.design_voice`、`voice_clone_service.clone_voice`、`stream_render_service.render_stream`、`async_render_service` 成功调用后未显式调用 `update_call_log` 回填 `usage_characters`。

后续应：显式在 service 层调用 `adapter.update_call_log(job_id, usage_characters, trace_id)`。

## P1：近期可优化

### P1-1：Provider 抽象仍偏 MiniMax voice_id 模式

当前系统仍默认很多 Provider 都类似 MiniMax：

创建/克隆音色 → 得到远端 voice_id → 后续传 voice_id 生成

但 MiMo / GPT-SoVITS / CosyVoice 不一定如此。

后续需要支持：

- system_preset
- remote_voice_id
- stateless_design
- stateless_clone
- local_reference
- local_finetune
- manual_import

### P1-2：ProviderVoice metadata 缺少标准语义

当前 metadata_json 可以保存扩展信息，但还没有统一规范。

建议后续建立：

```json
{
  "source_type": "remote_voice_id",
  "model": "...",
  "voice_prompt": "...",
  "reference_audio_path": "...",
  "provider_specific": {}
}
```

### P1-3：RenderPlan 缺少 provider_voice_metadata

当前 RenderPlan 主要包含：

- provider
- model
- provider_voice_id
- voice_params
- audio_params

但对于 MiMo / 本地模型，需要传递更多 ProviderVoice metadata。

建议后续增加：

- provider_voice_source_type
- provider_voice_metadata
- style_instruction
- provider_options

### P1-4：缺少 ProviderCapabilities

不同 Provider 能力不同。

后续每个 Provider 应声明：

- tts
- voice_clone
- voice_design
- delete_voice
- stream
- true_streaming
- subtitle_timeline
- preset_voice
- stateless_clone
- stateless_design
- singing

前端应根据 capabilities 展示功能。

### P1-5：Async / Stream 已纳入 confirm_cost ✅

> 2026-05-12 更新：`AsyncRenderRequest` 和 `StreamRenderRequest` 已增加 `confirm_cost` 字段，`async_render_service` 和 `stream_render_service` 已接入 `CostGuardService.require_confirmed`。

仍需补充：usage_characters 回填（见 P0-5）。

### P1-6：ProviderCallLog usage 补录需要真实链路验证

当前已实现 usage_characters / provider_trace_id 补录，但需要确认真实调用时 job_id 上下文是否正确。

建议增加健康检查：

- 执行一次真实或模拟 MiniMax T2A
- 查询 provider_call_logs
- 确认 usage_characters 非空
- 确认 provider_trace_id 非空
- 确认 StatsService total_characters 正常统计

### P1-7：SQLite / storage / logs 使用相对路径

当前默认路径容易受启动目录影响。

风险：

- 从不同目录启动生成不同 voice_lab.db
- 用户误以为数据丢失
- storage 文件找不到
- logs 分散

建议：

- 启动时打印 DATABASE_URL 绝对路径
- 启动时打印 STORAGE_DIR 绝对路径
- 启动时打印 LOG_DIR 绝对路径
- .env.example 建议使用绝对路径

### P1-8：前端批量轮询终态需要人工确认

需要人工确认：

- success 后是否停止轮询
- partial 后是否停止轮询
- failed 后是否停止轮询
- 是否显示失败段
- 是否显示重试失败段按钮

## P2：中期规划

### P2-1：MiMo Provider 接入

优先只接：

- mimo-v2.5-tts 预置音色 TTS

后续再接：

- mimo-v2.5-tts-voicedesign
- mimo-v2.5-tts-voiceclone

### P2-2：手机端 H5/PWA

手机端第一版只保留：

- 选择场景
- 选择声音
- 输入文案
- 成本提示
- 生成试听
- 播放 / 下载 / 保存历史

不搬完整管理后台。

### P2-3：request_hash 缓存

避免相同请求重复调用云端模型。

缓存 key 应包含：

- provider
- model
- provider_voice_id
- text
- voice_params
- audio_params
- subtitle
- output_format

### P2-4：Budget Guard

增加：

- 每日预算
- Provider 预算
- 用户预算
- 预算预占
- 实际结算
- 超预算拒绝

### P2-5：用户自带 API Key

后续支持：

- 用户自带 MiniMax Key
- 用户自带 MiMo Key
- API Key 加密存储
- Key 可用性检查
- Key 级并发控制
- Key 级预算统计

### P2-6：SQLite 迁移 PostgreSQL

多人试用或小规模上线前建议迁移 PostgreSQL。

### P2-7：本地 Provider

后续可探索：

- local_gpt_sovits
- local_cosyvoice
- local_fish_speech
- local_indextts

优先级低于 MiMo 和产品主流程。
