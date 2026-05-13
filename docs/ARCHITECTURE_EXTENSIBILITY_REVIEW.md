# Voice Lab 架构设计与可扩展性自检报告

## 1. 报告目的

本文档用于记录 Voice Lab 当前架构设计状态、可扩展性问题、横切能力缺口，以及后续架构演进方向。

本报告不涉及功能开发，只用于项目自检和后续任务拆分。

---

## 2. 当前项目阶段判断

Voice Lab 当前已经从 MiniMax API Demo 演进为 AI 声音资产管理与语音生成工作台雏形。

当前已经具备：

- VoiceProfile 声音人设
- ProviderVoice Provider 音色资产
- VoiceBinding 人设与音色绑定
- Mock Provider
- MiniMax Provider
- T2A 同步生成
- 异步生成
- WebSocket 流式生成
- 多版本试音
- 声音设计
- 声音克隆
- 音色导入
- 音色删除生命周期闭环
- 批量长文本生成
- 剧本多角色生成
- ProviderVoice 生成前状态校验
- Cost Guard 统一入口
- ProviderCallLog / StatsService 统计雏形

当前仍不适合直接开放多人试用，主要原因：

- 前端仍是测试面板，不是产品工作台
- 缺少全局 Resource Guard
- 缺少预算预占与实际结算
- SQLite / storage / logs 仍使用本地开发式配置
- Provider 抽象仍偏 MiniMax voice_id 模式
- 多 Provider 能力差异尚未抽象

---

## 3. 当前架构已经做对的部分

### 3.1 已有 Provider Adapter 基础

当前 `SpeechProvider` 已经抽象出以下能力：

- render_sync
- render_stream
- create_async_task
- query_async_task
- list_voices
- delete_voice
- design_voice
- clone_voice
- upload_voice_file

这说明系统已经具备底层 Provider 可替换的基础。

当前实际注册 Provider：

- mock
- minimax

尚未接入：

- mimo
- local_gpt_sovits
- local_cosyvoice
- aliyun
- volcengine
- elevenlabs

### 3.2 已有声音资产三层模型

当前项目已经形成：

- VoiceProfile：上层声音人设
- ProviderVoice：底层 Provider 音色资产
- VoiceBinding：人设与音色绑定关系

这使得业务层不再直接依赖单个 voice_id，而是通过绑定关系使用底层音色资产。

### 3.3 已有 Cost Guard 横切能力

当前 Cost Guard 已经升级为统一入口：

- COST_PROVIDER_SET
- HIGH_RISK_OPERATIONS
- CostGuardService.require_confirmed(provider, operation, confirm_cost)

当前已覆盖的高风险操作包括：

- voice_design
- voice_clone
- provider_voice_preview
- provider_voice_import_verify
- binding_voice_preview
- voice_variants
- batch_longtext
- batch_script
- async_render
- stream_render

这说明成本确认能力已经从点状 if 判断，升级为操作策略入口。

### 3.4 已有 Provider 调用日志基础

当前 ProviderCallLog 已支持：

- request_id
- job_id
- provider
- api_path
- method
- status_code
- duration_ms
- provider_trace_id
- usage_characters
- error_type
- error_message
- created_at

这为后续成本统计、调用追踪、Provider 健康分析和预算系统提供了基础。

---

## 4. 架构设计主要问题

### 4.1 Provider 抽象缺少 ProviderCapabilities

当前 `SpeechProvider` 是方法接口集合，但没有能力声明。

问题：

- 不是所有 Provider 都支持 voice_clone
- 不是所有 Provider 都支持 voice_design
- 不是所有 Provider 都支持 delete_voice
- 不是所有 Provider 都支持 true_streaming
- 不是所有 Provider 都返回 subtitle timeline
- 不是所有 Provider 都有远端持久 voice_id

当前做法容易导致：

- 前端不知道该展示哪些按钮
- service 层只能靠 provider 名称判断
- 新 Provider 被迫实现无意义方法
- 后续接 MiMo / 本地模型时出现大量 if provider == xxx

建议后续增加 ProviderCapabilities：

```json
{
  "tts": true,
  "preset_voice": true,
  "voice_clone": true,
  "voice_design": true,
  "delete_voice": true,
  "remote_voice_id": true,
  "stateless_clone": false,
  "stateless_design": false,
  "true_streaming": true,
  "subtitle_timeline": true,
  "singing": false
}
```

### 4.2 RenderPlan 仍偏 MiniMax voice_id 模式

当前 RenderPlan 主要包含：

- provider
- model
- provider_voice_id
- voice_params
- audio_params
- subtitle
- output_format
- language_boost

当前 voice_params 主要支持：

- speed
- vol
- pitch
- emotion

问题：

- 无法表达 MiMo 的 stateless_design
- 无法表达 MiMo 的 stateless_clone
- 无法表达本地模型 reference_audio_path
- 无法表达 voice_prompt
- 无法表达 provider-specific options
- 无法表达 source_type
- 无法表达 style_instruction / director instruction

建议后续设计 RenderPlan v2：

```python
class RenderPlanV2:
    provider: str
    model: str
    operation: str
    provider_voice_id: str
    provider_voice_source_type: str
    provider_voice_metadata: dict
    text: str
    processed_text: str
    style_instruction: str | None
    voice_params: dict
    audio_params: dict
    provider_options: dict
    subtitle: SubtitlePlan
```

### 4.3 ProviderVoice metadata_json 缺少标准语义

当前 ProviderVoice 有 metadata_json，这是正确方向，但缺少规范。

问题：

- metadata 可能变成杂物箱
- 不同 Provider 各写各的字段
- service 层无法稳定读取
- RenderPlan 无法统一使用
- 接 MiMo / 本地模型会出现临时字段堆叠

建议定义 ProviderVoiceMetadataSpec：

```json
{
  "source_type": "remote_voice_id",
  "model": "speech-2.8-hd",
  "voice_prompt": null,
  "reference_audio_path": null,
  "reference_text": null,
  "provider_specific": {}
}
```

source_type 建议枚举：

- system_preset
- remote_voice_id
- stateless_design
- stateless_clone
- local_reference
- local_finetune
- manual_import

### 4.4 Cost Guard 已完成 P0，但仍不是预算系统

当前 Cost Guard 解决的是：

- 防误触
- 防绕过前端直接高风险调用
- 高风险操作必须 confirm_cost

但仍未解决：

- estimate_id
- 一次性确认令牌
- 预算预占
- 实际使用结算
- 每日预算
- Provider 预算
- 用户预算
- API Key 额度限制

后续应演进为 Budget Guard：

```
cost estimate
  → estimate_id
  → 用户确认
  → 预算预占
  → 任务执行
  → usage 回填
  → 实际结算
```

### 4.5 Resource Guard 完全缺失

当前系统仍缺少全局资源调度。

缺失能力：

- provider 级并发限制
- model 级并发限制
- operation 级并发限制
- API Key / Token 级限制
- 高风险操作串行保护
- 批量任务全局限制
- 重复点击防护
- 429 重试和退避
- 任务排队机制

当前风险：

- 多人同时试用时打爆云端 Provider
- 用户重复点击导致重复扣费
- 批量任务并发放大成本
- SQLite 写锁
- 文件写入冲突
- 音频合并压力
- Provider 返回限流错误

建议 Resource Guard 以以下维度设计：

```
provider + model + operation + api_key_id
```

### 4.6 ProviderCallLog 不是统一调用链的一部分

当前有 ProviderCallLog，但 usage 回填不完整。

已知缺口：

- voice_design_service 成功后未显式回填 usage_characters
- voice_clone_service 成功后未显式回填 usage_characters
- stream_render_service 成功后未统一 update_call_log
- async_render_service 完成后 usage 回填不完整

后续应建立 ProviderCallContext：

```
operation
provider
model
job_id
request_id
api_key_id
duration_ms
trace_id
usage_characters
status
error
```

所有真实 Provider 调用都应进入统一调用上下文，而不是让 adapter 或 service 分散记录。

### 4.7 批量任务已有内部并发，但没有全局任务队列

当前 batch 有 segment 和状态管理，但仍不是全局任务队列。

后续可能需要统一管理：

- sync render
- async render
- stream render
- preview
- voice design
- voice clone
- voice variants
- batch longtext
- batch script
- mimo tts
- local inference

建议后续抽象 JobQueue / OperationExecutor。

### 4.8 配置体系仍偏本地开发

当前默认配置仍是：

```
database_url = sqlite:///./voice_lab.db
storage_dir = ./storage
log_dir = ./logs
batch_max_concurrency = 5
```

问题：

- 从不同目录启动可能生成不同数据库
- storage 和 logs 路径不稳定
- SQLite 对多人试用不友好
- batch_max_concurrency=5 对试用阶段偏高
- 启动时缺少路径自检和配置摘要

建议：

- 启动时打印 database/storage/log 的绝对路径
- .env.example 提示使用绝对路径
- 试用阶段 batch_max_concurrency 降到 1 或 2
- 多人试用前迁移 PostgreSQL

### 4.9 前端仍是测试台，不是产品工作台

当前前端仍以功能测试为主：

- T2A 生成
- 音色管理
- 声音克隆
- 声音设计
- 绑定管理
- 批量生成

问题：

- 普通用户不知道从哪里开始
- 创作路径不突出
- 管理功能和生成流程混在一起
- 手机端 H5/PWA 难以复用
- 后续功能继续增加会进一步复杂化

建议后续重组为：

- 创作工作台
- 声音资产
- 生成历史
- 批量任务
- 高级设置

---

## 5. 可扩展性风险清单

### 5.1 多 Provider 扩展风险

当前接入 MiMo、本地 GPT-SoVITS、CosyVoice 时会遇到：

- 缺少 ProviderCapabilities
- 缺少 source_type
- RenderPlan 不支持 metadata
- 不同 Provider 生命周期不同
- 不同 Provider 请求结构不同
- 不同 Provider 价格和并发策略不同

### 5.2 多模型扩展风险

同一 Provider 下可能有多个模型：

- 普通 TTS 模型
- VoiceDesign 模型
- VoiceClone 模型
- 流式模型
- 唱歌模型

当前系统还没有 provider + model + operation 的统一策略表。

### 5.3 成本扩展风险

当前是 confirm_cost 防误触，不是成本系统。

后续多人试用会需要：

- 用户维度
- API Key 维度
- Provider 价格表
- Model 价格表
- 每日预算
- 任务预算预占
- 实际 usage 结算

### 5.4 任务扩展风险

当前不同类型任务由不同 service 管理。

后续应避免：

- 每个任务自己处理状态
- 每个任务自己写日志
- 每个任务自己做并发
- 每个任务自己做错误处理

应逐步收敛到 OperationExecutor。

### 5.5 前端扩展风险

当前 index.html 承载过多能力。

后续风险：

- 单文件越来越难维护
- 高风险操作确认容易再次遗漏
- 手机端复用困难
- 产品主流程不清晰
- 管理功能和创作功能耦合

---

## 6. 建议的架构演进方向

### 6.1 第一层：OperationPolicy

定义所有操作：

- t2a_sync
- t2a_async
- t2a_stream
- provider_voice_preview
- binding_voice_preview
- provider_voice_import_verify
- voice_design
- voice_clone
- voice_variants
- batch_longtext
- batch_script
- list_voices
- delete_voice

每个 operation 声明：

- 是否真实调用 Provider
- 是否可能产生费用
- 是否高风险
- 是否需要 confirm_cost
- 是否需要 ResourceGuard
- 是否需要 ProviderVoice
- 是否允许 mock 绕过
- 是否需要 usage 回填
- 是否需要删除确认

### 6.2 第二层：ProviderCapabilities

每个 Provider 声明自身能力。

这会影响：

- API 是否允许某操作
- 前端是否展示某按钮
- service 是否能调用某 adapter 方法
- 文档如何说明该 Provider 限制

### 6.3 第三层：ProviderVoiceMetadataSpec

将 metadata_json 标准化。

先文档化，再代码化。

### 6.4 第四层：RenderPlan v2

让 RenderPlan 能承载不同 Provider 的声音来源和参数。

### 6.5 第五层：ResourceGuard

基于 provider + model + operation + api_key_id 控制并发。

### 6.6 第六层：ProviderCallContext / UsageLogger

所有真实 Provider 调用都通过统一上下文记录调用日志。

---

## 7. 推荐整改顺序

### 阶段 A：架构文档固化

- 新增本文档
- 将 ProviderCapabilities / OperationPolicy / MetadataSpec / RenderPlan v2 作为后续任务来源

### 阶段 B：产品主流程整理

- 将测试面板整理成创作工作台
- 保留高级功能，但弱化测试面板感
- 主流程突出：场景 → 声音 → 文案 → 成本 → 生成 → 复用

### 阶段 C：Resource Guard 第一版

- provider + model + operation 并发控制
- 高风险操作串行
- mock 不限制
- 预留 api_key_id

### 阶段 D：ProviderVoice metadata 规范

- 定义 source_type
- 统一 metadata 字段
- 为 MiMo 和本地模型做准备

### 阶段 E：MiMo 预置音色 TTS

- 只接 mimo-v2.5-tts
- 只接预置音色
- 不接 voice design / voice clone

### 阶段 F：RenderPlan v2 / ProviderCapabilities

- 支持 stateless_design
- 支持 stateless_clone
- 支持 local_reference
- 前端按 capabilities 展示功能

---

## 8. 当前结论

Voice Lab 当前最大的风险不是功能不足，而是架构开始进入复杂阶段。

已经完成的部分：

- Provider Adapter 基础
- 声音资产模型
- ProviderVoice 状态校验
- Cost Guard 统一入口
- 批量生成基础能力
- 调用日志雏形

仍需补齐的部分：

- ProviderCapabilities
- OperationPolicy
- ProviderVoice metadata 标准
- RenderPlan v2
- ResourceGuard
- BudgetGuard
- ProviderCallContext
- 产品主流程重组

一句话结论：

当前项目已经具备继续扩展的基础，但在接入 MiMo、本地模型、手机端和多人试用前，必须先完成架构横切能力的收敛，否则后续会持续出现点状补丁和 Provider 特判。
