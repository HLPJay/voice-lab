# P14-CONTEXT-C1-A0：剧本 context 保存与详情查看前置审查

## 1. 背景

P14-CONTEXT-B3 已完成长文本 context 的保存与一键回填。当前 `batch_longtext.js` 已接入 `ContextStore.pushContext`，`SampleSidebar` 已支持 longtext 详情面板和恢复按钮。

本阶段审查剧本（script）context 的保存与详情查看前置条件，评估 C1 实现阶段的可行性和风险。

## 2. 当前代码事实

### 2.1 batch_script.js 当前链路

`batch_script.js` 在 `handleBatchScriptSubmit` 中：

1. 收集 `_scriptRows` 中的有效行（lines）
2. 构造 `mode: 'script'` 的 submit payload
3. 调用 `guardedJsonFetch('/api/voice/batch/submit', { mode: 'script', script: lines, ... })`
4. `resp.ok` 后：
   - `var data = await resp.json()`
   - `_currentBatchId = data.batch_id`
   - 创建 `_batchSampleContextById[data.batch_id]`（包含 source/mode/text_preview/provider/profile_id/audio_format 等）
   - 调用 `showBatchProgress(data.batch_id, 'batchScriptProgressPanel')`
   - 调用 `startBatchPoll(data.batch_id, 'batchScriptProgressPanel')`
   - 调用 `loadRuntimeStatus()`

**当前未调用 `ContextStore.pushContext()`**。这是 C1 需要补充的核心接入点。

### 2.2 ContextStore script normalize 能力

`context_store.js` 当前已实现 `normalizeScriptContext(input, out)`：

**支持字段：**
- `lines[]`：每行 `{ role, text, profile_id, params: {} }`，上限 `MAX_SCRIPT_LINES = 200`
- `provider`
- `silence_between_ms`（默认 500，上限 3000）
- `output_format`（默认 'hex'）
- `audio_format`（默认 'mp3'）
- `need_subtitle`

**normalizeScriptContext 现状：**
- `params` 字段固定为空对象 `{}`（当前 script UI 无行级 params 输入）
- 不保存行级 speed / emotion / vol / pitch
- 不保存 `batch_id`（需要手动设置：`out.batch_id = input.batch_id` 已在 `normalizeContext` 中统一处理）

**判断：ContextStore.normalizeScriptContext 基本足够支撑 C1，但需确认 `batch_id` 是否被 normalizeContext 正确传递。**

### 2.3 sample_store.js context_id 透传能力

`safePushBatchSample(source, data, extra = {})` 当前已有：
```js
context_id: extra.context_id || null,
```

`extra` 参数来自 `_batchSampleContextById[data.batch_id]`。longtext B2 实现已将 `context_id` 回填到 `_batchSampleContextById`，因此 script merged sample 的 `context_id` 透传链路已就绪。

**判断：sample_store.js 无需修改，`context_id` 透传机制已就绪。**

### 2.4 sample_sidebar.js 现状

`showSampleDetail(sampleId)` 当前：
- 调用 `ContextStore.getContext(contextId)` 获取 context
- 当 context 为 null 时显示"完整上下文不可用"
- 当 context 存在时渲染详情面板
- 当 `context.type === 'longtext'` 时显示"恢复到长文本"按钮

**判断：showSampleDetail 可以展示 script context，但当前缺少 `context.type === 'script'` 时的 lines 渲染逻辑。**

## 3. script context 字段设计

C1 阶段 `ContextStore.pushContext` 应传入字段：

| 字段 | 来源 | 说明 |
|------|------|------|
| `context_id` | `data.batch_id` | 与 longtext B2 策略一致 |
| `type` | `'script'` | 固定值 |
| `source` | `'batch_script_merged'` | 固定值 |
| `lines` | 当前提交的 lines（与 submit payload 相同） | 含 role / text / profile_id / params: {} |
| `provider` | `#batchScriptProvider.value` | |
| `silence_between_ms` | `#batchScriptSilence.value` | |
| `output_format` | `'hex'` | 固定，与 submit 一致 |
| `audio_format` | `#batchScriptOutputFormat.value` | |
| `need_subtitle` | `#batchScriptNeedSubtitle.checked` | |
| `batch_id` | `data.batch_id` | |

**不保存字段：**
- `profile_id`（script 每行独立 profile，无单一 profile_id）
- `model` / `voice_id` / `voice_name`（每行独立）
- 行级 `params`（当前 UI 无输入）

## 4. context_id 策略

```
context_id = data.batch_id
```

**理由：**
- 与 longtext B2 策略完全一致
- batch merged sample 的 job_id / batch_id 共用同一个 batch_id
- 无需额外生成 UUID
- `_batchSampleContextById[data.batch_id].context_id = data.batch_id` 在 ContextStore 保存后回填
- `safePushBatchSample` 已通过 `extra.context_id` 透传

## 5. 保存位置与 fail-safe 策略

参考 longtext B2 的实现模式。

在 `batch_script.js` 的 `handleBatchScriptSubmit` 中，`resp.ok` 且 `data.batch_id` 存在后：

```js
// 已有：_batchSampleContextById[data.batch_id] 创建（lines 152-167）

// 新增：保存 script context 到 ContextStore（fail-safe）
try {
  if (window.ContextStore && typeof window.ContextStore.pushContext === 'function' && data && data.batch_id) {
    var contextId = data.batch_id;
    window.ContextStore.pushContext({
      context_id: contextId,
      type: 'script',
      source: 'batch_script_merged',
      lines: lines,  // 当前提交的 lines 数组
      provider: provider,
      silence_between_ms: silence,
      output_format: 'hex',
      audio_format: outputFormat,
      need_subtitle: needSubtitle,
      batch_id: data.batch_id,
    });
    // 回填 context_id 到 _batchSampleContextById，供 safePushBatchSample 透传
    if (window._batchSampleContextById && window._batchSampleContextById[data.batch_id]) {
      window._batchSampleContextById[data.batch_id].context_id = contextId;
    }
  }
} catch (e) {
  // fail-safe: context save must not block batch generation
}

// 已有：showBatchProgress / startBatchPoll / loadRuntimeStatus
showBatchProgress(data.batch_id, 'batchScriptProgressPanel');
startBatchPoll(data.batch_id, 'batchScriptProgressPanel');
loadRuntimeStatus();
```

**要求：**
- context 保存必须在 `showBatchProgress` 之前
- 保存失败不应阻塞 batch 生成
- 必须 try/catch fail-safe
- 不应改变 submit payload
- 不应改变 `showResult` 成功提示
- 不应改变 `showBatchProgress` / `startBatchPoll` 参数

## 6. SampleSidebar script 详情展示策略

C1 实现阶段需修改 `showSampleDetail` 的 HTML 生成逻辑。

当 `context.type === 'script'` 时，详情面板应展示：

```
来源: 剧本合并
行数: N
Provider: xxx
音频格式: mp3
字幕: 是/否
段间静音: xxxms

台词列表:
[角色名] 台词文本
[角色名] 台词文本
...
```

**具体实现：**
- `context.lines` 遍历渲染
- 每行显示：role + text（使用 `white-space: pre-wrap` 保留格式）
- 每行附显示 profile_id（如果有）
- 所有展示字段使用 `esc()` 转义
- lines 区域高度限制（如 `max-height: 300px; overflow-y: auto`）
- 显示"剧本行数"元数据
- `context.type === 'script'` 时不显示"恢复到长文本"按钮（C2 再做"恢复到剧本"）

**按钮策略：**
- `context.type === 'longtext'` → 显示"恢复到长文本"
- `context.type === 'script'` → 不显示任何恢复按钮（C1 不实现回填）
- 按钮均使用 `data-context-id`（attr() escape）

## 7. C1 实现文件白名单建议

建议 C1 允许修改：

| 文件 | 修改范围 |
|------|---------|
| `app/static/js/batch_script.js` | 在 submit 成功后调用 ContextStore.pushContext，回填 context_id |
| `app/static/js/sample_sidebar.js` | showSampleDetail 增加 script lines 详情渲染；恢复按钮条件更精确 |
| `app/static/index.html` | 如需为 script 详情面板增加 CSS，仅限 SampleSidebar 样式区 |
| `tests/test_sample_sidebar_static.py` | 新增 script 详情展示测试 |
| `tests/test_context_store_longtext_integration_static.py` | 新增 script context 保存集成测试 |
| `docs/PROJECT_HEALTH_CHECK.md` | 追加 C1 章节 |
| `docs/agent/NEXT_TASKS.md` | 更新当前阶段和已完成列表 |

**建议原则上不修改：**
- `app/static/js/context_store.js`（normalizeScriptContext 已足够）
- `app/static/js/sample_store.js`（context_id 透传已就绪）
- `app/static/js/batch_longtext.js`（longtext 已稳定）

## 8. C1 测试计划

### 8.1 batch_script context 保存测试

**静态测试（test_context_store_longtext_integration_static.py 新增 script 部分）：**
- `batch_script.js` 调用 `ContextStore.pushContext`
- 仅在 `resp.ok` 且 `data.batch_id` 存在后保存
- `type: 'script'`
- `source: 'batch_script_merged'`
- `context_id = data.batch_id`
- `batch_id = data.batch_id`
- 保存 `lines`（与 submit payload 一致）
- 保存 `provider`
- 保存 `silence_between_ms`
- 保存 `output_format: 'hex'`
- 保存 `audio_format`
- 保存 `need_subtitle`
- try/catch fail-safe 包裹
- 写入失败不阻塞 `showBatchProgress`
- `_batchSampleContextById[data.batch_id].context_id` 在 polling 前写入

### 8.2 submit payload 不变测试

- `mode: 'script'` 不变
- `script: lines` 不变
- `provider` 不变
- `silence_between_ms` 不变
- `output_format: 'hex'` 不变
- `audio_format` 不变
- `need_subtitle` 不变
- `confirm_cost: false` 不变

### 8.3 SampleSidebar script 详情测试

- 有 `context_id` 的 script sample 显示详情按钮（已有条件：`sample.context_id` 存在）
- `showSampleDetail` 能读取 `ContextStore.getContext`
- `context.type === 'script'` 时展示 lines
- 展示 role / text / profile_id
- 所有展示字段使用 `esc()`
- `context.type === 'script'` 时不显示"恢复到长文本"
- `context.type === 'script'` 时不显示"恢复到剧本"
- 不调用 `fillTextInput`
- 不调用 `restoreLongtextContext`
- 不调用 fetch / API

### 8.4 旧样本兼容测试

- 无 `context_id` 的旧 script sample 不显示详情按钮
- 旧样本播放 / 下载 / 复制 / 删除不受影响

## 9. 阶段边界

**C1 实现阶段必须明确不做：**
- 不实现剧本一键回填（C2）
- 不恢复 `lines` 到 script UI
- 不调用 `addScriptLine` / `removeScriptLine`
- 不写 `scriptRole_*` / `scriptText_*` / `scriptProfile_*`
- 不修改 `_scriptRows`
- 不修改 `ContextStore` schema（normalizeScriptContext 已足够）
- 不修改 `SampleStore` schema
- 不修改 batch submit payload
- 不调用后端 API（ContextStore 是 localStorage）
- 不调用真实 MiniMax
- 不自动提交批量任务

## 10. 风险与观察项

### 风险 1（低）：lines 数据一致性问题

**描述：** context 保存时使用的 `lines` 与 submit payload 中的 `lines` 引用同一个局部变量，但如果 submit 成功后用户修改了 DOM 中的行，`lines` 变量不会同步。

**评估：** 低风险，因为 `lines` 在 submit 开头收集后就固定了，与 DOM 后续修改无关。

### 风险 2（中）：batch_id 重复覆盖

**描述：** 如果同一 batch_id 的任务被提交两次（极低概率），ContextStore 会以新 context 覆盖旧 context。

**评估：** 低风险，upsert 行为是预期内的 LRU 语义。

### 观察项 1：行级 params 暂不支持

当前 `normalizeScriptContext` 中 `params` 固定为空对象。如果未来 script UI 支持行级 speed/emotion 等参数，需要同步修改 `normalizeScriptContext`。

C1 不需要修改 schema。

### 观察项 2：script 详情面板无滚动限制验证

`lines` 上限 `MAX_SCRIPT_LINES = 200`，但详情面板的 CSS 滚动限制需要在实现时验证是否足够。

## 11. A0 结论

**P14-CONTEXT-C1 可以进入实现阶段。**

理由：
1. `batch_script.js` 已具备完整 submit 链路和 `_batchSampleContextById` 创建逻辑，只需在 polling 前增加 `ContextStore.pushContext` 调用
2. `ContextStore.normalizeScriptContext` 已支持 script context 所有必要字段，无需修改 schema
3. `sample_store.js` 的 `context_id` 透传机制已就绪，无需修改
4. `SampleSidebar.showSampleDetail` 已有展示结构，增加 `type === 'script'` 的 lines 渲染即可
5. B2 longtext 实现提供了完整的参考模式，C1 可以直接复用
6. C1 不修改 submit payload，不修改 Store schema，边界清晰

**建议下一阶段：P14-CONTEXT-C1：剧本 context 保存与详情查看实现**
