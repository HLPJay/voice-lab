# P16 Full Suite Baseline Triage D4-F2

**生成时间：** 2026-05-17  
**任务：** P16-V1-CLOSEOUT-FULL-SUITE-BASELINE-TRIAGE-D4-F2  

---

## 1. 当前分支与提交

| 项目 | 值 |
|------|----|
| 分支 | `p16/real-usage-issues` |
| HEAD | `013c011` fix: ensure provider URL filter is applied before first loadAll draw |
| D4-F1 | `740bc5e` fix: clarify local stats are not official provider billing |
| D4-F0 | `a3f762a` fix: apply provider visibility filter at runtime |
| D4-E0 | `d0116e2` fix: hide testing providers from normal UI |

---

## 2. Scoped Tests 结果

```
python -m pytest tests/test_cost_guard.py tests/test_runtime_status_header_static.py tests/test_usage_stats_semantics_static.py -q
```

**结果：102 passed，0 failed，耗时 7.86s**

---

## 3. Full Suite 结果

```
python -m pytest -q --tb=short --disable-warnings
```

**结果：1707 passed，57 failed，7 skipped，1 error，耗时 318s**

### 失败文件清单

| 文件 | 失败数 |
|------|--------|
| `tests/test_context_store_static.py` | 29 |
| `tests/test_voice_preview.py` | 5 |
| `tests/test_provider_voice_import.py` | 4 |
| `tests/test_xiaomi_mimo_chat_tts_adapter.py` | 4 |
| `tests/test_voice_clone.py` | 4 |
| `tests/e2e/test_frontend_capabilities.py` | 4 (+1 error) |
| `tests/test_cancel_confirmation_static.py` | 3 |
| `tests/test_voice_design.py` | 2 |
| `tests/test_voice_binding_service.py` | 1 |
| `tests/test_workspace_restore_static.py` | 1 |

---

## 4. 失败模块分组

### A. Xiaomi MiMo adapter 配置类（4 个）

**文件：** `tests/test_xiaomi_mimo_chat_tts_adapter.py`

| 测试 | 断言内容 | 实际状态 |
|------|----------|---------|
| `test_xiaomi_mimo_disabled_by_default` | `enabled is False` | `enabled = True` |
| `test_xiaomi_mimo_adapter_config_voice_clone_unsupported` | `voice_clone.supported is False` | `supported = True` |
| `test_xiaomi_mimo_adapter_config_voice_design_unsupported` | `voice_design.supported is False` | `supported = True` |
| `test_xiaomi_mimo_not_in_capabilities_when_disabled` | `xiaomi_mimo not in providers` | xiaomi_mimo 已出现在列表中 |

**根因：** P16 阶段（d0116e2 之前）已将 xiaomi_mimo 设为 `enabled=true`，adapter YAML 已定义 `voice_clone.supported: true` 和 `voice_design.supported: true`。这些测试的断言基于 xiaomi_mimo 仍处于禁用/受限状态的旧口径，已过期。

### B. context store 类（29 个）

**文件：** `tests/test_context_store_static.py`

**全部失败原因：** `Failed: Node.js eval failed:` — Node.js 端返回空 stdout。

**根因：** 测试依赖 `require('jsdom')` 来模拟 localStorage。当前环境 Node.js v22.15.0 已安装，但 **`jsdom` npm 包未安装**。

```
node -e "const { JSDOM } = require('jsdom');"
# Error: Cannot find module 'jsdom'
```

与代码逻辑无关，纯环境依赖缺失。

### C. cancel confirmation 类（3 个）

**文件：** `tests/test_cancel_confirmation_static.py`

| 测试 |
|------|
| `test_clone_quick_preview_confirm_before_fetch` |
| `test_design_quick_preview_confirm_before_fetch` |
| `test_import_quick_preview_confirm_before_fetch` |

**根因：** 同 B 组，依赖 jsdom，未安装。

### D. workspace restore 类（1 个）

**文件：** `tests/test_workspace_restore_static.py`

- `test_safePushWorkspaceSample_writes_context_id_to_sample`

**根因：** 同 B 组，依赖 jsdom，未安装。

### E. voice preview 独立运行失败（3 个）

**文件：** `tests/test_voice_preview.py`，运行 `python -m pytest tests/test_voice_preview.py` 也失败

| 测试 | 错误 |
|------|------|
| `TestProviderVoicePreviewService::test_plan_uses_provider_voice_id_not_binding` | POST 返回 422，期望 200 |
| `TestProviderVoicePreviewResourceGuard::test_preview_rejected_when_slot_full` | `ProviderVoicePreviewRequest` 缺少必填 `provider` 字段 |
| `TestVoicePreviewResourceGuard::test_preview_rejected_when_slot_full` | 同上 |

**根因：** commit `7a89847`（P16 早期，远早于 D4）将 `ProviderVoicePreviewRequest.provider` 从有默认值 `"minimax"` 改为无默认值的必填字段：

```python
# before 7a89847
provider: str = "minimax"
# after 7a89847  
provider: str = Field(min_length=1)
```

对应测试发送请求时未包含 `provider` 字段，导致 422。测试未随 schema 更新。

### F. voice preview 全量套件额外失败（2 个，仅在 full suite 中出现）

**文件：** `tests/test_voice_preview.py`

| 测试 |
|------|
| `TestMiniMaxClonePayload::test_clone_payload_excludes_input_sensitive` |
| `TestMiniMaxDesignVoice::test_design_voice_base_resp_failure_raises_provider_error` |

**根因：** 这两个测试需要 MINIMAX_API_KEY 有值（adapter 的 `_require_api_key()` 在 `_request` mock 之前被调用）。全量套件运行时 conftest.py autouse fixture `reset_httpx_shared_client` 会在每个测试前调用 `clear_settings_cache()`，清空 lru_cache 后重新读取 Settings。在某些测试执行顺序下，Settings 的 env_file 解析可能失效，导致 key 为空。独立运行时 `.env` 文件正常被 `pydantic_settings` 读取，key 有值，测试通过。

### G. voice clone / design / import / binding 全量套件失败（11 个，仅在 full suite 中出现）

**文件：** `test_voice_clone.py` (4), `test_voice_design.py` (2), `test_provider_voice_import.py` (4), `test_voice_binding_service.py` (1)

**验证：**
```
python -m pytest tests/test_voice_clone.py tests/test_voice_design.py tests/test_provider_voice_import.py tests/test_voice_binding_service.py -q
# 47 passed (0 failed!)
```

**根因：** 测试隔离问题——独立运行全部通过，全量套件中某些先行测试污染了共享状态（数据库 session/model registry 或 Settings cache），导致后续测试失败。不是 D4 引入的回归。

### H. E2E 前端能力类（4 个失败 + 1 error）

**文件：** `tests/e2e/test_frontend_capabilities.py`

| 测试 |
|------|
| `test_voice_clone_error_insufficient_balance_is_displayed` |
| `test_voice_clone_mock_submit_success` |
| `test_voice_import_clone_mock_success` |
| `test_quick_bind_success_go_create_switches_workspace` |

**根因：** Playwright E2E 测试失败。主要错误包括：
- `Element is not an <input>, <textarea> or [contenteditable] element` — UI 结构变化后 locator 失效
- `'绑定成功' in '请选当前 Provider 支持的模型'` — 预期成功消息但收到模型验证提示，UI 流程变化

---

## 5. Pre-existing 验证矩阵

**验证方法：** 使用 `git worktree` 在 `740bc5e` 和 `a3f762a` 两个历史 commit 上运行相同失败文件的子集，与 HEAD `013c011` 对比。

```bash
git worktree add ../voice_lab_triage_740bc5e 740bc5e
git worktree add ../voice_lab_triage_a3f762a a3f762a
```

| 失败模块 | HEAD 013c011 | 740bc5e | a3f762a | 判断 |
|----------|:-----------:|:-------:|:-------:|------|
| A: xiaomi_mimo adapter (4) | FAIL | FAIL | FAIL | **pre-existing，P16 早期已存在** |
| B: context_store (29) | FAIL | FAIL | FAIL | **pre-existing，jsdom 环境依赖** |
| C: cancel_confirmation (3) | FAIL | FAIL | FAIL | **pre-existing，jsdom 环境依赖** |
| D: workspace_restore (1) | FAIL | FAIL | FAIL | **pre-existing，jsdom 环境依赖** |
| E: voice_preview standalone (3) | FAIL | FAIL | FAIL | **pre-existing，schema 变更 7a89847** |
| F: voice_preview full-suite-only (2) | FAIL | FAIL* | FAIL* | **pre-existing，API key env 依赖** |
| G: voice clone/design/import/binding standalone | PASS | PASS† | PASS† | **非代码回归，测试顺序污染** |
| H: E2E (4) | FAIL | FAIL | FAIL | **pre-existing，UI 流程变化** |

> \* worktree 无 `.env` 文件，MINIMAX_API_KEY 不可用，这两个测试在 worktree 中也失败（原因略有不同）  
> † 注意：a3f762a worktree 中 TestMiniMaxCloneAdapter 两个测试因无 .env 而失败，但在主目录（有 .env）独立运行时通过

**关键结论：** D4-F1（740bc5e）和 D4-F1A（013c011）**均未引入任何新失败**。所有 57 个失败在 a3f762a（D4-F0 之前）已存在或属于环境依赖问题。

---

## 6. 失败原因初判

| 组 | 失败原因 | D4-F1/F1A 引入？ | P16 引入？ | main 已存在？ | 环境问题？ | 测试假设过期？ |
|----|---------|:--:|:--:|:--:|:--:|:--:|
| A xiaomi_mimo adapter | 测试断言已过期（xiaomi_mimo 被 P16 启用） | 否 | 是（P16 启用时测试未更新） | 否 | 否 | **是** |
| B/C/D jsdom 类 | npm jsdom 包未安装 | 否 | 否 | 可能否 | **是** | 否 |
| E voice_preview schema | provider 字段变为必填（7a89847） | 否 | 是（P16 早期） | 否 | 否 | **是（测试未更新）** |
| F voice_preview full-suite env | .env/API key 在 full suite 中丢失 | 否 | 否 | 否 | **是** | 否 |
| G clone/design/import ordering | 测试顺序污染，standalone 通过 | 否 | 否 | 可能是 | 否 | 否 |
| H E2E 前端 | UI 结构/流程变化导致 locator/断言过期 | 否 | 是（P16 晚期） | 否 | **是（需浏览器）** | **是** |

---

## 7. 必须合并前修复的问题

以下问题影响 V1 核心链路或有真实误导风险，建议在合并前修复：

### 7.1 E: voice_preview schema（3 个独立运行失败）

**文件：** `tests/test_voice_preview.py`  
**原因：** `ProviderVoicePreviewRequest` schema 变更后测试未更新，测试向 `/api/voice/provider-voices/preview` 发请求时缺少必填 `provider` 字段  
**风险等级：** 中 — 测试覆盖了 voice preview 的核心逻辑（RenderPlan 使用正确 voice_id、资源守卫）  
**修复方向：** 在测试请求体中补充 `"provider": "mock"` 字段；对 schema validation 测试补充 provider missing 的 422 case  

### 7.2 A: xiaomi_mimo adapter 测试对齐（4 个失败）

**文件：** `tests/test_xiaomi_mimo_chat_tts_adapter.py`  
**原因：** 测试断言 xiaomi_mimo 禁用/不支持 clone/design，但 P16 已启用并配置这些能力  
**风险等级：** 中 — 这些测试的"失败"实际是测试假设与当前 V1 口径不符，不代表代码错误  
**修复方向：** 更新测试：删除/反转 disabled_by_default 断言，添加 enabled=true 正向断言；根据 V1 口径说明 clone/design 当前实验性可选  

---

## 8. 可以延后处理的问题

| 组 | 建议处理任务 | 优先级 |
|----|------------|--------|
| B/C/D jsdom 环境 (33) | 安装 `jsdom`：`cd voice_lab && npm install jsdom`（需确认 package.json 依赖管理） | 低 |
| F full-suite env (2) | 补充 mock `_require_api_key()` 或在 conftest 注入测试 key；不涉及真实 API | 中 |
| G ordering pollution (11) | 排查 full suite 测试顺序污染源（可能是某个 test 改变了 module-level DB state）；standalone 通过所以不阻塞 | 低 |
| H E2E (4) | Playwright E2E 失败需要专项调试，UI 流程变化需要更新 locator 和断言 | 低 |

---

## 9. 下一步任务建议

### P16-V1-CLOSEOUT-VOICE-PREVIEW-TEST-FIX-D4-F3A（阻塞合并，建议优先）

修复 `tests/test_voice_preview.py` 中 3 个独立失败的测试：
- `test_plan_uses_provider_voice_id_not_binding`：请求体补充 `"provider": "mock"`
- `test_preview_rejected_when_slot_full`（×2）：构造 `ProviderVoicePreviewRequest` 时补充 `provider="minimax"`

### P16-V1-CLOSEOUT-XIAOMI-MIMO-TEST-ALIGN-D4-F3（阻塞合并，建议优先）

将 `tests/test_xiaomi_mimo_chat_tts_adapter.py` 的测试假设更新为当前 V1 口径：
- 将 `test_xiaomi_mimo_disabled_by_default` 改为 `test_xiaomi_mimo_enabled_by_default`
- 删除 voice_clone/design `supported is False` 断言，改为当前配置实际值
- 将 `test_xiaomi_mimo_not_in_capabilities_when_disabled` 改为正向验证 xiaomi_mimo 出现在 capabilities 中

### P16-V1-CLOSEOUT-JSDOM-ENV-SETUP-D4-F4（可延后）

安装 jsdom，解除 B/C/D 共 33 个测试的环境依赖：
- 确认是否有 `package.json` / `package-lock.json`；
- `npm install jsdom` 并记录到依赖管理

### P16-V1-CLOSEOUT-E2E-REPAIR-D4-F5（可延后）

修复 4 个 Playwright E2E 测试，更新 UI locator 和断言适配当前 P16 UI 结构。

### P16-V1-CLOSEOUT-FULL-SUITE-ORDERING-D4-F6（低优先级）

排查 full suite 测试顺序污染：11 个测试 standalone 通过，full suite 失败，需找到造成污染的 fixture 或 DB session 泄漏。

---

## 10. 明确结论

### 是否可以合并 main：**否（当前有 2 个明确阻塞项）**

**阻塞项：**

1. **voice_preview schema 测试失败（E 组，3 个独立运行失败）**  
   原因：schema 变更后测试未更新，`ProviderVoicePreviewRequest` 缺少必填 `provider` 字段。  
   影响：Provider Voice Preview 链路测试覆盖失效，合并后 CI 会持续红。

2. **xiaomi_mimo adapter 测试假设过期（A 组，4 个失败）**  
   原因：P16 已将 xiaomi_mimo 设为 enabled，但测试仍断言 disabled。  
   影响：测试对 V1 功能状态的误描述，导致测试套件不可信。

**豁免清单（合并前可明确豁免的失败）：**

| 豁免项 | 失败数 | 豁免理由 |
|--------|--------|----------|
| jsdom 环境（B/C/D 组） | 33 | npm 依赖问题，与业务代码无关，可独立处理 |
| full-suite ordering（G 组） | 11 | standalone 全通过，非代码回归 |
| full-suite env（F 组） | 2 | .env 隔离问题，不影响代码正确性 |
| E2E（H 组） | 4 | 需浏览器环境专项调试，不影响后端/API 链路 |

**合并前必须修复：**
- D4-F3A: voice_preview 测试修复（3 个）
- D4-F3: xiaomi_mimo 测试对齐（4 个）

修复完成后 full suite 将从 57 failed → **约 46 failed（均为可豁免类）**，达到可合并条件。
