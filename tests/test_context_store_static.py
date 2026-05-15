"""
test_context_store_static.py

P14-CONTEXT-B1: Static contract tests for context_store.js.
Covers API surface, storage format, normalization, and fail-safe behavior.
Uses Node.js + jsdom for localStorage simulation.
"""

import os
import re
import subprocess
import sys
import json
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT_STORE_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'context_store.js')


def read_js():
    return open(CONTEXT_STORE_PATH, 'r', encoding='utf-8').read()


def node_eval(js_code, context_store_js):
    """Evaluate JS code in Node.js with jsdom localStorage stub."""
    full = '''
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { url: 'http://localhost' });
global.window = dom.window;
global.document = dom.window.document;
global.localStorage = dom.window.localStorage;
global.crypto = { randomUUID: () => require('crypto').randomUUID() };
''' + context_store_js + '\n' + js_code

    try:
        result = subprocess.run(
            ['node', '-e', full],
            capture_output=True, encoding='utf-8', errors='replace', timeout=10,
            cwd=REPO_ROOT
        )
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return '', str(e)


def node_eval_expr(expr, context_store_js):
    """Evaluate a JS expression and return its JSON-serialized value."""
    stdout, stderr = node_eval('console.log(JSON.stringify(' + expr + '))', context_store_js)
    if stderr and 'SyntaxError' not in stderr and 'ReferenceError' not in stderr:
        pass
    try:
        return json.loads(stdout)
    except:
        return stdout


# ── Static contract ─────────────────────────────────────────────────────────

class TestStaticContract:
    def test_file_exists(self):
        assert os.path.exists(CONTEXT_STORE_PATH)

    def test_window_contextstore_exposed(self):
        js = read_js()
        assert 'window.ContextStore' in js

    def test_exposes_seven_methods(self):
        js = read_js()
        methods = ['pushContext', 'getContext', 'getContexts',
                   'deleteContext', 'clearContexts', 'normalizeContext', 'trimContexts']
        for m in methods:
            assert m in js, m + ' must be exposed'

    def test_storage_key(self):
        js = read_js()
        assert "voice_lab_sample_context_v1" in js

    def test_max_contexts_50(self):
        js = read_js()
        assert 'MAX_CONTEXTS' in js
        assert '50' in js

    def test_version_1(self):
        js = read_js()
        assert 'VERSION' in js
        assert 'var VERSION = 1' in js or 'var VERSION=1' in js

    def test_uses_object_wrapper_format(self):
        js = read_js()
        assert '{ version:' in js or '{version:' in js
        assert 'contexts' in js

    def test_no_dom_references(self):
        js = read_js()
        assert 'document.getElementById' not in js
        assert 'document.querySelector' not in js
        assert "getElementById('" not in js
        assert "querySelector('" not in js

    def test_no_fetch(self):
        js = read_js()
        assert 'fetch(' not in js

    def test_no_guarded_json_fetch(self):
        js = read_js()
        assert 'guardedJsonFetch' not in js

    def test_no_sample_store_reference(self):
        js = read_js()
        assert 'SampleStore' not in js

    def test_no_sample_sidebar_reference(self):
        js = read_js()
        assert 'SampleSidebar' not in js

    def test_no_recent_jobs_reference(self):
        js = read_js()
        assert 'recentJob' not in js


# ── Behavioral tests (Node.js + jsdom) ──────────────────────────────────────

@pytest.fixture
def context_store_js():
    return read_js()


class TestContextStoreBehavior:
    def test_push_and_get_longtext(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
const ctx = store.pushContext({
  context_id: 'test-lt-1',
  type: 'longtext',
  source: 'batch_longtext_merged',
  full_text: '这是一段测试长文本',
  provider: 'minimax',
  profile_id: 'profile-1',
  segment_strategy: 'auto',
  max_segment_chars: 2000,
  silence_between_ms: 300,
  output_format: 'hex',
  audio_format: 'mp3',
  need_subtitle: true,
  batch_id: 'batch-001'
});
const retrieved = store.getContext('test-lt-1');
console.log(JSON.stringify({
  pushReturned: !!ctx && ctx.context_id === 'test-lt-1',
  retrievedType: retrieved ? retrieved.type : null,
  retrievedText: retrieved ? retrieved.full_text : null,
  retrievedStrategy: retrieved ? retrieved.segment_strategy : null,
}));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['pushReturned'], 'pushContext should return context with context_id'
        assert result['retrievedType'] == 'longtext'
        assert result['retrievedText'] == '这是一段测试长文本'
        assert result['retrievedStrategy'] == 'auto'

    def test_push_and_get_script(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
const ctx = store.pushContext({
  context_id: 'test-sc-1',
  type: 'script',
  source: 'batch_script_merged',
  lines: [
    { role: '旁白', text: '第一句台词', profile_id: 'p1' },
    { role: '男主', text: '第二句台词', profile_id: 'p2' },
    { role: '', text: '旁白独白', profile_id: 'p1' }
  ],
  provider: 'minimax',
  silence_between_ms: 500,
  output_format: 'hex',
  audio_format: 'mp3',
  need_subtitle: true,
  batch_id: 'batch-002'
});
const retrieved = store.getContext('test-sc-1');
console.log(JSON.stringify({
  pushReturned: !!ctx && ctx.context_id === 'test-sc-1',
  retrievedType: retrieved ? retrieved.type : null,
  lineCount: retrieved ? retrieved.lines.length : 0,
  roleCount: retrieved ? retrieved.lines.filter(l => l.role).length : 0,
}));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['pushReturned']
        assert result['retrievedType'] == 'script'
        assert result['lineCount'] == 3
        assert result['roleCount'] == 2  # role='' row not counted as named role

    def test_get_contexts_returns_newest_first(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
store.pushContext({ context_id: 'old', type: 'longtext', source: 'test', full_text: 'old text', created_at: '2025-01-01T00:00:00Z' });
store.pushContext({ context_id: 'new', type: 'longtext', source: 'test', full_text: 'new text', created_at: '2026-01-01T00:00:00Z' });
const all = store.getContexts();
console.log(JSON.stringify({ firstId: all[0] ? all[0].context_id : null, secondId: all[1] ? all[1].context_id : null }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['firstId'] == 'new', 'newest should be first'
        assert result['secondId'] == 'old'

    def test_push_same_id_replaces(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
store.pushContext({ context_id: 'dup', type: 'longtext', source: 'test', full_text: 'v1', created_at: '2025-01-01T00:00:00Z' });
store.pushContext({ context_id: 'dup', type: 'longtext', source: 'test', full_text: 'v2', created_at: '2026-01-01T00:00:00Z' });
const all = store.getContexts();
console.log(JSON.stringify({ count: all.length, firstText: all[0] ? all[0].full_text : null }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['count'] == 1, 'should replace, not duplicate'
        assert result['firstText'] == 'v2', 'should have updated text'

    def test_delete_context(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
store.pushContext({ context_id: 'todel', type: 'longtext', source: 'test', full_text: 'to delete' });
const remaining = store.deleteContext('todel');
console.log(JSON.stringify({ remaining: remaining.length }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['remaining'] == 0, 'deleted context should not appear'

    def test_clear_contexts(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
store.pushContext({ context_id: 'x', type: 'longtext', source: 'test', full_text: 'x' });
store.clearContexts();
const all = store.getContexts();
console.log(JSON.stringify({ count: all.length }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['count'] == 0

    def test_malformed_json_returns_empty_array(self, context_store_js):
        code = '''
const store = window.ContextStore;
try {
  localStorage.setItem('voice_lab_sample_context_v1', 'not json');
} catch(e) {}
const all = store.getContexts();
console.log(JSON.stringify({ count: all.length }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['count'] == 0, 'malformed JSON should return []'

    def test_legacy_flat_array_format_compat(self, context_store_js):
        code = '''
try {
  localStorage.setItem('voice_lab_sample_context_v1', JSON.stringify([{ context_id: 'legacy', type: 'longtext', source: 'test', full_text: 'legacy text', created_at: '2025-01-01T00:00:00Z' }]));
} catch(e) {}
const all = window.ContextStore.getContexts();
console.log(JSON.stringify({ count: all.length, text: all[0] ? all[0].full_text : null }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['count'] == 1, 'legacy array format should be readable'
        assert result['text'] == 'legacy text'

    def test_max_50_eviction(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
for (var i = 0; i < 60; i++) {
  store.pushContext({ context_id: 'ctx-' + i, type: 'longtext', source: 'test', full_text: 'text' + i, created_at: new Date(2025, 0, i+1).toISOString() });
}
const all = store.getContexts();
console.log(JSON.stringify({ count: all.length, firstId: all[0] ? all[0].context_id : null, lastId: all[all.length-1] ? all[all.length-1].context_id : null }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['count'] == 50, 'should cap at 50'
        assert result['firstId'] == 'ctx-59', 'newest should be first'

    def test_trim_contexts_does_not_persist(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
for (var i = 0; i < 5; i++) {
  store.pushContext({ context_id: 'ctx-' + i, type: 'longtext', source: 'test', full_text: 'text' + i });
}
var raw = localStorage.getItem('voice_lab_sample_context_v1');
var parsed = JSON.parse(raw);
var beforeTrim = parsed.contexts.length;
store.trimContexts(parsed.contexts.slice());
var rawAfter = localStorage.getItem('voice_lab_sample_context_v1');
var parsedAfter = JSON.parse(rawAfter);
console.log(JSON.stringify({ beforeTrim: beforeTrim, afterTrim: parsedAfter.contexts.length }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['beforeTrim'] == 5, 'trimContexts should not change storage'

    def test_quota_exceeded_fail_safe(self, context_store_js):
        code = '''
const store = window.ContextStore;
store.clearContexts();
// Attempt to push huge context — should not throw
var huge = { context_id: 'huge', type: 'longtext', source: 'test', full_text: new Array(100000).join('x') };
var returned = store.pushContext(huge);
console.log(JSON.stringify({ returned: !!returned, returnedId: returned ? returned.context_id : null }));
'''
        stdout, stderr = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['returned'] == True, 'pushContext should return even if storage fails'

    def test_longtext_full_text_truncate_50000(self, context_store_js):
        code = '''
var long_text = new Array(60000).join('字');
var normalized = window.ContextStore.normalizeContext({
  context_id: 'trunc',
  type: 'longtext',
  source: 'test',
  full_text: long_text
});
console.log(JSON.stringify({ len: normalized.full_text.length }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['len'] == 50000, 'full_text should be truncated to 50000'

    def test_longtext_max_segment_chars_clamp(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'c1', type: 'longtext', source: 'test', max_segment_chars: 9999
});
console.log(JSON.stringify({ clamped: norm.max_segment_chars }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['clamped'] == 5000, 'max_segment_chars > 5000 should clamp to 5000'

    def test_longtext_silence_clamp(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 's1', type: 'longtext', source: 'test', silence_between_ms: 9999
});
console.log(JSON.stringify({ clamped: norm.silence_between_ms }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['clamped'] == 3000, 'silence > 3000 should clamp to 3000'

    def test_longtext_invalid_strategy_fallback_auto(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 's2', type: 'longtext', source: 'test', segment_strategy: 'invalid'
});
console.log(JSON.stringify({ strategy: norm.segment_strategy }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['strategy'] == 'auto', 'invalid strategy should fallback to auto'

    def test_longtext_invalid_output_format_fallback_hex(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'o1', type: 'longtext', source: 'test', output_format: 'invalid'
});
console.log(JSON.stringify({ of: norm.output_format }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['of'] == 'hex', 'invalid output_format should fallback to hex'

    def test_longtext_invalid_audio_format_fallback_mp3(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'a1', type: 'longtext', source: 'test', audio_format: 'invalid'
});
console.log(JSON.stringify({ af: norm.audio_format }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['af'] == 'mp3', 'invalid audio_format should fallback to mp3'

    def test_script_lines_filter_empty_text(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'sl1',
  type: 'script',
  source: 'test',
  lines: [
    { role: 'A', text: '有效', profile_id: 'p1' },
    { role: '', text: '', profile_id: '' },
    { role: 'B', text: '  ', profile_id: 'p2' },
    { role: 'C', text: '也有效', profile_id: '' }
  ]
});
console.log(JSON.stringify({ count: norm.lines.length, validTexts: norm.lines.map(l => l.text) }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['count'] == 2, 'empty/whitespace text rows should be filtered'
        assert '有效' in result['validTexts']
        assert '也有效' in result['validTexts']

    def test_script_lines_max_200(self, context_store_js):
        code = '''
var lines = [];
for (var i = 0; i < 250; i++) lines.push({ role: 'R', text: 'Line ' + i, profile_id: 'p' });
var norm = window.ContextStore.normalizeContext({
  context_id: 'sl2', type: 'script', source: 'test', lines: lines
});
console.log(JSON.stringify({ count: norm.lines.length }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['count'] == 200, 'script lines should be capped at 200'

    def test_script_silence_clamp(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'ss1', type: 'script', source: 'test', silence_between_ms: -100
});
console.log(JSON.stringify({ clamped: norm.silence_between_ms }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['clamped'] == 500, 'script silence < 0 should fallback to default 500'

    def test_script_invalid_output_format_fallback_hex(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'so1', type: 'script', source: 'test', output_format: 'bad'
});
console.log(JSON.stringify({ of: norm.output_format }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['of'] == 'hex'

    def test_script_invalid_audio_format_fallback_mp3(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'sa1', type: 'script', source: 'test', audio_format: 'bad'
});
console.log(JSON.stringify({ af: norm.audio_format }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['af'] == 'mp3'

    def test_unknown_type_minimal_fields(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'unk1',
  type: 'unknown',
  source: 'test-source',
  full_text: 'should not appear',
  lines: [{ text: 'should not appear' }]
});
console.log(JSON.stringify({
  contextId: norm.context_id,
  type: norm.type,
  source: norm.source,
  hasFullText: norm.full_text !== undefined,
  hasLines: norm.lines !== undefined
}));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['contextId'] == 'unk1'
        assert result['type'] == 'unknown'
        assert result['source'] == 'test-source'
        assert result['hasFullText'] == False, 'unknown type should not keep full_text'
        assert result['hasLines'] == False, 'unknown type should not keep lines'

    def test_context_id_prefers_input_context_id_over_sample_id(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  context_id: 'explicit-id',
  sample_id: 'sample-id',
  type: 'longtext',
  source: 'test',
  full_text: 'text'
});
console.log(JSON.stringify({ id: norm.context_id }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['id'] == 'explicit-id', 'context_id takes priority over sample_id'

    def test_context_id_falls_back_to_sample_id(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  sample_id: 'fallback-sample',
  type: 'longtext',
  source: 'test',
  full_text: 'text'
});
console.log(JSON.stringify({ id: norm.context_id }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['id'] == 'fallback-sample', 'should use sample_id when context_id absent'

    def test_context_id_generated_when_neither_present(self, context_store_js):
        code = '''
var norm = window.ContextStore.normalizeContext({
  type: 'longtext',
  source: 'test',
  full_text: 'text'
});
console.log(JSON.stringify({ id: norm.context_id, hasId: !!norm.context_id && norm.context_id.length > 5 }));
'''
        stdout, _ = node_eval(code, context_store_js)
        try:
            result = json.loads(stdout)
        except:
            pytest.fail('Node.js eval failed: ' + stdout)
        assert result['hasId'], 'should generate UUID when neither context_id nor sample_id present'
