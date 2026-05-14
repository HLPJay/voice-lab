# P8-UX1 桌面宽屏布局与响应式适配

## 1. 背景

用户反馈桌面浏览器很宽，但页面主体占用偏窄。

P8-FIX5B 已完成历史单行布局修复。当前阶段只做前端 CSS 布局宽度优化，不涉及业务逻辑。

## 2. 问题分析

| 问题 | 原因 | 影响 | 修复方案 |
|---|---|---|---|
| 主体容器偏窄 | `.container { max-width: 800px }` | 桌面宽屏下大量横向空间浪费 | 扩大 max-width 到 1180px |
| 无 CSS 宽度变量 | 直接写死 800px | 无法响应不同屏幕 | 引入 `--page-max-width` 和 `--page-padding-x` 变量 |
| 无桌面宽屏响应式 | 缺少大屏媒体查询 | 1440px+ 超宽屏没有适配 | 添加 `@media (min-width: 1440px)` |
| 无平板适配 | 缺少 1024px 断点 | 平板横向空间未利用 | 添加 `@media (max-width: 1024px)` |
| 历史单行布局需保留 | 宽屏调整不能破坏已有布局 | P8-FIX5B 成果需保护 | 不改 `.history-row` grid 结构 |

## 3. 修复内容

- CSS 顶部增加变量：`--page-max-width: 1180px`、`--page-padding-x: 24px`
- `.container` 的 `max-width: 800px` 改为 `var(--page-max-width)`，并添加 `padding: 0 var(--page-padding-x)`
- 新增 `@media (min-width: 1440px)`：容器最大宽度 1240px
- 新增 `@media (max-width: 1024px)`：容器最大宽度 960px，padding 20px
- `@media (max-width: 760px)`：padding 14px（同时保留已有的历史 row 单列 override）
- `@media (max-width: 600px)`：保持原有的 config-grid/variants-grid 单列
- 历史 row 的 grid 布局不变（760px media query 仅覆盖 narrow 情况）

## 4. 修改后布局策略

```
桌面超宽屏（≥1440px）：最大宽度 1240px，居中，padding 24px
普通桌面（≥1024px）：最大宽度 1180px，居中，padding 24px
平板（≥761px）：最大宽度 960px，居中，padding 20px
窄屏（≤760px）：padding 14px，历史 row 降级为单列
超窄屏（≤600px）：保持 600px 断点调整
```

## 5. API endpoint 不变说明

- 未改后端 API
- 未改 `/api/voice/jobs`
- 未改 `/api/voice/assets`
- 未改生成接口
- 未改音色接口

## 6. 未处理事项

- 未处理 P8-BE3（历史任务与资产物理清理）
- 未处理 P8-5（localStorage 最近任务恢复）
- 未拆分 index.html
- 未引入 React / Vue

## 7. 验证命令

### 7.1 变量检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for v in ["--page-max-width", "--page-padding-x"]:
    assert v in html, f"Missing {v}"
print("PASS")
PY
```

### 7.2 容器宽度检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
assert "max-width: var(--page-max-width)" in html, "Container should use variable"
assert "max-width: 800px" not in html, "Old 800px still exists"
print("PASS")
PY
```

### 7.3 响应式检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for mq in ["@media (min-width: 1440px)", "@media (max-width: 1024px)", "@media (max-width: 760px)"]:
    assert mq in html, f"Missing {mq}"
print("PASS")
PY
```

### 7.4 历史 grid 保留检查

```bash
python - <<'PY'
from pathlib import Path, re
html = Path("app/static/index.html").read_text(encoding="utf-8")
match = re.search(r"\.history-row\s*\{([^}]*)\}", html, re.S)
block = match.group(1)
assert "display: grid" in block
assert "grid-template-columns" in block
assert "flex-wrap" not in block
print("PASS")
PY
```

## 8. 验证结果

- 宽屏变量检查: PASS
- 容器宽度检查: PASS
- 响应式媒体查询检查: PASS
- 历史 grid 保留检查: PASS
- pytest: 384 passed, 6 skipped

## 9. 阶段结论

**P8-UX1 已完成。** 桌面宽屏下页面主体宽度已扩大并保持居中，历史列表、表单和结果区可以更充分利用横向空间；平板和手机端保留响应式适配。未改后端 API 和业务逻辑。