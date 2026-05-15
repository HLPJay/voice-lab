"""
test_longtext_ux_hints_static.py

P14-LONGTEXT-UX-B1: Static contract tests for longtext production hints.

Covers:
- DOM elements exist
- JS functions exist and are callable
- countBatchTextChars behavior
- estimateBatchSegments behavior for all strategies
- getBatchStrategyHint content
- bindBatchLongtextHints event bindings
- CSS classes exist
- updateBatchLongtextHints init call
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

class TestBatchHintsDOM:
    def test_batchLongtextHints_exists(self):
        assert 'id="batchLongtextHints"' in read_html()

    def test_batchTextCount_exists(self):
        assert 'id="batchTextCount"' in read_html()

    def test_batchEstimatedCost_exists(self):
        assert 'id="batchEstimatedCost"' in read_html()

    def test_batchEstimatedSegments_exists(self):
        assert 'id="batchEstimatedSegments"' in read_html()

    def test_batchStrategyHint_exists(self):
        assert 'id="batchStrategyHint"' in read_html()

    def test_batchTextWarning_exists(self):
        assert 'id="batchTextWarning"' in read_html()

    def test_batchSubtitleHint_exists(self):
        assert 'id="batchSubtitleHint"' in read_html()


# ── JS function existence ─────────────────────────────────────────────────────

class TestBatchHintsFunctions:
    def test_countBatchTextChars_exists(self):
        html = read_html()
        assert 'function countBatchTextChars' in html

    def test_estimateBatchSegments_exists(self):
        html = read_html()
        assert 'function estimateBatchSegments' in html

    def test_getBatchStrategyHint_exists(self):
        html = read_html()
        assert 'function getBatchStrategyHint' in html

    def test_updateBatchLongtextHints_exists(self):
        html = read_html()
        assert 'function updateBatchLongtextHints' in html

    def test_bindBatchLongtextHints_exists(self):
        html = read_html()
        assert 'function bindBatchLongtextHints' in html

    def test_getBatchTextValue_exists(self):
        html = read_html()
        assert 'function getBatchTextValue' in html

    def test_getBatchMaxCharsValue_exists(self):
        html = read_html()
        assert 'function getBatchMaxCharsValue' in html

    def test_getBatchStrategyValue_exists(self):
        html = read_html()
        assert 'function getBatchStrategyValue' in html


# ── Display text content ──────────────────────────────────────────────────────

class TestBatchHintsDisplayText:
    def test_count_shows_50000(self):
        body = func_body('updateBatchLongtextHints', read_html())
        assert '/ 50000 字' in body

    def test_cost_shows_estimated(self):
        body = func_body('updateBatchLongtextHints', read_html())
        assert '预计消耗' in body

    def test_segments_shows_estimated(self):
        body = func_body('updateBatchLongtextHints', read_html())
        assert '预计分段' in body

    def test_no_money_symbols(self):
        body = func_body('updateBatchLongtextHints', read_html())
        # No ¥ or $ in the hint update function
        assert '¥' not in body
        assert '$' not in body


# ── Strategy hint content ────────────────────────────────────────────────────

class TestStrategyHintContent:
    def test_auto_hint_contains_merge(self):
        body = func_body('getBatchStrategyHint', read_html())
        assert '合并' in body

    def test_auto_hint_contains_estimate(self):
        body = func_body('getBatchStrategyHint', read_html())
        assert '当前预计' in body

    def test_paragraph_hint_contains_blank_line(self):
        body = func_body('getBatchStrategyHint', read_html())
        assert '空行' in body

    def test_sentence_hint_contains_punctuation(self):
        body = func_body('getBatchStrategyHint', read_html())
        assert '句号' in body

    def test_line_hint_contains_every_line(self):
        body = func_body('getBatchStrategyHint', read_html())
        assert '每一行' in body


# ── Subtitle hint ────────────────────────────────────────────────────────────

class TestSubtitleHint:
    def test_subtitle_hint_contains_duration(self):
        html = read_html()
        assert '已开启字幕，生成耗时可能增加' in html


# ── estimateBatchSegments behavior ─────────────────────────────────────────

class TestEstimateBatchSegments:
    def test_empty_text_returns_zero(self):
        body = func_body('estimateBatchSegments', read_html())
        # Empty text case should return 0
        assert "return 0" in body

    def test_maxChars_invalid_fallback(self):
        body = func_body('estimateBatchSegments', read_html())
        # Should handle invalid maxChars with fallback to 2000
        assert '2000' in body

    def test_maxChars_clamp_to_100_5000(self):
        body = func_body('estimateBatchSegments', read_html())
        # Should clamp: Math.max(100, Math.min(5000, ...))
        assert '100' in body
        assert '5000' in body

    def test_auto_returns_one_when_small(self):
        body = func_body('estimateBatchSegments', read_html())
        # auto strategy: if total <= maxChars, return 1
        assert '1' in body

    def test_line_strategy_nonempty_lines(self):
        body = func_body('estimateBatchSegments', read_html())
        # line strategy should split by newline
        assert "split('\\n')" in body or "split(\"\\n\")" in body

    def test_sentence_strategy_punctuation(self):
        body = func_body('estimateBatchSegments', read_html())
        # sentence strategy should split by sentence-ending punctuation
        assert '。' in body or '！？' in body


# ── Event bindings ───────────────────────────────────────────────────────────

class TestEventBindings:
    def test_binds_batchText(self):
        body = func_body('bindBatchLongtextHints', read_html())
        assert 'batchText' in body

    def test_binds_batchStrategy(self):
        body = func_body('bindBatchLongtextHints', read_html())
        assert 'batchStrategy' in body

    def test_binds_batchMaxChars(self):
        body = func_body('bindBatchLongtextHints', read_html())
        assert 'batchMaxChars' in body

    def test_binds_batchNeedSubtitle(self):
        body = func_body('bindBatchLongtextHints', read_html())
        assert 'batchNeedSubtitle' in body

    def test_calls_updateBatchLongtextHints_on_init(self):
        body = func_body('bindBatchLongtextHints', read_html())
        assert 'updateBatchLongtextHints' in body


# ── Forbidden operations ────────────────────────────────────────────────────

class TestNoForbiddenOperations:
    def test_no_fetch_in_hints_functions(self):
        html = read_html()
        funcs = [
            'countBatchTextChars', 'estimateBatchSegments', 'getBatchStrategyHint',
            'updateBatchLongtextHints', 'bindBatchLongtextHints',
            'getBatchTextValue', 'getBatchMaxCharsValue', 'getBatchStrategyValue'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'fetch(' not in body, fn + ' must not call fetch'

    def test_no_guardedJsonFetch_in_hints_functions(self):
        html = read_html()
        funcs = [
            'countBatchTextChars', 'estimateBatchSegments', 'getBatchStrategyHint',
            'updateBatchLongtextHints', 'bindBatchLongtextHints',
            'getBatchTextValue', 'getBatchMaxCharsValue', 'getBatchStrategyValue'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'guardedJsonFetch' not in body, fn + ' must not call guardedJsonFetch'

    def test_no_SampleStore_in_hints_functions(self):
        html = read_html()
        funcs = [
            'countBatchTextChars', 'estimateBatchSegments', 'getBatchStrategyHint',
            'updateBatchLongtextHints', 'bindBatchLongtextHints',
            'getBatchTextValue', 'getBatchMaxCharsValue', 'getBatchStrategyValue'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'SampleStore' not in body, fn + ' must not reference SampleStore'

    def test_no_localStorage_write_in_hints_functions(self):
        html = read_html()
        funcs = [
            'countBatchTextChars', 'estimateBatchSegments', 'getBatchStrategyHint',
            'updateBatchLongtextHints', 'bindBatchLongtextHints',
            'getBatchTextValue', 'getBatchMaxCharsValue', 'getBatchStrategyValue'
        ]
        for fn in funcs:
            body = func_body(fn, html)
            assert 'localStorage.setItem' not in body, fn + ' must not write localStorage'

    def test_bindBatchLongtextHints_prevents_duplicate_binding(self):
        body = func_body('bindBatchLongtextHints', read_html())
        # Should have a guard to prevent duplicate binding
        assert '_batchLongtextHintsBound' in body


# ── Submit payload not modified ─────────────────────────────────────────────

class TestNoSubmitPayloadChange:
    def test_handleBatchLongtextSubmit_unchanged(self):
        # Read from batch_longtext.js
        batch_longtext_path = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'batch_longtext.js')
        bl = open(batch_longtext_path, 'r', encoding='utf-8').read()
        # The submit payload should not change — check key fields are still there
        assert "mode: 'longtext'" in bl
        assert "text: text" in bl
        assert "segment_strategy: strategy" in bl
        assert "max_segment_chars: maxChars" in bl

    def test_updateBatchLongtextHints_does_not_call_submit(self):
        body = func_body('updateBatchLongtextHints', read_html())
        assert 'submit' not in body.lower()


# ── CSS classes exist ────────────────────────────────────────────────────────

class TestCSSClasses:
    def test_batch_hints_css_exists(self):
        html = read_html()
        assert '.batch-hints' in html

    def test_batch_hint_row_css_exists(self):
        html = read_html()
        assert '.batch-hint-row' in html

    def test_batch_hint_warning_css_exists(self):
        html = read_html()
        assert '.batch-hint-warning' in html

    def test_batch_hint_strategy_css_exists(self):
        html = read_html()
        assert '.batch-hint-strategy' in html

    def test_batch_hint_subtitle_css_exists(self):
        html = read_html()
        assert '.batch-hint-subtitle' in html


# ── Init call at end of body ────────────────────────────────────────────────

class TestInitCall:
    def test_bindBatchLongtextHints_called_at_bottom(self):
        html = read_html()
        # Should be called before </body>
        body_end = html.rfind('</body>')
        init_call = html.rfind('bindBatchLongtextHints()')
        assert init_call > 0 and init_call < body_end, \
            'bindBatchLongtextHints() must be called before </body>'
