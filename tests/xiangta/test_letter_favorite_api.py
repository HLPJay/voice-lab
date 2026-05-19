"""P25H: Letter favorite API — backend targeted test."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.services.letter_service import LetterService, clear_letters_for_tests


@pytest.fixture(autouse=True)
def _clear_letters():
    """Clear in-memory letters before and after each test for isolation."""
    clear_letters_for_tests()
    yield
    clear_letters_for_tests()


@pytest.fixture(scope="function")
def client():
    """Create a fresh FastAPI app with xiangta router for each test."""
    clear_letters_for_tests()
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestLetterFavoriteAPI:
    """Test the favorite update endpoint."""

    def test_patch_letters_favorite_updates_favorited_true(self, client):
        """PATCH with favorited=true sets favorited=True on the letter."""
        # Create a letter first
        create_resp = client.post(
            "/api/xiangta/letters",
            json={
                "recipient": "lover",
                "scene": "miss",
                "style": "gentle",
                "rawText": "test raw",
                "finalText": "test final",
                "voicePreset": "female-gentle",
                "tone": "gentle",
            },
        )
        assert create_resp.status_code == 200
        letter_id = create_resp.json()["data"]["letterId"]

        # Verify initial favorited is False
        list_resp = client.get("/api/xiangta/letters")
        assert list_resp.status_code == 200
        letters = list_resp.json()["data"]["letters"]
        letter = next(l for l in letters if l["letterId"] == letter_id)
        assert letter["favorited"] is False

        # Update favorite to true
        fav_resp = client.patch(
            f"/api/xiangta/letters/{letter_id}/favorite",
            json={"favorited": True},
        )
        assert fav_resp.status_code == 200
        assert fav_resp.json()["ok"] is True
        assert fav_resp.json()["data"]["favorited"] is True

        # Verify persistence via GET
        list_resp2 = client.get("/api/xiangta/letters")
        letters2 = list_resp2.json()["data"]["letters"]
        letter2 = next(l for l in letters2 if l["letterId"] == letter_id)
        assert letter2["favorited"] is True

    def test_patch_letters_favorite_updates_favorited_false(self, client):
        """PATCH with favorited=false sets favorited=False on the letter."""
        # Create a letter first
        create_resp = client.post(
            "/api/xiangta/letters",
            json={
                "recipient": "lover",
                "scene": "miss",
                "style": "gentle",
                "rawText": "test raw",
                "finalText": "test final",
                "voicePreset": "female-gentle",
                "tone": "gentle",
            },
        )
        assert create_resp.status_code == 200
        letter_id = create_resp.json()["data"]["letterId"]

        # Set to true first
        client.patch(
            f"/api/xiangta/letters/{letter_id}/favorite",
            json={"favorited": True},
        )

        # Set back to false
        fav_resp = client.patch(
            f"/api/xiangta/letters/{letter_id}/favorite",
            json={"favorited": False},
        )
        assert fav_resp.status_code == 200
        assert fav_resp.json()["data"]["favorited"] is False

        # Verify via GET
        list_resp = client.get("/api/xiangta/letters")
        letters = list_resp.json()["data"]["letters"]
        letter = next(l for l in letters if l["letterId"] == letter_id)
        assert letter["favorited"] is False

    def test_patch_letters_unknown_id_returns_404(self, client):
        """PATCH with unknown letter_id returns 404."""
        resp = client.patch(
            "/api/xiangta/letters/nonexistent_id/favorite",
            json={"favorited": True},
        )
        assert resp.status_code == 404
        assert resp.json()["ok"] is False
        assert resp.json()["errorKind"] == "not_found"

    def test_post_letters_defaults_favorited_false(self, client):
        """POST /letters creates letter with favorited=False."""
        resp = client.post(
            "/api/xiangta/letters",
            json={
                "recipient": "lover",
                "scene": "miss",
                "style": "gentle",
                "rawText": "test raw",
                "finalText": "test final",
                "voicePreset": "female-gentle",
                "tone": "gentle",
            },
        )
        assert resp.status_code == 200
        letter_id = resp.json()["data"]["letterId"]

        list_resp = client.get("/api/xiangta/letters")
        letters = list_resp.json()["data"]["letters"]
        letter = next(l for l in letters if l["letterId"] == letter_id)
        assert letter["favorited"] is False
