# P8-FIX3C Tab DOM 结构修复

## 1. 背景

用户反馈点击"剧本"tab 后内容为空白。经代码审查发现存在 DOM 结构问题导致 tab 内容不正确显示。

---

## 2. 问题清单

| 问题 | 类型 | 根因 | 修复方式 |
|---|---|---|---|
| tab-script 显示空白 | DOM 嵌套 | tab-script 嵌套在 tab-longtext 内部 | 添加 `</div>` 闭合标签 |
| subtab-danger 位置异常 | DOM 层级 | subtab-danger 在 tab-advanced 外部 | 移入 tab-advanced 内部 |
| Tab 顺序不符合预期 | DOM 顺序 | workspace→history→voices→advanced→longtext→script | 重排为 workspace→longtext→script→voices→history→advanced |
| tab 切换逻辑可优化 | 运行态 | 先清除 active 再验证 content 存在 | 改为先验证 content 存在再切换 |
| script tab 缺少 profile 加载 | 运行态 | callback 缺失 | 新增 script tab profile 加载回调 |

---

## 3. 修复内容

### Fix 1: 修复 tab-script 嵌套问题

**问题**：`tab-script` 的 `</div>` 闭合标签缺失，导致其内容嵌套在 `tab-longtext` 内部。

**修复**：在 `tab-script` 开启前添加 `</div>`：

```html
</div>

<!-- TAB: SCRIPT -->
<div class="tab-content" id="tab-script">
```

**验证**：HTMLParser 确认 `tab-script` parent = None（顶级）。

### Fix 2: 修复 subtab-danger 位置

**问题**：`subtab-danger` 位于 `tab-advanced` 闭合标签之后，成为其兄弟节点而非子节点。

**修复**：将 subtab-danger 整体（34 行）移入 `tab-advanced` 内部。

**验证**：HTMLParser 确认 `subtab-danger` parent = `tab-advanced`。

### Fix 3: Tab 切换选择器优化

**问题**：`.tab-btn` 选择器可能匹配子 tab 按钮。

**修复**：改为 `.tab-btn[data-tab]` 更精确匹配。

```javascript
// Before
document.querySelectorAll('.tab-btn').forEach(btn => {

// After
document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
```

### Fix 4: Tab 切换逻辑顺序

**问题**：先移除所有 active class，再验证目标 content 存在，如果不存在则无 active tab。

**修复**：先验证 content 存在，再进行切换。

```javascript
// Verify content exists before switching
const content = document.getElementById('tab-' + tab);
if (!content) {
  console.warn('Missing tab content: tab-' + tab);
  return;
}
// Then remove active and activate new tab
```

### Fix 5: 重排 Tab DOM 顺序

**修复前**：
- workspace (line 586)
- history (line 693)
- voices (line 718)
- advanced (line 768)
- longtext (line 1133)
- script (line 1242)

**修复后**：
- workspace (line 586)
- longtext (line 692)
- script (line 800)
- voices (line 841)
- history (line 890)
- advanced (line 914)

### Fix 6: 新增 script tab profile 加载回调

**问题**：`workspace` 和 `longtext` tab 有 profile 加载回调，`script` 没有。

**修复**：新增 script tab 回调。

```javascript
if (tab === 'script') {
  loadProfiles(true).then(() => populateProfileSelect(document.getElementById('batchScriptProfile')));
}
```

---

## 4. DOM 验证

### 4.1 Tab 嵌套检查

```
tab-workspace: OK (top-level)
tab-longtext: OK (top-level)
tab-script: OK (top-level)
tab-voices: OK (top-level)
tab-history: OK (top-level)
tab-advanced: OK (top-level)
```

### 4.2 Tab 顺序检查

```
Order: ['tab-workspace', 'tab-longtext', 'tab-script', 'tab-voices', 'tab-history', 'tab-advanced']
Expected: ['tab-workspace', 'tab-longtext', 'tab-script', 'tab-voices', 'tab-history', 'tab-advanced']
MATCH: YES
```

### 4.3 subtab-danger 位置检查

```
subtab-danger parent: tab-advanced (line 1219)
tab-advanced range: lines 914-1252
subtab-danger INSIDE tab-advanced: OK
```

---

## 5. 修改文件

| 文件 | 修改内容 |
|---|---|
| `app/static/index.html` | DOM 结构修复（Fix 1-6） |

---

## 6. API endpoint 不变

- `/api/voice/render` - 未改
- `/api/voice/render/async` - 未改
- `/api/voice/batch/submit` - 未改
- `/api/voice/jobs` - 未改
- `/api/voice/assets/` - 未改

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

### 7.2 Tab 顺序验证

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")

class TabVerifier:
    def __init__(self, html):
        self.html = html
        self.lines = html.split('\n')
        self.tab_ranges = {}

    def find_all_tabs(self):
        import re
        for i, line in enumerate(self.lines):
            if 'class="tab-content' in line and 'id="tab-' in line:
                m = re.search(r'id="(tab-[^"]+)"', line)
                if m:
                    tab_id = m.group(1)
                    self.tab_ranges[tab_id] = {'start': i, 'end': None}

    def find_closing(self, start_idx):
        depth = 0
        for i in range(start_idx, len(self.lines)):
            line = self.lines[i]
            opens = line.count('<div')
            closes = line.count('</div>')
            depth += opens - closes
            if i > start_idx and depth == 0:
                return i
        return None

    def verify(self):
        self.find_all_tabs()
        for tab_id, info in self.tab_ranges.items():
            close_idx = self.find_closing(info['start'])
            info['end'] = close_idx
        return self.tab_ranges

tv = TabVerifier(html)
ranges = tv.verify()
order = list(ranges.keys())
expected = ['tab-workspace', 'tab-longtext', 'tab-script', 'tab-voices', 'tab-history', 'tab-advanced']
print("PASS" if order == expected else f"FAIL: got {order}")
PY
```

### 7.3 Nesting 验证

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")

import re
class NestingChecker:
    def __init__(self, html):
        self.lines = html.split('\n')
        self.tab_ranges = {}
        
    def find_all_tabs(self):
        for i, line in enumerate(self.lines):
            if 'class="tab-content' in line and 'id="tab-' in line:
                m = re.search(r'id="(tab-[^"]+)"', line)
                if m:
                    self.tab_ranges[m.group(1)] = {'start': i}
                    
    def find_closing(self, start_idx):
        depth = 0
        for i in range(start_idx, len(self.lines)):
            depth += self.lines[i].count('<div') - self.lines[i].count('</div>')
            if i > start_idx and depth == 0:
                return i
        return None
    
    def check_nesting(self):
        self.find_all_tabs()
        nested = []
        for tab, info in self.tab_ranges.items():
            close = self.find_closing(info['start'])
            info['end'] = close
            for other, other_info in self.tab_ranges.items():
                if other != tab and info['start'] < other_info['start'] < close:
                    nested.append(f"{other} inside {tab}")
        return nested

nc = NestingChecker(html)
issues = nc.check_nesting()
print("PASS - No nesting" if not issues else f"NESTED: {issues}")
PY
```

---

## 8. 验证结果

### 8.1 pytest

```
375 passed, 6 skipped
```

### 8.2 Tab DOM 验证

- 6 tabs found: PASS
- Correct order: PASS
- No nesting: PASS
- subtab-danger inside tab-advanced: PASS

---

## 9. 未处理事项

- P8-BE1：历史任务返回音频资产字段
- P8-UX1：桌面宽屏布局与响应式适配
- P8-5：localStorage 最近任务恢复
- 历史播放/下载后端字段支持

---

## 10. 阶段结论

**P8-FIX3C 已完成。** 修复了以下问题：

1. tab-script 嵌套在 tab-longtext 内的问题（Fix 1）
2. subtab-danger 位置异常问题（Fix 2）
3. Tab 切换选择器优化（Fix 3）
4. Tab 切换逻辑顺序优化（Fix 4）
5. Tab DOM 顺序重排（Fix 5）
6. script tab profile 加载回调缺失（Fix 6）

所有 375 个测试通过，Tab DOM 结构正确。
