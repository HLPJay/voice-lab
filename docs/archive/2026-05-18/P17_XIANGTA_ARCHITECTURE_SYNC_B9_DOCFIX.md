# P17 XiangTa Architecture Sync B9 Docfix

## Context

B9 + FIX1 + FIX2 + FIX3 completed and manually smoke-tested.

## What was synchronized

| Area | Update |
|---|---|
| `docs/xiangta/B9_MANUAL_SMOKE_REPORT.md` | **新增** — B9 手工验收报告（启动方式、链路、已修复问题、遗留问题） |
| `docs/xiangta/ARCHITECTURE.md` | **更新** — 新增"架构总览"、"Concurrency & Scalability Boundary"、"当前不做事项"，更新 B9 调用链 |
| `src/xiangta/README.md` | **更新** — 同步阶段状态，删除过期 A1/A2/A3/A4 TODO，添加 B9 完成状态 |
| `apps/xiangta_runtime/main.py` | **更新** — docstring 描述 B9 Core audio link 双服务模式 |
| `apps/xiangta_runtime/README.md` | **更新** — 描述 B9 链路、启动命令、注意事项 |
| `docs/agent/NEXT_TASKS.md` | **更新** — 添加 B9-FIX1/2/3 完成状态，新增 C1-C4/NEXT 下一步 |

## Architecture boundary

- **Core remains unchanged**：`app/**`、`src/voice_lab/**` 未修改
- **XiangTa uses Core HTTP API only**：只通过 `GET /api/voice/profiles`、`POST /api/voice/render`、`GET /api/voice/runtime/status` 调用 Core
- **No forbidden imports**：XiangTa 代码未 import `app.providers.*`、`app.repositories.*`、`app.services.*`

## apps / src / app boundaries documented

| 目录 | 定位 |
|---|---|
| `app/**` | Voice Lab Core — 音频能力底座（profile/binding/provider/render/asset/job） |
| `src/xiangta/**` | XiangTa 产品服务层 — 通过 HTTP 调用 Core，不直接调用 Provider/Repository |
| `apps/xiangta-h5/**` | XiangTa H5 前端 — 静态 HTML/JS，用户输入与播放 |
| `apps/xiangta_runtime/**` | XiangTa 本地 runtime — 应用壳，挂载 H5 + /api/xiangta/* |

## Concurrency boundary

- **Current B9 is synchronous**：POST /api/xiangta/tts 同步等待 Core render 完成
- **Current scope is local single-user / light browser validation**
- **Future TTS task orchestration required**：后续需 `POST /api/xiangta/tts/tasks` + `GET /api/xiangta/tts/tasks/{taskId}`

## Not changed

- No business logic changed
- No Core code changed
- No provider code changed
- No API key read
- No persistence added
- No LLM added
- No tests added (documentation-only task)
