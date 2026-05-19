# P18-XIANGTA-COPYWRITING-LLM-MVP-C8

## 实现内容

- 新增 `CopywritingGateway` Protocol（`copywriting_gateway.py`）
- 新增 `TemplateCopywritingGateway`：复用模板逻辑
- 新增 `FakeLlmCopywritingGateway`：可预测 fake LLM 文案
- `CopywritingService` 支持 `gateway + fallback_to_template` 模式
- `create_product_service` 根据 `runtime_config` 自动装配 gateway
- 默认（`feature_llm_copywriting_enabled=false` 或 `provider!=fake`）走 template
- 显式 `XIANGTA_COPYWRITING_MODE=llm + XIANGTA_COPYWRITING_PROVIDER=fake` 走 fake LLM
- unknown/minimax/openai/deepseek 等未实现 provider → safe fallback template
- LLM 失败时 `fallback_to_template=True` → template；`fallback_to_template=False` → `LlmFailedError`
- `/suggestions` 响应结构保持不变，不暴露 provider/model/apiKey

## 测试覆盖

`tests/xiangta/test_copywriting_gateway.py`：14 个测试
- TemplateGateway 返回 3 条 stable suggestions
- FakeLlmGateway 返回 fake LLM 文案
- `CopywritingService(gateway=None)` 走 template
- `CopywritingService(gateway=fake)` 走 fake LLM
- fake gateway 失败 + `fallback=True` → template
- fake gateway 失败 + `fallback=False` → `LlmFailedError`
- 默认 config → template（无真实 API 调用）
- env 开启 fake LLM → `get_suggestions` 走 fake LLM
- unknown provider → safe fallback template
- `/suggestions` 不暴露 provider/model/apiKey

## 未实现

- 真实 MiniMax / OpenAI / DeepSeek / Claude API
- API key 读取 / HTTP client / httpx
- agent / 工具调用 / 多轮对话 / 用户画像
- prompt 管理平台
- 真实 LLM provider adapter（C8.5 或独立 provider 接入阶段）

## 下一步

P18-XIANGTA-H5-PRODUCT-FLOW-C9
