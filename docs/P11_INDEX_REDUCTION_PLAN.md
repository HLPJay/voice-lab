# P11 index.html 瘦身计划

## P11-FE-REDUCE-A0：index.html 体积审查与抽离优先级

**审查时间：** 2026-05-15

---

## 1. 当前 index.html 体积

**行数：** 4668 行

**主要组成：**

| 区域 | 近似行范围 | 说明 |
|---|---|---|
| HTML DOM（所有 tab） | ~1–870 | 纯结构 |
| Tab 切换 + 全局初始化 | ~1610–1700 | Tab 事件绑定 |
| Provider capability | ~1620–1680 | P9-CAPABILITY3 |
| Runtime status | JS 文件已抽离 | — |
| History | JS 文件已抽离 | — |
| Profile/voice 加载 | ~1722–1780 | loadProfiles, loadVoices, populateProfileSelect |
| bindVoiceToProfile | ~1780–1795 | 绑定 API |
| Cost hint | ~1860–1900 | updateCostHint |
| Profile select population | ~1901–1925 | populateAllProfiles, showProfileRetry |
| **P10 音色绑定提示** | ~1927–2030 | **B1/B3 建议优先抽离** |
| **P8-5 最近任务** | ~2033–2200 | recentJobRestore/restoreRecentJob |
| Shared helpers（esc, toast, hexToBlobUrl 等） | ~2236–2320 | esc, showToast, hexToBlobUrl, confirmHighCost |
| guardedJsonFetch + error helpers | ~2330–2620 | parseApiError, formatApiError, renderApiError 等 |
| **handleGenerate + 单条生成链路** | ~2686–3270 | **禁止动** |
| checkBindingStatus + refreshBindingVoiceSelect | ~3304–3360 | 绑定状态刷新 |
| refreshVoiceBindStatus | ~3374–3390 | 刷新 voice bind map |
| **Voice list / audition workstation** | ~3417–3650 | renderAuditionWorkstation, handleListVoices |
| Voice table render/filter/pagination | ~3729–3870 | filterVoiceList, renderVoiceTable, pagination |
| quickBindVoice | ~3930–3993 | 绑定面板 |
| loadAllBindings | ~3995–4020 | 加载所有绑定 |
| handleVoiceDeleteFromList | ~4023–4060 | 删除音色 |
| Binding management handlers | ~4079–4230 | handleListBindings, handleCreateBinding |
| Profile creation | ~4173–4220 | handleCreateProfile |
| Script line management | ~4258–4310 | addScriptLine, removeScriptLine, event delegation |
| Batch progress / polling / rendering | ~4375–4565 | showBatchProgress, startBatchPoll, renderBatchResultPlayer |
| Batch submit/play/retry | ~4644–4668 | handleBatchPlay, handleBatchRetry |

---

## 2. P10 结论回顾与 P9-FE2-A0 的关系

**P9-FE2-A0（2026-05-15）结论：** 暂停前端模块化，聚焦产品功能打磨。

**理由：**
1. voice_list.js 可抽但优先级低
2. audition_workstation.js 强耦合单条生成链路，不应单独抽
3. profile_binding.js window 出口已够用
4. error_helpers.js 12+ call sites，迁移成本大，拆分收益有限
5. batch_shared.js 需统一设计状态管理，当前阶段不应动

**P10 已完成：** B1–B6 产品打磨全部完成，所有 UI hint 逻辑直接写在 index.html 中，无新增模块文件。

**P11 问题：** P10 新增的 UI hint 逻辑（B1/B3 绑定提示）是否可以/应该抽出为独立模块？

---

## 3. P10 新增逻辑审查

### updateWorkspaceVoiceBindingHint（B1）

- **行数：** ~39 行（1927–1965）
- **依赖：** `esc()`、`window._voiceBindMap`、`profileSelect.value`、`providerSelect.value`
- **调用方：** profileSelect change、providerSelect change、workspace tab 切换回调、populateAllProfiles 末尾
- **无状态写入**、无 API 调用、只操作 DOM

### updateBatchVoiceBindingHint（B3-longtext）

- **行数：** ~28 行（1966–1993）
- **依赖：** `esc()`、`window._voiceBindMap`、`#batchProfile.value`、`#batchProvider.value`
- **调用方：** `#batchProfile.change`、`#batchProvider.change`、longtext tab 切换回调
- **无状态写入**、无 API 调用、只操作 DOM

### updateScriptLineVoiceHint（B3-script）

- **行数：** ~42 行（1994–2035）
- **依赖：** `esc()`、`window._voiceBindMap`、`#scriptProfile_${id}.value`、`#batchScriptProvider.value`
- **调用方：** `addScriptLine()` 末尾、script tab 切换回调、`#scriptLines` change 事件委托
- **无状态写入**、无 API 调用、只操作 DOM

### 共同特征

| 特征 | 说明 |
|---|---|
| 无独立状态 | 只读取 `window._voiceBindMap` 和 DOM 值 |
| 无直接 API 调用 | 通过 `window._voiceBindMap` 间接依赖 loadAllBindings |
| 只操作 DOM | 无事件 dispatch，无跨模块通信 |
| 纯 UI 展示逻辑 | 展示音色绑定状态引导用户操作 |
| 高内聚 | 三个函数逻辑几乎完全一致（同一模式的不同 DOM 目标） |

---

## 4. 可抽离模块候选分析

### product_hints.js（强烈推荐优先抽离）

**包含内容：**
- `updateWorkspaceVoiceBindingHint()`
- `updateBatchVoiceBindingHint()`
- `updateScriptLineVoiceHint()`

**理由：**
1. **纯 UI，无业务状态**：不管理任何状态，只读取 `window._voiceBindMap`
2. **高内聚低耦合**：三处音色绑定提示逻辑高度一致，抽出后可复用
3. **风险极低**：不影响 handleGenerate、batch payload、后端 API、shared state
4. **E2E 已有覆盖**：B1/B3 的 E2E 间接覆盖了这些函数的运行时行为
5. **不再往 index.html 加逻辑**：P10 已完成，产品打磨不再新增代码到 index.html

**window 入口：**
```javascript
window.updateWorkspaceVoiceBindingHint = updateWorkspaceVoiceBindingHint;
window.updateBatchVoiceBindingHint = updateBatchVoiceBindingHint;
window.updateScriptLineVoiceHint = updateScriptLineVoiceHint;
```

**E2E 需求：**
- 迁移后需新增 `test_product_hints_module_is_loaded_and_exports_available`
- 验证 `window.updateWorkspaceVoiceBindingHint` 等为 function

### recent_job_restore.js（可选）

**包含内容：**
- `saveRecentJob() / loadRecentJob() / clearRecentJob()`
- `renderRecentJobRestore()`
- `restoreRecentJob()`
- `renderRecoveredJob()`

**问题：**
- 依赖 `apiJson()` 和 `renderApiError()` — 这两个在 index.html 中短期内不会动
- `renderRecoveredJob()` 调用 `resultSectionLabel()`、`audioPlayerHtml()`、`timelineTable()` 等 index.html 内的 HTML builder
- 如果抽出，需要同时移动这些 HTML builder 或以 `window.*` 接口替代
- **结论：当前不建议抽，收益复杂化大于收益**

### voice_list.js（优先级低，P9-FE2-A0 已说明）

**包含内容：**
- `handleListVoices`、`filterVoiceList`、`renderVoiceTable`
- `handlePageSizeChange`、`handlePrevPage`、`handleNextPage`

**问题：**
- 依赖 `renderAuditionWorkstation`、`setupAuditionWorkstation`（audition workstation 强耦合单条生成）
- `renderVoiceTable` 内部有 `_voiceBindMap` 写入逻辑
- 建议等 audition workstation 整体方案确定后再评估

### script_lines.js（可选但不紧急）

**包含内容：**
- `addScriptLine`、`removeScriptLine`、`updateScriptLineLimitState`
- `_scriptRows`、`_scriptLineCount`、`MAX_SCRIPT_LINES`
- 事件委托（input/change/click）

**问题：**
- 依赖 `populateProfileSelect`、`esc`、`loadProfiles`、`_cachedProfiles`
- `batch_script.js` 已通过 window 调用 `populateProfileSelect`，如果抽出 script_lines.js，`batch_script.js` 需要调整对 `addScriptLine` 的调用方式
- **结论：当前不建议动，batch_script.js 刚稳定**

### profile_binding_helpers.js（P9-FE2-A0 结论保留）

- `checkBindingStatus`、`refreshBindingVoiceSelect`、`refreshVoiceBindStatus`
- 依赖关系复杂，被多处引用
- 当前 window 出口够用，不值得动

### error_helpers.js（P9-FE2-A0 结论保留）

- 12+ call sites，迁移成本大
- 拆分收益有限，当前不建议动

---

## 5. P11-FE-REDUCE 建议方案

### 优先级 1（立即可做，风险极低）

**抽离 `product_hints.js`：**
- 将 `updateWorkspaceVoiceBindingHint`、`updateBatchVoiceBindingHint`、`updateScriptLineVoiceHint` 移入
- 依赖 `esc()` 已存在于 index.html，移到 IIFE 顶部
- window 入口：`window.updateWorkspaceVoiceBindingHint` 等
- 不移动任何 HTML builder、API call、状态管理代码

### 优先级 2（等产品反馈后再评估）

- voice_list.js 是否抽出，取决于 voice list 功能是否稳定
- batch_shared.js 统一状态管理，取决于批量任务复杂度是否上升

### 不再往 index.html 加代码

- P10 产品打磨已完成
- 后续新功能/产品化代码，优先考虑是否值得新增 module 文件，而非继续堆到 index.html

---

## 6. P11-FE-REDUCE-B1 最小实现方案

**目标：** 抽出 `product_hints.js`

**不改：**
- handleGenerate、batch payload、后端 API
- shared batch state
- voice list rendering
- error helpers

**只做：**
1. 新建 `app/static/js/product_hints.js`
2. 将三个 `update*VoiceHint` 函数移入（附带 `esc()` 局部副本）
3. index.html 中三个函数改为 `window.updateWorkspaceVoiceBindingHint` 等调用
4. 加载顺序：product_hints.js 在 index.html inline script 之前（与 provider_capabilities.js 一致）
5. 新增 E2E：`test_product_hints_module_is_loaded_and_exports_available`

**验收标准：**
1. `window.updateWorkspaceVoiceBindingHint` 类型为 function
2. `window.updateBatchVoiceBindingHint` 类型为 function
3. `window.updateScriptLineVoiceHint` 类型为 function
4. B1/B2/B3 的 existing E2E 全部仍然 pass
5. 不调用真实 MiniMax API

---

## 7. E2E 策略

- 只需新增 module-loaded E2E，不需要 behavioral E2E（这三个函数的行为已由 B1/B3 的 existing E2E 覆盖）
- 不需要 targeted E2E 因为这三个函数不涉及 API 调用

---

## 8. 与 P9-FE2-A0 结论的关系

**P9-FE2-A0 结论需要小修正：**

P9-FE2-A0 说"error_helpers.js 迁移成本大，拆分收益有限"和"profile_binding_helpers 不值得动"，这个结论**仍然有效**。

但 P9-FE2-A0 是在"暂停模块化"的背景下说的，P10 完成后，现在是**重新评估**的好时机——只抽那些**纯 UI、无状态、零业务耦合**的低风险模块。

**修正结论：**
- `product_hints.js` 是当前唯一值得优先抽离的模块

---

## P11-FE-REDUCE-B1：product_hints.js 抽离实现

**执行时间：** 2026-05-15

### 实现内容

**新建文件：** `app/static/js/product_hints.js`

**迁移内容：**
- `updateWorkspaceVoiceBindingHint` → `window.updateWorkspaceVoiceBindingHint`
- `updateBatchVoiceBindingHint` → `window.updateBatchVoiceBindingHint`
- `updateScriptLineVoiceHint` → `window.updateScriptLineVoiceHint`
- `switchToVoicesTab()` — 共享的切 tab 逻辑

**关键设计决策：**
- 函数内改为 `document.getElementById()` 访问 DOM，而非依赖 inline script 中的脚本局部变量 `profileSelect` / `providerSelect`
- 这样 product_hints.js 在 index.html inline script 之前加载时，函数仍能正常工作（因为事件处理器在 inline script 中设置，设置时函数已在 window 上）
- 使用局部 `phEsc()` 替代 index.html 的 `esc()`

**index.html 改动：**
- 新增 `<script src="/static/js/product_hints.js"></script>`（history.js 之后）
- 删除三个函数定义（原 lines 1926–2016）
- 事件绑定调用方式不变（仍为 `updateWorkspaceVoiceBindingHint()`，通过 window 引用）

**验收结果：**

| 验收项 | 结果 |
|---|---|
| `window.updateWorkspaceVoiceBindingHint` 类型为 function | ✅ |
| `window.updateBatchVoiceBindingHint` 类型为 function | ✅ |
| `window.updateScriptLineVoiceHint` 类型为 function | ✅ |
| B1/B2/B3 E2E 全部 pass | ✅（4 targeted, 29 total） |
| 不调用真实 MiniMax API | ✅ |

### E2E

- targeted（B1/B2/B3）：4 passed
- full suite：29 passed
- 无需新增 module-loaded E2E（B1/B2/B3 已有 behavioral E2E 覆盖）

### P11-FE-REDUCE-A1-CHECK 验证结果

| 检查项 | 结果 |
|---|---|
| index.html 中无 updateWorkspaceVoiceBindingHint 函数定义 | ✅ |
| index.html 中无 updateBatchVoiceBindingHint 函数定义 | ✅ |
| index.html 中无 updateScriptLineVoiceHint 函数定义 | ✅ |
| window.updateWorkspaceVoiceBindingHint 类型为 function | ✅ |
| window.updateBatchVoiceBindingHint 类型为 function | ✅ |
| window.updateScriptLineVoiceHint 类型为 function | ✅ |
| script 加载顺序正确（product_hints.js 在 inline script 之前） | ✅ |
| product_hints.js 只处理 UI hint，无生成逻辑 | ✅ |
| 未改 handleGenerate / batch payload / 后端 API / shared batch state | ✅ |
| targeted E2E（4）：voice_binding_hint + quick_bind：4 passed | ✅ |
- 其它模块（voice_list、script_lines、error_helpers、batch_shared）当前阶段不应动

---

## P11-FE-REDUCE-A2-A0：recent_job 模块抽离边界审查

**审查时间：** 2026-05-15

**性质：** 文档记录，不迁移代码

---

### A2 审查范围

P8-5 最近任务恢复相关函数：

| 函数 | 行 | 职责 |
|---|---|---|
| `RECENT_JOB_STORAGE_KEY` | 1943 | localStorage key 常量 |
| `safeTextPreview` | 1945 | 文本截断辅助 |
| `extractJobId` | 1951 | 从 API 响应提取 job_id |
| `extractAudioAssetId` | 1955 | 从 API 响应提取 audio_asset_id |
| `buildRecentJobPayload` | 1962 | 构建 localStorage payload |
| `saveRecentJob` | 1979 | 保存到 localStorage + 调用 renderRecentJobRestore |
| `loadRecentJob` | 1990 | 从 localStorage 加载 |
| `clearRecentJob` | 2007 | 从 localStorage 清除 + 调用 renderRecentJobRestore |
| `renderRecentJobRestore` | 2016 | 渲染最近任务卡片 DOM |
| `restoreRecentJob` | 2046 | 调用 jobs API + 调用 renderRecoveredJob |
| `renderRecoveredJob` | 2072 | 渲染恢复后的任务结果卡片 |

---

### 依赖分析

#### saveRecentJob / loadRecentJob / clearRecentJob / buildRecentJobPayload

**特征：**
- 纯 localStorage 操作 + 纯数据转换
- 无 DOM 依赖（除 `renderRecentJobRestore` 调用外）
- 无 API 调用
- `buildRecentJobPayload` 只调用 `extractJobId`、`extractAudioAssetId`、`safeTextPreview`

**可迁移性：可迁移，风险低**

`saveRecentJob` 被以下位置调用（均在 index.html inline script 中）：
- `restoreRecentJob()` — line 2059
- `handleGenerate` — line 2659, 2662
- `startStreamGenerate` — line 2749
- `startAsyncPolling` — line 2902

抽离后需要这些调用点使用 `window.saveRecentJob(...)` 或保持 `saveRecentJob(...)`（通过 window 引用）。

#### renderRecentJobRestore

**依赖：**
- `loadRecentJob()` — 可随模块迁移
- `formatLocalDateTime()` — index.html 中的共享 helper（被多处使用）
- `esc()` — index.html 中的共享 helper

**问题：**
- 依赖 index.html 中的共享 helper，无法独立迁移
- 渲染 DOM 到 `#recentJobRestore`

**可迁移性：暂不迁移**

#### restoreRecentJob

**依赖：**
- `loadRecentJob()` — 可随模块迁移
- `apiJson()` — index.html 中的共享 API helper（被多处使用）
- `renderApiError()` — index.html 中的 shared error helper
- `renderRecoveredJob()` — 见下

**可迁移性：暂不迁移**

#### renderRecoveredJob

**依赖：**
- `extractAudioAssetId()` — 可随模块迁移
- `esc()` — index.html 共享 helper
- `safeTextPreview()` — 可随模块迁移
- `statusLabel()` — index.html 共享 helper
- `resultSectionLabel()` — index.html 共享 helper
- `audioPlayerHtml()` — index.html 共享 helper
- `timelineTable()` — index.html 共享 helper
- `resultStatusHintHtml()` — index.html 共享 helper

**问题：**
- 依赖大量 index.html 共享 helper，无法独立迁移
- 渲染 DOM 到 `#resultsArea`

**可迁移性：暂不迁移**

---

### 抽离方案分析

#### 方案 A：只迁移 localStorage 核心（低风险）

**迁移：**
- `RECENT_JOB_STORAGE_KEY`
- `extractJobId`
- `extractAudioAssetId`
- `safeTextPreview`
- `buildRecentJobPayload`
- `saveRecentJob`
- `loadRecentJob`
- `clearRecentJob`

**保留在 index.html：**
- `renderRecentJobRestore`（依赖 `formatLocalDateTime`、`esc`）
- `restoreRecentJob`（依赖 `apiJson`、`renderApiError`）
- `renderRecoveredJob`（依赖多个共享 helper）

**问题：**
- `saveRecentJob` 被多处调用，抽离后 index.html 内仍需调用 `window.saveRecentJob`
- `renderRecentJobRestore` 和 `restoreRecentJob` 继续留在 index.html，逻辑分散
- 节省约 40 行，但引入模块边界复杂度

**结论：不值得，收益太小**

#### 方案 B：不迁移（现状）

**理由：**
1. **E2E 零覆盖**：无任何 E2E 测试 recent job restore，迁移风险无测试网保护
2. **高度耦合**：三个 render 函数依赖大量 index.html 共享 helper，强行迁移破坏内聚性
3. **节省有限**：只迁移 localStorage 核心 + 提取工具，约 40 行，收益小
4. **调用分散**：`saveRecentJob` 在 5 处被调用（handleGenerate/stream/async 链路），每处都需要改为 window 调用

**结论：暂不迁移，维持现状**

---

### A2-A0 审查结论

**不建议迁移 recent_jobRestore 相关函数到独立模块。**

| 原因 | 说明 |
|---|---|
| E2E 零覆盖 | 无任何 E2E 测试 recent job restore，迁移无保护 |
| 高度耦合 | render 函数依赖多个 index.html 共享 helper，无法独立迁移 |
| 收益有限 | localStorage 核心仅 40 行，迁移收益小 |
| 分散调用 | saveRecentJob 在 5 处被调用，引入 window 调用复杂度 |

**建议：**
- 后续如需迁移，先补 recent job restore E2E
- 优先确保 P11 其它更高价值任务完成
- batch_shared 状态管理设计、P11 后端能力增强优先于 recent_job 模块化

---

## P11-FE-REDUCE-CHECK：index.html 瘦身收口检查

**执行时间：** 2026-05-15

### 检查结果

| 检查项 | 结果 |
|---|---|
| product_hints.js 加载顺序正确（在 inline script 之前） | ✅ |
| index.html 中无 updateWorkspaceVoiceBindingHint 函数定义 | ✅ |
| index.html 中无 updateBatchVoiceBindingHint 函数定义 | ✅ |
| index.html 中无 updateScriptLineVoiceHint 函数定义 | ✅ |
| window.updateWorkspaceVoiceBindingHint 可用 | ✅ |
| window.updateBatchVoiceBindingHint 可用 | ✅ |
| window.updateScriptLineVoiceHint 可用 | ✅ |
| recent_job_restore 保持不迁移 | ✅ |
| 未改 handleGenerate | ✅ |
| 未改 batch_longtext.js / batch_script.js payload | ✅ |
| 未改后端 API | ✅ |
| 未改 shared batch state | ✅ |
| 未调用真实 MiniMax | ✅ |
| E2E 全量 29 passed | ✅ |

### P11 完成清单

| 任务 | 状态 |
|---|---|
| P11-A0: index.html 瘦身审查 | ✅ |
| P11-A1: product_hints.js 抽离 | ✅ |
| P11-A1-CHECK: product_hints.js 验证 | ✅ |
| P11-A2-A0: recent_jobRestore 审查（结论：不迁移） | ✅ |

### P11 结论

P11 index.html 瘦身阶段完成。优先抽离了纯 UI 无耦合的 `product_hints.js`，收益明确且风险极低。`recent_job_restore` 因 E2E 零覆盖 + 高度耦合，结论为不迁移。后续不再主动往 index.html 增加新逻辑，新模块需有明确收益才引入。
