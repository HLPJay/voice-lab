# Design Reference — 想Ta了 H5

## 设计来源

本 H5 前端（`apps/xiangta-h5/`）基于以下设计稿实现：

**`design_h5/想他了点击版本/`**

### 设计文件索引

| 文件 | 说明 |
|---|---|
| `想他了 · Mobile Design.html` | 移动端交互设计总览 |
| `app.html` | 主应用页面原型 |
| `screens.jsx` | 各屏幕状态定义 |
| `components.jsx` | UI 组件设计规范 |
| `tokens.jsx` | 设计 token（颜色、字体、间距） |
| `states.jsx` | 交互状态机 |
| `letters-store.jsx` | 信笺数据结构参考 |

## 实现映射

| 设计流程 | H5 实现 |
|---|---|
| bootstrap 加载 | `loadBootstrap()` → `GET /api/xiangta/bootstrap` |
| 文案建议生成 | `generateSuggestions()` → `POST /api/xiangta/suggestions` |
| 选择建议 | `selectSuggestion(index)` |
| 语音生成 | `generateTts()` → `POST /api/xiangta/tts` |
| 保存信笺 | `saveLetter()` → `POST /api/xiangta/letters` |
| 历史记录 | `loadLetters()` → `GET /api/xiangta/letters` |

## 约束

- B7-1 MVP 为干跑合约（dry-run），不生成真实音频
- 设计稿为参考依据，H5 实现以后端 API contract 为准
