# P8-FIX7 高消费动作二次确认提示修复

## 1. 背景

用户反馈声音克隆和声音设计是高消费动作，点击按钮前需要明确提示用户单次可能约人民币 10 元级别，实际价格以 MiniMax 官网为准。

## 2. 问题分析

| 问题 | 原因 | 影响 | 修复方案 |
|---|---|---|---|
| 高消费动作无费用提示 | 现有确认只说"可能产生费用" | 用户对费用无心理预期 | 增加独立确认，提示约 10 元级别 |
| 顶部提示不等于动作级确认 | 确认在 guardedJsonFetch 内，只对 minimax | mock provider 无确认 | 在 handler 函数开头增加独立确认 |
| 费用说明不具体 | _OPERATION_MESSAGES 无具体金额 | 用户无法评估成本 | 文案明确写"约人民币 10 元级别，以官网为准" |

## 3. 修复内容

- 新增 `confirmHighCostVoiceAction(actionName)` helper：使用 `window.confirm()` 返回 boolean，文案包含高消费提醒、约 10 元级别、MiniMax 官网价格为准
- `handleCloneVoice()` 开头增加 `if (!confirmHighCostVoiceAction('声音克隆')) { return; }`
- `handleDesignVoice()` 开头增加 `if (!confirmHighCostVoiceAction('声音设计 / 创建音色')) { return; }`
- 克隆按钮下方新增 `.high-cost-inline-hint` 行内提示文字
- 生成设计按钮下方新增 `.high-cost-inline-hint` 行内提示文字
- 新增 `.high-cost-inline-hint` CSS：font-size: 0.78rem，color: #c05621

## 4. 确认文案说明

```
即将执行：声音克隆

这是高消费 / 工程验证能力。
声音克隆、声音设计或创建音色可能产生较高费用。
单次操作可能是约人民币 10 元级别，实际价格以 MiniMax 官方价格页为准。

请确认你已经了解费用、额度限制和音频素材合规要求。

是否继续？
```

## 5. API endpoint 不变说明

- 未改后端 API
- 未改克隆接口 `/api/voice/clone/create`
- 未改声音设计接口 `/api/voice/design/create`
- 未改 Cost Guard
- 未改 Resource Guard
- guardedJsonFetch 原有 minimax 确认保留（作为双重确认）

## 6. 未处理事项

- 未做真实价格拉取
- 未做官网价格链接配置
- 未做计费系统
- 未做 P8-BE3

## 7. 验证命令

### 7.1 高消费确认 helper 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for m in ["function confirmHighCostVoiceAction", "高消费", "约人民币 10 元级别", "MiniMax 官方价格", "window.confirm"]:
    assert m in html, f"Missing {m}"
print("PASS")
PY
```

### 7.2 克隆确认检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
assert "confirmHighCostVoiceAction('声音克隆')" in html, "Missing clone confirm"
print("PASS")
PY
```

### 7.3 声音设计确认检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
assert "confirmHighCostVoiceAction('声音设计 / 创建音色')" in html, "Missing design confirm"
print("PASS")
PY
```

### 7.4 API marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for m in ["guardedJsonFetch", "apiJson", "/api/voice"]:
    assert m in html, f"Missing {m}"
print("PASS")
PY
```

## 8. 验证结果

- 高消费确认 helper 检查: PASS
- 克隆确认检查: PASS
- 声音设计确认检查: PASS
- API marker 检查: PASS
- pytest: 384 passed, 6 skipped

## 9. 阶段结论

**P8-FIX7 已完成。** 声音克隆和声音设计 / 创建音色按钮已增加高消费二次确认，提示用户单次可能产生约 10 元级别费用并以 MiniMax 官网价格为准。用户取消时不会调用后端，用户确认后原流程保持不变。