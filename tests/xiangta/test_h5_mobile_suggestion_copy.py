import os
import re


ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
APP_JS_PATH = os.path.join(ROOT, "apps", "xiangta-h5", "app.js")
CSS_PATH = os.path.join(ROOT, "apps", "xiangta-h5", "css", "screens-suggestions-voice.css")


def read(path):
    with open(path, encoding="utf-8") as f:
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
    body = get_function_body(read(APP_JS_PATH), "renderSuggestionCards")
    assert "event.preventDefault();" in body
    assert "event.stopPropagation();" in body
    assert "copySuggestion(index, event, copyBtn);" in body


def test_copy_suggestion_keeps_clipboard_api_path():
    body = get_function_body(read(APP_JS_PATH), "copySuggestion")
    assert "navigator.clipboard?.writeText" in body


def test_copy_suggestion_mobile_fallback_is_strengthened():
    body = get_function_body(read(APP_JS_PATH), "copySuggestion")
    assert "area.focus();" in body
    assert "area.select();" in body
    assert "setSelectionRange" in body
    assert "area.setSelectionRange(0, area.value.length);" in body


def test_copy_suggestion_fallback_cleanup_is_guaranteed():
    body = get_function_body(read(APP_JS_PATH), "copySuggestion")
    assert "finally" in body
    assert "area.parentNode.removeChild(area);" in body


def test_copy_failure_feedback_is_clear():
    body = get_function_body(read(APP_JS_PATH), "copySuggestion")
    assert "复制失败，请长按文字手动复制" in body


def test_copy_success_is_button_local_feedback():
    body = get_function_body(read(APP_JS_PATH), "copySuggestion")
    assert "markSuggestionCopyButtonCopied(button);" in body
    helper = get_function_body(read(APP_JS_PATH), "markSuggestionCopyButtonCopied")
    assert 'button.textContent = "已复制";' in helper
    assert 'button.classList.add("copied");' in helper
    assert "setTimeout" in helper
    assert 'button.textContent = button.dataset.copyOriginalText || "复制";' in helper


def test_copy_path_does_not_rerender_or_reselect():
    body = get_function_body(read(APP_JS_PATH), "copySuggestion")
    assert "renderSuggestionCards(" not in body
    assert "selectSuggestion(" not in body


def test_css_tap_feedback_and_transition_are_mobile_safe():
    css = read(CSS_PATH)
    assert ".suggestion-card," in css
    assert "-webkit-tap-highlight-color: transparent;" in css
    assert "touch-action: manipulation;" in css
    assert "transition: all 0.18s ease;" not in css


def test_suggestion_card_click_still_selects():
    body = get_function_body(read(APP_JS_PATH), "renderSuggestionCards")
    assert 'card.addEventListener("click", () => selectSuggestion(index));' in body
