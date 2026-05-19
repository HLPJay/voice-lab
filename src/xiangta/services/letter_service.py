"""
LetterService — 信笺 CRUD。

B6-1 版本：进程内内存存储 MVP。
B6-2 版本：支持可选 SQLite 持久化（通过 repository 注入）。

不调用 Core / Provider / LLM。
"""
from __future__ import annotations

import random
import string
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.storage.letter_repository import LetterRepository

# 模块级全局 store，所有默认 LetterService 实例共享。
# 保证 POST 后 GET 能读到记录。
_LETTERS: list[dict] = []


def clear_letters_for_tests() -> None:
    """测试用清理方法，生产代码不调用。"""
    _LETTERS.clear()


class LetterService:

    def __init__(self, repository: "LetterRepository | None" = None) -> None:
        """
        Args:
            repository: Optional storage backend. If None, falls back to the
            module-level _LETTERS shared list (backward compatible).
        """
        self._repository = repository

    async def create(self, data: dict) -> dict:
        """保存信笺，返回 letterId / createdAt。"""
        if self._repository is not None:
            return await self._repository.create(data)

        # Default in-memory behavior using module-level shared _LETTERS
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
        _LETTERS.append(record)
        return {"letterId": letter_id, "createdAt": created_at}

    async def list(self, limit: int = 50, offset: int = 0) -> dict:
        """返回最近创建的信笺（最新在前）。"""
        if self._repository is not None:
            return await self._repository.list(limit=limit, offset=offset)

        # Default in-memory behavior using module-level shared _LETTERS
        limit  = max(1, min(limit, 100))
        offset = max(0, offset)
        all_sorted = list(reversed(_LETTERS))
        total      = len(all_sorted)
        page       = all_sorted[offset: offset + limit]
        return {
            "letters": page,
            "total":   total,
            "limit":   limit,
            "offset":  offset,
        }

    async def update_favorite(self, letter_id: str, favorited: bool) -> dict | None:
        """更新信笺收藏状态。"""
        if self._repository is not None:
            return await self._repository.update_favorite(letter_id, favorited)

        # Default in-memory fallback
        for record in _LETTERS:
            if record["letterId"] == letter_id:
                record["favorited"] = favorited
                return record
        return None

    def clear(self) -> None:
        """清空存储。"""
        if self._repository is not None:
            self._repository.clear()
            return
        _LETTERS.clear()
