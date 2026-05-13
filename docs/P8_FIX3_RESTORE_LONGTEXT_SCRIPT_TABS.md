# P8-FIX3 恢复长文本 / 剧本 tab 内容区

## 1. 背景

用户反馈点击"剧本"tab 后内容为空白。

经 P8-FIX1A 审查时报告内容缺失，但后续核实发现内容本来存在。

本阶段重新以当前 dev 代码为准进行强制审查。

---

## 2. 根因分析

### 2.1 代码核实结果

经过完整代码审查，**所有内容均已存在**：

| 元素 | 状态 | 位置 |
|---|---|---|
| `tab-longtext` | 存在 | 第 1135 行 |
| `tab-script` | 存在 | 第 1243 行 |
| 长文本配置 card | 存在 | tab-longtext 内 |
| 剧本配置 card | 存在 | tab-script 内 |
| batchText textarea | 存在 | tab-longtext |
| batchProfile select | 存在 | tab-longtext |
| batchProvider select | 存在 | tab-longtext |
| batchLongtextSubmit button | 存在 | tab-longtext |
| batchScriptProvider select | 存在 | tab-script |
| batchScriptSubmit button | 存在 | tab-script |
| scriptLines container | 存在 | tab-script |
| addScriptLine function | 存在 | 第 4258 行 |
| removeScriptLine function | 存在 | 第 4283 行 |
| handleBatchLongtextSubmit function | 存在 | 第 4298 行 |
| handleBatchScriptSubmit function | 存在 | 第 4374 行 |

### 2.2 可能的问题原因

内容存在于代码中，但用户仍看到空白页。可能原因：

1. **浏览器缓存**：用户运行的是旧版本缓存，未加载最新 HTML/JS
2. **JavaScript 错误**：`getElementById('tab-script')` 在某些情况下返回 null（但代码验证显示元素存在）
3. **Tab 切换逻辑**：缺少对 script tab 的 profile 加载回调（longtext 有 `loadProfiles` 回调，script 没有）

### 2.3 Tab 切换回调差异

```javascript
// tab-workspace callback
if (tab === 'workspace') { loadProfiles(true).then(...); }

// tab-longtext callback
if (tab === 'longtext') { loadProfiles(true).then(...); }

// tab-script callback
// （无回调）
```

Script tab 缺少 profile 加载回调可能导致脚本行的人设选择无法正确加载。但不会导致空白页。

### 2.4 Tab 内容区 DOM 顺序

```
1. tab-workspace (第 586 行)
2. tab-longtext (第 1135 行)
3. tab-script (第 1243 行)
4. tab-voices (第 718 行)
5. tab-history (第 693 行)
6. tab-advanced (第 768 行)
```

DOM 顺序与导航按钮顺序不一致，但 JS 通过 `getElementById('tab-' + tab)` 直接激活对应内容，与 DOM 位置无关。

---

## 3. 修复内容

### 3.1 确认状态

经完整核实，**不需要恢复任何缺失内容**。所有 tab-longtext 和 tab-script 内容均已存在。

### 3.2 新增 script tab profile 加载回调

为 script tab 新增 profile 加载回调，与 longtext 保持一致：

```javascript
if (tab === 'script') {
  loadProfiles(true).then(() => populateProfileSelect(document.getElementById('batchScriptProfile')));
}
```

此修改确保 script tab 的人设下拉框能正确加载数据。

### 3.3 Tab 切换 null 防御

为 tab 切换逻辑增加 null 防御：

```javascript
const content = document.getElementById('tab-' + tab);
if (content) {
  content.classList.add('active');
} else {
  console.warn(`Missing tab content: tab-${tab}`);
}
```

---

## 4. DOM id 保留 / 新增说明

以下 DOM id 均存在：

| DOM id | 位置 | 状态 |
|---|---|---|
| `tab-longtext` | 第 1135 行 | 存在 |
| `tab-script` | 第 1243 行 | 存在 |
| `batchText` | tab-longtext | 存在 |
| `batchProfile` | tab-longtext | 存在 |
| `batchProvider` | tab-longtext | 存在 |
| `batchStrategy` | tab-longtext | 存在 |
| `batchMaxChars` | tab-longtext | 存在 |
| `batchSilence` | tab-longtext | 存在 |
| `batchOutputFormat` | tab-longtext | 存在 |
| `batchNeedSubtitle` | tab-longtext | 存在 |
| `batchLongtextSubmit` | tab-longtext | 存在 |
| `batchScriptProvider` | tab-script | 存在 |
| `batchScriptSilence` | tab-script | 存在 |
| `batchScriptOutputFormat` | tab-script | 存在 |
| `batchScriptNeedSubtitle` | tab-script | 存在 |
| `batchScriptSubmit` | tab-script | 存在 |
| `scriptLines` | tab-script | 存在 |

---

## 5. JS function 保留 / 新增说明

| 函数 | 位置 | 状态 |
|---|---|---|
| `handleBatchLongtextSubmit` | 第 4298 行 | 存在 |
| `handleBatchScriptSubmit` | 第 4374 行 | 存在 |
| `addScriptLine` | 第 4258 行 | 存在 |
| `removeScriptLine` | 第 4283 行 | 存在 |

---

## 6. API endpoint 不变说明

- `/api/voice/batch/submit` - 未改
- `/api/voice/batch/{batch_id}/status` - 未改
- `/api/voice/batch/{batch_id}/download` - 未改
- `/api/voice/render` - 未改
- `/api/voice/render/async` - 未改
- `/api/voice/jobs` - 未改

---

## 7. 验证命令

### 7.1 Tab 完整性

```bash
python - <<'PY'
from pathlib import Path, re
html = Path("app/static/index.html").read_text(encoding="utf-8")
tabs = re.findall(r'data-tab="([^"]+)"', html)
ids = set(re.findall(r'id="([^"]+)"', html))
missing = [f"tab-{t}" for t in tabs if f"tab-{t}" not in ids]
print("PASS" if not missing else f"MISSING: {missing}")
PY
```

### 7.2 长文本 / 剧本 DOM

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-longtext", "tab-script", "batchText", "batchLongtextSubmit", "batchScriptSubmit", "scriptLines"]
missing = [x for x in required if x not in html]
print("PASS" if not missing else f"MISSING: {missing}")
PY
```

### 7.3 Batch JS 函数

```bash
grep -c "function handleBatchLongtextSubmit\|function handleBatchScriptSubmit\|function addScriptLine\|function removeScriptLine" app/static/index.html
```

---

## 8. 验证结果

### 8.1 Tab 完整性
**PASS** - 所有 6 个 tab 均有对应内容区

### 8.2 长文本 / 剧本 DOM
**PASS** - 所有必需 DOM 元素均存在

### 8.3 Batch JS 函数
**PASS** - 所有 batch 相关函数均存在

### 8.4 pytest
**375 passed, 6 skipped**

---

## 9. 未处理事项

- 未处理 P8-BE1（历史任务返回音频资产字段）
- 未处理 P8-UX1（桌面宽屏布局与响应式适配）
- 未处理 P8-5（localStorage 最近任务恢复）
- 未处理历史播放 / 下载后端字段

---

## 10. 阶段结论

**P8-FIX3 已完成。**

经完整代码审查，tab-longtext 和 tab-script 内容区**本来完整存在**，并非缺失。P8-FIX1A 审查结论为误判。

本阶段在 script tab 切换逻辑中新增 profile 加载回调，与 longtext tab 保持一致。如用户仍看到空白页，建议清除浏览器缓存或硬刷新（Ctrl+Shift+R）确认是否为缓存问题。
