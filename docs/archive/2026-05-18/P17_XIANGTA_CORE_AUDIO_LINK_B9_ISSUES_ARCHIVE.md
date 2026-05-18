# P17 XiangTa Core Audio Link B9 Issues Archive

## Fixed / Handled

| ID | 问题 | 处理方式 | 文件 |
|---|---|---|---|
| F1 | `tts_orchestrator.py` `generate()` 使用 `profile_id` 变量但方法签名缺少该参数 | 添加 `profile_id: str | None = None` 参数 | `src/xiangta/services/tts_orchestrator.py` |
| F2 | `test_voice_lab_gateway_contract.py` 缺少 `CoreProfilesUnavailableError` 和 `CoreProfilesResponseError` 导入 | 添加到 import | `tests/xiangta/test_voice_lab_gateway_contract.py` |
| F3 | `tts_orchestrator.py` `tone_preset.resolve()` 异常未被 try-except 捕获，导致 `TonePresetDisabled` 直接穿透 | 将 `tone_preset.resolve()` 放入 try-except 块，转换为 `PresetNotFoundError` | `src/xiangta/services/tts_orchestrator.py` |
| F4 | `runtime_config.py` docstring 包含 `MINIMAX_API_KEY` 等字符串，导致边界测试误报 | 改写 docstring 为通用描述 | `src/xiangta/config/runtime_config.py` |
| F5 | `test_tts_api.py` 中 `_fake_generate_tts_with_profile` 定义在 `TestTtsHappyPath` 类内部，导致 `NameError: name '_fake_generate_tts_with_profile' is not defined` | 移动到模块级别，修正函数签名（移除多余 self_ 参数） | `tests/xiangta/test_tts_api.py` |
| F6 | `_fake_generate_tts` 函数签名有多余 `self` 参数（IDE hint） | 移除未使用的 `self` 参数 | `tests/xiangta/test_tts_api.py` |

## Deferred / Gaps

| ID | 问题 | 原因 | 后续建议 |
|---|---|---|---|
| G1 | `voice_mappings.json` 中 `coreProfileId` 为占位符 | B9 阶段不修改 Core 配置 | 后续 Admin 配置治理阶段正式映射 |
| G2 | Core `confirm_cost` 行为未验证 | 需真实链路测试 | B9 手工 smoke 时确认 |

## Not Changed

- Core `app/**` 未修改
- `src/voice_lab/**` 未修改
- Core Provider 未修改
- Core Repository 未修改
- Core Service 未修改
- Core schema/API contract 未修改
- 真实 API key 未读取
- 持久化未实现
- LLM 未接入
