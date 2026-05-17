# XiangTa MVP Closeout Report

**任务**：P17-XIANGTA-MVP-CLOSEOUT-B7  
**日期**：2026-05-18  
**分支**：`p17/xiangta-product-init`  
**基线 HEAD**：`98bcf73`

> **B8-1 补充（2026-05-18）**：P17-XIANGTA-RUNTIME-B8-1 新增 `apps/xiangta_runtime/main.py`，提供统一本地运行入口，同源挂载 H5（`/h5`）和 `/api/xiangta/*`。scoped tests 530/530 通过。`/tts` 默认 no_provider 仍是 MVP 边界。

---

## 1. Closeout 结论

**结论：MVP 主流程闭环，可以准备 `P17-XIANGTA-MERGE-DEV-REVIEW` 合并审查。**

- 产品端所有核心 API（bootstrap / suggestions / tts / letters）均已实现，默认路径下可稳定返回 HTTP 响应（无未捕获异常）。
- Admin 配置读写 API 全部就绪。
- H5 静态前端主流程完整，基于设计稿 `design_h5/想他了点击版本/` 实现。
- 真实 LLM 和真实 Provider 尚未接入，当前为 template / dry-run / mock path，不建议直接进入真实 Provider 接入，应先完成 dev 合并审查。

---

## 2. 当前分支与提交

| 项 | 值 |
|---|---|
| 分支 | `p17/xiangta-product-init` |
| closeout 基线 HEAD | `98bcf73` |
| 最近提交（按时间倒序） | `98bcf73` P17-XIANGTA-H5-B7-1-FIX1 |
| | `3eaed1b` P17-XIANGTA-H5-B7-1 |
| | `43b39f0` P17-XIANGTA-LETTERS-B6-1 |
| | `49f68a2` P17-XIANGTA-COPYWRITING-B5-1 |
| | `de99146` P17-XIANGTA-ADMIN-CONFIG-B4-3 |
| origin 同步 | HEAD = origin HEAD（clean） |

---

## 3. MVP 能力清单

### 3.1 产品端 API

| 接口 | 状态 | 默认路径 | 备注 |
|---|---|---|---|
| `GET /api/xiangta/bootstrap` | ✅ 完成 | 默认可用 | 读取 JSON 配置；providerStatus 默认 `not_integrated` |
| `POST /api/xiangta/suggestions` | ✅ 完成 | 默认可用 | 模板版，不调用真实 LLM |
| `POST /api/xiangta/tts` | ✅ 完成 | 返回稳定 400 | 默认无 Core http_client；mock integration 路径有完整 in-process 测试 |
| `POST /api/xiangta/letters` | ✅ 完成 | 默认可用 | 进程内内存存储，重启丢失 |
| `GET /api/xiangta/letters` | ✅ 完成 | 默认可用 | 进程内内存存储 |
| `GET /api/xiangta/provider/status` | ✅ 完成 | 默认可用 | 无 http_client 时返回 `not_integrated` |

### 3.2 Admin 配置 API

| 接口 | 状态 | 备注 |
|---|---|---|
| `GET /api/xiangta/admin/config` | ✅ 完成 | 只读汇总 |
| `GET /api/xiangta/admin/voice-mappings` | ✅ 完成 | 只读 |
| `GET /api/xiangta/admin/tone-presets` | ✅ 完成 | 只读 |
| `PUT /api/xiangta/admin/voice-mappings/{id}` | ✅ 完成 | 原子写，threading.Lock |
| `PATCH /api/xiangta/admin/voice-mappings/{id}/enabled` | ✅ 完成 | |
| `PUT /api/xiangta/admin/tone-presets/{id}` | ✅ 完成 | |
| `PATCH /api/xiangta/admin/tone-presets/{id}/enabled` | ✅ 完成 | |

### 3.3 H5 前端

| 能力 | 状态 | 备注 |
|---|---|---|
| bootstrap 加载 | ✅ 完成 | `GET /api/xiangta/bootstrap` |
| 文案建议生成 | ✅ 完成 | `POST /api/xiangta/suggestions` |
| 语音生成 | ✅ 完成（UI 层） | `POST /api/xiangta/tts`；默认路径返回错误，UI 处理降级 |
| 保存信笺 | ✅ 完成 | `POST /api/xiangta/letters` |
| 历史记录 | ✅ 完成 | `GET /api/xiangta/letters` |
| 设计来源文档 | ✅ 完成 | `DESIGN_REFERENCE.md` 引用 `design_h5/想他了点击版本/` |
| 本地预览服务 | ✅ 完成 | `apps/xiangta-h5/serve.py` |
| 无外部 CDN | ✅ 完成 | 无 npm/构建工具/外部依赖 |

### 3.4 测试覆盖

| 测试文件 | 测试数 | 说明 |
|---|---|---|
| `test_bootstrap_api.py` | — | bootstrap / provider/status 集成测试 |
| `test_boundary_contract.py` | — | 架构边界契约（不 import app.*、不读 API key 等） |
| `test_core_render_mock_integration.py` | — | Core render mock integration |
| `test_voice_lab_gateway_contract.py` | — | VoiceLabGateway TTS / status 合约 |
| `test_xiangta_status_core_mock_integration.py` | — | ProviderStatus Core mock integration |
| `test_xiangta_tts_core_mock_integration.py` | — | TTS Core mock integration（app-level） |
| `test_h5_static_contract.py` | 40 | H5 静态文件契约 |
| `test_mvp_smoke_flow.py` | 30 | MVP smoke（新增，本次 closeout） |
| **全套合计** | **512** | 全部通过 |

---

## 4. 核心用户流程

### 4.1 bootstrap

1. `GET /api/xiangta/bootstrap`
2. 读取 `voice_mappings.json` / `tone_presets.json` / `scene_config.json`
3. 组装 `recipients / scenes / styles / voicePresets / tonePresets / limits / providerStatus`
4. 默认 providerStatus.kind = `not_integrated`（无 Core http_client）
5. voicePresets 不暴露 `coreProfileId`

### 4.2 suggestions

1. `POST /api/xiangta/suggestions` with `{ recipient, scene, rawText }`
2. `CopywritingService.generate_suggestions()` 通过静态模板表返回 3 条建议（restrained / gentle / sincere）
3. **不调用 LLM**，模板覆盖 5 scene × 3 style = 15 条目

### 4.3 tts

1. `POST /api/xiangta/tts` with `{ text, voicePreset, tone, recipient, scene }`
2. `TtsOrchestrator` → `VoiceLabGateway.generate_tts()`
3. **默认路径**：`VoiceLabGateway` 无 `http_client`，抛出 `CoreRenderUnavailableError` → 转换为 `NoProviderError` → 路由返回 `400 {"ok":false, "errorKind":"no_provider", "retryable":true}`
4. **in-process Core mock 路径**（仅测试注入）：注入 fake Core http_client，可完整返回 `audioUrl`

### 4.4 letters/history

1. `POST /api/xiangta/letters` → 进程内 `_LETTERS` 列表追加，返回 `letterId`
2. `GET /api/xiangta/letters` → 倒序返回，支持 limit/offset
3. **内存存储，进程重启丢失，多 worker 不共享**

### 4.5 H5 flow

1. 打开 `apps/xiangta-h5/index.html`
2. `loadBootstrap()` 自动填充 recipient / scene / voicePreset / tone 选项
3. 用户选参数 → 填 rawText → `generateSuggestions()` → 展示 3 条建议
4. 点击建议 → `selectSuggestion()` → 自动填充 finalText
5. `generateTts()` → 展示 taskId / status / 降级消息
6. `saveLetter()` → `loadLetters()` → 展示历史列表
7. H5 需同源后端或反向代理 `/api/xiangta/*`；本地可用 `serve.py`

---

## 5. Mock / Dry-run / 默认路径说明

| 能力 | 默认路径 | 测试注入路径 |
|---|---|---|
| `/suggestions` | 模板版，直接可用，不调用 LLM | — |
| `/tts` | `VoiceLabGateway` 无 http_client → 稳定 400 no_provider | 注入 fake Core http_client → 完整 audioUrl；已有 app-level mock integration 测试验证 |
| `/letters` | 进程内内存，直接可用 | — |
| `bootstrap.providerStatus` | `not_integrated`（默认） | 注入 fake gateway 可返回 `ok`；已有 Core mock integration 测试 |

**重要**：`/tts` 默认路径 **不** 生成真实音频，返回 400 no_provider。生产可用需注入 Core http_client。

---

## 6. 不接真实 Provider / LLM 声明

本 MVP 全程不接触真实 Provider 或 LLM：

- 无真实 MiniMax API key 读取
- 无真实 MiMo API key 读取
- 无真实 OpenAI API key 读取
- `CopywritingService` 使用静态模板，不调用 `generate_llm_text()`
- `TtsOrchestrator` 默认走稳定降级路径，不调用真实 Provider adapter
- H5 静态文件不含任何 API key 或 provider 参数
- 所有测试中的 API key 相关操作均为 `monkeypatch.delenv`（删除而非读取）

---

## 7. 安全边界

### 7.1 API key

- 源码 `src/xiangta/**` 不读取 `MINIMAX_API_KEY` / `MIMO_API_KEY` / `OPENAI_API_KEY`
- H5 `app.js` 不含任何 API key 字符串（`test_h5_static_contract.py` 强制验证）
- 测试文件中仅通过 `monkeypatch.delenv` 移除环境变量

### 7.2 Provider/Core 字段泄露

- 用户端响应（`/bootstrap` / `/suggestions` / `/letters`）不暴露：
  `api_key`, `provider_voice_id`, `binding_id`, `params_json`, `model_id`, `voice_id`, `stack_trace`, `core_profile_id`
- `/bootstrap.voicePresets` 不含 `coreProfileId`
- Admin API 可返回 `coreProfileId` / `providerPolicy` / `renderOverrides`（管理端合理）

### 7.3 app/src.voice_lab 保护

- XiangTa 不直接 import `app.repositories.*` / `app.providers.*`
- XiangTa 不调用 `get_provider()` / `adapter.render_sync()` / 构造 `RenderPlan`
- `VoiceLabGateway` 是唯一 Core 边界，boundary contract 测试强制验证（512 tests）

### 7.4 H5 静态安全

- 无外部 CDN 引用（`cdn.jsdelivr.net` 等均禁止）
- `escHtml()` 函数防止 XSS（所有动态内容注入前转义）
- `API_BASE = ""`（相对路径，无硬编码 host）

---

## 8. MVP 限制

以下限制是已知的、有意识的 MVP 边界，不是 bug：

1. **TTS 默认路径不生产音频**：需注入 Core http_client 或后续真实 Provider 接入阶段处理
2. **Letters 进程内存储**：重启丢失，多 worker 不共享，不适合生产
3. **单进程 JSON 配置写入**：`threading.Lock` 只保证单进程写安全
4. **suggestions 为模板版**：风格固定，未来需接 LLM 实现个性化
5. **H5 需同源后端**：无生产 Nginx/Caddy/反向代理配置
6. **无用户鉴权**：所有接口无认证，单用户本地开发假设
7. **无真实并发队列**：TTS 无任务队列、用户限流、取消、重试、状态轮询

---

## 9. Open Gaps

| Gap ID | 问题 | 当前影响 | 后续建议 |
|---|---|---|---|
| GAP-MVP-001 | Letters 当前为进程内内存存储，重启丢失，多 worker 不共享 | POST→GET 在单进程内可用，多 worker 部署会丢数据 | DB 化（SQLite/PostgreSQL） |
| GAP-MVP-002 | Admin 配置写入仅单进程 `threading.Lock`，uvicorn 多 worker 下不保证跨进程互斥 | 多 worker 并发写可能导致文件竞争 | DB 化或分布式锁 |
| GAP-MVP-003 | TTS 产品层暂无任务队列、用户限流、取消、重试、状态查询 | 长时请求无法异步轮询、无限流保护 | 引入异步任务队列（如 Celery/ARQ） |
| GAP-MVP-004 | 真实 Provider / LLM 未接入，当前仍是 mock/template 路径 | TTS 默认路径返回 400，suggestions 无个性化 | 真实 Provider 接入作为新阶段处理 |
| GAP-MVP-005 | H5 静态页面需同源后端或反向代理 `/api/xiangta/*`，当前没有生产部署配置 | 本地开发需手动配置代理 | 补充 Nginx/Caddy 配置或 Docker Compose |
| GAP-MVP-006 | Core profileId 正式存在性校验未接 Core profiles public API | B4-3 仅做格式校验（空串/占位符检测），不验证 profileId 是否真实存在 | VoiceLabGateway.get_voice_profiles() 接 Core 校验（B4-4） |
| GAP-MVP-007 | Admin write errorKind 与 B4-2 文档的命名尚未完全统一 | errorKind 偶有 `write_failed` vs 文档期望值不一致 | 后续 Admin API 版本对齐 |
| GAP-MVP-008 | ProductConfigWriter 对 suitableRecipients / recommendedScenes / defaultTone 的存在性校验仍偏弱 | 可写入未在枚举中定义的值 | 引入枚举校验 |

历史 GAP（B2/B4 阶段登记，参考 NEXT_TASKS.md）：
- GAP-B2-001 ~ GAP-B2-004：Core render 路径 profileId、provider 强制、in-process facade、seed_defaults 问题
- GAP-B4-001 ~ GAP-B4-003：配置写入原子性、coreProfileId 校验、tone_presets 字段补全

---

## 10. 合并 dev 前建议

**建议进入 `P17-XIANGTA-MERGE-DEV-REVIEW`（合并 dev 前审查）**，不建议直接进入真实 Provider 接入。

合并前人工检查清单：

- [ ] 确认 `src/xiangta/**` 无真实 API key / Provider adapter 引用
- [ ] 确认 `apps/xiangta-h5/app.js` 无敏感字段
- [ ] 确认 `src/xiangta/configs/*.json` 无真实 provider_voice_id / params_json
- [ ] 确认 `.env` / `.env.*` 不含 XiangTa 专用密钥
- [ ] 512 tests 全绿
- [ ] 确认无 DB schema 变更（当前无 DB，无需 migration）
- [ ] 确认 `app/` Core 主链路无被动修改

真实 Provider 接入应作为新阶段（`P17-XIANGTA-A3` 或后续命名），在 dev 合并审查通过后启动。

---

## 11. 验收命令记录

```bash
# MVP smoke flow
python -m pytest tests/xiangta/test_mvp_smoke_flow.py -q
# 30 passed

# H5 静态契约
python -m pytest tests/xiangta/test_h5_static_contract.py -q
# 40 passed

# 全套 XiangTa 测试
python -m pytest tests/xiangta -q
# 512 passed

# 保护检查（无禁止文件修改）
git diff --name-only
# 只出现 docs/xiangta/ tests/xiangta/ docs/agent/ 文件

# 安全边界扫描（仅文档/测试断言，无真实密钥）
grep -R "MINIMAX_API_KEY\|get_provider(\|RenderPlan" docs/xiangta tests/xiangta docs/agent
# 全部为文档引用或测试中的 assert-not-contains 断言
```
