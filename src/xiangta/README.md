# src/xiangta — XiangTa 产品服务层

## 定位

XiangTa 产品服务层。
通过 `VoiceLabGateway` + `CoreHttpClient` 调用 Voice Lab Core 上层 HTTP API。
B9 已打通 Core profiles / Core render / audioUrl 播放链路。

**不直接 import Core 内部模块。不直接调用 Provider。不读取真实 API key。**

## 架构原则

- **唯一 Core 入口**：所有对 Core 的调用必须通过 `services/voice_lab_gateway.py` + `services/core_http_client.py`
- **前端零底层概念**：API 只传 recipient/scene/style/voicePreset/tone/profileId，不传 voice_id/model_id/provider/api_key
- **产品与底座分离**：本包不修改 `app/**` / `src/voice_lab/**` 任何文件
- **Core HTTP Only**：只通过以下 Core HTTP API 使用底座：`GET /api/voice/profiles`、`POST /api/voice/render`、`GET /api/voice/runtime/status`

## 目录结构

```
src/xiangta/
├── api/
│   ├── routes.py          — FastAPI 路由（挂载到 XiangTa runtime）
│   └── schemas.py         — 请求/响应 Pydantic 模型
├── services/
│   ├── voice_lab_gateway.py   — Core 访问边界（VoiceLabGateway）
│   ├── core_http_client.py    — Core HTTP 客户端（CoreHttpClient）
│   ├── tts_orchestrator.py    — TTS 任务调度
│   ├── product_service.py      — 主流程编排门面
│   ├── preset_mapper.py       — 产品预设映射（历史）
│   ├── copywriting_service.py — 文案建议（模板版）
│   ├── provider_status_service.py
│   ├── letter_service.py
│   ├── tone_preset_service.py
│   ├── voice_preset_mapping_service.py
│   └── error_translator.py
├── config/
│   └── runtime_config.py  — 运行时配置（XIANGTA_CORE_BASE_URL）
├── configs/               — 产品配置 JSON（voice_mappings.json 等）
├── prompts/               — LLM Prompt 模板（按场景）
└── models/                — 产品数据模型（dataclass）
```

## Core HTTP API 边界

XiangTa 只能使用以下 Core 上层 HTTP API：

```python
CORE_PROFILES_PATH = "/api/voice/profiles"
CORE_RENDER_PATH = "/api/voice/render"
CORE_STATUS_PATH = "/api/voice/runtime/status"
```

禁止 XiangTa 代码 import：

```python
app.providers.*
app.repositories.*
app.services.*
app.main
```

## 开发阶段

| 阶段 | 任务 | 状态 |
|---|---|---|
| A0 | 骨架初始化 | ✅ |
| A1 | 配置层 + Bootstrap + Gateway dry-run | ✅ |
| A2 | TTS dry-run 合约 | ✅ |
| B1-B4 | 产品配置模型（Repository / Bootstrap / Mapping / Admin） | ✅ |
| B5 | 文案建议（模板版） | ✅ |
| B6 | 信笺历史（进程内内存） | ✅ |
| B7 | H5 主流程 | ✅ |
| B8-1 | XiangTa Runtime 本地入口 | ✅ |
| **B9** | **Core audio link（profiles + render + audioUrl）** | **✅** |
| B9-FIX1 | H5 渲染修复 + tone 异常转换 | ✅ |
| B9-FIX2 | Core HTTP URL 拼接修复 | ✅ |
| B9-FIX3 | Core audioUrl 绝对路径修复 | ✅ |
| Next | H5 主流程 polish、profile mapping 产品化、TTS task orchestration 设计 | TODO |
| A3-A5 | 历史占位：真实 LLM 接入、异步任务、多用户 | Parked |

详见 `docs/agent/NEXT_TASKS.md`
