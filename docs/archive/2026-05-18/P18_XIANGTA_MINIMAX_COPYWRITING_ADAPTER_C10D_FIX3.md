# P18-XIANGTA-MINIMAX-COPYWRITING-ADAPTER-C10D-FIX3 — Archive

**拆分 MiniMax base URL 和 endpoint path，修复 A 类 URL 语义冲突**

## 概述

基于 C10D-FIX2 MiniMax 官方文档核验结果，修复真实联调前的 A 类 blocker。

## 修改文件

- `src/xiangta/services/copywriting_minimax_gateway.py` — 新增 `MiniMaxConfigError`、`build_minimax_chat_completion_url()`、`endpoint_path` 参数
- `src/xiangta/config/runtime_config.py` — 新增 `minimax_copywriting_endpoint_path` 字段和 env 覆盖
- `src/xiangta/services/product_service.py` — 传入 `endpoint_path` 到 gateway
- `tests/xiangta/test_copywriting_minimax_gateway.py` — 新增 URL builder 和 endpoint_path 测试
- `tests/xiangta/test_runtime_config.py` — 新增 `endpoint_path` 读取和覆盖测试
- `configs/xiangta.runtime.local.example.json` — baseUrl 修正为 `https://api.minimaxi.com`，新增 `endpointPath`
- `docs/xiangta/MINIMAX_COPYWRITING_ADAPTER_GAP_ANALYSIS_C10D_FIX2.md` — 标记 A-1 已修复
- `docs/xiangta/MINIMAX_OFFICIAL_API_REFERENCE_C10D_FIX2.md` — 添加 C10D-FIX3 说明
- `docs/xiangta/MINIMAX_COPYWRITING_ADAPTER.md` — 新增主 adapter 文档
- `docs/agent/MINIMAX_COPYWRITING_LOCAL_CONFIG_C10D_FIX1.md` — 修正 baseUrl 示例

## 修复内容

### A 类 blocker 修复

**问题**：`baseUrl` 语义未锁定，用户可能把完整 endpoint 填入 `baseUrl`，导致 adapter 拼接出重复路径。

**修复**：
- 新增 `endpoint_path` 配置字段，默认 `/v1/chat/completions`
- `baseUrl` 只能是 host/base（`https://api.minimaxi.com`），不得包含 endpoint path
- `build_minimax_chat_completion_url()` 在 `baseUrl` 包含 `/v1/chat/completions` 时主动抛 `MiniMaxConfigError`
- 适配器显式使用 `base_url + endpoint_path` 拼接

### runtime_config 新字段

```python
@dataclass(frozen=True)
class XiangTaRuntimeConfig:
    minimax_copywriting_endpoint_path: str = "/v1/chat/completions"
```

支持配置路径：
- `copywriting.minimax.endpointPath`（nested，local config）
- `copywriting.minimaxEndpointPath`（flat，local config）
- `XIANGTA_MINIMAX_COPYWRITING_ENDPOINT_PATH`（env，最高优先级）

## 适配器 URL 语义确认

| 字段 | 值 |
|---|---|
| `baseUrl` | `https://api.minimaxi.com` |
| `endpointPath` | `/v1/chat/completions` |
| full URL | `https://api.minimaxi.com/v1/chat/completions` |

## 测试结果

```
tests/xiangta/test_copywriting_minimax_gateway.py: 16 passed
tests/xiangta/test_runtime_config.py: 49 passed
tests/xiangta -q --basetemp .pytest-tmp: 841 passed + 7 pre-existing SQLite failures
```

## 未真实调用 MiniMax

本任务未进行任何真实 MiniMax API 调用。

## 下一步

`P18-XIANGTA-MINIMAX-COPYWRITING-EVAL-C10E` — 使用 `configs/xiangta.runtime.local.json` 中的真实 key 进行 behind-flag smoke 与 10-case 情绪效果评估。

C10E 联调前条件：
- `baseUrl = https://api.minimaxi.com`
- `endpointPath = /v1/chat/completions`
- 真实 apiKey 已填入 local config 或 env
- 确认 `feature_llm_copywriting_enabled=true`、`copywriting_mode=llm`、`copywriting_provider=minimax`
