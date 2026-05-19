# P18-XIANGTA-STORAGE-FOUNDATION-C6-FIX3

## 修复内容（已在上次 FIX1 中实现）

- `DEFAULT_SQLITE_PATH` 为 `Path(".data/xiangta.sqlite3")`（FIX1 引入）
- `SQLiteLetterRepository.__init__` 对 Path 实例调用 `ensure_dir_for`（FIX1 引入）
- 显式 `:memory:` 保持不变，连接层已正确处理

## 验证结果

- `test_letter_storage_sqlite.py`：10 个测试全部通过
- xiangta 全量测试：670 个全部通过

## 未修改

- 未修改 API / storage / runtime_config / H5 / Core

## 下一步

P18-XIANGTA-TTS-TASK-MVP-C7
