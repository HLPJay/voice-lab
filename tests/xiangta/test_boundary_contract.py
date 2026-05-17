"""
P17-XIANGTA-INIT-A0-FIX1 边界合约测试

验证 XiangTa 产品层配置与公共接口不包含底层 Provider 参数。
这些测试保护架构边界，防止 voice_id/model_id/sample_rate/bitrate 等字段
泄露到产品层公共结构中。
"""
import json
import inspect
from pathlib import Path

import pytest

# ── 禁止字段集合 ──────────────────────────────────────────────────────────────

FORBIDDEN_KEYS = {
    "voice_id",
    "model_id",
    "sample_rate",
    "bitrate",
    "api_key",
    "minimax_api_key",
    "mimo_api_key",
}

FORBIDDEN_PUBLIC_FIELDS = {
    "coreProfileId",
    "core_profile_id",
    "profile_id",
    "provider",
    "model",
    "provider_voice_id",
    "binding_id",
    "params_json",
    "api_key",
}

_CONFIGS_DIR = Path(__file__).parent.parent.parent / "src" / "xiangta" / "configs"


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _collect_keys(obj, seen=None) -> set[str]:
    """递归收集 dict/list 结构中所有的 key。"""
    if seen is None:
        seen = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            seen.add(k)
            _collect_keys(v, seen)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, seen)
    return seen


def assert_no_forbidden_keys(data, source: str):
    keys = _collect_keys(data)
    bad = keys & FORBIDDEN_KEYS
    assert not bad, (
        f"{source} 包含禁止的底层参数字段：{bad}\n"
        f"这些字段属于 Voice Lab Core 内部，不得出现在 XiangTa 产品层配置中。"
    )


# ── voice_presets.json 测试 ───────────────────────────────────────────────────

class TestVoicePresetsJson:

    def setup_method(self):
        with open(_CONFIGS_DIR / "voice_presets.json", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_is_list(self):
        assert isinstance(self.data, list), "voice_presets.json 应为 JSON 数组"

    def test_no_forbidden_keys(self):
        assert_no_forbidden_keys(self.data, "voice_presets.json")

    def test_no_core_params_field(self):
        for item in self.data:
            assert "_core_params" not in item, (
                f"voice_presets.json 中的 {item.get('id')} 仍包含 _core_params，"
                f"应已移除。"
            )

    def test_required_product_fields(self):
        required = {"id", "name", "desc", "core_binding_key", "enabled"}
        for item in self.data:
            missing = required - set(item.keys())
            assert not missing, (
                f"voice_presets.json 中的 {item.get('id')} 缺少字段：{missing}"
            )

    def test_core_binding_key_format(self):
        for item in self.data:
            key = item.get("core_binding_key", "")
            assert key.startswith("xiangta_"), (
                f"core_binding_key 应以 'xiangta_' 开头，得到：{key!r}"
            )


# ── tone_presets.json 测试 ────────────────────────────────────────────────────

class TestTonePresetsJson:

    def setup_method(self):
        with open(_CONFIGS_DIR / "tone_presets.json", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_is_list(self):
        assert isinstance(self.data, list)

    def test_no_forbidden_keys(self):
        assert_no_forbidden_keys(self.data, "tone_presets.json")

    def test_no_provider_param_fields(self):
        provider_params = {"speed", "speed_delta", "pitch", "emotion",
                           "provider_param", "sample_rate"}
        for item in self.data:
            bad = set(item.keys()) & provider_params
            assert not bad, (
                f"tone_presets.json 中的 {item.get('id')} 包含 Provider 参数字段：{bad}"
            )

    def test_required_product_fields(self):
        required = {"id", "label", "desc", "style_hint", "enabled"}
        for item in self.data:
            missing = required - set(item.keys())
            assert not missing, (
                f"tone_presets.json 中的 {item.get('id')} 缺少字段：{missing}"
            )


# ── PresetMapper 接口测试 ─────────────────────────────────────────────────────

class TestPresetMapperInterface:

    def test_has_resolve_binding_method(self):
        from src.xiangta.services.preset_mapper import PresetMapper
        assert hasattr(PresetMapper, "resolve_binding"), (
            "PresetMapper 应有 resolve_binding() 方法（不是 resolve_voice）"
        )

    def test_resolve_binding_signature_no_forbidden_params(self):
        from src.xiangta.services.preset_mapper import PresetMapper
        sig = inspect.signature(PresetMapper.resolve_binding)
        param_names = set(sig.parameters.keys()) - {"self"}
        bad = param_names & FORBIDDEN_KEYS
        assert not bad, (
            f"PresetMapper.resolve_binding() 参数中包含禁止字段：{bad}"
        )

    def test_no_resolve_voice_returning_forbidden(self):
        """resolve_voice() 若存在，其文档不应承诺返回底层参数。"""
        from src.xiangta.services.preset_mapper import PresetMapper
        if hasattr(PresetMapper, "resolve_voice"):
            doc = (PresetMapper.resolve_voice.__doc__ or "").lower()
            for key in FORBIDDEN_KEYS:
                assert key.lower() not in doc, (
                    f"PresetMapper.resolve_voice docstring 提及了禁止字段 '{key}'，"
                    f"请改用 resolve_binding()。"
                )


# ── VoiceLabGateway 接口测试 ──────────────────────────────────────────────────

class TestVoiceLabGatewayInterface:

    def test_generate_tts_signature_no_forbidden_params(self):
        from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
        sig = inspect.signature(VoiceLabGateway.generate_tts)
        param_names = set(sig.parameters.keys()) - {"self"}
        bad = param_names & FORBIDDEN_KEYS
        assert not bad, (
            f"VoiceLabGateway.generate_tts() 签名中包含禁止的 Provider 参数：{bad}\n"
            f"Provider-specific 参数应在 gateway 内部或 Core 内部解析，不得暴露给调用方。"
        )

    def test_generate_tts_accepts_core_render_target(self):
        from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
        sig = inspect.signature(VoiceLabGateway.generate_tts)
        assert "target" in sig.parameters, (
            "VoiceLabGateway.generate_tts() 应接受 CoreRenderTarget 参数"
        )


# ── API Schemas 测试 ──────────────────────────────────────────────────────────

class TestApiSchemas:

    def test_tts_request_no_forbidden_fields(self):
        from src.xiangta.api.schemas import TtsRequest
        fields = set(TtsRequest.model_fields.keys())
        bad = fields & FORBIDDEN_KEYS
        assert not bad, (
            f"TtsRequest 包含禁止的底层字段：{bad}"
        )

    def test_tts_data_no_forbidden_fields(self):
        from src.xiangta.api.schemas import TtsData
        fields = set(TtsData.model_fields.keys())
        bad = fields & FORBIDDEN_KEYS
        assert not bad, (
            f"TtsData 响应包含禁止的底层字段：{bad}"
        )

    def test_provider_status_data_no_forbidden_fields(self):
        from src.xiangta.api.schemas import ProviderStatusData
        fields = set(ProviderStatusData.model_fields.keys())
        bad = fields & FORBIDDEN_KEYS
        assert not bad, (
            f"ProviderStatusData 包含禁止的底层字段：{bad}"
        )

    def test_provider_kind_includes_not_integrated(self):
        from src.xiangta.api.schemas import ProviderKind
        # ProviderKind 是 Literal，检查其 __args__
        args = getattr(ProviderKind, "__args__", ())
        assert "not_integrated" in args, (
            "ProviderKind 应包含 'not_integrated' 状态，表示尚未接入真实 Provider"
        )

    def test_tts_contract_no_forbidden_fields(self):
        from src.xiangta.api.schemas import TtsContract
        fields = set(TtsContract.model_fields.keys())
        forbidden = FORBIDDEN_KEYS | {"coreBindingKey", "core_binding_key"}
        bad = fields & forbidden
        assert not bad, f"TtsContract 包含禁止的底层字段：{bad}"

    def test_bootstrap_voice_preset_schema_does_not_expose_core_fields(self):
        from src.xiangta.api.schemas import VoicePresetItem

        fields = set(VoicePresetItem.model_fields.keys())
        forbidden = {
            "core_binding_key", "coreBindingKey", "coreProfileId",
            "core_profile_id", "profile_id", "provider", "model",
            "provider_voice_id", "binding_id", "params_json",
        }
        assert forbidden.isdisjoint(fields), (
            f"VoicePresetItem 不得暴露 Core 字段：{forbidden & fields}"
        )


# ── A2 架构边界：import 隔离 ──────────────────────────────────────────────────

class TestA2ImportBoundary:
    """
    验证产品层各模块不直接 import src.voice_lab.*。
    product_service、routes 只能通过 voice_lab_gateway 访问 Core 边界。
    tts_orchestrator 不直接 import 真实 Provider。
    """

    def _get_source(self, module_path: str) -> str:
        import importlib
        import inspect
        mod = importlib.import_module(module_path)
        return inspect.getsource(mod)

    def test_routes_does_not_import_voice_lab_directly(self):
        src = self._get_source("src.xiangta.api.routes")
        assert "from src.voice_lab" not in src, (
            "routes.py 不得直接 import src.voice_lab.*"
        )
        assert "import src.voice_lab" not in src, (
            "routes.py 不得直接 import src.voice_lab.*"
        )

    def test_product_service_does_not_import_voice_lab_directly(self):
        src = self._get_source("src.xiangta.services.product_service")
        assert "from src.voice_lab" not in src, (
            "product_service.py 不得直接 import src.voice_lab.*"
        )
        assert "import src.voice_lab" not in src, (
            "product_service.py 不得直接 import src.voice_lab.*"
        )

    def test_tts_orchestrator_does_not_import_voice_lab_directly(self):
        src = self._get_source("src.xiangta.services.tts_orchestrator")
        assert "from src.voice_lab" not in src, (
            "tts_orchestrator.py 不得直接 import src.voice_lab.*"
        )
        assert "import src.voice_lab" not in src, (
            "tts_orchestrator.py 不得直接 import src.voice_lab.*"
        )

    def test_tts_orchestrator_does_not_import_provider_adapter(self):
        src = self._get_source("src.xiangta.services.tts_orchestrator")
        provider_imports = ["minimax", "mimo", "openai", "azure", "elevenlabs"]
        for token in provider_imports:
            assert token not in src.lower(), (
                f"tts_orchestrator.py 不得直接 import Provider adapter（检测到：{token}）"
            )

    def test_tts_orchestrator_does_not_import_preset_mapper(self):
        src = self._get_source("src.xiangta.services.tts_orchestrator")
        assert "preset_mapper" not in src, "tts_orchestrator.py 不应继续依赖 PresetMapper"

    def test_gateway_dry_run_signature_no_forbidden_params(self):
        import inspect
        from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
        sig = inspect.signature(VoiceLabGateway.generate_tts_dry_run)
        param_names = set(sig.parameters.keys()) - {"self"}
        bad = param_names & FORBIDDEN_KEYS
        assert not bad, (
            f"VoiceLabGateway.generate_tts_dry_run() 签名包含禁止参数：{bad}"
        )

    def test_bootstrap_service_does_not_import_voice_lab_directly(self):
        src = self._get_source("src.xiangta.services.bootstrap_service")
        assert "from src.voice_lab" not in src
        assert "import src.voice_lab" not in src

    def test_bootstrap_service_does_not_import_app_modules(self):
        src = self._get_source("src.xiangta.services.bootstrap_service")
        assert "from app." not in src
        assert "import app." not in src

    def test_bootstrap_service_does_not_read_environment(self):
        src = self._get_source("src.xiangta.services.bootstrap_service")
        assert "os.environ" not in src

    def test_bootstrap_service_does_not_call_get_provider(self):
        src = self._get_source("src.xiangta.services.bootstrap_service")
        assert "get_provider(" not in src

    def test_bootstrap_service_does_not_read_legacy_voice_presets_loader(self):
        src = self._get_source("src.xiangta.services.bootstrap_service")
        assert "load_voice_presets(" not in src, (
            "BootstrapService 不应继续直接读取旧的 voice_presets.json"
        )


class TestProductConfigRepositoryBoundary:

    def _get_source(self, module_path: str) -> str:
        import importlib
        import inspect
        mod = importlib.import_module(module_path)
        return inspect.getsource(mod)

    def test_repository_does_not_import_app_modules(self):
        src = self._get_source("src.xiangta.config.product_config_repository")
        assert "from app." not in src
        assert "import app." not in src

    def test_repository_does_not_import_voice_lab_directly(self):
        src = self._get_source("src.xiangta.config.product_config_repository")
        assert "from src.voice_lab" not in src
        assert "import src.voice_lab" not in src

    def test_repository_does_not_read_environment(self):
        src = self._get_source("src.xiangta.config.product_config_repository")
        forbidden_tokens = ["os.environ", "MINIMAX_API_KEY", "MIMO_API_KEY", "OPENAI_API_KEY"]
        for token in forbidden_tokens:
            assert token not in src, (
                f"product_config_repository.py 不得读取环境或 API key（检测到：{token}）"
            )

    def test_public_voice_preset_model_does_not_expose_core_fields(self):
        from dataclasses import fields

        from src.xiangta.config.product_config_models import PublicVoicePreset

        public_fields = {field.name for field in fields(PublicVoicePreset)}
        assert FORBIDDEN_PUBLIC_FIELDS.isdisjoint(public_fields), (
            f"PublicVoicePreset 不得暴露 Core 字段：{FORBIDDEN_PUBLIC_FIELDS & public_fields}"
        )


class TestMappingServicesBoundary:
    def _get_source(self, module_path: str) -> str:
        import importlib
        import inspect
        mod = importlib.import_module(module_path)
        return inspect.getsource(mod)

    def test_voice_preset_mapping_service_does_not_import_app_modules(self):
        src = self._get_source("src.xiangta.services.voice_preset_mapping_service")
        assert "from app." not in src
        assert "import app." not in src

    def test_tone_preset_service_does_not_import_app_modules(self):
        src = self._get_source("src.xiangta.services.tone_preset_service")
        assert "from app." not in src
        assert "import app." not in src

    def test_voice_preset_mapping_service_does_not_read_environment(self):
        src = self._get_source("src.xiangta.services.voice_preset_mapping_service")
        assert "os.environ" not in src

    def test_tone_preset_service_does_not_read_environment(self):
        src = self._get_source("src.xiangta.services.tone_preset_service")
        assert "os.environ" not in src


class TestB14BoundaryCloseout:
    def _get_source(self, module_path: str) -> str:
        import importlib
        import inspect
        mod = importlib.import_module(module_path)
        return inspect.getsource(mod)

    def test_tts_orchestrator_does_not_import_bootstrap_config(self):
        src = self._get_source("src.xiangta.services.tts_orchestrator")
        assert "src.xiangta.config.bootstrap_config" not in src

    def test_tts_orchestrator_does_not_import_product_config_repository(self):
        src = self._get_source("src.xiangta.services.tts_orchestrator")
        assert "ProductConfigRepository" not in src

    def test_provider_status_service_does_not_import_app_modules(self):
        src = self._get_source("src.xiangta.services.provider_status_service")
        assert "from app." not in src
        assert "import app." not in src

    def test_provider_status_service_does_not_import_voice_lab_directly(self):
        src = self._get_source("src.xiangta.services.provider_status_service")
        assert "from src.voice_lab" not in src
        assert "import src.voice_lab" not in src

    def test_provider_status_service_does_not_read_environment(self):
        src = self._get_source("src.xiangta.services.provider_status_service")
        assert "os.environ" not in src

    def test_provider_status_service_does_not_call_get_provider(self):
        src = self._get_source("src.xiangta.services.provider_status_service")
        assert "get_provider(" not in src


class TestB2B1aGatewayBoundary:
    def _get_source(self, module_path: str) -> str:
        import importlib
        import inspect
        mod = importlib.import_module(module_path)
        return inspect.getsource(mod)

    def test_gateway_does_not_import_app_repositories(self):
        src = self._get_source("src.xiangta.services.voice_lab_gateway")
        assert "app.repositories" not in src

    def test_gateway_does_not_import_app_providers(self):
        src = self._get_source("src.xiangta.services.voice_lab_gateway")
        assert "app.providers" not in src

    def test_gateway_does_not_reference_render_plan(self):
        src = self._get_source("src.xiangta.services.voice_lab_gateway")
        assert "RenderPlan" not in src

    def test_gateway_does_not_call_get_provider(self):
        src = self._get_source("src.xiangta.services.voice_lab_gateway")
        assert "get_provider(" not in src

    def test_gateway_does_not_read_environment(self):
        src = self._get_source("src.xiangta.services.voice_lab_gateway")
        assert "os.environ" not in src
