"""
P25V-FIX1 — Audio proxy API tests.

Verifies:
  1. Missing url returns 400 error.
  2. Non-http/https URL is rejected with 400.
  3. URL not matching core_base_url host:port is rejected with 403.
  4. Allowed core URL is fetched and returned with correct Content-Type.
  5. Range header is forwarded to upstream.
  6. Upstream 206 Partial Content is returned as 206.
  7. Content-Type from upstream is preserved.
  8. Upstream connection error returns 502.
  9. Unconfigured core returns 503.

Uses monkeypatched httpx.AsyncClient — no real Core is called.
"""
import pytest
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.xiangta.api.routes import router


ALLOWED_URL = "http://127.0.0.1:8000/api/voice/assets/abc/download"


@pytest.fixture(autouse=True)
def _core_env(monkeypatch):
    """Set a fake core_base_url so the allowlist check can pass."""
    monkeypatch.setenv("XIANGTA_CORE_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_CORE_BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper — create a fake httpx.Response
# ---------------------------------------------------------------------------

def _fake_upstream(
    status_code: int = 200,
    content: bytes = b"FAKEAUDIO",
    content_type: str = "audio/mpeg",
    extra_headers: dict | None = None,
) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.content = content
    headers: dict[str, str] = {"content-type": content_type}
    if extra_headers:
        headers.update(extra_headers)
    resp.headers = headers
    return resp


def _make_client_ctx(return_value: MagicMock):
    """Build an async context manager mock for httpx.AsyncClient(...)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=return_value)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ---------------------------------------------------------------------------
# Validation tests (no upstream call needed)
# ---------------------------------------------------------------------------

class TestAudioProxyValidation:
    def test_missing_url_returns_400(self, client):
        r = client.get("/api/xiangta/audio/proxy")
        assert r.status_code == 400
        body = r.json()
        assert body["errorKind"] == "bad_request"

    def test_empty_url_returns_400(self, client):
        r = client.get("/api/xiangta/audio/proxy?url=")
        assert r.status_code == 400
        assert r.json()["errorKind"] == "bad_request"

    def test_non_http_url_rejected(self, client):
        r = client.get("/api/xiangta/audio/proxy?url=ftp://127.0.0.1:8000/file.mp3")
        assert r.status_code == 400
        assert r.json()["errorKind"] == "bad_request"

    def test_file_url_rejected(self, client):
        r = client.get("/api/xiangta/audio/proxy?url=file:///etc/passwd")
        assert r.status_code == 400

    def test_disallowed_host_rejected(self, client):
        """URL pointing to a different host must be rejected (open proxy prevention)."""
        r = client.get(
            "/api/xiangta/audio/proxy?url=http://evil.example.com/audio.mp3"
        )
        assert r.status_code == 403
        assert r.json()["errorKind"] == "forbidden"

    def test_disallowed_port_rejected(self, client):
        """Same host but different port must also be rejected."""
        r = client.get(
            "/api/xiangta/audio/proxy?url=http://127.0.0.1:9999/audio.mp3"
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Fetch tests (upstream mocked)
# ---------------------------------------------------------------------------

class TestAudioProxyFetch:
    def test_allowed_url_returns_200(self, client):
        fake = _fake_upstream(status_code=200, content=b"AUDIO_BYTES")
        mock_client = _make_client_ctx(fake)
        with patch("src.xiangta.api.routes.httpx.AsyncClient", return_value=mock_client):
            r = client.get(f"/api/xiangta/audio/proxy?url={ALLOWED_URL}")
        assert r.status_code == 200
        assert r.content == b"AUDIO_BYTES"

    def test_content_type_preserved(self, client):
        fake = _fake_upstream(content_type="audio/wav")
        mock_client = _make_client_ctx(fake)
        with patch("src.xiangta.api.routes.httpx.AsyncClient", return_value=mock_client):
            r = client.get(f"/api/xiangta/audio/proxy?url={ALLOWED_URL}")
        assert "audio/wav" in r.headers.get("content-type", "")

    def test_range_header_forwarded(self, client):
        """When client sends Range, it should be forwarded to upstream."""
        captured: dict = {}

        async def capturing_get(url, headers=None, **kw):
            captured["headers"] = headers or {}
            return _fake_upstream(
                status_code=206,
                extra_headers={
                    "content-range": "bytes 0-999/5000",
                    "accept-ranges": "bytes",
                },
            )

        mock_client = MagicMock()
        mock_client.get = capturing_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.xiangta.api.routes.httpx.AsyncClient", return_value=mock_client):
            r = client.get(
                f"/api/xiangta/audio/proxy?url={ALLOWED_URL}",
                headers={"Range": "bytes=0-999"},
            )
        assert r.status_code == 206
        assert "Range" in captured["headers"]
        assert captured["headers"]["Range"] == "bytes=0-999"

    def test_upstream_206_returned_as_206(self, client):
        fake = _fake_upstream(
            status_code=206,
            extra_headers={
                "content-range": "bytes 0-999/5000",
                "accept-ranges": "bytes",
            },
        )
        mock_client = _make_client_ctx(fake)
        with patch("src.xiangta.api.routes.httpx.AsyncClient", return_value=mock_client):
            r = client.get(
                f"/api/xiangta/audio/proxy?url={ALLOWED_URL}",
                headers={"Range": "bytes=0-999"},
            )
        assert r.status_code == 206

    def test_content_range_header_forwarded(self, client):
        fake = _fake_upstream(
            status_code=206,
            extra_headers={"content-range": "bytes 0-999/5000"},
        )
        mock_client = _make_client_ctx(fake)
        with patch("src.xiangta.api.routes.httpx.AsyncClient", return_value=mock_client):
            r = client.get(
                f"/api/xiangta/audio/proxy?url={ALLOWED_URL}",
                headers={"Range": "bytes=0-999"},
            )
        assert (
            "content-range" in r.headers or "Content-Range" in r.headers
        ), "Content-Range must be forwarded"

    def test_upstream_error_returns_502(self, client):
        async def failing_get(url, headers=None, **kw):
            raise httpx.ConnectError("connection refused")

        mock_client = MagicMock()
        mock_client.get = failing_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.xiangta.api.routes.httpx.AsyncClient", return_value=mock_client):
            r = client.get(f"/api/xiangta/audio/proxy?url={ALLOWED_URL}")
        assert r.status_code == 502
        assert r.json()["errorKind"] == "upstream_error"


class TestAudioProxyNoCoreConfigured:
    def test_no_core_returns_503(self, client, monkeypatch):
        monkeypatch.setenv("XIANGTA_CORE_ENABLED", "false")
        monkeypatch.delenv("XIANGTA_CORE_BASE_URL", raising=False)
        r = client.get(
            f"/api/xiangta/audio/proxy?url={ALLOWED_URL}"
        )
        assert r.status_code == 503
        assert r.json()["errorKind"] == "not_configured"
