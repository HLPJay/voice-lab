# P8-BE3C 资产清理 dry-run 工具

## 1. 背景

P8-BE3B 已确认清理策略。BE3C 只实现 dry-run，不删除、不移动、不修改数据库。orphan 不等于可删除。

## 2. 工具说明

- 脚本：`scripts/cleanup_assets.py`
- 只支持 `--dry-run`
- 默认输出 `docs/generated/asset_cleanup_dry_run.json`
- 不支持 `--execute` / `--quarantine` / `--purge` / `--restore`

## 3. 参数说明

| 参数 | 含义 | 默认值 |
|---|---|---|
| `--dry-run` | 必填，只生成计划 | — |
| `--kind` | temp / orphan-audio / orphan-subtitle / orphan | orphan |
| `--min-age-days` | 最小文件年龄 | 7 |
| `--max-files` | 最大候选文件数量 | 1000 |
| `--output` | 输出 JSON 路径 | docs/generated/asset_cleanup_dry_run.json |
| `--storage-dir` | 存储根目录 | app config |

## 4. 候选规则

### 4.1 orphan audio candidate

条件：
- 文件位于 storage/audio
- 不在 AudioAsset.file_path 引用集合中
- 文件年龄 >= min_age_days
- 不在 72 小时 running-like 保护窗口内
- 不在 quarantine

### 4.2 orphan subtitle pair candidate

条件：
- 文件位于 storage/subtitles
- 不在 SubtitleAsset.file_path / srt_path 引用集合中
- **必须 json+srt 同时存在**（成对）
- 文件年龄 >= min_age_days
- 不在 72 小时保护窗口内
- 不在 quarantine

单边字幕文件（只有 json 或只有 srt）不进入候选，进入 excluded。

### 4.3 temp candidate

条件：
- 文件位于 storage/temp
- 文件年龄 >= min_age_days
- 不在保护窗口内

### 4.4 kind=orphan

包含 orphan-audio 和 orphan-subtitle，不包含 temp。

## 5. 保护规则

- DB 引用文件：永久排除
- quarantine：默认排除
- running-like jobs（queued/pending/running/processing）：72 小时保护窗口
- 保护窗口内文件不得进入候选

## 6. 输出结构

```json
{
  "report_version": "p8-be3c-dry-run",
  "generated_at": "...",
  "mode": "dry-run",
  "storage_root": "<REDACTED>",
  "kind": "orphan",
  "min_age_days": 7,
  "max_files": 1000,
  "protection": {
    "standard_running_statuses": ["pending", "processing", "queued", "running"],
    "extended_running_statuses": ["protected"],
    "running_like_job_count": 102,
    "protection_window_hours": 72,
    "db_referenced_files_excluded": true,
    "quarantine_excluded": true,
    "subtitle_pair_required": true
  },
  "summary": {
    "candidate_file_count": 0,
    "candidate_group_count": 0,
    "candidate_total_bytes": 0,
    "excluded_recent_count": 34435,
    "excluded_db_referenced_count": 0,
    "excluded_running_guard_count": 0,
    "excluded_unpaired_subtitle_count": 0,
    "truncated": false
  },
  "candidates": [],
  "excluded": {...},
  "notices": [...]
}
```

## 7. 执行结果摘要

```
Kind: orphan
Min age days: 7
Candidates: 0 groups / 0 files
Candidate bytes: 0
Excluded recent: 34,435
Excluded DB referenced: 0
Excluded running guard: 0
Excluded unpaired subtitles: 0
Truncated: false
```

注：当前所有 orphan 文件年龄均在 0-7 天内（BE3A2 显示全部为 0-1d 或 1-7d），因此 min-age-days=7 时无候选文件。

## 8. 安全边界

- 未删除文件
- 未移动文件
- 未修改数据库
- 未实现 quarantine
- 未实现 execute
- 未实现 restore
- 未实现 purge
- generated report 默认不提交

## 9. 下一阶段建议

**P8-BE3D：quarantine 隔离执行**

只有在人工审查 dry-run 结果后才能进入。BE3D 将实现 quarantine 移动，保留 manifest，支持 restore。

## 10. Bug 修复记录（P8-BE3C-FIX）

| Bug | 问题 | 修复 |
|---|---|---|
| 1 | `orphan_audio_excl_recent` 错误包含 eligible 文件 | 改为 mutually exclusive 分类：db_referenced / recent / running_guard / eligible |
| 2 | `excluded_db_count` 用残差公式 | 改为直接统计 `db_referenced_audio + db_referenced_subtitle` |
| 3 | `truncated` 用 `candidate_id` 混算 | 改为基于 `total_eligible_file_count > max_files` |
| 4 | `running_guard` 保护窗口口径不透明 | 新增 `protection_age_days` 字段到报告 |
| 5 | 缺少单元测试 | 新增 `tests/test_cleanup_assets_dry_run.py`，31 个测试 |

## 11. 阶段结论

**P8-BE3C 已完成。** 当前阶段新增资产清理 dry-run 工具，只生成候选清理计划，不删除文件、不移动文件、不修改数据库；工具会排除 DB 引用文件、quarantine、running-like 保护窗口内文件，并对 orphan subtitle 执行 json/srt 成对候选。下一阶段应先人工审查 dry-run 结果，再决定是否进入 P8-BE3D quarantine 隔离执行。
