# P18_XIANGTA_H5_PROTOTYPE_REBUILD_C10A_FIX2

## 备份

- v1 备份 tag：`p18-h5-v1-before-prototype-rebuild`
- 结果：已创建，并已推送到 `origin`

## 读取的 design_h5 文件

- `design_h5/想他了点击版本/app.html`
- `design_h5/想他了点击版本/想他了 · Mobile Design.html`
- `design_h5/想他了点击版本/screens.jsx`
- `design_h5/想他了点击版本/components.jsx`
- `design_h5/想他了点击版本/tokens.jsx`
- `design_h5/想他了点击版本/states.jsx`
- `design_h5/想他了点击版本/letters-store.jsx`

## 本次处理

- 重建 `apps/xiangta-h5/index.html`，改为原型主导的五屏结构
- 重建 `apps/xiangta-h5/styles.css`，按手机容器、深色情绪氛围、暖金 CTA、步骤条与卡片体系收口
- 重组 `apps/xiangta-h5/app.js`，保留真实 API wiring：
  - `/api/xiangta/bootstrap`
  - `/api/xiangta/suggestions`
  - `/api/xiangta/tts/tasks`
  - `/api/xiangta/letters`
- 保留 formal/dev mode
- 保留 no-audio save

## 差异表

| 页面/交互 | 原型要求 | 旧 H5 状态 | 本次处理 | 未对齐原因 |
| --- | --- | --- | --- | --- |
| Home | 手机容器 + 情绪入口 | 局部对齐 | 按原型重建 | - |
| Compose | 第 1 步 + 进度 + 引导问题 | 普通表单感偏强 | 按原型重建 | - |
| Suggest | 第 2 步 + 建议选择 | 更像普通列表 | 按原型重建/对齐 | - |
| Voice | 第 3 步 + 语音状态 | 普通结果框 | 按原型重建/对齐 | - |
| History | 信笺卡片 | 普通列表 | 按原型对齐 | - |

## 原型 mock 被真实 API 替换的部分

- 建议卡：由 `/api/xiangta/suggestions` 返回
- 语音任务：由 `/api/xiangta/tts/tasks` + poll 返回
- 历史信笺：由 `/api/xiangta/letters` 返回
- 首页选择项与 providerStatus：由 `/api/xiangta/bootstrap` 返回

## 未完全对齐

- 暂未把原型里的所有微动效完整移植到静态 H5
- 暂未做逐像素比对，仅保证结构、层级、CTA、卡片与主流程按原型重建

## 截图验收建议

- Home 390px
- Compose 390px
- Suggest 390px
- Voice 390px
- History 390px

## Follow-up cleanup

- 手工验证 Compose / Suggest / Voice 的中文文案与原型是否还需逐条微调
- 检查历史页在真实长文本和含音频状态下的卡片密度
- 在 C10B 中记录手机端安全区、底部 CTA、空态与失败态截图

## 下一步

- `P18-XIANGTA-MANUAL-H5-VALIDATION-C10B`
