"""
Tests for SQLite letters storage foundation.

Covers:
1. schema init creates tables, records version, is idempotent
2. resolve_sqlite_path: None/"" → default path, :memory: → memory
3. SQLiteLetterRepository default path creates .data/ dir + cross-instance persistence
4. list newest-first with same-second rowid ordering
5. limit/offset consistent with memory implementation
6. clear() empties storage
7. create_product_service sqlite env cross-instance persistence
8. create_product_service defaults to memory
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


class TestSqliteSchema:
    def test_init_creates_tables_and_records_version_idempotent(self, tmp_path):
        """init_schema creates letters + storage_meta, records schema_version, is idempotent."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))
        _loop().run_until_complete(repo.create(_SAMPLE))

        conn = connect(str(tmp_path / "test.db"))
        tables = {r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert "letters" in tables
        assert "storage_meta" in tables
        assert get_schema_version(conn) == SCHEMA_VERSION

        # idempotent: calling init_schema again should not raise
        init_schema(conn)
        assert get_schema_version(conn) == SCHEMA_VERSION


class TestResolveSqlitePath:
    @pytest.mark.parametrize("url", [None, "", ":memory:"])
    def test_resolve_sqlite_path(self, url):
        """resolve_sqlite_path: None/''→default, :memory:→memory."""
        if url in (None, ""):
            assert resolve_sqlite_path(url) == DEFAULT_SQLITE_PATH
        else:
            assert resolve_sqlite_path(url) == ":memory:"


class TestSqliteRepository:
    def test_default_path_and_cross_instance(self, monkeypatch, tmp_path):
        """database_url=None creates .data/ dir + file; two instances share data."""
        monkeypatch.chdir(tmp_path)
        repo_a = SQLiteLetterRepository(database_url=None)
        _loop().run_until_complete(repo_a.create(_SAMPLE))

        db_path = tmp_path / DEFAULT_SQLITE_PATH
        assert db_path.exists(), f"{db_path} not created"

        repo_b = SQLiteLetterRepository(database_url=None)
        assert _loop().run_until_complete(repo_b.list())["total"] == 1

    def test_newest_first_and_same_second_ordering(self, tmp_path):
        """list() orders newest first; same-second creates ordered by rowid."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))
        r1 = _loop().run_until_complete(repo.create({**_SAMPLE, "title": "早"}))
        r2 = _loop().run_until_complete(repo.create({**_SAMPLE, "title": "晚"}))
        result = _loop().run_until_complete(repo.list())
        assert result["letters"][0]["letterId"] == r2["letterId"]
        assert result["letters"][1]["letterId"] == r1["letterId"]

    def test_limit_offset(self, tmp_path):
        """limit/offset behavior consistent with memory implementation."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))
        for i in range(5):
            _loop().run_until_complete(repo.create({**_SAMPLE, "title": f"第{i}封"}))
        result = _loop().run_until_complete(repo.list(limit=3, offset=2))
        assert len(result["letters"]) == 3
        assert result["total"] == 5

    def test_clear(self, tmp_path):
        """clear() empties all letters from SQLite storage."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))
        _loop().run_until_complete(repo.create(_SAMPLE))
        _loop().run_until_complete(repo.create(_SAMPLE))
        repo.clear()
        assert _loop().run_until_complete(repo.list())["total"] == 0


class TestStorageIntegration:
    def test_create_product_service_sqlite_cross_instance(self, monkeypatch, tmp_path):
        """create_product_service with STORAGE_TYPE=sqlite persists across instances."""
        monkeypatch.setenv("XIANGTA_STORAGE_TYPE", "sqlite")
        monkeypatch.setenv("XIANGTA_STORAGE_DATABASE_URL", str(tmp_path / "xiangta.db"))

        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()
        _loop().run_until_complete(svc.create_letter(_SAMPLE))

        svc2 = ps_module.create_product_service()
        assert _loop().run_until_complete(svc2.list_letters())["total"] == 1

    def test_create_product_service_defaults_to_memory(self, monkeypatch):
        """create_product_service with no STORAGE_TYPE env uses memory."""
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