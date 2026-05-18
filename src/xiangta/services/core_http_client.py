"""
Core HTTP Client — XiangTa 对 Voice Lab Core 的 HTTP 上层调用封装。

只封装 GET/POST，不读取任何真实 Provider API key。
不使用 httpx 以外的额外依赖（项目已有 httpx 则复用）。
不使用复杂生命周期管理，每次请求用短生命周期 context。
"""
from __future__ import annotations

import logging

try:
    import httpx
except ImportError:
    httpx = None


logger = logging.getLogger(__name__)


class CoreHttpClient:
    """
    封装 XiangTa 到 Core 的 HTTP 调用。

    - base_url 末尾斜杠自动规范化。
    - 支持传入 /api/voice/profiles 等相对路径。
    - 网络错误不泄露 stack trace 到用户端。
    - 不读取真实 Provider API key。
    """

    def __init__(self, base_url: str, timeout: float = 20.0) -> None:
        if httpx is None:
            raise RuntimeError(
                "CoreHttpClient requires httpx but it is not installed. "
                "Please add httpx to requirements.txt or use a fake client in tests."
            )
        # 规范化 base_url，去除末尾斜杠
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _url(self, path: str) -> str:
        """拼接 base_url 和相对路径，自动处理斜杠。"""
        path = path.lstrip("/")
        return f"{self._base_url}/{path}"

    async def get(self, path: str) -> dict:
        """
        发起 GET 请求。
        网络错误捕获后返回安全错误 dict，不抛异常。
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(self._url(path))
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("Core HTTP GET %s failed: %s", path, exc)
            return {"error": "network_error", "detail": "Failed to reach Core"}

    async def post(self, path: str, json: dict) -> dict:
        """
        发起 POST 请求。
        网络错误捕获后返回安全错误 dict，不抛异常。
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url(path), json=json)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("Core HTTP POST %s failed: %s", path, exc)
            return {"error": "network_error", "detail": "Failed to reach Core"}

    def absolute_url(self, url_or_path: str) -> str:
        """
        将相对路径转换为绝对 URL。

        - 以 http:// 或 https:// 开头的 URL 原样返回。
        - 以 /api/ 开头的相对路径拼接 Core base_url。
        - 空字符串原样返回。
        """
        if not url_or_path:
            return url_or_path
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            return url_or_path
        return self._url(url_or_path)
