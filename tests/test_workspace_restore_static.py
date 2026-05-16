"""
test_workspace_restore_static.py

P16-WORKSPACE-RESTORE-B1: Static contract tests for workspace context restore.
Covers: ContextStore workspace normalize, index.html buildWorkspaceRestoreContext,
SampleStore context_id write, sample_sidebar.js restore logic, old sample fallback.
"""

import os
import re
import subprocess
import json
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT_STORE_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'context_store.js')
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')
SAMPLE_SIDEBAR_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_sidebar.js')


def read_context_store():
    return open(CONTEXT_STORE_PATH, 'r', encoding='utf-8').read()


def read_index():
    return open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()


def read_sidebar():
    return open(SAMPLE_SIDEBAR_PATH, 'r', encoding='utf-8').read()


def func_body(name, content):
    """Return the full body of a named function (including nested braces)."""
    # Match 'function name(' specifically to avoid matching restoreWorkspaceContextById
    marker = 'function ' + name + '('
    start = content.find(marker)
    if start < 0:
        # Fallback: try exact match at word boundary
        marker = 'function ' + name + ' '
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


# ── ContextStore workspace normalize ────────────────────────────────────────────

class TestContextStoreWorkspaceNormalize:
    def test_normalizeWorkspaceContext_exists(self):
        c = read_context_store()
        assert 'function normalizeWorkspaceContext' in c

    def test_normalizeContext_has_workspace_branch(self):
        c = read_context_store()
        body = func_body('normalizeContext', c)
        assert "type === 'workspace'" in body or 'type === "workspace"' in body

    def test_workspace_context_has_full_text(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'full_text' in body

    def test_workspace_context_has_gen_mode(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'gen_mode' in body

    def test_workspace_context_has_variant_count(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'variant_count' in body

    def test_workspace_context_has_output_format(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'output_format' in body

    def test_workspace_context_has_need_subtitle(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'need_subtitle' in body

    def test_workspace_context_has_params(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'params' in body

    def test_workspace_context_params_has_speed_vol_pitch_emotion(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'speed' in body
        assert 'vol' in body
        assert 'pitch' in body
        assert 'emotion' in body

    def test_workspace_context_has_job_id_asset_id_download_url(self):
        c = read_context_store()
        body = func_body('normalizeWorkspaceContext', c)
        assert 'job_id' in body
        assert 'asset_id' in body
        assert 'download_url' in body

    def test_workspace_context_type_is_workspace(self):
        c = read_context_store()
        # type is set by normalizeContext base object, check the branch exists
        body = func_body('normalizeContext', c)
        assert "type === 'workspace'" in body or 'type === "workspace"' in body


# ── index.html buildWorkspaceRestoreContext ─────────────────────────────────────

class TestIndexBuildWorkspaceRestoreContext:
    def test_buildWorkspaceRestoreContext_exists(self):
        c = read_index()
        assert 'function buildWorkspaceRestoreContext' in c

    def test_uses_textInput_value_for_full_text(self):
        c = read_index()
        body = func_body('buildWorkspaceRestoreContext', c)
        # Must read from textInput.value (full text, not text_preview)
        assert 'textInput' in body

    def test_calls_ContextStore_pushContext(self):
        c = read_index()
        # At the call sites, ContextStore.pushContext should be called
        assert 'ContextStore.pushContext' in c

    def test_context_id_passed_to_safePushWorkspaceSample(self):
        c = read_index()
        body = func_body('safePushWorkspaceSample', c)
        assert 'context_id' in body

    def test_safePushWorkspaceSample_writes_context_id_to_sample(self):
        c = read_index()
        # The sample object in safePushWorkspaceSample should include context_id
        body = func_body('safePushWorkspaceSample', c)
        # Look for context_id in the sample object (extend window to 800 chars)
        sample_start = body.find('var sample = {')
        assert sample_start >= 0, 'sample object must exist'
        sample_region = body[sample_start:sample_start + 800]
        assert 'context_id' in sample_region, 'sample must include context_id field'

    def test_buildWorkspaceRestoreContext_returns_type_workspace(self):
        c = read_index()
        body = func_body('buildWorkspaceRestoreContext', c)
        assert "'workspace'" in body or '"workspace"' in body

    def test_buildWorkspaceRestoreContext_reads_gen_mode_from_dom(self):
        c = read_index()
        body = func_body('buildWorkspaceRestoreContext', c)
        assert 'genMode' in body or "name=\"genMode\"" in body

    def test_buildWorkspaceRestoreContext_reads_variant_count_input(self):
        c = read_index()
        body = func_body('buildWorkspaceRestoreContext', c)
        assert 'variantCount' in body


# ── sample_sidebar.js workspace restore ─────────────────────────────────────────

class TestSidebarWorkspaceRestore:
    def test_isWorkspaceSource_exists(self):
        c = read_sidebar()
        assert 'function isWorkspaceSource' in c

    def test_isWorkspaceSource_returns_true_for_workspace_sources(self):
        c = read_sidebar()
        body = func_body('isWorkspaceSource', c)
        assert 'workspace_sync' in body
        assert 'workspace_async' in body
        assert 'workspace_stream' in body
        assert 'workspace_variant' in body

    def test_switchToWorkspaceTab_exists(self):
        c = read_sidebar()
        assert 'function switchToWorkspaceTab' in c

    def test_restoreWorkspaceContextById_exists(self):
        c = read_sidebar()
        assert 'function restoreWorkspaceContextById' in c

    def test_restoreWorkspaceContext_exists(self):
        c = read_sidebar()
        assert 'function restoreWorkspaceContext' in c

    def test_restoreWorkspaceContext_restores_textInput(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'textInput' in body

    def test_restoreWorkspaceContext_restores_providerSelect(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'providerSelect' in body

    def test_restoreWorkspaceContext_restores_profileSelect(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'profileSelect' in body

    def test_restoreWorkspaceContext_restores_audioFormat(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'audioFormat' in body

    def test_restoreWorkspaceContext_restores_outputFormat(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'outputFormat' in body

    def test_restoreWorkspaceContext_restores_needSubtitle(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'needSubtitle' in body

    def test_restoreWorkspaceContext_restores_genMode(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'genMode' in body

    def test_restoreWorkspaceContext_restores_variantCount(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'variantCount' in body

    def test_restoreWorkspaceContext_restores_voice_params(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'paramSpeed' in body
        assert 'paramVol' in body
        assert 'paramPitch' in body
        assert 'paramEmotion' in body

    def test_restoreWorkspaceContext_does_not_call_handleGenerate(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'handleGenerate' not in body

    def test_restoreWorkspaceContext_does_not_call_fetch(self):
        c = read_sidebar()
        body = func_body('restoreWorkspaceContext', c)
        assert 'fetch(' not in body

    def test_buildCard_uses_data_context_id_for_workspace(self):
        c = read_sidebar()
        body = func_body('buildCard', c)
        # Should use data-context-id for workspace samples with context_id
        assert 'data-context-id' in body

    def test_buildCard_uses_restore_title_for_workspace(self):
        c = read_sidebar()
        body = func_body('buildCard', c)
        # workspace with context_id should have "恢复工作台" button
        assert '恢复工作台' in body

    def test_bindActionEvents_handles_data_context_id(self):
        c = read_sidebar()
        body = func_body('bindActionEvents', c) if 'function bindActionEvents' in c else c
        # Should read data-context-id attribute
        assert 'data-context-id' in body or 'contextId' in body

    def test_bindActionEvents_calls_restoreWorkspaceContextById(self):
        c = read_sidebar()
        body = func_body('bindActionEvents', c) if 'function bindActionEvents' in c else c
        assert 'restoreWorkspaceContextById' in body


# ── Old sample fallback ──────────────────────────────────────────────────────────

class TestOldSampleFallback:
    def test_no_context_id_still_uses_fillTextInput(self):
        c = read_sidebar()
        body = func_body('buildCard', c)
        # Non-workspace or no-context_id → should still have data-text fill button
        assert 'data-text' in body
        assert '填入工作台' in body

    def test_fillTextInput_still_exists(self):
        c = read_sidebar()
        assert 'function fillTextInput' in c

    def test_fillTextInput_only_writes_textInput(self):
        c = read_sidebar()
        body = func_body('fillTextInput', c)
        assert 'textInput' in body
        # Should NOT restore any other fields
        assert 'providerSelect' not in body
        assert 'profileSelect' not in body


# ── Longtext/script not broken ─────────────────────────────────────────────────

class TestLongtextScriptNotBroken:
    def test_restoreLongtextContext_still_exists(self):
        c = read_sidebar()
        assert 'function restoreLongtextContext' in c

    def test_restoreScriptContext_still_exists(self):
        c = read_sidebar()
        assert 'function restoreScriptContext' in c

    def test_applyLongtextContextToForm_still_exists(self):
        c = read_sidebar()
        assert 'function applyLongtextContextToForm' in c

    def test_sample_detail_restore_btn_still_exists(self):
        c = read_sidebar()
        assert 'sample-detail-restore-btn' in c

    def test_sample_detail_restore_script_btn_still_exists(self):
        c = read_sidebar()
        assert 'sample-detail-restore-script-btn' in c
