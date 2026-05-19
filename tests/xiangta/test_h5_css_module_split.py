"""Tests for P23A: CSS module split into css/ subdirectory."""
import os

CSS_DIR = "apps/xiangta-h5/css"
H5_INDEX = "apps/xiangta-h5/index.html"
STYLES_SHIM = "apps/xiangta-h5/styles.css"

EXPECTED_MODULES = [
    "tokens.css",
    "base.css",
    "layout.css",
    "components.css",
    "screens-home.css",
    "screens-compose.css",
    "screens-suggestions-voice.css",
    "screens-result.css",
    "screens-history-letter-settings.css",
    "overlays.css",
]


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestModuleFilesExist:
    def test_css_directory_exists(self):
        assert os.path.isdir(CSS_DIR), "css/ subdirectory must exist"

    def test_all_module_files_exist(self):
        for name in EXPECTED_MODULES:
            path = os.path.join(CSS_DIR, name)
            assert os.path.isfile(path), f"{name} must exist in css/"


class TestModuleContents:
    def test_tokens_has_root_block(self):
        css = _read(f"{CSS_DIR}/tokens.css")
        assert ":root {" in css
        assert "--xt-bg:" in css

    def test_base_has_reset(self):
        css = _read(f"{CSS_DIR}/base.css")
        assert "box-sizing: border-box" in css

    def test_layout_has_phone_shell(self):
        css = _read(f"{CSS_DIR}/layout.css")
        assert ".phone-shell" in css
        assert ".screen" in css

    def test_components_has_cta_button(self):
        css = _read(f"{CSS_DIR}/components.css")
        assert ".cta-button" in css

    def test_overlays_has_opening_overlay(self):
        css = _read(f"{CSS_DIR}/overlays.css")
        assert ".opening-overlay" in css
        assert ".hidden" in css

    def test_screens_result_has_result_styles(self):
        css = _read(f"{CSS_DIR}/screens-result.css")
        assert "result" in css.lower()

    def test_screens_history_has_history_styles(self):
        css = _read(f"{CSS_DIR}/screens-history-letter-settings.css")
        assert ".history" in css or "history" in css

    def test_screens_home_has_home_styles(self):
        css = _read(f"{CSS_DIR}/screens-home.css")
        assert "home" in css.lower()


class TestIndexHtmlUpdated:
    def test_index_links_to_module_files(self):
        html = _read(H5_INDEX)
        for name in EXPECTED_MODULES:
            assert f"/h5/css/{name}" in html, \
                f"index.html must link to /h5/css/{name}"

    def test_index_does_not_link_old_styles_css_directly(self):
        html = _read(H5_INDEX)
        assert 'href="styles.css"' not in html, \
            "index.html must not link directly to styles.css anymore"


class TestShimFileExists:
    def test_styles_css_shim_exists(self):
        assert os.path.isfile(STYLES_SHIM)

    def test_styles_css_contains_imports(self):
        css = _read(STYLES_SHIM)
        assert "@import" in css, "styles.css shim must use @import"
        assert "tokens.css" in css
