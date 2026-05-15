# P14-LONGTEXT-UX-B0：长文本字数 / 消耗 / 分段策略提示方案设计

**日期：2026-05-15**
**前提：P14-PRODUCT-A0-FIX1 完成**

## 1. 背景

长文本是真实内容生产入口之一。当前长文本页面缺少生成前的关键可理解性提示：字数 / 预计消耗 / 预计分段数量 / 分段策略说明，导致用户难以预期生成结果。

P14-LONGTEXT-UX-B0 只做设计文档，不实现代码。

## 2. 当前代码事实

### 长文本输入区

```html
<textarea id="batchText" maxlength="50000">
```

### 每段上限

```html
<input type="number" id="batchMaxChars" value="2000" min="100" max="5000" step="100">
```

- 默认值：2000
- 最小值：100
- 最大值：5000

### 分段策略

```html
<select id="batchStrategy">
  <option value="auto">自动（按段落合并，推荐长文）</option>
  <option value="paragraph">按空行分段</option>
  <option value="sentence">每句一段</option>
  <option value="line">每行一段</option>
</select>
```

当前 4 种策略值（以后端 `Literal["auto", "paragraph", "sentence", "line"]` 为准）：

| value | label |
|-------|-------|
| auto | 自动（按段落合并，推荐长文） |
| paragraph | 按空行分段 |
| sentence | 每句一段 |
| line | 每行一段 |

### 当前 helper text

策略 select 下方已有：

```
自动策略会合并较短内容；"每句一段"会按句号/问号/感叹号切分；如需逐行控制，请选择"每行一段"。
```

### batch_longtext.js submit payload

```javascript
{
  mode: 'longtext',
  text: text,
  profile_id: profileId,
  provider: provider,
  segment_strategy: strategy,    // 'auto' | 'paragraph' | 'sentence' | 'line'
  max_segment_chars: maxChars,   // number, default 2000
  silence_between_ms: silence,   // number, default 300
  output_format: 'hex',
  audio_format: outputFormat,
  params: params,               // { speed, vol, pitch, emotion }
  need_subtitle: needSubtitle,  // boolean
  confirm_cost: false,
}
```

### 后端 schema 约束

```python
class LongtextBatchRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    segment_strategy: Literal["auto", "paragraph", "sentence", "line"] = "auto"
    max_segment_chars: int = Field(default=2000, ge=100, le=5000)
    silence_between_ms: int = Field(default=300, ge=0, le=3000)
    need_subtitle: bool = True
    confirm_cost: bool = False
```

## 3. 当前 UX 问题

1. **无字数提示**：用户不知道已输入多少字，距离 50000 上限还有多少
2. **无消耗预估**：用户不知道这次生成大概要花多少字
3. **无分段数量提示**：用户不知道文本会被切成几段
4. **"自动"策略易误解**：容易被理解成"每个自然段单独生成一段"，实际上会自动合并短段落
5. **"每句一段"易误解**：用户可能以为按所有标点切分，实际上只按句末标点（。！？）
6. **无字幕耗时提示**：开启字幕后生成耗时增加，用户无预期

## 4. 字数提示设计

### 显示内容

```
当前字数：{count} / 50000 字
```

### 显示位置

建议在 `#batchText` 标题行右侧，或 textarea 右下角附近。

不增加新 DOM 容器，不遮挡输入区。

### 阈值与状态提示

| 范围 | 提示 |
|------|------|
| 0～80%（0～40000 字）| 无额外提示 |
| 80%～95%（40000～47500 字）| "文本较长，请确认分段策略" |
| 95%～100%（47500～50000 字）| "接近 50000 字上限" |
| 50000 | maxlength 阻止输入，但仍保留防御性提示 |

### 中文字符计数说明

```
JS string.length 将中文字、英文字符、标点均计为 1 个字符。
这是前端字数估算，不等同 provider token 消耗。
```

## 5. 预计消耗提示设计

### 显示内容

```
预计消耗：{count} 字
实际消耗以生成结果和 provider usage 为准
```

### 限制

```
不显示金额
不承诺最终计费
不把字数等同 token
不调用 provider 预估接口
```

### 字幕耗时提示

当 `need_subtitle` 勾选时，在预计消耗下方追加：

```
已开启字幕，生成耗时可能增加。
```

## 6. 预计分段数量设计

### 估算规则（前端 JS 估算）

#### auto（自动合并短段落）

```
1. 按空行拆分，得到自然段列表
2. 贪心合并：连续短段落（< max_segment_chars）向前合并直到不超过上限
3. 如果合并后总段数 = 1，显示"预计 1 段"
4. 否则显示"预计约 N 段"
```

说明：auto 策略是"尽量保持段落边界 + 合并短段落"，不是每个自然段单独生成。

#### paragraph（按空行分段）

```
1. 按连续空行拆分
2. 过滤空段
3. 每个非空段为 1 段
4. 如果某段超过 max_segment_chars，继续按句子边界拆分（估算值）
```

#### sentence（每句一段）

```
1. 按中文句末标点（。！？）和英文句末标点（.!?）拆分
2. 每句为 1 段
3. 超过 max_segment_chars 的超长句继续拆分（估算值）
```

#### line（每行一段）

```
1. 按非空行计数
2. 每非空行为 1 段
```

### 显示内容

```
预计分段：约 {n} 段
```

### 重要说明

```
前端预计分段只作为提示，真实分段以后端 batch orchestration 结果为准。
```

## 7. 分段策略 helper text

### 策略说明

#### auto（自动（按段落合并，推荐长文））

```
先识别自然段，再把较短段落合并到每段上限以内。适合文章、书摘、课程稿、口播稿。
若文本总长度未超过每段上限，可能最终只有 1 段。
```

#### paragraph（按空行分段）

```
以空行作为段落边界，适合已经整理好段落结构的长文。
注意：普通换行不一定等同于空行。
```

#### sentence（每句一段）

```
按句号、问号、感叹号等句子边界拆分，适合段落不清晰但句子边界明显的文本。
```

#### line（每行一段）

```
每一行作为独立生成段，适合手动控制节奏、列表、分镜旁白或台词。
```

### 动态更新

切换策略时，helper text 随策略变化：

| 策略 | helper text |
|------|------------|
| auto | 自动策略会保持自然段边界，但会把较短段落合并到每段上限内。当前预计：约 N 段。如果希望每段单独生成，请选择"按空行分段"或"每行一段"，或降低每段上限。 |
| paragraph | 按空行分段。以空行作为段落边界，适合已经整理好段落结构的长文。 |
| sentence | 每句一段。按句号、问号、感叹号等句子边界拆分。 |
| line | 每行一段。每一行作为独立生成段。 |

## 8. UI 放置建议

### 整体布局

在长文本配置卡片内（`#batchText` 下方），新增一个轻量提示区：

```html
<div class="batch-hints">
  <div class="batch-hint-row">
    <span>当前字数：<strong>2549</strong> / 50000 字</span>
    <span>预计消耗：2549 字</span>
    <span>预计分段：约 2 段</span>
  </div>
  <div class="batch-hint-warning" style="display:none">文本较长，请确认分段策略。</div>
  <div class="batch-hint-subtitle" style="display:none">已开启字幕，生成耗时可能增加。</div>
</div>
```

### 设计约束

```
不增加复杂弹窗
不遮挡输入区
不影响提交按钮位置
不修改 batch submit payload
不改变现有 DOM 结构（只追加）
```

## 9. 边界与不做事项

```
B0 不实现代码
B1 不调用真实 MiniMax API
不调用 provider 预估接口
不显示金额
不承诺最终费用
不改变后端分段逻辑
不改变 batch submit payload 结构
不改变默认分段策略
不改变 max_segment_chars 默认值
不实现 segment samples
```

## 10. P14-LONGTEXT-UX-B1 实现建议

### 技术要点

1. **字数统计**：监听 `#batchText` 的 `input` 事件，实时更新 `text.length`
2. **预计分段估算**：纯前端 JS 算法，不需要调用后端
3. **动态 helper text**：监听 `#batchStrategy` 的 `change` 事件
4. **字幕提示**：监听 `#batchNeedSubtitle` 的 `change` 事件
5. **不修改 submit handler**：Hints 组件为纯展示层，不参与提交逻辑

### 不触碰区域

```
window.handleBatchLongtextSubmit 不改
guardedJsonFetch 调用不改
batch_longtext.js submit payload 不改
```

## 11. 测试计划（B1 实现后）

```python
1. #batchText 输入后字数实时更新
2. 清空文本后显示 0 / 50000
3. 输入 45000 字（>80%）显示"文本较长"提示
4. 输入 49000 字（>95%）显示"接近上限"提示
5. #batchMaxChars 从 2000 改为 500 后，预计分段数量增加
6. 切换 strategy 为 line，预计分段按非空行计数
7. 切换 strategy 为 sentence，预计分段按句末标点估算
8. 勾选 need_subtitle 后显示字幕耗时提示
9. 不勾选则不显示
10. 各种策略下 helper text 正确切换
11. auto 策略总字数 < max 时显示"预计 1 段"
12. 确认不改变 batch submit payload
```

## 12. A0/B0 结论

### 确认事实

- `#batchText maxlength="50000"`
- `#batchStrategy` 值为 `auto` / `paragraph` / `sentence` / `line`
- `#batchMaxChars` 默认 2000，范围 100～5000
- submit payload 中 `segment_strategy` 和 `max_segment_chars` 字段与 UI 对应
- 后端 schema 约束与前端 UI 一致

### 设计结论

- 在 `#batchText` 附近显示当前字数 / 50000 字
- 显示预计消耗字数（仅数字，不显示金额，不承诺计费）
- 显示预计分段数量（前端估算，说明以后端为准）
- 四种策略增加动态 helper text
- "auto" 策略说明为何可能只有 1 段
- 开启字幕时追加耗时提示
- B0 只写设计文档，不实现代码

### 阶段状态

B0 完成，建议进入 B1 实现。

## 13. 剧本生产入口统计提示补充

### 1. 为什么剧本也需要统计提示

```
剧本也是主生产入口之一。与长文本不同，剧本是结构化行数据，用户不只关心总字数，还关心行数、角色、每行 profile 是否完整、预计生成段数。
```

### 2. 剧本统计建议字段

```
剧本页建议显示：

- 总行数
- 有效台词行数
- 空文本行数
- 总字数
- 预计消耗字数
- 预计生成段数
- 角色数
- 涉及 profile 数
- 未选择 profile 的行数
- 字幕耗时提示
```

示例：

```
剧本统计：共 8 行，7 行有效，约 1260 字
角色：旁白 / 男主 / 女主
预计生成：7 段
未选择音色：1 行
已开启字幕，生成耗时可能增加。
```

### 3. 剧本和长文本的差异

```
长文本统计重点：
- 当前字数
- 预计分段
- 分段策略说明

剧本统计重点：
- 行数（总行数 / 有效行数 / 空行数）
- 角色数
- profile 完整性（每行是否已选音色）
- 每行是否有文本
- 预计生成段数
```

### 4. 后续阶段建议

```
P14-SCRIPT-UX-B0：剧本行数 / 字数 / 角色 / 音色完整性提示方案设计
P14-SCRIPT-UX-B1：实现剧本统计与提示
```

```
P14-LONGTEXT-UX-B1 仍只实现长文本提示，不顺手扩展剧本。
剧本统计单独进入 P14-SCRIPT-UX-B0/B1，避免 B1 范围失控。
```
