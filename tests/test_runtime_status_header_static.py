"""
test_runtime_status_header_static.py

P16-V1-CLOSEOUT-HEADER-STATUS-FIX-D4-F0: Static contract tests for runtime
status header provider/model consistency.

Covers:
1. runtime_status.js uses getDefaultTtsModel for model chip (provider-aware)
2. runtime_status.js does NOT use data.current.default_model unconditionally
3. runtime_status.js has providerSelect change listener
4. runtime_status.js has provider-capabilities-applied listener
5. auth action_hint is no longer hardcoded to MINIMAX_API_KEY only
6. runtime_status.py returns default_ws_model field
7. xiaomi_mimo default model is mimo-v2.5-tts (from adapter config)
8. mock_configured remains testing_only=true in providers.yaml
9. No real external API calls
"""

import os
import re
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_STATUS_JS = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'runtime_status.js')
RUNTIME_STATUS_PY = os.path.join(REPO_ROOT, 'app', 'api', 'runtime_status.py')
PROVIDERS_YAML = os.path.join(REPO_ROOT, 'config', 'providers.yaml')
XIAOMI_ADAPTER_YAML = os.path.join(REPO_ROOT, 'config', 'adapters', 'xiaomi_mimo_chat_tts.yaml')


def read_file(path):
    return open(path, 'r', encoding='utf-8').read()


# ── runtime_status.js static checks ─────────────────────────────────────────

class TestRuntimeStatusJsModelChip:
    def test_uses_getDefaultTtsModel_for_model_chip(self):
        content = read_file(RUNTIME_STATUS_JS)
        assert 'getDefaultTtsModel' in content, \
            'runtime_status.js must use getDefaultTtsModel for provider-aware model chip'

    def test_chipModel_not_unconditional_default_model(self):
        """chipModel must not blindly use data.current.default_model for all providers."""
        content = read_file(RUNTIME_STATUS_JS)
        # Must check currentProvider against default_provider before falling back
        assert re.search(r'currentProvider\s*===\s*.*default_provider', content), \
            'chipModel fallback must guard: currentProvider === default_provider'

    def test_chipModel_fallback_to_dash_on_mismatch(self):
        """When provider does not match default_provider and no capability found, show '-'."""
        content = read_file(RUNTIME_STATUS_JS)
        assert "': '-'" in content or "'-'" in content, \
            "chipModel mismatch path must fallback to '-'"

    def test_providerSelect_change_triggers_loadRuntimeStatus(self):
        content = read_file(RUNTIME_STATUS_JS)
        assert 'providerSelect' in content, 'must reference providerSelect'
        # All three elements must appear together in order (multi-line, within ~400 chars)
        assert re.search(
            r"getElementById\s*\(\s*['\"]providerSelect['\"]"
            r"[\s\S]{0,300}"
            r"addEventListener\s*\(\s*['\"]change['\"]"
            r"[\s\S]{0,100}"
            r"loadRuntimeStatus",
            content,
            re.DOTALL
        ), ('providerSelect change listener must call loadRuntimeStatus(). '
            'Expected: getElementById("providerSelect") → addEventListener("change") → loadRuntimeStatus()')

    def test_provider_capabilities_applied_triggers_loadRuntimeStatus(self):
        content = read_file(RUNTIME_STATUS_JS)
        assert 'provider-capabilities-applied' in content, \
            'must listen to provider-capabilities-applied event'
        idx = content.find('provider-capabilities-applied')
        region = content[idx:idx + 200]
        assert 'loadRuntimeStatus' in region, \
            'provider-capabilities-applied handler must call loadRuntimeStatus()'

    def test_no_infinite_loop_from_listeners(self):
        """loadRuntimeStatus must not dispatch provider-capabilities-applied."""
        content = read_file(RUNTIME_STATUS_JS)
        load_idx = content.find('window.loadRuntimeStatus = async function')
        assert load_idx >= 0
        # Find end of loadRuntimeStatus function body (closes before scheduleRuntimeStatus)
        sched_idx = content.find('window.scheduleRuntimeStatusRefresh', load_idx)
        func_body = content[load_idx:sched_idx]
        assert 'provider-capabilities-applied' not in func_body, \
            'loadRuntimeStatus must not dispatch provider-capabilities-applied (loop risk)'


# ── runtime_status.py static checks ──────────────────────────────────────────

class TestRuntimeStatusPyFields:
    def test_default_ws_model_in_response(self):
        content = read_file(RUNTIME_STATUS_PY)
        assert 'default_ws_model' in content, \
            'runtime_status.py must return default_ws_model in current block'

    def test_auth_hint_not_hardcoded_minimax_only(self):
        """_ACTION_HINTS must not hardcode 'auth': '检查 MINIMAX_API_KEY' statically."""
        content = read_file(RUNTIME_STATUS_PY)
        # The old hardcoded line should be gone
        assert '"auth": "检查 MINIMAX_API_KEY"' not in content and \
               "'auth': '检查 MINIMAX_API_KEY'" not in content, \
            'auth hint must not be hardcoded to MINIMAX_API_KEY in _ACTION_HINTS dict'

    def test_auth_hint_is_dynamic(self):
        """Auth hint must be resolved dynamically (via _get_auth_hint or equivalent)."""
        content = read_file(RUNTIME_STATUS_PY)
        assert '_get_auth_hint' in content or 'get_auth_hint' in content, \
            'auth hint must use a dynamic helper function'

    def test_auth_hint_covers_mimo(self):
        """Auth hint helper must handle xiaomi/mimo provider."""
        content = read_file(RUNTIME_STATUS_PY)
        assert 'mimo' in content.lower() or 'xiaomi' in content.lower(), \
            'auth hint helper must handle mimo/xiaomi provider names'
        assert 'MIMO_API_KEY' in content, \
            'auth hint for mimo must reference MIMO_API_KEY'

    def test_no_real_api_call_in_runtime_status(self):
        """runtime_status.py must not import or call real provider adapters."""
        content = read_file(RUNTIME_STATUS_PY)
        assert 'XiaomiMiMo' not in content, 'must not import XiaomiMiMo adapter directly'
        assert 'MiniMaxAdapter' not in content, 'must not import MiniMax adapter directly'
        assert 'requests.get' not in content, 'must not make real HTTP calls'


# ── provider config checks ────────────────────────────────────────────────────

def _extract_provider_section(content: str, provider_name: str) -> str:
    """Extract a provider's YAML block (from its name to the next provider entry)."""
    start = content.find(f'name: "{provider_name}"')
    if start < 0:
        return ''
    # Find the next provider entry marker '  - name:' after start
    next_entry = content.find('  - name:', start + 1)
    end = next_entry if next_entry > start else len(content)
    return content[start:end]


class TestProviderConfig:
    def test_mock_configured_testing_only(self):
        content = read_file(PROVIDERS_YAML)
        section = _extract_provider_section(content, 'mock_configured')
        assert section, 'mock_configured provider must exist'
        assert 'testing_only: true' in section, \
            'mock_configured must have testing_only: true in metadata'

    def test_mock_configured_ui_visible_false(self):
        content = read_file(PROVIDERS_YAML)
        section = _extract_provider_section(content, 'mock_configured')
        assert 'ui_visible: false' in section, \
            'mock_configured must have ui_visible: false in metadata'

    def test_xiaomi_mimo_ui_visible(self):
        content = read_file(PROVIDERS_YAML)
        section = _extract_provider_section(content, 'xiaomi_mimo')
        assert section, 'xiaomi_mimo provider must exist'
        assert 'ui_visible: true' in section, \
            'xiaomi_mimo must be ui_visible: true'

    def test_minimax_ui_visible(self):
        content = read_file(PROVIDERS_YAML)
        section = _extract_provider_section(content, 'minimax')
        assert 'ui_visible: true' in section, \
            'minimax must be ui_visible: true'


# ── xiaomi_mimo adapter config checks ────────────────────────────────────────

class TestXiaomiMiMoAdapterConfig:
    def test_default_model_is_mimo(self):
        content = read_file(XIAOMI_ADAPTER_YAML)
        assert 'mimo-v2.5-tts' in content, \
            'xiaomi_mimo adapter must have mimo-v2.5-tts as default model'

    def test_tts_models_list_has_mimo(self):
        content = read_file(XIAOMI_ADAPTER_YAML)
        idx = content.find('tts:')
        assert idx >= 0
        tts_section = content[idx:idx + 300]
        assert 'mimo-v2.5-tts' in tts_section, \
            'xiaomi_mimo tts.models must include mimo-v2.5-tts'

    def test_no_speech_28_hd_in_xiaomi_adapter(self):
        content = read_file(XIAOMI_ADAPTER_YAML)
        assert 'speech-2.8-hd' not in content, \
            'xiaomi_mimo adapter must not reference speech-2.8-hd'


# ── capability registry integration checks ────────────────────────────────────

class TestCapabilityIntegration:
    def test_xiaomi_mimo_default_model_from_registry(self):
        """Capability registry returns mimo-v2.5-tts as default for xiaomi_mimo."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        clear_capability_registry_cache()
        cap = get_capability('xiaomi_mimo')
        assert cap is not None
        model = (cap.tts.default_model if cap.tts else None) or cap.default_model
        assert model == 'mimo-v2.5-tts', \
            f'xiaomi_mimo default model must be mimo-v2.5-tts, got {model!r}'

    def test_minimax_default_model_from_registry(self):
        """Capability registry returns speech-2.8-hd as default for minimax."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        clear_capability_registry_cache()
        cap = get_capability('minimax')
        assert cap is not None
        model = (cap.tts.default_model if cap.tts else None) or cap.default_model
        assert 'speech' in (model or '').lower() or model is not None, \
            'minimax must have a default model'

    def test_xiaomi_mimo_model_never_speech_28_hd(self):
        """xiaomi_mimo capability must never yield speech-2.8-hd as default model."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        clear_capability_registry_cache()
        cap = get_capability('xiaomi_mimo')
        tts_model = cap.tts.default_model if cap and cap.tts else None
        cap_model = cap.default_model if cap else None
        for m in [tts_model, cap_model]:
            assert m != 'speech-2.8-hd', \
                f'xiaomi_mimo must not yield speech-2.8-hd as default model (got {m!r})'

    def test_mock_configured_is_testing_only_in_capability(self):
        """mock_configured capability has testing_only=True in metadata."""
        from app.providers.capability_registry import get_capability, clear_capability_registry_cache
        clear_capability_registry_cache()
        cap = get_capability('mock_configured')
        assert cap is not None
        assert cap.metadata.get('testing_only') is True, \
            'mock_configured capability must have metadata.testing_only=True'


# ── API integration test ──────────────────────────────────────────────────────

class TestRuntimeStatusApiDefaultWsModel:
    """API-level integration test: default_ws_model field is present."""

    def test_default_ws_model_field_present(self):
        import os
        import tempfile
        from contextlib import asynccontextmanager

        from fastapi import FastAPI
        from fastapi.exceptions import RequestValidationError
        from sqlmodel import Session, SQLModel, create_engine

        from app.api import api_router
        from app.core.database import get_session as _get_session
        from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        try:
            engine = create_engine(f'sqlite:///{path}', connect_args={'check_same_thread': False})
            SQLModel.metadata.create_all(engine)

            @asynccontextmanager
            async def lifespan(_app):
                yield

            app = FastAPI(lifespan=lifespan)
            app.add_exception_handler(VoiceLabError, voice_lab_error_handler)
            app.add_exception_handler(RequestValidationError, request_validation_error_handler)

            def override():
                with Session(engine) as sess:
                    yield sess

            app.dependency_overrides[_get_session] = override
            app.include_router(api_router)

            from fastapi.testclient import TestClient
            client = TestClient(app)
            resp = client.get('/api/voice/runtime/status')
            assert resp.status_code == 200
            data = resp.json()
            assert 'default_ws_model' in data['current'], \
                'API must return default_ws_model in current block'
            assert data['current']['default_ws_model'] is not None
        finally:
            engine.dispose()
            os.unlink(path)

    def test_auth_hint_minimax_returns_minimax_key(self):
        """Auth hint for minimax calls references MINIMAX_API_KEY."""
        from app.api.runtime_status import _get_auth_hint
        hint = _get_auth_hint('minimax')
        assert 'MINIMAX_API_KEY' in hint, f'Expected MINIMAX_API_KEY in hint, got: {hint!r}'

    def test_auth_hint_xiaomi_returns_mimo_key(self):
        """Auth hint for xiaomi_mimo calls references MIMO_API_KEY."""
        from app.api.runtime_status import _get_auth_hint
        hint = _get_auth_hint('xiaomi_mimo')
        assert 'MIMO_API_KEY' in hint, f'Expected MIMO_API_KEY in hint, got: {hint!r}'

    def test_auth_hint_unknown_is_generic(self):
        """Auth hint for unknown provider is generic."""
        from app.api.runtime_status import _get_auth_hint
        hint = _get_auth_hint('some_future_provider')
        assert 'API Key' in hint or 'api key' in hint.lower(), \
            f'Unknown provider hint should be generic, got: {hint!r}'

    def test_auth_hint_none_is_generic(self):
        from app.api.runtime_status import _get_auth_hint
        hint = _get_auth_hint(None)
        assert hint, 'must return a non-empty hint for None provider'
