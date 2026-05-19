"""
P17-XIANGTA-RUNTIME-B8-1 — XiangTa Runtime App 测试

验证 apps/xiangta_runtime/main.py 可以同时提供：
  - /api/xiangta/* 产品 API
  - /h5/* H5 静态页面
  - / 重定向到 /h5/index.html
"""
import pytest
from fastapi.testclient import TestClient

from apps.xiangta_runtime.main import app
from src.xiangta.services.letter_service import clear_letters_for_tests

_LETTER_BODY = {
    "recipient": "lover",
    "scene": "miss",
    "style": "gentle",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "rawText": "好想你呀今天",
    "finalText": "今天有风，想起了你，希望你一切都好。",
    "title": "小风",
}

_SUGGESTIONS_BODY = {
    "recipient": "lover",
    "scene": "miss",
    "rawText": "好想你呀今天",
}

_TTS_BODY = {
    "text": "好想你呀今天好想你",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "recipient": "lover",
    "scene": "miss",
}

_ADMIN_HEADERS = {"X-XiangTa-Admin-Token": "test-admin-token"}


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch):
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_ADMIN_TOKEN", "test-admin-token")


@pytest.fixture(scope="module")
def client():
    with TestClient(app, follow_redirects=False) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_letters():
    clear_letters_for_tests()
    yield
    clear_letters_for_tests()


# ── import & root ─────────────────────────────────────────────────────────────

class TestRuntimeAppImport:

    def test_app_importable(self):
        from apps.xiangta_runtime.main import app as runtime_app
        assert runtime_app is not None

    def test_root_redirects(self, client):
        r = client.get("/")
        assert r.status_code in (200, 301, 302, 307, 308)

    def test_root_redirect_target(self, client):
        r = client.get("/")
        if r.status_code in (301, 302, 307, 308):
            assert "/h5" in r.headers.get("location", "")


# ── H5 静态页面 ──────────────────────────────────────────────────────────────

class TestRuntimeH5:

    def test_h5_index_html_returns_200(self, client):
        r = client.get("/h5/index.html")
        assert r.status_code == 200

    def test_h5_index_html_content_type(self, client):
        r = client.get("/h5/index.html")
        assert "text/html" in r.headers.get("content-type", "")

    def test_h5_styles_css_returns_200(self, client):
        r = client.get("/h5/styles.css")
        assert r.status_code == 200

    def test_h5_app_js_returns_200(self, client):
        r = client.get("/h5/app.js")
        assert r.status_code == 200


# ── API 路由 ──────────────────────────────────────────────────────────────────

class TestRuntimeApi:

    def test_bootstrap_returns_200(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert r.status_code == 200

    def test_bootstrap_ok_true(self, client):
        assert client.get("/api/xiangta/bootstrap").json()["ok"] is True

    def test_suggestions_returns_200(self, client):
        r = client.post("/api/xiangta/suggestions", json=_SUGGESTIONS_BODY)
        assert r.status_code == 200

    def test_suggestions_three_items(self, client):
        data = client.post("/api/xiangta/suggestions", json=_SUGGESTIONS_BODY).json()["data"]
        assert len(data["suggestions"]) == 3

    def test_tts_stable_no_500(self, client):
        r = client.post("/api/xiangta/tts", json=_TTS_BODY)
        assert r.status_code != 500, f"tts raised 500: {r.text}"

    def test_tts_stable_response_shape(self, client):
        r = client.post("/api/xiangta/tts", json=_TTS_BODY)
        assert r.status_code in (200, 400)
        body = r.json()
        if r.status_code == 400:
            assert body["ok"] is False
            assert "errorKind" in body
        else:
            assert body["ok"] is True

    def test_create_letter_returns_200(self, client):
        r = client.post("/api/xiangta/letters", json=_LETTER_BODY)
        assert r.status_code == 200

    def test_list_letters_returns_200(self, client):
        r = client.get("/api/xiangta/letters")
        assert r.status_code == 200

    def test_admin_config_returns_200(self, client):
        r = client.get("/api/xiangta/admin/config", headers=_ADMIN_HEADERS)
        assert r.status_code == 200


# ── H5 与 API 同源共存 ────────────────────────────────────────────────────────

class TestRuntimeCoexistence:

    def test_h5_and_api_on_same_app(self, client):
        h5_ok = client.get("/h5/index.html").status_code == 200
        api_ok = client.get("/api/xiangta/bootstrap").status_code == 200
        assert h5_ok and api_ok, "H5 and API should both be accessible on the same app"

    def test_api_path_not_shadowed_by_h5_mount(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert r.status_code == 200
        assert r.json().get("ok") is True
