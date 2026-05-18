# P18-XIANGTA-LLM-PROMPT-CONTRACT-C10C

## 实现内容

- 新增 `src/xiangta/services/copywriting_prompt_contract.py`
  - PromptContractInput / PromptMessage / PromptContract dataclasses
  - RECIPIENT_BOUNDARIES / SCENE_EMOTION_RULES / STYLE_OUTPUT_RULES
  - GLOBAL_SAFETY_RULES / TTS_FRIENDLY_RULES
  - build_copywriting_prompt_contract() — 构建完整 prompt contract
  - build_offline_eval_cases() — 10 个离线评估 case
  - validate_prompt_contract_static() — 静态校验（无网络调用）
- 新增 `tests/xiangta/test_copywriting_prompt_contract.py`（37 tests）
- 新增 `docs/agent/LLM_PROMPT_CONTRACT_C10C.md`
- 新增 `docs/agent/LLM_OFFLINE_EVAL_CASES_C10C.md`

## 测试结果

- 811 tests pass（+37 new）

## 未实现

- 未接真实 LLM Provider
- 未读取 API key
- 未发起网络请求
- 未修改 H5 主流程
- 未修改现有 /api/xiangta/suggestions 行为

## 下一步

P18-XIANGTA-MINIMAX-COPYWRITING-ADAPTER-C10D

## Follow-up cleanup

- H5 静态测试数量偏多，后续 cleanup 可压缩
- app.js 仍未拆分 ui-meta/ui-components，待前端方向稳定后再做组件化整理
