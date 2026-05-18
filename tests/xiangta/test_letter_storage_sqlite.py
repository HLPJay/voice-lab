"""
Tests for SQLite letters storage foundation.

Covers:
1. SQLiteLetterRepository initializes and creates letters table
2. create then list persists across SQLite repo instances (same file)
3. Two LetterService instances with SQLite repo share data (cross-instance persistence)
4. list() returns newest first with SQLite
5. limit/offset behavior is consistent
6. clear() empties SQLite letters
7. create_product_service with XIANGTA_STORAGE_TYPE=sqlite uses SQLiteLetterRepository
8. create_product_service defaults to memory storage (no env)
"""
import pytest

from src.xiangta.services.letter_service import LetterService
from src.xiangta.storage import (
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


class TestSqliteLetterRepository:
    def test_repo_initializes_and_creates_letters_table(self, tmp_path):
        """SQLiteLetterRepository init creates letters table and storage_meta."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))
        # Trigger schema init by calling create
        import asyncio
        asyncio.get_event_loop().run_until_complete(repo.create(_SAMPLE))

        conn = connect(tmp_path / "test.db")
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='letters'")
        assert cur.fetchone() is not None, "letters table not created"

    def test_create_and_list_persists_across_instances(self, tmp_path):
        """Creating a letter in one repo instance is readable from another instance pointing to same file."""
        repo_a = SQLiteLetterRepository(database_url=str(tmp_path / "shared.db"))
        repo_b = SQLiteLetterRepository(database_url=str(tmp_path / "shared.db"))

        import asyncio
        asyncio.get_event_loop().run_until_complete(repo_a.create(_SAMPLE))

        result = asyncio.get_event_loop().run_until_complete(repo_b.list())
        assert result["total"] == 1
        assert result["letters"][0]["recipient"] == "lover"

    def test_two_letter_service_instances_share_sqlite_data(self, tmp_path):
        """Two LetterService instances with SQLite repos share data across instances."""
        db_url = str(tmp_path / "shared.db")
        svc_a = LetterService(repository=SQLiteLetterRepository(database_url=db_url))
        svc_b = LetterService(repository=SQLiteLetterRepository(database_url=db_url))

        import asyncio
        asyncio.get_event_loop().run_until_complete(svc_a.create(_SAMPLE))

        result = asyncio.get_event_loop().run_until_complete(svc_b.list())
        assert result["total"] == 1

    def test_list_returns_newest_first(self, tmp_path):
        """list() returns newest letter first (ORDER BY created_at DESC)."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))

        import asyncio
        loop = asyncio.get_event_loop()
        r1 = loop.run_until_complete(repo.create({**_SAMPLE, "title": "第一封"}))
        r2 = loop.run_until_complete(repo.create({**_SAMPLE, "title": "第二封"}))

        result = loop.run_until_complete(repo.list())
        assert result["letters"][0]["letterId"] == r2["letterId"]
        assert result["letters"][1]["letterId"] == r1["letterId"]

    def test_limit_and_offset_consistent_with_memory(self, tmp_path):
        """limit/offset behavior matches the memory implementation."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))

        import asyncio
        loop = asyncio.get_event_loop()
        for i in range(5):
            loop.run_until_complete(repo.create({**_SAMPLE, "title": f"第{i}封"}))

        result = loop.run_until_complete(repo.list(limit=3, offset=2))
        assert len(result["letters"]) == 3
        assert result["total"] == 5
        assert result["limit"] == 3
        assert result["offset"] == 2

    def test_clear_empties_sqlite_letters(self, tmp_path):
        """clear() removes all letters from SQLite storage."""
        repo = SQLiteLetterRepository(database_url=str(tmp_path / "test.db"))

        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repo.create(_SAMPLE))
        loop.run_until_complete(repo.create(_SAMPLE))

        repo.clear()
        result = loop.run_until_complete(repo.list())
        assert result["total"] == 0


class TestStorageIntegration:
    def test_create_product_service_uses_sqlite_when_env_set(self, monkeypatch, tmp_path):
        """create_product_service uses SQLiteLetterRepository when XIANGTA_STORAGE_TYPE=sqlite."""
        monkeypatch.setenv("XIANGTA_STORAGE_TYPE", "sqlite")
        monkeypatch.setenv("XIANGTA_STORAGE_DATABASE_URL", str(tmp_path / "xiangta.db"))

        # Import inside to pick up patched env
        from src.xiangta.services.product_service import create_product_service
        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(svc.create_letter(_SAMPLE))
        assert "letterId" in result

        # Second service instance with same db file should see it
        svc2 = ps_module.create_product_service()
        result2 = loop.run_until_complete(svc2.list_letters())
        assert result2["total"] == 1

    def test_create_product_service_defaults_to_memory_without_env(self, monkeypatch):
        """create_product_service uses in-memory storage when no XIANGTA_STORAGE_TYPE is set."""
        monkeypatch.delenv("XIANGTA_STORAGE_TYPE", raising=False)
        monkeypatch.delenv("XIANGTA_STORAGE_DATABASE_URL", raising=False)

        from src.xiangta.services.product_service import create_product_service
        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(svc.create_letter(_SAMPLE))
        assert "letterId" in result

        # List should show the created letter
        result2 = loop.run_until_complete(svc.list_letters())
        assert result2["total"] == 1
        assert result2["letters"][0]["recipient"] == "lover"
