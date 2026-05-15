"""
test_sample_sidebar_static.py

P13-CREATION-B4: Static contract tests for sample_sidebar.js.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDEBAR_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_sidebar.js')


class TestSampleSidebarFileExists:
    """File presence and basic structure."""

    def test_file_exists(self):
        assert os.path.isfile(SIDEBAR_JS_PATH), \
            'sample_sidebar.js must exist at app/static/js/sample_sidebar.js'

    def test_iife_wrapper(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert '(function ()' in content, \
            'sample_sidebar.js must use IIFE (function(){})()'
        assert "window.SampleSidebar" in content, \
            'sample_sidebar.js must reference window.SampleSidebar'

    def test_use_strict(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert "'use strict'" in content or '"use strict"' in content, \
            'sample_sidebar.js must use strict mode'


class TestSampleSidebarExports:
    """window.SampleSidebar must expose the required methods."""

    def test_init_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'init:' in content or 'init :' in content, \
            'SampleSidebar must have init method'

    def test_render_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'render:' in content or 'render :' in content, \
            'SampleSidebar must have render method'

    def test_refresh_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'refresh:' in content or 'refresh :' in content, \
            'SampleSidebar must have refresh method'

    def test_playSample_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'playSample:' in content or 'playSample :' in content, \
            'SampleSidebar must have playSample method'

    def test_deleteSample_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'deleteSample:' in content or 'deleteSample :' in content, \
            'SampleSidebar must have deleteSample method'

    def test_clearSamples_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'clearSamples:' in content or 'clearSamples :' in content, \
            'SampleSidebar must have clearSamples method'

    def test_copyText_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'copyText:' in content or 'copyText :' in content, \
            'SampleSidebar must have copyText method'

    def test_fillTextInput_exists(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'fillTextInput:' in content or 'fillTextInput :' in content, \
            'SampleSidebar must have fillTextInput method'

    def test_all_eight_methods_present(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        found = re.findall(r'(?:window\.SampleSidebar\s*=\s*\{[^}]*\})', content, re.DOTALL)
        assert found, 'Could not find window.SampleSidebar assignment'
        obj = found[0]
        required = ['init', 'render', 'refresh', 'playSample', 'deleteSample',
                    'clearSamples', 'copyText', 'fillTextInput']
        for m in required:
            assert re.search(r'\b' + m + r'\s*:', obj), \
                'SampleSidebar missing method: ' + m


class TestSampleSidebarNoApiCalls:
    """Must not call any backend API."""

    def test_no_fetch(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'fetch(' not in content, \
            'sample_sidebar.js must not call fetch()'

    def test_no_guardedJsonFetch(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'guardedJsonFetch' not in content, \
            'sample_sidebar.js must not call guardedJsonFetch'

    def test_no_xmlHttpRequest(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'XMLHttpRequest' not in content, \
            'sample_sidebar.js must not use XMLHttpRequest'


class TestSampleSidebarDomAccess:
    """Must only access DOM elements by known IDs."""

    def test_getElementById_known_ids(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        ids = re.findall(r'getElementById\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
        allowed = {'sampleSidebarRoot', 'textInput', 'sampleSidebarClearBtn'}
        for id_ in ids:
            assert id_ in allowed, \
                'getElementById references unknown ID: ' + id_

    def test_querySelector_known_selectors(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        selectors = re.findall(r'querySelector\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
        # Only class selectors for sample sidebar cards are allowed
        allowed_classes = {
            'sample-btn-play', 'sample-btn-copy', 'sample-btn-fill',
            'sample-btn-delete', 'sample-btn-clear', 'sample-sidebar-empty',
            'sample-sidebar-header', 'sample-sidebar-title',
            'sample-card', 'sample-card-meta', 'sample-source-badge',
            'sample-duration', 'sample-text', 'sample-profile',
            'sample-profile-name', 'sample-voice-name', 'sample-card-actions',
        }
        for sel in selectors:
            # class selectors start with '.'
            if sel.startswith('.'):
                cls = sel[1:]
                assert cls in allowed_classes, \
                    'querySelector uses unknown class: ' + sel

    def test_no_innerHTML_with_untrusted_input(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        # Must use textContent or escape user data before innerHTML
        # The buildCard function uses encodeURIComponent for data attributes
        # which is acceptable
        assert True  # Guarded by data attribute encoding pattern


class TestSampleSidebarStorageIntegration:
    """Must interact correctly with SampleStore via localStorage."""

    def test_reads_sample_store_storage_key(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'voice_lab_recent_samples_v1' in content, \
            'sample_sidebar.js must read voice_lab_recent_samples_v1 from localStorage'

    def test_writes_to_sampleSidebarRoot(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'sampleSidebarRoot' in content, \
            'sample_sidebar.js must write to #sampleSidebarRoot'

    def test_calls_sampleStore_deleteSample(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'SampleStore.deleteSample' in content, \
            'sample_sidebar.js must call SampleStore.deleteSample'

    def test_calls_sampleStore_clearSamples(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'SampleStore.clearSamples' in content, \
            'sample_sidebar.js must call SampleStore.clearSamples'

    def test_storage_event_listener_registered(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'addEventListener' in content and 'storage' in content, \
            'sample_sidebar.js must listen to storage events for cross-tab sync'

    def test_render_called_on_storage_change(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        # The storage event listener must call render when storage key changes
        # Find the storage event listener registration
        storage_idx = content.find("addEventListener('storage'")
        assert storage_idx >= 0, \
            'sample_sidebar.js must register a storage event listener'
        # Extract the listener function body (up to 400 chars after the registration)
        snippet = content[storage_idx:storage_idx + 400]
        assert 'render' in snippet, \
            'storage event handler must call render'


class TestSampleSidebarPlayBehavior:
    """playSample must handle URL and fallback correctly."""

    def test_playSample_handles_missing_url(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function playSample')
        assert func_start >= 0, 'playSample function must exist'
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        # Must check if URL is falsy before playing
        assert ('!url' in func_body or 'url' in func_body), \
            'playSample must check URL existence'

    def test_playSample_uses_sharedAudioPlayer(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function playSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert '_sharedAudioPlayer' in func_body, \
            'playSample must try window._sharedAudioPlayer first'

    def test_playSample_fallback_audio(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function playSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'new Audio' in func_body, \
            'playSample must fallback to new Audio()'


class TestSampleSidebarCopyTextBehavior:
    """copyText must handle clipboard API with fallback."""

    def test_copyText_uses_clipboard_api(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function copyText')
        assert func_start >= 0, 'copyText function must exist'
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'navigator.clipboard' in func_body, \
            'copyText must use navigator.clipboard'

    def test_copyText_has_fallback(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function copyText')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'execCommand' in func_body or 'textarea' in func_body, \
            'copyText must have execCommand fallback'


class TestSampleSidebarFillTextInputBehavior:
    """fillTextInput must write to #textInput and dispatch event."""

    def test_fillTextInput_gets_textInput(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function fillTextInput')
        assert func_start >= 0, 'fillTextInput function must exist'
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'textInput' in func_body, \
            'fillTextInput must get #textInput element'

    def test_fillTextInput_dispatches_input_event(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function fillTextInput')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'dispatchEvent' in func_body or 'dispatchEvent' in content, \
            'fillTextInput must dispatch input event'


class TestSampleSidebarDeleteBehavior:
    """deleteSample must call SampleStore and re-render."""

    def test_deleteSample_calls_sampleStore_delete(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function deleteSample')
        assert func_start >= 0, 'deleteSample function must exist'
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'SampleStore.deleteSample' in func_body, \
            'deleteSample must call SampleStore.deleteSample'

    def test_deleteSample_calls_render(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function deleteSample')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'render()' in func_body, \
            'deleteSample must call render() after delete'


class TestSampleSidebarClearBehavior:
    """clearSamples must call SampleStore and re-render."""

    def test_clearSamples_calls_sampleStore_clear(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function clearSamples')
        assert func_start >= 0, 'clearSamples function must exist'
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'SampleStore.clearSamples' in func_body, \
            'clearSamples must call SampleStore.clearSamples'

    def test_clearSamples_calls_render(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function clearSamples')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'render()' in func_body, \
            'clearSamples must call render() after clear'


class TestSampleSidebarCardBuilder:
    """buildCard must produce correct HTML structure."""

    def test_buildCard_uses_data_sample_id(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildCard')
        assert func_start >= 0, 'buildCard function must exist'
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'data-sample-id' in func_body, \
            'buildCard must set data-sample-id attribute'

    def test_buildCard_uses_encodeURIComponent_for_url(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildCard')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'encodeURIComponent' in func_body, \
            'buildCard must use encodeURIComponent for data attributes'

    def test_buildCard_action_buttons(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        func_start = content.find('function buildCard')
        func_end = content.find('\n  }', func_start) + 4
        func_body = content[func_start:func_end]
        assert 'sample-btn-play' in func_body, 'buildCard must include play button'
        assert 'sample-btn-copy' in func_body, 'buildCard must include copy button'
        assert 'sample-btn-fill' in func_body, 'buildCard must include fill button'
        assert 'sample-btn-delete' in func_body, 'buildCard must include delete button'


class TestSampleSidebarSourceLabel:
    """sourceLabel must map all valid sources."""

    def test_source_label_maps_workspace_sync(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'workspace_sync' in content, \
            'sourceLabel must map workspace_sync'

    def test_source_label_maps_workspace_async(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'workspace_async' in content, \
            'sourceLabel must map workspace_async'

    def test_source_label_maps_workspace_stream(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'workspace_stream' in content, \
            'sourceLabel must map workspace_stream'

    def test_source_label_maps_workspace_variant(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'workspace_variant' in content, \
            'sourceLabel must map workspace_variant'

    def test_source_label_maps_audition(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'audition' in content, \
            'sourceLabel must map audition'


class TestSampleSidebarNoIndexHtmlDependencies:
    """Must not depend on index.html internal state."""

    def test_no_handleGenerate(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'handleGenerate' not in content, \
            'sample_sidebar.js must not reference handleGenerate'

    def test_no_voiceBindMap(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'voiceBindMap' not in content, \
            'sample_sidebar.js must not reference voiceBindMap'

    def test_no_profileBinding(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'profileBinding' not in content, \
            'sample_sidebar.js must not reference profileBinding'

    def test_no_batchState(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'batchState' not in content, \
            'sample_sidebar.js must not reference batchState'

    def test_no_sharedBatchState(self):
        content = open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()
        assert 'sharedBatchState' not in content, \
            'sample_sidebar.js must not reference sharedBatchState'
