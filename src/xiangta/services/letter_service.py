"""
LetterService — 信笺 CRUD。

B6-1 版本：进程内内存存储 MVP。
不写文件，不接 DB，不调用 Core / Provider / LLM。
"""
from __future__ import annotations

import random
import string
import time

# 模块级全局 store，所有 LetterService 实例共享。
# 保证 POST 后 GET 能读到记录。
_LETTERS: list[dict] = []


def clear_letters_for_tests() -> None:
    """测试用清理方法，生产代码不调用。"""
    _LETTERS.clear()


class LetterService:

    async def create(self, data: dict) -> dict:
        """保存信笺，返回 letterId / createdAt。"""
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
        limit  = max(1, min(limit, 100))
        offset = max(0, offset)
        # 最新在前
        all_sorted = list(reversed(_LETTERS))
        total      = len(all_sorted)
        page       = all_sorted[offset: offset + limit]
        return {
            "letters": page,
            "total":   total,
            "limit":   limit,
            "offset":  offset,
        }

    def clear(self) -> None:
        """测试用实例方法，等同于 clear_letters_for_tests()。"""
        _LETTERS.clear()
