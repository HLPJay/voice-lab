# P18-XIANGTA-MINIMAX-COPYWRITING-ADAPTER-C10D — Archive

**MiniMax LLM Copywriting Adapter — behind feature flag, default disabled**

## 概述

实现真实 MiniMax LLM 文案生成 adapter behind feature flag，默认不启用。

## 新增文件

- `src/xiangta/services/copywriting_minimax_gateway.py` — 核心实现
- `tests/xiangta/test_copywriting_minimax_gateway.py` — 18 个测试

## 修改文件

- `src/xiangta/config/runtime_config.py` — 新增 MiniMax 配置字段
- `src/xiangta/services/product_service.py` — MiniMax gateway 注入逻辑

## 关键设计

### MiniMaxCopywritingGateway

- 实现 `CopywritingGateway` Protocol
- 复用 `build_copywriting_prompt_contract()` 构建 prompt
- `MiniMaxHttpClient` Protocol 实现 HTTP 抽象
- `UrllibMiniMaxHttpClient` 使用 stdlib urllib（无额外依赖）
- `parse_minimax_copywriting_response()` 支持多种响应格式

### 响应格式支持

- `choices[0].message.content`
- `reply`
- `content`
- `data.choices[0].message.content`
- ```json``` fence 包裹格式

### 验证规则

- 必须恰好 3 条 suggestions
- style 必须在 `restrained | gentle | sincere` 中
- 每条 text 和 fitsFor 不得为空
- 输出不得包含 `apiKey | coreProfileId | providerRawResponse | rawResponse`

### Feature Flag 条件

```python
runtime_config.feature_llm_copywriting_enabled == True
runtime_config.copywriting_mode == "llm"
runtime_config.copywriting_provider == "minimax"
runtime_config.minimax_copywriting_api_key is not None
runtime_config.minimax_copywriting_base_url is not None
runtime_config.minimax_copywriting_model is not None
```

## 环境变量

| 变量 | 说明 |
|---|---|
| `XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED` | 启用 LLM 文案 |
| `XIANGTA_COPYWRITING_MODE` | `llm` |
| `XIANGTA_COPYWRITING_PROVIDER` | `minimax` |
| `XIANGTA_MINIMAX_COPYWRITING_API_KEY` | MiniMax API key |
| `XIANGTA_MINIMAX_COPYWRITING_BASE_URL` | MiniMax base URL |
| `XIANGTA_MINIMAX_COPYWRITING_MODEL` | 模型名称 |
| `XIANGTA_COPYWRITING_FALLBACK_TO_TEMPLATE` | LLM 失败时是否 fallback 到模板 |

## 测试结果

- 18/18 MiniMax gateway tests: PASS
- 94 个 copywriting 相关测试: PASS
- 822 xiangta suite: PASS + 7 pre-existing SQLite failures

## 后续

- C10E: 真实 MiniMax 手工联调与 10-case 情绪效果评估
- 不得默认启用真实 Provider
- 不得修改 H5 主流程
