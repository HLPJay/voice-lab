"""
Letter repository — protocol and implementations.

Provides LetterRepository protocol with two implementations:
- MemoryLetterRepository: in-process list (existing behavior)
- SQLiteLetterRepository: persistent SQLite storage

Protocol methods:
  async create(data: dict) -> dict       # returns {letterId, createdAt}
  async list(limit, offset) -> dict      # returns {letters, total, limit, offset}
  def clear() -> None
"""
from __future__ import annotations

import os
import random
import string
import time
from pathlib import Path
from typing import Protocol, runtime_checkable

import sqlite3

from src.xiangta.storage.database import (
    connect,
    ensure_dir_for,
    init_schema,
    resolve_sqlite_path,
)


# ── Protocol ────────────────────────────────────────────────────────────────

@runtime_checkable
class LetterRepository(Protocol):
    """Protocol for letter storage backends."""

    async def create(self, data: dict) -> dict:
        """Save a letter, return {letterId, createdAt}."""
        ...

    async def list(self, limit: int = 50, offset: int = 0) -> dict:
        """Return letters page, newest first."""
        ...

    def clear(self) -> None:
        """Clear all letters."""
        ...


# ── Memory implementation ──────────────────────────────────────────────────

class MemoryLetterRepository:
    """In-process list storage owned by this repository instance."""

    def __init__(self) -> None:
        self._letters: list[dict] = []

    async def create(self, data: dict) -> dict:
        letter_id = "L_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        record = {
            "letterId":    letter_id,
            "recipient":   data.get("recipient", ""),
            "scene":       data.get("scene", ""),
            "style":       data.get("style", ""),
            "rawText":     data.get("rawText", ""),
            "finalText":   data.get("finalText", ""),
            "voicePreset": data.get("voicePreset", ""),
            "tone":        data.get("tone", ""),
            "audioUrl":    data.get("audioUrl"),
            "durationSecs": data.get("durationSecs"),
            "title":       data.get("title"),
            "createdAt":   created_at,
            "favorited":   False,
            "openCount":   0,
            "openedAt":    None,
        }
        self._letters.append(record)
        return {"letterId": letter_id, "createdAt": created_at}

    async def list(self, limit: int = 50, offset: int = 0) -> dict:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        all_sorted = list(reversed(self._letters))
        total = len(all_sorted)
        page = all_sorted[offset: offset + limit]
        return {
            "letters": page,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def clear(self) -> None:
        self._letters.clear()


# ── SQLite implementation ──────────────────────────────────────────────────

class SQLiteLetterRepository:
    """Persistent SQLite storage for letters."""

    def __init__(self, database_url: str | None = None) -> None:
        self._target: str | Path = resolve_sqlite_path(database_url)
        if isinstance(self._target, Path):
            ensure_dir_for(self._target)
        self._conn: sqlite3.Connection | None = None

    def _ensure_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = connect(self._target)
            init_schema(self._conn)
        return self._conn

    def _to_db_record(self, data: dict) -> dict:
        """Convert camelCase API data to snake_case DB record."""
        return {
            "letter_id":    "L_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10)),
            "recipient":    data.get("recipient", ""),
            "scene":        data.get("scene", ""),
            "style":        data.get("style", ""),
            "raw_text":     data.get("rawText", ""),
            "final_text":   data.get("finalText", ""),
            "voice_preset": data.get("voicePreset", ""),
            "tone":         data.get("tone", ""),
            "audio_url":    data.get("audioUrl"),
            "duration_secs": data.get("durationSecs"),
            "title":        data.get("title"),
            "created_at":   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "favorited":    0,
            "open_count":   0,
            "opened_at":    None,
        }

    def _to_api_record(self, row: sqlite3.Row) -> dict:
        """Convert snake_case DB row to camelCase API record."""
        return {
            "letterId":     row["letter_id"],
            "recipient":    row["recipient"],
            "scene":       row["scene"],
            "style":       row["style"],
            "rawText":     row["raw_text"],
            "finalText":   row["final_text"],
            "voicePreset": row["voice_preset"],
            "tone":        row["tone"],
            "audioUrl":    row["audio_url"],
            "durationSecs": row["duration_secs"],
            "title":       row["title"],
            "createdAt":   row["created_at"],
            "favorited":   bool(row["favorited"]),
            "openCount":   row["open_count"],
            "openedAt":    row["opened_at"],
        }

    async def create(self, data: dict) -> dict:
        record = self._to_db_record(data)
        conn = self._ensure_connection()
        conn.execute(
            """
            INSERT INTO letters (
                letter_id, recipient, scene, style, raw_text, final_text,
                voice_preset, tone, audio_url, duration_secs, title,
                created_at, favorited, open_count, opened_at
            ) VALUES (
                :letter_id, :recipient, :scene, :style, :raw_text, :final_text,
                :voice_preset, :tone, :audio_url, :duration_secs, :title,
                :created_at, :favorited, :open_count, :opened_at
            )
            """,
            record,
        )
        conn.commit()
        return {"letterId": record["letter_id"], "createdAt": record["created_at"]}

    async def list(self, limit: int = 50, offset: int = 0) -> dict:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        conn = self._ensure_connection()

        # Total count
        total_row = conn.execute("SELECT COUNT(*) as cnt FROM letters").fetchone()
        total = total_row["cnt"] if total_row else 0

        # Page with ORDER BY created_at DESC, then by rowid DESC for same-second stability
        rows = conn.execute(
            """
            SELECT * FROM letters
            ORDER BY created_at DESC, rowid DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

        return {
            "letters": [self._to_api_record(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def clear(self) -> None:
        conn = self._ensure_connection()
        conn.execute("DELETE FROM letters")
        conn.commit()
