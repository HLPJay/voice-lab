"""P25M: History load/filter refresh and favorite no-full-refresh checks."""
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


def test_load_letters_refreshes_history_chips_when_screen_is_history():
    body = get_function_body(read_app_js(), "loadLetters")
    assert 'if (state.screen === "history")' in body
    assert "renderHistoryFilterChips();" in body


def test_toggle_history_has_local_star_update_helper_and_used():
    content = read_app_js()
    assert "function updateHistoryFavoriteStarUi(letterId, favorited)" in content
    body = get_function_body(content, "toggleHistoryLetterFavorite")
    assert "updateHistoryFavoriteStarUi(letterId, newValue);" in body


def test_star_click_still_stops_propagation():
    body = get_function_body(read_app_js(), "renderLetters")
    assert "event.stopPropagation();" in body
    assert "toggleHistoryLetterFavorite(letter.id || letter.letterId);" in body


def test_toggle_history_no_unconditional_full_render_on_optimistic_update():
    body = get_function_body(read_app_js(), "toggleHistoryLetterFavorite")
    assert "shouldRenderLettersAfterFavoriteChange(previousValue, newValue)" in body


def test_success_path_avoids_duplicate_full_render_when_values_match():
    body = get_function_body(read_app_js(), "toggleHistoryLetterFavorite")
    assert "authoritativeValue !== newValue" in body


def test_fav_filter_can_trigger_membership_full_render():
    body = get_function_body(read_app_js(), "shouldRenderLettersAfterFavoriteChange")
    assert 'state.historyFilter === "fav"' in body


def test_result_and_letter_detail_sync_lines_remain():
    body = get_function_body(read_app_js(), "toggleHistoryLetterFavorite")
    assert "state.resultFavorited = newValue;" in body
    assert "state.resultSavedLetter.favorited = newValue;" in body
    assert "state.letterDetailFavoritedMap[letterId] = newValue;" in body
    assert "state.activeLetterDetail.favorited = newValue;" in body
