# P14-SCRIPT-UX-B0：剧本行数 / 字数 / 角色 / 音色完整性提示方案设计

**日期：2026-05-15**
**前提：P14-LONGTEXT-UX-B1-CLOSE 完成**

## 1. 背景

剧本是主要生产入口之一。与长文本不同，剧本是结构化行数据，用户在提交前需要理解行数、字数、角色分布、profile / 音色完整性以及预计生成段数。

P14-SCRIPT-UX-B0 只做设计文档，不实现代码。

## 2. 当前代码事实

### 2.1 剧本 Tab DOM 结构

```html
<!-- 剧本配置卡片 -->
<div class="card">
  <div class="card-title">剧本配置</div>
  <div class="config-grid">
    <select id="batchScriptProvider">...</select>
    <input type="number" id="batchScriptSilence" value="500" min="0" max="3000" step="100">
    <select id="batchScriptOutputFormat">...</select>
    <input type="checkbox" id="batchScriptNeedSubtitle" checked>
  </div>
  <div class="form-group full-width">
    <label>台词列表</label>
    <div style="font-size:0.78rem;color:#718096;margin-bottom:6px">角色名仅用于区分段落，实际发音由声音人设决定。</div>
    <div id="scriptLines"><!-- Dynamic script rows --></div>
    <button class="btn-sm" id="scriptAddLineBtn" onclick="addScriptLine()" style="margin-top:8px">+ 添加一行</button>
  </div>
  <button class="btn-primary" id="batchScriptSubmit" onclick="handleBatchScriptSubmit()">提交批量任务</button>
</div>
```

### 2.2 `_scriptRows` 真实结构

```javascript
const _scriptRows = [];  // stable state: {id, role, text, profileId}
```

每个 state 对象的字段：

| 字段 | 类型 | 来源 |
|------|------|------|
| `id` | integer | 递增序号，`_scriptLineCount++` |
| `role` | string | `scriptRole_{id}`.value |
| `text` | string | `scriptText_{id}`.value |
| `profileId` | string | `scriptProfile_{id}`.value |

### 2.3 剧本行 DOM 元素

每行 container `div#scriptLine_{id}` 内部：

| DOM id | 元素类型 | placeholder / 说明 |
|--------|----------|-------------------|
| `scriptRole_{id}` | input[type=text] | "例如：旁白、男声" |
| `scriptText_{id}` | input[type=text] | "台词内容"，maxlength=5000 |
| `scriptProfile_{id}` | select | "选择人设"，第一选项 value="" |
| `scriptVoiceHint_{id}` | span | 空，显示音色绑定提示 |
| (删除按钮) | button.btn-sm | 内联 `onclick="removeScriptLine(id)"` |

### 2.4 事件同步机制

输入事件通过事件委托同步到 `_scriptRows`：

```javascript
// input 事件同步 role 和 text
document.getElementById('scriptLines').addEventListener('input', e => {
  // field === 'role' → state.role = e.target.value
  // field === 'text' → state.text = e.target.value
});

// change 事件同步 profile
document.getElementById('scriptLines').addEventListener('change', e => {
  // field === 'profile' → state.profileId = e.target.value
});
```

### 2.5 提交时的数据过滤

`handleBatchScriptSubmit` 在提交前过滤 `_scriptRows`：

```javascript
_scriptRows.forEach(function(state) {
  if (state.text && state.text.trim()) {
    lines.push({ role: state.role || '', text: state.text.trim(), profile_id: state.profileId || '', params: {} });
  }
});
```

**关键事实**：
- 只推送 `text.trim()` 非空的行
- 空文本行不参与提交
- `role` 可以为空字符串（旁白等场景）
- `profile_id` 可以为空字符串（会在提交时被后端或前端拦截报错）

### 2.6 batch_script.js submit payload

```javascript
{
  mode: 'script',
  script: [
    { role: string, text: string, profile_id: string, params: {} },
    ...
  ],
  provider: string,
  silence_between_ms: number,
  output_format: 'hex',
  audio_format: string,
  need_subtitle: boolean,
  confirm_cost: false,
}
```

### 2.7 后端 ScriptBatchRequest schema

```python
class ScriptLine(BaseModel):
    role: str
    text: str = Field(min_length=1)
    profile_id: str
    params: dict = Field(default_factory=dict)

class ScriptBatchRequest(BaseModel):
    mode: Literal["script"] = "script"
    script: list[ScriptLine] = Field(min_length=1, max_length=200)
    provider: str | None = None
    output_format: Literal["hex", "url"] = "hex"
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"
    silence_between_ms: int = Field(default=500, ge=0, le=3000)
    need_subtitle: bool = True
    confirm_cost: bool = False
```

关键约束：
- `script` 数组最小长度 1（至少一行有效台词）
- 每行 `text` 必须 min_length=1
- `profile_id` 字段存在但**后端 schema 无 min_length 约束**（前端 validation 会拦截空 profile_id）

### 2.8 当前剧本 Tab 是否已有提示区

**不存在。** 当前剧本 Tab 只有配置区和台词列表，无任何统计提示区。

### 2.9 MAX_SCRIPT_LINES

```javascript
var MAX_SCRIPT_LINES = 200;
```

剧本最多支持 200 行。

## 3. 当前 UX 问题

1. **无行数提示**：用户不知道已填多少行台词、总行数多少
2. **无有效行数提示**：用户不知道有多少行是有效填写的
3. **无字数统计**：用户不知道台词总字数和预计消耗
4. **无预计生成段数提示**：用户不知道会生成多少个音频片段
5. **无角色统计**：用户不知道有多少个角色
6. **无音色完整性提示**：用户不知道是否有行未选择音色
7. **无字幕耗时提示**：用户不知道开启字幕后生成耗时增加

## 4. 剧本统计字段设计

建议显示字段：

```
剧本统计：共 N 行，M 行有效，约 X 字
预计生成：M 段
角色：旁白 / 男主 / 女主（共 K 个角色）
涉及音色：N 个
未选择音色：X 行
已开启字幕，生成耗时可能增加。
```

说明：
- "预计生成"段数等于有效台词行数（每行台词对应一个生成片段）
- 角色统计指有效台词行中的 role 去重
- 涉及音色数指有效行中 profile_id 非空去重数量
- 未选择音色行数：有效行中 profile_id 为空的行数

## 5. 行数统计设计

### 显示内容

```
剧本统计：共 {total} 行，{valid} 行有效
```

### 统计规则

```
总行数 = _scriptRows.length
有效台词行数 = _scriptRows 中 text.trim() 非空的行数
空文本行数 = _scriptRows 中 text.trim() 为空的行数（可推导：total - valid）
```

### 重要说明

```
空文本行不计入有效行数，不计入预计生成段数，不计入预计消耗。
submit 时会被过滤掉，不参与实际生成。
```

## 6. 字数与预计消耗设计

### 显示内容

```
约 {count} 字
```

### 统计规则

```
总字数 = 有效台词行的 text.trim().length 之和
预计消耗 = 总字数
```

### 限制

```
不显示金额
不承诺最终计费
不把字数等同 provider token
不调用 provider 预估接口
实际消耗以后端返回和 provider usage 为准
```

## 7. 预计生成段数设计

### 显示内容

```
预计生成：{n} 段
```

### 统计规则

```
预计生成段数 = 有效台词行数
```

### 说明

```
剧本模式按行生成，每一行台词对应一个生成片段。
最终生成段数以后端 batch result 中的 total_segments 为准。
```

## 8. 角色统计设计

### 显示内容

```
角色：旁白 / 男主 / 女主（共 3 个角色）
```

或无 role 时：

```
角色：未命名角色 A / 未命名角色 B（共 2 个未命名）
```

### 统计规则

```
角色数 = 有效台词行中 role.trim() 非空去重后的数量
角色列表 = 去重后的 role 名称，最多显示前 3 个，溢出显示"等 N 个"
```

### 空 role 处理

```
空 role 不计入角色数。
如果有效台词行中有 role 为空的行，单独提示："有 X 行未填写角色名"。
当前 UI 的 role 是可选的占位符，不影响提交。
```

## 9. Profile / 音色完整性设计

### 显示内容

```
涉及音色：2 个
未选择音色：1 行
```

### 统计规则

```
涉及 profile 数 = 有效台词行中 profileId 非空去重后的数量
未选择音色的行数 = 有效台词行中 profileId 为空的数量
```

### 提示规则

```
未选择音色 = 0：
音色已完整。

未选择音色 > 0：
有 X 行未选择音色，请确认是否使用默认音色或手动选择。
```

### 关于 profile 选择的说明

当前 UI：
- `scriptProfile_{id}` select 第一选项是 `value=""`，placeholder 文本为"选择人设"
- 提交前 validation 会拦截空 profile_id 并报错

## 10. 字幕耗时提示设计

### DOM id

`#batchScriptNeedSubtitle`（checkbox，checked 默认值）

### 显示内容

```
已开启字幕，生成耗时可能增加。
```

### 提示规则

```
勾选时显示，未勾选时隐藏。
```

## 11. UI 放置建议

### 整体布局

在剧本配置卡片内、台词列表 `#scriptLines` 区域上方或下方，新增轻量提示区：

```html
<div class="batch-script-hints" id="batchScriptHints">
  <div class="batch-hint-row">
    <span id="batchScriptLineStats">剧本统计：共 0 行，0 行有效</span>
    <span id="batchScriptCharStats">约 0 字</span>
    <span id="batchScriptEstimatedSegments">预计生成：0 段</span>
  </div>
  <div class="batch-hint-row">
    <span id="batchScriptRoleStats">角色：0 个</span>
    <span id="batchScriptProfileStats">涉及音色：0 个</span>
  </div>
  <div class="batch-hint-warning" id="batchScriptProfileWarning" style="display:none"></div>
  <div class="batch-hint-subtitle" id="batchScriptSubtitleHint" style="display:none">已开启字幕，生成耗时可能增加。</div>
</div>
```

建议放置位置：`#scriptLines` container 之后、`#scriptAddLineBtn` 附近，或作为 `#scriptLines` 的第一个子元素。

### 设计约束

```
不遮挡剧本行
不改变添加/删除行按钮位置
不影响提交按钮
不修改 batch submit payload
不改变现有 DOM 结构（只追加新元素）
可换行
```

### CSS 类复用

建议复用的类：
- `.batch-hints`
- `.batch-hint-row`
- `.batch-hint-warning`
- `.batch-hint-subtitle`

剧本提示可使用 `.batch-script-hints` 独立前缀，避免与长文本提示冲突。

## 12. 边界与不做事项

```
B0 不实现代码
B0 不修改 _scriptRows 结构
B0 不修改 batch_script.js
B0 不修改 submit payload
B0 不修改后端 schema
B0 不调用真实 MiniMax API
B0 不接 ContextStore
B0 不做一键回填
B0 不做剧本详情弹层
B0 不做全局侧边栏
B0 不做 history sample_store
B0 不改长文本统计（已在 P14-LONGTEXT-UX-B1 实现）
```

## 13. P14-SCRIPT-UX-B1 实现建议

### 技术要点

1. **新增 DOM**：在 `#scriptLines` 附近追加剧本提示区
2. **收集统计数据**：遍历 `_scriptRows`，计算总行数、有效行数、总字数、角色去重、profile 去重
3. **事件监听**：
   - 监听 `#scriptLines` 的 `input` 事件（用于 text/role 变化）
   - 监听 `#scriptLines` 的 `change` 事件（用于 profile 变化）
   - 监听添加行 / 删除行（`_scriptRows` 变化）
   - 监听 `#batchScriptNeedSubtitle` 的 `change` 事件
4. **更新 DOM**：统计变化时更新所有提示元素的文本
5. **不参与提交逻辑**：Hints 组件为纯展示层

### 不触碰区域

```
window.handleBatchScriptSubmit 不改
guardedJsonFetch 调用不改
batch_script.js 业务逻辑不改
_scriptRows 数据结构不改
```

### B1 范围控制

```
B1 只实现剧本统计，不顺手实现其他功能。
```

## 14. 测试计划（B1 实现后）

```python
1. 剧本提示区 DOM 存在（#batchScriptHints 等）
2. 总行数统计正确（_scriptRows.length）
3. 有效台词行数统计正确（text.trim() 非空）
4. 空文本行数可推导（total - valid）
5. 总字数统计正确（有效行 text.trim().length 之和）
6. 预计消耗显示总字数
7. 不显示金额符号（无 ¥ / $）
8. 预计生成段数等于有效台词行数
9. 角色数去重正确（role.trim() 非空去重）
10. role 为空的行不计入角色数
11. 有未填写角色名的行时提示"有 X 行未填写角色名"
12. profile 数去重正确（profileId 非空去重）
13. 未选择 profile 行数正确（有效行中 profileId 为空）
14. 未选择 profile > 0 时显示 warning
15. 未选择 profile = 0 时不显示 warning
16. 勾选字幕显示耗时提示
17. 取消字幕隐藏耗时提示
18. 添加行后统计更新
19. 删除行后统计更新
20. 修改文本后统计更新
21. 修改 role 后角色统计更新
22. 修改 profile 后音色统计更新
23. 不调用 fetch / guardedJsonFetch
24. 不写 localStorage
25. 不引用 SampleStore / ContextStore
26. 不修改 batch submit payload
27. 不修改后端 API
```

## 15. B0 结论

### 确认事实

- `_scriptRows` 结构：`[{id, role, text, profileId}]`
- DOM ids：`scriptLine_{id}`, `scriptRole_{id}`, `scriptText_{id}`, `scriptProfile_{id}`
- 提交时过滤：`text.trim()` 非空才进入 payload
- `role` 可为空，`profile_id` 可为空（但提交前会被前端 validation 拦截）
- 后端 `script: list[ScriptLine]` 约束：每行 `text` min_length=1，数组长度 1~200
- `#batchScriptNeedSubtitle` checkbox 默认 checked
- 当前剧本 Tab 无任何统计提示区

### 设计结论

- 显示总行数 / 有效台词行数 / 空文本行数（可推导）
- 显示总字数 / 预计消耗字数
- 显示预计生成段数（= 有效台词行数）
- 显示角色数与角色列表（role.trim() 非空去重）
- 空 role 行单独提示"未填写角色名"
- 显示涉及音色数（profileId 非空去重）
- 显示未选择音色的行数
- 勾选字幕时显示生成耗时提示
- 剧本统计只作为前端提示，不参与提交逻辑

### 阶段状态

B0 完成，建议进入 B1 实现。
