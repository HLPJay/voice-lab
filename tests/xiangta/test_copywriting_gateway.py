"""
Tests for C8 Copywriting Gateway.

Covers (7 test functions, 12 test cases):
1. TemplateGateway: 3 suggestions, styles, labels
2. FakeLlmGateway success + failure (parametrized)
3. CopywritingService: gateway=None/fake/success (parametrized)
4. CopywritingService: fallback behavior (parametrized)
5. create_product_service: default config → template
6. create_product_service: provider wiring (parametrized, 3 cases)
7. /suggestions: no forbidden fields
"""
from __future__ import annotations

import pytest

from src.xiangta.services.copywriting_gateway import (
    CopywritingRequest,
    FakeLlmCopywritingGateway,
    TemplateCopywritingGateway,
)
from src.xiangta.services.copywriting_service import CopywritingService
from src.xiangta.services.error_translator import LlmFailedError

_FORBIDDEN_KEYS = {
    "provider", "model", "api_key", "rawResponse",
    "prompt", "source",
}


def _collect_keys(obj, seen=None):
    if seen is None:
        seen = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            seen.add(k)
            _collect_keys(v, seen)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, seen)
    return seen


class TestTemplateGateway:
    @pytest.mark.asyncio
    async def test_template_returns_3_suggestions(self):
        """TemplateGateway: 3 suggestions, restrained/gentle/sincere, Chinese labels."""
        gw = TemplateCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover", scene="miss", raw_text="想你了"
        ))
        assert len(result.suggestions) == 3
        assert {s.style for s in result.suggestions} == {"restrained", "gentle", "sincere"}
        assert {s.style_label for s in result.suggestions} == {"克制版", "温柔版", "真诚版"}
        assert result.source == "template"


class TestFakeLlmGateway:
    @pytest.mark.parametrize("should_fail,expect_success", [(False, True), (True, False)])
    @pytest.mark.asyncio
    async def test_fake_llm(self, should_fail, expect_success):
        """FakeLlmGateway: success returns 3 suggestions; failure raises."""
        gw = FakeLlmCopywritingGateway(should_fail=should_fail)
        if expect_success:
            result = await gw.generate(CopywritingRequest(
                recipient="lover", scene="miss", raw_text="想你了"
            ))
            assert len(result.suggestions) == 3
            assert result.source == "fake_llm"
            for s in result.suggestions:
                assert "想你了" in s.text
        else:
            with pytest.raises(RuntimeError):
                await gw.generate(CopywritingRequest(
                    recipient="lover", scene="miss", raw_text="想你了"
                ))


class TestCopywritingService:
    @pytest.mark.parametrize("gateway_type", ["none", "fake"])
    @pytest.mark.asyncio
    async def test_copywriting_service_gateway(self, gateway_type):
        """gateway=None→template; gateway=fake→fake results."""
        gw = None if gateway_type == "none" else FakeLlmCopywritingGateway()
        svc = CopywritingService(gateway=gw, fallback_to_template=True)
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert len(result["suggestions"]) == 3
        assert {s["style"] for s in result["suggestions"]} == {"restrained", "gentle", "sincere"}
        if gateway_type == "fake":
            assert any("想你了" in s["text"] for s in result["suggestions"])

    @pytest.mark.parametrize("fallback,expect_error", [(True, False), (False, True)])
    @pytest.mark.asyncio
    async def test_fallback_behavior(self, fallback, expect_error):
        """fallback=True→template; fallback=False→raises LlmFailedError."""
        gw = FakeLlmCopywritingGateway(should_fail=True)
        svc = CopywritingService(gateway=gw, fallback_to_template=fallback)
        if expect_error:
            with pytest.raises(LlmFailedError):
                await svc.generate_suggestions(
                    recipient="lover", scene="miss", raw_text="想你了"
                )
        else:
            result = await svc.generate_suggestions(
                recipient="lover", scene="miss", raw_text="想你了"
            )
            assert len(result["suggestions"]) == 3


class TestProductServiceWiring:
    def test_default_uses_template(self, monkeypatch):
        """默认配置不走 fake LLM, 使用 template."""
        monkeypatch.setenv("XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED", "false")
        monkeypatch.setenv("XIANGTA_COPYWRITING_MODE", "template")
        monkeypatch.setenv("XIANGTA_COPYWRITING_PROVIDER", "none")

        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            svc.get_suggestions(recipient="lover", scene="miss", raw_text="想你")
        )
        assert len(result["suggestions"]) == 3
        assert "想你" in result["suggestions"][0]["text"]

    @pytest.mark.parametrize("provider,expect_fake", [
        ("none",    False),
        ("fake",    True),
        ("minimax", False),
    ])
    def test_provider_wiring(self, monkeypatch, provider, expect_fake):
        """不同 provider 值：fake→fake LLM, 其他→template."""
        monkeypatch.setenv("XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED", "true")
        monkeypatch.setenv("XIANGTA_COPYWRITING_MODE", "llm")
        monkeypatch.setenv("XIANGTA_COPYWRITING_PROVIDER", provider)

        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            svc.get_suggestions(recipient="lover", scene="miss", raw_text="想你")
        )
        assert len(result["suggestions"]) == 3
        if expect_fake:
            texts = [s["text"] for s in result["suggestions"]]
            assert any("轻轻" in t or "慢慢" in t or "认真" in t for t in texts)
        else:
            assert "想你" in result["suggestions"][0]["text"]


class TestSuggestionsApi:
    def test_suggestions_response_no_forbidden_fields(self):
        """默认 template 模式下 /suggestions 不暴露 provider/model/apiKey/source."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.xiangta.api.routes import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "lover",
            "scene": "miss",
            "rawText": "我想说一些话",
        })
        assert r.status_code == 200
        body = r.json()
        bad = _collect_keys(body) & _FORBIDDEN_KEYS
        assert not bad, f"响应包含禁止字段：{bad}"
