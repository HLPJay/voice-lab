"""
test_cancel_confirmation_static.py

P16-CANCEL-FIX1: Static contract tests for cancel/confirmation semantics.
Covers: confirmHighRiskOperation helper, t2a in _OPERATION_MESSAGES,
handleGenerate confirm-order, startStreamGenerate no-independent-confirm,
quick-preview inline confirm, confirm_cost in payload.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')
CLONE_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'voice_clone.js')
DESIGN_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'voice_design.js')
IMPORT_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'voice_import.js')


def read_index():
    return open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()


def read_clone():
    return open(CLONE_JS_PATH, 'r', encoding='utf-8').read()


def read_design():
    return open(DESIGN_JS_PATH, 'r', encoding='utf-8').read()


def read_import():
    return open(IMPORT_JS_PATH, 'r', encoding='utf-8').read()


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


# ── _OPERATION_MESSAGES ────────────────────────────────────────────────────────

class TestOperationMessages:
    def test_t2a_in_operation_messages(self):
        """t2a must be present in _OPERATION_MESSAGES for minimax cost confirm."""
        c = read_index()
        assert 't2a' in c, "t2a key must exist in index.html"
        # Find _OPERATION_MESSAGES block and look for t2a within it
        op_start = c.find('_OPERATION_MESSAGES')
        assert op_start >= 0, "_OPERATION_MESSAGES must exist"
        op_block = c[op_start:op_start + 2000]
        assert 't2a' in op_block, "t2a must be inside _OPERATION_MESSAGES block"
        # Verify it's a proper entry with a colon after the key
        t2a_idx = op_block.find('t2a')
        after = op_block[t2a_idx:t2a_idx + 30]
        assert ':' in after, "t2a entry must have a colon (confirm message follows)"


# ── confirmHighRiskOperation helper ──────────────────────────────────────────

class TestConfirmHighRiskHelper:
    def test_confirmHighRiskOperation_exists(self):
        c = read_index()
        assert 'function confirmHighRiskOperation' in c

    def test_confirmHighRiskOperation_returns_boolean(self):
        c = read_index()
        body = func_body('confirmHighRiskOperation', c)
        assert 'return confirm(' in body or 'return !!confirm(' in body

    def test_confirmHighRiskOperation_no_ui_mutation(self):
        c = read_index()
        body = func_body('confirmHighRiskOperation', c)
        # Must NOT call setLoading, clear resultsArea, or stopAsyncPolling
        assert 'setLoading' not in body
        assert 'resultsArea' not in body
        assert 'stopAsyncPolling' not in body


# ── handleGenerate confirm order ───────────────────────────────────────────────

class TestHandleGenerateConfirmOrder:
    def test_confirm_before_setLoading(self):
        """confirmHighRiskOperation call must appear before setLoading in handleGenerate."""
        c = read_index()
        body = func_body('handleGenerate', c)
        confirm_pos = body.find('confirmHighRiskOperation')
        setloading_pos = body.find('setLoading(true)')
        assert confirm_pos >= 0, 'confirmHighRiskOperation must be called in handleGenerate'
        assert confirm_pos < setloading_pos, 'confirm must be called BEFORE setLoading(true)'

    def test_confirm_before_stopAsyncPolling(self):
        """confirmHighRiskOperation call must appear before stopAsyncPolling."""
        c = read_index()
        body = func_body('handleGenerate', c)
        confirm_pos = body.find('confirmHighRiskOperation')
        stop_pos = body.find('stopAsyncPolling()')
        assert confirm_pos < stop_pos, 'confirm must be called BEFORE stopAsyncPolling()'

    def test_confirm_before_resultsArea_clear(self):
        """confirmHighRiskOperation call must appear before resultsArea.innerHTML = ''."""
        c = read_index()
        body = func_body('handleGenerate', c)
        confirm_pos = body.find('confirmHighRiskOperation')
        clear_pos = body.find("resultsArea.innerHTML = ''")
        assert confirm_pos < clear_pos, 'confirm must be called BEFORE resultsArea.innerHTML = ""'

    def test_confirm_returns_early_on_cancel(self):
        """Cancel path must return immediately without side effects."""
        c = read_index()
        body = func_body('handleGenerate', c)
        # confirmHighRiskOperation result is checked and returns if false
        assert '!confirmHighRiskOperation(operation)' in body
        assert 'return;' in body  # early return on cancel


# ── startStreamGenerate no independent confirm ─────────────────────────────────

class TestStartStreamGenerate:
    def test_no_independent_confirm(self):
        """startStreamGenerate must NOT have its own confirm dialog."""
        c = read_index()
        body = func_body('startStreamGenerate', c)
        # Should NOT have confirm() inside startStreamGenerate
        assert 'confirm(' not in body, 'startStreamGenerate must not have independent confirm'


# ── quick preview confirm (clone/design/import) ─────────────────────────────────

class TestQuickPreviewConfirm:
    def test_clone_quick_preview_confirm_before_fetch(self):
        """clone quick preview must confirm before fetch."""
        c = read_clone()
        # Find the quick preview onclick
        confirm_pos = c.find("provider === 'minimax' && !confirm(")
        fetch_pos = c.find("fetch('/api/voice/render'")
        assert confirm_pos >= 0, 'clone quick preview must have minimax confirm'
        assert fetch_pos >= 0, 'clone quick preview must call fetch'
        assert confirm_pos < fetch_pos, 'confirm must appear BEFORE fetch in clone quick preview'

    def test_clone_quick_preview_confirm_cost_in_payload(self):
        """clone quick preview payload must include confirm_cost."""
        c = read_clone()
        fetch_call = c[c.find("fetch('/api/voice/render'"):]
        assert 'confirm_cost' in fetch_call[:500], 'clone quick preview must set confirm_cost in payload'

    def test_design_quick_preview_confirm_before_fetch(self):
        """design quick preview must confirm before fetch."""
        c = read_design()
        confirm_pos = c.find("provider === 'minimax' && !confirm(")
        fetch_pos = c.find("fetch('/api/voice/render'")
        assert confirm_pos >= 0, 'design quick preview must have minimax confirm'
        assert fetch_pos >= 0, 'design quick preview must call fetch'
        assert confirm_pos < fetch_pos, 'confirm must appear BEFORE fetch in design quick preview'

    def test_design_quick_preview_confirm_cost_in_payload(self):
        """design quick preview payload must include confirm_cost."""
        c = read_design()
        fetch_call = c[c.find("fetch('/api/voice/render'"):]
        assert 'confirm_cost' in fetch_call[:500], 'design quick preview must set confirm_cost in payload'

    def test_import_quick_preview_confirm_before_fetch(self):
        """import quick preview must confirm before fetch."""
        c = read_import()
        confirm_pos = c.find("provider === 'minimax' && !confirm(")
        fetch_pos = c.find("fetch('/api/voice/render'")
        assert confirm_pos >= 0, 'import quick preview must have minimax confirm'
        assert fetch_pos >= 0, 'import quick preview must call fetch'
        assert confirm_pos < fetch_pos, 'confirm must appear BEFORE fetch in import quick preview'

    def test_import_quick_preview_confirm_cost_in_payload(self):
        """import quick preview payload must include confirm_cost."""
        c = read_import()
        fetch_start = c.find("fetch('/api/voice/render'")
        fetch_call = c[fetch_start:fetch_start + 500]
        assert 'confirm_cost' in fetch_call, 'import quick preview must set confirm_cost in payload'
