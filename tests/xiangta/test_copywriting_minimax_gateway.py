# -*- coding: utf-8 -*-
"""
P18-XIANGTA-MINIMAX-COPYWRITING-ADAPTER-C10D — MiniMax Gateway Tests.
"""
import pytest

from src.xiangta.services.copywriting_gateway import CopywritingRequest
from src.xiangta.services.copywriting_minimax_gateway import (
    MiniMaxCopywritingGateway,
    MiniMaxCopywritingResponseError,
    MiniMaxHttpError,
    parse_minimax_copywriting_response,
)


# ── Fake HTTP client ─────────────────────────────────────────────────────────

class FakeMiniMaxHttpClient:
    def __init__(self, response=None, error=None):
        self._response = response or {}
        self._error = error
        self.call_count = 0
        self.last_call = None

    async def create_chat_completion(
        self, *, base_url, api_key, model, messages, timeout_seconds
    ):
        self.call_count += 1
        self.last_call = {
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "messages": messages,
            "timeout_seconds": timeout_seconds,
        }
        if self._error:
            raise self._error
        return self._response


# ── Helpers ────────────────────────────────────────────────────────────────

def make_payload(content_str):
    return {"choices": [{"message": {"content": content_str}}]}


def valid_response(content=None):
    if content is None:
        content = VALID_JSON
    return make_payload(content)


VALID_JSON = """```json
{
  "summary": "AI summary",
  "intent": "AI intent",
  "suggestions": [
    {"style": "restrained", "styleLabel": "r1", "fitsFor": "f1", "text": "a"},
    {"style": "gentle", "styleLabel": "g1", "fitsFor": "f2", "text": "b"},
    {"style": "sincere", "styleLabel": "s1", "fitsFor": "f3", "text": "c"}
  ]
}
```"""


# ── Parse tests ────────────────────────────────────────────────────────────

class TestParseResponse:

    def test_valid_response_parses(self):
        result = parse_minimax_copywriting_response(valid_response())
        assert result.summary == "AI summary"
        assert result.intent == "AI intent"
        assert len(result.suggestions) == 3
        assert result.source == "minimax"

    def test_fenced_json_parsed(self):
        payload = make_payload(VALID_JSON)
        result = parse_minimax_copywriting_response(payload)
        assert len(result.suggestions) == 3

    def test_plain_json_no_fence(self):
        payload = make_payload('{"summary":"s","intent":"i","suggestions":[{"style":"restrained","styleLabel":"r","fitsFor":"f","text":"a"},{"style":"gentle","styleLabel":"g","fitsFor":"f","text":"b"},{"style":"sincere","styleLabel":"s","fitsFor":"f","text":"c"}]}')
        result = parse_minimax_copywriting_response(payload)
        assert len(result.suggestions) == 3
        assert result.suggestions[0].style == "restrained"

    def test_whitespace_stripped(self):
        payload = make_payload("  " + VALID_JSON + "  ")
        result = parse_minimax_copywriting_response(payload)
        assert len(result.suggestions) == 3

    def test_reply_field_extraction(self):
        payload = {"reply": VALID_JSON}
        result = parse_minimax_copywriting_response(payload)
        assert len(result.suggestions) == 3

    def test_content_field_extraction(self):
        payload = {"content": VALID_JSON}
        result = parse_minimax_copywriting_response(payload)
        assert len(result.suggestions) == 3

    def test_data_choices_extraction(self):
        payload = {"data": {"choices": [{"message": {"content": VALID_JSON}}]}}
        result = parse_minimax_copywriting_response(payload)
        assert len(result.suggestions) == 3

    def test_wrong_styles_rejected(self):
        # 3 suggestions but one has invalid style
        bad = '{"summary":"s","intent":"i","suggestions":[{"style":"restrained","styleLabel":"r","fitsFor":"f","text":"a"},{"style":"WRONGSTYLE","styleLabel":"g","fitsFor":"f","text":"b"},{"style":"sincere","styleLabel":"s","fitsFor":"f","text":"c"}]}'
        with pytest.raises(MiniMaxCopywritingResponseError, match="invalid style"):
            parse_minimax_copywriting_response(make_payload(bad))

    def test_fewer_than_3_suggestions_rejected(self):
        bad = '{"summary":"s","intent":"i","suggestions":[{"style":"restrained","styleLabel":"r","fitsFor":"f","text":"hi"}]}'
        with pytest.raises(MiniMaxCopywritingResponseError, match="exactly 3 suggestions"):
            parse_minimax_copywriting_response(make_payload(bad))

    def test_more_than_3_suggestions_rejected(self):
        bad = '{"summary":"s","intent":"i","suggestions":[{"style":"restrained","styleLabel":"r","fitsFor":"f","text":"a"},{"style":"gentle","styleLabel":"g","fitsFor":"f","text":"b"},{"style":"sincere","styleLabel":"s","fitsFor":"f","text":"c"},{"style":"restrained","styleLabel":"r","fitsFor":"f","text":"d"}]}'
        with pytest.raises(MiniMaxCopywritingResponseError, match="exactly 3 suggestions"):
            parse_minimax_copywriting_response(make_payload(bad))

    def test_empty_text_rejected(self):
        bad = '{"summary":"s","intent":"i","suggestions":[{"style":"restrained","styleLabel":"r","fitsFor":"f","text":""}]}'
        with pytest.raises(MiniMaxCopywritingResponseError, match="empty text"):
            parse_minimax_copywriting_response(make_payload(bad))

    def test_empty_fits_for_rejected(self):
        bad = '{"summary":"s","intent":"i","suggestions":[{"style":"restrained","styleLabel":"r","fitsFor":"","text":"hi"}]}'
        with pytest.raises(MiniMaxCopywritingResponseError, match="empty fitsFor"):
            parse_minimax_copywriting_response(make_payload(bad))

    def test_forbidden_field_in_output_rejected(self):
        bad = '{"summary":"test apiKey secret","intent":"i","suggestions":[{"style":"restrained","styleLabel":"r","fitsFor":"f","text":"a"},{"style":"gentle","styleLabel":"g","fitsFor":"f","text":"b"},{"style":"sincere","styleLabel":"s","fitsFor":"f","text":"c"}]}'
        with pytest.raises(MiniMaxCopywritingResponseError, match="forbidden field"):
            parse_minimax_copywriting_response(make_payload(bad))


# ── Gateway tests ─────────────────────────────────────────────────────────

class TestMiniMaxGateway:

    def _req(self, **kw):
        d = dict(recipient="lover", scene="miss", raw_text="很想你")
        d.update(kw)
        return CopywritingRequest(**d)

    def test_reuses_prompt_contract(self):
        client = FakeMiniMaxHttpClient(valid_response())
        gw = MiniMaxCopywritingGateway(
            api_key="fake-key",
            base_url="https://api.minimax.chat",
            model="MiniMax-Text-01",
            timeout_seconds=20,
            _http_client=client,
        )
        import asyncio
        asyncio.run(gw.generate(self._req()))
        assert client.call_count == 1
        call = client.last_call
        assert call["base_url"] == "https://api.minimax.chat"
        assert call["model"] == "MiniMax-Text-01"
        assert call["timeout_seconds"] == 20
        user_msg = next(m["content"] for m in call["messages"] if m["role"] == "user")
        assert "lover" in user_msg
        assert "miss" in user_msg

    def test_http_client_injected(self):
        client = FakeMiniMaxHttpClient(valid_response())
        gw = MiniMaxCopywritingGateway(
            api_key="k", base_url="u", model="m", _http_client=client
        )
        import asyncio
        asyncio.run(gw.generate(self._req()))
        assert client.call_count == 1

    def test_network_error_raises_http_error(self):
        client = FakeMiniMaxHttpClient(error=MiniMaxHttpError("Connection refused"))
        gw = MiniMaxCopywritingGateway(
            api_key="k", base_url="u", model="m", _http_client=client
        )
        import asyncio
        with pytest.raises(MiniMaxHttpError):
            asyncio.run(gw.generate(self._req()))

    def test_invalid_response_raises_parse_error(self):
        client = FakeMiniMaxHttpClient(make_payload("not json at all"))
        gw = MiniMaxCopywritingGateway(
            api_key="k", base_url="u", model="m", _http_client=client
        )
        import asyncio
        with pytest.raises(MiniMaxCopywritingResponseError):
            asyncio.run(gw.generate(self._req()))

    def test_valid_response_returns_copywriting_result(self):
        client = FakeMiniMaxHttpClient(valid_response())
        gw = MiniMaxCopywritingGateway(
            api_key="k", base_url="u", model="m", _http_client=client
        )
        import asyncio
        result = asyncio.run(gw.generate(self._req()))
        assert len(result.suggestions) == 3
        styles = {s.style for s in result.suggestions}
        assert styles == {"restrained", "gentle", "sincere"}
