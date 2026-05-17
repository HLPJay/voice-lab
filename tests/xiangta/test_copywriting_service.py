"""
P17-XIANGTA-COPYWRITING-B5-1 — CopywritingService 单元测试

不调用真实 LLM；使用 FakeGateway 确保 gateway 不被调用。
"""
import pytest
from src.xiangta.services.copywriting_service import CopywritingService


class FakeGateway:
    async def generate_llm_text(self, *args, **kwargs):
        raise AssertionError("B5-1 must not call real/fake LLM gateway")


@pytest.fixture
def svc():
    return CopywritingService(gateway=FakeGateway())


# ── 基本结构 ──────────────────────────────────────────────────────────────────

class TestGenerateSuggestionsStructure:

    @pytest.mark.asyncio
    async def test_returns_summary(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        assert "summary" in result
        assert result["summary"]

    @pytest.mark.asyncio
    async def test_returns_intent(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        assert "intent" in result
        assert result["intent"]

    @pytest.mark.asyncio
    async def test_returns_suggestions_list(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)

    @pytest.mark.asyncio
    async def test_exactly_three_suggestions(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        assert len(result["suggestions"]) == 3

    @pytest.mark.asyncio
    async def test_styles_are_restrained_gentle_sincere(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        styles = [s["style"] for s in result["suggestions"]]
        assert styles == ["restrained", "gentle", "sincere"]

    @pytest.mark.asyncio
    async def test_style_labels_present(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        for s in result["suggestions"]:
            assert s["styleLabel"]

    @pytest.mark.asyncio
    async def test_fits_for_present(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        for s in result["suggestions"]:
            assert s["fitsFor"]

    @pytest.mark.asyncio
    async def test_text_non_empty(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        for s in result["suggestions"]:
            assert s["text"]

    @pytest.mark.asyncio
    async def test_char_count_equals_len_text(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        for s in result["suggestions"]:
            assert s["charCount"] == len(s["text"])

    @pytest.mark.asyncio
    async def test_style_labels_are_chinese(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我今天很想你")
        labels = {s["style"]: s["styleLabel"] for s in result["suggestions"]}
        assert labels["restrained"] == "克制版"
        assert labels["gentle"] == "温柔版"
        assert labels["sincere"] == "真诚版"


# ── raw_text 处理 ─────────────────────────────────────────────────────────────

class TestRawTextHandling:

    @pytest.mark.asyncio
    async def test_raw_text_is_stripped(self, svc):
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="  我今天很想你  "
        )
        for s in result["suggestions"]:
            assert "  " not in s["text"].strip()

    @pytest.mark.asyncio
    async def test_empty_raw_text_raises(self, svc):
        with pytest.raises((ValueError, Exception)):
            await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="")

    @pytest.mark.asyncio
    async def test_whitespace_only_raw_text_raises(self, svc):
        with pytest.raises((ValueError, Exception)):
            await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="   ")

    @pytest.mark.asyncio
    async def test_raw_text_included_in_output(self, svc):
        raw = "我今天突然很想你"
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text=raw)
        any_has_raw = any(raw in s["text"] for s in result["suggestions"])
        assert any_has_raw, "至少一条建议应包含原始文本"


# ── 场景差异化 ────────────────────────────────────────────────────────────────

class TestSceneContent:

    @pytest.mark.asyncio
    async def test_miss_scene_contains_relevant_expression(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="miss", raw_text="我想你了")
        all_text = " ".join(
            s["text"] for s in result["suggestions"]
        ) + result["summary"] + result["intent"]
        keywords = ["想念", "在意", "挂念", "想你"]
        assert any(k in all_text for k in keywords), (
            f"miss 场景输出未包含想念相关词。all_text={all_text!r}"
        )

    @pytest.mark.asyncio
    async def test_sorry_scene_contains_relevant_expression(self, svc):
        result = await svc.generate_suggestions(recipient="lover", scene="sorry", raw_text="我做错了")
        all_text = " ".join(
            s["text"] for s in result["suggestions"]
        ) + result["summary"] + result["intent"]
        keywords = ["抱歉", "对不起", "在意"]
        assert any(k in all_text for k in keywords), (
            f"sorry 场景输出未包含道歉相关词。all_text={all_text!r}"
        )

    @pytest.mark.asyncio
    async def test_thanks_scene_output(self, svc):
        result = await svc.generate_suggestions(recipient="friend", scene="thanks", raw_text="你帮了我很多")
        assert len(result["suggestions"]) == 3

    @pytest.mark.asyncio
    async def test_comfort_scene_output(self, svc):
        result = await svc.generate_suggestions(recipient="family", scene="comfort", raw_text="你还好吗")
        assert len(result["suggestions"]) == 3

    @pytest.mark.asyncio
    async def test_night_scene_output(self, svc):
        result = await svc.generate_suggestions(recipient="self", scene="night", raw_text="今天很累")
        assert len(result["suggestions"]) == 3


# ── 不调用 gateway ────────────────────────────────────────────────────────────

class TestNoGatewayCall:

    @pytest.mark.asyncio
    async def test_does_not_call_generate_llm_text(self, svc):
        # FakeGateway.generate_llm_text raises AssertionError if called.
        # If this test passes, gateway was not called.
        result = await svc.generate_suggestions(
            recipient="lover", scene="miss", raw_text="我今天很想你"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_works_without_gateway(self):
        svc_no_gw = CopywritingService(gateway=None)
        result = await svc_no_gw.generate_suggestions(
            recipient="lover", scene="miss", raw_text="我今天很想你"
        )
        assert len(result["suggestions"]) == 3
