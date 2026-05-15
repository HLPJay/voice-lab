"""
test_sample_store_workspace_integration_static.py

B2/B2-CHECK-FIX: Static contract tests for workspace -> sample_store integration.
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

    def test_buildAssetDownloadUrl_uses_encodeURIComponent(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildAssetDownloadUrl')
        func_end = content.find('\n  }\n', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'encodeURIComponent' in func_body, \
            'buildAssetDownloadUrl must use encodeURIComponent(assetId)'

    def test_buildWorkspaceSampleContext_function_present(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'function buildWorkspaceSampleContext' in content, \
            'buildWorkspaceSampleContext helper must be present'

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
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'try {' in func_body and '} catch' in func_body, \
            'safePushWorkspaceSample must be wrapped in try/catch'

    def test_safePushWorkspaceSample_guards_sample_store_exists(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        # Must check window.SampleStore exists before calling
        assert re.search(r"if\s*\(\s*!\s*window\.SampleStore", func_body) or \
               re.search(r"if\s*\(\s*typeof\s+window\.SampleStore", func_body), \
            'safePushWorkspaceSample must guard against missing SampleStore'

    def test_safePushWorkspaceSample_guards_asset_id(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        # Must return early if no assetId
        assert re.search(r"if\s*\(\s*!\s*assetId", func_body), \
            'safePushWorkspaceSample must return early if assetId is falsy'

    def test_safePushWorkspaceSample_extra_parameter_used(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        # extra must be used for asset_id, duration_ms overrides
        assert 'extra.asset_id' in func_body or 'extra[' in func_body, \
            'safePushWorkspaceSample must use extra.asset_id from extra parameter'

    def test_safePushWorkspaceSample_duration_ms_precedence(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        # Must check audio_asset.duration_ms (via optional chaining) and total_duration_ms
        assert 'audio_asset' in func_body and 'duration_ms' in func_body, \
            'duration_ms must read audio_asset.duration_ms'
        assert 'total_duration_ms' in func_body, \
            'duration_ms must read total_duration_ms (stream)'

    def test_safePushWorkspaceSample_model_precedence(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        # model: data?.model || ctx.model || null
        assert re.search(r"data\?\.model\s*\|\|", func_body), \
            'model must prioritize data?.model over context'

    def test_unified_context_saved_before_all_modes(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # The unified buildWorkspaceSampleContext call must appear BEFORE the
        # "if (isStream)" check (i.e., before any mode-specific branching)
        build_ctx_pos = content.find('buildWorkspaceSampleContext({')
        is_stream_pos = content.find('if (isStream)', build_ctx_pos if build_ctx_pos >= 0 else 0)
        assert build_ctx_pos >= 0 and is_stream_pos > build_ctx_pos, \
            'buildWorkspaceSampleContext must be called before any mode branching'

    def test_async_job_id_update_after_response(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # After async response, must update window._workspaceSampleContext.job_id
        async_branch = re.search(
            r"if\s*\(\s*isAsync\s*\)\s*\{[^}]*?\{[^}]*\}[\s\S]*?window\._workspaceSampleContext\.job_id\s*=",
            content
        )
        assert async_branch, \
            'async branch must update window._workspaceSampleContext.job_id after getting response'

    def test_safePushWorkspaceSample_called_in_renderResults_sync(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_sync'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_sync', ...) must be in renderResults"

    def test_safePushWorkspaceSample_called_in_renderResults_variants(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_variant'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_variant', ...) must be in renderResults variants"

    def test_safePushWorkspaceSample_called_in_renderAsyncResult(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_async'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_async', ...) must be in renderAsyncResult"

    def test_safePushWorkspaceSample_called_in_renderStreamResult(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_stream'"
        assert re.search(pattern, content), \
            "safePushWorkspaceSample('workspace_stream', ...) must be in renderStreamResult"

    def test_getSelectedProfileName_present(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        assert 'function getSelectedProfileName' in content, \
            'getSelectedProfileName helper must be present'

    def test_buildWorkspaceSampleContext_includes_text_preview_truncation(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildWorkspaceSampleContext')
        func_end = content.find('\n  }\n', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'text_preview' in func_body, \
            'buildWorkspaceSampleContext must include text_preview'
        assert 'substring' in func_body or 'slice' in func_body, \
            'text_preview must be truncated'

    def test_buildWorkspaceSampleContext_includes_profile_name(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildWorkspaceSampleContext')
        func_end = content.find('\n  }\n', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'profile_name' in func_body, \
            'buildWorkspaceSampleContext must include profile_name'

    def test_buildWorkspaceSampleContext_uses_voiceBindMap(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildWorkspaceSampleContext')
        func_end = content.find('\n  }\n', func_start) + 4
        func_body = content[func_start:func_end]
        assert '_voiceBindMap' in func_body, \
            'buildWorkspaceSampleContext must look up voice from _voiceBindMap'

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

    def test_no_direct_localStorage_in_safePush(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        forbidden = ['localStorage.getItem', 'localStorage.setItem', 'localStorage.removeItem']
        found = [kw for kw in forbidden if kw in func_body]
        assert not found, \
            f'safePushWorkspaceSample must not use localStorage directly: {found}'

    def test_variants_call_passes_extra_asset_id(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # variants call must pass extra with asset_id (handle multiline object)
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_variant'[\s\S]*?\{[\s\S]*?asset_id[\s\S]*?\}\s*\)"
        assert re.search(pattern, content), \
            'variants safePushWorkspaceSample must pass extra with asset_id'

    def test_variants_call_passes_extra_duration_ms(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # variants call must pass extra with duration_ms
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_variant'[\s\S]*?duration_ms[\s\S]*?\}\s*\)"
        assert re.search(pattern, content), \
            'variants safePushWorkspaceSample must pass extra.duration_ms'

    def test_stream_call_passes_extra_asset_id(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # stream call must pass extra with asset_id (handle multiline object)
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_stream'[\s\S]*?\{[\s\S]*?asset_id[\s\S]*?\}\s*\)"
        assert re.search(pattern, content), \
            'stream safePushWorkspaceSample must pass extra with asset_id'

    def test_stream_call_passes_extra_duration_ms(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        # stream call must pass extra with duration_ms
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_stream'[\s\S]*?duration_ms[\s\S]*?\}\s*\)"
        assert re.search(pattern, content), \
            'stream safePushWorkspaceSample must pass extra.duration_ms'

    def test_stream_call_does_not_pass_blob_url(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        stream_call_block = re.search(
            r"safePushWorkspaceSample\s*\(\s*'workspace_stream'[\s\S]*?\}\s*\)",
            content
        )
        assert stream_call_block, 'stream safePushWorkspaceSample call not found'
        call_text = stream_call_block.group(0)
        assert 'blob:' not in call_text, \
            'stream safePushWorkspaceSample must not pass blob URL'

    def test_sync_call_passes_extra_asset_id(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_sync'[\s\S]*?\{[\s\S]*?asset_id[\s\S]*?\}\s*\)"
        assert re.search(pattern, content), \
            'sync safePushWorkspaceSample must pass extra with asset_id'

    def test_async_call_passes_extra_asset_id(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        pattern = r"safePushWorkspaceSample\s*\(\s*'workspace_async'[\s\S]*?\{[\s\S]*?asset_id[\s\S]*?\}\s*\)"
        assert re.search(pattern, content), \
            'async safePushWorkspaceSample must pass extra with asset_id'

    def test_buildWorkspaceSampleContext_includes_audio_format(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildWorkspaceSampleContext')
        func_end = content.find('\n  }\n', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'audio_format' in func_body, \
            'buildWorkspaceSampleContext must include audio_format'

    def test_safePushWorkspaceSample_no_blob_url_in_download(self):
        content = open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function safePushWorkspaceSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert "blob:" not in func_body, \
            'safePushWorkspaceSample must not handle blob: URLs'
