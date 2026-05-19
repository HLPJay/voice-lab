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


def test_copy_click_handler_prevents_default_and_stops_propagation():
    body = get_function_body(read_app_js(), "renderSuggestionCards")
    assert "event.preventDefault();" in body
    assert "event.stopPropagation();" in body
    assert "copySuggestion(index, event);" in body


def test_copy_suggestion_keeps_clipboard_api_path():
    body = get_function_body(read_app_js(), "copySuggestion")
    assert "navigator.clipboard?.writeText" in body


def test_copy_suggestion_mobile_fallback_is_strengthened():
    body = get_function_body(read_app_js(), "copySuggestion")
    assert "area.focus();" in body
    assert "area.select();" in body
    assert "setSelectionRange" in body
    assert 'area.setSelectionRange(0, area.value.length);' in body


def test_copy_suggestion_fallback_cleanup_is_guaranteed():
    body = get_function_body(read_app_js(), "copySuggestion")
    assert "finally" in body
    assert "area.parentNode.removeChild(area);" in body


def test_copy_failure_feedback_is_clear():
    body = get_function_body(read_app_js(), "copySuggestion")
    assert "复制失败，请长按文字手动复制" in body


def test_suggestion_card_click_still_selects():
    body = get_function_body(read_app_js(), "renderSuggestionCards")
    assert 'card.addEventListener("click", () => selectSuggestion(index));' in body
