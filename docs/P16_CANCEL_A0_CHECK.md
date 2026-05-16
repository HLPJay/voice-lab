# P16-CANCEL-A0-CHECK：取消确认与生成状态问题复核

## 1. 阶段背景

P16-REAL-USAGE-ISSUES-A0 完成了真实使用问题统一审查，识别了流式取消卡死、高消费入口 confirm 不统一、确认前副作用等 P0 问题。本阶段对审查结论进行代码事实复核，确认问题属实后进入 P16-CANCEL-FIX1。

## 2. 复核范围

基于 `origin/dev` 当前代码，验证 P16-REAL-USAGE-ISSUES-A0 中的问题描述是否与实际代码一致。

## 3. 代码事实复核

### 3.1 handleGenerate 执行顺序

**文件**：`index.html` lines 3220-3260

**确认事实**：

```javascript
// lines 3220-3224
if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
stopAsyncPolling();           // ← confirm 前已停止旧轮询
setLoading(true);              // ← confirm 前已禁用按钮
resultsArea.innerHTML = '';    // ← confirm 前已清空结果

// line 3234-3236
if (isStream) {
  startStreamGenerate(...);     // ← cancel 后 handleGenerate 直接 return，无 setLoading(false)
  return;
}

// lines 3255-3260
if (isAsync) { endpoint = '/api/voice/render/async'; operation = 'async_render'; }
else if (isVariant) { endpoint = '/api/voice/variants/render'; operation = 'voice_variants'; }
else { endpoint = '/api/voice/render'; operation = 't2a'; }  // ← t2a 不在 _OPERATION_MESSAGES 中

const resp = await guardedJsonFetch(endpoint, payload, { provider, operation, highRisk: true });
// ↑ guardedJsonFetch 内部才弹 confirm，此时 setLoading/resultsArea/stopAsyncPolling 已执行
```

**结论**：确认。`handleGenerate()` 在 `guardedJsonFetch` 内部弹 confirm 之前，已执行 `setLoading(true)` / `stopAsyncPolling()` / `resultsArea.innerHTML = ''`。

### 3.2 流式取消卡死

**文件**：`index.html` lines 3299-3301

**确认事实**：

```javascript
function startStreamGenerate(text, profileId, provider, subtitle, audioFormat, voiceParams) {
  if (provider === 'minimax' && !confirm('流式生成会调用云端 TTS，可能产生费用，是否确认继续？')) {
    return;  // ← cancel 直接 return，无 setLoading(false)
  }
  // ...后续 WebSocket 建立...
}
```

`handleGenerate()` 在调用 `startStreamGenerate()` 之前已执行 `setLoading(true)`（line 3222）。`startStreamGenerate()` 取消后直接 return，无任何 `setLoading(false)` 路径。

**结论**：确认。流式取消后按钮卡死在"生成中…"状态。

### 3.3 取消前停止旧轮询

**文件**：`index.html` lines 3221 / 3168-3171

**确认事实**：

`handleGenerate()` line 3221 执行 `stopAsyncPolling()`，其定义（line 3168）：

```javascript
function stopAsyncPolling() {
  clearAsyncPollingTimer();
  asyncPollingState.stopped = true;  // ← 标记已停止，不再自动轮询
}
```

此调用在 `guardedJsonFetch` 内部 confirm **之前**。如果用户取消，旧异步轮询已被停止。

**结论**：确认。如果用户在 confirm 对话框点取消，`stopAsyncPolling()` 已执行，旧轮询被停止。

### 3.4 t2a 确认缺口

**文件**：`index.html` lines 2832-2843 / 3258

**确认事实**：

`_OPERATION_MESSAGES` 当前定义（line 2832）：

```javascript
const _OPERATION_MESSAGES = {
  voice_design: ...,      // ✓
  voice_clone: ...,       // ✓
  provider_voice_preview: ...,         // ✓
  provider_voice_import_verify: ...,   // ✓
  binding_voice_preview: ...,          // ✓
  voice_variants: ...,    // ✓
  batch_longtext: ...,    // ✓
  batch_script: ...,      // ✓
  async_render: ...,      // ✓
  stream_render: ...,     // ✓
  // ← 没有 t2a
};
```

`handleGenerate()` 对非 async/variant 单条使用 `operation = 't2a'`（line 3258），但 `t2a` 不在 `_OPERATION_MESSAGES` 中。`guardedJsonFetch` 判断逻辑（line 2847）：

```javascript
if (provider === 'minimax' && highRisk && _OPERATION_MESSAGES[operation]) {
  if (!confirm(_OPERATION_MESSAGES[operation])) { throw new Error('USER_CANCELLED'); }
}
```

由于 `_OPERATION_MESSAGES['t2a']` 为 `undefined`，条件不满足，普通单条 minimax TTS 不会弹确认。

**结论**：确认。普通单条 minimax TTS（mode=single）无费用确认提示。

### 3.5 quick preview 绕过确认

**文件**：`voice_clone.js` line 321 / `voice_design.js` line 179 / `voice_import.js` line 184

**确认事实**：

三个 quick preview 全部直接 `fetch`，不走 `guardedJsonFetch`：

```javascript
// voice_clone.js line 321
var r = await fetch('/api/voice/render', {
  method: 'POST',
  body: JSON.stringify({ text: text, profile_id: profileId, provider: provider }),
});

// voice_design.js line 179
var resp = await fetch('/api/voice/render', { ... });

// voice_import.js line 184
fetch('/api/voice/render', { ... }).then(...);
```

当 `provider = 'minimax'` 时，这本质是 TTS 调用，但完全绕过了费用确认。

**结论**：确认。quick preview 绕过 `guardedJsonFetch`，对 minimax 无确认提示。

### 3.6 guardedJsonFetch 入口确认前副作用横向确认

**文件**：各 JS 模块

| 入口 | 走 guardedJsonFetch | confirm 前 setLoading | confirm 前清结果 | confirm 前停轮询 | confirm 前禁用按钮 |
|---|---|---|---|---|---|
| workspace single（index.html line 3260） | ✓ | ✓（line 3222） | ✓（line 3224） | ✓（line 3221） | ✓（via setLoading） |
| workspace async（index.html line 3260） | ✓ | ✓ | ✓ | ✓ | ✓ |
| workspace variants（index.html line 3260） | ✓ | ✓ | ✓ | ✓ | ✓ |
| workspace stream（index.html line 3234） | —（独立 confirm） | ✓（外层 line 3222） | ✓ | ✓ | ✓ |
| batch_longtext（batch_longtext.js line 45） | ✓ | ✓（line 40 btn.disabled） | ✓（line 42 clearResult） | — | ✓ |
| batch_script（batch_script.js） | ✓ | ✓ | ✓ | — | ✓ |
| clone quick preview（voice_clone.js line 321） | ✕（直接 fetch） | — | — | — | — |
| design quick preview（voice_design.js line 179） | ✕（直接 fetch） | — | — | — | — |
| import quick preview（voice_import.js line 184） | ✕（直接 fetch） | — | — | — | — |

所有走 `guardedJsonFetch` 的入口在 confirm 前都有副作用。

### 3.7 多版本等待态缺失

**文件**：`index.html` lines 3257 / 3278 / 3671-3718

**确认事实**：

多版本走 `guardedJsonFetch('/api/voice/variants/render', ...)`，是同步 HTTP 请求。`setLoading(true)`（line 3222）在请求前已执行。`renderResults(data, true)`（line 3278）只在接口返回后才渲染。接口返回前 resultsArea 为空（已清空），无等待态卡片。

**结论**：确认。多版本试音接口返回前无等待态卡片。

### 3.8 workspace 样本恢复缺口

**文件**：`sample_sidebar.js` lines 457-466 / `index.html` lines 2457-2493

**确认事实**：

`fillTextInput(text)` 只写 `#textInput`：

```javascript
function fillTextInput(text) {
  var input = document.getElementById('textInput');
  if (input) { input.value = text; input.focus(); input.dispatchEvent(new Event('input')); }
}
```

`buildWorkspaceSampleContext()` 只保存：`text_preview / profile_id / profile_name / provider / model / job_id / audio_format / voice_id / voice_name`，不保存：`speed / vol / pitch / emotion / need_subtitle / genMode / outputFormat / variantCount`。

**结论**：确认。当前 ↓ 是"填入文本"，不是"恢复完整工作台配置"。

## 4. 问题分级确认

| 优先级 | 问题 | 复核结论 |
|---|---|---|
| P0 | 流式取消后按钮卡死 | 确认：startStreamGenerate cancel 无 setLoading(false) |
| P0 | 确认前 setLoading(true)/清空 resultsArea/stopAsyncPolling | 确认：handleGenerate lines 3220-3224 |
| P0 | t2a 普通单条无确认 | 确认：t2a 不在 _OPERATION_MESSAGES |
| P0 | quick preview 绕过确认（minimax TTS） | 确认：voice_clone/design/import quick preview 直接 fetch |
| P1 | 多版本试音无等待态 | 确认：variants 同步请求，接口返回前 resultsArea 空白 |
| P1 | workspace 样本只能恢复文本 | 确认：fillTextInput 只写 textInput，无参数恢复 |

## 5. P16-CANCEL-FIX1 推荐边界

### 5.1 应纳入

1. 流式取消：`startStreamGenerate()` cancel 后 handleGenerate 应 `setLoading(false)`；或将 confirm 移到 `setLoading` 之前
2. t2a 确认：加入 `_OPERATION_MESSAGES['t2a'] = '...'`
3. quick preview 确认：voice_clone/design/import quick preview 改走 `guardedJsonFetch` 或统一确认 helper
4. 确认前副作用统一：先 confirm，通过后再 setLoading(true) / 清 resultsArea / stopAsyncPolling()
5. cancel 语义：取消后 UI 保持不变，不发请求，不写 recent job / SampleStore / ContextStore

### 5.2 不纳入

- workspace 参数完整恢复（→ P16-WORKSPACE-RESTORE-A0）
- SampleStore schema 扩展
- 剧本参数增强
- 小说转剧本
- 统计模块
- 后端任务模型改造

### 5.3 可选纳入

多版本等待态可并入 P16-CANCEL-FIX1，或拆到 P16-VARIANTS-UX-FIX1。

## 6. 不进入范围

剧本工作台扩展优化暂不进入 P16-CANCEL-FIX1 范围。

## 7. 复核结论

**通过**。所有 A0 问题描述均与实际代码一致，P16-CANCEL-FIX1 边界清晰，可以进入修复实现。
