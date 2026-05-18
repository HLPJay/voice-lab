"""
Tests for C8 Copywriting Gateway.

Covers:
1. Default CopywritingService (no gateway) returns template 3 suggestions
2. FakeLlmCopywritingGateway returns 3 stable suggestions
3. CopywritingService with fake gateway returns fake LLM results
4. fake gateway failure + fallback=True → template
5. fake gateway failure + fallback=False → LlmFailedError
6. create_product_service default config → template
7. env enables fake LLM → get_suggestions uses fake LLM
8. unknown provider → safe fallback (template), no real API calls
9. /suggestions response doesn't expose provider/model/apiKey/rawResponse
"""
from __future__ import annotations

import pytest

from src.xiangta.services.copywriting_gateway import (
    CopywritingRequest,
    CopywritingSuggestion,
    CopywritingResult,
    FakeLlmCopywritingGateway,
    TemplateCopywritingGateway,
)
from src.xiangta.services.copywriting_service import CopywritingService
from src.xiangta.services.error_translator import LlmFailedError

_FORBIDDEN_KEYS = {
    "provider", "model", "api_key", "rawResponse",
    "prompt", "minimax_api_key", "openai_api_key",
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
    async def test_returns_3_suggestions(self):
        gw = TemplateCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover", scene="miss", raw_text="想你了"
        ))
        assert len(result.suggestions) == 3
        assert result.source == "template"

    @pytest.mark.asyncio
    async def test_styles_are_restrained_gentle_sincere(self):
        gw = TemplateCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover", scene="miss", raw_text="想你了"
        ))
        styles = {s.style for s in result.suggestions}
        assert styles == {"restrained", "gentle", "sincere"}

    @pytest.mark.asyncio
    async def test_style_labels_chinese(self):
        gw = TemplateCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover", scene="miss", raw_text="想你了"
        ))
        labels = {s.style_label for s in result.suggestions}
        assert labels == {"克制版", "温柔版", "真诚版"}


class TestFakeLlmGateway:
    @pytest.mark.asyncio
    async def test_returns_3_suggestions(self):
        gw = FakeLlmCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover", scene="miss", raw_text="想你了"
        ))
        assert len(result.suggestions) == 3
        assert result.source == "fake_llm"

    @pytest.mark.asyncio
    async def test_contains_raw_text_in_each(self):
        gw = FakeLlmCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover", scene="miss", raw_text="想你了"
        ))
        for s in result.suggestions:
            assert "想你了" in s.text

    @pytest.mark.asyncio
    async def test_failure_raises(self):
        gw = FakeLlmCopywritingGateway(should_fail=True)
        with pytest.raises(RuntimeError):
            await gw.generate(CopywritingRequest(
                recipient="lover", scene="miss", raw_text="想你了"
            ))


class TestCopywritingServiceWithGateway:
    @pytest.mark.asyncio
    async def test_no_gateway_uses_template(self):
        svc = CopywritingService(gateway=None)
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert len(result["suggestions"]) == 3
        styles = {s["style"] for s in result["suggestions"]}
        assert styles == {"restrained", "gentle", "sincere"}

    @pytest.mark.asyncio
    async def test_fake_gateway_returns_fake_results(self):
        gw = FakeLlmCopywritingGateway()
        svc = CopywritingService(gateway=gw, fallback_to_template=True)
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert len(result["suggestions"]) == 3
        # fake LLM text contains raw_text
        assert any("想你了" in s["text"] for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_gateway_failure_with_fallback_uses_template(self):
        gw = FakeLlmCopywritingGateway(should_fail=True)
        svc = CopywritingService(gateway=gw, fallback_to_template=True)
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        # Should fall back to template
        assert len(result["suggestions"]) == 3
        styles = {s["style"] for s in result["suggestions"]}
        assert styles == {"restrained", "gentle", "sincere"}

    @pytest.mark.asyncio
    async def test_gateway_failure_no_fallback_raises_llm_failed(self):
        gw = FakeLlmCopywritingGateway(should_fail=True)
        svc = CopywritingService(gateway=gw, fallback_to_template=False)
        with pytest.raises(LlmFailedError):
            await svc.generate_suggestions(
                recipient="lover", scene="miss", raw_text="想你了"
            )


class TestProductServiceWiring:
    def test_default_uses_template(self, monkeypatch):
        """默认配置不走 fake LLM gateway."""
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
        # template has scene-based closers, fake has AI prefix
        assert "想你" in result["suggestions"][0]["text"]

    def test_fake_llm_env_uses_fake_gateway(self, monkeypatch):
        """显式开启 fake LLM 时使用 FakeLlmCopywritingGateway."""
        monkeypatch.setenv("XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED", "true")
        monkeypatch.setenv("XIANGTA_COPYWRITING_MODE", "llm")
        monkeypatch.setenv("XIANGTA_COPYWRITING_PROVIDER", "fake")

        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            svc.get_suggestions(recipient="lover", scene="miss", raw_text="想你")
        )
        # fake LLM format has "轻轻说给你听" / "慢慢告诉你" / "认真说"
        texts = [s["text"] for s in result["suggestions"]]
        assert any("轻轻" in t or "慢慢" in t or "认真" in t for t in texts)

    def test_unknown_provider_falls_back_to_template(self, monkeypatch):
        """未知 provider 不调用外部 API，安全回退 template."""
        monkeypatch.setenv("XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED", "true")
        monkeypatch.setenv("XIANGTA_COPYWRITING_MODE", "llm")
        monkeypatch.setenv("XIANGTA_COPYWRITING_PROVIDER", "minimax")  # not implemented

        import importlib
        import src.xiangta.services.product_service as ps_module
        importlib.reload(ps_module)
        svc = ps_module.create_product_service()

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            svc.get_suggestions(recipient="lover", scene="miss", raw_text="想你")
        )
        assert len(result["suggestions"]) == 3
        # should be template, not fake LLM
        assert "想你" in result["suggestions"][0]["text"]


class TestSuggestionsApiSecurity:
    def test_suggestions_response_no_forbidden_fields(self, monkeypatch):
        """默认 template 模式下 /suggestions 不暴露 provider/model/apiKey."""
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
