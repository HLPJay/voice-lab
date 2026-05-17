# apps/xiangta_mobile — 想Ta了移动端前端

## 定位

想Ta了的用户界面层（H5 / PWA）。

## 技术栈

- React 18 + Babel Standalone（浏览器端 JSX 转译，无构建步骤）
- 纯 localStorage 持久化（MVP 阶段）
- Python http.server 本地开发，Nginx 生产部署

## 目录结构（待建）

```
apps/xiangta_mobile/
├── app.html          — SPA 入口（移动端，正式工程文件）
├── tokens.jsx        — 设计 Token（从设计稿迁移）
├── components.jsx    — 基础组件库
├── screens.jsx       — 7 个主屏
├── letters-store.jsx — 本地存储层
└── manifest.webmanifest
```

## 与设计参考的关系

`design_h5/想他了点击版本/` 是 Claude Design 阶段的设计稿，**只作为参考**，
不是正式工程目录。正式代码在本目录下维护。

## 开发状态

- P17-A0：目录初始化，等待 A3（TTS 真实实现）后迁移设计稿代码
- 迁移时替换：EXPRESSION_BANK mock → POST /api/xiangta/suggestions
- 迁移时替换：_silentWav() → POST /api/xiangta/tts 返回的真实音频 URL

详见 `docs/product/XIANGTA_MVP_SCOPE.md`
