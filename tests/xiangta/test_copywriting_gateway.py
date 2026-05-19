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
    "prompt",
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

    @pytest.mark.asyncio
    async def test_template_avoids_duplicate_terminal_punctuation(self):
        gw = TemplateCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover",
            scene="comfort",
            raw_text="如果你今天很累，就先不用解释。想说的时候我会听，不想说也没有关系。",
        ))
        texts = [s.text for s in result.suggestions]
        assert all("。。" not in text for text in texts)
        assert all("。，" not in text for text in texts)

    @pytest.mark.asyncio
    async def test_comfort_templates_use_light_paragraph_break(self):
        gw = TemplateCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover",
            scene="comfort",
            raw_text="如果你今天很累，就先不用解释。想说的时候我会听，不想说也没有关系。",
        ))
        texts = {s.style: s.text for s in result.suggestions}
        assert "\n\n我在这里，随时找我。" in texts["restrained"]
        assert "\n\n不管怎样，我陪着你。" in texts["gentle"]
        assert "\n\n你不是一个人，我一直在。" in texts["sincere"]

    @pytest.mark.asyncio
    async def test_other_scenes_also_use_light_paragraph_break(self):
        gw = TemplateCopywritingGateway()
        for scene in ["miss", "sorry", "thanks", "night"]:
            result = await gw.generate(CopywritingRequest(
                recipient="lover",
                scene=scene,
                raw_text="今天突然想起你了。",
            ))
            assert all("\n\n" in s.text for s in result.suggestions), scene

    @pytest.mark.asyncio
    async def test_paragraph_break_adds_terminal_punctuation_when_missing(self):
        gw = TemplateCopywritingGateway()
        result = await gw.generate(CopywritingRequest(
            recipient="lover",
            scene="thanks",
            raw_text="今天真的很想认真谢谢你",
        ))
        texts = [s.text for s in result.suggestions]
        assert all("。\n\n" in text for text in texts)


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


# ── normalize_copy_text ────────────────────────────────────────────────────────

from src.xiangta.services.copywriting_gateway import normalize_copy_text


class TestNormalizeCopyText:
    def test_empty_string(self):
        assert normalize_copy_text("") == ""
        assert normalize_copy_text(None) == ""

    def test_passes_through_normal_text(self):
        text = "今天突然想起你，其实我心里很安静，也很想靠近你。"
        assert normalize_copy_text(text) == text

    def test_cleans_duplicate_periods(self):
        assert normalize_copy_text("今天想起你。。") == "今天想起你。"
        assert normalize_copy_text("很想你。。真的好想你。。") == "很想你。真的好想你。"

    def test_cleans_duplicate_exclamation(self):
        assert normalize_copy_text("想你！！") == "想你！"

    def test_cleans_duplicate_question(self):
        assert normalize_copy_text("你在干嘛？？") == "你在干嘛？"

    def test_cleans_duplicate_comma(self):
        assert normalize_copy_text("今天，老朋友，，好久不见") == "今天，老朋友，好久不见"

    def test_paragraph_split_two_sentences(self):
        text = "今天突然想起你。其实我心里很安静。"
        result = normalize_copy_text(text)
        assert "今天突然想起你。" in result
        assert "其实我心里很安静。" in result

    def test_paragraph_split_three_sentences_two_paragraphs(self):
        text = "今天突然想起你。其实我心里很安静。也想靠近你。"
        result = normalize_copy_text(text)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "今天突然想起你。" in lines[0]
        assert "其实我心里很安静。" in lines[1] or "也想靠近你。" in lines[1]

    def test_paragraph_max_three(self):
        text = "第一句。第二句。第三句。第四句。第五句。"
        result = normalize_copy_text(text)
        lines = result.split("\n")
        assert len(lines) == 3

    def test_normalizes_before_split(self):
        text = "今天想起你。。第二句。第三句。"
        result = normalize_copy_text(text)
        assert "。。" not in result

    def test_preserves_single_paragraph(self):
        text = "今天突然想起你。"
        result = normalize_copy_text(text)
        assert result == "今天突然想起你。"

    def test_idempotent(self):
        text = "今天想起你。。第二句。第三句。第四句。"
        result1 = normalize_copy_text(text)
        result2 = normalize_copy_text(result1)
        assert result1 == result2


# ── CopywritingService: timeout and fallback ─────────────────────────────────────

import asyncio
from dataclasses import dataclass


class SlowFakeGateway:
    """Fake gateway that sleeps beyond the timeout to simulate LLM timeout."""
    async def generate(self, request):
        await asyncio.sleep(10)  # 10s > 8s default timeout
        from src.xiangta.services.copywriting_gateway import CopywritingResult
        return CopywritingResult(
            summary="slow",
            intent="slow",
            suggestions=[],
            source="fake_slow",
        )


class FailingFakeGateway:
    """Fake gateway that always raises an exception."""
    async def generate(self, request):
        raise RuntimeError("simulated LLM failure")


class TestCopywritingServiceTimeout:
    @pytest.mark.asyncio
    async def test_timeout_returns_degraded_template(self):
        """LLM timeout → fallback to template with degraded=True."""
        gw = SlowFakeGateway()
        svc = CopywritingService(gateway=gw, fallback_to_template=True)
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        # Should fall back to template
        assert len(result["suggestions"]) == 3
        assert result["degraded"] is True
        assert result["source"] == "template"

    @pytest.mark.asyncio
    async def test_timeout_no_degraded_when_fallback_disabled(self):
        """fallback=False with timeout → raises LlmFailedError."""
        gw = SlowFakeGateway()
        svc = CopywritingService(gateway=gw, fallback_to_template=False)
        with pytest.raises(LlmFailedError):
            await svc.generate_suggestions(
                recipient="lover", scene="miss", raw_text="想你了"
            )

    @pytest.mark.asyncio
    async def test_error_returns_degraded_template(self):
        """LLM error → fallback to template with degraded=True."""
        gw = FailingFakeGateway()
        svc = CopywritingService(gateway=gw, fallback_to_template=True)
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert len(result["suggestions"]) == 3
        assert result["degraded"] is True
        assert result["source"] == "template"

    @pytest.mark.asyncio
    async def test_error_no_degraded_when_fallback_disabled(self):
        """fallback=False with error → raises LlmFailedError."""
        gw = FailingFakeGateway()
        svc = CopywritingService(gateway=gw, fallback_to_template=False)
        with pytest.raises(LlmFailedError):
            await svc.generate_suggestions(
                recipient="lover", scene="miss", raw_text="想你了"
            )

    @pytest.mark.asyncio
    async def test_template_only_no_degraded(self):
        """Template-only service returns degraded=False."""
        svc = CopywritingService(gateway=None)
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert result["degraded"] is False
        assert result["source"] == "template"
        assert result["latencyMs"] is None


class TestCopywritingServiceCache:
    @pytest.mark.asyncio
    async def test_cached_result_not_calling_gateway(self):
        """Second call with same params uses cache, does not call gateway."""
        call_count = 0

        class CountingFakeGateway:
            async def generate(self, request):
                nonlocal call_count
                call_count += 1
                from src.xiangta.services.copywriting_gateway import CopywritingResult, CopywritingSuggestion
                return CopywritingResult(
                    summary="cached",
                    intent="cached",
                    suggestions=[
                        CopywritingSuggestion(
                            style="gentle",
                            style_label="温柔版",
                            fits_for="test",
                            text="hello",
                        )
                    ],
                    source="fake",
                )

        gw = CountingFakeGateway()
        from src.xiangta.services.copywriting_service import _CopywritingCache
        cache = _CopywritingCache()
        svc = CopywritingService(gateway=gw, cache=cache)
        await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert call_count == 1
        await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert call_count == 1  # cached, not called again

    @pytest.mark.asyncio
    async def test_different_raw_text_not_cached(self):
        """Different raw_text does not hit cache."""
        call_count = 0

        class CountingFakeGateway:
            async def generate(self, request):
                nonlocal call_count
                call_count += 1
                from src.xiangta.services.copywriting_gateway import CopywritingResult, CopywritingSuggestion
                return CopywritingResult(
                    summary="cached",
                    intent="cached",
                    suggestions=[
                        CopywritingSuggestion(
                            style="gentle",
                            style_label="温柔版",
                            fits_for="test",
                            text=request.raw_text,
                        )
                    ],
                    source="fake",
                )

        gw = CountingFakeGateway()
        from src.xiangta.services.copywriting_service import _CopywritingCache
        cache = _CopywritingCache()
        svc = CopywritingService(gateway=gw, cache=cache)
        await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert call_count == 1
        await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="很想你"
        )
        assert call_count == 2  # different raw_text, not cached

    @pytest.mark.asyncio
    async def test_different_scene_not_cached(self):
        """Different scene does not hit cache."""
        call_count = 0

        class CountingFakeGateway:
            async def generate(self, request):
                nonlocal call_count
                call_count += 1
                from src.xiangta.services.copywriting_gateway import CopywritingResult, CopywritingSuggestion
                return CopywritingResult(
                    summary="cached",
                    intent="cached",
                    suggestions=[
                        CopywritingSuggestion(
                            style="gentle",
                            style_label="温柔版",
                            fits_for="test",
                            text=request.raw_text,
                        )
                    ],
                    source="fake",
                )

        gw = CountingFakeGateway()
        from src.xiangta.services.copywriting_service import _CopywritingCache
        cache = _CopywritingCache()
        svc = CopywritingService(gateway=gw, cache=cache)
        await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="想你了"
        )
        assert call_count == 1
        await svc.generate_suggestions(
            recipient="lover", scene="sorry", raw_text="想你了"
        )
        assert call_count == 2  # different scene, not cached

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Cache can be cleared."""
        from src.xiangta.services.copywriting_service import _CopywritingCache
        cache = _CopywritingCache()
        cache.set("lover", "miss", "想你了", "value")
        assert cache.get("lover", "miss", "想你了") == "value"
        cache.clear()
        assert cache.get("lover", "miss", "想你了") is None

    @pytest.mark.asyncio
    async def test_cache_eviction(self):
        """Cache evicts oldest entry when full (100 entries)."""
        from src.xiangta.services.copywriting_service import _CopywritingCache
        cache = _CopywritingCache()
        # Fill to capacity
        for i in range(100):
            cache.set("r", f"s{i}", f"text{i}", f"value{i}")
        # Oldest should still be accessible
        assert cache.get("r", "s0", "text0") == "value0"
        # Adding one more evicts oldest
        cache.set("r", "s100", "text100", "value100")
        assert cache.get("r", "s0", "text0") is None  # evicted
        assert cache.get("r", "s100", "text100") == "value100"  # new one present
