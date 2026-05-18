"""
Minimal SQLite database utilities for XiangTa storage.

Handles:
- SQLite path resolution (sqlite:///, :memory:, plain path)
- Connection factory
- Schema initialization with version tracking
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

# Schema version for future migration compatibility
SCHEMA_VERSION = 1

# Default SQLite file path when STORAGE_TYPE=sqlite but no DATABASE_URL is set
DEFAULT_SQLITE_PATH = ".data/xiangta.sqlite3"

# Minimal schema: letters + storage_meta
_LETTERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS letters (
    letter_id TEXT PRIMARY KEY,
    recipient TEXT NOT NULL,
    scene TEXT NOT NULL,
    style TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    final_text TEXT NOT NULL,
    voice_preset TEXT NOT NULL,
    tone TEXT NOT NULL,
    audio_url TEXT,
    duration_secs REAL,
    title TEXT,
    created_at TEXT NOT NULL,
    favorited INTEGER NOT NULL DEFAULT 0,
    open_count INTEGER NOT NULL DEFAULT 0,
    opened_at TEXT
);
"""

_STORAGE_META_SCHEMA = """
CREATE TABLE IF NOT EXISTS storage_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def resolve_sqlite_path(database_url: str | None) -> str | Path:
    """
    Resolve XIANGTA_STORAGE_DATABASE_URL to a database target.

    Supports:
      None or ""           → DEFAULT_SQLITE_PATH (persistent file)
      :memory:             → ":memory:" (SQLite in-memory)
      sqlite:///path.db    → strip prefix, use as path
      /absolute/path.db    → use as absolute path
      relative/path.db     → use relative to cwd

    Raises ValueError for unsupported formats.
    """
    if database_url is None or database_url.strip() == "":
        return DEFAULT_SQLITE_PATH

    url = database_url.strip()

    if url == ":memory:":
        return ":memory:"

    if url.startswith("sqlite:///"):
        path_str = url[len("sqlite:///"):]
        return Path(path_str)

    if url.startswith("sqlite://"):
        raise ValueError(f"Unsupported sqlite URL format: {url!r}")

    # Plain path (absolute or relative)
    return Path(url)


def ensure_dir_for(path: Path) -> None:
    """Create parent directories if they don't exist."""
    parent = path.parent
    if parent != Path("."):
        parent.mkdir(parents=True, exist_ok=True)


def connect(target: str | Path) -> sqlite3.Connection:
    """
    Open a SQLite connection.

    Args:
        target: File path or ":memory:" for in-memory SQLite.

    Returns:
        sqlite3.Connection with row_factory = sqlite3.Row
    """
    if target == ":memory:":
        conn = sqlite3.connect(":memory:")
    else:
        conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """
    Initialize storage schema if not already present.

    Creates letters table and storage_meta table.
    Records current schema version.
    Safe to call repeatedly (CREATE TABLE IF NOT EXISTS).
    """
    cur = conn.cursor()
    cur.execute(_LETTERS_SCHEMA)
    cur.execute(_STORAGE_META_SCHEMA)
    conn.commit()

    # Record schema version
    cur.execute(
        "INSERT OR IGNORE INTO storage_meta (key, value) VALUES (?, ?)",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()


def get_schema_version(conn: sqlite3.Connection) -> int | None:
    """Return the recorded schema version, or None if not set."""
    cur = conn.cursor()
    cur.execute(
        "SELECT value FROM storage_meta WHERE key = ?",
        ("schema_version",),
    )
    row = cur.fetchone()
    return int(row["value"]) if row else None
