import os
import re


ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
INDEX_HTML_PATH = os.path.join(ROOT, "apps", "xiangta-h5", "index.html")
LAYOUT_CSS_PATH = os.path.join(ROOT, "apps", "xiangta-h5", "css", "layout.css")
APP_JS_PATH = os.path.join(ROOT, "apps", "xiangta-h5", "app.js")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_step_screen_structure_exists_for_compose_suggest_voice():
    html = read(INDEX_HTML_PATH)
    ordered_ids = ("screenCompose", "screenSuggest", "screenVoice", "screenHistory")
    for i, screen_id in enumerate(ordered_ids[:-1]):
        start = html.find(f'<section id="{screen_id}" class="screen">')
        assert start >= 0, f"{screen_id} missing"
        end = html.find(f'<section id="{ordered_ids[i + 1]}" class="screen">', start + 1)
        assert end > start, f"{screen_id} boundary missing"
        section = html[start:end]
        assert 'class="step-screen"' in section
        assert 'class="step-screen-header"' in section
        assert 'class="step-screen-content"' in section
        assert 'class="step-screen-cta"' in section


def test_business_ids_preserved():
    html = read(INDEX_HTML_PATH)
    required_ids = [
        "rawTextArea",
        "rawTextCount",
        "fillExampleLink",
        "guidancePrompts",
        "riskHint",
        "btnGenSuggestions",
        "aiUnderstanding",
        "suggestRiskHint",
        "suggestionsArea",
        "finalTextArea",
        "btnToVoice",
        "voicePicker",
        "toneChips",
        "ttsResult",
        "saveLetterSection",
        "btnGenTtsTask",
    ]
    for item_id in required_ids:
        assert f'id="{item_id}"' in html


def test_step_layout_css_rules_exist():
    css = read(LAYOUT_CSS_PATH)
    assert ".step-screen {" in css
    assert "height: 100%;" in css
    assert "display: flex;" in css
    assert "flex-direction: column;" in css
    assert "overflow: hidden;" in css
    assert ".step-screen-content {" in css
    assert "min-height: 0;" in css
    assert "overflow-y: auto;" in css
    assert ".step-screen-cta {" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "var(--xt-kb, 0px)" in css


def test_visual_viewport_keyboard_var_logic_exists():
    app_js = read(APP_JS_PATH)
    assert "function initKeyboardSafeInset()" in app_js
    assert "window.visualViewport" in app_js
    assert 'setProperty("--xt-kb"' in app_js
    assert "Math.max(0" in app_js


def test_payloads_unchanged():
    app_js = read(APP_JS_PATH)
    assert 'recipient: state.selectedRecipient' in app_js
    assert 'scene: state.selectedScene' in app_js
    assert "rawText: rawText" in app_js
    assert "voicePreset: state.selectedVoice" in app_js
    assert "tone: state.selectedTone" in app_js
