# P8-BE3B 资产清理策略确认

## 1. 背景

P8-BE3A / A1 / A2 已完成资产审查。当前 DB 资产记录健康，主要问题是 orphan storage files。orphan 不等于可删除。本阶段只确认策略，不删除数据。

## 2. BE3A2 最新结论

基于 P8-BE3A2 审查结果（报告版本 p8-be3a2）：

| 维度 | 数值 |
|---|---|
| AudioAsset | 436 |
| SubtitleAsset | 169 |
| VoiceJob | 532 |
| content files (audio+subtitles) | 34,119 |
| all scanned files | 34,119 |
| orphan audio files | 19,701 |
| orphan subtitle files | 14,418 |
| orphan subtitle pairs (json+srt) | 7,209 |
| running-like jobs (standard) | 102（running: 100, processing: 2） |
| temp files | 0 |
| metadata files | 0 |
| missing file DB records | 0 |
| deleted job assets | 0 |

关键判断：
- 数据库资产记录健康，missing DB records = 0
- 当前没有 deleted job assets
- 当前没有 temp / metadata 文件
- 当前最大风险是大量 orphan storage files（~34,119 个）
- 当前有 102 个 running-like jobs，清理策略必须极度保守
- orphan 文件可能有回填价值，不能直接视为可删除

## 3. 资产分类

### 3.1 DB 引用音频文件

定义：`AudioAsset.file_path` 指向的文件。

数量：436（全部 file_path 存在，无缺失）

策略：**永久保留，第一版清理工具禁止处理**。

原因：前端历史播放 / 下载依赖这些文件。missing file DB records = 0 说明 DB 引用资产健康。

### 3.2 DB 引用字幕文件

定义：`SubtitleAsset.file_path` / `SubtitleAsset.srt_path` 指向的文件。

数量：169

策略：**永久保留，第一版清理工具禁止处理**。

原因：字幕时间轴和下载能力依赖这些文件。

### 3.3 orphan audio files

定义：`storage/audio` 下未被 `AudioAsset.file_path` 引用的文件。

当前数量：19,701

策略：
- **不直接删除**。
- 先进入 dry-run 候选。
- 未来真实执行只能先 quarantine，不能直接物理删除。
- 可能有回填价值（早期版本生成但未入库的有效资产）。

### 3.4 orphan subtitle files

定义：`storage/subtitles` 下未被 `SubtitleAsset.file_path` / `SubtitleAsset.srt_path` 引用的文件。

当前数量：14,418（全部以 json+srt 配对形式存在，共 7,209 对）

pair 分析：
- 配对完整（json + srt）：7,209 对
- json 无 srt：0
- srt 无 json：0

策略：
- **不直接删除**。
- **必须 json/srt 成对处理**，不能单独删除 json 或 srt。
- 先进入 dry-run 候选。
- 未来真实执行只能先 quarantine。

### 3.5 temp files

当前数量：0

策略：
- 如果未来存在 temp files，可以作为第一优先级 dry-run 候选。
- temp 生命周期最短，默认保留 1 天。
- 第一版清理工具执行时必须先确认 temp 状态。

### 3.6 metadata files

当前数量：0

策略：
- 暂不清理。
- 如果未来存在，必须先确认是否可辅助 orphan 回填（P8-BE4）。

### 3.7 deleted job assets

当前数量：0

策略：
- 当前不作为清理主线。
- 如果未来存在 deleted job assets，需要单独策略处理。

## 4. 保护规则

### 4.1 永远禁止第一版自动清理的内容

1. `AudioAsset.file_path` 指向的文件
2. `SubtitleAsset.file_path` 指向的文件
3. `SubtitleAsset.srt_path` 指向的文件
4. VoiceJob 数据库记录
5. AudioAsset 数据库记录
6. SubtitleAsset 数据库记录
7. DB 引用文件
8. quarantine 目录内文件
9. 运行中任务可能正在生成的文件

### 4.2 数据库不清理原则

第一版清理策略明确：
- 不删除 VoiceJob
- 不删除 AudioAsset
- 不删除 SubtitleAsset
- 不删除 DB 引用文件
- 不修改 job status
- 不做数据库级 cleanup

原因：当前 missing file DB records = 0，deleted job assets = 0，DB 资产记录健康。

### 4.3 running-like job 保护

标准 running-like 状态（必须保护）：
```
queued / pending / running / processing
```

扩展状态（注意区分）：
```
protected
```

当前 running-like jobs：102（running: 100, processing: 2）

保护要求：
1. 清理工具执行前必须重新查询 job 状态。
2. 只要存在 running-like jobs，默认保护最近 72 小时内文件。
3. 运行中任务关联资产禁止清理。
4. 第一版 dry-run 报告必须显示 running-like job 统计。

### 4.4 最近文件保护窗口

| 类型 | 默认保护窗口 | running-like 存在时 |
|---|---|---|
| orphan audio | 7 天 | 72 小时以上 |
| orphan subtitle | 7 天 | 72 小时以上 |
| temp | 1 天 | 72 小时以上 |

注意：保护窗口不代表可以删除窗口外文件。窗口外文件也必须先 dry-run，再 quarantine。

## 5. 默认保留策略

| 类型 | 当前数量 | 策略 | 默认保护 |
|---|---|---|---|
| DB 引用音频 | 436 | 永久保留 | 不清理 |
| DB 引用字幕 | 169 | 永久保留 | 不清理 |
| orphan audio | 19,701 | 只 dry-run | 7 天，running-like 时 72 小时以上 |
| orphan subtitle | 14,418 | 只 dry-run，成对处理 | 7 天，running-like 时 72 小时以上 |
| temp | 0 | 可优先 dry-run | 1 天 |
| metadata | 0 | 暂不清理 | 待确认 |
| deleted job assets | 0 | 暂不处理 | 待确认 |

## 6. 清理流程分阶段

```
P8-BE3C：dry-run 清理工具（只输出候选清单，不移动/删除）
P8-BE3D：quarantine 隔离执行（移动到 quarantine/，保留 manifest）
P8-BE3E：永久删除 quarantine（purge，30 天隔离期后执行）
```

重要：每个阶段必须明确边界，不得在上一阶段实现下一阶段的能力。

## 7. BE3C dry-run 工具设计

BE3C **只实现 dry-run，不实现 execute，不实现 quarantine**。

### 7.1 参数设计

```bash
python scripts/cleanup_assets.py --dry-run
python scripts/cleanup_assets.py --dry-run --kind temp --min-age-days 1
python scripts/cleanup_assets.py --dry-run --kind orphan-audio --min-age-days 7
python scripts/cleanup_assets.py --dry-run --kind orphan-subtitle --min-age-days 7
python scripts/cleanup_assets.py --dry-run --kind orphan --min-age-days 7
python scripts/cleanup_assets.py --dry-run --kind orphan --min-age-days 7 --max-files 1000
python scripts/cleanup_assets.py --dry-run --kind orphan --min-age-days 7 --output docs/generated/asset_cleanup_dry_run.json
```

### 7.2 参数含义

| 参数 | 含义 |
|---|---|
| `--dry-run` | 只输出计划，不移动，不删除 |
| `--kind` | temp / orphan-audio / orphan-subtitle / orphan |
| `--min-age-days` | 最小文件年龄 |
| `--max-files` | 最大候选数量（首次建议限制 100 或 1000） |
| `--output` | 输出 dry-run JSON 计划文件 |

### 7.3 dry-run 输出结构

```json
{
  "report_version": "p8-be3c-dry-run",
  "mode": "dry-run",
  "kind": "orphan",
  "min_age_days": 7,
  "protection": {
    "running_like_jobs": 102,
    "protection_window_hours": 72,
    "db_referenced_files_excluded": true,
    "quarantine_excluded": true
  },
  "summary": {
    "candidate_file_count": 0,
    "candidate_total_bytes": 0,
    "excluded_recent_count": 0,
    "excluded_db_referenced_count": 0,
    "excluded_running_guard_count": 0
  },
  "candidates": []
}
```

### 7.4 禁止能力

BE3C 禁止实现：
- 物理删除文件
- 移动文件到 quarantine
- 修改数据库
- 生成 manifest

## 8. BE3D quarantine 设计

BE3D **只实现 quarantine 移动，不实现永久删除**。

### 8.1 quarantine 目录结构

```
storage/quarantine/<timestamp>/
├── manifest.json
├── audio/
├── subtitles/
└── temp/
```

示例：`storage/quarantine/2026-05-14T120000/`

### 8.2 manifest 字段

```json
{
  "manifest_version": "p8-be3d-quarantine",
  "created_at": "...",
  "mode": "quarantine",
  "kind": "orphan",
  "files": [
    {
      "original_path": "audio/...",
      "quarantine_path": "quarantine/2026-05-14T120000/audio/...",
      "size_bytes": 12345,
      "reason": "orphan_audio",
      "mtime": "...",
      "sha256": null
    }
  ]
}
```

### 8.3 restore 设计

```bash
python scripts/cleanup_assets.py --restore --manifest storage/quarantine/<timestamp>/manifest.json --confirm RESTORE
```

要求：
- quarantine 必须可恢复。
- 否则不允许进入真实执行阶段。

## 9. 风险控制

1. **dry-run 是默认模式**，不传 `--execute` 就不能执行真实操作。
2. **execute 必须显式传入**，并带 confirm token。
3. **第一版 execute 只能 quarantine**，不能物理删除。
4. **永久删除另设阶段**（P8-BE3E）。
5. 清理前必须重新扫描数据库和 storage。
6. 清理前必须重新检查 running-like jobs。
7. 清理工具必须拒绝 DB 引用文件。
8. 清理工具必须默认排除 quarantine。
9. **orphan subtitle 必须 json/srt 成对处理**，不能只删其中一个。
10. 生成 dry-run report 后需要人工确认。
11. 首次执行建议 `max-files` 限制，例如 100 或 1000。
12. generated report 默认不提交 git。
13. 所有 execute 操作必须生成审计日志（manifest）。
14. 清理后必须能对照 manifest 恢复。

## 10. 当前阶段不做事项

- 不删除文件
- 不移动文件
- 不修改数据库
- 不写 cleanup_assets.py
- 不做真实清理
- 不做自动清理
- 不做永久删除
- 不在 BE3C 中实现 quarantine execute
- 不在 BE3D 中实现 purge

## 11. 下一阶段建议

**P8-BE3C：资产清理 dry-run 工具**

明确：
- **只实现 dry-run，不实现 execute**。
- **不实现 quarantine execute**。
- 输出标准 dry-run JSON 计划。
- 首次只支持 `--kind orphan --min-age-days 7`。
- 支持 `--max-files` 限制。

## 12. 阶段结论

**P8-BE3B 已完成。** 当前阶段基于 BE3A2 审查结果确认资产清理策略：第一版不删除数据库记录，不删除 DB 正在引用的资产文件，不直接永久删除 orphan 文件；orphan audio/subtitle 只能先进入 dry-run，subtitle 必须 json/srt 成对处理；真实执行必须先 quarantine，永久删除另设阶段。下一阶段建议进入 P8-BE3C：资产清理 dry-run 工具。
