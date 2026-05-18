"""
P19-XIANGTA-VOICE-BINDING-PAGE — Voice Binding Status API 测试

覆盖：
  1. GET /voice-bindings/status 不返回 coreProfileId
  2. placeholder 判断（空 / <...> / todo）
  3. bound + Core 有该 profile → coreAvailable=true
  4. bound + Core 无该 profile → coreAvailable=false
  5. Core 不可用 → 接口不 500
  6. PUT voice-mappings/{id} 写入合法 coreProfileId
  7. 非法 / placeholder coreProfileId 被 writer 拒绝
  8. Admin API 无 token → 403
  9. TTS 未绑定 voicePreset → voice_preset_not_bound
 10. Admin 页面文件存在性
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.config.product_config_writer import ProductConfigWriter
from src.xiangta.services.admin_config_service import AdminConfigService
from src.xiangta.services.product_service import ProductService
from src.xiangta.services.provider_status_service import ProviderStatusService
from src.xiangta.services.voice_preset_mapping_service import (
    VoicePresetMappingService,
    _is_placeholder_profile_id,
)
from src.xiangta.services.error_translator import VoicePresetProfileNotConfiguredError

import src.xiangta.api.routes as routes_module


# ── Fixtures ──────────────────────────────────────────────────────────────────

_ADMIN_HEADERS = {"X-XiangTa-Admin-Token": "test-admin-token"}


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch):
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_ADMIN_TOKEN", "test-admin-token")


@pytest.fixture
def four_voice_mappings(tmp_path, monkeypatch):
    mappings = [
        {
            "id": "female-gentle",
            "label": "温柔女声",
            "desc": "适合想念、晚安",
            "genderStyle": "female",
            "suitableRecipients": ["lover"],
            "recommendedScenes": ["miss", "night"],
            "defaultTone": "gentle",
            "enabled": True,
            "sortOrder": 10,
            "coreProfileId": "<core_profile_id_from_core_profiles>",
            "providerPolicy": "default",
            "renderOverrides": {},
            "notes": None,
        },
        {
            "id": "male-gentle",
            "label": "温和男声",
            "desc": "更沉静",
            "genderStyle": "male",
            "suitableRecipients": ["lover"],
            "recommendedScenes": ["miss", "sorry"],
            "defaultTone": "gentle",
            "enabled": True,
            "sortOrder": 20,
            "coreProfileId": "real-core-profile-001",
            "providerPolicy": "default",
            "renderOverrides": {},
            "notes": None,
        },
        {
            "id": "female-bright",
            "label": "明亮女声",
            "desc": "适合感谢",
            "genderStyle": "female",
            "suitableRecipients": ["friend"],
            "recommendedScenes": ["thanks"],
            "defaultTone": "gentle",
            "enabled": True,
            "sortOrder": 30,
            "coreProfileId": "",
            "providerPolicy": "default",
            "renderOverrides": {},
            "notes": None,
        },
        {
            "id": "male-mature",
            "label": "沉稳男声",
            "desc": "适合安慰",
            "genderStyle": "male",
            "suitableRecipients": ["family"],
            "recommendedScenes": ["comfort"],
            "defaultTone": "restrained",
            "enabled": True,
            "sortOrder": 40,
            "coreProfileId": "fake-gone-profile",
            "providerPolicy": "default",
            "renderOverrides": {},
            "notes": None,
        },
    ]
    (tmp_path / "voice_mappings.json").write_text(
        json.dumps(mappings, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "tone_presets.json").write_text(
        json.dumps([{"id": "gentle", "label": "温柔", "desc": "", "style_hint": "gentle", "enabled": True}]),
        encoding="utf-8",
    )
    return tmp_path, mappings


@pytest.fixture
def svc_with_core_available(four_voice_mappings, monkeypatch):
    """Service with Core available and real profiles."""
    tmp_path, mappings = four_voice_mappings

    from src.xiangta.config.product_config_repository import ProductConfigRepository
    from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService
    from src.xiangta.services.tone_preset_service import TonePresetService
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator
    from src.xiangta.services.tts_task_service import TtsTaskService

    config_repo = ProductConfigRepository(configs_dir=tmp_path)
    writer = ProductConfigWriter(config_dir=tmp_path)
    admin_svc = AdminConfigService(writer=writer)
    provider_status_svc = ProviderStatusService(gateway=None)
    voice_mapping_svc = VoicePresetMappingService(config_repository=config_repo)
    tone_preset_svc = TonePresetService(config_repository=config_repo)
    limits = config_repo.get_limits()

    mock_gw = MagicMock()
    mock_gw.list_profiles = AsyncMock(return_value=[
        {"id": "real-core-profile-001", "name": "真实男声", "gender_style": "male"},
        {"id": "real-core-profile-002", "name": "真实女声", "gender_style": "female"},
    ])

    tts = TtsOrchestrator(
        gateway=mock_gw,
        voice_mapping_service=voice_mapping_svc,
        tone_preset_service=tone_preset_svc,
        max_tts_chars=limits.max_tts_chars,
        use_dry_run=True,
    )
    tts_tasks = TtsTaskService(tts_orchestrator=tts)

    service = ProductService(
        bootstrap=MagicMock(**{"get_bootstrap": AsyncMock(return_value={})}),
        provider_status=provider_status_svc,
        config_repository=config_repo,
        admin_config_service=admin_svc,
        tts=tts,
        tts_tasks=tts_tasks,
    )
    monkeypatch.setattr(routes_module, "create_product_service", lambda: service)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), tmp_path


@pytest.fixture
def svc_without_core(four_voice_mappings, monkeypatch):
    """Service without Core connection."""
    tmp_path, mappings = four_voice_mappings

    from src.xiangta.config.product_config_repository import ProductConfigRepository
    from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService
    from src.xiangta.services.tone_preset_service import TonePresetService
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator
    from src.xiangta.services.tts_task_service import TtsTaskService
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

    config_repo = ProductConfigRepository(configs_dir=tmp_path)
    writer = ProductConfigWriter(config_dir=tmp_path)
    admin_svc = AdminConfigService(writer=writer)
    provider_status_svc = ProviderStatusService(gateway=None)
    voice_mapping_svc = VoicePresetMappingService(config_repository=config_repo)
    tone_preset_svc = TonePresetService(config_repository=config_repo)
    limits = config_repo.get_limits()

    # No gateway — Core not available
    gw = VoiceLabGateway()  # empty gateway
    tts = TtsOrchestrator(
        gateway=gw,
        voice_mapping_service=voice_mapping_svc,
        tone_preset_service=tone_preset_svc,
        max_tts_chars=limits.max_tts_chars,
        use_dry_run=True,
    )
    tts_tasks = TtsTaskService(tts_orchestrator=tts)

    service = ProductService(
        bootstrap=MagicMock(**{"get_bootstrap": AsyncMock(return_value={})}),
        provider_status=provider_status_svc,
        config_repository=config_repo,
        admin_config_service=admin_svc,
        tts=tts,
        tts_tasks=tts_tasks,
    )
    monkeypatch.setattr(routes_module, "create_product_service", lambda: service)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), tmp_path


# ── Test 1-4: GET /voice-bindings/status ─────────────────────────────────────

class TestVoiceBindingsStatus:
    """Tests for GET /api/xiangta/voice-bindings/status."""

    def test_does_not_return_core_profile_id(self, svc_with_core_available):
        """响应中不得包含 coreProfileId 字符串。"""
        client, _ = svc_with_core_available
        r = client.get("/api/xiangta/voice-bindings/status")
        assert r.status_code == 200
        body = r.json()
        for item in body["data"]["items"]:
            assert "coreProfileId" not in item, f"item {item['voicePreset']} 包含 coreProfileId"

    def test_unbound_is_detected(self, svc_with_core_available):
        """coreProfileId 为 placeholder 时 bound=false。"""
        client, _ = svc_with_core_available
        r = client.get("/api/xiangta/voice-bindings/status")
        assert r.status_code == 200
        body = r.json()
        items = {item["voicePreset"]: item for item in body["data"]["items"]}

        # female-gentle: placeholder → unbound
        assert items["female-gentle"]["bound"] is False
        assert items["female-gentle"]["reason"] is not None

        # male-gentle: real profile → bound
        assert items["male-gentle"]["bound"] is True

        # female-bright: empty string → unbound
        assert items["female-bright"]["bound"] is False

        # male-mature: fake profile not in Core → coreAvailable=false
        assert items["male-mature"]["bound"] is True
        assert items["male-mature"]["coreAvailable"] is False

    def test_core_available_when_profile_exists(self, svc_with_core_available):
        """Core 有该 profile 时 coreAvailable=true。"""
        client, _ = svc_with_core_available
        r = client.get("/api/xiangta/voice-bindings/status")
        assert r.status_code == 200
        body = r.json()
        items = {item["voicePreset"]: item for item in body["data"]["items"]}
        assert items["male-gentle"]["coreAvailable"] is True

    def test_core_not_available_when_no_core(self, svc_without_core):
        """Core 不可用时接口不 500，coreAvailable=null。"""
        client, _ = svc_without_core
        r = client.get("/api/xiangta/voice-bindings/status")
        assert r.status_code == 200
        body = r.json()
        for item in body["data"]["items"]:
            assert item["coreAvailable"] is None, f"{item['voicePreset']} coreAvailable 应为 null"

    def test_all_bound_is_false_when_some_unbound(self, svc_with_core_available):
        """有未绑定时 allBound=false。"""
        client, _ = svc_with_core_available
        r = client.get("/api/xiangta/voice-bindings/status")
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["allBound"] is False


# ── Test 5-7: Admin PUT voice-mappings ──────────────────────────────────────

class TestAdminVoiceMappingWrite:
    """Tests for PUT /api/xiangta/admin/voice-mappings/{id}."""

    def test_update_core_profile_id(self, svc_with_core_available):
        """可以写入合法的 coreProfileId。"""
        client, _ = svc_with_core_available
        r = client.put(
            "/api/xiangta/admin/voice-mappings/female-gentle",
            json={"coreProfileId": "new-real-profile", "providerPolicy": "default"},
            headers=_ADMIN_HEADERS,
        )
        assert r.status_code == 200
        assert r.json()["data"]["coreProfileId"] == "new-real-profile"

    def test_rejects_placeholder_core_profile_id(self, svc_with_core_available):
        """占位 coreProfileId 被 writer 拒绝（422）。"""
        client, _ = svc_with_core_available
        r = client.put(
            "/api/xiangta/admin/voice-mappings/female-gentle",
            json={"coreProfileId": "<core_profile_id_from_core_profiles>"},
            headers=_ADMIN_HEADERS,
        )
        assert r.status_code == 422
        assert "coreProfileId" in r.json().get("message", "").lower() or \
               "占位" in r.json().get("message", "")

    def test_rejects_empty_core_profile_id(self, svc_with_core_available):
        """空 coreProfileId 被 writer 拒绝。"""
        client, _ = svc_with_core_available
        r = client.put(
            "/api/xiangta/admin/voice-mappings/female-gentle",
            json={"coreProfileId": ""},
            headers=_ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_admin_without_token_returns_403(self, svc_with_core_available):
        """无 Admin Token 返回 403。"""
        client, _ = svc_with_core_available
        r = client.put(
            "/api/xiangta/admin/voice-mappings/female-gentle",
            json={"coreProfileId": "some-profile"},
        )
        assert r.status_code == 403


# ── Test 8: Placeholder detection ─────────────────────────────────────────────

class TestPlaceholderDetection:
    @pytest.mark.parametrize("value,expected", [
        (None, True),
        ("", True),
        ("<core_profile_id_from_core_profiles>", True),
        ("<some_placeholder>", True),
        ("<placeholder>", True),
        ("todo-something", True),
        ("TODO-core-profile", True),
        ("real-profile-001", False),
        ("core-profile-xyz", False),
        ("profile_123", False),
    ])
    def test_placeholder_detection(self, value, expected):
        assert _is_placeholder_profile_id(value) is expected


# ── Test 9: TTS unbound voice preset error ───────────────────────────────────

class TestTtsUnboundVoicePreset:
    def test_tts_task_returns_voice_preset_not_bound_error(self, svc_with_core_available, monkeypatch):
        """未绑定 voicePreset 时 TTS 返回 voice_preset_not_bound，message 明确。"""
        from src.xiangta.services.voice_preset_mapping_service import VoicePresetProfileNotConfigured

        client, tmp_path = svc_with_core_available
        import src.xiangta.api.routes as routes_module

        # Get the real service from routes
        real_svc = routes_module.create_product_service()

        # Override tts.generate to raise the expected error directly
        async def mock_generate(self, text, voice_preset, tone, recipient, scene, profile_id=None):
            raise VoicePresetProfileNotConfigured(
                "voicePreset 'female-gentle' 尚未配置有效 Core profile，请先在 Admin 配置中绑定 coreProfileId"
            )

        # Monkeypatch the generate method on the real TtsOrchestrator instance
        from src.xiangta.services import tts_orchestrator as tts_module
        original_generate = real_svc._tts.generate
        real_svc._tts.generate = mock_generate.__get__(real_svc._tts, type(real_svc._tts))

        try:
            r = client.post(
                "/api/xiangta/tts/tasks",
                json={
                    "text": "这是一段测试文字。",
                    "voicePreset": "female-gentle",  # unbound (placeholder)
                    "tone": "gentle",
                    "recipient": "lover",
                    "scene": "miss",
                },
            )
            assert r.status_code == 200  # task created
            body = r.json()
            task = body["data"]
            assert task["status"] == "failed", f"expected failed, got {task['status']}"
            assert task["errorKind"] == "voice_preset_not_bound", f"got {task['errorKind']}"
            assert "Admin" in task["message"] or "绑定" in task["message"]
        finally:
            real_svc._tts.generate = original_generate


# ── Test 10: Admin page files exist ───────────────────────────────────────────

class TestAdminPageFiles:
    def test_admin_html_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]  # project root
        admin_html = root / "apps" / "xiangta-h5" / "admin-voice-bindings.html"
        assert admin_html.exists(), f"admin-voice-bindings.html not found at {admin_html}"

    def test_admin_js_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        admin_js = root / "apps" / "xiangta-h5" / "admin-voice-bindings.js"
        assert admin_js.exists(), f"admin-voice-bindings.js not found at {admin_js}"

    def test_admin_css_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        admin_css = root / "apps" / "xiangta-h5" / "admin-voice-bindings.css"
        assert admin_css.exists(), f"admin-voice-bindings.css not found at {admin_css}"

    def test_admin_js_calls_correct_apis(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        admin_js = root / "apps" / "xiangta-h5" / "admin-voice-bindings.js"
        content = admin_js.read_text(encoding="utf-8")
        assert "/api/xiangta/core/profiles" in content
        assert "/api/xiangta/admin/voice-mappings" in content
        assert "/api/xiangta/admin/voice-mappings/" in content
        assert "X-XiangTa-Admin-Token" in content
