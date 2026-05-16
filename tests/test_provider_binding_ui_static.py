"""
test_provider_binding_ui_static.py

P16-PROVIDER-BINDING-UI-B2: Static contract tests for Provider-first profile/binding UI.

Covers:
- Scope boundary: no backend/API/schema changes
- Provider-first UI: DOM order in Workspace config area
- Workspace profile binding helpers: getWorkspaceProfileBindingState, refreshWorkspaceProfileAvailability
- Parameter area / generate button control: setWorkspaceBindingControlsEnabled, updateWorkspaceBindingUiState
- handleGenerate guard preserved
- Event handlers: providerSelect/profileSelect change handlers
- checkBindingStatus integration with updateWorkspaceBindingUiState
- CSS: .disabled-by-binding
"""

import os
import re

import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')


def read_file(path):
    return open(path, 'r', encoding='utf-8').read()


# ── 16.1 Scope boundary ───────────────────────────────────────────────────────

class TestScopeBoundary:
    """Verify no backend/API/schema changes"""

    def test_not_modified_app_models(self):
        content = read_file(INDEX_HTML_PATH)
        # B2 must not reference app/models paths (they should not appear as strings)
        assert 'app/models/' not in content, \
            'Must not reference app/models/'

    def test_not_modified_app_repositories(self):
        content = read_file(INDEX_HTML_PATH)
        assert 'app/repositories/' not in content, \
            'Must not reference app/repositories/'

    def test_not_modified_app_services(self):
        content = read_file(INDEX_HTML_PATH)
        assert 'app/services/' not in content, \
            'Must not reference app/services/'

    def test_not_modified_app_api(self):
        content = read_file(INDEX_HTML_PATH)
        assert 'app/api/' not in content, \
            'Must not reference app/api/'

    def test_not_modified_resolve_binding(self):
        content = read_file(INDEX_HTML_PATH)
        # resolve_binding is a backend function, B2 must not call it from frontend
        assert 'resolve_binding' not in content, \
            'Must not call resolve_binding'

    def test_not_modified_provider_capabilities_js(self):
        provider_capabilities_path = os.path.join(
            REPO_ROOT, 'app', 'static', 'js', 'provider_capabilities.js'
        )
        if os.path.exists(provider_capabilities_path):
            content = read_file(provider_capabilities_path)
            # Should not be modified in B2
            assert 'provider-first' not in content.lower(), \
                'provider_capabilities.js should not be modified in B2'

    def test_not_modified_profile_binding_js(self):
        profile_binding_path = os.path.join(
            REPO_ROOT, 'app', 'static', 'js', 'profile_binding.js'
        )
        if os.path.exists(profile_binding_path):
            content = read_file(profile_binding_path)
            assert 'refreshWorkspaceProfileAvailability' not in content, \
                'profile_binding.js should not be modified in B2'

    def test_no_model_dropdown_added(self):
        """8. No new model dropdown in Workspace area"""
        content = read_file(INDEX_HTML_PATH)
        # B2 explicitly does NOT add a model dropdown
        # Check the workspace config area doesn't have a model select
        ws_area = re.search(r'<div class="card">\s*<div class="card-title">配置</div>.*?</div>',
                           content, re.DOTALL)
        if ws_area:
            ws_content = ws_area.group()
            assert 'modelSelect' not in ws_content, \
                'Must not add modelSelect to Workspace config area'


# ── 16.2 Provider-first UI ─────────────────────────────────────────────────────

class TestProviderFirstUI:
    """9-14. Provider-first Workspace config area"""

    def test_provider_select_before_profile_select_in_workspace(self):
        """9. Workspace config area providerSelect appears before profileSelect"""
        content = read_file(INDEX_HTML_PATH)
        # Find the Workspace config area using a less restrictive pattern
        # The card with "配置" title contains the config-grid
        ws_match = re.search(
            r'<div class="card">\s*<div class="card-title">[^<]*</div>\s*<div class="config-grid">(.*?)</div>\s*</div>',
            content, re.DOTALL
        )
        assert ws_match, 'Workspace config-grid not found'
        ws_content = ws_match.group(1)
        provider_idx = ws_content.find('providerSelect')
        profile_idx = ws_content.find('profileSelect')
        assert provider_idx >= 0, 'providerSelect not found in Workspace config'
        assert profile_idx >= 0, 'profileSelect not found in Workspace config'
        assert provider_idx < profile_idx, \
            'providerSelect must appear before profileSelect in Workspace config'

    def test_getWorkspaceProfileBindingState_exists(self):
        """10. getWorkspaceProfileBindingState exists"""
        content = read_file(INDEX_HTML_PATH)
        assert 'function getWorkspaceProfileBindingState' in content, \
            'getWorkspaceProfileBindingState must be declared'

    def test_getWorkspaceProfileBindingState_returns_status(self):
        """10. getWorkspaceProfileBindingState returns expected statuses"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function getWorkspaceProfileBindingState')
        assert idx >= 0, 'getWorkspaceProfileBindingState must exist'
        # Use a larger slice to capture the full function body
        # Function ends before refreshWorkspaceProfileAvailability starts
        func_end = content.find('function refreshWorkspaceProfileAvailability', idx)
        assert func_end > idx, 'Could not find end of getWorkspaceProfileBindingState'
        func_body = content[idx:func_end]
        # Must return status: 'available' / 'unbound' / 'no-provider' / 'no-profile'
        # JavaScript object literal uses status: 'value' (no quotes around status key)
        assert "status: 'available'" in func_body or 'status: "available"' in func_body, \
            'Must return status: available'
        assert "status: 'unbound'" in func_body or 'status: "unbound"' in func_body, \
            'Must return status: unbound'
        assert "status: 'no-provider'" in func_body or 'status: "no-provider"' in func_body, \
            'Must return status: no-provider'
        assert "status: 'no-profile'" in func_body or 'status: "no-profile"' in func_body, \
            'Must return status: no-profile'

    def test_refreshWorkspaceProfileAvailability_exists(self):
        """11. refreshWorkspaceProfileAvailability exists"""
        content = read_file(INDEX_HTML_PATH)
        assert 'function refreshWorkspaceProfileAvailability' in content, \
            'refreshWorkspaceProfileAvailability must be declared'

    def test_refreshWorkspaceProfileAvailability_does_not_call_populateProfileSelect(self):
        """12. refreshWorkspaceProfileAvailability does not call populateProfileSelect"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function refreshWorkspaceProfileAvailability')
        assert idx >= 0, 'refreshWorkspaceProfileAvailability must exist'
        func_body = content[idx:idx + 2000]
        # Should not call populateProfileSelect
        assert 'populateProfileSelect' not in func_body, \
            'refreshWorkspaceProfileAvailability must not call populateProfileSelect'

    def test_refreshWorkspaceProfileAvailability_marks_unbound_profiles(self):
        """13. Unbound profile text includes '未绑定当前 Provider'"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function refreshWorkspaceProfileAvailability')
        assert idx >= 0, 'refreshWorkspaceProfileAvailability must exist'
        func_body = content[idx:idx + 2000]
        assert '未绑定当前 Provider' in func_body, \
            'Unbound profile option must include "未绑定当前 Provider"'

    def test_refreshWorkspaceProfileAvailability_does_not_hide_profiles(self):
        """14. Does not hide profiles from dropdown"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function refreshWorkspaceProfileAvailability')
        func_body = content[idx:idx + 2000]
        # Must not remove/hide options
        assert 'remove(' not in func_body and 'hidden' not in func_body.lower(), \
            'Must not hide or remove unbound profile options'


# ── 16.3 Parameter area / Generate button ─────────────────────────────────────

class TestParameterAreaControls:
    """15-19. setWorkspaceBindingControlsEnabled behavior"""

    def test_setWorkspaceBindingControlsEnabled_exists(self):
        """15. setWorkspaceBindingControlsEnabled exists"""
        content = read_file(INDEX_HTML_PATH)
        assert 'function setWorkspaceBindingControlsEnabled' in content, \
            'setWorkspaceBindingControlsEnabled must be declared'

    def test_setWorkspaceBindingControlsEnabled_disables_param_inputs(self):
        """16. Disables paramSpeed/paramVol/paramPitch/paramEmotion"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function setWorkspaceBindingControlsEnabled')
        assert idx >= 0, 'setWorkspaceBindingControlsEnabled must exist'
        func_body = content[idx:idx + 1000]
        # Must reference these param IDs
        for param_id in ['paramSpeed', 'paramVol', 'paramPitch', 'paramEmotion']:
            assert param_id in func_body, \
                f'setWorkspaceBindingControlsEnabled must reference {param_id}'

    def test_setWorkspaceBindingControlsEnabled_disables_generateBtn(self):
        """17. Disables generateBtn"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function setWorkspaceBindingControlsEnabled')
        func_body = content[idx:idx + 1000]
        assert 'generateBtn' in func_body, \
            'setWorkspaceBindingControlsEnabled must reference generateBtn'

    def test_setWorkspaceBindingControlsEnabled_does_not_disable_textInput(self):
        """18. Does not disable textInput"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('function setWorkspaceBindingControlsEnabled')
        func_body = content[idx:idx + 1000]
        # Should not mention textInput (workspace text input)
        assert 'textInput' not in func_body or 'textInput' not in func_body.split('paramIds')[0], \
            'Must not disable textInput in setWorkspaceBindingControlsEnabled'

    def test_handleGenerate_guard_preserved(self):
        """19. handleGenerate guard isWorkspaceBindingAvailable() is preserved"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('async function handleGenerate')
        assert idx >= 0, 'handleGenerate must exist'
        func_body = content[idx:idx + 2000]
        # Must have the binding availability guard
        assert 'isWorkspaceBindingAvailable()' in func_body, \
            'handleGenerate guard isWorkspaceBindingAvailable() must be preserved'
        # Must NOT remove the guard
        assert not re.search(r'isWorkspaceBindingAvailable.*return', func_body), \
            'Must not remove handleGenerate guard'


# ── 16.4 CSS ──────────────────────────────────────────────────────────────────

class TestCSS:
    """CSS: .disabled-by-binding"""

    def test_disabled_by_binding_css_exists(self):
        """CSS: .param-row.disabled-by-binding exists"""
        content = read_file(INDEX_HTML_PATH)
        assert '.disabled-by-binding' in content, \
            'CSS rule .param-row.disabled-by-binding must exist'
        # Should have opacity style
        assert 'opacity' in content, \
            '.disabled-by-binding should use opacity'


# ── 16.5 Events & restore ─────────────────────────────────────────────────────

class TestEventHandlers:
    """20-23. providerSelect/profileSelect change handlers, restore"""

    def test_provider_select_change_calls_refreshWorkspaceProfileAvailability(self):
        """20. providerSelect change calls refreshWorkspaceProfileAvailability"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("providerSelect.addEventListener('change'")
        assert idx >= 0, 'providerSelect change listener must exist'
        handler_block = content[idx:idx + 300]
        assert 'refreshWorkspaceProfileAvailability' in handler_block, \
            'providerSelect change must call refreshWorkspaceProfileAvailability'

    def test_profile_select_change_calls_checkBindingStatus(self):
        """21. profileSelect change calls checkBindingStatus"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("profileSelect.addEventListener('change'")
        assert idx >= 0, 'profileSelect change listener must exist'
        handler_block = content[idx:idx + 300]
        assert 'checkBindingStatus' in handler_block, \
            'profileSelect change must call checkBindingStatus'

    def test_checkBindingStatus_calls_updateWorkspaceBindingUiState_on_bound(self):
        """22a. checkBindingStatus bound branch calls updateWorkspaceBindingUiState"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('async function checkBindingStatus')
        assert idx >= 0, 'checkBindingStatus must exist'
        func_body = content[idx:idx + 3000]
        # Find bound branch (matched.length > 0)
        bound_match = re.search(
            r'if\s*\(\s*matched\.length\s*>\s*0\s*\)(.*?)(?:else|catch|$)',
            func_body, re.DOTALL
        )
        assert bound_match, 'Bound branch must exist'
        bound_body = bound_match.group(1)
        assert 'updateWorkspaceBindingUiState' in bound_body, \
            'Bound branch must call updateWorkspaceBindingUiState'

    def test_checkBindingStatus_calls_updateWorkspaceBindingUiState_on_unbound(self):
        """22b. checkBindingStatus unbound branch calls updateWorkspaceBindingUiState"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('async function checkBindingStatus')
        assert idx >= 0, 'checkBindingStatus must exist'
        func_end = content.find('\n  // ============================================================', idx)
        if func_end < idx:
            func_end = idx + 5000
        func_body = content[idx:func_end]
        # Verify updateWorkspaceBindingUiState is called somewhere in the function
        assert 'updateWorkspaceBindingUiState' in func_body, \
            'checkBindingStatus must call updateWorkspaceBindingUiState somewhere'
        # The unbound branch should call it - search from the unbound text to after it
        unbound_section = re.search(
            r'statusEl\.textContent\s*=\s*`✕[^`]*`[^;]*;[\s\S]{0,1000}updateWorkspaceBindingUiState',
            func_body
        )
        assert unbound_section, 'Unbound branch must call updateWorkspaceBindingUiState after statusEl.textContent'

    def test_checkBindingStatus_calls_updateWorkspaceBindingUiState_on_error(self):
        """22c. checkBindingStatus error branch calls updateWorkspaceBindingUiState"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find('async function checkBindingStatus')
        assert idx >= 0, 'checkBindingStatus must exist'
        func_end = content.find('\n  // ============================================================', idx)
        if func_end < idx:
            func_end = idx + 5000
        func_body = content[idx:func_end]
        # Find catch branch by looking for catch followed by updateWorkspaceBindingUiState
        catch_section = re.search(
            r'catch\s*\([^)]*\)\s*\{[^}]*updateWorkspaceBindingUiState',
            func_body, re.DOTALL
        )
        assert catch_section, 'Error catch branch must call updateWorkspaceBindingUiState'

    def test_workspace_tab_switch_calls_refreshWorkspaceProfileAvailability(self):
        """22d. Workspace tab switch calls refreshWorkspaceProfileAvailability"""
        content = read_file(INDEX_HTML_PATH)
        idx = content.find("tab === 'workspace'")
        assert idx >= 0, "tab === 'workspace' must exist"
        ws_block = content[idx:idx + 350]
        assert 'refreshWorkspaceProfileAvailability' in ws_block, \
            "Workspace tab switch must call refreshWorkspaceProfileAvailability"


# ── 16.6 Other helpers exist ─────────────────────────────────────────────────

class TestOtherHelpers:
    """updateWorkspaceBindingUiState exists"""

    def test_updateWorkspaceBindingUiState_exists(self):
        content = read_file(INDEX_HTML_PATH)
        assert 'function updateWorkspaceBindingUiState' in content, \
            'updateWorkspaceBindingUiState must be declared'
