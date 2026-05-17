"""
P17-XIANGTA-LETTERS-B6-1 — LetterService 单元测试
"""
import pytest
from src.xiangta.services.letter_service import LetterService, clear_letters_for_tests

_SAMPLE = {
    "recipient": "lover",
    "scene": "miss",
    "style": "gentle",
    "rawText": "我今天突然很想你",
    "finalText": "有些挂念你，我今天突然很想你，悄悄想了一会儿。",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "audioUrl": "/api/voice/assets/audio_123/download",
    "durationSecs": 2.4,
    "title": "想你了",
}


@pytest.fixture(autouse=True)
def clean_store():
    clear_letters_for_tests()
    yield
    clear_letters_for_tests()


@pytest.fixture
def svc():
    return LetterService()


# ── create ────────────────────────────────────────────────────────────────────

class TestCreate:

    @pytest.mark.asyncio
    async def test_returns_letter_id(self, svc):
        result = await svc.create(_SAMPLE)
        assert "letterId" in result
        assert result["letterId"].startswith("L_")

    @pytest.mark.asyncio
    async def test_returns_created_at(self, svc):
        result = await svc.create(_SAMPLE)
        assert "createdAt" in result
        assert "T" in result["createdAt"]

    @pytest.mark.asyncio
    async def test_unique_letter_ids(self, svc):
        r1 = await svc.create(_SAMPLE)
        r2 = await svc.create(_SAMPLE)
        assert r1["letterId"] != r2["letterId"]

    @pytest.mark.asyncio
    async def test_record_persists(self, svc):
        await svc.create(_SAMPLE)
        result = await svc.list()
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_record_has_favorited_false(self, svc):
        await svc.create(_SAMPLE)
        result = await svc.list()
        assert result["letters"][0]["favorited"] is False

    @pytest.mark.asyncio
    async def test_record_has_open_count_zero(self, svc):
        await svc.create(_SAMPLE)
        result = await svc.list()
        assert result["letters"][0]["openCount"] == 0

    @pytest.mark.asyncio
    async def test_record_has_opened_at_null(self, svc):
        await svc.create(_SAMPLE)
        result = await svc.list()
        assert result["letters"][0]["openedAt"] is None

    @pytest.mark.asyncio
    async def test_record_stores_recipient(self, svc):
        await svc.create(_SAMPLE)
        result = await svc.list()
        assert result["letters"][0]["recipient"] == "lover"

    @pytest.mark.asyncio
    async def test_record_stores_final_text(self, svc):
        await svc.create(_SAMPLE)
        result = await svc.list()
        assert "挂念" in result["letters"][0]["finalText"]

    @pytest.mark.asyncio
    async def test_audio_url_optional(self, svc):
        data = {**_SAMPLE, "audioUrl": None}
        result = await svc.create(data)
        assert result["letterId"]

    @pytest.mark.asyncio
    async def test_duration_secs_optional(self, svc):
        data = {**_SAMPLE, "durationSecs": None}
        result = await svc.create(data)
        assert result["letterId"]

    @pytest.mark.asyncio
    async def test_title_optional(self, svc):
        data = {**_SAMPLE, "title": None}
        result = await svc.create(data)
        assert result["letterId"]


# ── list ─────────────────────────────────────────────────────────────────────

class TestList:

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self, svc):
        result = await svc.list()
        assert result["letters"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_total_reflects_all_records(self, svc):
        await svc.create(_SAMPLE)
        await svc.create(_SAMPLE)
        result = await svc.list()
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_newest_first(self, svc):
        data_a = {**_SAMPLE, "title": "第一条"}
        data_b = {**_SAMPLE, "title": "第二条"}
        r1 = await svc.create(data_a)
        r2 = await svc.create(data_b)
        result = await svc.list()
        # 最新在前：第二条应排第一
        assert result["letters"][0]["letterId"] == r2["letterId"]
        assert result["letters"][1]["letterId"] == r1["letterId"]

    @pytest.mark.asyncio
    async def test_limit_applied(self, svc):
        for _ in range(5):
            await svc.create(_SAMPLE)
        result = await svc.list(limit=3)
        assert len(result["letters"]) == 3
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_offset_applied(self, svc):
        ids = []
        for i in range(4):
            r = await svc.create({**_SAMPLE, "title": f"第{i}条"})
            ids.append(r["letterId"])
        result = await svc.list(limit=2, offset=2)
        assert len(result["letters"]) == 2

    @pytest.mark.asyncio
    async def test_returns_limit_in_response(self, svc):
        result = await svc.list(limit=10)
        assert result["limit"] == 10

    @pytest.mark.asyncio
    async def test_returns_offset_in_response(self, svc):
        result = await svc.list(offset=5)
        assert result["offset"] == 5

    @pytest.mark.asyncio
    async def test_limit_clamps_to_max_100(self, svc):
        result = await svc.list(limit=999)
        assert result["limit"] == 100

    @pytest.mark.asyncio
    async def test_limit_clamps_to_min_1(self, svc):
        result = await svc.list(limit=0)
        assert result["limit"] == 1

    @pytest.mark.asyncio
    async def test_offset_clamps_to_min_0(self, svc):
        result = await svc.list(offset=-5)
        assert result["offset"] == 0

    @pytest.mark.asyncio
    async def test_two_service_instances_share_store(self):
        svc_a = LetterService()
        svc_b = LetterService()
        await svc_a.create(_SAMPLE)
        result = await svc_b.list()
        assert result["total"] == 1


# ── clear ─────────────────────────────────────────────────────────────────────

class TestClear:

    @pytest.mark.asyncio
    async def test_clear_empties_store(self, svc):
        await svc.create(_SAMPLE)
        svc.clear()
        result = await svc.list()
        assert result["total"] == 0
