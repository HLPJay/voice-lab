# Next Tasks

## 当前阶段

**P17 已合并到 dev ✅ → 当前阶段：P18-XIANGTA-PRODUCT-API**

`docs/xiangta/**` 是 XiangTa 后续产品构建的权威设计文档目录。`docs/product/XIANGTA_*.md` 与 A0-A2 保留为历史阶段记录，不再作为后续实现的主依据。

## 下一步（P17 阶段路线图）

| 任务 | 内容 | 状态 |
|---|---|---|
| P17-XIANGTA-INIT-A0 | Core Freeze 声明 + 骨架初始化 | ✅ |
| P17-XIANGTA-INIT-A0-FIX1 | 清理产品层底层参数泄露，修正 voicePreset/Core 边界 | ✅ |
| P17-XIANGTA-A1 | 配置协议 + bootstrap/status 只读接口，不接真实 TTS | ✅ |
| P17-XIANGTA-A1-FIX1 | 抽离配置加载（config/loader.py）与 Bootstrap 组装（BootstrapService），消除 product_service.py 责任膨胀 | ✅ |
| P17-XIANGTA-A2 | TtsOrchestrator + VoiceLabGateway dry-run 合约 | ✅ |
| P17-XIANGTA-DOCS-FIX1 | 修正 docs/xiangta 路径、示例值和 XiangTa→Core 调用边界 | ✅ |
| P17-XIANGTA-PRODUCT-CONFIG-B1 | 产品配置模型落地总阶段 | ✅ |
| P17-XIANGTA-PRODUCT-CONFIG-B1-1 | ProductConfigRepository 与产品配置模型基础落地 | ✅ |
| P17-XIANGTA-PRODUCT-CONFIG-B1-2 | BootstrapService 接入 ProductConfigRepository | ✅ |
| P17-XIANGTA-PRODUCT-CONFIG-B1-3 | VoicePresetMappingService / TonePresetService 接入 ProductConfigRepository | ✅ |
| P17-XIANGTA-PRODUCT-CONFIG-B1-4 | ProviderStatus / limits / tone 配置读取边界收口 | ✅ |
| P17-XIANGTA-CORE-RENDER-B2-A0 | Core render 接入前置审查与 mock 策略确认 | ✅ |
| P17-XIANGTA-CORE-RENDER-B2-B1a | VoiceLabGateway 接 Core render HTTP contract mock path | ✅ |
| P17-XIANGTA-CORE-RENDER-B2-B1b | TtsOrchestrator 切到 VoiceLabGateway.generate_tts() | ✅ |
| P17-XIANGTA-CORE-RENDER-B2-B2 | Core render mock integration test | ✅ |
| P17-XIANGTA-CORE-RENDER-B2-B3 | XiangTa app-level Core mock integration test | ✅ |
| P17-XIANGTA-PROVIDER-STATUS-B3 | ProviderStatus runtime/status mock path | ✅ |
| P17-XIANGTA-ADMIN-CONFIG-B4-1 | 配置管理只读 API | ✅ |
| P17-XIANGTA-ADMIN-CONFIG-B4-2 | 配置管理写接口设计与安全边界 | ✅ |
| P17-XIANGTA-ADMIN-CONFIG-B4-3 | 配置管理写接口最小实现 | ✅ |
| P17-XIANGTA-COPYWRITING-B5-1 | CopywritingService 模板文案建议 | ✅ |
| P17-XIANGTA-LETTERS-B6-1 | letters/history 进程内内存闭环 | ✅ |
| P17-XIANGTA-H5-B7-1 | H5 静态前端主流程 | ✅ |
| P17-XIANGTA-H5-B7-1-FIX1 | serve.py 迁移 + DESIGN_REFERENCE.md | ✅ |
| P17-XIANGTA-MVP-CLOSEOUT-B7 | MVP closeout，512 tests 全绿 | ✅ |
| P17-XIANGTA-MERGE-DEV-REVIEW | 合并前代码审查，PASS_WITH_NOTES | ✅ |
| P17-XIANGTA-RUNTIME-B8-1 | apps/xiangta_runtime/main.py，530 tests 全绿 | ✅ |
| P17-XIANGTA-CORE-AUDIO-LINK-B9 | Core HTTP API 链路打通，583 tests 全绿 | ✅ |
| P17-XIANGTA-CORE-AUDIO-LINK-B9-FIX1 | H5 渲染修复 + tone 异常转换 | ✅ |
| P17-XIANGTA-CORE-AUDIO-LINK-B9-FIX2 | Core HTTP URL 重复拼接修复 | ✅ |
| P17-XIANGTA-CORE-AUDIO-LINK-B9-FIX3 | Core audioUrl 绝对路径修复 | ✅ |
| P17-XIANGTA-ARCHITECTURE-SYNC-B9-DOCFIX | B9 文档固化与架构同步 | ✅ |
| P17-XIANGTA-BACKEND-CAPABILITY-PLAN-C1 | 产品后端能力路线图：配置/存储/队列/LLM/安全/错误/观测/用户 | ✅ |
| P17-XIANGTA-RUNTIME-CONFIG-C2 | Runtime Config 设计 + 实现（runtime.json + env override） | ✅ |
| P17-XIANGTA-CODE-AUDIT-C2A | 只读代码审查：边界/可维护性/安全/配置/错误/并发/存储/H5/测试覆盖 | ✅ |
| P17-XIANGTA-CODE-CLEANUP-C2B | 小步清理：异常字符串匹配/docstring/dataclass位置/runtime警告日志 | ✅ |
| P17-XIANGTA-STORAGE-DESIGN-C3 | Storage 设计（SQLite schema + migration） | ✅ |
| P17-XIANGTA-TTS-TASK-ORCHESTRATION-DESIGN-C4 | 异步 TTS task 设计（async API + queue strategy） | ✅ |
| P17-XIANGTA-COPYWRITING-LLM-DESIGN-C5 | LLM Copywriting 设计（gateway + fallback + security） | ✅ |
| P17-XIANGTA-BACKEND-ERROR-CONTRACT-C6 | Error Contract 设计（统一错误 schema + errorKind 枚举） | ✅ |
| P17-XIANGTA-PROFILE-MAPPING-DESIGN-C7 | voicePreset → coreProfileId 映射产品化设计 | ✅ |
| P17-XIANGTA-H5-DESIGN-ALIGNMENT-C8 | H5 设计对齐（适配新 API 契约） | ✅ |
| P17-XIANGTA-MERGE-DEV-EXECUTE | 执行 merge p17/xiangta-product-init → dev | ✅ |
| P17-XIANGTA-A3 | 历史占位：真实 LLM 接入 | Parked |
| P17-XIANGTA-A5 | 前端工程化与主路径联调 | Parked |

## P18 XiangTa Product API Implementation

P18 目标：在不修改 Core 的前提下，把 P17 的设计逐步落地为产品主路径 API。  
优先顺序：先 voicePreset 产品 API，再 mapping hardening，再 Admin gate，再 Error Contract，再 Storage / TTS Task / H5。

| 任务 | 内容 | 推荐执行工具 | 状态 |
|---|---|---|---|
| P18-XIANGTA-POST-MERGE-DOCFIX-C0 | P17 merge 后 NEXT_TASKS 收口，建立 P18 路线图 | MiniMax / Codex | ✅ |
| P18-XIANGTA-VOICE-PRESETS-API-C1 | 新增 GET /api/xiangta/voice-presets，普通 H5 只看到产品声线字段 | Codex / Claude Code Sonnet | Next |
| P18-XIANGTA-VOICE-PRESET-RESOLUTION-C2 | 强化 voicePreset → coreProfileId 解析，处理占位符/disabled/profile_not_found | Codex | Planned |
| P18-XIANGTA-ADMIN-GATE-C3 | Admin dev-only gate / token gate 最小实现 | Codex | Planned |
| P18-XIANGTA-ERROR-CONTRACT-MIN-C4 | 最小 Error Contract 实现，兼容 flat/nested error | Codex | Planned |
| P18-XIANGTA-H5-DEV-FORMAL-MODE-C5 | H5 formal/dev 模式最小适配，coreProfileSelect 进入 Dev Panel | Claude Code Sonnet | Planned |
| P18-XIANGTA-STORAGE-FOUNDATION-C6 | SQLite storage foundation：migration + repository 基础 | Codex / Claude Code | Planned |
| P18-XIANGTA-TTS-TASK-MVP-C7 | TTS task MVP：POST /tts/tasks + GET task + in-memory queue | Claude Code Opus / Codex | Planned |
| P18-XIANGTA-COPYWRITING-LLM-MVP-C8 | LLM Copywriting Gateway MVP，template fallback 保留 | Codex | Planned |
| P18-XIANGTA-H5-PRODUCT-FLOW-C9 | H5 正式产品流实现，对齐 C8 设计稿 | Claude Code | Planned |

**C2A 遗留未处理**：CA-06（H5 防重复点击）deferred to C8；CA-01（Admin 鉴权）deferred to C6 or security task；CA-04（CoreHttpClient 错误上下文）deferred to C6；CA-02（ProductService 私有字段访问）deferred to C2B 后续或 C3。

## 本阶段约束

**先后端能力设计，再前端独立优化。不要直接进入 H5 实现。不要直接接 LLM。不要直接做用户系统。**

- C1（Backend Capability Plan）已完成
- C2-C8 为设计 + 实现的混合阶段
- C9+ 才开始 Storage 实现
- 不修改 Core
- 不实现 Redis / Celery（第一阶段）
- 不实现多用户（user_id 设计预留）

## P18 阶段约束

- 不修改 Core：不得修改 `app/**`、`src/voice_lab/**`
- 不直接接真实 LLM，LLM 接入必须等 P18-C8
- 不直接实现 TTS queue，TTS task 必须等 P18-C7
- 不直接重构 H5，H5 正式实现必须等 P18-C9
- 不引入 Redis / Celery
- 不引入用户系统
- 不直接公网暴露 Admin API
- 优先小步实现产品主路径 API
- 每个实现任务必须有 tests/xiangta 覆盖

## P18 当前已知问题

- `voice_mappings.json` 中 `coreProfileId` 仍为 `<core_profile_id_from_core_profiles>` 占位符；正式 voicePreset 路径尚不能直接用于真实生成。
- 当前 H5 仍是 B9 smoke page，正式产品页尚未实现。
- 当前 TTS 仍是同步 `/api/xiangta/tts`，异步 `/tts/tasks` 未实现。
- 当前 letters 仍为进程内内存存储，SQLite 未实现。
- 当前 Admin API 尚无 gate，仅适合本地开发。
- full-suite 仍存在 Xiaomi MiMo / frontend E2E 历史失败；`tests/xiangta` 是 P18 scoped regression 标准。

## Core Contract Gap 登记区

> 此处登记在产品开发中发现的 voice_lab Core 能力缺口。
> 格式：`[ ] GAP-XXX: <描述> — 发现于 P17-XIANGTA-XXXX`
> 不得直接修改 src/voice_lab/* 解决，需独立 Core 修复任务。

- [ ] GAP-B2-001: XiangTa `voice_mappings` 仍使用 `<core_profile_id_from_core_profiles>` 占位；B2-B1 测试前需在 fixture / fake repository 中指向真实 Core profile（发现于 `P17-XIANGTA-CORE-RENDER-B2-A0`）
- [ ] GAP-B2-002: 若 XiangTa 在 B2-B1 中未显式传 `provider="mock"`，Core render 会回落到默认 `settings.voice_provider=minimax`；B2-B1 必须强制 mock provider（发现于 `P17-XIANGTA-CORE-RENDER-B2-A0`）
- [ ] GAP-B2-003: 当前 Core 没有与 `POST /api/voice/render` 完全等价的进程内 high-level facade；B2-B1 优先走 HTTP API，若未来要走进程内需先补 facade（发现于 `P17-XIANGTA-CORE-RENDER-B2-A0`）
- [ ] GAP-B2-004: `seed_defaults()` 虽创建 mock binding，但未同时 seed `ProviderVoice`；B2-B1 测试需复用 `seed_mock_binding` 或显式补建 provider voice（发现于 `P17-XIANGTA-CORE-RENDER-B2-A0`）

> 备注：B2-B3 测试路径已通过 fake repository 将 `voicePreset -> deep_night_programmer`，并显式断言 `provider="mock"`。
> 正式产品配置仍需在后续 Admin / 配置治理阶段消化 GAP-B2-001 与 GAP-B2-002。

- [ ] GAP-B4-001: 当前配置存储仍为 JSON 文件，写接口需要原子写 / 备份 / 并发锁；MVP 阶段用 threading.Lock + atomic rename，多人并发需评估 DB 化（发现于 `P17-XIANGTA-ADMIN-CONFIG-B4-2`）
- [ ] GAP-B4-002: coreProfileId 正式合法性校验需要 Core profiles public API / VoiceLabGateway 支持；B4-3 只做格式校验，B4-4 通过 VoiceLabGateway.get_voice_profiles() 接 Core 校验（发现于 `P17-XIANGTA-ADMIN-CONFIG-B4-2`）
- [ ] GAP-B4-003: tone_presets.json 当前不含 sort_order / render_overrides / copywriting_style 字段；B4-3 写入时应以 default 值补全，确保文件格式与模型定义一致（发现于 `P17-XIANGTA-ADMIN-CONFIG-B4-2`）

## XiangTa 下一步约束

下一步进入 `P18-XIANGTA-VOICE-PRESETS-API-C1`。P18-C1 是第一个代码实现任务，只实现 /voice-presets 产品 API，不改 H5，不改 Core，不做 DB。

B9 已就绪（`apps/xiangta_runtime/main.py` + Core HTTP client），启动命令：
```bash
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5173
```

合并审查已完成（PASS_WITH_NOTES）：
- XiangTa scoped 测试 512/512 全绿
- Core / app 无误改
- API key / Provider 无泄露
- H5 无外部 CDN / 无敏感字段
- 全仓 56 个预存在失败全部为非 XiangTa 历史问题

**合并后不得直接进入真实 Provider 接入**。真实 Provider / LLM 接入应在 dev 合并后作为独立新阶段处理。

审查报告：`docs/xiangta/MERGE_DEV_REVIEW.md`  
MVP closeout 报告：`docs/xiangta/MVP_CLOSEOUT_REPORT.md`

## P16 已完成历史

## 当前 Closeout 范围

- 不再将 D4-F4、D4-F5、D4-F6P 视为待办，它们已完成
- 当前仍保留的豁免项：jsdom 环境依赖、Playwright E2E locator 过期、full-suite ordering pollution、full-suite env/API key 隔离问题
- 合并前关注点：人工验收、scoped regression、secret 暴露检查、数据库 schema 变更说明检查
- Xiaomi MiMo 当前作为可选 Provider 保持打开；默认 Provider 仍为 MiniMax，closeout 阶段仅禁止未授权 real-call / probe

## 已完成（续）

- P16-XIAOMI-MIMO-TTS-REAL-PROBE-B1：执行小米 MiMo 真实 API 最小探测 ✅
- P16-XIAOMI-MIMO-TTS-REAL-PROBE-B2：真实 API 探测执行（用户手动执行成功） ✅
- P16-XIAOMI-MIMO-TTS-ADAPTER-TEST-TRIAGE-C0：adapter 测试失败排查 ✅
- P16-XIAOMI-MIMO-TTS-CONFIG-AND-DUPLICATE-TRIAGE-D1：配置审查与重复 banner 修复 ✅
- P16-XIAOMI-MIMO-TTS-REAL-PROBE-A0：小米 MiMo 真实 API 最小探测方案 ✅
- P16-XIAOMI-MIMO-TTS-B1-CHECK：验证 Xiaomi MiMo Chat TTS 最小实现 ✅
- P16-XIAOMI-MIMO-TTS-B1-CHECK-FIX1：修复 Xiaomi MiMo 配置化边界问题 ✅
- P16-XIAOMI-MIMO-TTS-B1：实现 Xiaomi MiMo Chat TTS 最小可行路径 ✅
- P16-ADAPTER-PLUGIN-DISCOVERY-B1-CHECK-FIX1：修复 Adapter 插件发现主路径与错误处理 ✅
- P16-ADAPTER-PLUGIN-DISCOVERY-B1：Adapter 插件发现与配置化注册 ✅
- P16-XIAOMI-MIMO-TTS-A0：小米 MiMo speech-synthesis-v2.5 接入前置审查 ✅
- P16-ADAPTER-PLUGIN-CONFIG-B1-CLOSE：AdapterConfig 与插件配置加载阶段收口 ✅
- P16-ADAPTER-PLUGIN-CONFIG-B1-CHECK-FIX1：修复 AdapterConfig 与 capability 合成边界 ✅
- P16-ADAPTER-PLUGIN-CONFIG-B1：实现 AdapterConfig 与 Adapter 插件配置加载 ✅
- P16-ADAPTER-PLUGIN-CONFIG-A0：Adapter 插件化与配置分层设计 ✅
- P16-DYNAMIC-PROVIDER-CONFIG-B1-CLOSE：Provider 配置化接入阶段收口 ✅
- P16-DYNAMIC-PROVIDER-CONFIG-B1-CHECK：Provider 配置化接入实现复核 ✅
- P16-DYNAMIC-PROVIDER-CONFIG-B1：Provider 配置化接入实现 ✅
- P16-DYNAMIC-PROVIDER-CONFIG-A0：Provider 配置化接入架构设计 ✅
- P16-PROVIDER-BINDING-UI-B2-OBS-FIX1-CLOSE：Provider-first UI 观察项修复阶段收口 ✅
- P16-PROVIDER-BINDING-UI-B2-OBS-FIX1-CHECK：验证 Provider-first UI 观察项修复 ✅
- P16-PROVIDER-BINDING-UI-B2-OBS-FIX1：修复 Provider-first UI 观察项 ✅
- NEXT-PRIORITY-REVIEW：选择 Provider-first UI 观察项修复 ✅
- P16-PROVIDER-BINDING-UI-B2-CLOSE：Provider-first profile/binding UI 阶段收口 ✅
- P16-PROVIDER-BINDING-UI-B2-CHECK：验证 Provider-first profile/binding UI ✅
- P16-PROVIDER-BINDING-UI-B2：实现 Provider-first profile/binding UI ✅
- P16-PROVIDER-BINDING-UI-B2-A0：Provider-first profile/binding UI 设计 ✅
- NEXT-PRIORITY-REVIEW：选择 Provider-first profile/binding UI 设计 ✅
- P16-PROVIDER-MODEL-BINDING-CLOSE：Provider / Model / VoiceBinding 最小增强阶段收口 ✅
- P16-PROVIDER-MODEL-BINDING-B1-CHECK：验证最小 model/binding 可见性与恢复增强 ✅
- P16-PROVIDER-MODEL-BINDING-B1：实现最小 model/binding 可见性与恢复增强 ✅
- P16-PROVIDER-MODEL-BINDING-B1-A0：最小 model/binding 可见性与恢复增强前置设计 ✅
- P16-PROVIDER-MODEL-BINDING-A0-CHECK：Provider / Model / VoiceBinding 全链路审查复核 ✅
- P16-PROVIDER-MODEL-BINDING-A0：Provider / Model / VoiceBinding 全链路审查 ✅
- NEXT-PRIORITY-REVIEW：选择 Provider / Model / VoiceBinding 全链路审查 ✅
- P16-PROVIDER-MOCK-FIX1-CHECK：验证 mock/provider boundary fixes ✅
- P16-PROVIDER-MOCK-FIX1：修复 mock fallback / provider binding / cost boundary ✅
- P16-PROVIDER-MOCK-CLOSE：Provider mock boundary 阶段收口 ✅
- P16-PROVIDER-BOUNDARY-A0-CHECK：Provider 边界审查复核 ✅
- P16-PROVIDER-BOUNDARY-A0：Provider / Mock / Capability / 新大模型接入边界审查 ✅
- P16-WORKSPACE-RESTORE-CLOSE：workspace 最近样本完整恢复阶段收口 ✅
- P16-WORKSPACE-RESTORE-B1-FIX1：修复 workspace restore 复核发现的问题 ✅
- P16-WORKSPACE-RESTORE-B1-CHECK：workspace context 保存与完整恢复复核 ⚠️ (发现阻塞问题，已修复)
- P16-WORKSPACE-RESTORE-B1：实现 workspace context 保存与完整恢复 ✅
- P16-CANCEL-FIX1-CHECK：取消确认语义和 loading 状态修复复核 ✅
- P16-WORKSPACE-RESTORE-A0：workspace 最近样本完整恢复方案审查 ✅
- P16-WORKSPACE-RESTORE-A0-CHECK：workspace 最近样本完整恢复方案复核 ✅

## 已完成（续）

- P16-CANCEL-FIX1：修复取消确认语义和 loading 状态 ✅
- P14-CONTEXT-C2-FIX2：修复 SampleSidebar 详情面板插入位置 ✅
- P14-CONTEXT-C2-FIX2-CHECK：SampleSidebar 详情面板插入位置修复复核 ✅
- P14-CONTEXT-C2-FIX3：修复 SampleSidebar 详情面板被 flex 压缩裁切 ✅
- P14-CONTEXT-C2-FIX3-CHECK：SampleSidebar 详情面板 flex 压缩修复复核 ✅
- P14-PRODUCT-B0-SKIP：SampleSidebar 常驻策略确认，跳过隐藏/过滤设计 ✅
- P15-STATS-A0：后期统计能力设计 ✅
- P15-STATS-A0-CHECK：后期统计能力设计复核 ✅
- P15-STATS-B1-A0：轻量本地统计面板实现前置审查 ✅
- P15-STATS-B1-PARK：统计面板实现延后，保留为后期待办 ✅
- P14-CONTEXT-C2-CLOSE：P14 context restore 闭环阶段收口 ✅
- P14-CONTEXT-C2-FIX1-CHECK：剧本恢复 Batch Script 面板切换修复复核 ✅
- P14-CONTEXT-C2-FIX1：修复剧本恢复切换到正确 Batch Script 面板 ✅
- P14-CONTEXT-C2-CHECK：剧本一键回填复核 ✅ (发现阻塞问题)
- P14-CONTEXT-C2：剧本一键回填 ✅
- P14-CONTEXT-C1-FIX1-CHECK：script detail panel HTML 结构修复复核 ✅
- P14-CONTEXT-C1-FIX1：修复 script detail panel HTML 结构 ✅
- P14-SIDEBAR-ACTIONS-B1-UXFIX1：侧边栏操作按钮平铺恢复 ✅
- P14-CONTEXT-C1-CHECK：剧本 context 保存与详情查看复核 ✅ (发现阻塞问题)
- P14-CONTEXT-C1：剧本 context 保存与详情查看实现 ✅
- P14-CONTEXT-C1-A0：剧本 context 保存与详情查看前置审查 ✅
- P14-CONTEXT-B3-CHECK：长文本一键回填复核 ✅
- P14-CONTEXT-B3：长文本一键回填 ✅
- P13-CREATION-B5-A0：batch sample_store 接入字段核验与方案设计 ✅
- P13-CREATION-B5-A0-CODE-CHECK-FIX：batch A0 文档代码事实校验修正 ✅
- P13-CREATION-B5-A0-CODE-CHECK-FIX2：batch MVP1 前置条件与 download_url 策略收紧 ✅
- P13-PRE-B5-REGRESSION-CHECK：已有功能回归自检 ✅
- P13-CREATION-B5-MVP1：batch merged audio 接入 sample_store ✅
- P13-CREATION-B5-MVP1-CHECK-FIX1：safePushBatchSample 默认参数与任务状态修正 ✅
- P13-CREATION-B5-CHECK：batch merged audio sample_store 接入复核已完成 ✅
- P13-CREATION-B5-CLOSE：batch merged audio sample_store 阶段收口 ✅
- P13-FINAL-CHECK：P13 最近样本系统最终验收 ✅
- P13-CLOSE：P13 最近样本系统阶段收口归档 ✅
- P14-PRODUCT-A0：样本复用与配置恢复产品方案审查 ✅
- P14-PRODUCT-A0-FIX1：长文本生产入口可用性方向补充 ✅
- P14-PRODUCT-A0-FIX2：文档章节编号修正 ✅
- P14-LONGTEXT-UX-B0：长文本字数 / 消耗 / 分段策略提示方案设计 ✅
- P14-LONGTEXT-UX-B0-FIX1：剧本生产入口统计提示方向补充 ✅
- P14-LONGTEXT-UX-B1：长文本字数统计、预计分段、策略说明 ✅
- P14-LONGTEXT-UX-B1-CHECK：长文本 UX hints 实现复核 ✅
- P14-LONGTEXT-UX-B1-CLOSE：长文本 UX hints 阶段收口 ✅
- P14-SCRIPT-UX-B0：剧本行数 / 字数 / 角色 / 音色完整性提示方案设计 ✅
- P14-SCRIPT-UX-B1-CHECK：剧本 UX hints 实现复核 ✅
- P14-SCRIPT-UX-B1-CLOSE：剧本 UX hints 阶段收口 ✅
- P14-CONTEXT-B0：可恢复创作上下文 ContextStore 设计 ✅
- P14-CONTEXT-B1-CHECK：context_store.js 基础模块复核 ✅
- P14-CONTEXT-B1-CHECK-FIX1：ContextStore 默认值与注释修复 ✅
- P14-CONTEXT-B1-CLOSE：context_store.js 基础模块阶段收口 ✅
- P14-CONTEXT-B2-A0：长文本 context 保存与详情查看接入前置审查 ✅
- P14-CONTEXT-B2：长文本 context 保存与详情查看实现 ✅
- P14-CONTEXT-B2-CHECK：长文本 context 保存与详情查看复核 ✅
- P14-CONTEXT-B2-CLOSE：长文本 context 保存与详情查看阶段收口 ✅
- P14-SIDEBAR-ACTIONS-A0：侧边栏按钮显示策略设计 ✅
- P14-SIDEBAR-ACTIONS-B1：侧边栏按钮分层与更多菜单实现 ✅

## 已完成

- P9-FE1：voice_clone.js、voice_import.js、voice_design.js 抽离 ✅
- P9-FE2-A0：index.html 剩余逻辑边界审查 ✅
- P10-PRODUCT-A0：产品打磨优先级审查 ✅
- P10-PRODUCT-B0：Workspace 音色快捷选择区边界审查 ✅
- P10-PRODUCT-B1：Workspace 音色快捷选择区实现 ✅
- P10-PRODUCT-B2-A0：Voices tab 快速创作联动边界审查 ✅
- P10-PRODUCT-B2：Voices tab 快速创作联动实现 ✅
- P10-PRODUCT-B3-A0：Batch tab 音色快速选择边界审查 ✅
- P10-PRODUCT-B3-longtext：Batch longtext tab 绑定音色提示实现 ✅
- P10-PRODUCT-B3-script：Batch script tab 每行动态绑定音色提示实现 ✅
- P10-PRODUCT-B4：简化 onboarding 文案 ✅
- P10-PRODUCT-B5：Advanced tab 重命名为音色工具 ✅
- P10-PRODUCT-B6：历史最近任务快捷入口实现 ✅
- P11-FE-REDUCE-A0：index.html 瘦身审查 ✅
- P11-FE-REDUCE-A1：product_hints.js 抽离 ✅
- P11-FE-REDUCE-A1-CHECK：product_hints.js 验证 ✅
- P11-FE-REDUCE-A2-A0：recent_job 模块审查（结论：不迁移） ✅
- P11-FE-REDUCE-CHECK：index.html 瘦身收口 ✅
- P12-USAGE-FIX1：workspace binding hint 与 #bindingStatus 同步修复 ✅
- P12-USAGE-UX1：compact advanced tool hints ✅
- P12-USAGE-FIX2：check initial workspace binding status ✅
- P12-USAGE-FIX3：sync batch binding hints ✅
- P12-USAGE-FIX3B：add status to bind map entries ✅
- P12-USAGE-UX2：redesign recent job entry ✅
- P12-USAGE-FIX4-A0：audit audio download failures ✅
- P12-USAGE-FIX4-B0：audit batch merged audio asset_id ✅
- P12-USAGE-FIX4：normalize batch download href ✅
- P12-USAGE-UX3：clarify async mode positioning ✅
- P12-USAGE-UX4-A0：audit advanced quick bind panels ✅
- P12-USAGE-UX4-B1：normalize advanced quick bind panel layout ✅
- P12-USAGE-FIX5-A0：audit audio duration display ✅
- P12-USAGE-FIX5-B1：extend audioPlayerHtml + batch total_duration display ✅
- P12-USAGE-FIX5-B2：normalize advanced audio duration display ✅
- P12-USAGE-UX5：clarify sentence segmentation copy ✅
- P12-USAGE-UX5-FIX：repair HTML attribute quotes ✅
- P12-USAGE-FIX6-A0：audit audio asset duration persistence ✅
- P12-USAGE-FIX6-B1：add audio duration fallback (pydub) ✅
- P12-USAGE-CHECK：close real usage polish ✅
- P12-USAGE-UX6：fix sentence segmentation semantics ✅
- P12-USAGE-CHECK2：close post-UX6 polish ✅
- P13-CREATION-A0：样本观察侧边栏设计审查 ✅
- P13-CREATION-A0-CHECK：A0 文档事实核验与修正 ✅
- P13-CREATION-B0：样本观察侧边栏最小实现方案设计 ✅
- P13-CREATION-B1：sample_store.js 前端样本存储模块实现 ✅
- P13-CREATION-B1-CHECK-FIX：sample_store 契约修正 ✅
- P13-CREATION-B1-CHECK-FIX2：sample_store 测试覆盖补强 ✅
- P13-CREATION-B2：workspace 生成结果接入 sample_store ✅
- P13-CREATION-B2-CHECK-FIX：workspace sample_store 接入修正 ✅
- P13-CREATION-B2-CHECK-FIX2：workspace sample metadata model 来源修正 ✅
- P13-CREATION-B2-CHECK：workspace sample_store 接入复核 ✅
- P13-CREATION-B3：audition_records 接入 sample_store ✅
- P13-CREATION-B3-CHECK：audition_records sample_store 接入复核 ✅
- P13-CREATION-B4：sample_sidebar.js + index.html 容器 UI 实现 ✅
- P13-CREATION-B4-CHECK-FIX：sample sidebar UI 契约修正 ✅
- P13-CREATION-B4-CHECK-FIX2：sample sidebar UI 安全与 metadata 修正 ✅
- P13-CREATION-B4-CHECK-FIX3：sample sidebar empty refresh 与 URL safety 修正 ✅
- P13-CREATION-B4-CHECK-FIX4：sample sidebar 空状态事件绑定修正 ✅
- P13-CREATION-B4-CHECK：sample sidebar UI 复核 ✅
- P13-CREATION-B4-CLOSE：sample sidebar UI 阶段收口 ✅
- P13-B4-REGRESSION-FIX1：修复 workspace layout tab 回归 ✅
- P15-STATS-B1-PARK：统计面板实现延后，保留为后期待办 ✅
- P16-REAL-USAGE-ISSUES-A0：真实使用问题统一审查 ✅
- P16-CANCEL-A0-CHECK：取消确认与生成状态问题复核 ✅

## Next

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-XIAOMI-MIMO-TTS-REAL-PROBE-B3 | historical P16 real-probe follow-up, not XiangTa next step | 后置评估 |
| P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 | analyze MiMo voicedesign semantic mapping | B3 成功后评估 |
| P16-XIAOMI-MIMO-TTS-VOICE-CLONE-A0 | analyze MiMo voiceclone semantic mapping | B3 成功后评估 |
| P16-OPENAI-COMPATIBLE-TTS-A0 | design OpenAI-compatible TTS adapter | 可后置 |
| P16-DYNAMIC-PROVIDER-CONFIG-B2 | provider capability override enhancements | 可后置 |
| P16-PROVIDER-CAPABILITY-UI-B1 | capability-driven provider/model UI | real probe 后评估 |
| P16-VOICE-PROFILE-DELETE-A0 | design voice profile deactivate/delete flow | 评估候选：补齐人设生命周期管理 |
| P16-VARIANTS-UX-FIX1 | add visible waiting state for voice variants | 可后置 |
| P17-CREATION-RECORD-A0 | design server-side creation record and restore API | Backlog |
| P13-HISTORY-SECURITY-FIX1 | escape history text snippet | 小型安全债 |
| P15-STATS-B1 | local statistics panel | Backlog |
| P15-SERVER-STATS-A0 | server-side statistics | Backlog |

## 长期规则

每次新增 provider、adapter、probe 或环境变量时，必须同步检查：
- `.env.example` 是否更新（新增变量注释占位）
- `.gitignore` 是否忽略临时文件
- `docs` 是否记录变量用途
- `tests` 是否有对应测试覆盖

## Paused / Do not touch yet

| 区域 | 原因 |
|---|---|
| `batch_shared.js` | shared batch state 风险极高，需统一状态管理设计 |
| `profile_binding.js` | 被 voice list / audition / batch / clone / design 多处共用 |
| `audition_workstation.js` | 强耦合 `handleGenerate` 单条生成链路 |
| `error_helpers.js` | 被十余处引用，迁移成本大，收益小 |
| `provider_capabilities.js` | 已稳定，无充分理由动 |
| Vite / React migration | 当前阶段不引入 |
| dynamic loading | 当前阶段不需要 |
| tab/subtab switching | 涉及所有 Tab DOM visibility 状态，不应抽 |
| 移动端 H5 | 当前阶段不优先 |
| SaaS / 多用户 | 当前阶段不引入 |

## 详细历史来源

- 完整变更记录：`docs/PROJECT_HEALTH_CHECK.md`
- 前端模块化演进：`docs/P9_FRONTEND_MODULARIZATION.md`
- 产品打磨计划：`docs/P10_PRODUCT_POLISH_PLAN.md`
- P11 瘦身计划：`docs/P11_INDEX_REDUCTION_PLAN.md`
- P12 真实使用验证：`docs/P12_USAGE_VALIDATION_PLAN.md`
