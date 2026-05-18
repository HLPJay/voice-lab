"""B9: Core audio link boundary tests."""
import importlib
import inspect


def _get_source(module_path: str) -> str:
    return inspect.getsource(importlib.import_module(module_path))


class TestB9CoreAudioLinkBoundary:
    """B9: Core audio link boundary tests — verify no forbidden imports or API keys."""

    def test_tts_orchestrator_generate_accepts_profile_id_param(self):
        """B9: generate() accepts optional profile_id for direct Core profile path."""
        from src.xiangta.services.tts_orchestrator import TtsOrchestrator
        sig = inspect.signature(TtsOrchestrator.generate)
        assert "profile_id" in sig.parameters

    def test_tts_orchestrator_generate_signature_no_lowlevel_params(self):
        from src.xiangta.services.tts_orchestrator import TtsOrchestrator
        sig = inspect.signature(TtsOrchestrator.generate)
        bad = sig.parameters.keys() & {"voice_id", "model_id", "api_key", "sample_rate", "bitrate"}
        assert not bad

    def test_product_service_reads_xiangta_runtime_config_only(self):
        src = _get_source("src.xiangta.services.product_service")
        assert "XIANGTA_CORE_BASE_URL" in src
        for token in ["MINIMAX_API_KEY", "MIMO_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]:
            assert token not in src, f"product_service.py must not read {token}"

    def test_runtime_config_does_not_read_provider_keys(self):
        src = _get_source("src.xiangta.config.runtime_config")
        for token in ["MINIMAX_API_KEY", "MIMO_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]:
            assert token not in src, f"runtime_config.py must not read {token}"

    def test_voice_lab_gateway_has_list_profiles_method(self):
        from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
        assert hasattr(VoiceLabGateway, "list_profiles")

    def test_voice_lab_gateway_profiles_path_uses_core_constant(self):
        from src.xiangta.services.voice_lab_gateway import CORE_PROFILES_PATH
        assert CORE_PROFILES_PATH == "/api/voice/profiles"

    def test_voice_lab_gateway_render_path_uses_core_constant(self):
        from src.xiangta.services.voice_lab_gateway import CORE_RENDER_PATH
        assert CORE_RENDER_PATH == "/api/voice/render"

    def test_core_http_client_requires_httpx(self):
        src = _get_source("src.xiangta.services.core_http_client")
        assert "httpx" in src

    def test_core_http_client_does_not_read_provider_keys(self):
        src = _get_source("src.xiangta.services.core_http_client")
        for token in ["MINIMAX_API_KEY", "MIMO_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]:
            assert token not in src

    def test_tts_request_schema_has_profile_id_field(self):
        from src.xiangta.api.schemas import TtsRequest
        fields = set(TtsRequest.model_fields.keys())
        assert "profileId" in fields

    def test_tts_request_profile_id_is_optional(self):
        from src.xiangta.api.schemas import TtsRequest
        field = TtsRequest.model_fields["profileId"]
        assert field.is_required() is False

    def test_core_profiles_response_schema_exists(self):
        from src.xiangta.api.schemas import CoreProfilesResponse
        fields = set(CoreProfilesResponse.model_fields.keys())
        assert "data" in fields

    def test_core_profiles_data_has_profiles_field(self):
        from src.xiangta.api.schemas import CoreProfilesData
        fields = set(CoreProfilesData.model_fields.keys())
        assert "profiles" in fields
        assert "total" in fields
        assert "source" in fields

    def test_core_profile_item_has_expected_safe_fields(self):
        from src.xiangta.api.schemas import CoreProfileItem
        fields = set(CoreProfileItem.model_fields.keys())
        expected = {"id", "name", "description", "genderStyle", "ageStyle",
                    "toneStyle", "emotionStyle", "speedStyle", "pauseStyle",
                    "sceneTags", "isActive"}
        assert expected.issubset(fields)

    def test_core_profile_item_no_forbidden_fields(self):
        from src.xiangta.api.schemas import CoreProfileItem
        fields = set(CoreProfileItem.model_fields.keys())
        forbidden = {"api_key", "provider_voice_id", "binding_id", "params_json",
                     "model_id", "voice_id", "provider", "stack_trace"}
        assert forbidden.isdisjoint(fields)

    def test_product_service_has_list_core_profiles_method(self):
        from src.xiangta.services.product_service import ProductService
        assert hasattr(ProductService, "list_core_profiles")

    def test_product_service_generate_tts_accepts_profile_id(self):
        from src.xiangta.services.product_service import ProductService
        sig = inspect.signature(ProductService.generate_tts)
        assert "profile_id" in sig.parameters

    def test_gateway_filter_profile_removes_forbidden_fields(self):
        from src.xiangta.services.voice_lab_gateway import _filter_profile
        raw = {
            "id": "test",
            "name": "Test",
            "api_key": "SECRET",
            "provider_voice_id": "voice_123",
            "binding_id": "bind_456",
            "params_json": "{}",
            "model_id": "model_x",
            "provider": "mock",
        }
        filtered = _filter_profile(raw)
        assert "api_key" not in filtered
        assert "provider_voice_id" not in filtered
        assert "binding_id" not in filtered
        assert "params_json" not in filtered
        assert "model_id" not in filtered
        assert "provider" not in filtered
        assert filtered["id"] == "test"
        assert filtered["name"] == "Test"

    def test_gateway_constants_are_http_path_strings(self):
        from src.xiangta.services.voice_lab_gateway import (
            CORE_PROFILES_PATH, CORE_RENDER_PATH, CORE_STATUS_PATH,
        )
        assert isinstance(CORE_PROFILES_PATH, str)
        assert isinstance(CORE_RENDER_PATH, str)
        assert isinstance(CORE_STATUS_PATH, str)
        assert CORE_PROFILES_PATH == "/api/voice/profiles"
        assert CORE_RENDER_PATH == "/api/voice/render"
        assert CORE_STATUS_PATH == "/api/voice/runtime/status"
