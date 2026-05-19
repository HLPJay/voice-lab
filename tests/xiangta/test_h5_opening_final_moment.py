"""
Tests for opening overlay + result save seal/detail transition.
"""

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fn_body(js: str, fn_name: str, window: int = 2600) -> str:
    start = js.find(f"function {fn_name}")
    assert start >= 0, f"{fn_name} not found"
    return js[start:start + window]


class TestOpeningOverlayStillPresent:
    def test_opening_overlay_dom_still_exists(self):
        html = _read(H5_INDEX)
        assert 'id="openingOverlay"' in html

    def test_result_save_seal_overlay_dom_still_exists(self):
        html = _read(H5_INDEX)
        assert 'id="resultSaveSealOverlay"' in html


class TestSealThenDetailFlow:
    def test_seal_then_open_detail_function_exists(self):
        js = _read(H5_APP)
        assert "function showResultSaveSealThenOpenDetail(letter)" in js

    def test_seal_then_open_detail_calls_letter_detail(self):
        js = _read(H5_APP)
        body = _fn_body(js, "showResultSaveSealThenOpenDetail")
        assert 'showScreen("letterDetail")' in body

    def test_sets_active_letter_before_opening_detail(self):
        js = _read(H5_APP)
        body = _fn_body(js, "showResultSaveSealThenOpenDetail")
        id_idx = body.find("state.activeLetterDetailId")
        obj_idx = body.find("state.activeLetterDetail = letter")
        screen_idx = body.find('showScreen("letterDetail")')
        assert id_idx >= 0 and obj_idx >= 0 and screen_idx >= 0
        assert id_idx < screen_idx
        assert obj_idx < screen_idx

    def test_result_saved_moment_function_still_exists(self):
        js = _read(H5_APP)
        assert "function showResultSavedMoment()" in js
