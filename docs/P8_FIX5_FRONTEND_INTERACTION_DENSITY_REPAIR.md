# P8-FIX5 前端交互与信息密度全局自检修复

## 1. 背景

用户反馈当前前端存在以下问题：

- 历史记录一条任务不应该占用多行
- 高级 tab 中其他控件页（声音设计、绑定管理、危险操作）不可点击
- 需要全局分析前端交互问题

---

## 2. 问题分析

| 问题 | 类型 | 根因 | 修复方案 |
|---|---|---|---|
| 高级子 tab 不可点击 | JavaScript | `switchAdvancedSubtab` 函数不存在（被调用但未定义） | 实现 `switchAdvancedSubtab` 函数并绑定事件 |
| 高级子 tab 与主 tab class 污染 | CSS/JS | 高级子 tab 使用 `.tab-btn` class，与主 tab 相同 | 改为 `.advanced-subtab-btn` 独立 class |
| 高级子 tab 面板 `display:none` 内联样式 | HTML | 直接使用 `style="display:none"` | 改为 `.advanced-subtab-panel` class 统一管理 |
| 历史任务行 audio player 默认撑开行高 | UI 布局 | `audioPlayerHtml(assetId)` 直接内联在行内 | 改为点击播放后懒展开到独立行 |
| 播放/下载按钮直接渲染播放器 | UI 布局 | `historyJobCardHtml` 内联播放器 HTML | 改为 Play 按钮，播放器懒展开 |

---

## 3. 高级子 tab 修复说明

### 3.1 HTML 修改

高级子 tab 按钮改为独立 class：

```html
<div class="advanced-subtab-nav">
  <button class="advanced-subtab-btn active" data-advanced-subtab="clone">声音克隆</button>
  <button class="advanced-subtab-btn" data-advanced-subtab="design">声音设计</button>
  <button class="advanced-subtab-btn" data-advanced-subtab="bindings">绑定管理</button>
  <button class="advanced-subtab-btn" data-advanced-subtab="danger">危险操作</button>
</div>
```

高级子 tab 内容面板改为统一 class：

```html
<div class="advanced-subtab-panel active" id="subtab-clone">...</div>
<div class="advanced-subtab-panel" id="subtab-design">...</div>
<div class="advanced-subtab-panel" id="subtab-bindings">...</div>
<div class="advanced-subtab-panel" id="subtab-danger">...</div>
```

### 3.2 CSS 新增

```css
.advanced-subtab-nav {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 16px;
  overflow-x: auto;
  scrollbar-width: none;
}

.advanced-subtab-btn {
  padding: 10px 18px;
  border: none;
  background: transparent;
  color: #718096;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  border-radius: 4px 4px 0 0;
}

.advanced-subtab-btn.active {
  color: #5a67d8;
  border-bottom-color: #5a67d8;
}

.advanced-subtab-panel {
  display: none;
}

.advanced-subtab-panel.active {
  display: block;
}
```

### 3.3 JS 新增

`switchAdvancedSubtab(name)` 函数实现：

```javascript
function switchAdvancedSubtab(name) {
  const target = document.getElementById('subtab-' + name);
  if (!target) {
    console.error('Missing advanced subtab:', name);
    return;
  }
  document.querySelectorAll('.advanced-subtab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.advancedSubtab === name);
  });
  document.querySelectorAll('.advanced-subtab-panel').forEach(panel => {
    panel.classList.remove('active');
  });
  target.classList.add('active');
}
```

事件绑定使用独立选择器：

```javascript
document.querySelectorAll('.advanced-subtab-btn[data-advanced-subtab]').forEach(btn => {
  btn.addEventListener('click', () => {
    switchAdvancedSubtab(btn.dataset.advancedSubtab);
  });
});
```

---

## 4. 历史列表紧凑化说明

### 4.1 CSS 新增

```css
.history-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.82rem;
  flex-wrap: wrap;
}

.history-type {
  font-weight: 600;
  color: #2d3748;
  white-space: nowrap;
  min-width: 40px;
}

.history-time {
  color: #a0aec0;
  white-space: nowrap;
  min-width: 140px;
}

.history-text {
  flex: 1;
  min-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-job-id {
  color: #718096;
  font-size: 0.72rem;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.history-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.history-audio-row {
  display: none;
  padding: 10px 0 14px;
  border-bottom: 1px solid #f0f0f0;
}

.history-audio-row.visible {
  display: block;
}
```

### 4.2 historyJobCardHtml 修改

结构从直接内联播放器改为：

```javascript
// 历史行（默认一行）
return `<div class="history-row">
  <span class="history-type">${typeLabel}</span>
  ${statusBadge}
  <span class="history-time">${time}</span>
  <span class="history-text" title="${rawText}">${textSnippet}</span>
  <span class="history-job-id" title="${rawJobId}">${jobIdShort}</span>
  <span class="history-actions">
    ${playBtn}  ${downloadBtn}  ${copyBtn}  ${deleteBtn}
  </span>
</div>
<div class="history-audio-row" id="history-audio-${jobId}"></div>`;
```

有资产时：`playBtn` 为 `<button onclick="toggleHistoryAudio(...)">播放</button>`
无资产时：`playBtn` 为 `<button disabled>播放</button>`

### 4.3 播放器懒展开

`toggleHistoryAudio(assetId, jobId)` 函数：

```javascript
function toggleHistoryAudio(assetId, jobId) {
  const row = document.getElementById('history-audio-' + jobId);
  if (!row) return;
  if (row.classList.contains('visible')) {
    row.classList.remove('visible');
    row.innerHTML = '';
  } else {
    row.innerHTML = '<div style="padding:8px 0">' + audioPlayerHtml(assetId) + '</div>';
    row.classList.add('visible');
  }
}
```

---

## 5. 事件绑定隔离说明

主 tab 绑定（不变）：

```javascript
document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
```

高级子 tab 绑定（独立）：

```javascript
document.querySelectorAll('.advanced-subtab-btn[data-advanced-subtab]').forEach(btn => {
```

两者互不干扰。

---

## 6. API endpoint 不变说明

- 未改后端 API
- 未改 `/api/voice/jobs`
- 未改 `/api/voice/assets`
- 未新增 DELETE

---

## 7. 未处理事项

- 未接入真实历史删除（留给 P8-BE2 / P8-FE5）
- 未做 P8-BE3（资产物理清理）
- 未做 P8-UX1（桌面宽屏布局）
- 未做 P8-5（localStorage）

---

## 8. 验证命令

### 8.1 高级子 tab marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["advanced-subtab-btn", "data-advanced-subtab", "advanced-subtab-panel",
    "function switchAdvancedSubtab", "document.querySelectorAll('.advanced-subtab-btn"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 8.2 事件隔离检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["document.querySelectorAll('.tab-btn[data-tab]')",
    "document.querySelectorAll('.advanced-subtab-btn[data-advanced-subtab]')"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 8.3 历史紧凑布局检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["history-row", "history-actions", "history-text", "history-job-id",
    "history-audio-row", "toggleHistoryAudio"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"FAIL: {missing}")
print("PASS")
PY
```

### 8.4 播放器懒展开检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
history_fn = html.find("function historyJobCardHtml")
toggle_fn = html.find("function toggleHistoryAudio")
history_block = html[history_fn:toggle_fn]
if "audioPlayerHtml(assetId)" in history_block:
    raise SystemExit("FAIL: audioPlayerHtml inline in historyJobCardHtml")
print("PASS")
PY
```

### 8.5 禁用按钮检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["当前历史记录未返回可播放音频资产",
    "当前历史记录未返回可下载音频资产", "disabled"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"FAIL: {missing}")
if "/api/voice/assets/undefined" in html:
    raise SystemExit("FAIL: undefined asset URL")
print("PASS")
PY
```

---

## 9. 验证结果

### 9.1 静态检查

- 高级子 tab marker 检查: PASS
- 事件隔离检查: PASS
- 历史紧凑布局 marker 检查: PASS
- 播放器懒展开检查: PASS
- 禁用按钮检查: PASS

### 9.2 pytest

```
384 passed, 6 skipped
```

---

## 10. 手工验证要求（浏览器）

应在浏览器中验证：

1. 6 个主 tab 可点击并正确切换内容
2. 高级 / 声音克隆 可点击
3. 高级 / 声音设计 可点击
4. 高级 / 绑定管理 可点击
5. 高级 / 危险操作 可点击
6. 历史记录默认一行展示
7. 点击播放后展开音频播放器
8. 再点播放收起播放器
9. 无资产时播放/下载按钮 disabled

---

## 11. 阶段结论

**P8-FIX5 已完成。** 高级子 tab 已与主 tab 事件绑定隔离，声音克隆、声音设计、绑定管理、危险操作均可点击。历史记录已改为一行式紧凑列表，播放器改为点击播放后展开，播放/下载/复制 ID/删除操作位集中展示。未改后端 API，未接入真实历史删除。
