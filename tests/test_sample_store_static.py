"""
test_sample_store_static.py

B1: Static contract tests for sample_store.js
Verifies the JS module file contains correct exports, constants and safety properties
without executing browser-side code.
"""

import os
import re
import subprocess
import sys

import pytest


# Path relative to repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_STORE_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_store.js')


class TestSampleStoreStatic:
    """Part A: Static contract — read the JS file as text and assert facts."""

    def test_file_exists(self):
        assert os.path.isfile(SAMPLE_STORE_PATH), \
            f'sample_store.js not found at {SAMPLE_STORE_PATH}'

    def test_window_sample_store_exposed(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        assert 'window.SampleStore' in content, \
            'window.SampleStore must be defined'

    def test_all_six_public_methods_present(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        for method in ['pushSample', 'getSamples', 'deleteSample',
                       'clearSamples', 'normalizeSample', 'trimSamples']:
            # Allow "function pushSample" or "pushSample:" (object shorthand / alias)
            pattern = r'\b' + re.escape(method) + r'\b'
            assert re.search(pattern, content), \
                f'Method {method} not found in sample_store.js'

    def test_storage_key_constant(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        assert 'voice_lab_recent_samples_v1' in content, \
            'STORAGE_KEY constant voice_lab_recent_samples_v1 must be present'

    def test_max_samples_constant(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        assert 'MAX_SAMPLES' in content, \
            'MAX_SAMPLES constant must be present'
        assert re.search(r'MAX_SAMPLES\s*=\s*200\b', content), \
            'MAX_SAMPLES must equal 200'

    def test_text_preview_max_constant(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        assert 'TEXT_PREVIEW_MAX' in content, \
            'TEXT_PREVIEW_MAX constant must be present'
        assert re.search(r'TEXT_PREVIEW_MAX\s*=\s*100\b', content), \
            'TEXT_PREVIEW_MAX must equal 100'

    def test_text_preview_truncation(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        # Must use String() coercion before .substring
        assert re.search(r"String\s*\(\s*input\.text_preview", content), \
            'text_preview must be coerced with String() before truncation'

    def test_audio_format_allows_override(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        # audio_format should be "input.audio_format || 'mp3'" not hard-coded 'mp3'
        assert re.search(r"input\.audio_format\s*\|\|\s*'mp3'", content), \
            'audio_format must allow caller override; use input.audio_format || \'mp3\''

    def test_blob_url_rejection(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        assert "startsWith('blob:')" in content or 'indexOf' in content, \
            'download_url must reject blob: URLs'

    def test_no_recent_jobs(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        lower = content.lower()
        # JSDoc comments may mention recentJobs as a documented prohibition -- that is fine.
        # We detect all actual JS code forms that would read/write the recentJobs key.
        import re
        forbidden = [
            # localStorage / safeGetItem / safeSetItem forms
            (r"localstorage\s*\.\s*getitem\s*\(\s*['\"']recentjobs['\"]",
             "localStorage.getItem('recentJobs')"),
            (r"localstorage\s*\.\s*setitem\s*\(\s*['\"']recentjobs['\"]",
             "localStorage.setItem('recentJobs')"),
            (r"safegetitem\s*\(\s*['\"']recentjobs['\"]",
             "safeGetItem('recentJobs')"),
            (r"safesetitem\s*\(\s*['\"']recentjobs['\"]",
             "safeSetItem('recentJobs')"),
            # window.recentJobs property access
            (r"window\s*\.\s*recentjobs", 'window.recentJobs property'),
            # bracket-notation subscript with 'recentJobs' as the key
            (r"\[\s*['\"']recentjobs['\"]\s*\]",
             "bracket subscript ['recentJobs']"),
            # direct identifier reference recentJobs.something or recentJobs[...]
            (r"recentjobs\s*[.\[]", 'recentJobs identifier deref'),
        ]
        for pattern, label in forbidden:
            assert not re.search(pattern, lower),                 'sample_store.js must not access recentJobs (' + label + '); pattern: ' + pattern

    def test_no_backend_fetch(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        # Should not call any HTTP endpoint
        forbidden = ['fetch(', '/api/', 'XMLHttpRequest', 'axios', 'http://', 'https://']
        found = [kw for kw in forbidden if kw in content]
        assert not found, \
            f'Forbidden backend references found: {found}'

    def test_no_dom_dependencies(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        # Should not call document.getElementById, querySelector, etc.
        forbidden = ['document.getElementById', 'document.querySelector',
                     'document.createElement', '$(']
        found = [kw for kw in forbidden if kw in content]
        assert not found, \
            f'Forbidden DOM references found: {found}'

    def test_normalizeSample_has_context_id_field(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        assert 'context_id:' in content, \
            'normalizeSample must have context_id field'

    def test_normalizeSample_context_id_from_input(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        idx = content.find('context_id:')
        assert idx >= 0, 'context_id field must exist'
        field_region = content[idx:idx + 100]
        assert 'input.context_id' in field_region, \
            'context_id must read from input.context_id'

    def test_normalizeSample_context_id_null_fallback(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        idx = content.find('context_id:')
        field_region = content[idx:idx + 100]
        assert 'null' in field_region, \
            'context_id must default to null when missing'

    def test_no_context_store_reference(self):
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        lower = content.lower()
        forbidden = ['contextstore', 'context_store', 'context store']
        found = [kw for kw in forbidden if kw in lower]
        assert not found, \
            f'sample_store.js must not reference ContextStore: {found}'


# ── helpers ──────────────────────────────────────────────────────────

def _node_available():
    """Check if node is available on this system."""
    try:
        subprocess.run(
            ['node', '--version'],
            capture_output=True, timeout=10
        )
        return True
    except Exception:
        return False


def _run_node_check(script):
    """Execute node script, return (stdout, stderr, returncode)."""
    result = subprocess.run(
        ['node', '-e', script],
        capture_output=True, text=True, timeout=30,
        cwd=REPO_ROOT
    )
    return result.stdout, result.stderr, result.returncode


# ── Part B: Behavioural tests (Node.js, skip if node unavailable) ──


@pytest.mark.skipif(
    not _node_available(),
    reason='Node.js not available; behavioural tests skipped'
)
class TestSampleStoreBehavior:
    """Part B: Execute sample_store.js in Node.js with mocked globals."""

    def _load_js_module(self):
        """Load sample_store.js into Node vm with mocked window/localStorage."""
        js_content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        script = f"""
        (function() {{
            var window = {{ crypto: {{ randomUUID: function() {{ return 'test-uuid'; }} }} }};
            var localStorage = {{ _data: {{}}, getItem: function(k) {{ return this._data[k] || null; }}, setItem: function(k, v) {{ this._data[k] = v; }}, removeItem: function(k) {{ delete this._data[k]; }} }};
            {js_content}
            // expose for testing
            if (typeof global !== 'undefined') {{
                global._SampleStore = window.SampleStore;
                global._localStorage = localStorage;
            }} else if (typeof window !== 'undefined') {{
                window._SampleStore = window.SampleStore;
                window._localStorage = localStorage;
            }}
        }})();
        """
        return script

    def _eval_in_vm(self, expression):
        load = self._load_js_module()
        script = f"""
        {load}
        var _store = (typeof global !== 'undefined' ? global._SampleStore : window._SampleStore);
        var _ls = (typeof global !== 'undefined' ? global._localStorage : window._localStorage);
        var _key = 'voice_lab_recent_samples_v1';
        {expression}
        """
        stdout, stderr, rc = _run_node_check(script)
        return stdout.strip(), stderr.strip(), rc

    def test_push_sample_writes_local_storage(self):
        stdout, stderr, rc = self._eval_in_vm(
            "var s = _store.pushSample({ source: 'test', text_preview: 'hello world' });"
            "var stored = JSON.parse(_ls.getItem('voice_lab_recent_samples_v1'));"
            "console.log('stored_count:' + stored.length + ',first_id:' + (stored[0] && stored[0].sample_id ? 'ok' : 'missing'));"
        )
        assert rc == 0, f'Node error: {stderr}'
        assert 'stored_count:1' in stdout
        assert 'first_id:ok' in stdout

    def test_get_samples_returns_array(self):
        stdout, stderr, rc = self._eval_in_vm(
            "_store.clearSamples();"
            "var arr = _store.getSamples();"
            "console.log('isArray:' + Array.isArray(arr) + ',length:' + arr.length);"
        )
        assert rc == 0, f'Node error: {stderr}'
        assert 'isArray:true' in stdout

    def test_text_preview_truncated_at_100_chars(self):
        long_text = 'x' * 200
        stdout, stderr, rc = self._eval_in_vm(
            "_store.clearSamples();"
            "var s = _store.pushSample({ source: 'test', text_preview: '" + long_text + "' });"
            "console.log('textLen:' + s.text_preview.length + ',c99:' + s.text_preview.charCodeAt(99) + ',c100:' + s.text_preview.charCodeAt(100));"
        )
        assert rc == 0, f'Node error: {stderr}'
        # 100 chars + ellipsis = 101
        assert 'textLen:101' in stdout
        # charCode 99=120('x'), charCode 100=8230(ELLIPSIS U+2026)
        assert 'c99:120' in stdout and 'c100:8230' in stdout

    def test_200_plus_samples_trimmed_to_200(self):
        stdout, stderr, rc = self._eval_in_vm("""
        _store.clearSamples();
        for (var i = 0; i < 220; i++) {{
            _store.pushSample({ source: 'test', text_preview: 'item' + i });
        }}
        var arr = _store.getSamples();
        console.log(JSON.stringify({ count: arr.length }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"count":200' in stdout

    def test_malformed_json_returns_empty_array(self):
        # Inject malformed JSON directly into localStorage
        stdout, stderr, rc = self._eval_in_vm("""
        _ls.setItem('voice_lab_recent_samples_v1', 'not-valid-json{{');
        var arr = _store.getSamples();
        console.log(JSON.stringify({ isArray: Array.isArray(arr), length: arr.length }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"isArray":true' in stdout
        assert '"length":0' in stdout

    def test_delete_sample_removes_entry(self):
        stdout, stderr, rc = self._eval_in_vm("""
        _store.clearSamples();
        var s = _store.pushSample({ source: 'test', text_preview: 'to-delete' });
        var id = s.sample_id;
        var before = _store.getSamples().length;
        _store.deleteSample(id);
        var after = _store.getSamples().length;
        console.log(JSON.stringify({ before: before, after: after }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"before":1' in stdout
        assert '"after":0' in stdout

    def test_clear_samples_wipes_storage(self):
        stdout, stderr, rc = self._eval_in_vm("""
        _store.pushSample({ source: 'test', text_preview: 'item1' });
        _store.pushSample({ source: 'test', text_preview: 'item2' });
        _store.clearSamples();
        var arr = _store.getSamples();
        console.log(JSON.stringify({ length: arr.length }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"length":0' in stdout

    def test_blob_url_set_to_null(self):
        stdout, stderr, rc = self._eval_in_vm("""
        var s = _store.normalizeSample({
            source: 'test',
            text_preview: 'blob test',
            download_url: 'blob:http://localhost:3000/abc123'
        });
        console.log(JSON.stringify({ downloadUrl: s.download_url }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"downloadUrl":null' in stdout

    def test_audio_format_can_be_overridden(self):
        stdout, stderr, rc = self._eval_in_vm("""
        var s = _store.normalizeSample({
            source: 'test',
            text_preview: 'wav test',
            audio_format: 'wav'
        });
        console.log(JSON.stringify({ audioFormat: s.audio_format }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"audioFormat":"wav"' in stdout

    def test_no_recent_jobs_written(self):
        # Check that recentJobs key is NOT written; our own key contains 'recent' so we
        # specifically check for 'recentJobs' which is the forbidden key
        stdout, stderr, rc = self._eval_in_vm(
            "_store.pushSample({ source: 'test', text_preview: 'test' });"
            "var keys = Object.keys(_ls._data);"
            "var hasRecentJobs = keys.indexOf('recentJobs') !== -1 || keys.indexOf('recentJobs_v1') !== -1 || keys.indexOf('recentJobs_v2') !== -1;"
            "console.log('keys:' + JSON.stringify(keys) + ',hasRecentJobs:' + hasRecentJobs);"
        )
        assert rc == 0, f'Node error: {stderr}'
        assert 'hasRecentJobs:false' in stdout

    def test_get_samples_returns_created_at_desc_order(self):
        # Write out-of-order data directly to localStorage, then verify getSamples sorts
        stdout, stderr, rc = self._eval_in_vm(
            "_ls.setItem('voice_lab_recent_samples_v1', JSON.stringify(["
            "{ sample_id: 'old', created_at: '2026-01-01T00:00:00.000Z', text_preview: 'old' },"
            "{ sample_id: 'new', created_at: '2026-03-01T00:00:00.000Z', text_preview: 'new' },"
            "{ sample_id: 'mid', created_at: '2026-02-01T00:00:00.000Z', text_preview: 'mid' }"
            "]));"
            "var arr = _store.getSamples();"
            "console.log('order:' + arr.map(function(s){return s.sample_id;}).join(','));"
        )
        assert rc == 0, f'Node error: {stderr}'
        # Must be sorted newest-first: new, mid, old
        assert 'order:new,mid,old' in stdout

    def test_get_samples_trims_existing_storage_to_200(self):
        # Write 220 items directly into mocked localStorage (bypass pushSample),
        # then verify getSamples() caps the result at 200.
        stdout, stderr, rc = self._eval_in_vm("""
        var items = [];
        for (var i = 0; i < 220; i++) {
            items.push({sample_id: "s" + i, created_at: "2026-01-01T00:00:" + String(i).padStart(2,"0") + ":00.000Z", text_preview: "item" + i});
        }
        _ls.setItem("voice_lab_recent_samples_v1", JSON.stringify(items));
        var arr = _store.getSamples();
        console.log("count:" + arr.length);
        """)
        assert rc == 0, f"Node error: {stderr}"
        assert "count:200" in stdout

    def test_get_samples_does_not_write_back_to_storage(self):
        # Verify that getSamples() reads but never writes to localStorage.
        stdout, stderr, rc = self._eval_in_vm("""
        var initial = [{sample_id:"a",created_at:"2026-01-01T00:00:01.000Z",text_preview:"alpha"},
                       {sample_id:"b",created_at:"2026-01-01T00:00:02.000Z",text_preview:"beta"}];
        _ls.setItem("voice_lab_recent_samples_v1", JSON.stringify(initial));
        var rawBefore = _ls.getItem("voice_lab_recent_samples_v1");
        _store.getSamples();
        var rawAfter = _ls.getItem("voice_lab_recent_samples_v1");
        console.log("same:" + (rawBefore === rawAfter));
        """)
        assert rc == 0, f"Node error: {stderr}"
        assert "same:true" in stdout

    def test_context_id_round_trip(self):
        stdout, stderr, rc = self._eval_in_vm("""
        _store.clearSamples();
        var s = _store.pushSample({ source: 'test', text_preview: 'ctx-test', context_id: 'my-ctx-456' });
        var retrieved = _store.getSamples().find(function(x){ return x.sample_id === s.sample_id; });
        console.log(JSON.stringify({ stored: retrieved ? retrieved.context_id : null }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"stored":"my-ctx-456"' in stdout, \
            'context_id must round-trip through pushSample/getSamples'

    def test_context_id_null_when_not_provided(self):
        stdout, stderr, rc = self._eval_in_vm("""
        _store.clearSamples();
        var s = _store.pushSample({ source: 'test', text_preview: 'no-ctx' });
        console.log(JSON.stringify({ ctxId: s.context_id }));
        """)
        assert rc == 0, f'Node error: {stderr}'
        assert '"ctxId":null' in stdout, \
            'context_id must be null when not provided'

    def test_context_id_does_not_affect_sample_id_generation(self):
        # Verify that context_id is not used in the sample_id generation logic.
        # We test this by checking the normalizeSample source code does not reference
        # input.context_id when generating sample_id.
        content = open(SAMPLE_STORE_PATH, 'r', encoding='utf-8').read()
        # Find the normalizeSample function body
        idx = content.find('function normalizeSample')
        func_body = content[idx:idx + 1500]
        # sample_id generation should use sample_id or crypto.randomUUID / Date.now
        # It should NOT incorporate context_id
        sample_id_line = ''
        for line in func_body.split('\n'):
            if 'sample_id:' in line:
                sample_id_line = line
                break
        assert 'context_id' not in sample_id_line, \
            'sample_id generation must not reference context_id: ' + sample_id_line
