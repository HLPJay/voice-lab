# P18-XIANGTA-H5-PROTOTYPE-PORT-C10A-FIX1

**日期**: 2026-05-18
**分支**: p18/xiangta-product-api
**状态**: DONE

## 任务

将 `design_h5/想他了点击版本/` 原型的视觉结构移植到 `apps/xiangta-h5/`，同时保留所有真实 API 接线。

## 变更清单

### index.html
- 添加 `phone-shell` 容器，移动端居中 max-width 430px
- 新增 `app-topbar`：LetterSeal SVG + 品牌标题 + 历史按钮
- 新增 `literary-greeting`：显示日期/星期/时段/时间
- Recipient 区域改为 2×2 卡片网格（含 SVG 图标 + 副标题）
- Scene 区域改为 2 列芯片（含 hint 副标题）
- CTA 按钮改为暖金色 `btn-cta`
- 新增底部 `status-pill-bar`（Provider 状态 + 隐私说明）
- 保留 `coreProfileSelect`、`devPanel`、所有 screen 结构

### styles.css
- 新增 `--c-cta` 暖金色令牌、`--font-serif`/`--font-sans`/`--font-mono` 排版令牌
- 新增 `.phone-shell`、`.app-topbar`、`.recipient-card`、`.scene-chip`、`.status-pill-bar` 样式
- 卡片圆角升级至 18px，输入框升级至 14px radius
- 保留所有功能性 CSS（`.tts-result`、`.suggestion-card`、`.letter-card` 等）

### app.js
- 新增 `RECIPIENT_META`：4 个对象（lover/family/friend/self），含 label、hint、SVG icon
- 新增 `SCENE_META`：5 个场景（miss/sorry/thanks/comfort/night），含 label、hint
- `renderRecipientGrid()` 改为渲染带图标+副标题的卡片
- `renderSceneGrid()` 改为渲染带副标题的芯片
- 新增 `renderLiteraryGreeting()`：根据当前时间渲染文学问候
- 新增 `renderStatusPill()`：根据 providerStatus 渲染底部状态药丸
- 保留所有 API 函数不变

### 测试
- 新增 `tests/xiangta/test_h5_design_alignment.py`（28 tests）
- 更新 `test_h5_product_flow.py` 和 `test_product_integration_smoke.py` 适配新 CSS 类名

## 测试结果

- 769 XiangTa tests passed
- 28 design alignment tests passed
- 45 H5 contract tests passed
- 18 runtime app tests passed

## 保留的 API 函数

loadBootstrap, generateSuggestions, selectSuggestion, generateTtsTask,
pollTtsTask, renderTtsTask, revealSaveLetterSection, saveLetter,
loadLetters, renderLetters, showScreen, applyModeUi, loadCoreProfiles,
renderCoreProfileSelect, generateTts (dev alias)
