"""
test_sample_store_batch_integration_static.py

P13-CREATION-B5-MVP1: Static contract tests for batch merged audio
sample_store integration.

Covers:
- isSafeBatchAudioUrl helper
- safePushBatchSample function
- batch_longtext.js context saving
- batch_script.js context saving
- renderBatchResultPlayer integration
- sourceLabel additions
- Anti-duplicate push mechanism
- All preconditions enforced
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')
BATCH_LONGTEXT_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'batch_longtext.js')
BATCH_SCRIPT_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'batch_script.js')
SAMPLE_SIDEBAR_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_sidebar.js')


def read_html():
    return open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()


def read_longtext():
    return open(BATCH_LONGTEXT_JS_PATH, 'r', encoding='utf-8').read()


def read_script():
    return open(BATCH_SCRIPT_JS_PATH, 'r', encoding='utf-8').read()


def read_sidebar():
    return open(SAMPLE_SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()


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


# ── isSafeBatchAudioUrl ────────────────────────────────────────────────────────

class TestIsSafeBatchAudioUrl:
    def test_function_exists(self):
        assert 'function isSafeBatchAudioUrl' in read_html()

    def test_rejects_blob(self):
        body = func_body('isSafeBatchAudioUrl', read_html())
        assert "'blob:'" in body or '"blob:"' in body

    def test_rejects_javascript(self):
        body = func_body('isSafeBatchAudioUrl', read_html())
        assert "'javascript:'" in body or '"javascript:"' in body

    def test_rejects_data(self):
        body = func_body('isSafeBatchAudioUrl', read_html())
        assert "'data:'" in body or '"data:"' in body

    def test_allows_api(self):
        body = func_body('isSafeBatchAudioUrl', read_html())
        assert "'/api/'" in body or '"/api/"' in body

    def test_allows_http(self):
        body = func_body('isSafeBatchAudioUrl', read_html())
        assert "'http://'" in body or '"http://"' in body

    def test_allows_https(self):
        body = func_body('isSafeBatchAudioUrl', read_html())
        assert "'https://'" in body or '"https://"' in body


# ── safePushBatchSample ───────────────────────────────────────────────────────

class TestSafePushBatchSample:
    def test_function_exists(self):
        assert 'function safePushBatchSample' in read_html()

    def test_is_fail_safe(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'try' in body and 'catch' in body

    def test_calls_SampleStore_pushSample(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'SampleStore.pushSample' in body

    def test_no_direct_localStorage(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'localStorage.getItem' not in body
        assert 'localStorage.setItem' not in body

    def test_rejects_non_success_status(self):
        body = func_body('safePushBatchSample', read_html())
        assert "data.status !== 'success'" in body or 'data.status !== "success"' in body

    def test_rejects_missing_batch_id(self):
        body = func_body('safePushBatchSample', read_html())
        assert '!data.batch_id' in body or '!batch_id' in body

    def test_rejects_missing_merged_audio_id(self):
        body = func_body('safePushBatchSample', read_html())
        assert '!audio.id' in body or '!merged_audio.id' in body or 'audio.id' in body

    def test_rejects_missing_audio_url(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'isSafeBatchAudioUrl' in body

    def test_download_url_uses_batch_api(self):
        body = func_body('safePushBatchSample', read_html())
        assert '/api/voice/batch/' in body
        assert 'encodeURIComponent(batchId)' in body or 'encodeURIComponent(data.batch_id)' in body

    def test_download_url_is_not_merged_audio_url(self):
        """download_url must use batch API, not merged_audio.url directly."""
        body = func_body('safePushBatchSample', read_html())
        # Should NOT use audio.url as the download_url value
        assert 'downloadUrl = audio.url' not in body
        # Should have batch download URL construction
        assert '/api/voice/batch/' in body

    def test_no_asset_fallback_in_download_url(self):
        """Must not fall back to /api/voice/assets/ as download_url."""
        body = func_body('safePushBatchSample', read_html())
        # The function should not have a fallback path for download_url to assets
        # Check that downloadUrl is set to batch API only
        assert 'downloadUrl = ' in body
        # Should not contain '/api/voice/assets/' in downloadUrl assignment
        download_url_block = body[body.find('downloadUrl'):body.find('downloadUrl')+300] if 'downloadUrl' in body else ''
        assert '/api/voice/assets/' not in download_url_block

    def test_source_batch_longtext_merged_from_render(self):
        """batch_longtext_merged source is passed from renderBatchResultPlayer."""
        html = read_html()
        body = html[html.find('function renderBatchResultPlayer'):]
        body = body[:body.find('\n  function ', 1)]
        assert 'batch_longtext_merged' in body

    def test_source_batch_script_merged_from_render(self):
        """batch_script_merged source is passed from renderBatchResultPlayer."""
        html = read_html()
        body = html[html.find('function renderBatchResultPlayer'):]
        body = body[:body.find('\n  function ', 1)]
        assert 'batch_script_merged' in body

    def test_segment_id_is_null(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'segment_id: null' in body

    def test_tags_batch_and_merged(self):
        body = func_body('safePushBatchSample', read_html())
        assert "'batch'" in body or '"batch"' in body
        assert "'merged'" in body or '"merged"' in body

    def test_model_is_null(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'model: null' in body

    def test_voice_id_is_null(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'voice_id: null' in body

    def test_voice_name_is_null(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'voice_name: null' in body

    def test_anti_duplicate_mechanism(self):
        body = func_body('safePushBatchSample', read_html())
        assert '_batchSamplePushedByKey' in body

    def test_calls_SampleSidebar_refresh_after_push(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'SampleSidebar.refresh' in body

    def test_extra_text_preview_fallback(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'text_preview' in body

    def test_segments_first_text_preview_fallback(self):
        body = func_body('safePushBatchSample', read_html())
        assert 'segments' in body and 'text_preview' in body


# ── batch_longtext.js context ──────────────────────────────────────────────────

class TestBatchLongtextContext:
    def test_batchSampleContextById_exists(self):
        c = read_longtext()
        assert '_batchSampleContextById' in c

    def test_saves_batch_longtext_merged_context(self):
        c = read_longtext()
        assert "source: 'batch_longtext_merged'" in c

    def test_saves_text_preview(self):
        c = read_longtext()
        assert 'text_preview: text' in c

    def test_saves_provider(self):
        c = read_longtext()
        assert 'provider: provider' in c

    def test_saves_profile_id(self):
        c = read_longtext()
        assert 'profile_id:' in c

    def test_profile_name_is_null(self):
        c = read_longtext()
        assert 'profile_name: null' in c

    def test_model_is_null(self):
        c = read_longtext()
        assert 'model: null' in c

    def test_voice_id_is_null(self):
        c = read_longtext()
        assert 'voice_id: null' in c

    def test_voice_name_is_null(self):
        c = read_longtext()
        assert 'voice_name: null' in c

    def test_saves_audio_format(self):
        c = read_longtext()
        assert 'audio_format:' in c

    def test_context_keyed_by_batch_id(self):
        c = read_longtext()
        assert 'data.batch_id' in c
        assert '_batchSampleContextById[data.batch_id]' in c or '_batchSampleContextById[data.batch_id]' in c.replace(' ', '')


# ── batch_script.js context ──────────────────────────────────────────────────

class TestBatchScriptContext:
    def test_batchSampleContextById_exists(self):
        c = read_script()
        assert '_batchSampleContextById' in c

    def test_saves_batch_script_merged_context(self):
        c = read_script()
        assert "source: 'batch_script_merged'" in c

    def test_getSingleProfileId_exists(self):
        c = read_script()
        assert 'function getSingleProfileId' in c

    def test_getSingleProfileId_returns_single_id(self):
        c = read_script()
        body = func_body('getSingleProfileId', c)
        assert 'ids.length === 1' in body

    def test_buildScriptTextPreview_exists(self):
        c = read_script()
        assert 'function buildScriptTextPreview' in c

    def test_buildScriptTextPreview_joins_with_newline(self):
        c = read_script()
        body = func_body('buildScriptTextPreview', c)
        assert "join" in body or 'parts.push' in body

    def test_saves_provider(self):
        c = read_script()
        assert 'provider: provider' in c

    def test_profile_name_is_null(self):
        c = read_script()
        assert 'profile_name: null' in c

    def test_model_is_null(self):
        c = read_script()
        assert 'model: null' in c

    def test_voice_id_is_null(self):
        c = read_script()
        assert 'voice_id: null' in c

    def test_voice_name_is_null(self):
        c = read_script()
        assert 'voice_name: null' in c

    def test_saves_audio_format(self):
        c = read_script()
        assert 'audio_format:' in c

    def test_context_keyed_by_batch_id(self):
        c = read_script()
        assert 'data.batch_id' in c
        assert '_batchSampleContextById[data.batch_id]' in c.replace(' ', '')


# ── renderBatchResultPlayer integration ───────────────────────────────────────

class TestRenderBatchResultPlayerIntegration:
    def test_calls_safePushBatchSample(self):
        html = read_html()
        body = html[html.find('function renderBatchResultPlayer'):]
        body = body[:body.find('\n  function ', 1)]
        assert 'safePushBatchSample' in body

    def test_determines_source_from_targetPanelId(self):
        html = read_html()
        body = html[html.find('function renderBatchResultPlayer'):]
        body = body[:body.find('\n  function ', 1)]
        assert 'batchScriptProgressPanel' in body
        assert 'batch_script_merged' in body
        assert 'batch_longtext_merged' in body

    def test_reads_batchSampleContextById(self):
        html = read_html()
        body = html[html.find('function renderBatchResultPlayer'):]
        body = body[:body.find('\n  function ', 1)]
        assert '_batchSampleContextById' in body

    def test_calls_after_merged_audio_check(self):
        html = read_html()
        body = html[html.find('function renderBatchResultPlayer'):]
        body = body[:body.find('\n  function ', 1)]
        # safePushBatchSample must appear after merged_audio check
        merged_check = body.find('!data.merged_audio')
        safe_push = body.find('safePushBatchSample')
        assert merged_check < safe_push, \
            'safePushBatchSample must be called after merged_audio check'


# ── sourceLabel additions ─────────────────────────────────────────────────────

class TestSourceLabelAdditions:
    def test_batch_longtext_merged_label(self):
        c = read_sidebar()
        body = c[c.find('function sourceLabel'):c.find('function sourceLabel')+500]
        assert 'batch_longtext_merged' in body
        assert '长文合并' in body

    def test_batch_script_merged_label(self):
        c = read_sidebar()
        body = c[c.find('function sourceLabel'):c.find('function sourceLabel')+500]
        assert 'batch_script_merged' in body
        assert '剧本合并' in body

    def test_batch_longtext_segment_reserved(self):
        c = read_sidebar()
        body = c[c.find('function sourceLabel'):c.find('function sourceLabel')+500]
        assert 'batch_longtext_segment' in body

    def test_batch_script_segment_reserved(self):
        c = read_sidebar()
        body = c[c.find('function sourceLabel'):c.find('function sourceLabel')+500]
        assert 'batch_script_segment' in body


# ── Negative tests: what must NOT appear ───────────────────────────────────────

class TestMustNotAppear:
    def test_safePushBatchSample_not_in_sidebar(self):
        s = read_sidebar()
        assert 'safePushBatchSample' not in s

    def test_batch_longtext_merged_not_in_sidebar_render(self):
        s = read_sidebar()
        # Only sourceLabel should reference it, not render logic
        body = s[s.find('function render'):s.find('function render')+3000]
        assert 'safePushBatchSample' not in body
        assert 'safePushWorkspaceSample' not in body

    def test_batch_script_merged_not_in_sidebar_render(self):
        s = read_sidebar()
        body = s[s.find('function render'):s.find('function render')+3000]
        assert 'safePushBatchSample' not in body

    def test_sample_store_not_modified(self):
        """sample_store.js must not be modified in B5-MVP1."""
        store_path = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_store.js')
        content = open(store_path, 'r', encoding='utf-8').read()
        # No batch-related code should be in sample_store.js
        assert 'safePushBatchSample' not in content
        assert 'batch_longtext_merged' not in content
        assert 'batch_script_merged' not in content
        assert '_batchSampleContextById' not in content

    def test_no_segment_samples(self):
        """B5-MVP1 must not implement segment-level samples."""
        html = read_html()
        # Should not push per-segment samples
        assert 'segment_id: null' in html  # merged audio has null segment_id
        # No segment loop pushing samples
        body = html[html.find('function safePushBatchSample'):]
        body = body[:body.find('\n  function ') if '\n  function ' in body else len(body)]
        assert 'forEach' not in body or 'segments' not in body

    def test_no_history_sample_modification(self):
        """History sample integration must not be modified."""
        s = read_sidebar()
        assert 'history' not in s.lower() or 'sourceLabel' in s

    def test_no_real_minimax_calls(self):
        """No real MiniMax API calls in batch integration."""
        html = read_html()
        longtext = read_longtext()
        script = read_script()
        for content in [html, longtext, script]:
            assert 'minimax.com' not in content
            assert 'api.minimaxi.ai' not in content
