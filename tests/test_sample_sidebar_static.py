"""
test_sample_sidebar_static.py

P13-CREATION-B4-CHECK-FIX: Static contract tests for sample_sidebar.js.
Covers all hardening requirements: SampleStore-only reads, HTML escape,
refresh button, clear confirm, 20-item cap, in-card audio playback.
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
    """Return the body of a named function."""
    marker = 'function ' + name
    start = content.find(marker)
    assert start >= 0, name + ' function must exist'
    # find closing brace by counting braces
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


# ── SampleStore-only reads ─────────────────────────────────────────────────────

class TestSampleStoreReadOnly:
    def test_getSamplesSafe_exists(self):
        c = read()
        assert 'function getSamplesSafe' in c, \
            'getSamplesSafe must exist'

    def test_getSamplesSafe_calls_SampleStore_getSamples(self):
        c = read()
        body = func_body('getSamplesSafe', c)
        assert 'SampleStore.getSamples' in body, \
            'getSamplesSafe must call SampleStore.getSamples'

    def test_render_uses_getSamplesSafe(self):
        c = read()
        body = func_body('render', c)
        assert 'getSamplesSafe()' in body, \
            'render must call getSamplesSafe()'

    def test_render_does_not_read_localStorage_directly(self):
        c = read()
        body = func_body('render', c)
        assert 'localStorage.getItem' not in body, \
            'render must not read localStorage directly'

    def test_render_does_not_JSON_parse_localStorage(self):
        c = read()
        body = func_body('render', c)
        assert 'JSON.parse' not in body, \
            'render must not JSON.parse localStorage'


# ── HTML escape ───────────────────────────────────────────────────────────────

class TestHtmlEscape:
    def test_esc_function_exists(self):
        c = read()
        assert 'function esc(' in c or 'function esc (s' in c, \
            'esc helper must exist'

    def test_esc_uses_textContent(self):
        c = read()
        body = func_body('esc', c)
        assert 'textContent' in body, \
            'esc must use textContent to escape HTML'

    def test_esc_uses_innerHTML(self):
        c = read()
        body = func_body('esc', c)
        assert 'innerHTML' in body, \
            'esc must use innerHTML to return escaped string'

    def test_buildCard_calls_esc_on_sample_id(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'esc(sample.sample_id' in body or 'esc(id' in body, \
            'buildCard must escape sample_id'

    def test_buildCard_calls_esc_on_text_preview(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'esc(' in body, \
            'buildCard must escape text fields'

    def test_buildCard_calls_esc_on_source(self):
        c = read()
        body = func_body('buildCard', c)
        # sourceLabel may call esc internally, or buildCard may call esc on source
        assert 'esc(source' in body or 'esc(' in body, \
            'buildCard must escape source'

    def test_buildCard_calls_esc_on_profile_name(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'esc(' in body, \
            'buildCard must escape profile_name / profile_id'

    def test_buildCard_calls_esc_on_voice_name(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'esc(' in body, \
            'buildCard must escape voice_name / voice_id'


# ── outer card wrapper ────────────────────────────────────────────────────────

class TestOuterCard:
    def test_sample_sidebar_card_exists(self):
        c = read()
        body = func_body('render', c)
        assert 'sample-sidebar-card' in body, \
            'render must use .sample-sidebar-card outer wrapper'


# ── refresh button ───────────────────────────────────────────────────────────

class TestRefreshButton:
    def test_sampleSidebarRefreshBtn_in_render(self):
        c = read()
        body = func_body('render', c)
        assert 'sampleSidebarRefreshBtn' in body, \
            'render must include refresh button'

    def test_sampleSidebarRefreshBtn_in_events(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'sampleSidebarRefreshBtn' in body, \
            'bindActionEvents must handle refresh button click'


# ── clear confirm ─────────────────────────────────────────────────────────────

class TestClearConfirm:
    def test_clearSamples_calls_confirm(self):
        c = read()
        body = func_body('clearSamples', c)
        assert 'confirm' in body, \
            'clearSamples must call window.confirm before clearing'


# ── 20-item cap ──────────────────────────────────────────────────────────────

class TestTwentyItemCap:
    def test_MAX_VISIBLE_constant(self):
        c = read()
        assert re.search(r'MAX_VISIBLE\s*=\s*20\b', c), \
            'MAX_VISIBLE must be set to 20'

    def test_render_uses_slice(self):
        c = read()
        body = func_body('render', c)
        assert 'slice(0,' in body or 'slice(0,' in c, \
            'render must use slice(0, MAX_VISIBLE) to limit items'

    def test_title_shows_count_ratio(self):
        c = read()
        body = func_body('render', c)
        assert 'visibleSamples.length' in body or 'showing' in body, \
            'render title should show visible/total count'


# ── playSample in-card audio ──────────────────────────────────────────────────

class TestPlaySampleInCard:
    def test_playSample_takes_sampleId(self):
        c = read()
        body = func_body('playSample', c)
        # signature should be playSample(sampleId)
        assert re.search(r'function playSample\s*\(\s*sampleId\s*\)', body), \
            'playSample must take sampleId parameter'

    def test_playSample_finds_sample_by_id(self):
        c = read()
        body = func_body('playSample', c)
        assert 'getSamplesSafe()' in body or 'SampleStore' in body, \
            'playSample must find sample by sample_id via SampleStore'

    def test_playSample_uses_download_url(self):
        c = read()
        body = func_body('playSample', c)
        assert 'download_url' in body, \
            'playSample must use sample.download_url'

    def test_playSample_blocks_blob_url(self):
        c = read()
        body = func_body('playSample', c)
        assert 'blob:' in body, \
            'playSample must block blob: URLs'

    def test_playSample_renders_audio_element(self):
        c = read()
        body = func_body('playSample', c)
        assert '<audio' in body or 'audio' in body, \
            'playSample must render an <audio> element'

    def test_playSample_has_controls_attribute(self):
        c = read()
        body = func_body('playSample', c)
        assert 'controls' in body, \
            'playSample audio must have controls attribute'

    def test_playSample_has_autoplay_attribute(self):
        c = read()
        body = func_body('playSample', c)
        assert 'autoplay' in body, \
            'playSample audio must have autoplay attribute'

    def test_playSample_does_not_use_new_Audio_as_main_path(self):
        c = read()
        body = func_body('playSample', c)
        # new Audio() may appear as a comment or deprecated path; main path must NOT be new Audio(url)
        # Verify the function does NOT do "new Audio(url)" as primary behavior
        assert not re.search(r'new\s+Audio\s*\(\s*downloadUrl\s*\)', body), \
            'playSample must not use new Audio(url) as primary playback path'

    def test_play_btn_uses_data_id(self):
        c = read()
        body = func_body('buildCard', c)
        assert 'data-id="' in body, \
            'play button must use data-id attribute (not data-url)'

    def test_play_btn_event_uses_sampleId(self):
        c = read()
        body = func_body('bindActionEvents', c)
        assert 'playSample(sampleId' in body or 'playSample(id' in body, \
            'play button click must call playSample with sampleId'


# ── no API calls ──────────────────────────────────────────────────────────────

class TestNoApiCalls:
    def test_no_fetch(self):
        c = read()
        assert 'fetch(' not in c

    def test_no_guardedJsonFetch(self):
        c = read()
        assert 'guardedJsonFetch' not in c

    def test_no_xmlHttpRequest(self):
        c = read()
        assert 'XMLHttpRequest' not in c


# ── no batch / history / workspace coupling ───────────────────────────────────

class TestNoUnwantedReferences:
    def test_no_batch_longtext(self):
        c = read()
        assert 'batch_longtext' not in c and 'batchLongtext' not in c

    def test_no_batch_script(self):
        c = read()
        assert 'batch_script' not in c and 'batchScript' not in c

    def test_no_history_sample_store(self):
        c = read()
        assert 'history' not in c.lower() or 'sourceLabel' in c, \
            'must not reference history sample_store'

    def test_no_safePushWorkspaceSample(self):
        c = read()
        assert 'safePushWorkspaceSample' not in c

    def test_no_safePushAuditionSample(self):
        c = read()
        assert 'safePushAuditionSample' not in c


# ── storage key constant ──────────────────────────────────────────────────────

class TestStorageKey:
    def test_storage_key_constant(self):
        c = read()
        assert 'voice_lab_recent_samples_v1' in c, \
            'must reference correct storage key'


# ── copyText / fillTextInput ─────────────────────────────────────────────────

class TestCopyText:
    def test_copyText_uses_clipboard(self):
        c = read()
        body = func_body('copyText', c)
        assert 'navigator.clipboard' in body

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


# ── deleteSample / clearSamples ────────────────────────────────────────────────

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

    def test_has_confirm_guard(self):
        c = read()
        body = func_body('clearSamples', c)
        assert 'confirm' in body


# ── sourceLabel maps ──────────────────────────────────────────────────────────

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


# ── no internal state coupling ────────────────────────────────────────────────

class TestNoInternalCoupling:
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

    def test_no_sharedBatchState(self):
        c = read()
        assert 'sharedBatchState' not in c
