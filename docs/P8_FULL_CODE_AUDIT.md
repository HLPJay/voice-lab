# P8 Full Code Audit

## 1. 审查基线

- Branch: `dev`
- Commit: `306dada` (p8-ux5-fix2: keep script batch progress in script tab)
- Date: 2026-05-14
- Reviewer: Claude Code (automated + human review)
- Scope: 全量自检，前端交互、后端 API、资产清理、测试覆盖、文档一致性

## 2. 执行命令

| 命令 | 结果 | 说明 |
|---|---|---|
| `git diff --check` | 无输出 | 无空白字符错误 |
| `python -m pytest tests/ -x -q` | **466 passed, 6 skipped** | 全量通过，无失败 |
| `python -m compileall app scripts tests` | 无错误 | 所有 Python 文件编译通过 |
| `git grep -n "os.remove\|shutil.rmtree\|unlink" scripts/` | 无匹配 | 清理脚本无物理删除 |
| `git grep -n "shutil.move" scripts/` | 2处（quarantine + restore） | 确认使用 move 而非 copy |
| `git grep -n "TODO\|FIXME" app/` | 无匹配 | 无悬空 TODO |
| `git grep -n "purge" scripts/cleanup_assets.py` | 拒绝 purge 参数 | 确认 purge 未实现 |
| `git status -sb` | `dev...origin/dev` 同步 | 无未同步更改 |

## 3. 当前功能状态总览

| 模块 | 状态 | 结论 |
|---|---|---|
| 创作工作台（T2A） | OK | 单条/异步/流式/多版本均正常，状态反馈完整 |
| 长文本批量 | OK | P8-UX5-FIX2 后长文本面板未被破坏 |
| 剧本批量 | OK | P8-UX5-FIX2 后剧本内显示进度，不跳转 Tab |
| 音色管理 | OK | 音色查询/试听/克隆/设计均正常 |
| 历史记录 | OK | P8-UX4-FIX 后播放/删除/复制均正常 |
| 高级 Tab | OK | 克隆/设计/绑定/危险操作确认正常 |
| Admin 面板 | OK | focus=call-logs 导航正常 |
| 状态条 | OK | P8-UX3 后 chip 跟随选择+tooltips |
| 资产清理 | OK | 手动 dry-run/quarantine/restore，无自动删除 |
| 后端 API | OK | 所有接口与前端契约一致 |
| 测试覆盖 | OK | 466 passed, 6 skipped，无失败 |

## 4. 问题清单

| ID | 等级 | 模块 | 问题 | 建议 | 是否立即修 |
|---|---|---|---|---|---|
| AUDIT-001 | P1 | 前端 | 长文本批量失败时错误回退到 `resultsArea`（T2A 区域），不是 batch 结果区 |
| AUDIT-002 | P2 | 前端 | profile select retry 按钮添加后未在成功后移除，DOM 残留 |
| AUDIT-003 | P2 | 前端 | `_currentBatchPanelId` 未声明 `let` 即使用，可导致 retry 异常 |
| AUDIT-004 | P2 | 前端 | runtime status chip 加载失败 catch 块静默，不显示用户提示 |
| AUDIT-005 | P3 | 前端 | README 测试数量 439，实际 466 |
| AUDIT-006 | P3 | 文档 | ARCHITECTURE.md 有历史遗留的"测试面板"描述（标注为仅供参考） |
| AUDIT-007 | P3 | 杂项 | `docs/prompts/` 目录有未跟踪的临时 prompt 文件 |

## 5. 详细问题说明

---

### AUDIT-001
- **等级**：P1
- **模块**：前端 / 长文本批量
- **问题描述**：`handleBatchLongtextSubmit` 失败时错误回退到 `document.getElementById('batchResult') || resultsArea`。由于 `batchResult` 元素不存在（只有 `batchResultPlayer`），错误最终出现在 `resultsArea`（T2A 生成结果区），语义不正确。
- **影响范围**：长文本批量提交 API 失败时，用户看到错误出现在创作工作台结果区，而不是批量任务区域。
- **证据位置**：`app/static/index.html:5061, 5078` — `const resultsEl = document.getElementById('batchResult') || resultsArea`
- **建议修复方式**：在长文本 tab HTML 中添加 `<div id="batchLongtextResult"></div>`，或将错误显示在 `batchProgressPanel` 内。
- **是否建议立即修复**：是（影响批量任务可发现性）

---

### AUDIT-002
- **等级**：P2
- **模块**：前端 / profile select
- **问题描述**：`showProfileRetry()` 在加载失败时通过 `parentNode.appendChild(btn)` 添加重试按钮，但如果后续 `loadProfiles()` 成功，该按钮从未被移除，会残留在 DOM 中。
- **影响范围**：profile select 加载失败后重试成功时，页面上残留重试按钮。
- **证据位置**：`app/static/index.html:1883-1899` — `profileSelect.parentNode.appendChild(btn)`
- **建议修复方式**：在 `populateAllProfiles` 成功回调中移除已存在的重试按钮，或用 `resultsEl` 容器管理而非 `parentNode.appendChild`。
- **是否建议立即修复**：否（不影响核心功能，修复成本低但属于体验优化）

---

### AUDIT-003
- **等级**：P2
- **模块**：前端 / batch 轮询
- **问题描述**：`_currentBatchPanelId` 在 `startBatchPoll` 中被赋值（`_currentBatchPanelId = targetPanelId`），但变量从未用 `let` 声明。虽然当前流程不会触发 undefined 问题（retry 只在 batch 提交后调用），但代码不健壮。
- **影响范围**：如果直接调用 `handleBatchRetry` 而非通过 `showBatchProgress`/`startBatchPoll` 流程，`targetPanelId` 为 `undefined`，导致 DOM 查询失败。
- **证据位置**：`app/static/index.html:5216` — 赋值语句；变量声明缺失于 `app/static/index.html:5012-5013` 附近
- **建议修复方式**：在 `let _batchPollTimer = null;` 下方添加 `let _currentBatchPanelId = 'batchProgressPanel';`
- **是否建议立即修复**：否（当前流程安全，但应补齐变量声明）

---

### AUDIT-004
- **等级**：P2
- **模块**：前端 / runtime status
- **问题描述**：`loadRuntimeStatus` 的 `catch` 块静默失败，不给用户任何反馈（按钮 gone、chip 显示为空），用户不知道是网络问题还是服务挂了。
- **影响范围**：API 不可用时用户看不到明确错误提示，不知道要重试。
- **证据位置**：`app/static/index.html:1617-1623` — `catch (_) { ... chipStatus.textContent = '点击重试'; ... }` 但无 toast/alert
- **建议修复方式**：增加 `showToast('用量统计加载失败，请点击重试', 'error')`。
- **是否建议立即修复**：否（芯片已有点击重试机制，轻量提示可后续补）

---

### AUDIT-005
- **等级**：P3
- **模块**：文档 / README
- **问题描述**：README.md 第 213 行测试数量为 `439 passed`，实际全量测试为 `466 passed`。
- **影响范围**：文档与实际状态不符，读者看到过时数字。
- **证据位置**：`README.md:213` — `当前：439 passed, 6 skipped, 0 failed`
- **建议修复方式**：更新为 `466 passed, 6 skipped`。
- **是否建议立即修复**：否（下次文档更新时修正即可）

---

### AUDIT-006
- **等级**：P3
- **模块**：文档 / ARCHITECTURE.md
- **问题描述**：ARCHITECTURE.md 包含过时项目描述（"Voice Lab 测试面板"），但该文档已标注为"历史文档，仅作参考"。
- **影响范围**：低，仅历史参考文档。
- **证据位置**：`docs/ARCHITECTURE.md:7`
- **建议修复方式**：无需修复（文档已标注仅供参考）。
- **是否建议立即修复**：否

---

### AUDIT-007
- **等级**：P3
- **模块**：杂项 / docs/prompts
- **问题描述**：`docs/prompts/P8_FIX1_FRONTEND_REGRESSION_REPAIR_COMMAND.md` 为临时 prompt 文件，未被 .gitignore 排除，未被任何文档索引引用。
- **影响范围**：低，污染仓库。
- **证据位置**：`docs/prompts/` 未在 .gitignore 中排除（但 .gitignore 已有 `docs/generated/`，不包含 `docs/prompts/`）
- **建议修复方式**：将 `docs/prompts/` 加入 .gitignore，或删除该目录（如果不再需要）。
- **是否建议立即修复**：否

---

### AUDIT-008
- **等级**：P1
- **模块**：前端 / 批量进度
- **问题描述**：`renderBatchStatus` 的 table header 硬编码包含 `<th>角色</th>`，但长文本批量任务的 segments 没有 role 字段，导致长文本批量进度表多出一列无意义的"角色"。
- **影响范围**：长文本批量提交后在剧本 Tab 的进度表出现无内容的"角色"列。
- **证据位置**：`app/static/index.html:5419` — `<th style="padding:4px 8px">角色</th>`
- **建议修复方式**：在 `renderBatchStatus` 中增加 `const isScriptPanel = targetPanelId === 'batchScriptProgressPanel'` 然后按 `isScriptPanel` 分支渲染 table header 和 rows。
- **是否已修复**：是（P8-UX7）

---

### AUDIT-009
- **等级**：P2
- **模块**：前端 / 剧本 Tab
- **问题描述**：剧本 Tab 的台词列表每行右侧声音人设 select 不稳定：用户选择后因 `populateProfileSelect` 重新设置 `innerHTML` 导致选择丢失；删除行后其他行状态不受影响（正确），但新增行时旧行选择可能受影响。
- **影响范围**：用户选择人设后立即消失，或添加新行时旧行选择被重置。
- **证据位置**：`app/static/index.html:1748-1762` — `populateProfileSelect`；`app/static/index.html:4989-5014` — `addScriptLine`
- **建议修复方式**：`populateProfileSelect` 保留已有选择；建立 `scriptRows` 状态数组管理台词行数据；`addScriptLine`/`removeScriptLine` 更新状态；`handleBatchScriptSubmit` 从状态数组读取而非 DOM 查询。
- **是否已修复**：是（P8-UX7）

---

## 6. 测试覆盖缺口

### 已有充分覆盖的领域
- `test_runtime_status.py` — 27 tests（runtime status API 全场景）
- `test_voice_jobs_delete.py` — 5 tests（软删除、幂等、404）
- `test_voice_jobs_assets.py` — 4 tests（audio_asset 字段完整性）
- `test_cleanup_assets_dry_run.py` — 31 tests（dry-run planner）
- `test_cleanup_assets_quarantine.py` — 24 tests（quarantine + restore）
- `test_batch_api.py` — 批量接口覆盖

### 缺口领域（建议后续补充）

1. **前端 E2E（无自动化）**：无 Playwright/Selenium 等浏览器级自动化测试，前端所有交互（播放、删除、批量提交）依赖手动验收。
   - 建议：引入 Playwright 最小 E2E 集，当前不强制引入。

2. **剧本批量 API 边界测试**：后端 `ScriptBatchRequest` 校验（`min_length=1`、`max_length=200`）和 `role` 为空时行为无明确单元测试覆盖。
   - 建议：补充 `test_batch_script_validation` 测试空台词、role 缺失场景。

3. **batchRetry 幂等性**：重试接口返回结构未专项测试。

4. **WebSocket session 问题**：`ws_render.py` 使用 `next(get_session())` 绕过 FastAPI 依赖注入，测试覆盖通过 monkey-patch 绕过，非理想但已覆盖。

## 7. 文档一致性问题

| 位置 | 问题 | 状态 |
|---|---|---|
| `README.md:213` | 测试数量 439 vs 实际 466 | 需更新 |
| `docs/ARCHITECTURE.md` | 历史文档有"测试面板"旧描述 | 已知，仅参考 |
| `docs/PROJECT_HEALTH_CHECK.md` | 最新阶段记录到 P8-UX5-FIX2 | ✅ 一致 |
| `.env.example` vs `app/core/config.py` | 所有配置项一致 | ✅ 一致 |
| `docs/P8_BE3D_ASSET_QUARANTINE.md` | shutil.move 描述与代码一致 | ✅ 一致 |
| `README` 资产清理命令 | 与 cleanup_assets.py 实际参数一致 | ✅ 一致 |

## 8. 安全与成本保护检查

| 检查项 | 结果 | 说明 |
|---|---|---|
| 高成本操作确认 | ✅ | `guardedJsonFetch` + `_OPERATION_MESSAGES` 覆盖所有高风险操作 |
| 资产清理无自动执行 | ✅ | 需手动调用 scripts/cleanup_assets.py |
| quarantine 使用 move 而非 copy | ✅ | `shutil.move` 在 quarantine 和 restore 中使用 |
| 无物理删除（os.remove/shutil.rmtree） | ✅ | cleanup_assets.py 无这些调用 |
| purge 未实现 | ✅ | cleanup_assets.py 拒绝 --purge 参数 |
| 软删除不删文件 | ✅ | `DELETE /api/voice/jobs/{id}` 只改 status |
| Admin 无数据修改操作 | ✅ | GET 接口为主，无 POST/PATCH |
| 内部 Provider API Key 不泄露 | ✅ | 前端只发 provider name，不发 key |

## 9. 资产清理工具专项检查

| 检查项 | 状态 |
|---|---|
| 启动不自动运行 | ✅ 无自动触发 |
| dry-run 不修改文件 | ✅ 只读 |
| quarantine 用 shutil.move | ✅ 源文件被移走 |
| restore 用 shutil.move | ✅ move 回原始位置 |
| 无 purge 实现 | ✅ 被拒绝 |
| 无自动删除 | ✅ |
| DB 引用资产不进入候选 | ✅ orphaned 候选只含无 DB 引用 |
| quarantine 文件夹排除扫描 | ✅ |
| docs/generated/ 在 .gitignore | ✅ |
| docs/prompts/ 未跟踪 | ⚠️ 建议加入 .gitignore |

## 10. 问题优先级清单

### 已修复
- **AUDIT-001**（P1）：长文本批量错误回退到 `resultsArea` — ✅ P8-UX6 已修复
- **AUDIT-002**（P2）：profile retry 按钮 DOM 残留 — ✅ P8-UX6 已修复
- **AUDIT-003**（P2）：`_currentBatchPanelId` 未声明变量 — ✅ P8-UX6 已修复
- **AUDIT-004**（P2）：runtime status 失败静默 — ✅ P8-UX6 已修复
- **AUDIT-005**（P3）：README 测试数量过时 — ✅ P8-UX6 已修复
- **AUDIT-008**（P1）：长文本进度表误显"角色"列 — ✅ P8-UX7 已修复
- **AUDIT-009**（P2）：剧本 profile select 不稳定 — ✅ P8-UX7 已修复

### 暂缓（文档 / 低优先级）
6. **AUDIT-006**（P3）：ARCHITECTURE.md 旧描述 — 无需处理（已标注仅供参考）
7. **AUDIT-007**（P3）：`docs/prompts/` 未跟踪 — 加入 .gitignore 或删除

## 11. 推荐下一步修复阶段命名

所有 P1-P2 问题已修复。剩余 P3 问题为文档/低优先级，建议下次有相关改动时一并处理，无需单独阶段。

AUDIT-006：无需处理（历史文档已标注仅供参考）。
AUDIT-007：建议运行 `git rm -r docs/prompts/` 或将其加入 .gitignore。

## 12. 代码质量备注

- 前端 `esc()` 函数（textContent trick）使用正确，能防止 HTML 注入
- 历史按钮已从 inline onclick 迁移到事件委托（`data-action` + `data-job-id`）
- 批量进度函数（`showBatchProgress`/`startBatchPoll`/`pollBatchStatus`/`renderBatchStatus`）已支持面板路由参数化
- 无悬空 TODO/FIXME
- cleanup_assets.py 符合安全清理策略（move-only，无 purge）
