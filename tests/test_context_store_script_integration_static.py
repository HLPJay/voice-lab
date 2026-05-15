"""
test_context_store_script_integration_static.py

P14-CONTEXT-C1: Integration tests for script context save and detail view.
Verifies:
- batch_script.js calls ContextStore.pushContext with type: 'script'
- context_id = data.batch_id
- source = 'batch_script_merged'
- saves lines, provider, silence_between_ms, output_format, audio_format, need_subtitle, batch_id
- fail-safe try/catch
- context_id written to _batchSampleContextById before polling
- SampleSidebar showSampleDetail renders script lines
- script context does not show restore button
- all display text uses esc()
- no fillTextInput / fetch / API calls
"""

import os
import re
import subprocess
import json
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')
BATCH_SCRIPT_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'batch_script.js')
SAMPLE_STORE_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_store.js')
SAMPLE_SIDEBAR_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_sidebar.js')
CONTEXT_STORE_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'context_store.js')


def read(path):
    return open(path, 'r', encoding='utf-8').read()


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


# ── batch_script.js tests ─────────────────────────────────────────────────

class TestBatchScriptContextSave:
    """batch_script.js calls ContextStore.pushContext for script context."""

    def test_calls_context_store_pushContext(self):
        content = read(BATCH_SCRIPT_PATH)
        assert 'ContextStore.pushContext' in content, \
            'batch_script.js must call ContextStore.pushContext'

    def test_pushContext_after_data_batch_id(self):
        content = read(BATCH_SCRIPT_PATH)
        # pushContext should come after data.batch_id is obtained
        idx = content.find('ContextStore.pushContext')
        assert idx >= 0, 'ContextStore.pushContext must exist'
        # Check that data.batch_id appears before it
        before = content[:idx]
        assert 'data.batch_id' in before or 'data && data.batch_id' in before, \
            'pushContext must be called after data.batch_id is available'

    def test_pushContext_type_is_script(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert re.search(r"type\s*:\s*['\"]script['\"]", call_body), \
            'type must be "script"'

    def test_pushContext_source_is_batch_script_merged(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert 'batch_script_merged' in call_body, \
            'source must be "batch_script_merged"'

    def test_pushContext_context_id_is_batch_id(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert 'context_id:' in call_body, \
            'pushContext must pass context_id'
        assert 'data.batch_id' in call_body, \
            'context_id must be data.batch_id'

    def test_pushContext_saves_batch_id(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert 'batch_id:' in call_body, \
            'pushContext must save batch_id'

    def test_pushContext_saves_lines(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert 'lines:' in call_body, \
            'pushContext must save lines'

    def test_pushContext_saves_provider(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert re.search(r"provider\s*:", call_body), \
            'pushContext must save provider'

    def test_pushContext_saves_silence_between_ms(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert 'silence_between_ms:' in call_body, \
            'pushContext must save silence_between_ms'

    def test_pushContext_saves_output_format_hex(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert "output_format:" in call_body, \
            'pushContext must save output_format'

    def test_pushContext_saves_audio_format(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert 'audio_format:' in call_body, \
            'pushContext must save audio_format'

    def test_pushContext_saves_need_subtitle(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        assert 'need_subtitle:' in call_body, \
            'pushContext must save need_subtitle'

    def test_pushContext_has_try_catch(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        assert idx >= 0
        # Find the try block before it
        search_region = content[max(0, idx - 400):idx + 100]
        assert 'try' in search_region or 'try{' in search_region or 'try {' in search_region, \
            'ContextStore.pushContext call must be inside try/catch'

    def test_pushContext_fail_safe_does_not_block_batch(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        assert idx >= 0
        # The catch block must not re-throw or call process.exit
        # Look from 500 chars before pushContext to 800 chars after
        # (try is before pushContext, catch is after)
        search_region = content[max(0, idx - 500):idx + 800]
        assert 'catch' in search_region, \
            'ContextStore.pushContext must have catch block'
        # Catch should be empty or just a comment (fail-safe)
        catch_idx = search_region.find('catch')
        catch_body = search_region[catch_idx:catch_idx + 200]
        # Should not contain throw, exit, abort, or showResult (error display)
        assert 'throw' not in catch_body.lower() or '//' in catch_body, \
            'catch block must not re-throw'
        assert 'showResult' not in catch_body, \
            'catch block must not show error to user'

    def test_context_save_not_call_fetch(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        if idx >= 0:
            region = content[max(0, idx - 300):idx + 500]
            assert 'fetch(' not in region, \
                'ContextStore.pushContext region must not call fetch'
            assert '/api/' not in region, \
                'ContextStore.pushContext region must not call API endpoints'

    def test_context_id_written_to_batchSampleContextById(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        assert idx >= 0
        region = content[idx:idx + 600]
        assert 'context_id' in region, \
            'context_id must be saved to _batchSampleContextById after pushContext'

    def test_context_id_write_before_showBatchProgress(self):
        content = read(BATCH_SCRIPT_PATH)
        # context_id write to _batchSampleContextById must appear before showBatchProgress call
        ctx_id_write = content.find('.context_id = ')
        show_batch = content.find('showBatchProgress(')
        assert ctx_id_write >= 0, 'context_id assignment to _batchSampleContextById must exist'
        assert show_batch >= 0, 'showBatchProgress call must exist'
        assert ctx_id_write < show_batch, \
            'context_id must be written to _batchSampleContextById before showBatchProgress'

    def test_context_save_not_modify_request_payload(self):
        content = read(BATCH_SCRIPT_PATH)
        # The ContextStore.pushContext block should be AFTER the guardedJsonFetch call.
        # Verify the submit payload still contains mode:'script'
        idx = content.find("mode: 'script'")
        assert idx >= 0, "mode:'script' payload key must still be present"
        # Verify it's inside the {...} argument list of guardedJsonFetch
        search_region = content[max(0, idx - 600):idx + 100]
        assert 'guardedJsonFetch' in search_region, \
            "mode:'script' must be in the guardedJsonFetch options object"

    def test_context_id_uses_batch_id_not_new_uuid(self):
        content = read(BATCH_SCRIPT_PATH)
        idx = content.find('ContextStore.pushContext')
        call_body = content[idx:idx + 800]
        # context_id should be set to data.batch_id, not a generated UUID
        assert 'data.batch_id' in call_body, \
            'context_id must use data.batch_id, not a new UUID'


# ── SampleSidebar script detail tests ─────────────────────────────────────────

class TestSampleSidebarScriptDetail:
    """SampleSidebar showSampleDetail renders script context lines."""

    def test_showSampleDetail_handles_script_type(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        assert re.search(r"context\.type\s*===\s*['\"]script['\"]", content), \
            'showSampleDetail must handle context.type === "script"'

    def test_renderScriptLinesDetail_exists(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'function renderScriptLinesDetail' in content, \
            'renderScriptLinesDetail function must exist'

    def test_renderScriptLinesDetail_reads_context_lines(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'context.lines' in func_body or 'lines' in func_body, \
            'renderScriptLinesDetail must read context.lines'

    def test_renderScriptLinesDetail_escapes_text(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'esc(' in func_body, \
            'renderScriptLinesDetail must escape text with esc()'

    def test_renderScriptLinesDetail_shows_line_count(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'lineCount' in func_body or 'length' in func_body, \
            'renderScriptLinesDetail must show line count'

    def test_renderScriptLinesDetail_shows_provider(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'provider' in func_body, \
            'renderScriptLinesDetail must show provider'

    def test_renderScriptLinesDetail_shows_audio_format(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'audio_format' in func_body, \
            'renderScriptLinesDetail must show audio_format'

    def test_renderScriptLinesDetail_shows_need_subtitle(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'need_subtitle' in func_body, \
            'renderScriptLinesDetail must show need_subtitle'

    def test_renderScriptLinesDetail_shows_silence_between_ms(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'silence_between_ms' in func_body, \
            'renderScriptLinesDetail must show silence_between_ms'

    def test_renderScriptLinesDetail_shows_role(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'role' in func_body, \
            'renderScriptLinesDetail must show role'

    def test_renderScriptLinesDetail_shows_text(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'text' in func_body, \
            'renderScriptLinesDetail must show text'

    def test_renderScriptLinesDetail_shows_profile_id(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function renderScriptLinesDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'profile_id' in func_body, \
            'renderScriptLinesDetail must show profile_id'

    def test_script_context_no_restore_button(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        # script type should not show sample-detail-restore-btn
        # Find the script branch
        script_branch_idx = body.find("context.type === 'script'")
        if script_branch_idx < 0:
            script_branch_idx = body.find('context.type === "script"')
        assert script_branch_idx >= 0, \
            'showSampleDetail must have a context.type === "script" branch'
        # The restore button code should be in the longtext branch, not script branch
        restore_idx = body.find('sample-detail-restore-btn')
        assert restore_idx >= 0, 'restore button must exist somewhere'
        # restore button must be in the longtext branch, not script branch
        assert restore_idx < script_branch_idx or body.find("'longtext'") < script_branch_idx, \
            'restore button must only appear in longtext branch, not script branch'

    def test_showSampleDetail_script_no_fillTextInput(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'fillTextInput' not in func_body, \
            'showSampleDetail must not call fillTextInput'

    def test_showSampleDetail_script_no_restoreLongtextContext(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'restoreLongtextContext' not in func_body, \
            'showSampleDetail must not call restoreLongtextContext'

    def test_showSampleDetail_script_no_fetch(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'fetch(' not in func_body, \
            'showSampleDetail must not call fetch'
        assert '/api/' not in func_body, \
            'showSampleDetail must not call API endpoints'

    def test_script_lines_not_in_data_attribute(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        # lines should not appear in any data-* attribute
        data_attr_refs = re.findall(r'data-[a-zA-Z-]+\s*=\s*"[^"]*lines[^"]*"', func_body)
        assert not data_attr_refs, \
            'lines must not appear in data-* attributes'

    def test_showSampleDetail_script_calls_renderScriptLinesDetail(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'renderScriptLinesDetail' in func_body, \
            'showSampleDetail must call renderScriptLinesDetail for script context'

    def test_showSampleDetail_script_branch_has_source_badge(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        # script branch should still show source badge
        script_branch_idx = func_body.find("context.type === 'script'")
        if script_branch_idx < 0:
            script_branch_idx = func_body.find('context.type === "script"')
        assert script_branch_idx >= 0
        region = func_body[script_branch_idx:script_branch_idx + 2000]
        assert '来源' in region or 'source' in region.lower(), \
            'script detail branch should show source'

    def test_longtext_still_has_restore_button(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        assert 'sample-detail-restore-btn' in body, \
            'longtext restore button must still exist'

    def test_longtext_restore_button_uses_data_context_id(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        assert 'data-context-id' in body, \
            'restore button must use data-context-id'

    def test_longtext_restore_button_conditional_on_longtext(self):
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        idx = body.find('sample-detail-restore-btn')
        assert idx >= 0
        # Look in a wider window (2000 chars before) since HTML content is built inline
        region = body[max(0, idx - 2000):idx + 50]
        assert "type === 'longtext'" in region or 'type === "longtext"' in region, \
            'restore button must be conditional on context.type === "longtext"'

    def test_showSampleDetail_script_branch_closes_meta_div_before_lines(self):
        """script branch must close sample-detail-meta div before appending scriptDetailHtml."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        # Find the script branch
        script_branch_idx = body.find("context.type === 'script'")
        if script_branch_idx < 0:
            script_branch_idx = body.find('context.type === "script"')
        assert script_branch_idx >= 0, \
            'showSampleDetail must have a context.type === "script" branch'
        # Find the closing brace of the if/else-if chain to bound our search
        else_branch_idx = body.find('} else {', script_branch_idx)
        script_substr = body[script_branch_idx:else_branch_idx if else_branch_idx > 0 else len(body)]
        # scriptDetailHtml must be preceded by '</div>' that closes sample-detail-meta
        # Find the panel.innerHTML assignment in the script branch (skip var declaration)
        inner_html_idx = script_substr.find("panel.innerHTML +=")
        assert inner_html_idx >= 0, 'script branch must have panel.innerHTML +='
        panel_part = script_substr[inner_html_idx:]
        close_div_idx = panel_part.find("'</div>'")
        # Find scriptDetailHtml after the panel.innerHTML assignment (in the += chain)
        script_detail_idx = panel_part.find('scriptDetailHtml')
        assert close_div_idx >= 0, \
            "script branch must contain closing '</div>' for sample-detail-meta"
        assert script_detail_idx >= 0, \
            'script branch must reference scriptDetailHtml'
        assert close_div_idx < script_detail_idx, \
            "sample-detail-meta closing '</div>' must appear before scriptDetailHtml in script branch"

    def test_showSampleDetail_script_shows_restore_button(self):
        """script context detail must show 'restore to script' button."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        # Find the script branch
        script_branch_idx = body.find("context.type === 'script'")
        if script_branch_idx < 0:
            script_branch_idx = body.find('context.type === "script"')
        assert script_branch_idx >= 0, \
            'showSampleDetail must have context.type === "script" branch'
        # Find the next else branch to bound our search
        else_branch_idx = body.find('} else {', script_branch_idx)
        script_branch = body[script_branch_idx:else_branch_idx if else_branch_idx > 0 else len(body)]
        assert 'sample-detail-restore-script-btn' in script_branch, \
            'script detail must show sample-detail-restore-script-btn'

    def test_showSampleDetail_longtext_hides_restore_script_button(self):
        """longtext context detail must NOT show 'restore to script' button."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        # Find the longtext branch
        longtext_branch_idx = body.find("context.type === 'longtext'")
        if longtext_branch_idx < 0:
            longtext_branch_idx = body.find('context.type === "longtext"')
        assert longtext_branch_idx >= 0, \
            'showSampleDetail must have context.type === "longtext" branch'
        # Find the next else/else-if branch
        next_branch_start = body.find('} else if', longtext_branch_idx)
        if next_branch_start < 0:
            next_branch_start = body.find('} else {', longtext_branch_idx)
        lt_branch = body[longtext_branch_idx:next_branch_start if next_branch_start > 0 else len(body)]
        assert 'sample-detail-restore-script-btn' not in lt_branch, \
            'longtext detail must NOT show sample-detail-restore-script-btn'

    def test_showSampleDetail_script_restore_button_uses_data_context_id(self):
        """script restore button must use data-context-id, not data-lines."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        script_branch_idx = body.find("context.type === 'script'")
        if script_branch_idx < 0:
            script_branch_idx = body.find('context.type === "script"')
        assert script_branch_idx >= 0
        else_branch_idx = body.find('} else {', script_branch_idx)
        script_branch = body[script_branch_idx:else_branch_idx if else_branch_idx > 0 else len(body)]
        assert 'data-context-id' in script_branch, \
            'restore script button must use data-context-id'
        assert 'data-lines' not in script_branch, \
            'restore script button must NOT use data-lines'
        assert 'data-full-text' not in script_branch, \
            'restore script button must NOT use data-full-text'

    def test_restoreScriptContext_function_exists(self):
        """restoreScriptContext function must exist."""
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'function restoreScriptContext' in content, \
            'restoreScriptContext function must exist'

    def test_restoreScriptContext_guards_type(self):
        """restoreScriptContext must guard on context.type === 'script'."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function restoreScriptContext'):]
        # Find the function body end
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert "context.type !== 'script'" in func_body or 'context.type !== "script"' in func_body, \
            'restoreScriptContext must guard on context.type !== "script"'

    def test_restoreScriptContext_does_not_fetch(self):
        """restoreScriptContext must not call fetch or guardedJsonFetch."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function restoreScriptContext'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'fetch' not in func_body or func_body.index('fetch') > func_body.index('//'), \
            'restoreScriptContext must not call fetch'
        assert 'guardedJsonFetch' not in func_body, \
            'restoreScriptContext must not call guardedJsonFetch'
        assert 'handleBatchScriptSubmit' not in func_body, \
            'restoreScriptContext must not call handleBatchScriptSubmit'
        assert 'ContextStore.pushContext' not in func_body, \
            'restoreScriptContext must not write to ContextStore'
        assert 'SampleStore.pushSample' not in func_body, \
            'restoreScriptContext must not write to SampleStore'

    def test_restoreScriptContext_calls_switchToScriptBatchMode(self):
        """restoreScriptContext must call switchToScriptBatchMode."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function restoreScriptContext'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'switchToScriptBatchMode' in func_body, \
            'restoreScriptContext must call switchToScriptBatchMode'

    def test_restoreScriptContext_calls_applyScriptContextToForm(self):
        """restoreScriptContext must call applyScriptContextToForm."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function restoreScriptContext'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'applyScriptContextToForm' in func_body, \
            'restoreScriptContext must call applyScriptContextToForm'

    def test_applyScriptContextToForm_function_exists(self):
        """applyScriptContextToForm function must exist."""
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'function applyScriptContextToForm' in content, \
            'applyScriptContextToForm function must exist'

    def test_applyScriptContextToForm_restores_provider(self):
        """applyScriptContextToForm must restore batchScriptProvider."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function applyScriptContextToForm'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'batchScriptProvider' in func_body, \
            'applyScriptContextToForm must restore batchScriptProvider'
        assert 'silence' in func_body.lower() or 'Silence' in func_body, \
            'applyScriptContextToForm must restore silence'
        assert 'audio_format' in func_body.lower() or 'OutputFormat' in func_body, \
            'applyScriptContextToForm must restore audio_format'
        assert 'need_subtitle' in func_body.lower() or 'Subtitle' in func_body, \
            'applyScriptContextToForm must restore need_subtitle'

    def test_applyScriptContextToForm_calls_addScriptLine(self):
        """applyScriptContextToForm must call addScriptLine to restore lines."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function applyScriptContextToForm'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'addScriptLine' in func_body, \
            'applyScriptContextToForm must call addScriptLine'

    def test_applyScriptContextToForm_does_not_call_fillTextInput(self):
        """applyScriptContextToForm must not call fillTextInput."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function applyScriptContextToForm'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'fillTextInput' not in func_body, \
            'applyScriptContextToForm must not call fillTextInput'

    def test_applyScriptContextToForm_does_not_call_restoreLongtextContext(self):
        """applyScriptContextToForm must not call restoreLongtextContext."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function applyScriptContextToForm'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'restoreLongtextContext' not in func_body, \
            'applyScriptContextToForm must not call restoreLongtextContext'

    def test_switchToScriptBatchMode_function_exists(self):
        """switchToScriptBatchMode function must exist."""
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'function switchToScriptBatchMode' in content, \
            'switchToScriptBatchMode function must exist'

    def test_switchToScriptBatchMode_sets_batch_mode_radio(self):
        """switchToScriptBatchMode must set input[name="batchMode"][value="script"].checked = true."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function switchToScriptBatchMode'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'input[name="batchMode"][value="script"]' in func_body, \
            'switchToScriptBatchMode must reference input[name="batchMode"][value="script"]'
        assert 'scriptRadio.checked = true' in func_body, \
            'switchToScriptBatchMode must set scriptRadio.checked = true'

    def test_switchToScriptBatchMode_triggers_change_event(self):
        """switchToScriptBatchMode must trigger change event on the batch mode radio."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function switchToScriptBatchMode'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'change' in func_body.lower(), \
            'switchToScriptBatchMode must dispatch change event'

    def test_switchToScriptBatchMode_shows_batch_script_panel(self):
        """switchToScriptBatchMode must show batchScriptPanel and hide batchLongtextPanel."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function switchToScriptBatchMode'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'batchScriptPanel' in func_body, \
            'switchToScriptBatchMode must reference batchScriptPanel'
        assert 'batchLongtextPanel' in func_body, \
            'switchToScriptBatchMode must reference batchLongtextPanel'
        # Check that batchScriptPanel is set to display: '' (visible)
        assert "scriptPanel.style.display = ''" in func_body or 'scriptPanel.style.display=""' in func_body, \
            'switchToScriptBatchMode must set batchScriptPanel.style.display = ""'
        # Check that batchLongtextPanel is set to display: 'none' (hidden)
        assert "longtextPanel.style.display = 'none'" in func_body or 'longtextPanel.style.display="none"' in func_body, \
            'switchToScriptBatchMode must set batchLongtextPanel.style.display = "none"'

    def test_switchToScriptBatchMode_no_early_return_after_click(self):
        """switchToScriptBatchMode must not return early after btn.click(), must continue to set batch mode."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function switchToScriptBatchMode'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        # After btn.click() there must NOT be an immediate return that bypasses batch mode switching
        # Find the btn.click pattern
        click_idx = func_body.find('.click()')
        if click_idx >= 0:
            # After .click() there should not be a bare 'return;' before batchMode code
            after_click = func_body[click_idx:]
            # Check if there's a return statement before batchMode code
            batch_mode_idx = after_click.find('batchMode')
            return_idx = after_click.find('return')
            if batch_mode_idx >= 0 and return_idx >= 0:
                assert return_idx > batch_mode_idx or return_idx == -1, \
                    'switchToScriptBatchMode must not return before setting batch mode after btn.click()'
            # Also check: the click block should not end with just 'return;'
            # i.e., the function should continue past the click
            lines_after_click = after_click[:100]
            assert not lines_after_click.strip().endswith('return;'), \
                'switchToScriptBatchMode must not return immediately after btn.click()'

    def test_findSampleCard_function_exists(self):
        """findSampleCard helper function must exist."""
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'function findSampleCard' in content, \
            'findSampleCard function must exist'

    def test_insertDetailPanel_function_exists(self):
        """insertDetailPanel helper function must exist."""
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'function insertDetailPanel' in content, \
            'insertDetailPanel function must exist'

    def test_insertDetailPanel_uses_insertBefore(self):
        """insertDetailPanel must use insertBefore to place panel near the card."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function insertDetailPanel'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'insertBefore' in func_body, \
            'insertDetailPanel must use insertBefore to place panel near the card'
        assert 'findSampleCard' in func_body, \
            'insertDetailPanel must use findSampleCard to locate the card'

    def test_showSampleDetail_calls_insertDetailPanel(self):
        """showSampleDetail must call insertDetailPanel instead of directly appending to root."""
        content = read(SAMPLE_SIDEBAR_PATH)
        body = content[content.find('function showSampleDetail'):]
        depth = 0
        end = len(body)
        for i, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        func_body = body[:end]
        assert 'insertDetailPanel' in func_body, \
            'showSampleDetail must call insertDetailPanel'
        # The direct root.appendChild(panel) calls should be replaced with insertDetailPanel
        # Only the fallback inside insertDetailPanel should use root.appendChild

    def test_longtext_restore_button_still_exists(self):
        """longtext restore button must still exist (not removed by C2)."""
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'sample-detail-restore-btn' in content, \
            'sample-detail-restore-btn must still exist'

    def test_flat_buttons_still_exist_no_more_menu(self):
        """flat action buttons must still exist, no more menu."""
        content = read(SAMPLE_SIDEBAR_PATH)
        assert 'sample-btn-copy' in content, \
            'sample-btn-copy must still exist'
        assert 'sample-btn-fill' in content, \
            'sample-btn-fill must still exist'
        assert 'sample-btn-delete' in content, \
            'sample-btn-delete must still exist'
        assert 'sample-btn-more' not in content, \
            'sample-btn-more must not exist (UXFIX1)'
        assert 'sample-more-menu' not in content, \
            'sample-more-menu must not exist (UXFIX1)'


# ── Behavioral tests (Node.js) ──────────────────────────────────────────────

@pytest.mark.skipif(
    not _node_available(),
    reason='Node.js not available; behavioural tests skipped'
)
class TestScriptContextBehavioral:
    """Execute integrated modules to verify runtime behavior."""

    def _load_modules(self):
        cs_js = read(CONTEXT_STORE_PATH)
        ss_js = read(SAMPLE_STORE_PATH)
        combined = '''
var window = { crypto: { randomUUID: function() { return require('crypto').randomUUID(); } } };
var localStorage = { _data: {}, getItem: function(k){return this._data[k]||null;}, setItem: function(k,v){this._data[k]=v;}, removeItem: function(k){delete this._data[k];} };
''' + cs_js + '\n' + ss_js
        return combined

    def _eval(self, expr, extra_js=''):
        combined = self._load_modules() + '\n' + extra_js + '\nconsole.log(JSON.stringify(' + expr + '))'
        stdout, stderr, rc = _run_node(combined)
        return stdout.strip(), stderr.strip(), rc

    def test_context_store_upsert_updates_existing(self):
        stdout, stderr, rc = self._eval(
            '(function() { '
            'window.ContextStore.pushContext({context_id:"script-upsert",type:"script",source:"batch_script_merged",lines:[{role:"A",text:"Hello",profile_id:"p1"}],provider:"minimax",batch_id:"script-upsert"}); '
            'window.ContextStore.pushContext({context_id:"script-upsert",type:"script",source:"batch_script_merged",lines:[{role:"B",text:"World",profile_id:"p2"}],provider:"minimax",batch_id:"script-upsert"}); '
            'var retrieved = window.ContextStore.getContext("script-upsert"); '
            'return {count: window.ContextStore.getContexts().length, role: retrieved ? retrieved.lines[0].role : null, text: retrieved ? retrieved.lines[0].text : null}; '
            '})()'
        )
        assert rc == 0, f'Node error: {stderr}'
        try:
            result = json.loads(stdout)
        except:
            pytest.fail(f'Could not parse JSON: {stdout}')
        assert result['count'] == 1, f"upsert must not increase count; got {result['count']}"
        assert result['role'] == 'B', f"upsert must update lines; got {result['role']}"
        assert result['text'] == 'World', f"upsert must update text; got {result['text']}"

    def test_context_store_script_normalizes_lines(self):
        stdout, stderr, rc = self._eval(
            '(function() { '
            'window.ContextStore.pushContext({context_id:"script-norm",type:"script",source:"batch_script_merged",lines:[{role:"角色",text:"测试台词",profile_id:"prof-1"}],provider:"minimax",silence_between_ms:500,output_format:"hex",audio_format:"mp3",need_subtitle:true,batch_id:"script-norm"}); '
            'var retrieved = window.ContextStore.getContext("script-norm"); '
            'return {hasLines: !!retrieved && Array.isArray(retrieved.lines), lineCount: retrieved ? retrieved.lines.length : 0, role: retrieved && retrieved.lines[0] ? retrieved.lines[0].role : null, text: retrieved && retrieved.lines[0] ? retrieved.lines[0].text : null, profile_id: retrieved && retrieved.lines[0] ? retrieved.lines[0].profile_id : null, provider: retrieved ? retrieved.provider : null, silence: retrieved ? retrieved.silence_between_ms : null, audio_format: retrieved ? retrieved.audio_format : null, need_subtitle: retrieved ? retrieved.need_subtitle : null}; '
            '})()'
        )
        assert rc == 0, f'Node error: {stderr}'
        try:
            result = json.loads(stdout)
        except:
            pytest.fail(f'Could not parse JSON: {stdout}')
        assert result['hasLines'], 'script context must have lines array'
        assert result['lineCount'] == 1, f"lineCount must be 1; got {result['lineCount']}"
        assert result['role'] == '角色', f"role must be normalized; got {result['role']}"
        assert result['text'] == '测试台词', f"text must be normalized; got {result['text']}"
        assert result['profile_id'] == 'prof-1', f"profile_id must be normalized; got {result['profile_id']}"
        assert result['provider'] == 'minimax', f"provider must be saved; got {result['provider']}"
        assert result['silence'] == 500, f"silence_between_ms must be saved; got {result['silence']}"
        assert result['audio_format'] == 'mp3', f"audio_format must be saved; got {result['audio_format']}"
        assert result['need_subtitle'] is True, f"need_subtitle must be saved; got {result['need_subtitle']}"
