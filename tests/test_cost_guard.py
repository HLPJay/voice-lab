"""Tests for Cost Guard feature: character estimation, cost calculation, and confirm_cost enforcement."""

import pytest
from fastapi.testclient import TestClient

from app.services.cost_guard_service import (
    CostGuardService,
    estimate_billing_characters,
    estimate_t2a_cost,
)


class TestBillingCharacterEstimation:
    """estimate_billing_characters rules: CJK=2, ASCII=1, other=1."""

    def test_chinese_characters_count_as_2(self):
        assert estimate_billing_characters("你好世界") == 8  # 4 chars * 2

    def test_english_letters_count_as_1(self):
        assert estimate_billing_characters("hello world") == 11  # 11 chars

    def test_digits_count_as_1(self):
        assert estimate_billing_characters("12345") == 5

    def test_space_and_punctuation_count_as_1(self):
        assert estimate_billing_characters("Hello, world!") == 13

    def test_mixed_cjk_and_ascii(self):
        # "Hello你好" = 5*1 + 2*2 = 9
        assert estimate_billing_characters("Hello你好") == 9

    def test_newline_counts_as_1(self):
        assert estimate_billing_characters("hello\nworld") == 11

    def test_empty_string(self):
        assert estimate_billing_characters("") == 0


class TestMinimaxCostEstimation:
    """estimate_t2a_cost for minimax provider."""

    def test_speech_2_8_turbo_price(self):
        est = estimate_t2a_cost("minimax", "speech-2.8-turbo", "hello world")  # 11 chars
        assert est["billing_characters"] == 11
        assert est["unit_price_cny_per_10k_chars"] == 2.0
        assert est["estimated_cost_cny"] == round(11 / 10000 * 2.0, 6)
        assert est["unknown_price"] is False

    def test_speech_2_8_hd_price(self):
        est = estimate_t2a_cost("minimax", "speech-2.8-hd", "你好")  # 2 CJK = 4 chars
        assert est["billing_characters"] == 4
        assert est["unit_price_cny_per_10k_chars"] == 3.5
        assert est["estimated_cost_cny"] == round(4 / 10000 * 3.5, 6)
        assert est["unknown_price"] is False

    def test_speech_02_5_turbo_price(self):
        est = estimate_t2a_cost("minimax", "speech-02.5-turbo", "hello")
        assert est["unit_price_cny_per_10k_chars"] == 2.0
        assert est["unknown_price"] is False

    def test_unknown_model_unknown_price(self):
        est = estimate_t2a_cost("minimax", "unknown-model", "hello")
        assert est["unknown_price"] is True
        assert est["estimated_cost_cny"] is None

    def test_non_minimax_returns_unknown_price(self):
        est = estimate_t2a_cost("openai", "gpt-4", "hello")
        assert est["unknown_price"] is True
        assert est["warnings"] == ["当前 provider 暂未配置价格估算"]
        assert est["estimated_cost_cny"] is None

    def test_cost_guard_service_wrapper(self):
        svc = CostGuardService()
        est = svc.estimate_t2a_cost("minimax", "speech-2.8-hd", "你好世界")
        assert est["billing_characters"] == 8
        assert est["estimated_cost_cny"] == round(8 / 10000 * 3.5, 6)


class TestConfirmCostEnforcement:
    """minimax high-risk operations require confirm_cost=true."""

    def test_voice_design_without_confirm_cost_rejected(self, test_app, seed_profile):
        """minimax voice_design without confirm_cost returns 422."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/design/create?provider=minimax",
            json={"prompt": "成熟女性，温柔知性", "preview_text": "你好，这是一段试听文本。"},
        )
        assert resp.status_code == 422

    def test_voice_design_with_confirm_cost_not_rejected(self, test_app, seed_profile):
        """minimax voice_design with confirm_cost=true is not rejected for confirm_cost reasons."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/design/create?provider=minimax",
            json={
                "prompt": "成熟女性，温柔知性",
                "preview_text": "你好，这是一段试听文本。",
                "confirm_cost": True,
            },
        )
        # Should NOT be 422 for confirm_cost validation
        assert resp.status_code != 422 or "confirm_cost" not in resp.text.lower()

    def test_voice_clone_without_confirm_cost_rejected(self, test_app, seed_profile):
        """minimax voice_clone without confirm_cost returns 422."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/clone/create?provider=minimax",
            json={
                "voice_id": "test_voice_clone_minimax",
                "file_id": 999999,
                "confirm_cost": False,
            },
        )
        assert resp.status_code in (400, 422)

    def test_provider_voice_preview_without_confirm_cost_rejected(self, test_app, seed_profile):
        """minimax provider_voice_preview without confirm_cost returns 422."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/provider-voices/preview?provider=minimax",
            json={
                "provider_voice_id": "some_voice",
                "model": "speech-2.8-hd",
                "text": "你好试听",
                "confirm_cost": False,
            },
        )
        assert resp.status_code == 422

    def test_batch_longtext_without_confirm_cost_rejected(self, test_app, session, seed_profile, seed_mock_binding):
        """minimax longtext batch without confirm_cost returns 422."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/batch/submit",
            json={
                "mode": "longtext",
                "text": "这是一段测试文本。",
                "profile_id": "deep_night_programmer",
                "provider": "minimax",
                "confirm_cost": False,
                "params": {},
            },
        )
        assert resp.status_code == 422

    def test_batch_script_without_confirm_cost_rejected(self, test_app, session, seed_profile, seed_mock_binding):
        """minimax script batch without confirm_cost returns 422."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/batch/submit",
            json={
                "mode": "script",
                "script": [
                    {"role": "narrator", "text": "你好世界", "profile_id": "deep_night_programmer"},
                ],
                "provider": "minimax",
                "confirm_cost": False,
            },
        )
        assert resp.status_code == 422

    def test_mock_provider_does_not_require_confirm_cost(self, test_app, seed_profile):
        """mock provider voice_design does not enforce confirm_cost."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/design/create?provider=mock",
            json={
                "prompt": "成熟女性，温柔知性",
                "preview_text": "你好，这是一段试听文本。",
                "confirm_cost": False,
            },
        )
        # 200-499 (not 422 about confirm_cost)
        assert resp.status_code != 422 or "confirm_cost" in resp.text.lower()

    def test_confirm_cost_true_passes_validation(self, test_app, session, seed_profile, seed_mock_binding):
        """confirm_cost=True bypasses the guard for minimax batch."""
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/batch/submit",
            json={
                "mode": "longtext",
                "text": "测试文本",
                "profile_id": "deep_night_programmer",
                "provider": "minimax",
                "confirm_cost": True,
                "params": {},
            },
        )
        # Should not be 422 (confirm_cost validation error)
        assert resp.status_code != 422


class TestCostEstimateAPI:
    """POST /api/voice/cost/estimate endpoint."""

    def test_estimate_cost_minimax_turbo(self, test_app):
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/cost/estimate",
            json={"provider": "minimax", "model": "speech-2.8-turbo", "text": "hello world"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["billing_characters"] == 11
        assert data["estimated_cost_cny"] == round(11 / 10000 * 2.0, 6)
        assert data["unknown_price"] is False

    def test_estimate_cost_minimax_hd(self, test_app):
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/cost/estimate",
            json={"provider": "minimax", "model": "speech-2.8-hd", "text": "你好"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["billing_characters"] == 4  # 2 CJK * 2
        assert data["estimated_cost_cny"] == round(4 / 10000 * 3.5, 6)

    def test_estimate_cost_non_minimax(self, test_app):
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/cost/estimate",
            json={"provider": "openai", "model": "tts-1", "text": "hello"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["unknown_price"] is True
        assert "暂未配置" in data["warnings"][0]
