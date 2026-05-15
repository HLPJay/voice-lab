# P14 Context Restore 闭环阶段收口

## 1. 阶段目标

对 P14 "最近样本 + context 详情 + 一键恢复" 闭环进行阶段性收口，明确已完成能力、已知边界和非阻塞观察项。

## 2. 最终产品能力

Voice Lab 当前已具备：

**最近样本记录 → 上下文详情 → 长文本恢复 → 剧本恢复 → 用户继续编辑再生成** 的基础创作闭环。

用户可在剧本批量任务生成后，将样本记录到 SampleSidebar；在 SampleSidebar 中查看剧本 context 详情；通过"恢复到剧本"按钮将 context 恢复到剧本 Tab 表单；继续编辑后手动重新提交。

## 3. 最近样本侧边栏能力

### 3.1 功能清单

- 最近样本本地存储（SampleStore + localStorage）
- 侧边栏卡片展示（sample_sidebar.js）
- 样本播放（in-card audio player）
- 样本下载（安全 URL 验证）
- 样本详情（context_id → ContextStore → 详情面板）
- 复制文本
- 填入工作台（canShowFill 控制）
- 删除样本
- 清空样本
- 跨 tab storage event 刷新

### 3.2 当前按钮策略

| 条件 | 播放 | 下载 | 详情 | 复制 | 填入 | 删除 |
|---|---|---|---|---|---|---|
| 有 safe download_url | ✓ | ✓ | — | — | — | — |
| 有 context_id | — | — | ✓ | — | — | — |
| 始终 | — | — | — | ✓ | — | ✓ |
| canShowFill(source) = true | — | — | — | — | ✓ | — |
| batch_longtext_* / batch_script_* | — | — | — | — | ✕ | — |

平铺按钮：播放 / 下载 / 详情 / 复制 / 填入 / 删除，无更多菜单。

## 4. Longtext Context 闭环

### 4.1 数据流

1. `handleBatchLongtextSubmit` 成功后
2. `ContextStore.pushContext({ context_id: data.batch_id, type: 'longtext', full_text, provider, ... })`
3. `_batchSampleContextById[data.batch_id].context_id = data.batch_id`
4. `showBatchProgress / startBatchPoll`
5. 任务完成后 `safePushBatchSample` 将 `context_id` 写入 SampleStore
6. SampleSidebar 展示样本卡片（有 context_id → 显示详情按钮）
7. 用户点击详情 → `showSampleDetail` → `ContextStore.getContext(contextId)` → 渲染长文本详情
8. 用户点击"恢复到长文本" → `restoreLongtextContext` → `switchToLongtextTab` → `applyLongtextContextToForm` → 恢复所有字段 → 聚焦文本框

### 4.2 恢复字段

| Context 字段 | 目标 DOM | 说明 |
|---|---|---|
| full_text | #batchText | 完整长文本 |
| provider | #batchProvider | Provider 选择 |
| profile_id | #batchProfile | 人设 |
| segment_strategy | #batchStrategy | 分段策略 |
| max_segment_chars | #batchMaxChars | 最大分段字数 |
| silence_between_ms | #batchSilence | 段间静音 |
| audio_format | #batchOutputFormat | 音频格式 |
| need_subtitle | #batchNeedSubtitle | 是否需要字幕 |
| params.speed/vol/pitch/emotion | #batchSpeed/Vol/Pitch/Emotion | 高级参数 |

## 5. Script Context 闭环

### 5.1 数据流

1. `handleBatchScriptSubmit` 成功后
2. `ContextStore.pushContext({ context_id: data.batch_id, type: 'script', lines, provider, ... })`
3. `_batchSampleContextById[data.batch_id].context_id = data.batch_id`
4. `showBatchProgress / startBatchPoll`
5. 任务完成后 `safePushBatchSample` 将 `context_id` 写入 SampleStore
6. SampleSidebar 展示样本卡片（有 context_id → 显示详情按钮）
7. 用户点击详情 → `showSampleDetail` → `ContextStore.getContext(contextId)` → 渲染剧本详情（来源/行数/Provider/音频格式/字幕/段间静音/台词列表）
8. 用户点击"恢复到剧本" → `restoreScriptContext` → `switchToScriptBatchMode`（点击 script tab + 设置 batchMode=script + 触发 change + 显示 batchScriptPanel） → `applyScriptContextToForm` → 清空旧剧本行 + 逐行恢复 + 恢复全局参数 → 聚焦第一行

### 5.2 恢复字段

全局参数：provider / silence_between_ms / audio_format / need_subtitle

剧本行：lines[].role / lines[].text / lines[].profile_id（延迟二次设置）

不恢复：output_format（固定 'hex'）、params（行级参数 UI 无输入）

## 6. 数据边界

### 6.1 ContextStore

- 使用 localStorage key `voice_lab_contexts_v1`
- `context_id = batch_id` 一对一策略
- 保存完整上下文（longtext full_text、script lines）
- 保存失败 fail-safe，不阻塞 batch 生成流程
- 不保存音频 blob / base64 / hex

### 6.2 SampleStore

- 使用 localStorage key `voice_lab_recent_samples_v1`
- 只保存轻量索引：sample_id / text_preview / source / provider / profile_name / download_url / duration_ms / created_at / **context_id**
- context_id 由 batch_longtext.js / batch_script.js 在 polling 前回填
- 不引用 ContextStore（索引隔离）

### 6.3 限制

- 当前实现为本地单用户工作台，不承诺多用户 SaaS 一致性
- 多 tab 并发写入 localStorage 由 storage event 处理，但不保证冲突处理

## 7. 已修复问题

### 7.1 B1 更多菜单 UX 问题

问题：更多菜单收纳复制/填入/删除，用户反馈操作不方便。

处理：`P14-SIDEBAR-ACTIONS-B1-UXFIX1` 恢复平铺按钮。

### 7.2 C1 Script Detail HTML 结构问题

问题：script 详情面板中 `.sample-detail-meta` 未正确关闭，text-label 和 lines-wrap 被错误嵌套。

处理：`P14-CONTEXT-C1-FIX1` 在 `renderScriptLinesDetail` 拼接前补充 `</div>`。

### 7.3 C2 剧本恢复子面板切换问题

问题：`switchToScriptBatchMode()` 只点击了 script tab，未设置 `input[name="batchMode"][value="script"]`，导致恢复后可能仍显示 batchLongtextPanel。

处理：`P14-CONTEXT-C2-FIX1` 重构函数，移除 early return，增加 batchMode=script 设置、change 事件触发和 panel 显示 fallback。

## 8. 已知非阻塞观察项

### 8.1 B3-OBS-001

`batchProfile` 在长文本恢复时可能被异步 `populateProfileSelect` 覆盖。当前已记录，不阻塞 P14 收口。

### 8.2 B3-OBS-002

长文本恢复成功反馈较轻（仅 focus），可进一步优化 toast / hint / 面板关闭行为。不阻塞 P14 收口。

### 8.3 E2E 404

全量测试存在 voice import clone E2E 资源 404。与 P14 context restore 无关，已判断为既有环境问题。

### 8.4 Product OBS

SampleSidebar 当前是全局最近样本，不按当前 Tab 过滤。后续可进入 P14-PRODUCT-B0 设计可见性策略。

## 9. 不进入范围

- SaaS / 多用户一致性
- 移动端 H5 布局
- 后端 API 扩展
- MiniMax Provider 修改
- 数据库模型修改
- batch submit payload 修改
- 动态加载 / ES module 迁移
- React / Vue / Vite 引入

## 10. 测试与验证情况

最新测试结果（`P14-CONTEXT-C2-FIX1-CHECK`）：

```
test_sample_sidebar_static.py + test_context_store_script_integration_static.py: 223 passed
test_sample_store_batch_integration_static.py + test_existing_function_regression_static.py: 161 passed
合计: 384 passed
```

全部 P14 相关静态测试通过，无阻塞问题。

## 11. 结论

**P14 context restore 闭环阶段可以收口。**

当前 Voice Lab 已具备 "最近样本记录 → 上下文详情查看 → 长文本一键恢复 → 剧本一键恢复 → 用户继续编辑再生成" 的完整创作闭环基础能力。ContextStore / SampleStore 边界稳定，数据存储 fail-safe，恢复逻辑完整且不自动提交，SampleSidebar 平铺按钮策略已就位。

## 12. 后续建议

| 阶段 | 内容 | 前提 |
|---|---|---|
| P14-PRODUCT-B0 | 全局 SampleSidebar 可见性与过滤策略设计 | P14-CONTEXT-C2-CLOSE 完成 |
| P14-PRODUCT-B1 | 长样本预览 / 详情行为设计 | P14-PRODUCT-B0 完成 |
| P13-HISTORY-SECURITY-FIX1 | 历史文本片段转义安全修复 | P13 归档后小型安全债 |
| 后续 | SaaS / 多用户 | 产品验证后 |
