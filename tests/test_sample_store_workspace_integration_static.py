"""
test_sample_store_workspace_integration_static.py

B2: Static contract tests for workspace -> sample_store integration.
Verifies the JS integration layer in index.html contains correct
helpers, context saves, and safePushWorkspaceSample calls without
executing browser-side code.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')


class TestWorkspaceSampleIntegrationStatic:
    """Static contract — read index.html as text and assert facts."""

    def test_sample_store_script_tag_present(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'sample_store.js' in content, \
            'index.html must include sample_store.js script tag'

    def test_buildAssetDownloadUrl_function_present(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'function buildAssetDownloadUrl' in content, \
            'buildAssetDownloadUrl helper must be present'

    def test_safePushWorkspaceSample_function_present(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'function safePushWorkspaceSample' in content, \
            'safePushWorkspaceSample helper must be present'

    def test_safePushWorkspaceSample_calls_sample_store(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'window.SampleStore.pushSample' in content, \
            'safePushWorkspaceSample must call window.SampleStore.pushSample'

    def test_safePushWorkspaceSample_is_fail_safe(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # Must have try/catch that never propagates
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'try {' in func_body and '} catch' in func_body, \
            'safePushWorkspaceSample must be wrapped in try/catch'

    def test_workspaceContext_global_set_before_stream(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # window._workspaceSampleContext must be set before startStreamGenerate
        # Use non-greedy match to handle nested braces in the object literal
        pattern = r'window\._workspaceSampleContext\s*=\s*\{[\s\S]*?\}\s*;[\s\S]*?startStreamGenerate'
        assert re.search(pattern, content), \
            'window._workspaceSampleContext must be saved before startStreamGenerate'

    def test_workspaceContext_global_set_before_async(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # window._workspaceSampleContext must be set before startAsyncPolling
        pattern = r'window\._workspaceSampleContext\s*=\s*\{[\s\S]*?\}\s*;[\s\S]*?startAsyncPolling'
        assert re.search(pattern, content), \
            'window._workspaceSampleContext must be saved before startAsyncPolling'

    def test_safePushWorkspaceSample_called_in_renderResults_sync(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # safePushWorkspaceSample('workspace_sync', ...) in renderResults statusOk block
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_sync'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_sync', ...) must be in renderResults"

    def test_safePushWorkspaceSample_called_in_renderResults_variants(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # safePushWorkspaceSample('workspace_variant', ...) in renderResults variants
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_variant'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_variant', ...) must be in renderResults variants"

    def test_safePushWorkspaceSample_called_in_renderAsyncResult(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # safePushWorkspaceSample('workspace_async', ...) in renderAsyncResult
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_async'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_async', ...) must be in renderAsyncResult"

    def test_safePushWorkspaceSample_called_in_renderStreamResult(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # safePushWorkspaceSample('workspace_stream', ...) in renderStreamResult
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_stream'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_stream', ...) must be in renderStreamResult"

    def test_getSelectedProfileName_present(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'function getSelectedProfileName' in content, \
            'getSelectedProfileName helper must be present'

    def test_workspaceContext_includes_text_preview_truncation(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # text_preview must be truncated to 100 chars before saving to context
        func_blocks = re.findall(
            r'window\._workspaceSampleContext\s*=\s*\{([^}]+)\}',
            content, re.DOTALL
        )
        assert len(func_blocks) >= 2, 'Should have 2 context saves (stream + async)'
        for block in func_blocks:
            assert 'text_preview' in block, \
                'context must include text_preview'
            # Should use substring or similar truncation
            has_truncation = (
                'substring' in block or
                'slice' in block or
                'substr' in block or
                "text.length > 100" in block
            )
            assert has_truncation, \
                'text_preview in context must be truncated (100 char max)'

    def test_workspaceContext_includes_profile_name(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_blocks = re.findall(
            r'window\._workspaceSampleContext\s*=\s*\{([^}]+)\}',
            content, re.DOTALL
        )
        for block in func_blocks:
            assert 'profile_name' in block, \
                'context must include profile_name'

    def test_workspaceContext_includes_job_id_for_async(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # Find the async branch and verify job_id is in the context save
        # The async context save is after "if (isAsync) {" and before "startAsyncPolling"
        async_branch_match = re.search(
            r"if\s*\(\s*isAsync\s*\)\s*\{[\s\S]*?window\._workspaceSampleContext\s*=\s*\{([\s\S]*?)\}\s*;",
            content
        )
        assert async_branch_match, 'Async context save not found'
        context_body = async_branch_match.group(1)
        assert 'job_id' in context_body, \
            'async context must include job_id'

    def test_safePushWorkspaceSample_extracts_asset_id(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'extractAudioAssetId' in func_body, \
            'safePushWorkspaceSample must use extractAudioAssetId'

    def test_safePushWorkspaceSample_builds_download_url(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'buildAssetDownloadUrl' in func_body, \
            'safePushWorkspaceSample must use buildAssetDownloadUrl'

    def test_safePushWorkspaceSample_uses_voiceBindMap_fallback(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert '_voiceBindMap' in func_body, \
            'safePushWorkspaceSample must look up voice from _voiceBindMap'

    def test_workspace_sync_source_tag_correct(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # Tags should include the source identifier
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_sync'"
        matches = re.findall(pattern, content)
        assert len(matches) >= 1, \
            "safePushWorkspaceSample('workspace_sync') must be called at least once"

    def test_workspace_variant_iterates_over_variants(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # Variants branch must iterate and call push for each variant with audio
        pattern = r"data\.variants\.forEach\s*\(\s*function\s*\(\s*\w+\s*\)\s*\{[^}]*safePushWorkspaceSample"
        assert re.search(pattern, content, re.DOTALL), \
            'renderResults variants branch must forEach and push each variant with audio_asset_id'

    def test_no_direct_localStorage_in_safePush(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        # Must NOT use localStorage directly — must go through SampleStore
        forbidden = ['localStorage.getItem', 'localStorage.setItem', 'localStorage.removeItem']
        found = [kw for kw in forbidden if kw in func_body]
        assert not found, \
            f'safePushWorkspaceSample must not use localStorage directly: {found}'

    def test_stream_context_saves_provider_and_profile(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        stream_context = re.search(
            r"if\s*\(\s*isStream\s*\)[^}]*window\._workspaceSampleContext\s*=\s*\{([^}]+)\}",
            content, re.DOTALL
        )
        assert stream_context, 'Stream context save not found'
        body = stream_context.group(1)
        assert 'provider' in body and 'profile_id' in body, \
            'stream context must include provider and profile_id'
