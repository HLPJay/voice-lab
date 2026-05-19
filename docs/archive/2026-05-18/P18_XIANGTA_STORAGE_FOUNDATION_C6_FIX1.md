# P18-XIANGTA-STORAGE-FOUNDATION-C6-FIX1

## 修复内容

- sqlite 模式缺省 databaseUrl 使用 `.data/xiangta.sqlite3`（`DEFAULT_SQLITE_PATH`）
- 显式 `:memory:` 仍可用
- SQLite list 同秒创建按 `rowid DESC` 保证最新在前
- `storage_meta` / `get_schema_version` 增加测试覆盖
- 修正 `MemoryLetterRepository` docstring（实例私有，非模块级共享）
- `resolve_sqlite_path` 返回类型改为 `str | Path`，区分 None/"" → 默认路径，`:memory:` → `":memory:"`
- `connect` 接收 `str | Path`，处理 `":memory:"` 字符串

## 未修改

- 未修改 API / runtime_config / H5 / Core

## 下一步

P18-XIANGTA-TTS-TASK-MVP-C7