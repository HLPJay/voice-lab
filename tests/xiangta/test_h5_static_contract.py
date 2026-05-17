"""
P17-XIANGTA-H5-B7-1 — H5 静态文件契约测试

验证前端静态文件存在、包含必要 API 路径、不含禁止内容。
"""
from pathlib import Path

_H5_DIR = Path(__file__).parent.parent.parent / "apps" / "xiangta-h5"
_DESIGN_DIR = Path(__file__).parent.parent.parent / "design_h5" / "想他了点击版本"


# ── 文件存在 ──────────────────────────────────────────────────────────────────

class TestFilesExist:

    def test_index_html_exists(self):
        assert (_H5_DIR / "index.html").exists()

    def test_styles_css_exists(self):
        assert (_H5_DIR / "styles.css").exists()

    def test_app_js_exists(self):
        assert (_H5_DIR / "app.js").exists()

    def test_readme_exists(self):
        assert (_H5_DIR / "README.md").exists()

    def test_serve_py_exists(self):
        assert (_H5_DIR / "serve.py").exists()

    def test_design_reference_exists(self):
        assert (_H5_DIR / "DESIGN_REFERENCE.md").exists()


# ── app.js API 路径覆盖 ───────────────────────────────────────────────────────

class TestAppJsApiPaths:

    def _src(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def test_calls_bootstrap(self):
        assert "/api/xiangta/bootstrap" in self._src()

    def test_calls_suggestions(self):
        assert "/api/xiangta/suggestions" in self._src()

    def test_calls_tts(self):
        assert "/api/xiangta/tts" in self._src()

    def test_calls_letters(self):
        assert "/api/xiangta/letters" in self._src()


# ── app.js 必要函数 ───────────────────────────────────────────────────────────

class TestAppJsFunctions:

    def _src(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def test_has_load_bootstrap(self):
        assert "loadBootstrap" in self._src()

    def test_has_generate_suggestions(self):
        assert "generateSuggestions" in self._src()

    def test_has_select_suggestion(self):
        assert "selectSuggestion" in self._src()

    def test_has_generate_tts(self):
        assert "generateTts" in self._src()

    def test_has_save_letter(self):
        assert "saveLetter" in self._src()

    def test_has_load_letters(self):
        assert "loadLetters" in self._src()

    def test_has_set_status(self):
        assert "setStatus" in self._src()

    def test_has_api_fetch(self):
        assert "apiFetch" in self._src()

    def test_api_base_is_relative(self):
        src = self._src()
        assert 'API_BASE = ""' in src or "API_BASE=''" in src


# ── app.js 安全：不含禁止内容 ─────────────────────────────────────────────────

class TestAppJsNoForbiddenContent:

    def _src(self):
        return (_H5_DIR / "app.js").read_text(encoding="utf-8")

    def test_no_minimax_api_key(self):
        assert "MINIMAX_API_KEY" not in self._src()

    def test_no_mimo_api_key(self):
        assert "MIMO_API_KEY" not in self._src()

    def test_no_openai_api_key(self):
        assert "OPENAI_API_KEY" not in self._src()

    def test_no_provider_voice_id(self):
        assert "provider_voice_id" not in self._src()

    def test_no_params_json(self):
        assert "params_json" not in self._src()

    def test_no_profile_id_field(self):
        assert "profile_id" not in self._src()


# ── index.html 不引用外部 CDN ─────────────────────────────────────────────────

class TestIndexHtmlNoCdn:

    def _src(self):
        return (_H5_DIR / "index.html").read_text(encoding="utf-8")

    def test_no_cdn_links(self):
        src = self._src()
        cdn_patterns = ["cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com",
                        "fonts.googleapis.com", "cdn.tailwindcss.com"]
        for pattern in cdn_patterns:
            assert pattern not in src, f"index.html 引用了外部 CDN: {pattern}"

    def test_has_viewport_meta(self):
        assert "viewport" in self._src()

    def test_has_app_title(self):
        assert "想Ta了" in self._src()

    def test_links_styles_css(self):
        assert "styles.css" in self._src()

    def test_links_app_js(self):
        assert "app.js" in self._src()


# ── DESIGN_REFERENCE.md 内容 ─────────────────────────────────────────────────

class TestDesignReferenceMd:

    def _src(self):
        return (_H5_DIR / "DESIGN_REFERENCE.md").read_text(encoding="utf-8")

    def test_references_design_dir(self):
        assert "design_h5/想他了点击版本" in self._src()

    def test_references_mobile_design_html(self):
        assert "想他了 · Mobile Design.html" in self._src()

    def test_has_implementation_mapping(self):
        assert "loadBootstrap" in self._src()

    def test_has_design_source_heading(self):
        assert "设计来源" in self._src()


# ── serve.py 结构 ─────────────────────────────────────────────────────────────

class TestServePy:

    def _src(self):
        return (_H5_DIR / "serve.py").read_text(encoding="utf-8")

    def test_imports_staticfiles(self):
        assert "StaticFiles" in self._src()

    def test_mounts_current_dir(self):
        assert "__file__" in self._src()

    def test_no_hardcoded_apps_path(self):
        assert '"apps"' not in self._src() and "'apps'" not in self._src()


# ── 设计目录存在 ──────────────────────────────────────────────────────────────

class TestDesignDirExists:

    def test_design_dir_exists(self):
        assert _DESIGN_DIR.exists(), f"设计目录不存在: {_DESIGN_DIR}"

    def test_mobile_design_html_exists(self):
        assert (_DESIGN_DIR / "想他了 · Mobile Design.html").exists()

    def test_screens_jsx_exists(self):
        assert (_DESIGN_DIR / "screens.jsx").exists()
