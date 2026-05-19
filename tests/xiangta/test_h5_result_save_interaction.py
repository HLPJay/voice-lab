"""
Hotfix tests for Result save flow (P22Q).

Required behavior:
1. resultSave calls showResultSaveSealThenOpenDetail(savedLetter)
2. resultSave no longer uses showResultSavedMoment as post-save path
3. duplicate save guard remains
4. save API endpoint remains /api/xiangta/letters
5. busy text uses product wording (正在收好...)
"""

H5_APP = "apps/xiangta-h5/app.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _result_save_body(js: str) -> str:
    start = js.find("async function resultSave")
    assert start >= 0, "resultSave function not found"
    return js[start:start + 2200]


class TestResultSaveHotfix:
    def test_result_save_function_exists(self):
        js = _read(H5_APP)
        assert "async function resultSave" in js

    def test_duplicate_save_guard_preserved(self):
        js = _read(H5_APP)
        body = _result_save_body(js)
        assert "if (state.resultSaved) return;" in body

    def test_save_api_endpoint_preserved(self):
        js = _read(H5_APP)
        body = _result_save_body(js)
        assert 'apiFetch("/api/xiangta/letters"' in body

    def test_busy_label_uses_product_wording(self):
        js = _read(H5_APP)
        body = _result_save_body(js)
        assert 'setBusy("btnResultSave", true, "正在收好...")' in body

    def test_failure_restores_save_label(self):
        js = _read(H5_APP)
        body = _result_save_body(js)
        assert 'setBusy("btnResultSave", false, "保存到信笺夹")' in body

    def test_success_calls_seal_then_open_detail(self):
        js = _read(H5_APP)
        body = _result_save_body(js)
        assert "showResultSaveSealThenOpenDetail(savedLetter);" in body

    def test_success_no_longer_uses_saved_moment_navigation_path(self):
        js = _read(H5_APP)
        body = _result_save_body(js)
        assert "showResultSavedMoment();" not in body
