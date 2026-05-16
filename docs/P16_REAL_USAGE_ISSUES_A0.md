# P16-REAL-USAGE-ISSUES-A0：真实使用问题统一审查

## 1. 阶段背景

P15 统计模块已完成设计/审查/Backlog 归档。用户真实使用中发现多个问题，本次统一审查问题根因、影响范围和优先级，确定后续修复阶段拆分。

## 2. 审查范围

- `index.html` 主要生成链路（handleGenerate / startStreamGenerate / guardedJsonFetch）
- `sample_sidebar.js` 样本恢复逻辑（fillTextInput）
- `voice_clone.js` quick preview 直接 fetch

## 3. 排除范围

**剧本工作台扩展优化暂不进入 P16 当前修复范围，后续产品需要时再单独启动。**

不处理：剧本角色默认参数 / 剧本逐行 speed/vol/pitch/emotion / 小说转剧本 / 广播剧增强。

## 4. 问题总览

| 优先级 | 问题 |
|---|---|
| P0 | 流式生成取消后按钮卡死 |
| P0 | 高消费入口 confirm 逻辑不统一（t2a 无确认 / quick preview 绕过） |
| P0 | 确认前 UI 已清空 resultsArea / setLoading(true) |
| P1 | 多版本试音无等待态卡片 |
| P1 | Workspace 最近样本只能恢复文本，不能恢复参数 |
| P2 | NEXT_TASKS 残留已完成项 |

## 5. P0 问题

### 5.1 流式生成取消后按钮卡死

**文件**：`index.html` lines 3201-3337

**根因**：`handleGenerate()` 在调用 `startStreamGenerate()` **之前**就已执行 `setLoading(true)`（line 3222）。`startStreamGenerate()` 有独立的 `confirm`（line 3300），用户点取消后直接 `return`（line 3301），但 `handleGenerate()` 没有 `setLoading(false)` 的 fallback 路径，导致按钮保持 disabled。

```javascript
// handleGenerate lines 3220-3236
if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
stopAsyncPolling();
setLoading(true);          // ← 确认前就 setLoading
resultsArea.innerHTML = '';

if (isStream) {
  startStreamGenerate(...); // ← cancel 后直接 return，无 setLoading(false)
  return;
}
```

**确认取消后行为**：
- resultsArea 已被清空（line 3224）
- stopAsyncPolling() 已执行（line 3221），旧轮询已停止
- setLoading(true) 未被撤销
- 按钮保持 "生成中…" 状态

**修复方向**：取消 = 无副作用。取消后不 setLoading，不清空 resultsArea，不停止旧轮询。

### 5.2 高消费入口 confirm 逻辑不统一

**文件**：`index.html` lines 2832-2843

`_OPERATION_MESSAGES` 当前定义：

| operation | 确认文案 | 入口 |
|---|---|---|
| voice_design | 声音设计会调用云端模型… | clone/design quick preview |
| voice_clone | 声音克隆会调用云端模型… | clone/design quick preview |
| provider_voice_preview | 真实试听会调用云端 TTS… | voice list preview |
| binding_voice_preview | 试听会调用云端 TTS… | binding preview |
| voice_variants | 多版本试音会多次调用云端 TTS… | workspace variants |
| batch_longtext | 批量生成会调用云端 TTS… | batch longtext |
| batch_script | 剧本批量生成会调用云端 TTS… | batch script |
| async_render | 异步生成会调用云端 TTS… | workspace async |
| stream_render | 流式生成会调用云端 TTS… | —（stream 用独立 confirm） |

**缺口 1：`t2a` 普通单条无确认**

`handleGenerate()` 中普通单条使用 `operation = 't2a'`（line 3258），但 `t2a` 不在 `_OPERATION_MESSAGES` 中。因此普通单条生成（mode=single，provider=minimax）没有费用确认提示。

**缺口 2：quick preview 绕过 confirmed**

`voice_clone.js` line 321 的 quick preview：

```javascript
var r = await fetch('/api/voice/render', {
  method: 'POST',
  body: JSON.stringify({ text: text, profile_id: profileId, provider: provider }),
});
```

直接 `fetch`，不走 `guardedJsonFetch`，完全绕过费用确认。对 `provider=minimax` 的真实 TTS 调用无任何提示。

### 5.3 确认前 UI 已清空 resultsArea / setLoading(true)

**文件**：`index.html` lines 3220-3260

`handleGenerate()` 在调用 `guardedJsonFetch` 之前就执行了：

1. `stopAsyncPolling()`（line 3221）— 停止旧任务轮询
2. `setLoading(true)`（line 3222）— 禁用按钮
3. `resultsArea.innerHTML = ''`（line 3224）— 清空结果区

这意味着用户看到 confirm 对话框之前，results 已经被清空、按钮已经被禁用。如果用户取消，只有 variants/async/single 在 catch 中调用 `setLoading(false)`；stream 没有（见 5.1）。

**后续修复原则**：先确认，再进入 loading，再清空结果区，再停止旧任务。

## 6. P1 问题

### 6.1 多版本试音无等待态卡片

**文件**：`index.html` lines 3257-3278

多版本试音 endpoint 为 `/api/voice/variants/render`，是同步 HTTP 请求。`handleGenerate()` 调用 `guardedJsonFetch` 后等待响应，期间：

- `setLoading(true)` 已执行（按钮显示"生成中…"）
- resultsArea 为空（已清空）
- 无等待态卡片（如"多版本生成中，请勿重复提交"）

`renderResults(data, true)`（line 3278）只在接口返回**后**才渲染结果（line 3671-3718）。

**修复方向**：确认通过后立即显示"多版本试音生成中"状态卡片，显示版本数量、Provider 可能较慢、不重复提交。第一版不需要实时进度百分比。

### 6.2 Workspace 最近样本只能恢复文本，不能恢复参数

**文件**：`sample_sidebar.js` lines 455-466 / `index.html` lines 2457-2493

右侧样本 ↓ 按钮（`sample-btn-fill`）调用 `fillTextInput(text)`，只写入 `#textInput`：

```javascript
function fillTextInput(text) {
  var input = document.getElementById('textInput');
  if (input) {
    input.value = text;
    input.focus();
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }
}
```

`buildWorkspaceSampleContext`（line 2457）当前保存的字段：

- `text_preview` / `profile_id` / `profile_name` / `provider` / `model` / `job_id` / `audio_format` / `voice_id` / `voice_name`

**缺失参数**：speed / vol / pitch / emotion / need_subtitle / genMode / outputFormat / variantCount

`SampleStore` schema 可扩展字段支持可选 `workspace_params`，但本阶段不改 Store schema。

### 6.3 确认前 UI 副作用

横向审查所有入口的确认前副作用（`index.html`）：

| 入口 | setLoading(true) 在 confirm 前 | 清空 resultsArea 在 confirm 前 | 停止旧轮询在 confirm 前 |
|---|---|---|---|
| workspace single | ✓ | ✓ | ✓ |
| workspace async | ✓ | ✓ | ✓ |
| workspace variants | ✓ | ✓ | ✓ |
| workspace stream | ✓（外层） | ✓ | ✓ |
| batch longtext | ✓ | ✓ | ✓ |
| batch script | ✓ | ✓ | ✓ |
| voice clone preview | —（直接 fetch） | — | — |
| voice design preview | —（直接 fetch） | — | — |

所有走 `guardedJsonFetch` 的入口在确认前都有副作用。quick preview 直接 fetch，无确认也无副作用（但绕过了安全提示）。

## 7. P2 问题

### 7.1 NEXT_TASKS 残留已完成项

**文件**：`docs/agent/NEXT_TASKS.md` line 130

`P14-CONTEXT-C2-FIX3-CHECK` 已在完成列表中标记 ✅，但仍出现在 Next 表中。应从 Next 表移除。

**清理项**：NEXT_TASKS-OBS-001：Next 表残留 `P14-CONTEXT-C2-FIX3-CHECK`，建议移除。

## 8. 修复优先级建议

| 优先级 | 问题 | 修复收益 |
|---|---|---|
| P0-FIX1 | 流式生成取消后按钮卡死 | 避免用户卡在生成态 |
| P0-FIX2 | t2a 普通单条无确认提示 | 避免无感费用 |
| P0-FIX3 | quick preview 绕过确认 | 避免试听无感费用 |
| P0-FIX4 | 确认前 UI 副作用 | 统一语义，减少用户困惑 |
| P1-FIX1 | 多版本试音无等待态 | 减少重复提交 |
| P1-FIX2 | Workspace 样本只能恢复文本 | 提升恢复完整度 |

## 9. 后续阶段拆分建议

### 推荐顺序

1. **P16-CANCEL-A0-CHECK**：复核取消/确认问题审查结论
2. **P16-CANCEL-FIX1**：修复取消确认语义和 loading 卡死
   - 流式取消 setLoading(false)
   - 确认前不 setLoading
   - 确认前不清空 resultsArea
   - 确认前不停止旧轮询
   - t2a 确认策略明确（加入 _OPERATION_MESSAGES 或确认范围）
   - quick preview 统一确认
3. **P16-VARIANTS-UX-FIX1**：补充多版本试音等待态（可并入 P16-CANCEL-FIX1）
4. **P16-WORKSPACE-RESTORE-A0**：审查 workspace 样本完整恢复方案
5. **P16-WORKSPACE-RESTORE-B1**：实现 workspace 样本恢复参数

### 可并行方向

- P13-HISTORY-SECURITY-FIX1（小型安全债，可独立处理）
- P15-STATS-Backlog 方向A/B（产品需要时启动）

## 10. 结论

P16 真实使用问题审查完成。P0 问题（流式取消卡死 / confirm 不统一 / 确认前副作用）需优先修复，P1 问题（多版本等待态 / Workspace 样本参数恢复）次之。所有修复均可在现有 `index.html` + `sample_sidebar.js` 范围内完成，不涉及后端或 Store schema 变更。

剧本工作台扩展优化暂不进入当前修复范围。
