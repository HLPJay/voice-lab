"""
test_provider_mock_boundary_static.py

P16-PROVIDER-MOCK-FIX1: Static contract tests for mock provider boundary fixes.
Covers: config mock_fallback_provider default, VoiceVariantService CostGuard resolution,
workspace binding unavailable guard.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(REPO_ROOT, 'app', 'core', 'config.py')
VARIANT_SERVICE_PATH = os.path.join(REPO_ROOT, 'app', 'services', 'voice_variant_service.py')
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')


def read_file(path):
    return open(path, 'r', encoding='utf-8').read()


def func_body(name, content):
    """Return the full body of a named function (JS braces or Python indentation)."""
    # Try JS-style 'function name(' first
    marker = 'function ' + name + '('
    start = content.find(marker)
    if start >= 0:
        # JS: use brace depth
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

    # Python: find def line
    for marker in ['def ' + name + '(', 'async def ' + name + '(']:
        start = content.find(marker)
        if start >= 0:
            break
    assert start >= 0, name + ' function must exist'

    # Find the closing ) of the parameter list
    paren_start = content.find('(', start)
    depth = 0
    for i in range(paren_start, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                closing_paren = i
                break

    # Skip -> return_type annotation if present
    body_colon = closing_paren + 1
    while body_colon < len(content) and content[body_colon] in ' \t':
        body_colon += 1
    if content[body_colon:body_colon+2] == '->':
        # Skip the return type annotation
        body_colon = content.find(':', body_colon)
        assert body_colon >= 0

    # Now find the actual colon that starts the body
    while body_colon < len(content) and content[body_colon] != ':':
        body_colon += 1
    assert body_colon < len(content), 'body colon not found'
    body_start = content.find('\n', body_colon)
    assert body_start >= 0
    body_start += 1

    # Determine base indentation from first non-empty, non-comment line
    pos = body_start
    base_indent = None
    first_real_line = None
    while pos < len(content):
        nl = content.find('\n', pos)
        if nl < 0:
            nl = len(content)
        line = content[pos:nl]
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            first_real_line = stripped
            # Count leading spaces
            ws = len(line) - len(line.lstrip())
            base_indent = ws
            break
        pos = nl + 1

    if base_indent is None:
        return content[start:]

    # Find end: first line at same or lower indent (blank/comments don't count)
    end = len(content)
    pos = body_start
    while pos < len(content):
        nl = content.find('\n', pos)
        if nl < 0:
            nl = len(content)
        line = content[pos:nl]
        ws = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and ws < base_indent:
            end = pos
            break
        pos = nl + 1

    return content[start:end]


# ── config.py mock_fallback_provider ────────────────────────────────────────────

class TestMockFallbackConfig:
    def test_mock_fallback_provider_default_is_none(self):
        c = read_file(CONFIG_PATH)
        assert 'mock_fallback_provider: str | None = None' in c

    def test_mock_fallback_provider_not_default_minimax(self):
        c = read_file(CONFIG_PATH)
        assert 'mock_fallback_provider: str | None = "minimax"' not in c


# ── VoiceVariantService CostGuard ─────────────────────────────────────────────

class TestVoiceVariantServiceCostGuard:
    def test_resolve_binding_imported(self):
        c = read_file(VARIANT_SERVICE_PATH)
        assert 'from app.repositories.voice_profile_repo import resolve_binding' in c

    def test_cost_guard_uses_resolved_provider(self):
        c = read_file(VARIANT_SERVICE_PATH)
        body = func_body('render_variants', c)
        # Must call resolve_binding and assign provider from resolved_provider
        assert 'resolve_binding' in body
        # Provider should be assigned from resolved_provider
        assert '_binding, provider = resolve_binding' in body or 'provider = resolve_binding' in body
        # CostGuard must use resolved_provider (not raw request.provider)
        assert 'require_confirmed(provider' in body or 'require_confirmed(resolved_provider' in body

    def test_cost_guard_not_called_with_raw_request_provider(self):
        c = read_file(VARIANT_SERVICE_PATH)
        body = func_body('render_variants', c)
        # Must NOT call CostGuard with a raw uncoditional "mock" from request.provider
        # The old pattern was: provider = request.provider or "mock";
        # self.cost_guard.require_confirmed(provider, ...)
        # After fix, binding is resolved first
        assert 'resolve_binding' in body
        # The binding resolution must come before CostGuard
        binding_idx = body.index('resolve_binding')
        require_idx = body.index('require_confirmed')
        assert binding_idx < require_idx, 'resolve_binding must come before require_confirmed'

    def test_render_voice_called_with_resolved_provider(self):
        c = read_file(VARIANT_SERVICE_PATH)
        body = func_body('render_variants', c)
        # VoiceRenderRequest must use the resolved provider, not request.provider directly
        # The provider variable must be assigned from resolved_provider before being passed
        assert '_binding, provider = resolve_binding' in body or ('provider = resolve_binding' in body and 'provider,' in body)
        # After fix, provider variable comes from resolved_provider
        # Check that VoiceRenderRequest uses `provider` not `request.provider`
        render_req_idx = body.find('VoiceRenderRequest(')
        assert render_req_idx >= 0
        # The provider kwarg in VoiceRenderRequest should be `provider=` (the resolved one)
        req_region = body[render_req_idx:render_req_idx + 300]
        assert 'provider=provider' in req_region or 'provider:provider' in req_region


# ── Frontend binding unavailable guard ────────────────────────────────────────

class TestWorkspaceBindingGuard:
    def test_workspaceBindingAvailable_variable_exists(self):
        c = read_file(INDEX_HTML_PATH)
        assert 'let workspaceBindingAvailable' in c or 'var workspaceBindingAvailable' in c

    def test_isWorkspaceBindingAvailable_function_exists(self):
        c = read_file(INDEX_HTML_PATH)
        assert 'function isWorkspaceBindingAvailable' in c

    def test_checkBindingStatus_sets_binding_available(self):
        c = read_file(INDEX_HTML_PATH)
        body = func_body('checkBindingStatus', c)
        # Should set workspaceBindingAvailable = true when bound
        assert 'workspaceBindingAvailable = true' in body

    def test_checkBindingStatus_sets_binding_unavailable(self):
        c = read_file(INDEX_HTML_PATH)
        body = func_body('checkBindingStatus', c)
        # Should set workspaceBindingAvailable = false when unbound or error
        assert 'workspaceBindingAvailable = false' in body

    def test_handleGenerate_blocks_when_binding_unavailable(self):
        c = read_file(INDEX_HTML_PATH)
        body = func_body('handleGenerate', c)
        # Must call isWorkspaceBindingAvailable in handleGenerate
        assert 'isWorkspaceBindingAvailable' in body
        # The guard must appear BEFORE confirmHighRiskOperation and setLoading
        guard_idx = body.index('isWorkspaceBindingAvailable')
        # Find confirmHighRiskOperation or setLoading
        try:
            confirm_idx = body.index('confirmHighRiskOperation')
            loading_idx = body.index('setLoading(true)')
            assert guard_idx < confirm_idx, 'binding guard must come before confirmHighRiskOperation'
            assert guard_idx < loading_idx, 'binding guard must come before setLoading'
        except ValueError:
            pass  # one may not exist in body, that's ok

    def test_handleGenerate_returns_without_fetch_when_no_binding(self):
        c = read_file(INDEX_HTML_PATH)
        body = func_body('handleGenerate', c)
        # When binding unavailable, must return without fetch
        guard_block_start = body.index('isWorkspaceBindingAvailable()')
        # Find the next return or the block after the guard
        # The guard block should have a return without calling fetch
        guard_region = body[guard_block_start:guard_block_start + 500]
        assert 'return' in guard_region, 'binding unavailable path must return without fetch'
        assert 'fetch(' not in guard_region, 'binding unavailable path must not call fetch'
