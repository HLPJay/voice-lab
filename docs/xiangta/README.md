# 想Ta了产品文档索引

本目录归档 XiangTa（想Ta了）产品层的权威设计文档。旧目录 `docs/product/XIANGTA_*.md` 保留为 A0-A2 历史记录；后续产品构建、评审和实现任务以本目录为准。

## 文档清单

| 文档 | 用途 |
|---|---|
| [PRODUCT_POSITIONING.md](PRODUCT_POSITIONING.md) | 产品定位：想Ta了是什么、不是什么，以及与 Voice Lab Core 的关系 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 三层架构：Mobile App → XiangTa Backend → Voice Lab Core |
| [CORE_CAPABILITIES.md](CORE_CAPABILITIES.md) | Core 已有 API 能力清单，以及 XiangTa 应如何复用 |
| [CODE_INVENTORY.md](CODE_INVENTORY.md) | 现有代码保留、调整、废弃清单 |
| [PRODUCT_CONFIG_MODEL.md](PRODUCT_CONFIG_MODEL.md) | P17-XIANGTA-PRODUCT-CONFIG-A0：产品配置模型设计 |
| [API_CONTRACT.md](API_CONTRACT.md) | 用户端 API、管理端 API、Core 调用契约 |
| [ROADMAP.md](ROADMAP.md) | 后续实施路线：从文档确认到 B1/B2/B3 实现 |
| [MVP_CLOSEOUT_REPORT.md](MVP_CLOSEOUT_REPORT.md) | P17-XIANGTA-MVP-CLOSEOUT-B7：MVP 能力清单、限制、gaps、合并前验收结论 |
| [MERGE_DEV_REVIEW.md](MERGE_DEV_REVIEW.md) | P17-XIANGTA-MERGE-DEV-REVIEW：合并 dev 前代码审查报告（结论：PASS_WITH_NOTES） |

## 当前状态（2026-05-18）

**MVP 主流程已闭环（P17-XIANGTA-MVP-CLOSEOUT-B7 完成）**，全套 512 tests 通过。

当前已就绪：bootstrap / template suggestions / tts（mock path）/ letters（进程内）/ Admin 配置读写 / H5 静态前端。

**当前不接真实 Provider / LLM**：suggestions 为模板版，tts 默认路径返回稳定降级（no_provider）。

下一步：`P17-XIANGTA-MERGE-DEV-REVIEW`（合并 dev 前人工审查），真实 Provider 接入作为审查通过后的新阶段。

---

## 当前结论

A0-A2 不需要推翻。保留 API 层、ProductService、BootstrapService、TtsOrchestrator、Gateway、ErrorTranslator、边界测试和 dry-run 编排；调整的是声线预设的数据来源。

废弃的是早期临时抽象：

- `voice_presets.json` 作为真实声线来源的定位
- `core_binding_key` 概念
- `PresetMapper.resolve_binding()` 承担声线映射的职责

修正后的方向：

- 用户端只看到 `voicePresetId`，不看到 `profile_id`
- 服务端通过 `VoicePresetMappingService` 把 `voicePresetId` 映射到 Core `profile_id`
- `tone_presets` 是 XiangTa 自有产品配置，不来自 Core
- TTS 生成复用 Core `POST /api/voice/render`
- 音频下载复用 Core `GET /api/voice/assets/{asset_id}/download`
- Provider 状态复用 Core `GET /api/voice/runtime/status`
