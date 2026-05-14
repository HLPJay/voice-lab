# P8-BE3D 资产 quarantine 和 restore 工具

## 1. 背景

P8-BE3C 已完成 dry-run 工具。BE3D 在此基础上增加 `--quarantine` 和 `--restore` 两个模式。核心原则：
- quarantine 使用 `shutil.move` 移动文件，源文件被移走，不复制，不删除
- 生成 manifest.json，支持 restore
- 禁止永久删除、禁止修改数据库

## 2. 工具说明

- 脚本：`scripts/cleanup_assets.py`
- 支持三种互斥模式：`--dry-run`（BE3C）、`--quarantine`、`--restore`
- 默认输出：`docs/generated/asset_cleanup_dry_run.json`

## 3. 参数说明

### 3.1 通用参数

| 参数 | 含义 | 默认值 |
|---|---|---|
| `--storage-dir` | 存储根目录 | app config |

### 3.2 dry-run 参数

| 参数 | 含义 | 默认值 |
|---|---|---|
| `--dry-run` | 必填，只生成计划 | — |
| `--kind` | temp / orphan-audio / orphan-subtitle / orphan | orphan |
| `--min-age-days` | 最小文件年龄 | 7 |
| `--max-files` | 最大候选文件数量 | 1000 |
| `--output` | 输出 JSON 路径 | docs/generated/asset_cleanup_dry_run.json |

### 3.3 quarantine 参数

| 参数 | 含义 | 必需 |
|---|---|---|
| `--quarantine` | 执行隔离移动 | 是 |
| `--plan` | dry-run JSON 计划路径 | 是 |
| `--confirm QUARANTINE` | 确认令牌 | 是 |

### 3.4 restore 参数

| 参数 | 含义 | 必需 |
|---|---|---|
| `--restore` | 执行恢复 | 是 |
| `--manifest` | manifest.json 路径 | 是 |
| `--confirm RESTORE` | 确认令牌 | 是 |

## 4. 模式互斥

`--dry-run`、`--quarantine`、`--restore` 三者互斥，不能同时指定。

## 5. quarantine 执行流程

### 5.1 计划验证

1. 验证 `report_version == "p8-be3c-dry-run"`
2. 验证 `mode == "dry-run"`
3. 验证 `candidates` 字段存在

### 5.2 DB 重新校验

在 quarantine 执行前，重新查询 DB 中的 `AudioAsset`、`SubtitleAsset` 记录：
- 如果文件在执行前已被 DB 引用，跳过（status=skipped, skip_reason=db_referenced）
- 防止 plan 生成后到执行前这段时间内文件被回填的情况

### 5.3 文件隔离

- 使用 `shutil.move` 移动文件到 `storage/quarantine/<timestamp>/`
- **源文件被移走**，不复制，不删除
- manifest 中记录为 status=moved，供未来 BE3E purge 阶段处理

### 5.4 路径安全

- 拒绝绝对路径（status=failed, skip_reason=absolute_path_not_allowed）
- 拒绝 `..` 路径遍历（status=failed, skip_reason=path_traversal_not_allowed）

### 5.5 字幕成对完整性

- 候选中的 json/srt 必须同时存在，否则 pair 整体跳过
- 缺少任一方则 pair 不进入隔离

### 5.6 quarantine 目录结构

```
storage/quarantine/<timestamp>/
├── manifest.json
├── audio/
└── subtitles/
```

## 6. manifest 结构

```json
{
  "manifest_version": "p8-be3d-quarantine",
  "created_at": "...",
  "mode": "quarantine",
  "source_plan": "<path>",
  "storage_root": "<REDACTED>",
  "quarantine_timestamp": "20260101T000000",
  "summary": {
    "requested_file_count": 0,
    "moved_file_count": 0,
    "skipped_file_count": 0,
    "failed_file_count": 0,
    "moved_total_bytes": 0
  },
  "files": [
    {
      "candidate_id": "cand_000001",
      "kind": "orphan-audio",
      "reason": "orphan_audio",
      "original_relative_path": "audio/...",
      "quarantine_relative_path": "quarantine/<timestamp>/audio/...",
      "size_bytes": 12345,
      "modified_time": "...",
      "status": "moved",
      "skip_reason": null,
      "error": null
    }
  ],
  "notices": [
    "Quarantine only. No files were permanently deleted.",
    "No database records were modified.",
    "Restore is available via --restore --manifest storage/quarantine/<timestamp>/manifest.json --confirm RESTORE."
  ]
}
```

## 7. restore 执行流程

### 7.1 manifest 验证

1. 验证 `manifest_version == "p8-be3d-quarantine"`
2. 验证 `mode == "quarantine"`

### 7.2 恢复规则

- **只恢复 status=moved 的文件**（其他状态跳过）
- **不覆盖**：如果原始路径已存在，跳过（conflict）
- 使用 `shutil.move` 移回原始位置

### 7.3 恢复结果字段

| status | 含义 |
|---|---|
| restored | 成功恢复 |
| conflict | 原始路径已存在，跳过 |
| skipped_not_moved | 非 moved 状态，跳过 |
| failed | 恢复失败 |

## 8. 安全边界

- 未实现 purge（永久删除）
- 未实现 purge-quarantine
- 未修改数据库
- 未复制源文件（quarantine 使用 move，移走源文件）
- `--purge` / `--purge-quarantine` 在任何情况下都被拒绝

## 9. 测试覆盖

`tests/test_cleanup_assets_quarantine.py`：24 个测试

| 测试类 | 覆盖内容 |
|---|---|
| TestForbiddenArguments | --purge / --purge-quarantine 拒绝 |
| TestModeMutualExclusivity | 三种模式互斥 |
| TestQuarantineRequires | --quarantine 必需参数验证 |
| TestRestoreRequires | --restore 必需参数验证 |
| TestDryRunRequires | --dry-run 独立运行 |
| TestPlanValidation | plan 版本和模式校验 |
| TestRestoreManifestValidation | manifest 版本和模式校验 |
| TestQuarantineManifestStructure | manifest 结构正确性 |
| TestRestoreBehavior | restore 跳过非 moved 状态和冲突文件 |
| TestNoDestructiveInQuarantine | quarantine 移走源文件（move 语义） |

## 10. 阶段结论

**P8-BE3D 已完成。** 当前阶段在 BE3C dry-run 工具基础上增加 `--quarantine` 和 `--restore` 两个模式：quarantine 通过 `shutil.move` 将候选文件隔离到 `storage/quarantine/<timestamp>/`，生成 manifest.json 支持未来 restore；restore 验证 manifest 后将 status=moved 的文件移回原始位置，不覆盖已有文件。下一阶段建议进入 P8-BE3E：quarantine 永久删除（purge），需在 30 天隔离期后执行。
