"""
Letter Service — 信笺 CRUD。

MVP 阶段：前端用 localStorage，本服务只返回占位 ID。
后续阶段：接入服务端数据库（需新 Core Contract 或独立 XiangTa DB）。
"""
from __future__ import annotations

import time
import random
import string


class LetterService:

    async def create(self, data: dict) -> dict:
        """
        MVP 阶段：生成客户端兼容的 ID，不做服务端持久化。

        Returns:
            {"letterId": str, "createdAt": str}
        """
        # TODO(P17-A4): 决策——服务端存储还是永久本地？MVP 返回占位
        letter_id = "L_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return {"letterId": letter_id, "createdAt": created_at}

    async def list(self, limit: int = 50, offset: int = 0) -> dict:
        """MVP 阶段返回空列表，前端用 localStorage。"""
        # TODO(P17-A4)
        return {"letters": [], "total": 0}
