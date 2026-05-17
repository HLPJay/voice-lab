# Voice Lab Core — 冻结基线声明

## 基线信息

| 字段 | 值 |
|---|---|
| 冻结 commit | `c9637c2b63abf13a151748f4c263f0eadcbfbc27` |
| 冻结日期 | 2026-05-17 |
| 冻结分支 | `dev` |
| 阶段 | P16 已完成，P17 XiangTa 产品层启动 |

---

## 冻结范围（禁止修改）

以下模块在本产品阶段不得修改，视为已归档能力底座：

```
src/voice_lab/**
  ├── adapters/          — Provider 适配层（MiniMax、Xiaomi MiMo 等）
  ├── services/          — TTS / VoiceProfile / VoiceBinding / AudioAsset / History
  ├── models/            — 现有数据库 ORM 模型
  └── api/               — 现有主工作台 API 路由

alembic/               — 数据库 migration（不新增 revision）
app/static/js/**       — 现有主工作台前端模块
design_h5/想他了点击版本/** — 设计稿目录（只读参考）
scripts/probe_*.py     — Provider 探针脚本
```

---

## Core Contract Gap 登记规范

如在产品开发过程中发现 Core 存在能力缺口（接口不足、参数缺失、错误码不齐等），
**不得在产品任务中直接修改 Core**，必须按以下流程登记：

1. 在 `docs/agent/NEXT_TASKS.md` 的 **Core Contract Gap** 区段新增一条
2. 格式：`[ ] GAP-XXX: <描述> — 发现于 P17-XIANGTA-XXXX`
3. 等待独立 Core 修复任务排期，与产品任务完全分离

---

## 已归档能力清单（P16 基线）

| 能力 | 状态 |
|---|---|
| MiniMax TTS speech-2.5-hd | 已验证 |
| Xiaomi MiMo LLM 接入 | 已验证 |
| VoiceProfile / VoiceBinding CRUD | 完整 |
| AudioAsset 存储与查询 | 完整 |
| Provider 能力注册表 | 完整 |
| Batch 长文本拆分 TTS | 完整 |
| 主工作台前端 E2E | 通过 |
