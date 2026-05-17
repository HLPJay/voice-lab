# 想Ta了产品定位

## 一句话

想Ta了是一个帮助用户把“说不出口的话”整理成有温度的文字和语音短笺的产品。

它不是聊天机器人，不做情感陪伴，不自动发送消息，不采集用户声音做克隆。它只帮助用户组织表达、生成语音，并把结果交还给用户自己决定是否保存或发送。

## 三层关系

```text
Mobile App / H5 / PWA
  面向用户：对象、场景、语气、声线、文案、生成结果
        ↓
XiangTa Backend
  产品化包装层：配置管理、文案编排、产品 API、Core 调用、错误翻译
        ↓
Voice Lab Core
  能力底座：profiles、bindings、provider adapters、render、assets、runtime status
```

Voice Lab Core 关心“如何生成语音”：provider、model、voice_id、binding、音频资产、运行状态。

XiangTa Backend 关心“如何把能力包装成产品”：用户端声线名称、场景、对象、语气、文案风格、使用限制和友好错误。

Mobile App 关心“用户如何完成表达”：选择对象和场景，输入真实想法，挑选文案和声线，生成语音。

## 用户端不暴露 Core 概念

用户端 API 只暴露产品语义：

- `voicePresetId`
- `recipient`
- `scene`
- `tone`
- `style`
- `text`

用户端不依赖这些 Core 字段：

- `profile_id`
- `provider`
- `model`
- `provider_voice_id`
- `params_json`
- API key 或 provider 配置

## XiangTa 自己维护什么

XiangTa Backend 维护产品配置和业务状态：

- `voice_mappings`：产品声线到 Core profile 的映射
- `tone_presets`：语气、风格和高层参数
- `recipients`：对象类型
- `scenes`：表达场景
- `copywriting_config`：文案模板、prompt、生成策略
- `limits`：字数、建议数量、生成开关、MVP 限制
- `letters`：用户保存的信笺记录

## Core 负责什么

Core 继续作为音频能力层：

- 声线 profile 管理
- profile 与 provider voice 的 binding
- provider 能力与运行状态
- TTS render
- 音频和字幕 assets
- 调用日志、成本、资源保护

XiangTa 应该“调用 Core”，不是复制 Core。

