# src/xiangta — 想Ta了产品服务层

## 定位

XiangTa 产品服务层。调用 Voice Lab Core 提供真实 TTS 和 LLM 能力，
向移动端前端（apps/xiangta_mobile）暴露产品语义 API。

## 架构原则

- **唯一 Core 入口**：所有对 `src/voice_lab` 的调用必须通过 `services/voice_lab_gateway.py`
- **前端零底层概念**：API 只传 recipient/scene/style/voicePreset/tone，不传 voice_id/model_id/sample_rate
- **产品与底座分离**：本包不修改 src/voice_lab/* 任何文件

## 目录结构

```
src/xiangta/
├── api/
│   ├── routes.py          — FastAPI 路由（单独挂载）
│   └── schemas.py         — 请求/响应 Pydantic 模型
├── services/
│   ├── voice_lab_gateway.py   ← 唯一 Core 访问入口
│   ├── preset_mapper.py       — 产品预设 → Core 参数
│   ├── copywriting_service.py — LLM 文案生成
│   ├── tts_orchestrator.py    — TTS 任务调度
│   ├── product_service.py     — 主流程编排
│   ├── provider_status_service.py
│   ├── letter_service.py
│   └── error_translator.py
├── configs/               — 产品配置 JSON
├── prompts/               — LLM Prompt 模板（按场景）
└── models/                — 产品数据模型（dataclass）
```

## 开发阶段

| 阶段 | 任务 | 状态 |
|---|---|---|
| A0 | 骨架初始化（本阶段） | ✅ |
| A1 | 配置层 + Gateway 实现 | TODO |
| A2 | LLM 文案生成 | TODO |
| A3 | TTS 真实生成 | TODO |
| A4 | 前端联调 | TODO |

详见 `docs/product/XIANGTA_MVP_SCOPE.md`
