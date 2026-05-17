# NEXT-PRIORITY-REVIEW：下一阶段优先级确认

## 1. 当前状态

当前已完成 P16-WORKSPACE-RESTORE-CLOSE。workspace 最近样本完整恢复能力已上线。

## 2. 已完成模块

| 模块 | 状态 |
|---|---|
| P16-WORKSPACE-RESTORE-* | ✅ 完整恢复能力已上线 |
| P16-CANCEL-FIX1 | ✅ 取消确认语义修复 |

## 3. 候选项列表

| 阶段 | 内容 | 背景 |
|---|---|---|
| P16-PROVIDER-BOUNDARY-A0 | Provider / Mock / Capability 边界审查 | 用户真实测试暴露问题 |
| P16-VARIANTS-UX-FIX1 | 多版本生成等待态 | UX 问题 |
| P17-CREATION-RECORD-A0 | 服务端创作记录设计 | 长期架构 |
| P13-HISTORY-SECURITY-FIX1 | 历史文本 escaping 安全债 | 小型安全债 |
| P15-STATS-B1 | 本地统计面板 | 已决策暂缓 |
| P15-SERVER-STATS-A0 | 服务端统计 | 已决策暂缓 |

## 4. 候选项优先级分析

### P16-PROVIDER-BOUNDARY-A0 — **推荐优先级：P0/P1**

用户真实测试暴露的问题：
- 选择 Mock 后仍可能生成
- Mock provider 无绑定时可能 fallback 到 MiniMax
- 前端显示的 provider 与后端实际 resolved provider 可能不一致
- Provider 能力差异未完全驱动前端 UI
- 未来新增其他大模型时，流式/字幕/情绪/克隆/音色库等能力可能不一致

风险：Provider 边界不清会影响后续所有大模型横向扩展。若不先理清，后续接 OpenAI TTS / Azure / ElevenLabs / 其他音频模型时会到处写 `if provider == xxx`。

### P16-VARIANTS-UX-FIX1 — 推荐优先级：P1 UX，后置

多版本试音生成时等待态不够明显，用户只能看到按钮"生成中"。这是体验问题，不是底层架构问题。可以后置到 Provider 边界审查后。

### P17-CREATION-RECORD-A0 — 推荐优先级：P2 / 长期架构，后置

当前 workspace restore 是前端 localStorage 最近样本恢复缓存，不是服务端长期创作记录。长期架构方向重要，但当前产品还未进入跨设备/多用户/长期历史阶段。

### P13-HISTORY-SECURITY-FIX1 — 推荐优先级：P2 小安全债，后置

历史文本 snippet escaping 是小型安全债。应保留，但不比 Provider 边界更紧急。

### P15-STATS-B1 / P15-SERVER-STATS-A0 — 推荐优先级：Backlog

统计模块此前已决策暂缓。管理面板已有部分统计能力。本地统计价值有限，服务端统计投入较大。继续后置，等产品真实使用量起来后再启动。

## 5. 推荐下一阶段

**P16-PROVIDER-BOUNDARY-A0：Provider / Mock / Capability / 新大模型接入边界审查**

理由：
1. Provider / Mock 问题是用户真实测试暴露的问题，关系到真实成本和真实调用
2. 该问题是底层架构问题，相比多版本等待态优先级更高
3. 相比服务端创作记录，更贴近当前功能稳定性
4. 相比统计模块，对继续产品化更关键
5. 未来新大模型接入前必须先理清的底层边界

## 6. P16-PROVIDER-BOUNDARY-A0 初步范围

下一阶段应审查：
1. Mock 的产品语义：是否必须是纯测试 Provider
2. mock_fallback_provider 是否合理
3. request.provider 与 resolved_provider 的关系
4. CostGuard 应以前端 provider 还是 resolved_provider 为准
5. Provider capability 是否足以表达能力差异
6. 前端 Provider 下拉是否应由 capabilities 动态驱动
7. 不支持流式 / 字幕 / 情绪 / 克隆的 Provider 如何处理
8. Provider 无 binding 时前后端如何拦截
9. 新增 Provider 的接入 checklist
10. 哪些修复进入后续 P16-PROVIDER-MOCK-FIX1

## 7. 后置项

继续后置：P16-VARIANTS-UX-FIX1 / P17-CREATION-RECORD-A0 / P13-HISTORY-SECURITY-FIX1 / P15-STATS-B1 / P15-SERVER-STATS-A0

## 8. 决策结论

下一阶段进入 **P16-PROVIDER-BOUNDARY-A0**。
