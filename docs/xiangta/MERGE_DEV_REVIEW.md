# XiangTa Merge Dev Review

**任务**：P17-XIANGTA-MERGE-DEV-REVIEW  
**审查员**：Claude Code  
**审查日期**：2026-05-18

---

> **B8-1 补充说明（2026-05-18）**：原结论为 PASS_WITH_NOTES，其中 Note 1 指出 XiangTa router 尚未挂载到运行时入口。
> P17-XIANGTA-RUNTIME-B8-1 已补齐此项：新增 `apps/xiangta_runtime/main.py`，同源挂载 H5（`/h5`）和 `/api/xiangta/*`，本地可通过单一 runtime 入口启动。
> 建议在执行 merge 前完成本地手工冒烟确认（P17-XIANGTA-RUNTIME-MANUAL-SMOKE-B8-2）或直接进入 merge execute。

---

## 1. 审查结论

**PASS_WITH_NOTES**

可以进入 `P17-XIANGTA-MERGE-DEV-EXECUTE`，带以下 notes：

1. **MVP 限制已知**：TTS 默认路径无 Core http_client，返回 no_provider；letters 为进程内内存，重启丢失；suggestions 为模板版，不调用 LLM。这些都是已知的、有意识的 MVP 边界。
2. **全仓测试存在 56 个预存在失败**，全部在非 XiangTa 模块（`test_voice_preview`, `test_xiaomi_mimo_call_log`, `e2e`），与本次改动无关。XiangTa scoped 测试 512/512 全绿。
3. **合并后不得直接进入真实 Provider 接入**。真实 Provider / LLM 接入应在 dev 合并审查通过后，作为独立新阶段处理。

---

## 2. 分支信息

| 项 | 值 |
|---|---|
| source | `p17/xiangta-product-init` |
| target | `dev` |
| source HEAD | `2054ee9` |
| target dev HEAD | `c9637c2` |
| review date | 2026-05-18 |

---

## 3. Diff 范围概览

### 3.1 文件统计

| 类型 | 数量 |
|---|---|
| 新增（A） | 83 |
| 修改（M） | 1 |
| 删除（D） | 0 |
| 总计 | 84 |
| 净增行数 | +12,009 / -7 |

本次改动包含 22 个 commit，从 `c6919f6`（P17-XIANGTA-INIT-A0）到 `2054ee9`（MVP-CLOSEOUT-B7）。

### 3.2 主要目录分布

| 目录 | 文件数 | 说明 |
|---|---|---|
| `src/xiangta/` | 26 | 新产品层：api / config / models / services / configs |
| `tests/xiangta/` | 25 | 新测试：512 tests |
| `docs/xiangta/` | 11 | 新产品文档 |
| `apps/xiangta-h5/` | 6 | H5 静态前端 |
| `docs/product/` | 5 | 历史阶段文档（A0-A2）|
| `apps/xiangta_mobile/` | 1 | 占位 README |
| `docs/agent/` | 1（M）| NEXT_TASKS.md 修改 |

### 3.3 删除文件

**无删除文件。**

（注：`serve_xiangta_h5.py` 在 B7-1-FIX1 中从根目录移动到 `apps/xiangta-h5/serve.py`，在 git diff 中表现为 rename，非 delete。）

---

## 4. 功能范围

### 4.1 XiangTa Backend（`src/xiangta/`）

全部新增，无对 Core `app/` 或 `src/voice_lab/` 的修改。

| 模块 | 说明 |
|---|---|
| `api/routes.py`, `api/schemas.py` | FastAPI 路由 + Pydantic 模型 |
| `config/product_config_repository.py` | 读取 JSON 配置 |
| `config/product_config_writer.py` | 原子写配置（threading.Lock） |
| `services/bootstrap_service.py` | bootstrap 组装 |
| `services/tts_orchestrator.py` | TTS 编排（→ VoiceLabGateway） |
| `services/voice_lab_gateway.py` | 唯一 Core 边界 |
| `services/copywriting_service.py` | 模板文案建议 |
| `services/letter_service.py` | 进程内 letters 存储 |
| `services/admin_config_service.py` | Admin 配置写委托 |
| `services/error_translator.py` | 统一错误翻译 |
| `configs/*.json` | 产品配置：recipients / scenes / voice_mappings / tone_presets |

### 4.2 Admin Config API

| 接口 | 说明 |
|---|---|
| `GET /admin/config` | 只读汇总 |
| `GET /admin/voice-mappings`, `GET /admin/tone-presets` | 只读列表 |
| `PUT /admin/voice-mappings/{id}` | 原子写 |
| `PATCH /admin/voice-mappings/{id}/enabled` | 启用/禁用 |
| `PUT /admin/tone-presets/{id}` | 原子写 |
| `PATCH /admin/tone-presets/{id}/enabled` | 启用/禁用 |

### 4.3 H5 Frontend（`apps/xiangta-h5/`）

全部新增，无运行时外部依赖。

| 文件 | 说明 |
|---|---|
| `index.html` | 单页 H5，移动端优先 |
| `styles.css` | 纯 CSS，无外部字体/CDN |
| `app.js` | 纯 JS，API_BASE="" |
| `serve.py` | 本地预览 FastAPI 静态服务 |
| `DESIGN_REFERENCE.md` | 设计来源说明 |
| `README.md` | 使用说明 |

### 4.4 Docs / Tests

- `docs/xiangta/**`：11 个新产品文档（architecture / api contract / config model / roadmap / closeout report 等）
- `tests/xiangta/**`：25 个新测试文件，512 tests 全绿
- `docs/product/XIANGTA_*.md`：5 个 A0-A2 历史阶段文档（已完成，保留为参考）

---

## 5. Core / Provider 边界检查

### 5.1 app/** 修改

**无。** `app/` 目录（Voice Lab Core）未被修改。

```
git diff --name-only origin/dev...origin/p17/xiangta-product-init | grep '^app/' → 无命中
```

### 5.2 src/voice_lab/** 修改

**无。** `src/voice_lab/` 目录未被修改。

### 5.3 src/xiangta/** 架构边界

- XiangTa 不 import `app.repositories.*` / `app.providers.*`
- XiangTa 不调用 `get_provider()` / `adapter.render_sync()`
- XiangTa 不构造 `RenderPlan`
- `VoiceLabGateway` 是唯一 Core 通信边界（当前无真实 http_client 注入，返回稳定降级）
- boundary contract 测试（`test_boundary_contract.py`）自动持续验证上述约束

### 5.4 design_h5/** 修改

**无。** 设计稿目录未被修改。

---

## 6. API key / Secret 检查

扫描范围：`src/xiangta`, `apps/xiangta-h5`, `tests/xiangta`, `docs/xiangta`, `docs/agent`

| 命中类型 | 数量 | 说明 |
|---|---|---|
| 运行时代码命中 | **0** | `src/xiangta/` 无任何 `MINIMAX_API_KEY` / `MIMO_API_KEY` / `OPENAI_API_KEY` |
| 测试断言命中 | 多处 | `assert "MINIMAX_API_KEY" not in src` — 检查边界的否定断言 |
| `monkeypatch.delenv` | 多处 | 测试中**移除**而非**读取**环境变量 |
| 文档说明命中 | 多处 | 文档中引用这些名称作为"禁止使用"的示例 |

**结论：无真实 API key 风险。**

---

## 7. 用户端字段泄露检查

### 7.1 用户端 schema（bootstrap / suggestions / letters）

`VoicePresetItem`（bootstrap 返回）不含 `coreProfileId`：
- 字段：`id`, `label`, `desc`, `genderStyle`, `suitableRecipients`, `recommendedScenes`, `defaultTone`, `enabled`
- ✅ 无 `coreProfileId`, `provider_voice_id`, `binding_id`, `params_json`, `api_key`

smoke test `test_bootstrap_no_forbidden_fields` 和 `test_bootstrap_no_core_profile_id_in_user_data` 自动验证。

### 7.2 Admin schema

`AdminVoiceMappingItem` 包含 `coreProfileId` / `providerPolicy` / `renderOverrides` — **管理端合理暴露**，Admin API 仅用于配置管理，非用户端。

### 7.3 H5 静态文件

```
grep coreProfileId/provider_voice_id/binding_id/params_json apps/xiangta-h5/ → 无命中
```

✅ H5 `app.js` 不含任何底层 Core/Provider 字段。

---

## 8. H5 静态安全检查

| 检查项 | 结果 |
|---|---|
| 外部 CDN 引用（jsdelivr / unpkg / cdnjs 等） | ✅ 无 |
| API key（MINIMAX_API_KEY 等） | ✅ 无 |
| Provider/Core 底层字段 | ✅ 无 |
| `API_BASE` 值 | `""` （相对路径，无硬编码 host）|
| XSS 防护 | `escHtml()` 全局使用 |

---

## 9. 测试结果

### XiangTa Scoped

```
python -m pytest tests/xiangta/test_mvp_smoke_flow.py -q     → 30 passed
python -m pytest tests/xiangta/test_h5_static_contract.py -q  → 40 passed
python -m pytest tests/xiangta -q                             → 512 passed
```

### Full Suite

```
python -m pytest -q  →  56 failed, 2242 passed, 7 skipped, 1 warning, 1 error in 308s
```

失败列表（全部为预存在非 XiangTa 问题）：

| 失败模块 | 说明 | 与本次改动相关？ |
|---|---|---|
| `tests/test_voice_preview.py` | Voice Lab Core provider 测试 | **否** |
| `tests/test_workspace_restore_static.py` | 工作区恢复测试 | **否** |
| `tests/test_xiaomi_mimo_call_log.py` | MiMo call log 测试 | **否** |
| `tests/e2e/test_frontend_capabilities.py` | 前端 E2E（clone mock） | **否** |

这些失败在 p17 分支的早期 commit 前就已存在，不是本次 XiangTa 改动引入的。

---

## 10. MVP 已知限制

以下限制是已知的、有意识的 MVP 边界：

1. **`/tts` 默认路径**：`VoiceLabGateway` 无 `http_client` 注入，返回稳定 `400 no_provider`。完整 `audioUrl` 由 in-process mock integration 测试验证（`test_xiangta_tts_core_mock_integration.py`）。不生成真实音频。
2. **`/suggestions` 模板版**：`CopywritingService` 使用静态模板表（5 scene × 3 style），不调用真实 LLM。
3. **`/letters` 进程内内存**：`_LETTERS` 列表为模块级变量，进程重启丢失，多 worker 不共享，不适合生产。
4. **Admin 配置写入**：JSON 文件 + `threading.Lock`，只承诺单进程写安全，uvicorn 多 worker 下无跨进程互斥。
5. **H5 静态同源要求**：需要同源后端或反向代理 `/api/xiangta/*`，当前无生产部署配置（Nginx/Caddy/Docker Compose）。
6. **无用户系统 / 鉴权 / 权限管理**：所有接口无认证，单用户本地开发假设。
7. **无真实并发队列**：TTS 无异步任务队列、用户限流、取消、重试、状态轮询。

---

## 11. Open Gaps

从 MVP Closeout Report 继承（详见 `MVP_CLOSEOUT_REPORT.md §9`）：

| Gap ID | 问题 | 优先级 |
|---|---|---|
| GAP-MVP-001 | Letters 进程内内存，重启丢失 | 合并后新阶段处理 |
| GAP-MVP-002 | Admin 配置写入单进程 Lock，多 worker 不安全 | 合并后新阶段处理 |
| GAP-MVP-003 | TTS 无任务队列 / 限流 / 重试 | 合并后新阶段处理 |
| GAP-MVP-004 | 真实 Provider / LLM 未接入 | 合并后新阶段处理，不得在本次合并后直接接入 |
| GAP-MVP-005 | H5 无生产部署配置 | 合并后新阶段处理 |
| GAP-MVP-006 | coreProfileId 存在性校验未接 Core profiles API | 合并后处理 |
| GAP-MVP-007 | Admin errorKind 命名与 B4-2 文档尚未完全统一 | 低优先级 |
| GAP-MVP-008 | ConfigWriter 枚举值校验偏弱 | 低优先级 |

---

## 12. 合并 dev 建议

**建议进入 `P17-XIANGTA-MERGE-DEV-EXECUTE`**，并带以下注意事项：

1. **确认全仓 56 个预存在失败不阻塞合并**：这些失败与 XiangTa 无关，合并前需人工确认 dev 分支在合并前是否已有这些失败（若已有，则属于已知问题）。
2. **合并后不得直接进入真实 Provider 接入**：真实 Provider / LLM 接入必须作为新的独立阶段，在 dev 合并后单独规划。
3. **告知接手者 MVP 限制**：TTS / letters / suggestions 的真实路径局限需在合并 PR 描述中明确标注。

---

## 13. 合并前人工确认清单

```markdown
- [ ] 确认 dev 分支当前已有 56 个预存在失败（不是本次引入）
- [ ] 确认 src/xiangta/**，apps/xiangta-h5/** 无真实 API key
- [ ] 确认 src/xiangta/configs/*.json 无真实 provider_voice_id / params_json
- [ ] 确认 .env / .env.* 不含 XiangTa 专用密钥
- [ ] 确认 app/（Voice Lab Core）无被动修改
- [ ] 确认 512 tests/xiangta 全绿
- [ ] 理解并接受 MVP 限制（TTS no_provider / letters 内存 / suggestions 模板）
- [ ] 合并后第一个 task = P17-XIANGTA-MERGE-DEV-EXECUTE，不得直接进入真实 Provider 接入
```
