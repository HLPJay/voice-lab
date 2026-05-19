"""P25H-FIX3 hotfix: favorite state reset and sync parity checks."""
import os
import re


APP_JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "app.js"
)


def read_app_js():
    with open(APP_JS_PATH, encoding="utf-8") as f:
        return f.read()


def get_function_body(content, name):
    match = re.search(
        r"(?:async\s+)?function\s+" + re.escape(name) + r"\(.*?(?=\n(?:async\s+function|function\s+\w|\Z))",
        content,
        re.DOTALL,
    )
    assert match, f"{name} not found"
    return match.group(0)


def test_renderTtsTask_resets_result_favorite_related_state():
    body = get_function_body(read_app_js(), "renderTtsTask")
    assert "state.resultFavorited = false;" in body
    assert "state.resultSavedLetterId = null;" in body
    assert "state.resultSavedLetter = null;" in body


def test_renderResultMetaPills_uses_saved_and_favorited_guard():
    body = get_function_body(read_app_js(), "renderResultMetaPills")
    assert "if (state.resultSaved && state.resultFavorited)" in body


def test_toggleHistoryLetterFavorite_syncs_result_saved_letter_object():
    body = get_function_body(read_app_js(), "toggleHistoryLetterFavorite")
    assert "if (state.resultSavedLetter) state.resultSavedLetter.favorited = newValue;" in body
    assert "if (state.resultSavedLetter) state.resultSavedLetter.favorited = !newValue;" in body
    assert "if (state.resultSavedLetter) state.resultSavedLetter.favorited = !!response.data.favorited;" in body


def test_toggleHistoryLetterFavorite_syncs_active_letter_detail_object():
    body = get_function_body(read_app_js(), "toggleHistoryLetterFavorite")
    assert "if (state.activeLetterDetail) state.activeLetterDetail.favorited = newValue;" in body
    assert "if (state.activeLetterDetail) state.activeLetterDetail.favorited = !newValue;" in body
    assert "if (state.activeLetterDetail) state.activeLetterDetail.favorited = !!response.data.favorited;" in body
