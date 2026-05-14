# P8-BE3A 资产清理策略审查与只读统计

## 1. 背景

P8-CHECK1 建议不要直接物理删除。当前历史任务支持软删除 status="deleted"，但资产文件（音频、字幕）长期堆积。P8-BE3A 本阶段只做只读统计，不删除任何数据。

## 2. 当前代码事实

### 2.1 AudioAsset 字段

```
id, job_id, provider, model, file_path, file_url, format,
duration_ms, sample_rate, bitrate, channel, usage_characters,
metadata_json, created_at
```

### 2.2 SubtitleAsset 字段

```
id, job_id, audio_asset_id, subtitle_type, file_path, srt_path,
timeline_json, created_at
```

### 2.3 storage_dir 默认

`./storage`（来自 `app.core.config.get_settings().storage_dir`）

### 2.4 AssetService 保存路径

```
AudioAsset.file_path = result.audio_path（来自 provider）
SubtitleAsset.file_path = storage/subtitles/<date>/<subtitle_id>.json
SubtitleAsset.srt_path = storage/subtitles/<date>/<subtitle_id>.srt
```

### 2.5 BE2 软删除语义

`VoiceJob.status = "deleted"`，不物理删除 VoiceJob row、AudioAsset row、SubtitleAsset row 或任何文件。

## 3. 本阶段安全边界

- 不删除文件
- 不删除数据库记录
- 不修改 job 状态
- 不读取音频内容
- 不打印敏感配置（如 API key）
- 不在报告中输出绝对敏感路径
- 只输出统计报告（JSON）和控制台摘要

## 4. 审查脚本说明

- 脚本：`scripts/audit_assets.py`
- 默认输出：`docs/generated/asset_audit_report.json`
- 支持 `--output` 参数指定报告路径
- 支持 `--storage-dir` 参数指定存储目录
- 示例：`python scripts/audit_assets.py --output docs/generated/asset_audit_report.json`

## 5. 统计维度

| 维度 | 字段 |
|---|---|
| AudioAsset 总数 | summary.audio_asset_count |
| SubtitleAsset 总数 | summary.subtitle_asset_count |
| VoiceJob 总数 | summary.voice_job_count |
| VoiceJob 状态分布 | summary.job_status_counts |
| storage 文件总数 | summary.storage_file_count |
| storage 总大小（字节） | summary.storage_total_bytes |
| orphan storage files | orphan_files.audio/subtitle_files_not_referenced_by_db |
| missing file DB records | cleanup_candidates_readonly.missing_file_db_records |
| deleted job assets | cleanup_candidates_readonly.deleted_job_assets |

## 6. 清理候选定义

这些都是候选，不代表本阶段会删除。

### A. orphan_storage_files

存在于 `storage/audio` 或 `storage/subtitles` 中，但没有被 `AudioAsset.file_path` / `SubtitleAsset.file_path` / `SubtitleAsset.srt_path` 引用的文件。

### B. missing_file_db_records

数据库中 AudioAsset / SubtitleAsset 指向的 `file_path` / `srt_path` 不存在。

### C. deleted_job_assets

AudioAsset / SubtitleAsset 关联的 `VoiceJob.status == "deleted"`。

## 7. 执行命令

```bash
python scripts/audit_assets.py --output docs/generated/asset_audit_report.json
```

## 8. 执行结果摘要

```
AudioAsset: 436
SubtitleAsset: 169
VoiceJob: 532
Storage files: 33,803
Orphan audio files (not in DB): 19,505
Orphan subtitle files (not in DB): 14,298
Missing file DB records (audio): 0
Missing file DB records (subtitle): 0
Deleted job audio assets: 0
Deleted job subtitle assets: 0
Report: docs/generated/asset_audit_report.json
```

### 关键发现

- **大量孤立文件**：storage 中有 19,505 个音频文件和 14,298 个字幕文件没有被数据库记录引用（总计 33,803 个文件）
- **DB 记录完整**：所有 436 个 AudioAsset 和 169 个 SubtitleAsset 的 file_path 均存在，无缺失文件记录
- **已删除任务资产为 0**：当前数据库中没有 status="deleted" 的 VoiceJob 关联的资产（说明还没有真正使用过软删除后的清理，或者孤立文件来自更早期的历史）
- **storage 文件总量很大**：需要评估清理价值

## 9. orphan 文件来源分析

孤立文件来源可能是：

1. 早期测试阶段产生的临时文件（mock provider 测试）
2. provider 返回了音频文件路径但没有保存到数据库记录
3. 数据库记录被手动删除但文件未清理
4. 不同步导致的悬空文件

由于已删除任务的资产为 0，孤立文件与软删除逻辑无关，更多是历史积累问题。

## 10. 下一阶段建议

**P8-BE3B：资产清理策略确认**

策略草案：

1. **不直接删除所有孤立文件**，因为它们可能是历史正常生成的
2. **支持 dry-run 模式**：只输出将要删除的文件清单，不实际删除
3. **按时间清理**：优先清理 N 天前、且关联 job 状态为成功/失败的孤立文件
4. **按文件名过滤**：跳过最近的孤立文件（可能是正在进行的任务产生的）
5. **必须人工确认**：删除前输出清单，人工确认后再执行
6. **删除后输出审计日志**：记录删除的文件清单、时间、操作人

## 11. 阶段结论

**P8-BE3A 已完成。** 当前阶段已新增只读资产审查脚本，用于统计数据库资产记录（436 AudioAsset + 169 SubtitleAsset）、磁盘文件（33,803 个）、孤立文件（19,505 音频 + 14,298 字幕）、缺失文件和 deleted job 关联资产（0）。本阶段未删除任何文件或数据库记录。下一阶段应先确认清理策略（建议从孤立文件清理开始，支持 dry-run），后再考虑 dry-run 清理工具。