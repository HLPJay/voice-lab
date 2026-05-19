# P18-XIANGTA-STORAGE-FOUNDATION-C6

## 实现内容

### 新增 `src/xiangta/storage/` 模块
- `database.py`: SQLite 连接工厂、路径解析（sqlite:///, :memory:, plain path）、schema 初始化、schema version tracking
- `letter_repository.py`: `LetterRepository` 协议 + `MemoryLetterRepository` + `SQLiteLetterRepository` 实现
- `__init__.py`: 模块导出

### LetterService 支持 repository 注入
- `__init__(repository=None)`: 注入可选 storage backend
- `repository is None`: 使用模块级 `_LETTERS` 内存列表（向后兼容）
- `repository is SQLiteLetterRepository`: 持久化 SQLite

### SQLiteLetterRepository
- 最小 schema: `letters` 表 + `storage_meta` 表（记录 schema version）
- camelCase ↔ snake_case 字段映射
- ORDER BY created_at DESC, letter_id DESC
- CREATE TABLE IF NOT EXISTS（可重复初始化）

### create_product_service 根据 runtime config 装配
- `XIANGTA_STORAGE_TYPE=sqlite` → `LetterService(repository=SQLiteLetterRepository(...))`
- 默认 memory storage（`repository=None`）
- 不修改 `runtime_config.py`

## 测试覆盖

`tests/xiangta/test_letter_storage_sqlite.py` (8 tests):
1. SQLiteLetterRepository 初始化创建 letters 表
2. 跨 repo 实例持久化（同一 db 文件）
3. 跨 LetterService 实例 SQLite 共享数据
4. list() 新建在前
5. limit/offset 行为一致
6. clear() 清空 SQLite letters
7. create_product_service XIANGTA_STORAGE_TYPE=sqlite 使用 SQLite
8. create_product_service 默认使用 memory storage

## 未实现项

- 多用户 / user_id
- TTS task 表
- LLM copywriting storage
- migration framework (Alembic)
- 多表复杂关系

## 下一步

P18-XIANGTA-TTS-TASK-MVP-C7