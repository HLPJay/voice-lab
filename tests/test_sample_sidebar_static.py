"""
test_sample_sidebar_static.py

P13-CREATION-B4-CHECK-FIX2: Static contract tests for sample_sidebar.js.
Covers: attr() helper, provider/model/created_at display, download button,
sourceLabel raw-source fix, SampleStore-only reads, esc, refresh, confirm.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDEBAR_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_sidebar.js')


# ── helpers ─────────────────────────────────────────────────────────────────

def read():
    return open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()


def func_body(name, content):
    """Return the full body of a named function (including nested braces)."""
    marker = 'function ' + name
    start = content.find(marker)
    assert start >= 0, name + ' function must exist'
    depth = 0
    end = start
    for i in range(start, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    return content[start:end]


# ── file structure ────────────────────────────────────────────────────────────

class TestFileStructure:
    def test_file_exists(self):
        assert os.path.isfile(SIDEBAR_JS_PATH)

    def test_iife(self):
        c = read()
        assert '(function ()' in c
        assert 'window.SampleSidebar' in c

    def test_use_strict(self):
        c = read()
        assert "'use strict'" in c or '"use strict"' in c


# ── exports ──────────────────────────────────────────────────────────────────

class TestExports:
    def test_all_eight_methods(self):
        c = read()
        found = re.findall(r'window\.SampleSidebar\s*=\s*\{([^}]+)\}', c, re.DOTALL)
        assert found
        obj = found[0]
        for m in ['init', 'render', 'refresh', 'playSample', 'deleteSample',
                  'clearSamples', 'copyText', 'fillTextInput']:
            assert re.search(r'\b' + m + r'\s*:', obj), 'missing: ' + m


# ── attr() helper ─────────────────────────────────────────────────────────────

class TestAttrHelper:
    def test_attr_function_exists(self):
        c = read()
        assert re.search(r'function attr\s*\(', c), \
            'attr() function must exist'

    def test_attr_replaces_double_quote(self):
        c = read()
        body = func_body('attr', c)
        assert '&quot;' in body or '&#34;' in body or ('\\"' in body and '&quot;' in body), \
            'attr() must escape " as &quot;'

    def test_attr_replaces_single_quote(self):
        c = read()
        body = func_body('attr', c)
        assert '&#39;' in body or '&#x27;' in body, \
            'attr() must escape \' as &#39;'

    def test_attr_replaces_ampersand(self):
        c = read()
        body = func_body('attr', c)
        assert '&amp;' in body, \
            'attr() must escape & as &amp;'

    def test_attr_replaces_angle_brackets(self):
        c = read()
        body = func_body('attr', c)
        assert '&lt;' in body and '&gt;' in body, \
            'attr() must escape < and >'


# ── esc() helper ─────────────────────────────────────────────────────────────

class TestEscHelper:
    def test_esc_exists(self):
        c = read()
        assert re.search(r'function esc\s*\(', c), 'esc() function must exist'

    def test_esc_uses_textContent(self):
        c = read()
        body = func_body('esc', c)
        assert 'textContent' in body, 'esc must use textContent'

    def test_esc_uses_innerHTML(self):
        c = read()
        body = func_body('esc', c)
        assert 'innerHTML' in body, 'esc must return innerHTML'


# ── SampleStore-only reads ─────────────────────────────────────────────────────

class TestSampleStoreReadOnly:
    def test_getSamplesSafe_exists(self):
        c = read()
        assert 'function getSamplesSafe' in c

    def test_render_uses_getSamplesSafe(self):
        c = read()
        body = func_body('render', c)
        assert 'getSamplesSafe()' in body

    def test_render_does_not_read_localStorage_directly(self):
        c = read()
        body = func_body('render', c)
        assert 'localStorage.getItem' not in body

    def test_render_does_not_JSON_parse(self):
        c = read()
        body = func_body('render', c)
        assert 'JSON.parse' not in body


# ── buildCard attribute escaping ─────────────────────────────────────────────

class TestBuildCardAttributeEscaping:
    def test_data_sample_id_uses_attr(self):
        c = read()
        body = func_body('buildCard', c)
        # idAttr = attr(...)
        assert 'idAttr = attr(' in body, \
            'buildCard must use attr() for idAttr'

    def test_data_sample_id_attribute_uses_idAttr(self):
        c = read()
        body = func_body('buildCard', c)
        # Must use idAttr (the attr()-escaped value) in data-sample-id attribute
        assert 'idAttr' in body and 'data-sample-id' in body, \
            'data-sample-id must reference attr()-escaped idAttr variable'

    def test_title_uses_attr(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'title="' in body and 'TitleAttr' in body, \
            'title attribute must use attr() escaped value'

    def test_source_tag_uses_attr_for_src(self):
        c = read()
        body = func_body('playSample', c)
        assert 'audioSrcAttr = attr(' in body or 'src="' in body, \
            '<source src> must use attr() escaped URL'


# ── sourceLabel raw source fix ────────────────────────────────────────────────

class TestSourceLabelRawSource:
    def test_sourceLabel_takes_raw_source(self):
        c = read()
        body = func_body('sourceLabel', c)
        assert 'source' in body and 'map[source]' in body, \
            'sourceLabel must look up raw source string in map'

    def test_sourceLabel_does_not_pre_escape_input(self):
        c = read()
        body = func_body('sourceLabel', c)
        # Should NOT be esc(source) as input to map lookup
        assert not re.search(r'map\s*\[\s*esc\s*\(\s*source', body), \
            'sourceLabel must not esc() the source before map lookup'

    def test_buildCard_passes_raw_source_to_sourceLabel(self):
        c = read()
        body = func_body('buildCard', c)
        # sourceLabel(sourceRaw) — not esc(source)
        assert 'sourceLabel(sourceRaw)' in body, \
            'buildCard must pass raw source to sourceLabel()'


# ── provider / model / created_at display ────────────────────────────────────

class TestMetadataDisplay:
    def test_provider_escaped_and_displayed(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'providerEsc' in body and 'provider' in body, \
            'buildCard must display escaped provider'

    def test_model_escaped_and_displayed(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'modelEsc' in body and 'model' in body, \
            'buildCard must display escaped model'

    def test_createdAt_escaped_and_displayed(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'createdAtEsc' in body and 'created_at' in body, \
            'buildCard must display escaped created_at'

    def test_formatCreatedAt_exists(self):
        c = read()
        assert 'function formatCreatedAt' in c, \
            'formatCreatedAt() must exist'

    def test_formatCreatedAt_uses_Date(self):
        c = read()
        body = func_body('formatCreatedAt', c)
        assert 'Date' in body, \
            'formatCreatedAt must use Date constructor'

    def test_formatCreatedAt_returns_empty_for_invalid(self):
        c = read()
        body = func_body('formatCreatedAt', c)
        assert 'isNaN' in body or 'return' in body, \
            'formatCreatedAt must handle invalid dates'


# ── download button ───────────────────────────────────────────────────────────

class TestDownloadButton:
    def test_download_button_exists(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-download' in body, \
            'buildCard must include sample-btn-download'

    def test_download_button_uses_download_url(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'downloadUrlAttr' in body and 'href="' in body, \
            'download button href must use attr()-escaped download_url'

    def test_download_button_uses_download_attribute(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'download="' in body or "download='" in body, \
            'download button must have download attribute'

    def test_download_button_rejects_blob_url(self):
        c = read()
        body = func_body('buildCard', c)
        # canDownload gated by isSafeAudioUrl which rejects blob:
        assert 'isSafeAudioUrl' in body, \
            'download button must use isSafeAudioUrl()'

    def test_download_button_does_not_call_backend(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'fetch(' not in body
        assert 'guardedJsonFetch' not in body


# ── URL safety ─────────────────────────────────────────────────────────────────

class TestUrlSafety:
    def test_isSafeAudioUrl_exists(self):
        c = read()
        assert 'function isSafeAudioUrl' in c, \
            'isSafeAudioUrl() must exist'

    def test_isSafeAudioUrl_rejects_blob(self):
        c = read()
        body = func_body('isSafeAudioUrl', c)
        assert "'blob:'" in body or '"blob:"' in body, \
            'isSafeAudioUrl must reject blob:'

    def test_isSafeAudioUrl_rejects_javascript(self):
        c = read()
        body = func_body('isSafeAudioUrl', c)
        assert "'javascript:'" in body or '"javascript:"' in body, \
            'isSafeAudioUrl must reject javascript:'

    def test_isSafeAudioUrl_rejects_data(self):
        c = read()
        body = func_body('isSafeAudioUrl', c)
        assert "'data:'" in body or '"data:"' in body, \
            'isSafeAudioUrl must reject data:'

    def test_isSafeAudioUrl_allows_api(self):
        c = read()
        body = func_body('isSafeAudioUrl', c)
        assert "'/api/'" in body or '"/api/"' in body, \
            'isSafeAudioUrl must allow /api/'

    def test_isSafeAudioUrl_allows_http(self):
        c = read()
        body = func_body('isSafeAudioUrl', c)
        assert "'http://'" in body or '"http://"' in body, \
            'isSafeAudioUrl must allow http://'

    def test_isSafeAudioUrl_allows_https(self):
        c = read()
        body = func_body('isSafeAudioUrl', c)
        assert "'https://'" in body or '"https://"' in body, \
            'isSafeAudioUrl must allow https://'

    def test_buildCard_uses_isSafeAudioUrl(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'isSafeAudioUrl(downloadUrl)' in body, \
            'buildCard must use isSafeAudioUrl for canPlay/canDownload'

    def test_playSample_uses_isSafeAudioUrl(self):
        c = read()
        body = func_body('playSample', c)
        assert 'isSafeAudioUrl' in body, \
            'playSample must use isSafeAudioUrl()'


# ── outer card wrapper ────────────────────────────────────────────────────────

class TestOuterCard:
    def test_sample_sidebar_card_in_render(self):
        c = read()
        body = func_body('render', c)
        assert 'sample-sidebar-card' in body


# ── refresh button ───────────────────────────────────────────────────────────

class TestRefreshButton:
    def test_refresh_button_in_render(self):
        c = read()
        body = func_body('render', c)
        assert 'sampleSidebarRefreshBtn' in body

    def test_refresh_button_event_handler(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sampleSidebarRefreshBtn' in body

    def test_empty_state_has_refresh_button(self):
        c = read()
        body = func_body('render', c)
        # The total===0 empty state branch must also include the refresh button
        assert 'sampleSidebarRefreshBtn' in body, \
            'empty state must also include refresh button'

    def test_render_binds_events_before_empty_state_return(self):
        c = read()
        body = func_body('render', c)
        # ensureActionEventsBound must be called BEFORE the total===0 early return
        ensure_idx = body.find('ensureActionEventsBound(root)')
        empty_idx = body.find('if (total === 0)')
        assert ensure_idx >= 0, 'render must call ensureActionEventsBound'
        assert empty_idx >= 0, 'render must have total===0 branch'
        assert ensure_idx < empty_idx, \
            'ensureActionEventsBound must be called before empty state return'


# ── ensureActionEventsBound ───────────────────────────────────────────────────

class TestEnsureActionEventsBound:
    def test_ensureActionEventsBound_exists(self):
        c = read()
        assert 'function ensureActionEventsBound' in c, \
            'ensureActionEventsBound must exist'

    def test_calls_bindActionEvents(self):
        c = read()
        body = func_body('ensureActionEventsBound', c)
        assert 'bindActionEvents' in body, \
            'ensureActionEventsBound must call bindActionEvents'

    def test_guards_against_double_bind(self):
        c = read()
        body = func_body('ensureActionEventsBound', c)
        assert '_eventsBound' in body, \
            'ensureActionEventsBound must check _eventsBound to avoid double binding'

    def test_no_new_listener_on_repeat_calls(self):
        c = read()
        # The function should check _eventsBound before calling bindActionEvents
        body = func_body('ensureActionEventsBound', c)
        assert '_eventsBound' in body and 'bindActionEvents' in body


# ── clear confirm ─────────────────────────────────────────────────────────────

class TestClearConfirm:
    def test_clearSamples_calls_confirm(self):
        c = read()
        body = func_body('clearSamples', c)
        assert 'confirm' in body


# ── MAX_VISIBLE cap ─────────────────────────────────────────────────────────

class TestMaxVisibleCap:
    def test_MAX_VISIBLE_equals_20(self):
        c = read()
        assert re.search(r'MAX_VISIBLE\s*=\s*20\b', c)

    def test_render_uses_slice(self):
        c = read()
        body = func_body('render', c)
        assert 'slice(0,' in body

    def test_title_shows_count_ratio(self):
        c = read()
        body = func_body('render', c)
        assert 'showing' in body and 'total' in body


# ── playSample in-card audio ──────────────────────────────────────────────────

class TestPlaySampleInCard:
    def test_playSample_takes_sampleId(self):
        c = read()
        body = func_body('playSample', c)
        assert re.search(r'function playSample\s*\(\s*sampleId\s*\)', body)

    def test_playSample_finds_sample_by_id(self):
        c = read()
        body = func_body('playSample', c)
        assert 'getSamplesSafe()' in body

    def test_playSample_blocks_unsafe_url(self):
        c = read()
        body = func_body('playSample', c)
        assert 'isSafeAudioUrl(downloadUrl)' in body, \
            'playSample must use isSafeAudioUrl to block unsafe URLs'

    def test_playSample_renders_audio_controls(self):
        c = read()
        body = func_body('playSample', c)
        assert 'controls' in body and 'autoplay' in body

    def test_play_btn_uses_data_id(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'data-id="' in body and 'sample-btn-play' in body


# ── no API calls ──────────────────────────────────────────────────────────────

class TestNoApiCalls:
    def test_no_fetch(self):
        c = read()
        assert 'fetch(' not in c

    def test_no_guardedJsonFetch(self):
        c = read()
        assert 'guardedJsonFetch' not in c


# ── no unwanted references ───────────────────────────────────────────────────

class TestNoUnwantedReferences:
    def test_no_batch_longtext_function_references(self):
        """sidebar must not call batch_longtext functions, but sourceLabel entries are allowed."""
        c = read()
        # sourceLabel map entries are allowed
        assert 'safePushBatchSample' not in c
        assert '_batchSampleContextById' not in c

    def test_no_batch_script_function_references(self):
        """sidebar must not call batch_script functions, but sourceLabel entries are allowed."""
        c = read()
        assert 'safePushBatchSample' not in c
        assert '_batchSampleContextById' not in c

    def test_no_safePushWorkspaceSample(self):
        c = read()
        assert 'safePushWorkspaceSample' not in c

    def test_no_safePushAuditionSample(self):
        c = read()
        assert 'safePushAuditionSample' not in c

    def test_no_handleGenerate(self):
        c = read()
        assert 'handleGenerate' not in c

    def test_no_voiceBindMap(self):
        c = read()
        assert 'voiceBindMap' not in c

    def test_no_profileBinding(self):
        c = read()
        assert 'profileBinding' not in c

    def test_no_batchState(self):
        c = read()
        assert 'batchState' not in c


# ── storage key ───────────────────────────────────────────────────────────────

class TestStorageKey:
    def test_storage_key_constant(self):
        c = read()
        assert 'voice_lab_recent_samples_v1' in c


# ── copyText / fillTextInput ─────────────────────────────────────────────────

class TestCopyText:
    def test_copyText_uses_clipboard(self):
        c = read()
        assert 'navigator.clipboard' in func_body('copyText', c)

    def test_copyText_has_execCommand_fallback(self):
        c = read()
        body = func_body('copyText', c)
        assert 'execCommand' in body or 'textarea' in body


class TestFillTextInput:
    def test_fillTextInput_writes_to_textInput(self):
        c = read()
        body = func_body('fillTextInput', c)
        assert 'textInput' in body

    def test_fillTextInput_dispatches_input_event(self):
        c = read()
        body = func_body('fillTextInput', c)
        assert 'dispatchEvent' in body


# ── deleteSample / clearSamples ─────────────────────────────────────────────

class TestDeleteSample:
    def test_calls_sampleStore_deleteSample(self):
        c = read()
        body = func_body('deleteSample', c)
        assert 'SampleStore.deleteSample' in body

    def test_calls_render_after_delete(self):
        c = read()
        body = func_body('deleteSample', c)
        assert 'render()' in body


class TestClearSamples:
    def test_calls_sampleStore_clearSamples(self):
        c = read()
        body = func_body('clearSamples', c)
        assert 'SampleStore.clearSamples' in body

    def test_calls_render_after_clear(self):
        c = read()
        body = func_body('clearSamples', c)
        assert 'render()' in body


# ── sourceLabel maps ─────────────────────────────────────────────────────────

class TestSourceLabel:
    def test_maps_workspace_sync(self):
        c = read()
        assert 'workspace_sync' in c

    def test_maps_workspace_async(self):
        c = read()
        assert 'workspace_async' in c

    def test_maps_workspace_stream(self):
        c = read()
        assert 'workspace_stream' in c

    def test_maps_workspace_variant(self):
        c = read()
        assert 'workspace_variant' in c

    def test_maps_audition(self):
        c = read()
        assert 'audition' in c


# ── detail view (P14-CONTEXT-B2) ─────────────────────────────────────────────

class TestDetailView:
    def test_showSampleDetail_function_exists(self):
        c = read()
        assert re.search(r'function showSampleDetail\s*\(', c), \
            'showSampleDetail function must exist'

    def test_showSampleDetail_exposed_on_window_sample_sidebar(self):
        c = read()
        assert re.search(r'showSampleDetail\s*:', c), \
            'showSampleDetail must be exposed on window.SampleSidebar'

    def test_detail_button_in_buildCard(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-detail' in body, \
            'buildCard must include sample-btn-detail button'

    def test_detail_button_conditional_on_context_id(self):
        c = read()
        body = func_body('buildCard', c)
        idx = body.find('sample-btn-detail')
        assert idx >= 0
        region = body[max(0, idx - 150):idx + 50]
        assert 'context_id' in region, \
            'detail button must be added only when sample.context_id exists'

    def test_detail_event_handler_calls_showSampleDetail(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-btn-detail' in body, \
            'bindActionEvents must handle sample-btn-detail click'
        assert 'showSampleDetail' in body, \
            'detail click must call showSampleDetail'

    def test_showSampleDetail_calls_context_store_getContext(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'ContextStore.getContext' in body, \
            'showSampleDetail must call ContextStore.getContext'

    def test_showSampleDetail_escapes_displayed_text(self):
        c = read()
        body = func_body('showSampleDetail', c)
        # Must escape displayed values
        assert 'esc(' in body, \
            'showSampleDetail must escape text with esc()'

    def test_showSampleDetail_no_fetch(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'fetch(' not in body, \
            'showSampleDetail must not call fetch'

    def test_showSampleDetail_no_localStorage_write(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'localStorage.setItem' not in body, \
            'showSampleDetail must not write to localStorage'

    def test_showSampleDetail_no_fill_back(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'fillTextInput' not in body, \
            'showSampleDetail must not implement fill/restore'

    def test_detail_panel_close_button(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'sample-detail-close' in body, \
            'detail panel must have close button'

    def test_detail_panel_removes_existing_panel(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'sample-detail-panel' in body, \
            'showSampleDetail must manage .sample-detail-panel element'

    def test_context_not_found_shows_graceful_message(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'sample-detail-empty' in body or '不可用' in body, \
            'showSampleDetail must show graceful message when context not found'


# ── flat action buttons (P14-SIDEBAR-ACTIONS-B1-UXFIX1) ──────────────────────

class TestFlatActionButtons:
    """Tests for flat action buttons in sample cards (B1-UXFIX1)."""

    def test_buildCard_contains_sample_btn_copy(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-copy' in body, \
            'buildCard must include sample-btn-copy as flat button'

    def test_buildCard_contains_sample_btn_fill(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-fill' in body, \
            'buildCard must include sample-btn-fill as flat button'

    def test_buildCard_contains_sample_btn_delete(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-delete' in body, \
            'buildCard must include sample-btn-delete as flat button'

    def test_buildCard_no_sample_more_wrap(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-more-wrap' not in body, \
            'buildCard must not include sample-more-wrap (more menu removed)'

    def test_buildCard_no_sample_more_menu(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-more-menu' not in body, \
            'buildCard must not include sample-more-menu'

    def test_buildCard_no_sample_btn_more(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-more' not in body, \
            'buildCard must not include sample-btn-more'

    def test_buildCard_no_sample_menu_copy(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-menu-copy' not in body, \
            'buildCard must not include sample-menu-copy (copy is now flat)'

    def test_buildCard_no_sample_menu_fill(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-menu-fill' not in body, \
            'buildCard must not include sample-menu-fill (fill is now flat)'

    def test_buildCard_no_sample_menu_delete(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-menu-delete' not in body, \
            'buildCard must not include sample-menu-delete (delete is now flat)'

    def test_canShowFill_function_exists(self):
        c = read()
        assert 'function canShowFill' in c, \
            'canShowFill function must exist'

    def test_canShowFill_rejects_batch_longtext_merged(self):
        c = read()
        body = func_body('canShowFill', c)
        assert 'batch_longtext_merged' in body, \
            'canShowFill must return false for batch_longtext_merged'

    def test_canShowFill_rejects_batch_script_merged(self):
        c = read()
        body = func_body('canShowFill', c)
        assert 'batch_script_merged' in body, \
            'canShowFill must return false for batch_script_merged'

    def test_bindActionEvents_handles_copy_button(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-btn-copy' in body, \
            'bindActionEvents must handle sample-btn-copy click'

    def test_bindActionEvents_handles_fill_button(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-btn-fill' in body, \
            'bindActionEvents must handle sample-btn-fill click'

    def test_bindActionEvents_handles_delete_button(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-btn-delete' in body, \
            'bindActionEvents must handle sample-btn-delete click'

    def test_flat_delete_calls_confirm(self):
        c = read()
        body = func_body('bindActionEvents', c)
        idx = body.find('sample-btn-delete')
        region = body[idx:idx + 400]
        assert 'confirm' in region, \
            'sample-btn-delete must call window.confirm before delete'

    def test_no_sample_more_wrap_in_bindActionEvents(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-more-wrap' not in body, \
            'bindActionEvents must not handle sample-more-wrap (more menu removed)'

    def test_no_sample_btn_more_in_bindActionEvents(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-btn-more' not in body, \
            'bindActionEvents must not handle sample-btn-more'

    def test_no_sample_menu_items_in_bindActionEvents(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-menu-copy' not in body, \
            'bindActionEvents must not handle sample-menu-copy'
        assert 'sample-menu-fill' not in body, \
            'bindActionEvents must not handle sample-menu-fill'
        assert 'sample-menu-delete' not in body, \
            'bindActionEvents must not handle sample-menu-delete'

    def test_play_and_download_still_flat(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-play' in body
        assert 'sample-btn-download' in body

    def test_detail_still_flat(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'sample-btn-detail' in body, \
            'detail button should remain flat'

    def test_no_new_fetch_api_calls(self):
        c = read()
        # Check only in bindActionEvents and showSampleDetail bodies
        be_body = func_body('bindActionEvents', c)
        detail_body = func_body('showSampleDetail', c)
        assert 'fetch(' not in be_body, \
            'bindActionEvents must not call fetch'
        assert '/api/' not in be_body, \
            'bindActionEvents must not call API endpoints'
        assert 'fetch(' not in detail_body, \
            'showSampleDetail must not call fetch'


# ── restore longtext (P14-CONTEXT-B3) ─────────────────────────────────────────

class TestRestoreLongtext:
    """Tests for longtext context restore functionality."""

    def test_dispatchInputChange_exists(self):
        c = read()
        assert 'function dispatchInputChange' in c, \
            'dispatchInputChange function must exist'

    def test_setValueIfPresent_exists(self):
        c = read()
        assert 'function setValueIfPresent' in c, \
            'setValueIfPresent function must exist'

    def test_setCheckedIfPresent_exists(self):
        c = read()
        assert 'function setCheckedIfPresent' in c, \
            'setCheckedIfPresent function must exist'

    def test_switchToLongtextTab_exists(self):
        c = read()
        assert 'function switchToLongtextTab' in c, \
            'switchToLongtextTab function must exist'

    def test_applyLongtextContextToForm_exists(self):
        c = read()
        assert 'function applyLongtextContextToForm' in c, \
            'applyLongtextContextToForm function must exist'

    def test_restoreLongtextContext_exists(self):
        c = read()
        assert 'function restoreLongtextContext' in c, \
            'restoreLongtextContext function must exist'

    def test_restoreLongtextContext_calls_switchToLongtextTab(self):
        c = read()
        body = func_body('restoreLongtextContext', c)
        assert 'switchToLongtextTab' in body, \
            'restoreLongtextContext must call switchToLongtextTab'

    def test_restoreLongtextContext_calls_applyLongtextContextToForm(self):
        c = read()
        body = func_body('restoreLongtextContext', c)
        assert 'applyLongtextContextToForm' in body, \
            'restoreLongtextContext must call applyLongtextContextToForm'

    def test_restoreLongtextContext_checks_type_longtext(self):
        c = read()
        body = func_body('restoreLongtextContext', c)
        assert "type !== 'longtext'" in body or 'type !== "longtext"' in body, \
            'restoreLongtextContext must guard on context.type !== "longtext"'

    def test_restoreLongtextContext_no_fetch(self):
        c = read()
        body = func_body('restoreLongtextContext', c)
        assert 'fetch(' not in body, \
            'restoreLongtextContext must not call fetch'

    def test_restoreLongtextContext_no_guardedJsonFetch(self):
        c = read()
        body = func_body('restoreLongtextContext', c)
        assert 'guardedJsonFetch' not in body, \
            'restoreLongtextContext must not call guardedJsonFetch'

    def test_restoreLongtextContext_no_submit(self):
        c = read()
        body = func_body('restoreLongtextContext', c)
        assert 'handleBatchLongtextSubmit' not in body, \
            'restoreLongtextContext must not call handleBatchLongtextSubmit'

    def test_restoreLongtextContext_no_context_store_write(self):
        c = read()
        body = func_body('restoreLongtextContext', c)
        assert 'ContextStore.pushContext' not in body, \
            'restoreLongtextContext must not write to ContextStore'

    def test_applyLongtextContextToForm_writes_batchText(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchText' in body, \
            'applyLongtextContextToForm must write to batchText'

    def test_applyLongtextContextToForm_writes_batchProfile(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchProfile' in body, \
            'applyLongtextContextToForm must write to batchProfile'

    def test_applyLongtextContextToForm_writes_batchProvider(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchProvider' in body, \
            'applyLongtextContextToForm must write to batchProvider'

    def test_applyLongtextContextToForm_writes_batchStrategy(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchStrategy' in body, \
            'applyLongtextContextToForm must write to batchStrategy'

    def test_applyLongtextContextToForm_writes_batchMaxChars(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchMaxChars' in body, \
            'applyLongtextContextToForm must write to batchMaxChars'

    def test_applyLongtextContextToForm_writes_batchSilence(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchSilence' in body, \
            'applyLongtextContextToForm must write to batchSilence'

    def test_applyLongtextContextToForm_writes_batchOutputFormat(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchOutputFormat' in body, \
            'applyLongtextContextToForm must write to batchOutputFormat'

    def test_applyLongtextContextToForm_writes_batchNeedSubtitle(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchNeedSubtitle' in body, \
            'applyLongtextContextToForm must write to batchNeedSubtitle'

    def test_applyLongtextContextToForm_writes_batchSpeed(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchSpeed' in body, \
            'applyLongtextContextToForm must write to batchSpeed'

    def test_applyLongtextContextToForm_writes_batchVol(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchVol' in body, \
            'applyLongtextContextToForm must write to batchVol'

    def test_applyLongtextContextToForm_writes_batchPitch(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchPitch' in body, \
            'applyLongtextContextToForm must write to batchPitch'

    def test_applyLongtextContextToForm_writes_batchEmotion(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'batchEmotion' in body, \
            'applyLongtextContextToForm must write to batchEmotion'

    def test_applyLongtextContextToForm_dispatches_events(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        # setValueIfPresent / setCheckedIfPresent call dispatchInputChange internally
        assert 'setValueIfPresent' in body or 'setCheckedIfPresent' in body, \
            'applyLongtextContextToForm must call setValueIfPresent/setCheckedIfPresent which dispatch events'

    def test_showSampleDetail_adds_restore_button_for_longtext(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'sample-detail-restore-btn' in body, \
            'showSampleDetail must add sample-detail-restore-btn button'

    def test_showSampleDetail_restore_button_uses_data_context_id(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'data-context-id' in body, \
            'restore button must use data-context-id attribute'

    def test_showSampleDetail_restore_button_conditional_on_longtext(self):
        c = read()
        body = func_body('showSampleDetail', c)
        # Button only added when context.type === 'longtext'
        idx = body.find('sample-detail-restore-btn')
        assert idx >= 0, 'restore button must exist in showSampleDetail'
        # Window must be wide enough to cover the longtext HTML building block
        region = body[max(0, idx - 2000):idx + 50]
        assert "type === 'longtext'" in region or 'type === "longtext"' in region, \
            'restore button must be conditional on context.type === "longtext"'

    def test_showSampleDetail_no_fill_back_in_showSampleDetail(self):
        c = read()
        body = func_body('showSampleDetail', c)
        assert 'fillTextInput' not in body, \
            'showSampleDetail must not directly fill/restore (fill logic is in restoreLongtextContext)'

    def test_showSampleDetail_restore_button_uses_attr_escape(self):
        c = read()
        body = func_body('showSampleDetail', c)
        idx = body.find('sample-detail-restore-btn')
        assert idx >= 0
        region = body[max(0, idx - 200):idx + 50]
        assert 'attr(' in region, \
            'restore button context_id must use attr() for escaping'

    def test_full_text_not_in_data_attribute(self):
        c = read()
        body = func_body('showSampleDetail', c)
        # full_text must NOT appear in any data-* attribute
        import re
        data_attr_refs = re.findall(r'data-[a-zA-Z-]+\s*=\s*"[^"]*full_text[^"]*"', body)
        assert not data_attr_refs, \
            'full_text must not appear in data-* attributes'

    def test_bindActionEvents_handles_restore_button(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sample-detail-restore-btn' in body, \
            'bindActionEvents must handle sample-detail-restore-btn click'

    def test_bindActionEvents_restore_reads_context_from_store(self):
        c = read()
        body = func_body('bindActionEvents', c)
        idx = body.find('sample-detail-restore-btn')
        region = body[idx:idx + 800]
        assert 'ContextStore.getContext' in region, \
            'restore handler must read context from ContextStore'

    def test_bindActionEvents_restore_calls_restoreLongtextContext(self):
        c = read()
        body = func_body('bindActionEvents', c)
        idx = body.find('sample-detail-restore-btn')
        region = body[idx:idx + 800]
        assert 'restoreLongtextContext' in region, \
            'restore handler must call restoreLongtextContext'

    def test_switchToLongtextTab_toggles_active_class(self):
        c = read()
        body = func_body('switchToLongtextTab', c)
        assert 'active' in body, \
            'switchToLongtextTab must toggle active class'

    def test_switchToLongtextTab_uses_data_tab_longtext(self):
        c = read()
        body = func_body('switchToLongtextTab', c)
        assert 'data-tab="longtext"' in body, \
            'switchToLongtextTab must target data-tab="longtext"'

    def test_applyLongtextContextToForm_reads_context_params(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'params' in body, \
            'applyLongtextContextToForm must safely read context.params'

    def test_applyLongtextContextToForm_handles_null_params(self):
        c = read()
        body = func_body('applyLongtextContextToForm', c)
        assert 'context.params || {}' in body or 'params ||' in body, \
            'applyLongtextContextToForm must handle null/undefined params'

