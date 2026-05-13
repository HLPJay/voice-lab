# P8-FIX2 创作工作台首页轻量 UX 修复

## 1. 背景

- P8-FIX1 已完成。
- 用户反馈创作工作台首页"主流程"大卡片位置不合适。
- 当前页面存在顶部导航和主流程卡片重复的问题。
- 本阶段只做轻量 UX 修复，不改业务逻辑。

---

## 2. 问题分析

| 问题 | 原因 | 影响 | 本阶段处理 |
|---|---|---|---|
| 主流程卡片占据首屏空间 | 独立 card 占用大量纵向空间 | 文案输入被下推，首屏核心操作不可见 | **已移除** |
| 主流程卡片与顶部导航重复 | 三个卡片内容（单段旁白/长文本/剧本）与顶部 tab 导航完全重复 | 用户看到重复入口，不知道哪个是主操作 | **已移除** |
| 文案输入被下推 | 主流程卡片在文案输入 card 之前 | 用户需要向下滚动才能开始输入 | **已优化** |
| 卡片看起来像入口但不是必要主操作 | 三个卡片区只是说明性内容，无实际功能 | 造成视觉干扰和认知负担 | **已移除** |
| 不属于 P8-UX1 宽屏布局问题 | 这是内容优先级问题，不是响应式布局问题 | 桌面和移动端都受影响 | **已移除** |
| 不属于后端 P8-BE1 问题 | 这是前端 UX 问题，不需要后端字段支持 | - | **已移除** |

---

## 3. 方案判断

- 移除"主流程"大卡片（3 列说明性卡片）
- 压缩欢迎卡片为轻量提示（只占 1 行）
- 保留顶部导航作为主模块入口
- 不新增额外跳转按钮
- 不改生成逻辑
- 不改后端 API
- 不做桌面宽屏响应式改造

---

## 4. 修改内容

### 4.1 移除内容

以下区域已从 `tab-workspace` 中移除：

1. "欢迎来到 Voice Lab" 大标题区域
2. "主流程"大卡片（包含 3 列说明性卡片）

### 4.2 保留内容

- `tab-workspace`、`textInput`、`charCount`、`costHint`
- `profileSelect`、`providerSelect`、`bindingStatus`
- `generateBtn`、`resultsArea`
- 所有配置项（音频格式、返回格式、语音参数）
- 同步/异步/流式生成 radio
- 所有 API endpoint 和 JS 函数

### 4.3 新增内容

轻量欢迎提示：

```html
<div class="card" style="padding:16px 20px">
  <div class="card-title">创作工作台</div>
  <p style="font-size:0.88rem;color:#718096;line-height:1.7">
    用于快速生成单段旁白。长文本和多角色剧本请使用上方对应模块。
  </p>
</div>
```

---

## 5. 修改后工作台结构

```
轻量欢迎提示（1 行）
文案输入 card
配置 card
生成按钮
结果展示
```

---

## 6. DOM id 保留说明

以下核心 DOM id 均存在：

| DOM id | 状态 |
|---|---|
| `tab-workspace` | 存在 |
| `textInput` | 存在 |
| `charCount` | 存在 |
| `costHint` | 存在 |
| `profileSelect` | 存在 |
| `providerSelect` | 存在 |
| `bindingStatus` | 存在 |
| `generateBtn` | 存在 |
| `resultsArea` | 存在 |

---

## 7. JS function 保留说明

以下核心 JS 函数均存在：

| 函数 | 状态 |
|---|---|
| `handleGenerate` | 存在 |
| `renderResults` | 存在 |
| `renderAsyncResult` | 存在 |
| `renderStreamResult` | 存在 |
| `handleBatchLongtextSubmit` | 存在 |
| `handleBatchScriptSubmit` | 存在 |
| `toggleHistory` | 存在 |
| `refreshHistory` | 存在 |

---

## 8. API endpoint 不变说明

- `/api/voice/render` - 未改
- `/api/voice/render/async` - 未改
- `/api/voice/variants` - 未改
- `/api/voice/batch/submit` - 未改
- `/api/voice/jobs` - 未改
- `/api/voice/assets/` - 未改
- 流式生成使用 WebSocket（非 HTTP endpoint）- 未改

---

## 9. 未处理事项

- 未处理 P8-BE1（历史任务返回音频资产字段）
- 未处理 P8-UX1（桌面宽屏布局与响应式适配）
- 未处理 P8-5（localStorage 最近任务恢复）
- 未处理历史播放/下载后端字段
- 未做桌面宽屏布局
- 未拆分 index.html
- 未引入 React/Vue

---

## 10. 验证命令

### 10.1 Workspace 结构检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-workspace", "textInput", "charCount", "costHint", "profileSelect",
    "providerSelect", "bindingStatus", "generateBtn", "resultsArea"]
forbidden = ["<div class=\"card-title\">主流程</div>",
    "适合短视频旁白、情绪独白、口播文案",
    "适合文章、长文、课程稿、书摘等内容的分段生成与合并",
    "适合多角色对话、音频剧、访谈式内容"]
print("PASS" if all(x in html for x in required) and not any(x in html for x in forbidden) else "FAIL")
PY
```

### 10.2 Tab 保留检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ['data-tab="workspace"', 'data-tab="longtext"', 'data-tab="script"',
    'id="tab-workspace"', 'id="tab-longtext"', 'id="tab-script"']
print("PASS" if all(x in html for x in required) else "FAIL")
PY
```

### 10.3 JS function 保留检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
fns = ["handleGenerate", "renderResults", "renderAsyncResult", "renderStreamResult",
    "handleBatchLongtextSubmit", "handleBatchScriptSubmit", "toggleHistory", "refreshHistory"]
print("PASS" if all(f"function {f}" in html or f"async function {f}" in html for f in fns) else "FAIL")
PY
```

---

## 11. 验证结果

- Workspace 结构检查：通过
- Tab 保留检查：通过
- JS function 保留检查：通过
- pytest：375 passed, 6 skipped

---

## 12. 阶段结论

**P8-FIX2 已完成。** 创作工作台首页已移除重复的"主流程"大卡片，欢迎区已轻量化（1 行提示），文案输入和生成配置更靠前。生成逻辑、长文本、剧本、历史、音色和高级模块均未改动。
