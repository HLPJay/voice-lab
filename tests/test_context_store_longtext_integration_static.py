"""
test_context_store_longtext_integration_static.py

P14-CONTEXT-B2: Integration tests for longtext context save and detail view.
Verifies:
- context_store.js is loaded in index.html before sample_sidebar.js
- batch_longtext.js calls ContextStore.pushContext with correct fields
- safePushBatchSample passes context_id to SampleStore
- SampleStore.normalizeSample accepts context_id
- SampleSidebar has detail button and showSampleDetail function
- Detail view renders full_text with proper escaping
- No fetch calls, no localStorage writes from sidebar detail
"""

import os
import re
import subprocess
import json
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')
BATCH_LONGTEXT_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'batch_longtext.js')
SAMPLE_STORE_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_store.js')
SAMPLE_SIDEBAR_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_sidebar.js')
CONTEXT_STORE_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'context_store.js')


def read(path):
    return open(path, 'r', encoding='utf-8').read()


# ── Node.js helpers ──────────────────────────────────────────────────────────

def _node_available():
    try:
        subprocess.run(['node', '--version'], capture_output=True, timeout=10)
        return True
    except Exception:
        return False


def _run_node(script):
    result = subprocess.run(
        ['node', '-e', script],
        capture_output=True, encoding='utf-8', errors='replace', timeout=30,
        cwd=REPO_ROOT
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


# ── index.html tests ────────────────────────────────────────────────────────

class TestIndexHtmlIntegration:
    """Verifies index.html loads context_store.js correctly."""

    def test_context_store_js_loaded_in_index_html(self):
        content = read(INDEX_HTML_PATH)
        assert '/static/js/context_store.js' in content, \
            'context_store.js must be loaded in index.html'

    def test_context_store_before_sample_sidebar(self):
        content = read(INDEX_HTML_PATH)
        idx_context = content.find('/static/js/context_store.js')
        idx_sidebar = content.find('/static/js/sample_sidebar.js')
        assert idx_context >= 0, 'context_store.js must be present'
        assert idx_sidebar >= 0, 'sample_sidebar.js must be present'
        assert idx_context < idx_sidebar, \
            'context_store.js must load before sample_sidebar.js'

    def test_safePushBatchSample_passes_context_id(self):
        content = read(INDEX_HTML_PATH)
        # Must have context_id: extra.context_id || null inside safePushBatchSample
        # Find the function
        idx = content.find('function safePushBatchSample')
        assert idx >= 0, 'safePushBatchSample must exist'
        # Extract function body (rough: next 2000 chars)
        func_body = content[idx:idx + 2000]
        assert 'context_id:' in func_body, \
            'safePushBatchSample must pass context_id to pushSample'
        assert re.search(r'context_id\s*:\s*extra\.context_id\s*\|\|\s*null', func_body), \
            'context_id must read from extra.context_id'

    def test_safePushBatchSample_reads_from_extra_context_id(self):
        content = read(INDEX_HTML_PATH)
        idx = content.find('function safePushBatchSample')
        func_body = content[idx:idx + 2000]
        # Must use extra.context_id not hardcoded
        assert 'extra.context_id' in func_body, \
            'safePushBatchSample must read extra.context_id'


# ── batch_longtext.js tests ─────────────────────────────────────────────────

class TestBatchLongtextIntegration:
    """Verifies batch_longtext.js calls ContextStore.pushContext correctly."""

    def test_calls_context_store_pushContext(self):
        content = read(BATCH_LONGTEXT_PATH)
        assert 'ContextStore.pushContext' in content or 'ContextStore &&' in content, \
            'batch_longtext.js must call ContextStore.pushContext'

    def test_pushContext_context_id_is_batch_id(self):
        content = read(BATCH_LONGTEXT_PATH)
        # Find pushContext call body
        idx = content.find('pushContext')
        assert idx >= 0, 'pushContext call must exist'
        # Next 800 chars after pushContext
        call_body = content[idx:idx + 800]
        assert 'context_id:' in call_body, \
            'pushContext must pass context_id'
        assert 'data.batch_id' in call_body, \
            'context_id must be data.batch_id'

    def test_pushContext_type_is_longtext(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert re.search(r"type\s*:\s*'longtext'", call_body), \
            'type must be "longtext"'

    def test_pushContext_source_is_batch_longtext_merged(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'batch_longtext_merged' in call_body, \
            'source must be "batch_longtext_merged"'

    def test_pushContext_saves_full_text(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'full_text:' in call_body, \
            'pushContext must save full_text'

    def test_pushContext_saves_provider(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert re.search(r"provider\s*:\s*provider", call_body), \
            'pushContext must save provider'

    def test_pushContext_saves_profile_id(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'profile_id:' in call_body, \
            'pushContext must save profile_id'

    def test_pushContext_saves_segment_strategy(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'segment_strategy:' in call_body, \
            'pushContext must save segment_strategy'

    def test_pushContext_saves_max_segment_chars(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'max_segment_chars:' in call_body, \
            'pushContext must save max_segment_chars'

    def test_pushContext_saves_silence_between_ms(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'silence_between_ms:' in call_body, \
            'pushContext must save silence_between_ms'

    def test_pushContext_saves_output_format_and_audio_format(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'output_format:' in call_body, \
            'pushContext must save output_format'
        assert 'audio_format:' in call_body, \
            'pushContext must save audio_format'

    def test_pushContext_saves_need_subtitle(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'need_subtitle:' in call_body, \
            'pushContext must save need_subtitle'

    def test_pushContext_saves_params(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'params:' in call_body, \
            'pushContext must save params'

    def test_pushContext_saves_batch_id(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('pushContext')
        call_body = content[idx:idx + 800]
        assert 'batch_id:' in call_body, \
            'pushContext must save batch_id'

    def test_pushContext_has_try_catch(self):
        content = read(BATCH_LONGTEXT_PATH)
        # Find the block that wraps ContextStore.pushContext
        idx = content.find('ContextStore.pushContext')
        assert idx >= 0
        # Find the try block before it
        search_region = content[max(0, idx - 400):idx + 100]
        assert 'try' in search_region or 'try{' in search_region or 'try {' in search_region, \
            'ContextStore.pushContext call must be inside try/catch'

    def test_context_save_not_call_fetch(self):
        content = read(BATCH_LONGTEXT_PATH)
        # The ContextStore.pushContext block should not contain fetch calls
        idx = content.find('ContextStore.pushContext')
        if idx >= 0:
            # Check surrounding 500 chars
            region = content[max(0, idx - 300):idx + 500]
            assert 'fetch(' not in region, \
                'ContextStore.pushContext region must not call fetch'
            assert '/api/' not in region, \
                'ContextStore.pushContext region must not call API endpoints'

    def test_context_save_not_modify_request_payload(self):
        content = read(BATCH_LONGTEXT_PATH)
        # The ContextStore.pushContext block should be AFTER the guardedJsonFetch call.
        # Verify guardedJsonFetch still has the correct payload by checking the actual call.
        # We look for the fetch call that has mode:'longtext' in its options object.
        idx = content.find("mode: 'longtext'")
        assert idx >= 0, "mode:'longtext' payload key must still be present"
        # This mode: 'longtext' should be inside the options argument of guardedJsonFetch
        # Verify it's inside the {...} argument list (search backward to find guardedJsonFetch call)
        search_region = content[max(0, idx - 600):idx + 100]
        assert 'guardedJsonFetch' in search_region, \
            "mode:'longtext' must be in the guardedJsonFetch options object"

    def test_context_id_written_to_batchSampleContextById(self):
        content = read(BATCH_LONGTEXT_PATH)
        idx = content.find('ContextStore.pushContext')
        assert idx >= 0
        region = content[idx:idx + 600]
        assert 'context_id' in region, \
            'context_id must be saved to _batchSampleContextById after pushContext'


# ── sample_store.js tests ───────────────────────────────────────────────────

class TestSampleStoreIntegration:
    """Verifies SampleStore.normalizeSample accepts context_id."""

    def test_normalizeSample_preserves_context_id(self):
        content = read(SAMPLE_STORE_PATH)
        assert 'context_id:' in content, \
            'normalizeSample must have context_id field'

    def test_normalizeSample_context_id_from_input(self):
        content = read(SAMPLE_STORE_PATH)
        idx = content.find('context_id:')
        field_body = content[idx:idx + 100]
        assert 'input.context_id' in field_body, \
            'context_id must come from input.context_id'

    def test_normalizeSample_context_id_null_when_missing(self):
        content = read(SAMPLE_STORE_PATH)
        idx = content.find('context_id:')
        field_body = content[idx:idx + 100]
        assert 'null' in field_body, \
            'context_id must be null when not provided'

    def test_sample_store_js_not_reference_context_store(self):
        content = read(SAMPLE_STORE_PATH)
        lower = content.lower()
        forbidden = ['contextstore', 'context_store', 'context store']
        found = [kw for kw in forbidden if kw in lower]
        assert not found, \
            f'sample_store.js must not reference ContextStore: {found}'


# ── sample_sidebar.js tests ────────────────────────────────────────────────

class TestSampleSidebarIntegration:
    """Verifies SampleSidebar has detail view functionality."""

    def test_sidebar_has_detail_action_button(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'sample-btn-detail' in content, \
            'sample_sidebar.js must have sample-btn-detail class'

    def test_detail_button_only_when_context_id_exists(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        # The detail button should be conditionally added only when sample.context_id exists
        idx = content.find('sample-btn-detail')
        assert idx >= 0
        # Check surrounding 200 chars for the conditional
        region = content[max(0, idx - 200):idx + 100]
        assert 'context_id' in region, \
            'detail button must be added only when sample.context_id exists'

    def test_sidebar_calls_context_store_getContext(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'ContextStore.getContext' in content, \
            'sample_sidebar.js must call ContextStore.getContext'

    def test_showSampleDetail_function_exists(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        assert re.search(r'function showSampleDetail\s*\(', content), \
            'showSampleDetail function must exist'

    def test_showSampleDetail_exposed_on_window(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        # window.SampleSidebar.showSampleDetail must be exposed
        assert re.search(r'showSampleDetail\s*:', content), \
            'showSampleDetail must be exposed on window.SampleSidebar'

    def test_detail_escape_full_text(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        # showSampleDetail should escape full_text with esc()
        # Look for fullTextEsc assignment which shows proper escaping
        assert 'fullTextEsc' in content, \
            'showSampleDetail must create escaped full_text variable (fullTextEsc)'
        idx = content.find('fullTextEsc')
        region = content[max(0, idx - 50):idx + 100]
        assert 'esc(' in region, \
            'fullTextEsc must be assigned from esc() call'

    def test_detail_no_fetch(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        idx = content.find('showSampleDetail')
        func_body = content[idx:idx + 2000]
        assert 'fetch(' not in func_body, \
            'showSampleDetail must not call fetch'
        assert '/api/' not in func_body, \
            'showSampleDetail must not call API endpoints'

    def test_detail_no_localStorage_write(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        idx = content.find('showSampleDetail')
        func_body = content[idx:idx + 2000]
        # Should not call localStorage.setItem or safeSetItem
        assert 'localStorage.setItem' not in func_body, \
            'showSampleDetail must not write to localStorage'

    def test_detail_no_fill_back(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        idx = content.find('showSampleDetail')
        assert idx >= 0, 'showSampleDetail must exist'
        # Extract the exact function body using brace counting
        depth = 0
        end = idx
        for i in range(idx, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = content[idx:end]
        # showSampleDetail should NOT call fillTextInput or modify DOM for fill
        # It should only display, not restore
        assert 'fillTextInput' not in func_body, \
            'showSampleDetail must not implement fill/restore'


# ── Behavioral tests (Node.js) ──────────────────────────────────────────────

@pytest.mark.skipif(
    not _node_available(),
    reason='Node.js not available; behavioural tests skipped'
)
class TestBehavioralIntegration:
    """Execute integrated modules to verify runtime behavior."""

    def _load_both_modules(self):
        cs_js = read(CONTEXT_STORE_PATH)
        ss_js = read(SAMPLE_STORE_PATH)
        combined = '''
var window = { crypto: { randomUUID: function() { return require('crypto').randomUUID(); } } };
var localStorage = { _data: {}, getItem: function(k){return this._data[k]||null;}, setItem: function(k,v){this._data[k]=v;}, removeItem: function(k){delete this._data[k];} };
''' + cs_js + '\n' + ss_js
        return combined

    def _eval(self, expr, extra_js=''):
        combined = self._load_both_modules() + '\n' + extra_js + '\nconsole.log(JSON.stringify(' + expr + '))'
        stdout, stderr, rc = _run_node(combined)
        return stdout.strip(), stderr.strip(), rc

    def test_sample_store_preserves_context_id_roundtrip(self):
        stdout, stderr, rc = self._eval(
            '(function() { var s = window.SampleStore.pushSample({source:"test",text_preview:"hello",context_id:"test-ctx-123"}); var all = window.SampleStore.getSamples(); var found = all.find(function(x){return x.sample_id === s.sample_id;}); return {hasCtxId: !!found && found.context_id === "test-ctx-123", ctxId: found ? found.context_id : null}; })()'
        )
        assert rc == 0, f'Node error: {stderr}'
        try:
            result = json.loads(stdout)
        except:
            pytest.fail(f'Could not parse JSON: {stdout}')
        assert result['hasCtxId'], f"context_id must round-trip through SampleStore; got {result}"

    def test_sample_store_context_id_null_when_not_provided(self):
        stdout, stderr, rc = self._eval(
            '(function() { var s = window.SampleStore.pushSample({source:"test",text_preview:"hello"}); return {ctxId: s.context_id}; })()'
        )
        assert rc == 0, f'Node error: {stderr}'
        try:
            result = json.loads(stdout)
        except:
            pytest.fail(f'Could not parse JSON: {stdout}')
        assert result['ctxId'] is None, f"context_id must be null when not provided; got {result['ctxId']}"

    def test_context_store_push_and_get_longtext(self):
        stdout, stderr, rc = self._eval(
            '(function() { '
            'var ctx = window.ContextStore.pushContext({context_id:"batch-abc",type:"longtext",source:"batch_longtext_merged",full_text:"这是一段测试长文本。",provider:"minimax",profile_id:"prof-1",segment_strategy:"auto",max_segment_chars:2000,silence_between_ms:300,output_format:"hex",audio_format:"mp3",need_subtitle:false,params:{speed:1.0},batch_id:"batch-abc"}); '
            'var retrieved = window.ContextStore.getContext("batch-abc"); '
            'return {pushed: !!ctx, retrieved: !!retrieved, fullText: retrieved ? retrieved.full_text : null, type: retrieved ? retrieved.type : null}; '
            '})()'
        )
        assert rc == 0, f'Node error: {stderr}'
        try:
            result = json.loads(stdout)
        except:
            pytest.fail(f'Could not parse JSON: {stdout}')
        assert result['pushed'], 'pushContext must succeed'
        assert result['retrieved'], 'getContext must retrieve the saved context'
        assert result['fullText'] == '这是一段测试长文本。', f"full_text must round-trip; got {result['fullText']}"
        assert result['type'] == 'longtext', f"type must be longtext; got {result['type']}"

    def test_context_store_upsert_updates_existing(self):
        stdout, stderr, rc = self._eval(
            '(function() { '
            'window.ContextStore.pushContext({context_id:"batch-upsert",type:"longtext",source:"batch_longtext_merged",full_text:"原始文本",provider:"minimax",batch_id:"batch-upsert"}); '
            'window.ContextStore.pushContext({context_id:"batch-upsert",type:"longtext",source:"batch_longtext_merged",full_text:"更新后的文本",provider:"minimax",batch_id:"batch-upsert"}); '
            'var retrieved = window.ContextStore.getContext("batch-upsert"); '
            'return {count: window.ContextStore.getContexts().length, fullText: retrieved ? retrieved.full_text : null}; '
            '})()'
        )
        assert rc == 0, f'Node error: {stderr}'
        try:
            result = json.loads(stdout)
        except:
            pytest.fail(f'Could not parse JSON: {stdout}')
        assert result['count'] == 1, f"upsert must not increase count; got {result['count']}"
        assert result['fullText'] == '更新后的文本', f"upsert must update full_text; got {result['fullText']}"

    def test_sample_store_context_id_does_not_affect_sample_id(self):
        stdout, stderr, rc = self._eval(
            '(function() { '
            'window.SampleStore.clearSamples(); '
            'var s1 = window.SampleStore.pushSample({source:"test",text_preview:"a",context_id:"ctx-1"}); '
            'var s2 = window.SampleStore.pushSample({source:"test",text_preview:"b",context_id:"ctx-2"}); '
            'return {id1: s1.sample_id, id2: s2.sample_id, different: s1.sample_id !== s2.sample_id}; '
            '})()'
        )
        assert rc == 0, f'Node error: {stderr}'
        try:
            result = json.loads(stdout)
        except:
            pytest.fail(f'Could not parse JSON: {stdout}')
        assert result['different'], "sample_id must be unique even with different context_id"
