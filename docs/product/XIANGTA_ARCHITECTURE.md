# 想Ta了 · 系统架构说明

## 三层架构全景

```
┌──────────────────────────────────────────────────────────────────┐
│  Layer 3 — XiangTa Mobile (用户端)                               │
│                                                                  │
│  apps/xiangta_mobile/                                            │
│  ├── H5 / PWA（React 18 + Babel Standalone，无构建步骤）          │
│  ├── 本地 localStorage 持久化（MVP 阶段）                         │
│  └── 只传产品语义：recipient / scene / rawText / style / preset  │
│                                                                  │
│  【前端边界规则】                                                  │
│  - 不暴露 voice_id、model_id、sample_rate、provider、API key     │
│  - 不直接调用 voice_lab Core API                                 │
│  - 只调用 XiangTa Product Server 定义的产品 API                  │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP / JSON
┌───────────────────────────▼──────────────────────────────────────┐
│  Layer 2 — XiangTa Product Server (产品服务层)                    │
│                                                                  │
│  src/xiangta/                                                    │
│  ├── api/routes.py          — FastAPI 路由（独立挂载，不改主应用）  │
│  ├── api/schemas.py         — 请求/响应 Pydantic 模型             │
│  ├── services/              — 产品业务逻辑                        │
│  │   ├── product_service.py      — 编排主流程                    │
│  │   ├── copywriting_service.py  — LLM 文案生成                  │
│  │   ├── tts_orchestrator.py     — TTS 任务调度                  │
│  │   ├── preset_mapper.py        — 产品预设 → Core 参数映射       │
│  │   ├── provider_status_service.py — Provider 状态聚合          │
│  │   ├── letter_service.py       — 信笺 CRUD（MVP 本地，后期服务端）│
│  │   ├── error_translator.py     — Core 错误 → 产品友好文案       │
│  │   └── voice_lab_gateway.py   ← 唯一对 Core 的访问入口         │
│  ├── configs/               — 产品配置（JSON）                   │
│  ├── prompts/               — LLM Prompt 模板（按场景分文件）     │
│  └── models/                — 产品数据模型                       │
└───────────────────────────┬──────────────────────────────────────┘
                            │ 只通过 voice_lab_gateway.py
┌───────────────────────────▼──────────────────────────────────────┐
│  Layer 1 — Voice Lab Core (能力底座，已冻结)                      │
│                                                                  │
│  src/voice_lab/                                                  │
│  ├── adapters/   — Provider 适配（MiniMax, Xiaomi MiMo）         │
│  ├── services/   — TTS / VoiceProfile / VoiceBinding / History   │
│  └── api/        — 主工作台 REST API                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## voice_lab_gateway.py — 隔离职责

`src/xiangta/services/voice_lab_gateway.py` 是 XiangTa 访问 Core 的**唯一入口**。

职责边界：

| 职责 | 在 gateway | 在 Product Service |
|---|---|---|
| 调用 Core TTS 服务 | ✅ | ❌ 不直接调用 |
| 调用 Core Provider 状态 | ✅ | ❌ |
| 解析 core_binding_key → Provider 参数 | ✅（gateway/Core 内部，对上层不可见） | ❌ |
| 产品业务逻辑 | ❌ | ✅ |
| 错误翻译 | ❌（抛原始异常） | ✅（error_translator） |

**强制规则**：
- 产品服务层（copywriting_service, tts_orchestrator 等）只允许 `import` gateway，不允许 `import` 任何 `src.voice_lab.*`
- gateway 内部不含业务逻辑，只做调用代理和参数透传

---

## preset_mapper.py — 产品概念 → CoreBindingRequest

前端传入产品语义：

```json
{
  "voicePreset": "female-gentle",
  "tone": "restrained",
  "scene": "miss"
}
```

`preset_mapper.py` 读取 `configs/voice_presets.json` 和 `configs/tone_presets.json`，
将其解析为 **CoreBindingRequest**（产品层稳定结构），再交给 `voice_lab_gateway.py`。

```json
{
  "core_binding_key": "xiangta_female_gentle",
  "voice_preset": "female-gentle",
  "tone": "restrained",
  "tone_hint": "calm",
  "enabled": true
}
```

**CoreBindingRequest 不包含 `voice_id`、`model_id`、`sample_rate`、`bitrate`。**
这些 Provider-specific 参数的解析在 `voice_lab_gateway` 内部或 Core 内部完成，
Product Server 完全不感知。

前端也永远不感知底层字段。

---

## error_translator.py — 错误友好化

Core 抛出的技术异常（配额超限、Provider 不可用、网络超时）
由 `error_translator.py` 翻译为产品层友好文案，
再通过 `api/schemas.py` 中定义的错误结构返回前端。

前端只看到：`{ "errorKind": "quota", "message": "今天的声音已用完，明天再来" }`

---

## 数据流（MVP 主路径）

```
用户输入 rawText
    → POST /api/xiangta/suggestions
    → copywriting_service.py 调用 LLM（via gateway）
    → 返回 3 条风格建议

用户选定文案 + voicePreset + tone
    → POST /api/xiangta/tts
    → tts_orchestrator.py 调用 preset_mapper
    → voice_lab_gateway.py 调用 Core TTS
    → 返回音频 URL

前端保存信笺到 localStorage（MVP）
```

---

## 目录映射

```
voice_lab/
├── apps/xiangta_mobile/    — 移动端前端（H5/PWA）
├── src/xiangta/            — 产品服务层
├── tests/xiangta/          — 产品层测试
├── docs/product/           — 本阶段产品文档
└── src/voice_lab/          — Core（冻结，只读）
```
