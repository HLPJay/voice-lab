# P8-BE3A2 资产审查硬化与策略就绪自检

## 1. 背景

P8-BE3A1 已补强资产审查报告。复核后发现仍存在若干策略口径问题：

- pending 未纳入 running-like 状态
- storage_file_count 口径不清（实际只覆盖 audio+subtitles）
- temp / metadata 分布不足
- safe_path_str 仍可能泄露 root 外绝对路径
- subtitle pair 需要区分全量和 orphan
- orphan 不等于可删除
- 缺少策略就绪检查

本阶段继续只读补强，不删除文件，不修改数据库。

## 2. 已知问题整理

| # | 问题 | 修复方案 |
|---|---|---|
| 1 | pending 未纳入 running-like 保护状态 | 新增 STANDARD_RUNNING_JOB_STATUSES 含 pending |
| 2 | protected 混入标准状态 | 拆为 STANDARD + EXTENDED 两组 |
| 3 | storage_file_count 口径不清 | 新增 content_file_count / all_scanned_file_count |
| 4 | temp / metadata 分布不足 | 新增 age/size 分布 + largest 清单 |
| 5 | safe_path_str 可能泄露绝对路径 | 改为 <OUTSIDE_STORAGE_ROOT>/<filename> |
| 6 | subtitle pair 不区分全量和 orphan | 新增 orphan_subtitle_pair_analysis |
| 7 | orphan 缺乏显式不可删除说明 | 新增 not_deletion_recommendation |
| 8 | 缺少策略就绪检查 | 新增 policy_readiness_check |

## 3. 本阶段修复内容

### 3.1 running-like 状态集合拆分

```python
STANDARD_RUNNING_JOB_STATUSES = {"queued", "pending", "running", "processing"}
EXTENDED_RUNNING_JOB_STATUSES = {"protected"}
RUNNING_JOB_STATUSES = STANDARD | EXTENDED
```

报告中 `running_job_guard` 新增 `standard_running_statuses`、`extended_running_statuses`、`running_like_job_count`、`recommended_protection_window_hours: 72`。

### 3.2 storage 统计口径明确化

| 字段 | 定义 |
|---|---|
| storage_file_count / storage_total_bytes | 兼容字段，值等同于 content |
| content_file_count / content_total_bytes | audio + subtitles |
| all_scanned_file_count / all_scanned_total_bytes | audio + subtitles + temp + metadata |
| storage_dirs | 各子目录（audio/subtitles/temp/metadata）的文件数和大小 |

### 3.3 temp / metadata 分布补齐

- `age_distribution.temp_files`
- `age_distribution.metadata_files`
- `size_distribution.temp_files`
- `size_distribution.metadata_files`
- `largest_storage_files.temp`（top 50）
- `largest_storage_files.metadata`（top 50）

### 3.4 safe_path_str 隐私硬化

```python
# 之前（可能泄露绝对路径）
return str(p)
# 之后（脱敏）
return f"<OUTSIDE_STORAGE_ROOT>/{p.name}"
```

### 3.5 orphan subtitle pair 分析

新增 `orphan_subtitle_pair_analysis`：只对 orphan_subtitle 文件集合做 json/srt 配对分析。

### 3.6 report_privacy_check

新增 `report_privacy_check`：自声明 storage_root 已脱敏、不输出绝对路径、不含音频内容、safe_path_policy 说明。

### 3.7 policy_readiness_check

```json
{
  "has_running_like_jobs": true,
  "has_recent_orphan_files": true,
  "has_temp_files": false,
  "has_metadata_files": false,
  "has_missing_db_records": false,
  "has_deleted_job_assets": false,
  "has_large_orphan_files": true,
  "orphan_should_not_be_deleted_directly": true,
  "recommended_next_stage": "P8-BE3B asset cleanup policy confirmation"
}
```

### 3.8 not_deletion_recommendation

`cleanup_candidates_readonly.not_deletion_recommendation` 显式说明：orphan 文件不等于可删除，可能有回填价值，不能直接清理。

### 3.9 报告版本升级

`report_version: "p8-be3a2"`

## 4. 安全边界

- 不删除文件
- 不移动文件
- 不修改数据库
- 不读取音频内容
- 不输出本机绝对路径
- `docs/generated/asset_audit_report.json` 默认不提交

## 5. 执行结果摘要

```
AudioAsset: 436
SubtitleAsset: 169
VoiceJob: 532
Content files (audio+subtitles): 34,119
All scanned files: 34,119
Orphan audio: 19,701
Orphan subtitle: 14,418
Orphan subtitle pairs: 7,209
All subtitle pairs: 7,209
Missing file DB records: 0
Deleted job assets: 0
Running-like jobs (standard): 102 (running:100, processing:2)
Protected audio assets: 0
Protected subtitle assets: 0
Policy readiness: has_running_like_jobs=True, has_recent_orphan=True,
                 has_large_orphan=True, orphan_should_not_be_deleted=True
```

注：temp / metadata 文件数为 0，当前 storage 中不存在这两个目录。

## 6. 对 BE3B 的影响

1. **运行态保护**：BE3B 策略应保护 queued / pending / running / processing 状态任务，建议扩大保护窗口至 72 小时
2. **temp 优先**：当前无 temp 文件，如有则应优先清理（生命周期短）
3. **orphan 回填风险**：orphan 可能有回填价值，清理前必须确认无回填需求
4. **字幕成对处理**：清理 orphan subtitle 必须 json+srt 成对处理，不能只清其中一个
5. **dry-run 默认**：BE3B 清理工具必须支持 dry-run 模式、quarantine 目录、manifest 审计，不允许直接物理删除

## 7. 阶段结论

**P8-BE3A2 已完成。** 当前阶段对资产审查脚本进行了硬化，补充 pending 运行态保护、storage 统计口径（content vs all_scanned）、temp/metadata 分布、root 外路径脱敏、orphan subtitle 配对分析、报告隐私自检和策略就绪检查。本阶段未删除任何文件或数据库记录，下一阶段建议进入 P8-BE3B 资产清理策略确认。
