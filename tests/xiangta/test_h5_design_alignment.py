"""
P18-XIANGTA-H5-PROTOTYPE-PORT-C10A-FIX1 — Design Alignment Tests

验证 H5 前端与原型设计结构对齐：phone-shell、topbar、
recipient cards with icons、scene chips with hints、
warm gold CTA、literary greeting、status pill。
"""
from pathlib import Path

_H5_DIR = Path(__file__).parent.parent.parent / "apps" / "xiangta-h5"


class TestPhoneShell:

    def _html(self):
        return (_H5_DIR / "index.html").read_text(encoding="utf-8")

    def test_phone_shell_container(self):
        assert "phone-shell" in self._html()

    def test_app_topbar_exists(self):
        assert "app-topbar" in self._html()

    def test_topbar_has_letter_seal(self):
        assert "letter-seal" in self._html()

    def test_topbar_has_brand_title(self):
        assert "topbar-title" in self._html()


class TestRecipientCards:

    def _js(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def _css(self):
        return (_H5_DIR / "styles.css").read_text(encoding="utf-8")

    def test_recipient_meta_map_exists(self):
        assert "RECIPIENT_META" in self._js()

    def test_recipient_card_class_in_css(self):
        assert ".recipient-card" in self._css()

    def test_recipient_card_icon_class(self):
        assert "recipient-card-icon" in self._js()

    def test_recipient_card_hint_class(self):
        assert "recipient-card-hint" in self._js()

    def test_recipient_meta_has_lover(self):
        src = self._js()
        assert "lover:" in src or '"lover"' in src or "'lover'" in src

    def test_recipient_meta_has_svg_icon(self):
        src = self._js()
        assert "icon:" in src and "<svg" in src


class TestSceneChips:

    def _js(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def _css(self):
        return (_H5_DIR / "styles.css").read_text(encoding="utf-8")

    def test_scene_meta_map_exists(self):
        assert "SCENE_META" in self._js()

    def test_scene_chip_class_in_css(self):
        assert ".scene-chip" in self._css()

    def test_scene_chip_label_class(self):
        assert "scene-chip-label" in self._js()

    def test_scene_chip_hint_class(self):
        assert "scene-chip-hint" in self._js()


class TestWarmGoldCta:

    def _css(self):
        return (_H5_DIR / "styles.css").read_text(encoding="utf-8")

    def _html(self):
        return (_H5_DIR / "index.html").read_text(encoding="utf-8")

    def test_cta_color_token_exists(self):
        assert "--c-cta" in self._css()

    def test_btn_cta_class_in_css(self):
        assert ".btn-cta" in self._css()

    def test_btn_cta_used_in_html(self):
        assert "btn-cta" in self._html()


class TestLiteraryGreeting:

    def _js(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def _html(self):
        return (_H5_DIR / "index.html").read_text(encoding="utf-8")

    def test_literary_greeting_element(self):
        assert "literaryGreeting" in self._html()

    def test_render_literary_greeting_function(self):
        assert "renderLiteraryGreeting" in self._js()

    def test_greeting_has_time_period(self):
        src = self._js()
        for period in ("清晨", "上午", "下午", "傍晚", "晚上", "深夜"):
            if period in src:
                return
        raise AssertionError("renderLiteraryGreeting missing time period labels")


class TestStatusPill:

    def _js(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def _html(self):
        return (_H5_DIR / "index.html").read_text(encoding="utf-8")

    def _css(self):
        return (_H5_DIR / "styles.css").read_text(encoding="utf-8")

    def test_status_pill_element(self):
        assert "statusPill" in self._html()

    def test_status_pill_bar_in_css(self):
        assert ".status-pill-bar" in self._css()

    def test_render_status_pill_function(self):
        assert "renderStatusPill" in self._js()

    def test_status_note_text(self):
        assert "本机保存" in self._html()


class TestDesignTokens:

    def _css(self):
        return (_H5_DIR / "styles.css").read_text(encoding="utf-8")

    def test_serif_font_token(self):
        assert "--font-serif" in self._css()

    def test_sans_font_token(self):
        assert "--font-sans" in self._css()

    def test_surface2_token(self):
        assert "--c-surface2" in self._css()

    def test_accent_ink_token(self):
        assert "--c-accent-ink" in self._css()


class TestComposeExampleStarter:

    def _js(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def _html(self):
        return (_H5_DIR / "index.html").read_text(encoding="utf-8")

    def test_fill_example_link_in_html(self):
        assert 'id="fillExampleLink"' in self._html()

    def test_fill_scene_example_function_exists(self):
        assert "function fillSceneExample" in self._js()

    def test_fill_scene_example_uses_raw_examples(self):
        src = self._js()
        start = src.find("function fillSceneExample")
        end = src.find("\n}", start)
        section = src[start:end]
        assert "RAW_EXAMPLES" in section

    def test_fill_scene_example_calls_update_compose_state(self):
        src = self._js()
        start = src.find("function fillSceneExample")
        end = src.find("\n}", start)
        section = src[start:end]
        assert "updateComposeState" in section

    def test_fill_example_link_bound_in_init_compose_listeners(self):
        src = self._js()
        start = src.find("function initComposeListeners")
        end = src.find("\n}", start)
        section = src[start:end]
        assert "fillExampleLink" in section
        assert "addEventListener" in section


class TestSuggestParity:

    def _js(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def _html(self):
        return (_H5_DIR / "index.html").read_text(encoding="utf-8")

    def _css(self):
        return (_H5_DIR / "styles.css").read_text(encoding="utf-8")

    def test_suggest_screen_has_understanding_and_cards(self):
        html = self._html()
        assert 'id="aiUnderstanding"' in html
        assert 'id="suggestionsArea"' in html
        assert 'id="btnToVoice"' in html

    def test_edit_and_copy_actions_exist_in_js(self):
        js = self._js()
        assert "function copySuggestion" in js
        assert "function editSuggestion" in js
        assert 'data-action="edit"' in js
        assert 'data-action="copy"' in js

    def test_suggestion_card_visual_tokens_exist(self):
        css = self._css()
        for token in [".small-pill-btn", ".suggestion-action-left", ".insight-dot", ".suggestion-card.selected"]:
            assert token in css
