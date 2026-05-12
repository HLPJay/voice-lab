# Voice Lab 下一阶段行动计划

## 总原则

当前阶段不要继续无序增加功能。

下一阶段目标是：

1. 巩固当前项目状态
2. 整理产品主流程
3. 增强试用阶段资源保护
4. 再接入低成本 Provider
5. 最后做手机端 H5/PWA

禁止同时推进：

- MiMo 接入
- 手机端
- Resource Guard
- Provider 架构大改
- 本地模型接入

必须分阶段推进。

---

## 阶段 1：产品主流程整理

目标：

把当前测试面板整理成声音内容生成工作台。

当前页面问题：

- 偏测试面板
- 功能入口太多
- 普通用户不知道从哪里开始
- 管理功能和创作功能混在一起

建议主流程：

选择场景 → 选择声音 → 输入文案 → 成本提示 → 生成试听 → 播放 / 下载 / 复用

建议页面结构：

- 创作首页
- 声音资产
- 生成历史
- 批量任务
- 设置 / 管理

创作首页场景模板：

- 深夜独白
- 好书推荐
- 情绪旁白
- 多角色音频剧
- 知识长文转音频

验收标准：

- 用户打开首页能理解产品用途
- 首页能完成一次完整生成
- 生成前能看到 provider / voice / 字符数 / 成本提示
- 生成后能播放、下载、查看历史
- 手机 390px 宽度下主流程可用

---

## 阶段 2：Resource Guard 第一版

目标：

控制真实云端模型调用的资源消耗，避免试用阶段并发、费用、限流失控。

第一版不做 Redis，不做分布式，不做用户 API Key 池。

实现范围：

- provider + model + operation 并发控制
- 高风险操作串行
- mock provider 不限制
- minimax / mimo 等真实 provider 受限制
- 所有 acquire 必须 finally release
- 预留 api_key_id = system_default

操作类型：

- t2a
- preview
- voice_design
- voice_clone
- batch_longtext
- batch_script
- async_render
- stream

建议默认限制：

- minimax_t2a_concurrency = 2
- minimax_voice_design_concurrency = 1
- minimax_voice_clone_concurrency = 1
- minimax_preview_concurrency = 1
- batch_global_concurrency = 1
- mimo_t2a_concurrency = 2
- mimo_voice_design_concurrency = 1
- mimo_voice_clone_concurrency = 1
- local_provider_concurrency = 1

验收标准：

- 超过并发限制时拒绝
- 返回友好错误："当前生成任务较多，请稍后再试"
- mock 不受影响
- 异常后 slot 能释放
- 批量任务不能绕过限制

---

## 阶段 3：MiMo 预置音色 TTS 接入

目标：

先接 MiMo 的预置音色 TTS，不接 voice design，不接 voice clone。

只支持：

- mimo-v2.5-tts
- 预置音色
- 普通 T2A

不支持：

- MiMo VoiceDesign
- MiMo VoiceClone
- MiMo 真流式
- MiMo 字幕时间轴

Provider 名称：

- mimo

预置音色：

- 冰糖
- 茉莉
- 苏打
- 白桦
- Mia
- Chloe
- Milo
- Dean

验收标准：

- Provider registry 增加 mimo
- 能用预置音色生成音频
- 生成结果能保存为 AudioAsset
- 能被 VoiceBinding 绑定
- CostGuard 对 mimo 暂时返回 unknown_price 或免费提示
- ResourceGuard 对 mimo 生效

---

## 阶段 4：手机端 H5/PWA

目标：

快速验证移动端内容生产场景。

只做 H5/PWA，不做原生 App。

手机端第一版只保留：

- 选择场景
- 选择声音
- 输入文案
- 成本提示
- 生成试听
- 播放
- 下载
- 历史记录

不包含：

- Provider 管理
- 音色删除
- API 调试
- 复杂绑定管理
- 管理后台

验收标准：

- 390px 宽度可用
- 单手操作路径清晰
- 生成按钮防重复点击
- 结果页可播放音频
- 历史记录可回听

---

## 阶段 5：MiMo VoiceDesign / VoiceClone

前置条件：

- MiMo 预置音色 TTS 已跑通
- ProviderVoice metadata 规范已定义
- RenderPlan 能传递 provider_voice_metadata
- ResourceGuard 已生效

MiMo VoiceDesign 设计：

- source_type = stateless_design
- metadata 保存 voice_prompt
- 生成时将 voice_prompt 放入 user message
- 目标文本放入 assistant message

MiMo VoiceClone 设计：

- source_type = stateless_clone
- metadata 保存 reference_audio_path
- 生成时读取本地音频并转 base64 data URI
- 需要限制音频大小

验收标准：

- VoiceDesign 可保存为 ProviderVoice
- VoiceClone 可保存为 ProviderVoice
- 后续生成可以复用这些 ProviderVoice
- 不假设 MiMo 返回远端持久 voice_id

---

## 阶段 6：Provider 抽象升级

目标：

避免后续每接一个 Provider 都重构。

需要增加：

- ProviderCapabilities
- ProviderVoice source_type
- RenderPlan provider_voice_metadata
- provider_options
- 前端按 capabilities 展示功能

ProviderCapabilities 示例：

```json
{
  "tts": true,
  "voice_clone": true,
  "voice_design": true,
  "delete_voice": false,
  "remote_voice_id": false,
  "stateless_clone": true,
  "stateless_design": true,
  "subtitle_timeline": false,
  "true_streaming": false
}
```

验收标准：

- MiniMax 能声明自己的能力
- MiMo 能声明自己的能力
- 前端根据能力显示/隐藏按钮
- Adapter 不需要硬编码太多上层逻辑

---

## 推荐执行顺序

1. 产品主流程整理
2. Resource Guard 第一版
3. MiMo 预置音色 TTS
4. 手机端 H5/PWA
5. MiMo VoiceDesign / VoiceClone
6. Provider 抽象升级

不建议跳过 Resource Guard 直接开放试用。
