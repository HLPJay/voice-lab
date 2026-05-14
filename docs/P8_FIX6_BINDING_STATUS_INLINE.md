# P8-FIX6 工作台配置区绑定状态行内化修复

## 1. 背景

用户反馈当前"已绑定"提示独占一整块区域，绑定状态本质上属于"声音人设"的辅助信息，应提升到"声音人设"标签后面。

## 2. 问题分析

| 问题 | 原因 | 影响 | 修复方案 |
|---|---|---|---|
| bindingStatus 独立占行 | 作为 config-grid 内独立 div | 占据整行导致左侧配置列出现大块空白 | 移到声音人设 label 后的 field-label-row 内 |
| 绑定状态与声音人设字段割裂 | 结构上分离 | 用户无法一眼看清标签与绑定状态关系 | 改为 label 后面行内 span |
| 长 voice_id 撑开布局 | 无 text-overflow 限制 | 破坏表单网格对齐 | 添加 max-width + text-overflow: ellipsis |
| 使用 innerHTML 输出大块 span | JS 直接输出 HTML 字符串 | 难以控制样式，CSS 难以精确匹配 | 改用 className + textContent |

## 3. 修复内容

- HTML：将 `<div id="bindingStatus">` 改为 `<span id="bindingStatus" class="binding-status-inline">` 放在 `.field-label-row` 内 label 后面
- 新增 `.field-label-row` CSS：flex 行布局，align-items: center
- 新增 `.binding-status-inline` CSS：font-size: 0.78rem，max-width: 420px，text-overflow: ellipsis，white-space: nowrap
- 新增 `.binding-status-inline.bound/unbound/error/loading` 颜色状态 CSS
- 新增 `@media (max-width: 760px)` 移动端降级：flex-wrap 允许换行
- JS `checkBindingStatus()` 改用 `statusEl.className` + `statusEl.textContent` 替代 `innerHTML`
- 保留 `bindingStatus` DOM id
- 保留原有绑定检查逻辑和接口调用

## 4. 修改后布局结构

```
声音人设  ✓ 已绑定: voice_id (model)
[人设选择框]
Provider
[Provider 选择框]
```

## 5. 状态样式说明

- bound：绿色 #2f855a
- unbound：橙色 #dd6b20
- error：红色 #e53e3e
- loading：灰色 #718096
- 长文本省略，不撑开布局

## 6. API endpoint 不变说明

- 未改后端 API
- 未改绑定接口（/api/voice/profiles/{profileId}/bindings）
- 未改生成接口
- 未改历史接口
- 未改最近任务恢复

## 7. 未处理事项

- 未处理 P8-BE3（历史任务与资产物理清理）
- 未处理其他新功能

## 8. 验证命令

### 8.1 DOM 结构检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for m in ["field-label-row", 'id="bindingStatus"', "binding-status-inline", 'for="profileSelect"']:
    assert m in html, f"Missing {m}"
print("PASS")
PY
```

### 8.2 CSS 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for m in [".field-label-row", ".binding-status-inline", ".binding-status-inline.bound",
          ".binding-status-inline.unbound", ".binding-status-inline.error",
          "text-overflow: ellipsis", "white-space: nowrap"]:
    assert m in html, f"Missing {m}"
print("PASS")
PY
```

### 8.3 JS 输出检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for m in ["statusEl.className", "binding-status-inline bound", "binding-status-inline unbound",
          "binding-status-inline error", "textContent"]:
    assert m in html, f"Missing {m}"
print("PASS")
PY
```

### 8.4 核心 DOM 保留检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for m in ['id="profileSelect"', 'id="bindingStatus"', 'id="providerSelect"',
          'id="generateBtn"', 'id="resultsArea"', 'id="recentJobRestore"']:
    assert m in html, f"Missing {m}"
print("PASS")
PY
```

## 9. 验证结果

- DOM 结构检查: PASS
- CSS 检查: PASS
- JS 输出检查: PASS
- 核心 DOM 保留检查: PASS
- pytest: 384 passed, 6 skipped

## 10. 阶段结论

**P8-FIX6 已完成。** 创作工作台配置区的绑定状态已从独立大块区域调整为"声音人设"标签后的行内状态提示，减少表单空白并保持绑定检查逻辑不变。未改后端 API 和生成逻辑。