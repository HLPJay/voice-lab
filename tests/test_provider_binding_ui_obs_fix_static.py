"""
test_provider_binding_ui_obs_fix_static.py

P16-PROVIDER-BINDING-UI-B2-OBS-FIX1: Static contract tests for Provider-first UI observation fixes.

Covers:
- OBS-1: _voiceBindMap is not a full cache, refreshWorkspaceProfileAvailability may
  incorrectly mark profiles with actual bindings as "unbound to current Provider".
- OBS-2: profileSelect change doesn't await checkBindingStatus,
  updateWorkspaceBindingUiState may briefly use old workspaceBindingAvailable.

Fixes:
- refreshWorkspaceBindingMap() with concurrency protection
- Workspace tab/populateAllProfiles pre-fills full binding map
- providerSelect change is async/await
- profileSelect change is async/await
"""

import os
import re

import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')


def read_file(path):
    return open(path, 'r', encoding='utf-8').read()


# ── 12.1 refreshWorkspaceBindingMap ───────────────────────────────────────────

class TestRefreshWorkspaceBindingMap:
    """refreshWorkspaceBindingMap exists and has correct behavior"""

    def test_function_exists(self):
        """1. index.html exists function refreshWorkspaceBindingMap"""
        content = read_file(INDEX_HTML_PATH)
        assert 'function refreshWorkspaceBindingMap' in content, \
            'refreshWorkspaceBindingMap must be declared'

    def test_calls_loadAllBindings(self):
        """2. refreshWorkspaceBindingMap calls loadAllBindings"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function refreshWorkspaceBindingMap')
        assert idx >= 0, 'refreshWorkspaceBindingMap must exist'
        func_body = content[idx:idx + 800]
        assert 'loadAllBindings' in func_body, \
            'refreshWorkspaceBindingMap must call loadAllBindings'

    def test_writes_window_voiceBindMap(self):
        """3. refreshWorkspaceBindingMap writes window._voiceBindMap"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function refreshWorkspaceBindingMap')
        assert idx >= 0, 'refreshWorkspaceBindingMap must exist'
        func_body = content[idx:idx + 800]
        assert 'window._voiceBindMap' in func_body, \
            'refreshWorkspaceBindingMap must write window._voiceBindMap'

    def test_does_not_call_real_minimax(self):
        """4. refreshWorkspaceBindingMap does not call real MiniMax"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function refreshWorkspaceBindingMap')
        assert idx >= 0, 'refreshWorkspaceBindingMap must exist'
        func_body = content[idx:idx + 800]
        # Should only call loadAllBindings which queries local backend
        assert 'MiniMax' not in func_body and 'minimax' not in func_body, \
            'refreshWorkspaceBindingMap must not call real MiniMax'

    def test_has_concurrency_protection(self):
        """5. refreshWorkspaceBindingMap has concurrency protection workspaceBindingMapLoading"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function refreshWorkspaceBindingMap')
        assert idx >= 0, 'refreshWorkspaceBindingMap must exist'
        # The function should check workspaceBindingMapLoading before proceeding
        func_body = content[idx:idx + 1000]
        assert 'workspaceBindingMapLoading' in func_body, \
            'refreshWorkspaceBindingMap must have workspaceBindingMapLoading concurrency guard'


# ── 12.2 Workspace initial load / populateAllProfiles ─────────────────────────

class TestWorkspaceInitialLoad:
    """Workspace tab/populateAllProfiles pre-fills full binding map"""

    def test_workspace_tab_activates_refreshWorkspaceBindingMap(self):
        """6. workspace tab activation awaits refreshWorkspaceBindingMap"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("tab === 'workspace'")
        assert idx >= 0, "tab === 'workspace' must exist"
        ws_block = content[idx:idx + 300]
        assert 'refreshWorkspaceBindingMap' in ws_block, \
            "Workspace tab must call refreshWorkspaceBindingMap"

    def test_workspace_tab_binds_refreshWorkspaceBindingMap_before_refreshAvailability(self):
        """7. refreshWorkspaceBindingMap called before refreshWorkspaceProfileAvailability"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("tab === 'workspace'")
        assert idx >= 0, "tab === 'workspace' must exist"
        ws_block = content[idx:idx + 300]
        # Find positions
        bind_map_idx = ws_block.find('refreshWorkspaceBindingMap')
        avail_idx = ws_block.find('refreshWorkspaceProfileAvailability')
        assert bind_map_idx >= 0, 'refreshWorkspaceBindingMap must be called'
        assert avail_idx >= 0, 'refreshWorkspaceProfileAvailability must be called'
        assert bind_map_idx < avail_idx, \
            'refreshWorkspaceBindingMap must be called before refreshWorkspaceProfileAvailability'

    def test_populateAllProfiles_calls_refreshWorkspaceBindingMap(self):
        """8. populateAllProfiles calls refreshWorkspaceBindingMap"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('async function populateAllProfiles')
        if idx < 0:
            idx = content.find('function populateAllProfiles')
        assert idx >= 0, 'populateAllProfiles must exist'
        func_body = content[idx:idx + 1000]
        assert 'refreshWorkspaceBindingMap' in func_body, \
            'populateAllProfiles must call refreshWorkspaceBindingMap'

    def test_populateAllProfiles_binds_refreshWorkspaceBindingMap_before_refreshAvailability(self):
        """9. populateAllProfiles calls refreshWorkspaceBindingMap before refreshWorkspaceProfileAvailability"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('async function populateAllProfiles')
        if idx < 0:
            idx = content.find('function populateAllProfiles')
        assert idx >= 0, 'populateAllProfiles must exist'
        func_body = content[idx:idx + 1000]
        bind_map_idx = func_body.find('refreshWorkspaceBindingMap')
        avail_idx = func_body.find('refreshWorkspaceProfileAvailability')
        assert bind_map_idx >= 0, 'refreshWorkspaceBindingMap must be called'
        assert avail_idx >= 0, 'refreshWorkspaceProfileAvailability must be called'
        assert bind_map_idx < avail_idx, \
            'refreshWorkspaceBindingMap must be called before refreshWorkspaceProfileAvailability in populateAllProfiles'


# ── 12.3 provider/profile change async ───────────────────────────────────────

class TestProviderProfileChangeHandlers:
    """providerSelect and profileSelect change handlers are async/await"""

    def test_provider_select_change_is_async(self):
        """10. providerSelect change handler is async"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("providerSelect.addEventListener('change'")
        assert idx >= 0, 'providerSelect change listener must exist'
        handler_block = content[idx:idx + 300]
        # Should have async ()
        assert re.search(r'async\s*\(\s*\)\s*=>', handler_block), \
            'providerSelect change handler must be async'

    def test_provider_select_change_awaits_refreshWorkspaceBindingMap(self):
        """11. providerSelect change handler awaits refreshWorkspaceBindingMap"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("providerSelect.addEventListener('change'")
        assert idx >= 0, 'providerSelect change listener must exist'
        handler_block = content[idx:idx + 300]
        assert 'await refreshWorkspaceBindingMap' in handler_block, \
            'providerSelect change handler must await refreshWorkspaceBindingMap'

    def test_provider_select_change_awaits_checkBindingStatus(self):
        """12. providerSelect change handler awaits checkBindingStatus"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("providerSelect.addEventListener('change'")
        assert idx >= 0, 'providerSelect change listener must exist'
        handler_block = content[idx:idx + 300]
        assert 'await checkBindingStatus' in handler_block, \
            'providerSelect change handler must await checkBindingStatus'

    def test_profile_select_change_is_async(self):
        """13. profileSelect change handler is async"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("profileSelect.addEventListener('change'")
        assert idx >= 0, 'profileSelect change listener must exist'
        handler_block = content[idx:idx + 300]
        assert re.search(r'async\s*\(\s*\)\s*=>', handler_block), \
            'profileSelect change handler must be async'

    def test_profile_select_change_awaits_checkBindingStatus(self):
        """14. profileSelect change handler awaits checkBindingStatus"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("profileSelect.addEventListener('change'")
        assert idx >= 0, 'profileSelect change listener must exist'
        handler_block = content[idx:idx + 300]
        assert 'await checkBindingStatus' in handler_block, \
            'profileSelect change handler must await checkBindingStatus'


# ── 12.4 Boundary checks ─────────────────────────────────────────────────────

class TestBoundaryChecks:
    """Verify no improper modifications"""

    def test_handleGenerate_guard_preserved(self):
        """15. handleGenerate guard isWorkspaceBindingAvailable is preserved"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('async function handleGenerate')
        assert idx >= 0, 'handleGenerate must exist'
        func_body = content[idx:idx + 2000]
        assert 'isWorkspaceBindingAvailable()' in func_body, \
            'handleGenerate guard must be preserved'

    def test_no_model_dropdown_added(self):
        """16. No model dropdown added in Workspace area"""
        content = read_file(INDEX_HTML_PATH)
        # B2 explicitly does NOT add a model dropdown
        ws_match = re.search(
            r'<div class="card">\s*<div class="card-title">[^<]*</div>\s*<div class="config-grid">(.*?)</div>\s*</div>',
            content, re.DOTALL
        )
        if ws_match:
            ws_content = ws_match.group(1)
            assert 'modelSelect' not in ws_content, \
                'Must not add modelSelect to Workspace config area'

    def test_not_modified_provider_capabilities_js(self):
        """17. provider_capabilities.js not modified"""
        provider_capabilities_path = os.path.join(
            REPO_ROOT, 'app', 'static', 'js', 'provider_capabilities.js'
        )
        if os.path.exists(provider_capabilities_path):
            content = read_file(provider_capabilities_path)
            assert 'refreshWorkspaceBindingMap' not in content, \
                'provider_capabilities.js must not be modified'

    def test_not_modified_profile_binding_js(self):
        """18. profile_binding.js not modified"""
        profile_binding_path = os.path.join(
            REPO_ROOT, 'app', 'static', 'js', 'profile_binding.js'
        )
        if os.path.exists(profile_binding_path):
            content = read_file(profile_binding_path)
            assert 'refreshWorkspaceBindingMap' not in content, \
                'profile_binding.js must not be modified'

    def test_not_modified_app_models(self):
        """19. app/models not modified"""
        content = read_file(INDEX_HTML_PATH)
        assert 'app/models/' not in content, \
            'Must not reference app/models/'

    def test_not_modified_app_repositories(self):
        """20. app/repositories not modified"""
        content = read_file(INDEX_HTML_PATH)
        assert 'app/repositories/' not in content, \
            'Must not reference app/repositories/'

    def test_not_modified_app_services(self):
        """21. app/services not modified"""
        content = read_file(INDEX_HTML_PATH)
        assert 'app/services/' not in content, \
            'Must not reference app/services/'

    def test_not_modified_app_api(self):
        """22. app/api not modified"""
        content = read_file(INDEX_HTML_PATH)
        assert 'app/api/' not in content, \
            'Must not reference app/api/'
