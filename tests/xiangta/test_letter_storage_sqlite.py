"""
Tests for SQLite letters storage foundation.

Covers:
1. SQLiteLetterRepository initializes and creates letters + storage_meta tables
2. create then list persists across SQLite repo instances (same file)
3. Two LetterService instances with SQLite repo share data (cross-instance persistence)
4. list() returns newest first with SQLite, same-second creates ordered by rowid
5. limit/offset behavior is consistent
6. clear() empties SQLite letters
7. create_product_service with XIANGTA_STORAGE_TYPE=sqlite uses SQLiteLetterRepository
8. create_product_service defaults to memory storage (no env)
9. SQLiteLetterRepository with None url uses default persistent path, :memory: uses memory
"""
import asyncio
import pytest

from src.xiangta.services.letter_service import LetterService
from src.xiangta.storage import (
    DEFAULT_SQLITE_PATH,
    SQLiteLetterRepository,
    connect,
    get_schema_version,
    init_schema,
    resolve_sqlite_path,
)
from src.xiangta.storage.database import SCHEMA_VERSION


_SAMPLE = {
    "recipient": "lover",
    "scene": "miss",
    "style": "gentle",
    "rawText": "我今天突然很想你",
    "finalText": "有些挂念你，我今天突然很想你，悄悄想了一会儿。",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "audioUrl": "/api/voice/assets/audio_123/download",
    "durationSecs": 2.4,
    "title": "想你了",
}


def _loop():
    return asyncio.get_event_loop()


class TestSqliteLetterRepository:
    def test_repo_creates_letters_and_storage_meta_tables(self, tmp_path):
        """SQLiteLetterRepository init creates both letters and storage_meta tables."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))
        _loop().run_until_complete(repo.create(_SAMPLE))

        conn = connect(str(tmp_path / "test.db"))
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('letters', 'storage_meta')"
        )
        tables = {row["name"] for row in cur.fetchall()}
        assert "letters" in tables, "letters table not created"
        assert "storage_meta" in tables, "storage_meta table not created"

    def test_schema_version_is_recorded(self, tmp_path):
        """storage_meta records the current schema version after init."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))
        _loop().run_until_complete(repo.create(_SAMPLE))

        conn = connect(str(tmp_path / "test.db"))
        version = get_schema_version(conn)
        assert version == SCHEMA_VERSION

    def test_init_schema_is_idempotent(self, tmp_path):
        """init_schema can be called multiple times without error."""
        conn = connect(str(tmp_path / "test.db"))
        init_schema(conn)
        init_schema(conn)  # should not raise
        assert get_schema_version(conn) == SCHEMA_VERSION

    def test_create_and_list_persists_across_instances(self, tmp_path):
        """Creating a letter in one repo instance is readable from another instance pointing to same file."""
        repo_a = SQLiteLetterRepository(database_url=str(tmp_path / "shared.db"))
        repo_b = SQLiteLetterRepository(database_url=str(tmp_path / "shared.db"))

        _loop().run_until_complete(repo_a.create(_SAMPLE))
        result = _loop().run_until_complete(repo_b.list())
        assert result["total"] == 1
        assert result["letters"][0]["recipient"] == "lover"

    def test_two_letter_service_instances_share_sqlite_data(self, tmp_path):
        """Two LetterService instances with SQLite repos share data across instances."""
        db_url = str(tmp_path / "shared.db")
        svc_a = LetterService(repository=SQLiteLetterRepository(database_url=db_url))
        svc_b = LetterService(repository=SQLiteLetterRepository(database_url=db_url))

        _loop().run_until_complete(svc_a.create(_SAMPLE))
        result = _loop().run_until_complete(svc_b.list())
        assert result["total"] == 1

    def test_list_returns_newest_first(self, tmp_path):
        """list() returns newest letter first (ORDER BY created_at DESC, rowid DESC)."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))

        r1 = _loop().run_until_complete(repo.create({**_SAMPLE, "title": "第一封"}))
        r2 = _loop().run_until_complete(repo.create({**_SAMPLE, "title": "第二封"}))

        result = _loop().run_until_complete(repo.list())
        assert result["letters"][0]["letterId"] == r2["letterId"]
        assert result["letters"][1]["letterId"] == r1["letterId"]

    def test_same_second_creates_ordered_by_rowid(self, tmp_path):
        """Two creates in the same second are ordered newest-first by rowid."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))

        # Both created in same second — rowid guarantees insertion order
        r1 = _loop().run_until_complete(repo.create({**_SAMPLE, "title": "早"}))
        r2 = _loop().run_until_complete(repo.create({**_SAMPLE, "title": "晚"}))

        result = _loop().run_until_complete(repo.list())
        # r2 should come first (higher rowid = inserted later)
        assert result["letters"][0]["letterId"] == r2["letterId"]
        assert result["letters"][1]["letterId"] == r1["letterId"]

    def test_limit_and_offset_consistent_with_memory(self, tmp_path):
        """limit/offset behavior matches the memory implementation."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))

        for i in range(5):
            _loop().run_until_complete(repo.create({**_SAMPLE, "title": f"第{i}封"}))

        result = _loop().run_until_complete(repo.list(limit=3, offset=2))
        assert len(result["letters"]) == 3
        assert result["total"] == 5
        assert result["limit"] == 3
        assert result["offset"] == 2

    def test_clear_empties_sqlite_letters(self, tmp_path):
        """clear() removes all letters from SQLite storage."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))

        _loop().run_until_complete(repo.create(_SAMPLE))
        _loop().run_until_complete(repo.create(_SAMPLE))
        repo.clear()
        result = _loop().run_until_complete(repo.list())
        assert result["total"] == 0


class TestStorageIntegration:
    def test_resolve_sqlite_path_none_returns_default_path(self):
        """resolve_sqlite_path(None) returns DEFAULT_SQLITE_PATH (persistent file)."""
        result = resolve_sqlite_path(None)
        assert result == DEFAULT_SQLITE_PATH
        assert result != ":memory:"

    def test_resolve_sqlite_path_empty_returns_default_path(self):
        """resolve_sqlite_path('') returns DEFAULT_SQLITE_PATH (persistent file)."""
        result = resolve_sqlite_path("")
        assert result == DEFAULT_SQLITE_PATH
        assert result != ":memory:"

    def test_resolve_sqlite_path_memory_returns_memory(self):
        """resolve_sqlite_path(':memory:') returns ':memory:'."""
        result = resolve_sqlite_path(":memory:")
        assert result == ":memory:"

    def test_create_product_service_uses_sqlite_when_env_set(self, monkeypatch, tmp_path):
        """create_product_service uses SQLiteLetterRepository when XIANGTA_STORAGE_TYPE=sqlite."""
        monkeypatch.setenv("XIANGTA_STORAGE_TYPE", "sqlite")
        monkeypatch.setenv("XIANGTA_STORAGE_DATABASE_URL", str(tmp_path / "xiangta.db"))

        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        result = _loop().run_until_complete(svc.create_letter(_SAMPLE))
        assert "letterId" in result

        svc2 = ps_module.create_product_service()
        result2 = _loop().run_until_complete(svc2.list_letters())
        assert result2["total"] == 1

    def test_create_product_service_defaults_to_memory_without_env(self, monkeypatch):
        """create_product_service uses in-memory storage when no XIANGTA_STORAGE_TYPE is set."""
        monkeypatch.delenv("XIANGTA_STORAGE_TYPE", raising=False)
        monkeypatch.delenv("XIANGTA_STORAGE_DATABASE_URL", raising=False)

        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        result = _loop().run_until_complete(svc.create_letter(_SAMPLE))
        assert "letterId" in result

        result2 = _loop().run_until_complete(svc.list_letters())
        assert result2["total"] == 1
        assert result2["letters"][0]["recipient"] == "lover"