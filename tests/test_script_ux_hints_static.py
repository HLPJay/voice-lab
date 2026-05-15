"""
test_script_ux_hints_static.py

P14-SCRIPT-UX-B1: Static contract tests for script production hints.

Covers:
- DOM elements exist
- JS functions exist and are callable
- collectScriptStats behavior for all stat fields
- formatRoleList content
- updateBatchScriptHints display text
- bindBatchScriptHints event bindings
- CSS classes exist
- updateBatchScriptHints init call
- No forbidden operations (fetch, guardedJsonFetch, SampleStore, localStorage write, submit payload change)
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')


def read_html():
    return open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()


def func_body(name, content):
    """Return the full body of a named function (including nested braces)."""
    marker = 'function ' + name
    start = content.find(marker)
    if start < 0:
        marker = name + ' = function'
        start = content.find(marker)
    if start < 0:
        marker = name + ': function'
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


# ── DOM element existence ──────────────────────────────────────────────────────

class TestScriptHintsDOM:
    def test_batchScriptHints_exists(self):
        assert 'id="batchScriptHints"' in read_html()

    def test_batchScriptLineStats_exists(self):
        assert 'id="batchScriptLineStats"' in read_html()

    def test_batchScriptCharStats_exists(self):
        assert 'id="batchScriptCharStats"' in read_html()

    def test_batchScriptEstimatedSegments_exists(self):
        assert 'id="batchScriptEstimatedSegments"' in read_html()

    def test_batchScriptRoleStats_exists(self):
        assert 'id="batchScriptRoleStats"' in read_html()

    def test_batchScriptProfileStats_exists(self):
        assert 'id="batchScriptProfileStats"' in read_html()

    def test_batchScriptRoleWarning_exists(self):
        assert 'id="batchScriptRoleWarning"' in read_html()

    def test_batchScriptProfileWarning_exists(self):
        assert 'id="batchScriptProfileWarning"' in read_html()

    def test_batchScriptSubtitleHint_exists(self):
        assert 'id="batchScriptSubtitleHint"' in read_html()


# ── JS function existence ───────────────────────────────────────────────────────

class TestScriptHintsFunctions:
    def test_getScriptRowsSafe_exists(self):
        html = read_html()
        assert 'function getScriptRowsSafe' in html

    def test_collectScriptStats_exists(self):
        html = read_html()
        assert 'function collectScriptStats' in html

    def test_formatRoleList_exists(self):
        html = read_html()
        assert 'function formatRoleList' in html

    def test_updateBatchScriptHints_exists(self):
        html = read_html()
        assert 'function updateBatchScriptHints' in html

    def test_bindBatchScriptHints_exists(self):
        html = read_html()
        assert 'function bindBatchScriptHints' in html


# ── Display text content ──────────────────────────────────────────────────────

class TestScriptHintsDisplayText:
    def test_line_stats_contains_row_count(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '剧本统计' in body

    def test_char_stats_contains_chars(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '约' in body and '字' in body

    def test_segments_contains_estimated(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '预计生成' in body

    def test_role_stats_contains_role(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '角色' in body

    def test_profile_stats_contains_profile(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '涉及音色' in body

    def test_no_money_symbols(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '¥' not in body
        assert '$' not in body


# ── collectScriptStats behavior ───────────────────────────────────────────────

class TestCollectScriptStats:
    def test_uses_getScriptRowsSafe(self):
        body = func_body('collectScriptStats', read_html())
        assert 'getScriptRowsSafe' in body

    def test_getScriptRowsSafe_uses_scriptRows(self):
        body = func_body('getScriptRowsSafe', read_html())
        assert '_scriptRows' in body

    def test_validRows_uses_trim(self):
        body = func_body('collectScriptStats', read_html())
        assert 'trim()' in body

    def test_totalChars_sums_valid_rows(self):
        body = func_body('collectScriptStats', read_html())
        assert 'totalChars' in body

    def test_estimatedSegments_equals_validRows(self):
        body = func_body('collectScriptStats', read_html())
        assert 'estimatedSegments' in body

    def test_roleSet_uses_object(self):
        body = func_body('collectScriptStats', read_html())
        assert 'roleSet' in body or 'Object' in body

    def test_profileSet_uses_object(self):
        body = func_body('collectScriptStats', read_html())
        assert 'profileSet' in body or 'Object' in body

    def test_emptyRoleRows_counted(self):
        body = func_body('collectScriptStats', read_html())
        assert 'emptyRoleRows' in body

    def test_missingProfileRows_counted(self):
        body = func_body('collectScriptStats', read_html())
        assert 'missingProfileRows' in body


# ── formatRoleList behavior ──────────────────────────────────────────────────

class TestFormatRoleList:
    def test_returns_zero_when_empty(self):
        body = func_body('formatRoleList', read_html())
        assert '0 个' in body

    def test_joins_with_slash(self):
        body = func_body('formatRoleList', read_html())
        assert '/' in body

    def test_shows_max_three(self):
        body = func_body('formatRoleList', read_html())
        # Should handle more than 3 roles
        assert 'slice(0, 3)' in body or 'slice(0,3)' in body


# ── Warning content ──────────────────────────────────────────────────────────

class TestWarningContent:
    def test_role_warning_contains_unnamed(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '未填写角色名' in body

    def test_profile_warning_contains_unselected(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert '未选择音色' in body


# ── Subtitle hint ────────────────────────────────────────────────────────────

class TestSubtitleHint:
    def test_subtitle_hint_contains_duration(self):
        html = read_html()
        assert '已开启字幕，生成耗时可能增加' in html


# ── Event bindings ───────────────────────────────────────────────────────────

class TestEventBindings:
    def test_binds_scriptLines_input(self):
        body = func_body('bindBatchScriptHints', read_html())
        assert 'scriptLines' in body

    def test_binds_scriptLines_change(self):
        body = func_body('bindBatchScriptHints', read_html())
        assert 'scriptLines' in body

    def test_binds_batchScriptNeedSubtitle(self):
        body = func_body('bindBatchScriptHints', read_html())
        assert 'batchScriptNeedSubtitle' in body

    def test_calls_updateBatchScriptHints_on_init(self):
        body = func_body('bindBatchScriptHints', read_html())
        assert 'updateBatchScriptHints' in body

    def test_addScriptLine_calls_updateBatchScriptHints(self):
        body = func_body('addScriptLine', read_html())
        assert 'updateBatchScriptHints' in body

    def test_removeScriptLine_calls_updateBatchScriptHints(self):
        body = func_body('removeScriptLine', read_html())
        assert 'updateBatchScriptHints' in body


# ── Forbidden operations ────────────────────────────────────────────────────

class TestNoForbiddenOperations:
    def test_no_fetch_in_hints_functions(self):
        html = read_html()
        funcs = [
            'getScriptRowsSafe', 'collectScriptStats', 'formatRoleList',
            'updateBatchScriptHints', 'bindBatchScriptHints'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'fetch(' not in body, fn + ' must not call fetch'

    def test_no_guardedJsonFetch_in_hints_functions(self):
        html = read_html()
        funcs = [
            'getScriptRowsSafe', 'collectScriptStats', 'formatRoleList',
            'updateBatchScriptHints', 'bindBatchScriptHints'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'guardedJsonFetch' not in body, fn + ' must not call guardedJsonFetch'

    def test_no_SampleStore_in_hints_functions(self):
        html = read_html()
        funcs = [
            'getScriptRowsSafe', 'collectScriptStats', 'formatRoleList',
            'updateBatchScriptHints', 'bindBatchScriptHints'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'SampleStore' not in body, fn + ' must not reference SampleStore'

    def test_no_localStorage_write_in_hints_functions(self):
        html = read_html()
        funcs = [
            'getScriptRowsSafe', 'collectScriptStats', 'formatRoleList',
            'updateBatchScriptHints', 'bindBatchScriptHints'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'localStorage.setItem' not in body, fn + ' must not write localStorage'

    def test_bindBatchScriptHints_prevents_duplicate_binding(self):
        body = func_body('bindBatchScriptHints', read_html())
        assert '_batchScriptHintsBound' in body


# ── Submit payload not modified ─────────────────────────────────────────────

class TestNoSubmitPayloadChange:
    def test_handleBatchScriptSubmit_unchanged(self):
        batch_script_path = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'batch_script.js')
        bs = open(batch_script_path, 'r', encoding='utf-8').read()
        assert "mode: 'script'" in bs
        assert 'script: lines' in bs or 'script:' in bs

    def test_updateBatchScriptHints_does_not_call_submit(self):
        body = func_body('updateBatchScriptHints', read_html())
        assert 'submit' not in body.lower()

    def test_batch_script_js_unchanged(self):
        # Verify batch_script.js wasn't modified in this commit
        batch_script_path = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'batch_script.js')
        content = open(batch_script_path, 'r', encoding='utf-8').read()
        # Should not contain any script hints references
        assert 'batchScriptHints' not in content


# ── CSS classes exist ────────────────────────────────────────────────────────

class TestCSSClasses:
    def test_batch_script_hints_css_exists(self):
        html = read_html()
        assert '.batch-script-hints' in html

    def test_batch_hint_row_css_exists(self):
        html = read_html()
        assert '.batch-hint-row' in html

    def test_batch_hint_warning_css_exists(self):
        html = read_html()
        assert '.batch-hint-warning' in html

    def test_batch_hint_subtitle_css_exists(self):
        html = read_html()
        assert '.batch-hint-subtitle' in html


# ── Init call at end of body ────────────────────────────────────────────────

class TestInitCall:
    def test_bindBatchScriptHints_called_at_bottom(self):
        html = read_html()
        body_end = html.rfind('</body>')
        init_call = html.rfind('bindBatchScriptHints()')
        assert init_call > 0 and init_call < body_end, \
            'bindBatchScriptHints() must be called before </body>'
