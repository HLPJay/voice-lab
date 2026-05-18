# B9 Core Audio Link Report

## 1. 阶段目标

XiangTa 产品层通过 Core 已公开的上层 HTTP API，完成"选择 Core 已有人设 → 调用 Core 音频生成 → 返回 audioUrl → H5 播放"的链路测试。

## 2. 当前实现链路

```
H5
→ GET /api/xiangta/core/profiles
→ XiangTa Gateway HTTP GET /api/voice/profiles
→ 用户选择 Core profile
→ POST /api/xiangta/tts (with profileId)
→ TtsOrchestrator (profile_id direct path)
→ VoiceLabGateway
→ Core HTTP POST /api/voice/render
→ Core 返回 audio_asset.url
→ XiangTa 返回 audioUrl
→ H5 展示 <audio controls> 播放器
```

## 3. 新增 API

| API | 方法 | 说明 |
|---|---|---|
| `/api/xiangta/core/profiles` | GET | 返回 Core 已有人设列表，source="core" 或 "not_integrated" |
| `/api/xiangta/tts` | POST | 支持可选 `profileId` 字段，直接走 Core profile 路径 |

## 4. H5 行为

- 页面加载时调用 `GET /api/xiangta/core/profiles`
- 新增 `coreProfileSelect` 下拉框展示 Core profiles
- 生成 TTS 时若选择 profile，payload 包含 `profileId`
- TTS 成功时用 DOM API 渲染 `<audio controls>` 播放器
- 未配置 Core 时显示"未连接 Core"或"暂无人设"

## 5. Core 连接方式

通过环境变量 `XIANGTA_CORE_BASE_URL` 配置，指向 `http://127.0.0.1:8000`。

## 6. 未配置 Core 时的降级行为

| 接口 | 行为 |
|---|---|
| `GET /api/xiangta/core/profiles` | 返回 `{"profiles": [], "total": 0, "source": "not_integrated"}` |
| `POST /api/xiangta/tts` (with profileId) | 返回 `NoProviderError`，H5 显示清晰错误，不崩溃 |

## 7. 是否修改 Core

- `app/**` 未修改
- `src/voice_lab/**` 未修改
- Core Provider/Repository/Service 未修改
- Core schema/API contract 未修改

## 8. 是否读取真实 API key

- 未读取 `MINIMAX_API_KEY`
- 未读取 `MIMO_API_KEY`
- 未读取 `OPENAI_API_KEY`
- 未读取 `DEEPSEEK_API_KEY`

## 9. 测试结果

```bash
python -m pytest tests/xiangta -q
572 passed in 4.38s
```

目标测试全部通过：
- `tests/xiangta/test_voice_lab_gateway_contract.py` ✅
- `tests/xiangta/test_tts_orchestrator.py` ✅
- `tests/xiangta/test_tts_api.py` ✅
- `tests/xiangta/test_h5_static_contract.py` ✅
- `tests/xiangta/test_b9_boundary_contract.py` ✅

## 10. 手工验证步骤

终端 1 - 启动 Voice Lab Core：
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

终端 2 - 启动 XiangTa Runtime：
```powershell
$env:XIANGTA_CORE_BASE_URL="http://127.0.0.1:8000"
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5173
```

访问 `http://127.0.0.1:5173/`，验证：
1. 页面能打开
2. 能加载 bootstrap
3. 能加载 Core profiles（`coreProfileSelect` 下拉框有内容）
4. 能选择 profile
5. 能输入文案
6. 能提交 TTS
7. 若 Core/provider 可用，能返回 audioUrl 并展示播放器
8. 若 Core/provider 不可用，H5 显示清晰错误，不崩溃
9. 页面不展示 `provider_voice_id` / `binding_id` / `params_json` / `api_key`

## 11. 遗留问题

1. `voice_mappings.json` 中 `coreProfileId` 仍为占位符，正式产品配置需在后续 Admin/配置治理阶段消化
2. Core cost guard 行为（`confirm_cost`）需在真实链路测试时确认

## 12. 下一步建议

- B9 手工真实链路 smoke（Core + XiangTa 双服务联调）
- profile mapping 产品化（Admin 接口正式接 Core profiles）
- Core cost guard / `confirm_cost` 行为确认
- LLM 文案接入待定
