# H5 Manual Validation — C10B

## 1. 验证目标

验证 H5 v2 是否已经形成：**原型交互链路 + 真实 API 接线 + 情绪表达闭环**。

## 2. 验证环境

```bash
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 0.0.0.0 --port 5174
```

访问：
- `http://127.0.0.1:5174/h5/index.html`
- `http://127.0.0.1:5174/h5/index.html?mode=dev`

## 3. 主链路验证（逐步）

```
1.  打开 Home → 看到品牌标题 + 时间问候语 + status pill
2.  选择 recipient：恋人 / 父母 / 朋友 / 自己
3.  选择 scene：想念 / 道歉 / 感谢 / 安慰 / 晚安
4.  点击"开始表达"
5.  进入 Compose 第 1 步
6.  点击"用一个例子开始" → textarea 自动填入当前 scene 的例子
7.  已有输入时再次点击 → 追加例子，不覆盖
8.  字数正常更新，"帮我整理表达"按钮启用
9.  点击"帮我整理表达"
10. 进入 Suggest 第 2 步
11. 查看 3 条建议：克制版 / 温柔版 / 真诚版
12. 选择一条建议 → 底部 CTA 启用
13. 点击"用这条 · 生成语音"
14. 进入 Voice 第 3 步
15. 选择音色 / 调整 tone
16. 点击"生成语音"
17. 等待 task 完成 → 显示 audio 或 失败提示
18. 无 audioUrl 时仍显示"可先保存文字信笺"
19. 保存信笺（填写标题或不填）
20. 进入 History
21. 看到刚保存的记录（含文字 / 含音频）
```

## 4. 每屏验收清单

### Home

| 检查项 | 标准 | 通过 |
|---|---|---|
| phone-shell 容器 | 宽度 max-430px，圆角 30px（桌面） | |
| 时间问候语 | 显示"月/日 · 周几 · 时段 · HH:MM" | |
| recipient grid | 2列卡片，带 icon + label + hint | |
| scene grid | 2列 chip，带 label + hint | |
| "开始表达"按钮 | 有 recipient + scene 时启用，无则禁用 | |
| status pill | 显示 MiniMax provider 状态 | |
| Dev Panel | formal mode 隐藏，?mode=dev 显示 | |

### Compose

| 检查项 | 标准 | 通过 |
|---|---|---|
| 步骤条 | 显示 1/3 进度 | |
| 标题 | "想念 · 给恋人" 格式 | |
| "用一个例子开始" | 点击填入当前 scene 示例 | |
| textarea | placeholder 为当前 scene 示例 | |
| 字数统计 | 实时更新，不超过 500 | |
| "帮我整理表达" | 4字以下禁用，4字以上启用 | |
| 引导问题卡 | 3 张 prompt card，点击追加到 textarea | |
| 风险提示 | 检测到"都是你""必须"等词时提示 | |
| 空状态 | 未输入时 CTA 禁用 | |

### Suggest

| 检查项 | 标准 | 通过 |
|---|---|---|
| 步骤条 | 显示 2/3 进度 | |
| AI 理解摘要 | 显示 summary + intent | |
| 建议卡片 | 3 张，克制版/温柔版/真诚版 | |
| 选择状态 | 选中卡片高亮，底部 CTA 启用 | |
| "返回改字" | 可回到 Compose | |
| risk hint | 显示当前 rawText 风险提示 | |
| 风格标签 | 每张卡片显示风格名称 | |

### Voice

| 检查项 | 标准 | 通过 |
|---|---|---|
| 步骤条 | 显示 3/3 进度 | |
| 文字预览 | 显示选中文案 | |
| 音色选择 | 显示 voice option，可切换 | |
| tone chips | 显示 tone 选项 | |
| 预计时长 | 显示时长估算 | |
| 生成按钮 | 调用 /api/xiangta/tts/tasks | |
| task 轮询 | 未完成时显示进度状态 | |
| audio 播放器 | 有 audioUrl 时显示 audio 控件 | |
| 失败提示 | task failed 或无 audio 时显示提示 | |
| 保存信笺 | 有无 audioUrl 均可保存文字 | |
| 保存成功 | toast 提示，进入 History 可查 | |

### History

| 检查项 | 标准 | 通过 |
|---|---|---|
| 历史卡片 | 显示标题/日期/收件人/场景/含语音标记 | |
| 预览文字 | 显示前 76 字 + 省略号 | |
| audio 播放器 | 含语音记录有 audio 控件 | |
| 刷新按钮 | 可重新加载最新记录 | |
| 空状态 | 无记录时显示空态提示 | |

### Dev Mode

| 检查项 | 标准 | 通过 |
|---|---|---|
| Dev Panel 显示 | ?mode=dev 时可见 | |
| core profile select | 可选择不同 core profile | |
| 旧接口 /tts | dev 可见，formal 隐藏 | |
| formal 不泄露 | coreProfileId / profileId 不出现在 formal UI | |

## 5. A/B/C 问题分级

### A 类阻塞（必须修复）

- 页面打不开（500 / 白屏）
- 主按钮点击无响应（无 network 记录）
- `/suggestions` 调用返回错误且无 fallback
- `/tts/tasks` 调用失败且无恢复提示
- 无 audioUrl 时无法保存文字信笺
- 保存后 History 看不到记录
- formal mode 泄露 coreProfileSelect / profileId
- 响应体出现 apiKey / providerRawResponse / coreProfileId
- 横向溢出 / 底部 CTA 被裁切

### B 类非阻塞（记录后续优化）

- 文案换行不够好
- 卡片密度略高
- 按钮视觉与原型有差异
- toast 体验可优化
- 部分场景文案还不够自然
- 引导问题 prompt 可更贴合场景

### C 类 cleanup（后续整理）

- H5 静态测试数量偏多，可压缩
- app.js 仍未拆分 ui-meta / ui-components
- CSS 命名可进一步整理
- 文档措辞可优化
