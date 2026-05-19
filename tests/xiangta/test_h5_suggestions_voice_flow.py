"""
Tests for H5 Suggestions + Voice Flow Prototype Parity (P22O).

Covers:
1. Suggestions screen structure and prototype alignment
2. Voice screen structure and prototype alignment
3. Suggestion card styling matches prototype tokens
4. Voice option checkmark uses SVG
5. Duration estimate uses flex row layout
6. Binding badge uses dark-theme tokens
7. Insight card uses prototype xt-card-elev styling
8. Core API semantics preserved
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestSuggestionsScreenStructure:
    """Suggestions screen HTML structure."""

    def test_screen_suggest_exists(self):
        html = _read(H5_INDEX)
        assert 'id="screenSuggest"' in html

    def test_ai_understanding_card_exists(self):
        html = _read(H5_INDEX)
        assert 'id="aiUnderstanding"' in html

    def test_suggestions_area_exists(self):
        html = _read(H5_INDEX)
        assert 'id="suggestionsArea"' in html

    def test_suggest_risk_hint_exists(self):
        html = _read(H5_INDEX)
        assert 'id="suggestRiskHint"' in html

    def test_btn_to_voice_exists(self):
        html = _read(H5_INDEX)
        assert 'id="btnToVoice"' in html

    def test_suggest_appbar_has_title(self):
        """AppBar context should show '挑一个最像你的版本'."""
        html = _read(H5_INDEX)
        assert "挑一个最像你的版本" in html

    def test_no_separate_step_hero_in_suggest(self):
        """Prototype puts title in AppBar, no separate step-hero for suggest."""
        html = _read(H5_INDEX)
        suggest_start = html.find('id="screenSuggest"')
        suggest_end = html.find('id="screenVoice"')
        suggest_section = html[suggest_start:suggest_end]
        assert "step-hero" not in suggest_section, \
            "Suggestions screen should not have separate step-hero section"


class TestSuggestionsCardStyling:
    """Suggestion card CSS matches prototype tokens."""

    def test_suggestion_card_uses_xt_surface(self):
        css = _read(H5_CSS)
        m = re.search(r'\.suggestion-card\s*\{[^}]+\}', css)
        assert m, "suggestion-card rule not found"
        rule = m.group()
        assert "var(--xt-surface)" in rule, \
            "suggestion-card background should use --xt-surface"

    def test_suggestion_card_selected_uses_xt_surface_2(self):
        css = _read(H5_CSS)
        m = re.search(r'\.suggestion-card\.selected\s*\{[^}]+\}', css)
        assert m, "suggestion-card.selected rule not found"
        rule = m.group()
        assert "var(--xt-surface-2)" in rule, \
            "suggestion-card.selected should use --xt-surface-2"

    def test_suggestion_card_border_radius_18(self):
        css = _read(H5_CSS)
        m = re.search(r'\.suggestion-card\s*\{[^}]+\}', css)
        assert m
        assert "border-radius: 18px" in m.group(), \
            "suggestion-card border-radius should be 18px per prototype"

    def test_suggestion_dot_exists_in_css(self):
        css = _read(H5_CSS)
        assert ".suggestion-dot" in css, \
            "suggestion-dot class should exist for selected indicator"

    def test_small_pill_btn_border_radius_999(self):
        css = _read(H5_CSS)
        matches = re.findall(r'\.small-pill-btn\s*\{[^}]+\}', css)
        found = any("border-radius: 999px" in m for m in matches)
        assert found, \
            "small-pill-btn should have pill border-radius"


class TestSuggestionsFunctionPreservation:
    """Core suggestion functions must be preserved."""

    def test_generate_suggestions_exists(self):
        js = _read(H5_APP)
        assert "function generateSuggestions" in js

    def test_select_suggestion_exists(self):
        js = _read(H5_APP)
        assert "function selectSuggestion" in js

    def test_edit_suggestion_exists(self):
        js = _read(H5_APP)
        assert "function editSuggestion" in js

    def test_copy_suggestion_exists(self):
        js = _read(H5_APP)
        assert "async function copySuggestion" in js

    def test_go_voice_exists(self):
        js = _read(H5_APP)
        assert "function goVoice" in js or "async function goVoice" in js

    def test_render_suggestion_cards_exists(self):
        js = _read(H5_APP)
        assert "function renderSuggestionCards" in js

    def test_suggestions_api_call_preserved(self):
        js = _read(H5_APP)
        assert "/api/xiangta/suggestions" in js

    def test_suggestion_card_staggered_animation(self):
        js = _read(H5_APP)
        assert "spaCardIn" in js, \
            "Suggestion cards should use spaCardIn animation"


class TestVoiceScreenStructure:
    """Voice screen HTML structure."""

    def test_screen_voice_exists(self):
        html = _read(H5_INDEX)
        assert 'id="screenVoice"' in html

    def test_voice_appbar_has_title(self):
        """AppBar should show '给这段话，配一个声音'."""
        html = _read(H5_INDEX)
        assert "给这段话，配一个声音" in html

    def test_no_separate_step_hero_in_voice(self):
        """Prototype puts title in AppBar, no separate step-hero for voice."""
        html = _read(H5_INDEX)
        voice_start = html.find('id="screenVoice"')
        voice_end = html.find('id="screenHistory"')
        voice_section = html[voice_start:voice_end]
        assert "step-hero" not in voice_section, \
            "Voice screen should not have separate step-hero section"


class TestVoiceOptionStyling:
    """Voice option card styling matches prototype."""

    def test_voice_option_check_svg(self):
        """Voice picker uses SVG checkmark instead of text."""
        js = _read(H5_APP)
        assert 'stroke="white"' in js or "stroke-width" in js, \
            "Voice checkmark should use SVG path"

    def test_voice_option_selected_uses_xt_accent_deep(self):
        css = _read(H5_CSS)
        m = re.search(r'\.voice-option\.selected\s*\{[^}]+\}', css)
        assert m, "voice-option.selected rule not found"
        rule = m.group()
        assert "var(--xt-accent-deep)" in rule, \
            "voice-option.selected border should use --xt-accent-deep"

    def test_voice_option_selected_name_uses_accent_ink(self):
        css = _read(H5_CSS)
        assert ".voice-option.selected .voice-option-name" in css, \
            "voice-option.selected .voice-option-name rule should exist"


class TestVoiceBindingBadgeDarkTheme:
    """Binding badges should use dark-theme tokens."""

    def test_bound_badge_uses_ok_soft(self):
        css = _read(H5_CSS)
        m = re.search(r'\.voice-bind-badge\.bound\s*\{[^}]+\}', css)
        assert m
        rule = m.group()
        assert "var(--ok-soft)" in rule, \
            "bound badge should use --ok-soft background"

    def test_unbound_badge_uses_warn_soft(self):
        css = _read(H5_CSS)
        m = re.search(r'\.voice-bind-badge\.unbound\s*\{[^}]+\}', css)
        assert m
        rule = m.group()
        assert "var(--warn-soft)" in rule, \
            "unbound badge should use --warn-soft background"

    def test_invalid_badge_uses_error_soft(self):
        css = _read(H5_CSS)
        m = re.search(r'\.voice-bind-badge\.invalid\s*\{[^}]+\}', css)
        assert m
        rule = m.group()
        assert "var(--error-soft)" in rule, \
            "invalid badge should use --error-soft background"


class TestDurationEstimateLayout:
    """Duration estimate uses flex row layout per prototype."""

    def test_duration_estimate_flex_layout(self):
        css = _read(H5_CSS)
        m = re.search(r'\.duration-estimate\s*\{[^}]+\}', css)
        assert m
        rule = m.group()
        assert "display: flex" in rule, \
            "duration-estimate should use flex layout"
        assert "justify-content: space-between" in rule, \
            "duration-estimate should space-between"

    def test_duration_estimate_label_class_exists(self):
        css = _read(H5_CSS)
        assert ".duration-estimate-label" in css

    def test_duration_estimate_value_class_exists(self):
        css = _read(H5_CSS)
        assert ".duration-estimate-value" in css

    def test_duration_estimate_value_uses_mono_font(self):
        css = _read(H5_CSS)
        m = re.search(r'\.duration-estimate-value\s*\{[^}]+\}', css)
        assert m
        assert "var(--xt-mono)" in m.group(), \
            "duration value should use monospace font"

    def test_render_duration_uses_html(self):
        """renderDurationEstimate should produce structured HTML."""
        js = _read(H5_APP)
        assert "duration-estimate-label" in js, \
            "renderDurationEstimate should output label element"
        assert "duration-estimate-value" in js, \
            "renderDurationEstimate should output value element"


class TestInsightCardPrototypeParity:
    """Insight card uses prototype xt-card-elev styling."""

    def test_insight_card_uses_xt_surface_2(self):
        css = _read(H5_CSS)
        m = re.search(r'\.insight-card\s*\{[^}]+\}', css)
        assert m
        assert "var(--xt-surface-2)" in m.group(), \
            "insight-card should use --xt-surface-2 background"

    def test_insight_card_has_border_radius_20(self):
        css = _read(H5_CSS)
        m = re.search(r'\.insight-card\s*\{[^}]+\}', css)
        assert m
        assert "border-radius: 20px" in m.group(), \
            "insight-card should have 20px border-radius"

    def test_insight_dot_uses_accent_ink(self):
        css = _read(H5_CSS)
        m = re.search(r'\.insight-dot\s*\{[^}]+\}', css)
        assert m
        assert "var(--xt-accent-ink)" in m.group(), \
            "insight-dot should use --xt-accent-ink"


class TestVoiceTextPreview:
    """Voice text preview card matches prototype."""

    def test_edit_button_text(self):
        """Prototype uses '编辑文字' not '返回改字'."""
        js = _read(H5_APP)
        assert "编辑文字" in js, \
            "Voice preview should say '编辑文字' per prototype"

    def test_voice_copy_edit_pill_style(self):
        """Edit button should be pill-styled per prototype."""
        css = _read(H5_CSS)
        m = re.search(r'\.voice-copy-edit\s*\{[^}]+\}', css)
        assert m
        rule = m.group()
        assert "border-radius: 999px" in rule, \
            "voice-copy-edit should have pill border-radius"


class TestTtsPayloadPreservation:
    """TTS API payload must not change."""

    def test_payload_has_text(self):
        js = _read(H5_APP)
        assert "text: text" in js

    def test_payload_has_voice_preset(self):
        js = _read(H5_APP)
        assert "voicePreset: state.selectedVoice" in js

    def test_payload_has_tone(self):
        js = _read(H5_APP)
        assert "tone: state.selectedTone" in js

    def test_payload_has_recipient(self):
        js = _read(H5_APP)
        assert "recipient: state.selectedRecipient" in js

    def test_payload_has_scene(self):
        js = _read(H5_APP)
        assert "scene: state.selectedScene" in js

    def test_no_profile_id_in_formal_payload(self):
        """profileId only added in dev mode."""
        js = _read(H5_APP)
        m = re.search(r'const payload = \{[^}]+\}', js, re.DOTALL)
        assert m
        assert "profileId" not in m.group(), \
            "profileId must not be in base payload"
