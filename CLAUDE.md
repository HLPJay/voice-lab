# Voice Lab — Claude Code 项目协作配置

## 项目定位

- **项目**：Voice Lab / minimax 音频接口整理项目
- **类型**：本地 Web App / 单用户 AI 音频创作工作台
- **当前阶段**：P9-FE1 前端模块化

## 技术栈

- **Backend**：Python / FastAPI / Provider Adapter / pytest
- **Frontend**：static HTML / plain JavaScript / IIFE / window exports / Playwright E2E
- **不引入**：React / Vue / Vite / Webpack / ES module

## 前端架构

- `index.html` 是 shell，承担 tab/subtab、shared helpers、profile/binding、voice list、audition workstation
- `app/static/js/*.js` 是已抽离的 IIFE 模块
- 模块间通过 `window.*` 通信，onclick 属性保持不变
- 不使用 ES module

## 强制规则

- 每次任务一个 commit
- 修改前执行 `git status -sb` 和 `git log --oneline -5`
- 前端模块迁移必须新增 `test_*_module_is_loaded_and_exports_available` E2E
- 涉及提交链路必须有 mock success E2E
- 涉及错误展示必须有 error E2E
- 高消费接口 E2E 必须 mock，不调用真实 MiniMax
- 功能迁移必须跑 targeted E2E 和前端 E2E 全量

## 禁止事项（未获明确授权前不改）

- 后端 API
- Provider Adapter
- Capability Registry / CapabilityValidator
- `provider_capabilities.js`
- highRisk confirm
- 错误展示 helper
- 共享 batch 状态
- 引入前端框架或构建工具

## 前端模块迁移防覆盖规则

从 index.html 抽取函数到 `app/static/js/*.js` 时：

1. **不要在 index.html 留下同名空函数 stub**。
2. **不要在 inline script 中留下同名函数声明**。
3. 原函数位置只留注释，不留可执行 JS。
4. 因为抽离脚本加载顺序在 inline script 之前，index.html 中的同名函数声明会覆盖 `window.*` 导出。
5. 只检查 `typeof window.xxx === 'function'` 的 module-loaded E2E 不足以覆盖 submit/import/clone/design handlers。
6. Submit/import/clone/design handlers 必须同时有 behavioral E2E，证明 mock API 实际被调用。

## 高风险区域（迁移时需格外小心）

- shared batch state
- profile / binding helpers
- provider capability
- error helpers
- voice list
- audition workstation

## 常用测试命令

```bash
# 检查空白字符
git diff --check

# 前端 E2E 全量
python -m pytest tests/e2e/test_frontend_capabilities.py -q

# targeted E2E
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "clone"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "import"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "design"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "script"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "batch_longtext"
```

## 详细历史

- 详细变更记录：`docs/PROJECT_HEALTH_CHECK.md`
- 前端模块化演进：`docs/P9_FRONTEND_MODULARIZATION.md`
- Agent 协作文档：`docs/agent/`
