# P12 Usage Archive - 2026-05-15

## 归档目的

本归档用于封存 Voice Lab 在 P12 真实使用修复阶段结束时的稳定状态，作为后续 P13 开发的基准点。

## 当前稳定提交

- Commit: 569d4041f1cb3a675eec08b19da57e2f230248a8
- Branch: dev
- Stage: P12-USAGE-CHECK2

## 当前产品定位

Voice Lab 当前是基于 MiniMax 音频能力的本地 Web App / 单用户 AI 音频创作工作台。

当前不是：

- 多人 SaaS
- 高并发多人系统
- 开放 API 平台
- 登录系统产品
- 移动端 Native App

## 当前已支持能力

- 同步 T2A
- 异步 T2A
- WebSocket 流式 T2A
- 批量长文本生成
- 批量剧本生成
- 字幕生成
- 音频资产保存与下载
- 历史记录
- Admin 统计
- Resource Guard 并发保护
- smoke test runner

## P12 收口内容

P12 真实使用修复阶段已经最终收口，主要完成：

- FIX1/2/3/3B：绑定提示同步
- UX1/2/3：UI/UX 优化
- FIX4/4A0/4B0：下载规范化
- UX4/4A0/4B1：quick bind 布局
- FIX5/5A0/5B1/5B2：音频时长展示与持久化
- UX5/UX5-FIX：分段文案 + HTML 引号
- FIX6/6A0/6B1：duration persistence + pydub fallback
- UX6：sentence 语义修复（每句一段）

## 当前限制

- 不承诺多人 SaaS
- 不承诺高并发
- 不引入 Redis / PostgreSQL / Worker 队列
- 不做 BYOK
- 不做登录系统
- 不做移动端 H5 优先优化
- 声音克隆 / 声音设计仍属于高级能力，暂缓产品化

## 后续入口

下一阶段从 P13 开始：

- P13-CREATION-A0：样本观察侧边栏设计
- 第一阶段只做设计审查
- 不直接开发功能
- 不调用真实 MiniMax
