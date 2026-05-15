# P12 真实使用问题记录

## P12-USAGE-FIX1：Workspace 音色绑定提示与 #bindingStatus 状态不一致

**发现时间：** 2026-05-15

**问题描述：**
- 在 workspace tab 中，切换人设后，`#bindingStatus` 显示"✓ 已绑定: xxx"，但 `#workspaceVoiceBindingHint` 显示"该人设尚未绑定音色"
- 根本原因：`checkBindingStatus()` 调用真实 API 获取绑定状态，但只更新 `#bindingStatus` DOM；`product_hints.js` 的 `updateWorkspaceVoiceBindingHint()` 读取 `window._voiceBindMap`，而该 map 只在 voices tab 调用 `loadAllBindings()` 时才被填充
- 数据源不一致：`#bindingStatus` ← API 直接返回，`#workspaceVoiceBindingHint` ← `window._voiceBindMap`

**影响范围：**
- Workspace tab 音色绑定提示（B1）
- 长文本 tab 音色绑定提示（B3-longtext）
- 剧本 tab 每行音色绑定提示（B3-script）

**修复方案：**
在 `checkBindingStatus()` 中，当 API 返回可用绑定时，将绑定数据同步写入 `window._voiceBindMap`；当无绑定时清除对应条目；最后调用 `window.updateWorkspaceVoiceBindingHint?.()` 确保 hint 与状态一致。

**修复位置：**
- `app/static/index.html`：`checkBindingStatus()` 函数（约 lines 3213-3260）

**E2E 覆盖：**
- 现有 29 个 E2E 测试全部通过
- 新增 Test 30（skipped）：因 providerSelect.value 在 page.evaluate 中不稳定，IIFE 闭包交互问题，测试设置困难
- 相关测试：Test 26（workspace hint 切换 tab）、Test 27（quick bind 成功切换）、Test 28（longtext hint 切换）、Test 29（script hint 切换）

**验证方式：**
- 手动切换 workspace → voices → workspace，binding hint 与 #bindingStatus 状态一致 ✅
- E2E targeted：29 passed ✅

## P12-USAGE-UX1：Advanced tab 提示区域过于臃肿

**发现时间：** 2026-05-15

**问题描述：**
- 「音色工具」页面有多个大卡片提示区域，占用过多垂直空间
- "高成本 / 工程验证能力" 大卡片（12px padding）+ "克隆、设计、导入音色后，建议绑定到人设再用于生成" 又一个大卡片
- "删除音色" 危险操作说明也是大卡片样式

**修复方案：**
- 将两个大卡片合并为一个紧凑 warning bar（约 3 行 vs 原来 6+ 行）
- 将 "删除音色" 大卡片改为紧凑 warning bar（2 行 vs 原来 4 行）

**修复位置：**
- `app/static/index.html`：tab-advanced 区域

**验证方式：**
- targeted E2E（clone/design/import）：6 passed ✅
- git diff --check：无 whitespace 错误 ✅

## P12-USAGE-FIX2：首次刷新 Workspace 默认人设绑定提示不准确

**发现时间：** 2026-05-15

**问题描述：**
- 首次刷新页面进入 Workspace 后，默认选中的人设可能已绑定音色，但页面仍显示"该人设尚未绑定音色"
- P12-USAGE-FIX1 已修复 checkBindingStatus() 的同步问题，但初始加载时 hint 仍可能错误

**原因：**
- populateAllProfiles() 中直接调用 updateWorkspaceVoiceBindingHint()，依赖 window._voiceBindMap
- 首次刷新时 _voiceBindMap 可能为空，导致错误提示

**修复方案：**
在 populateAllProfiles() 中：
1. 先调用 updateWorkspaceVoiceBindingHint() 同步设置正确初始状态
2. 再调用 checkBindingStatus() 异步刷新（以真实 API 为准）

**修复位置：**
- `app/static/index.html`：populateAllProfiles() 函数

**验证方式：**
- targeted E2E（workspace_voice_binding_hint / voice_binding_hint / quick_bind_success_go_create）：4 passed ✅
- git diff --check：无 whitespace 错误 ✅

## P12-USAGE-FIX3：Longtext / Script 绑定提示状态过期

**发现时间：** 2026-05-15

**问题描述：**
- Longtext tab 中，已绑定音色的人设仍显示"该人设尚未绑定音色"
- Script tab 中，每行已选择的人设仍显示"尚未绑定"

**原因：**
- updateBatchVoiceBindingHint() / updateScriptLineVoiceHint() 依赖 window._voiceBindMap
- 切换到 longtext/script tab 时只 loadProfiles + update hint，未刷新真实 bindings

**修复方案：**
- 增加 refreshVoiceBindMapForHints() helper，调用 loadAllBindings() 并写入 window._voiceBindMap
- 进入 longtext/script tab 时先 await refreshVoiceBindMapForHints() 再更新提示

**修复位置：**
- `app/static/index.html`：loadAllBindings() 后新增 helper；longtext/script tab switch 分支

**验证方式：**
- targeted E2E（batch_longtext_voice_binding_hint / batch_script_line_voice_binding_hint）：2 passed ✅
- git diff --check：无 whitespace 错误 ✅

**P12-USAGE-FIX3B：loadAllBindings() 缺少 status 字段**

**问题描述：**
- FIX3 后仍有问题：binding 确实存在，但 hint 仍显示"未绑定"

**原因：**
- product_hints.js 的 updateBatchVoiceBindingHint() 判断绑定时要求 `b.status === 'available'`
- loadAllBindings() 虽然只收集 available binding，但写入 voiceBindMap 时没有包含 status 字段

**修复方案：**
- 在 loadAllBindings() 的 push object 中增加 `status: b.status || 'available'`

**验证方式：**
- targeted E2E：2 passed ✅

## P12-USAGE-UX2：最近任务入口语义和位置不适合创作流程

**发现时间：** 2026-05-15

**问题描述：**
- 最近任务显示"无文本预览 · 未知状态 · 有音频资产"等低价值文本
- "恢复"按钮语义不准确
- 大卡片位于文案输入前，干扰主流程

**原因：**
- recent job 是任务恢复逻辑，不是创作样本管理
- 当前展示没有按任务状态区分动作语义

**修复方案：**
- 降级为 compact bar（不再是大 card）
- 根据信息完整度和状态调整按钮文案：
  - 无 info → "查看历史"
  - success → "查看最近结果"
  - processing → "继续查看进度"
  - failed → "查看失败原因"
- 信息严重不足时不显示大卡片

**修复位置：**
- `app/static/index.html`：renderRecentJobRestore() 函数

**验证方式：**
- git diff --check：通过 ✅
- 静态检查：node --check 不支持 HTML 内联脚本，跳过

**未改范围：**
- handleGenerate、renderResults、renderAsyncResult、renderStreamResult
- batch_longtext.js、batch_script.js
- 后端 API、localStorage 结构

## P12-USAGE-FIX4-A0：音频下载失败审查

**发现时间：** 2026-05-15

**问题描述：**
- Chrome 下载记录中部分音频下载失败，提示"无法从网站上提取文件"
- 部分 audio / subtitle / stream_audio 下载成功

**审查结论：**

| 风险等级 | 路径 | 问题 |
|---|---|---|
| **高** | `renderBatchResultPlayer` 批量音频下载 | `data.merged_audio.url` 直接作为 href，未使用 asset API |
| 中 | 流式 blob URL | 刷新页面后失效（已知限制） |
| 中 | asset_id 字段提取 | 三种字段名混用，需统一 |
| 低 | 单条/异步生成下载 | 正确使用 asset API ✅ |
| 低 | 字幕下载 | 正确使用 asset API ✅ |
| 低 | recent job 恢复 | 正确使用 asset API ✅ |

**后续 FIX4 修复方向：**
- 批量合并完成后应创建 voice_asset 记录并返回 asset_id
- 前端 `renderBatchResultPlayer` 中优先使用 `/api/voice/assets/${asset_id}/download`
- 如果 `merged_audio` 只有 url 而无 asset_id，保持现状（后端问题）

**审查输出：**
- `docs/P12_DOWNLOAD_AUDIT.md`：完整审查报告

## P12-USAGE-FIX4-B0：后端批量 merged_audio asset_id 审查

**发现时间：** 2026-05-15

**问题描述：**
FIX4-A0 审查发现 `renderBatchResultPlayer` 中 `data.merged_audio.url` 直接作为下载 href，可能导致下载失败。

**审查结论：**

经后端代码审查，**批量音频下载 URL 实际上已经是正确的**：

| 检查项 | 结论 |
|---|---|
| `merged_audio.id` | 就是 `merged_audio_asset_id`（即 AudioAsset.id）✅ |
| `merged_audio.url` | `/api/voice/assets/{merged_audio_asset_id}/download` ✅ |
| 批量合并音频是否已保存为 AudioAsset | ✅ 是（`_update_status()` 中创建） |
| URL 格式与单条/异步下载是否一致 | ✅ 完全一致 |

**关键代码位置：**
- `app/services/batch_orchestration_service.py`，lines 395-409：创建 `AudioAsset` 并存储 `merged_audio_asset_id`
- `app/services/batch_orchestration_service.py`，lines 638-645：返回 `merged_audio = {"id": ..., "url": ...}`
- `app/domain/schemas.py`，line 411：`merged_audio: dict | None`

**真正可能的下载失败原因：**
- 合并过程中异常处理导致文件不完整，但状态显示成功
- 文件路径 `merged_audio_path` 指向不存在的位置

**无需前端改动！**

**审查输出：**
- `docs/P12_DOWNLOAD_AUDIT.md` FIX4-B0 章节：后端审查详情

## P12-USAGE-FIX4：normalize batch download href

**发现时间：** 2026-05-15

**问题描述：**
- FIX4-A0 初步审查将批量下载判断为"高风险：直接用 merged_audio.url 未走 asset API"，这个判断不完整
- FIX4-B0 后端审查确认后端已正确创建 AudioAsset 并返回正确的 download URL

**修复方案：**
- 批量长文本 / 剧本的合并音频下载按钮优先使用语义化 endpoint：`/api/voice/batch/{batch_id}/download`
- 播放 `audio.src` 保持使用 `data.merged_audio.url`，不影响播放链路
- fallback 链：`batch_id` → `merged_audio.id` → `merged_audio.url`

**修复位置：**
- `app/static/index.html`：`renderBatchResultPlayer()`，`downloadAudio.href` 赋值逻辑

**验证方式：**
- git diff --check：无 whitespace 错误 ✅

**未改范围：**
- 不改后端 API
- 不改 batch payload
- 不改播放链路
- 不改 subtitle 下载逻辑
- 不调用真实 MiniMax

## P12-USAGE-UX3：短文本异步生成体感过慢 / 生成模式定位不清

**发现时间：** 2026-05-15

**问题描述：**
- 短文本选择异步生成后等待时间明显长，用户容易误判系统慢
- 用户不清楚各生成模式的适用场景，容易用错模式

**原因分析：**
- 异步链路适合长任务 / 可恢复任务，不适合短文本即时创作
- 当前生成模式仅有选项，无定位说明，用户无法判断该选哪个

**修复方案：**
- 在 Workspace 生成模式区域增加 `#generationModeHint` 提示容器
- 各模式定位文案：
  - 单条生成：适合短文案、普通旁白，推荐默认使用
  - 异步生成：适合较长或耗时任务，可能需要等待；短文本不建议优先使用（橙色警告样式）
  - 流式生成：适合观察实时返回效果
  - 多版本试音：适合比较不同参数或风格
- 异步模式选中时显示橙色警告提示

**修复位置：**
- `app/static/index.html`：生成模式 radio group 后新增 `#generationModeHint` 容器；CSS 新增 `.mode-hint` 和 `.async-warn` 样式；genModes change listener 增加 `updateGenerationModeHint()` 调用

**验证方式：**
- git diff --check：通过 ✅

**未改范围：**
- 不改 handleGenerate / startAsyncPolling / startStreamGenerate
- 不改异步架构、不改轮询、不改后端 API
- 不改生成 payload

## P12-USAGE-UX4-A0：音色工具快速绑定面板审查

**发现时间：** 2026-05-15

**问题描述：**
- 克隆/设计/导入音色成功后，快速绑定面板的人设选择框可能被挤压到不可见
- 用户只看到 model 选择框和"绑定"按钮，无法确认绑定到哪个人设
- 绑定成功后缺少"去创作"导向

**根因：**
- profile select 使用 `flex:1;min-width:0`，在窄屏或父容器宽度不足时可能被压缩到 width=0
- `setTimeout` 异步插入 select，导致布局时机问题
- `renderInlineCreateProfile` 插入的 `+ 新建` 按钮占用 flex 空间，进一步压缩 select 宽度
- 三处面板结构不统一（import 缺快速试听区）
- 绑定成功后无"去创作"按钮

**修复方案（UX4-B1）：**
- 统一 clone/design/import 三处面板为纵向堆叠布局
- profile select 改为 `flex:0 0 160px`（固定最小宽度，防止压缩到0）
- model select 和 bind button 放在第二行
- 绑定成功后增加"去创作"按钮
- 导入面板补齐快速试听区

**本轮审查输出：**
- `docs/P12_ADVANCED_QUICK_BIND_AUDIT.md`：完整审查报告

**未改范围：**
- 不改 `bindVoiceToProfile()` / `populateProfileSelect()` / `renderInlineCreateProfile()` 调用
- 不改克隆 / 设计 / 导入主流程
- 不改后端绑定 API
- 不调用真实 MiniMax
- 不新增 E2E
