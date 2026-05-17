# P16 V1 Closeout

## V1 已完成能力

- MiniMax 主链路：单段同步 TTS、异步批处理、WebSocket 流式链路可用
- Xiaomi MiMo 单段同步 TTS 样板：作为当前 V1 的第二 Provider 样板接入
- Provider 切换：Provider-first 绑定与工作台切换链路已打通
- 本地统计口径：管理面板和首页统计明确为本地统计，不冒充官方账单
- Xiaomi MiMo ProviderCallLog：Xiaomi MiMo 调用已写入本地 ProviderCallLog，并可进入 Provider 统计
- Admin provider filter：支持按 provider 聚焦管理面板数据
- Voice preview 测试口径对齐：`tests/test_voice_preview.py` 已适配 provider 必填 schema
- Xiaomi MiMo 测试口径对齐：`tests/test_xiaomi_mimo_chat_tts_adapter.py` 已对齐当前 V1 enabled / capabilities 口径
- Voice Profile 人设归档生命周期：支持 `is_active=false` 软归档，归档后不可用于新生成

## V1 不承诺能力

- 官方账单同步
- 官方余额查询
- model-level stats
- 多用户 SaaS billing
- Xiaomi MiMo clone/design 产品化
- 高并发多人系统
- 日志自动清理
- E2E 全绿

## 当前剩余豁免项

- jsdom 环境依赖
- Playwright E2E locator 过期
- full-suite ordering pollution
- full-suite env/API key 隔离问题

## 人工验收清单

- MiniMax 单段生成
- Xiaomi MiMo 单段生成
- Admin 看到 `xiaomi_mimo`
- Provider/model header 不错配
- 本地统计不冒充官方账单
- 人设创建
- 人设绑定
- 人设归档
- 归档后不能生成
- 历史记录仍保留

## 合并 main 条件

- scoped regression 通过
- 人工验收通过
- 剩余 full suite 失败已归类为可豁免
- 无真实 API secret 泄露
- 无数据库 schema 未说明变更

## V2 Backlog

- 批量归档测试人设脚本
- 人设恢复 restore API
- 人设 create/update/archive/restore API 规范化
- jsdom 依赖补齐
- E2E 修复
- 日志清理策略
- 官方账单同步
- model-level stats
- 上层软件 profile-render API
