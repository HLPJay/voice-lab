"""P25O: H5 screen scroll container and sticky CTA safe-space CSS checks."""
import os
import re


LAYOUT_CSS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "css", "layout.css"
)


def read_css():
    with open(LAYOUT_CSS_PATH, encoding="utf-8") as f:
        return f.read()


def block(css_text, selector):
    m = re.search(rf"{re.escape(selector)}\s*\{{(.*?)\}}", css_text, re.DOTALL)
    assert m, f"{selector} block not found"
    return m.group(1)


def test_screen_scroll_internal_scroller_contract():
    css = read_css()
    b = block(css, ".screen-scroll")
    assert "height: 100%;" in b
    assert "min-height: 0;" in b
    assert "overflow-y: auto;" in b
    assert "overflow-x: hidden;" in b
    assert "-webkit-overflow-scrolling: touch;" in b


def test_screen_scroll_step_has_sticky_safe_space():
    css = read_css()
    b = block(css, ".screen-scroll-step")
    assert "padding-bottom: calc(" in b
    assert "var(--xt-bottom-safe)" in b
    assert any(px in b for px in ["112px", "96px", "88px"])


def test_home_content_and_phone_shell_contract_unchanged():
    css = read_css()
    home = block(css, ".home-content")
    shell = block(css, ".phone-shell")
    assert "overflow-y: auto;" in home
    assert "overflow: hidden;" in shell
