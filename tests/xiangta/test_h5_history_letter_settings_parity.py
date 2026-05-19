"""
Tests for H5 History / LetterDetail / Settings prototype parity (P22R).

Covers:
1. screenHistory exists
2. screenLetterDetail exists
3. screenSettings exists
4. History large-title header exists (.history-screen-title)
5. History search button exists
6. History filter chips container exists
7. History empty state exists with correct text
8. History mini player exists
9. Letter detail paper card exists
10. Letter detail meta pills container exists
11. Letter detail action buttons exist (复制 / 分享 / 换个语气 / 重新编辑)
12. Settings large-title header exists
13. Settings xt-section-h section headers exist in JS
14. Settings "云同步" section exists in JS
15. Settings "本地数据" section exists in JS
16. Admin voice binding entry preserved
17. Sensitive fields not in JS output (api_key / admin token / coreProfileId / provider_voice_id / binding_id)
18. Result save behavior not broken
19. History favorites filter chip exists in JS
20. Opening overlay preserved
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestScreensExist:
    """All three screens must exist in HTML."""

    def test_screen_history_exists(self):
        html = _read(H5_INDEX)
        assert 'id="screenHistory"' in html

    def test_screen_letter_detail_exists(self):
        html = _read(H5_INDEX)
        assert 'id="screenLetterDetail"' in html

    def test_screen_settings_exists(self):
        html = _read(H5_INDEX)
        assert 'id="screenSettings"' in html


class TestHistoryScreenStructure:
    """History screen prototype-aligned header and elements."""

    def test_history_large_title_css_exists(self):
        css = _read(H5_CSS)
        assert ".history-screen-title" in css, \
            "history-screen-title CSS class must exist for large serif header"

    def test_history_screen_header_in_html(self):
        html = _read(H5_INDEX)
        assert "history-screen-header" in html, \
            "history-screen-header class must be in HTML"

    def test_history_screen_title_font_size(self):
        css = _read(H5_CSS)
        m = re.search(r'\.history-screen-title\s*\{[^}]+\}', css)
        assert m
        assert "26px" in m.group(), \
            "history-screen-title must use 26px font-size per prototype"

    def test_history_count_element_exists(self):
        html = _read(H5_INDEX)
        assert 'id="historyCount"' in html

    def test_history_search_btn_exists(self):
        html = _read(H5_INDEX)
        assert 'id="btnHistorySearch"' in html

    def test_history_filter_chips_exists(self):
        html = _read(H5_INDEX)
        assert 'id="historyFilterChips"' in html

    def test_history_filter_chips_all_in_js(self):
        js = _read(H5_APP)
        for label in ["全部", "恋人", "父母", "朋友", "自己", "收藏"]:
            assert label in js, f"History filter chip '{label}' must be in JS"

    def test_history_empty_state_text(self):
        js = _read(H5_APP)
        assert "还没有写过一封信" in js

    def test_history_empty_cta_text(self):
        js = _read(H5_APP)
        assert "写第一封" in js

    def test_history_mini_player_exists(self):
        html = _read(H5_INDEX)
        assert 'id="historyMiniPlayer"' in html

    def test_history_mini_player_frosted_glass(self):
        css = _read(H5_CSS)
        m = re.search(r'\.history-mini-player\s*\{[^}]+\}', css)
        assert m
        assert "backdrop-filter" in m.group(), \
            "mini player should use backdrop-filter for frosted glass"


class TestLetterDetailStructure:
    """Letter detail screen structure."""

    def test_letter_detail_paper_card_exists(self):
        html = _read(H5_INDEX)
        assert 'id="letterDetailCard"' in html

    def test_letter_detail_meta_pills_exists(self):
        html = _read(H5_INDEX)
        assert 'id="letterDetailMetaPills"' in html

    def test_letter_detail_body_exists(self):
        html = _read(H5_INDEX)
        assert 'id="letterDetailBody"' in html

    def test_letter_detail_signature_exists(self):
        html = _read(H5_INDEX)
        assert 'id="letterDetailSignature"' in html

    def test_letter_detail_action_copy(self):
        html = _read(H5_INDEX)
        assert "copyLetterDetailText" in html

    def test_letter_detail_action_share(self):
        html = _read(H5_INDEX)
        assert "shareLetterDetail" in html

    def test_letter_detail_action_retone(self):
        html = _read(H5_INDEX)
        assert "retoneLetterDetail" in html

    def test_letter_detail_action_recompose_label(self):
        """Button label should be 重新编辑 per prototype."""
        html = _read(H5_INDEX)
        assert "重新编辑" in html, \
            "LetterDetail action grid should show '重新编辑' per prototype"

    def test_letter_detail_favorite_btn_exists(self):
        html = _read(H5_INDEX)
        assert 'id="btnLetterDetailFavorite"' in html

    def test_letter_detail_paper_card_css_lines(self):
        css = _read(H5_CSS)
        assert "repeating-linear-gradient" in css, \
            "Letter detail paper card should have ruled line guide via repeating-linear-gradient"


class TestSettingsScreenStructure:
    """Settings screen prototype-aligned structure."""

    def test_settings_large_title_css_exists(self):
        css = _read(H5_CSS)
        assert ".settings-screen-title" in css

    def test_settings_screen_title_font_size(self):
        css = _read(H5_CSS)
        m = re.search(r'\.settings-screen-title\s*\{[^}]+\}', css)
        assert m
        assert "26px" in m.group()

    def test_settings_screen_header_in_html(self):
        html = _read(H5_INDEX)
        assert "settings-screen-header" in html

    def test_settings_本机状态_in_html(self):
        html = _read(H5_INDEX)
        assert "本机状态" in html

    def test_settings_section_header_服务连接_in_js(self):
        js = _read(H5_APP)
        assert "服务连接" in js

    def test_settings_section_header_声线绑定_in_js(self):
        js = _read(H5_APP)
        assert "声线绑定" in js

    def test_settings_云同步_section_in_js(self):
        js = _read(H5_APP)
        assert "云同步" in js, \
            "Settings must include '云同步·即将开放' section per prototype"

    def test_settings_本地数据_section_in_js(self):
        js = _read(H5_APP)
        assert "本地数据" in js

    def test_settings_version_footer_in_js(self):
        js = _read(H5_APP)
        assert "settings-version" in js

    def test_settings_quota_bar_in_js(self):
        js = _read(H5_APP)
        assert "settings-quota-track" in js

    def test_settings_xt_section_h_used_in_js(self):
        js = _read(H5_APP)
        assert "xt-section-h" in js, \
            "Settings should use xt-section-h section headers per prototype"

    def test_admin_voice_binding_entry_preserved(self):
        js = _read(H5_APP)
        assert "admin-voice-bindings" in js, \
            "Admin voice binding entry must be preserved in settings"

    def test_settings_sync_card_css_exists(self):
        css = _read(H5_CSS)
        assert ".settings-sync-card" in css

    def test_settings_version_css_exists(self):
        css = _read(H5_CSS)
        assert ".settings-version" in css


class TestSensitiveFieldsNotExposed:
    """Sensitive fields must not appear in rendered settings HTML."""

    def test_api_key_not_in_settings_render(self):
        js = _read(H5_APP)
        idx = js.find("function renderSettingsScreen")
        fn_body = js[idx:idx + 3000]
        assert "api_key" not in fn_body, \
            "api_key must not be rendered in settings"

    def test_admin_token_not_in_settings_render(self):
        js = _read(H5_APP)
        idx = js.find("function renderSettingsScreen")
        fn_body = js[idx:idx + 3000]
        assert "admin_token" not in fn_body

    def test_core_profile_id_not_in_settings_render(self):
        js = _read(H5_APP)
        idx = js.find("function renderSettingsScreen")
        fn_body = js[idx:idx + 3000]
        assert "coreProfileId" not in fn_body

    def test_provider_voice_id_not_in_settings_render(self):
        js = _read(H5_APP)
        idx = js.find("function renderSettingsScreen")
        fn_body = js[idx:idx + 3000]
        assert "provider_voice_id" not in fn_body

    def test_binding_id_not_in_settings_render(self):
        js = _read(H5_APP)
        idx = js.find("function renderSettingsScreen")
        fn_body = js[idx:idx + 3000]
        assert "binding_id" not in fn_body


class TestExistingBehaviorPreserved:
    """P22P / P22Q behaviors must not be broken."""

    def test_result_save_guard_preserved(self):
        js = _read(H5_APP)
        assert "if (state.resultSaved) return" in js

    def test_result_view_history_btn_preserved(self):
        html = _read(H5_INDEX)
        assert 'id="resultViewHistoryBtn"' in html

    def test_opening_overlay_preserved(self):
        html = _read(H5_INDEX)
        assert 'id="openingOverlay"' in html

    def test_history_navigates_from_result_save(self):
        html = _read(H5_INDEX)
        idx = html.find('id="resultViewHistoryBtn"')
        snippet = html[idx:idx + 200]
        assert "history" in snippet.lower()
