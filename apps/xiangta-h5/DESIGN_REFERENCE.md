# XiangTa H5 Design Reference

## 设计来源

原型目录：

- `design_h5/想他了点击版本/`

## 权威来源

当前 `apps/xiangta-h5/` 的页面结构与交互效果，统一以 `design_h5/想他了点击版本/` 为准。

本目录下的 H5 不再把旧表单页当作最终结构，而是：

- 以原型的五屏流程作为页面骨架
- 以项目已有后端 API 作为真实数据来源
- 用最小 adapter 吃掉接口差异

## 已读取的原型文件

- `design_h5/想他了点击版本/app.html`
- `design_h5/想他了点击版本/想他了 · Mobile Design.html`
- `design_h5/想他了点击版本/screens.jsx`
- `design_h5/想他了点击版本/components.jsx`
- `design_h5/想他了点击版本/tokens.jsx`
- `design_h5/想他了点击版本/states.jsx`
- `design_h5/想他了点击版本/letters-store.jsx`

## 实现映射

| 原型页面 | 当前真实接线 |
| --- | --- |
| Home | `loadBootstrap()` -> `GET /api/xiangta/bootstrap` |
| Compose | `generateSuggestions()` -> `POST /api/xiangta/suggestions` |
| Suggest | `selectSuggestion()` -> 前端状态切换 |
| Voice | `generateTtsTask()` -> `POST /api/xiangta/tts/tasks`，`pollTtsTask()` -> `GET /api/xiangta/tts/tasks/{taskId}` |
| History | `loadLetters()` -> `GET /api/xiangta/letters` |

## 保留的运行时约束

- formal mode 仍是默认主路径
- 只有 `?mode=dev` 才显示 Dev Panel
- formal mode 不调用 `/api/xiangta/core/profiles`
- formal mode 不传 `profileId`
- no-audio 仍允许保存文字信笺
- 正式语音主路径仍是 `/api/xiangta/tts/tasks`

## 不再采用的旧思路

- 不再以旧 `index.html` 表单结构为主继续局部修补
- 不再因为现有 DOM 方便而改变原型步骤条、卡片形态、底部 CTA 位置
- 不再把 `/api/xiangta/tts` 作为 formal 主路径
