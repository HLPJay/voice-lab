# P14-PRODUCT-A0：样本复用与配置恢复产品方案审查

**日期：2026-05-15**
**前提：P13 最近样本系统已归档**

## 1. 背景

P13 将 workspace / audition / batch merged audio 统一沉淀到 SampleStore，并通过 SampleSidebar 进行轻量观察。但 P13 归档文档明确：长文本和剧本才是真实内容生产入口。当前 SampleSidebar 只在 Workspace 内可见，且只有"复制文本"和"填入工作台"（填入 workspace 的 `#textInput`），无法满足以下需求：

- 在长文本 / 剧本 tab 直接查看最近生成的完整内容
- 点击即回填到长文本或剧本 tab，保留配置继续生成
- 跨 tab 复用已有配置

P14 的目标：在 P13 基础上，将 SampleSidebar 从"观察面板"升级为"样本复用入口"。

## 2. P13 已完成能力复盘

### SampleStore 当前存储结构

```javascript
{
  sample_id, created_at,
  source, job_id, batch_id, segment_id, asset_id,
  download_url,           // null if blob URL
  text_preview,           // 最多 100 字符（P13 截断后）
  profile_id, profile_name,
  provider, model,
  voice_id, voice_name,
  duration_ms,
  audio_format,
  status, tags
}
```

**P13 SampleStore 不存储：** `full_text`、`segment_strategy`、`lines`（剧本行）、`params`（speed/vol/pitch/emotion）等配置字段。

### SampleSidebar 当前行为

- 挂载在 workspace tab 内（`#sampleSidebarRoot` 在 `#tab-workspace` 内）
- 卡片 `text_preview` 在 UI 层再截断到 60 字符
- 卡片"填入工作台"按钮调用 `fillTextInput(text)`，写入 `#textInput`（workspace 文本框）
- 点击"复制文本"调用 `copyText(text_preview)`，复制的是截断后的 preview
- 无详情弹层，无长文本完整内容查看，无剧本行查看
- 无切换到长文本 / 剧本 tab 的能力

### batch_longtext.js / batch_script.js 当前行为

- submit 成功后缓存 `window._batchSampleContextById[data.batch_id]`
- 该 context 保存了 `text_preview`、`provider`、`profile_id`、`audio_format`，但**不是完整配置**
- `full_text`（长文全文）、`segment_strategy`、`max_segment_chars` 等**未保存**
- 剧本行的 `role / text / profile_id` 数组**未保存完整结构**

## 3. 当前用户困惑

1. **在哪找之前生成的长文本？** → 只能从 SampleSidebar 看到 100 字符截断文本，无法查看完整内容
2. **之前用哪个音色和参数生成的？** → SampleStore 的 `text_preview` 不含配置信息
3. **如何基于之前的配置继续生成？** → 没有回填机制
4. **在长文本 tab 能看到最近样本吗？** → 不能，Sidebar 只在 workspace 内
5. **剧本之前每行的角色和文本能恢复吗？** → 不能，SampleStore 不保存 lines 结构

## 4. Workspace / 长文本 / 剧本的产品定位

### Workspace 定位

**Workspace / 创作工作台不应继续被视为唯一主入口。**

它更适合：
- 短文本快速生成（1～200 字）
- 单句试听
- 音色测试
- 多版本对比
- 流式体验
- 快速样本观察

### 长文本定位

**长文本是真实内容生产入口之一。**

适合：
- 文章、书摘、课程稿、口播稿、长篇旁白、知识类内容

核心价值：
- 自动分段
- 批量生成
- 合并音频
- 字幕
- 下载交付

### 剧本定位

**剧本是真实内容生产入口之一。**

适合：
- 多角色台词、对话、故事、短剧、播客脚本、情景演绎

核心价值：
- 多角色
- 多 profile
- 台词结构化
- 批量生成
- 合并音频

## 5. 最近样本侧边栏的新定位

P13 定位：

```
最近样本观察面板
```

P14 目标：

```
最近样本复用入口
```

但必须说明：

```
P14-A0 只做方案，不实现。
```

新的产品目标：

```
最近样本侧边栏应该支持：
- 快速识别样本（source 标签 + 短预览）
- 播放
- 下载
- 复制
- 查看完整文本 / 完整剧本
- 一键回填到对应模式
```

## 6. 长文本样本如何显示

### 当前问题

长文本可能长达 50000 字，不可能全部显示在侧边栏卡片内。

### 卡片显示策略

```
卡片内：
- source badge：长文合并
- 文本预览：最多 2 行，约 120～160 字符
- 超出省略号截断
- 展示 metadata：时长、provider、profile、时间
- 不在卡片内显示完整文本

示例卡片布局：
[长文合并]           3′24″
这是一个关于人工智能的
文章摘要开头文本…       Provider: minimax
张三 · 2026/5/15 14:32

[▶] [⇩] [复制] [回填] [✕]
```

### metadata 字段

卡片应展示（来自 SampleStore）：

| 字段 | 来源 |
|------|------|
| source | `source` |
| duration | `duration_ms` |
| provider | `provider` |
| profile | `profile_name` 或 `profile_id` |
| created_at | `created_at` |

## 7. 剧本样本如何显示

### 当前问题

剧本有结构化行数据（role / text / profile_id），无法用纯文本预览完整表达。

### 卡片显示策略

```
卡片内：
- source badge：剧本合并
- 文本预览：取第一行 role + "：" + text 前 100 字符 + "…"
- 总行数提示：如"5 行角色"
- 展示 metadata：总段数、provider、profile、时间
- 不在卡片内显示所有行

示例卡片布局：
[剧本合并]           2′10″
旁白：这是一个关于…
（共 5 行）          Provider: minimax
李四 · 2026/5/15 16:42

[▶] [⇩] [复制] [回填] [✕]
```

## 8. 文本过长时的显示策略

**卡片内永远只显示短预览（120～160 字符）。**

完整内容通过点击"详情"触发详情弹层 / drawer。

```
不建议使用浏览器原生 title 展示完整长文本。

原因：
- 长文本不可控（可能 50000 字）
- 体验差（title 弹出慢）
- 移动端不可用
- 无法承载剧本结构（多行多角色）
```

**推荐方案：**

```
使用详情弹层 / drawer 展示完整内容。

详情弹层内容：
- 长文本：完整 `full_text`，内部滚动
- 剧本：完整 `lines` 数组，每行显示 role + text
- 均可复制全文
- 有关闭按钮
- 点击外部关闭
```

## 9. 点击查看完整内容的交互方案

### 触发方式

在卡片上增加"详情"按钮（新增），点击后打开详情弹层。

```
[长文合并]           3′24″
这是一个关于人工智能的
文章摘要开头文本…       Provider: minimax
张三 · 2026/5/15 14:32

[▶] [⇩] [详情] [复制] [回填] [✕]
```

### 详情弹层内容（长文本）

```
标题：长文合并样本详情
来源：batch_longtext_merged
时间：2026-05-15 14:32
Provider：minimax
Profile：张三
时长：3′24″

完整文本（可复制）：
[完整 50000 字文本区域，内部滚动]
```

### 详情弹层内容（剧本）

```
标题：剧本合并样本详情
来源：batch_script_merged
时间：2026-05-15 16:42
Provider：minimax
Profile：李四
总行数：5

台词行（可复制）：
旁白：这是一个关于人工智能的故事开头…
角色A：你好，我想了解一下…
角色B：当然可以，我来为你介绍…
旁白：就这样，他们开始了对话…
[关闭]
```

### 技术前提

详情弹层依赖 ContextStore 保存 `full_text` 和 `lines` 结构。如果 ContextStore 中无记录（老数据或存储已满），详情按钮置灰或提示"仅保留预览，无法查看完整内容"。

## 10. 长文本一键回填方案

### 目标

点击长文本样本的"回填"按钮，切换到长文本 tab，并恢复可恢复配置。

### v1 可恢复字段

```
- full_text         → #batchText
- profile_id        → #batchProfile
- provider          → #batchProvider
- output_format     → #batchOutputFormat
- need_subtitle     → #batchNeedSubtitle
```

### 后续可恢复字段（v2）

```
- segment_strategy  → #batchStrategy
- max_segment_chars → #batchMaxChars
- silence_between_ms → #batchSilence
- speed / vol / pitch / emotion → #batchSpeed / #batchVol / #batchPitch / #batchEmotion
```

### 回填行为

```
点击长文本样本"回填"：
1. 切换到长文本 tab
2. 填入 #batchText = full_text
3. 恢复 profile_id / provider / output_format / need_subtitle 等字段
4. 不自动生成
5. 用户确认后手动点击"提交批量任务"
```

**必须明确：**

```
回填不是自动重新生成。
回填只是恢复编辑状态。
```

## 11. 剧本一键回填方案

### 目标

点击剧本样本的"回填"按钮，切换到剧本 tab，并重建剧本行。

### v1 可恢复字段

```
- lines: [{ role, text, profile_id }]  → 重建剧本行
- provider                              → #batchScriptProvider
- output_format                          → #batchScriptOutputFormat
- need_subtitle                          → #batchScriptNeedSubtitle
```

### 后续可恢复字段（v2）

```
- silence_between_ms
- 每行 params（speed/vol/pitch/emotion）
- 角色默认音色偏好
```

### 回填行为

```
点击剧本样本"回填"：
1. 切换到剧本 tab
2. 弹确认："当前剧本内容将被替换，是否继续？"
3. 清空当前 script lines
4. 重建每一行 role / text / profile_id
5. 恢复 provider / output_format / need_subtitle
6. 不自动生成
7. 用户确认后手动点击"提交批量任务"
```

### 产品讨论：已有内容时是否覆盖？

**建议 A0 结论：**

```
默认弹确认：
"当前剧本内容将被替换，是否继续？"

- 确认 → 替换
- 取消 → 不操作
```

## 12. SampleStore 与 ContextStore 的边界

**不要把完整长文本 / 完整剧本 / 完整配置直接塞进 SampleStore。**

原因：

```
- SampleStore.text_preview 上限 100 字符（P13 设计）
- SampleStore 的价值是"轻量索引"，不是"内容仓库"
- 塞入 50000 字会直接撑爆 localStorage（5～10MB 限制）
-塞入剧本 lines 数组会让 SampleStore 结构复杂化
```

### P13 SampleStore 继续保持轻量

```
SampleStore 保存：
- source
- text_preview（100 字符截断）
- audio url
- provider
- profile_id / profile_name
- duration_ms
- created_at
- batch_id / job_id
- context_id（新增，指向 ContextStore）
```

### P14 应设计独立 ContextStore

```
新 key：voice_lab_sample_context_v1

ContextStore 保存：

longtext context:
{
  context_id,            // 关联 SampleStore.sample.context_id
  source: 'batch_longtext_merged',
  full_text,             // 完整长文本（最多 50000 字）
  profile_id,
  provider,
  segment_strategy,
  max_segment_chars,
  silence_between_ms,
  output_format,
  need_subtitle,
  params: { speed, vol, pitch, emotion },
  created_at
}

script context:
{
  context_id,            // 关联 SampleStore.sample.context_id
  source: 'batch_script_merged',
  lines: [{ role, text, profile_id, params }],
  provider,
  silence_between_ms,
  output_format,
  need_subtitle,
  created_at
}
```

### 关系

```
SampleStore.sample.context_id → ContextStore[context_id]
```

**SampleStore 负责"展示索引"。**
**ContextStore 负责"恢复上下文"。**

## 13. localStorage 存储限制与淘汰策略

### 限制背景

主流浏览器 localStorage 上限约 5～10MB。

### 存储估算

```
长文本（50000 字）≈ 50KB
剧本（100 行平均 200 字）≈ 20KB

ContextStore 如果保存 50 条长文本：≈ 2.5MB
加上 SampleStore 的 200 条样本：≈ 200KB
总计：≈ 3MB
→ 仍在安全范围内
```

### 存储策略

```
SampleStore：
- 继续最多 200 条
- 继续保存轻量 text_preview（100 字符）

ContextStore：
- 最多保存最近 20～50 条可恢复上下文
- 按 created_at LRU 淘汰
- 单条 longtext 最大 50000 字，超出不保存 full_text 但保留 sample
- 如果 context 缺失，回填按钮置灰或提示"仅保留预览，无法完整恢复"
```

### 存储失败的处理

```
保存 context 时如果 localStorage 满：
- 静默失败（不报 JS 错）
- SampleStore 样本仍正常保存
- 回填按钮对缺失 context 的样本置灰
- 提示："该样本无法回填，仅保留预览"
```

## 14. 全局侧边栏可见性

### 当前问题

P13 的 SampleSidebar 只挂在 Workspace tab 内。但长文本 / 剧本才是主生产入口，只在 Workspace 可见会造成体验割裂。

### 评估

```
当前：Sidebar 只在 #tab-workspace 内可见

问题：
- 用户在长文本 tab 生成内容后，无法从侧边栏看到最近样本
- 用户在剧本 tab 生成内容后，同样看不到
- 用户必须在 workspace tab 才能操作样本

结论：
- 侧边栏可见性是 P14 需要解决的核心 UX 问题
```

### 建议方案

```
方案 A（简单）：侧边栏改为各 tab 共享，挂在 tab-nav 下方
- 所有 tab 都能看到同一个侧边栏
- 不做三套侧边栏

方案 B（完整）：全局侧边栏组件
- 桌面端：固定在右侧，始终可见
- 窄屏：浮动按钮，点击打开 drawer

全局侧边栏是 P14-B0 设计内容，不在 A0 实现。
```

## 15. 不建议现在做的事

```
P14-A0 不建议：
- 直接修改 SampleStore 保存完整长文本（会撑爆 localStorage）
- 直接把侧边栏复制到三个 tab（维护三套代码）
- 直接做三套独立样本存储（维护成本高）
- 直接实现配置恢复（没有 ContextStore 设计会乱）
- 直接接后端 sample library（超出 P14 范围）
- 直接改成多用户 SaaS（超出 P14 范围）
- 直接做 segment samples（P13 已明确不做）
- 直接做 history sample_store（P13 已明确不做）
```

## 16. 长文本生产入口可用性问题

### 1. 当前问题

```
长文本是真实主生产入口之一，但当前长文本页面缺少生成前的关键可理解性提示：

- 没有在输入区附近显示当前字数 / 上限
- 没有显示预计消耗字数
- 没有显示预计分段数量
- 分段策略文案容易误解
- "自动（按段落合并，推荐长文）"容易被用户理解成"每个段落单独生成一段"
```

### 2. 字数提示设计

```
在 #batchText 附近显示：

当前字数：2549 / 50000 字

当接近上限时提示：

文本较长，请确认分段策略和每段上限。
```

### 3. 消耗 / 分段预估设计

```
预计消耗：2549 字
每段上限：2000 字
预计分段：约 2 段
实际消耗以生成结果和 provider usage 为准

---

这里是生成前预估，不作为最终计费依据。
最终消耗应以后端返回或 provider usage 为准。
```

### 4. 分段策略解释

```
自动合并短段落（推荐长文）：
先识别自然段，再把较短段落合并到每段上限以内。适合文章、书摘、课程稿、口播稿。
若文本总长度未超过每段上限，可能最终只有 1 段。

按空行分段：
以空行作为段落边界，适合已经整理好段落结构的长文。
注意：普通换行不一定等同于空行。

按句子分段：
按句号、问号、感叹号等句子边界拆分，适合段落不清晰但句子边界明显的文本。

每行一段：
每一行作为独立生成段，适合手动控制节奏、列表、分镜旁白或台词。
```

### 5. 动态 helper text

```
选择不同分段策略时，下方 helper text 动态变化。

例如选择"自动合并"策略时显示：

自动策略会保持自然段边界，但会把较短段落合并到每段上限内。
当前预计：约 2 段。
如果希望每段单独生成，请选择"按空行分段"或"每行一段"，或降低每段上限。
```

### 6. 产品优先级判断

```
长文本生产入口可用性属于主生产路径问题，不是普通 UI polish。
其优先级高于 Workspace spacing 和按钮视觉一致性。
```

### 7. 后续阶段建议

```
P14-LONGTEXT-UX-B0：长文本字数 / 消耗 / 分段策略提示方案设计
P14-LONGTEXT-UX-B1：实现长文本字数统计、预计分段、策略说明
```

```
P14-LONGTEXT-UX-B0 应优先于 ContextStore 实现。
原因：它直接影响长文本生产入口的可理解性，且范围比配置恢复更小。
```

## 17. P14 后续阶段拆分

### 建议优先级

```
优先级 1：长文本生产入口可用性（P14-LONGTEXT-UX-B0）
         原因：直接影响主生产路径可理解性，范围小、价值高

优先级 2：ContextStore 设计（P14-CONTEXT-B0）
         原因：没有 context 数据，后面的回填和详情都是无根之木

优先级 3：侧边栏详情弹层（P14-PRODUCT-B1）
         原因：用户现在最大困惑是"看不到完整内容"

优先级 4：长文本回填（P14-CONTEXT-B1）
         原因：长文本是主生产入口，回填价值高

优先级 5：剧本回填（P14-CONTEXT-B2）
         原因：剧本结构复杂，回填设计难度高于长文本

优先级 6：全局侧边栏可见性（P14-PRODUCT-B0）
         原因：影响所有 tab 的样本可见性，但可后期迭代
```

### 阶段拆分

| 阶段 | 内容 | 前提 |
|------|------|------|
| P14-LONGTEXT-UX-B0 | 长文本字数 / 消耗 / 分段策略提示方案设计 | P14-A0-FIX1 完成 |
| P14-LONGTEXT-UX-B1 | 实现长文本字数统计、预计分段、策略说明 | P14-LONGTEXT-UX-B0 完成 |
| P14-CONTEXT-B0 | ContextStore 数据结构设计 | P14-A0-FIX1 完成 |
| P14-PRODUCT-B0 | 全局 SampleSidebar 可见性方案设计 | P14-A0-FIX1 完成 |
| P14-PRODUCT-B1 | 侧边栏卡片预览与详情弹层设计 | P14-A0-FIX1 完成 |
| P14-CONTEXT-B1 | 长文本 context 保存与一键回填实现 | P14-CONTEXT-B0 完成 |
| P14-CONTEXT-B2 | 剧本 context 保存与一键回填实现 | P14-CONTEXT-B0 完成 |
| P14-UX-CHECK | 验证长文本 / 剧本生产路径是否清晰 | B1+B2 完成 |

### 产品判断

```
如果目标是提升真实生产效率，长文本生产入口可用性优先于 ContextStore。
建议优先做 P14-LONGTEXT-UX-B0。
```

## 17. A0 结论

P13 将 SampleSidebar 定位为"最近样本观察面板"，P14 应将其升级为"样本复用入口"。

核心升级路径：

```
1. 设计独立 ContextStore，保存 full_text 和完整配置
2. 侧边栏卡片保持短预览，点击"详情"打开弹层查看完整内容
3. 长文本样本支持一键回填到长文本 tab
4. 剧本样本支持一键回填到剧本 tab
5. 全局侧边栏在各主生产 tab 均可访问
```

关键约束：

```
- SampleStore 保持轻量（不存 full_text）
- ContextStore 独立设计（不污染 SampleStore）
- 不做 segment samples
- 不做 history sample_store
- 不做后端 sample library
- 不做多用户 / SaaS
```

A0 只输出方案，不进入实现。实现从 P14-CONTEXT-B0 开始。
