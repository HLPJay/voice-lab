# P8-BE3A1 资产审查报告增强

## 1. 背景

P8-BE3A 的只读资产审查脚本功能有限，无法支撑 BE3B 策略制定。P8-BE3A1 在 BE3A 基础上补强数据基础，不删除任何数据。

## 2. 增强内容

### 2.1 storage_root 脱敏

JSON 报告中 `storage_root` 字段值从实际绝对路径改为 `"<REDACTED>"`，避免敏感路径泄露。

### 2.2 隔离目录排除

`EXCLUDED_STORAGE_DIRS = {"quarantine"}` — 扫描 storage 时跳过 quarantine 子目录（可能含待清理文件）。

### 2.3 temp / metadata 目录统计

新增 `temp_file_count`、`temp_total_bytes`、`metadata_file_count`、`metadata_total_bytes`，了解辅助存储占用。

### 2.4 年龄分布

按文件修改时间分桶统计孤立文件年龄分布：
- 0-1d / 1-7d / 7-30d / 30-90d / 90d+

### 2.5 大小分布

按文件大小分桶统计孤立文件大小分布：
- 0B / <10KB / 10KB-1MB / 1MB-10MB / 10MB+

### 2.6 最大孤立文件清单

每类孤立文件（audio / subtitle）返回磁盘体积最大的前 50 个文件路径及大小、修改时间，供 BE3B 策略参考。

### 2.7 字幕对分析

分析 json/srt 配对情况：
- 配对完整（json + srt 同时存在）的字幕对数量
- 仅有 json 无 srt 的数量
- 仅有 srt 无 json 的数量

### 2.8 运行任务保护

识别当前处于 `running` / `queued` / `processing` / `protected` 状态的 VoiceJob，标记其关联资产为 protected（不可清理）。

### 2.9 回填候选人说明

`backfill_candidates_note` 字段说明孤立文件可能用于回填缺失的数据库记录，删除前需确认不需要保留。

### 2.10 报告版本

`report_version: "p8-be3a1"` 标识报告格式版本。

## 3. 关键新增发现

| 维度 | 数值 |
|---|---|
| storage_root 脱敏 | `<REDACTED>` |
| 排除扫描目录 | `quarantine` |
| 字幕对（json+srt 配对） | 7,179 对 |
| json 无 srt | 0 |
| srt 无 json | 0 |
| 运行中任务数 | 102（running:100, processing:2） |
| protected 音频资产 | 0 |
| protected 字幕资产 | 0 |
| 孤立音频年龄分布 | 0-1d: 7,716 / 1-7d: 11,887 |
| 孤立字幕年龄分布 | 0-1d: 5,062 / 1-7d: 9,296 |
| 孤立音频大小分布 | <10KB: 4,044 / 10KB-1MB: 15,559 |
| 孤立字幕大小分布 | <10KB: 14,358 |
| 最大孤立音频返回数 | 50（总计 19,603） |
| 最大孤立字幕返回数 | 50（总计 14,358） |

## 4. 关键发现

- **字幕全部配对**：所有 14,358 个孤立字幕文件都有对应的 json+srt 配对（7,179 对），说明字幕生成是完整流程
- **大量近期孤立文件**：几乎所有孤立文件年龄在 0-7 天内，暗示可能是测试阶段遗留或 provider 临时文件
- **无运行任务关联资产**：当前 102 个运行中任务均无关联 AudioAsset 或 SubtitleAsset 记录
- **音频大小适中**：孤立音频集中在 10KB-1MB（15,559 个），符合正常音频大小范围
- **无悬空字幕**：所有孤立字幕都有 json+srt 配对，无孤立的单文件

## 5. 验证命令

```bash
python scripts/audit_assets.py --output docs/generated/asset_audit_report.json
```

### 5.1 storage_root 脱敏检查

```bash
python -c "
import json
r = json.load(open('docs/generated/asset_audit_report.json'))
assert r['storage_root'] == '<REDACTED>', r['storage_root']
assert r['report_version'] == 'p8-be3a1'
print('PASS')
"
```

### 5.2 新增字段检查

```bash
python -c "
import json
r = json.load(open('docs/generated/asset_audit_report.json'))
for f in ['age_distribution', 'size_distribution', 'largest_orphan_files', 'subtitle_pair_analysis', 'running_job_guard', 'backfill_candidates_note']:
    assert f in r, f'Missing {f}'
print('PASS')
"
```

## 6. 下一阶段

**P8-BE3B：资产清理策略确认**

在 BE3A1 统计数据基础上：
- 确认孤立文件清理策略（如：仅清理 7d+ 的孤立文件）
- 确认删除操作需人工确认
- 确认 quarantine 目录处理方式
- 制定 dry-run 工具规格

## 7. 阶段结论

**P8-BE3A1 已完成。** 在 P8-BE3A 基础上新增 storage_root 脱敏、quarantine 排除、temp/metadata 统计、年龄分布、大小分布、最大孤立文件清单（各 50 个）、字幕对分析（7,179 对 json+srt）、运行任务保护（102 个 running/processing 任务）和回填候选人说明。pytest 384 passed, 6 skipped。下一阶段为 P8-BE3B 资产清理策略确认。
