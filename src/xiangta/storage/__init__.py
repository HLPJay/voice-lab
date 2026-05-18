"""
XiangTa storage module.

Exports:
- LetterRepository (protocol)
- MemoryLetterRepository
- SQLiteLetterRepository
- resolve_sqlite_path
- connect, init_schema (database utilities)
"""
from src.xiangta.storage.database import (
    SCHEMA_VERSION,
    connect,
    ensure_dir_for,
    get_schema_version,
    init_schema,
    resolve_sqlite_path,
)
from src.xiangta.storage.letter_repository import (
    LetterRepository,
    MemoryLetterRepository,
    SQLiteLetterRepository,
)

__all__ = [
    "LetterRepository",
    "MemoryLetterRepository",
    "SQLiteLetterRepository",
    "resolve_sqlite_path",
    "connect",
    "init_schema",
    "ensure_dir_for",
    "get_schema_version",
    "SCHEMA_VERSION",
]
