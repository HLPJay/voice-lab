# P18-XIANGTA-STORAGE-FOUNDATION-C6-FIX4

## 修复内容

- `DEFAULT_SQLITE_PATH` 从字符串 `".data/xiangta.sqlite3"` 改为 `Path(".data/xiangta.sqlite3")`
- `resolve_sqlite_path(None/""`) 返回 `Path`，`isinstance(..., Path)` 为 `True`
- `resolve_sqlite_path(":memory:")` 返回 `":memory:"`（字符串）
- `database_url=None` 时 `ensure_dir_for(Path)` 会创建 `.data/` 目录
- 补充 `isinstance` 类型断言到 `test_resolve_sqlite_path`

## 未修改

- 未修改 API / runtime_config / product_service / H5 / Core
- 未实现 C7

## 下一步

P18-XIANGTA-TTS-TASK-MVP-C7
