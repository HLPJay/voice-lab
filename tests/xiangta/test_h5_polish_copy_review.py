"""
Small copy-review checks for P25C H5 polish.
"""

H5_APP = "apps/xiangta-h5/app.js"
H5_INDEX = "apps/xiangta-h5/index.html"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fn_body(js: str, signature: str, window: int = 2200) -> str:
    idx = js.find(signature)
    assert idx >= 0, f"{signature} not found"
    return js[idx:idx + window]


def test_bootstrap_failure_copy_no_longer_mentions_organizing():
    js = _read(H5_APP)
    body = _fn_body(js, "async function loadBootstrap()")
    assert "启动配置加载失败，请刷新重试" in body
    assert "这次整理没成功，可以稍后重试" not in body


def test_copywriting_timeout_copy_is_still_present():
    js = _read(H5_APP)
    assert "这次整理超时了，可以稍后重试" in js


def test_visible_copy_no_longer_says_server_does_not_save():
    html = _read(H5_INDEX)
    js = _read(H5_APP)
    combined = html + "\n" + js
    assert "服务器不保存" not in combined
    assert "只保存在这台设备" not in combined
    assert "信笺仅保存在这台设备" not in combined


def test_storage_copy_mentions_current_service():
    html = _read(H5_INDEX)
    js = _read(H5_APP)
    combined = html + "\n" + js
    assert "保存在当前服务中" in combined


def test_tts_payload_is_unchanged():
    js = _read(H5_APP)
    body = _fn_body(js, "async function generateTtsTask()", window=3000)
    assert "text: text," in body
    assert "voicePreset: state.selectedVoice," in body
    assert "tone: state.selectedTone," in body
    assert "recipient: state.selectedRecipient," in body
    assert "scene: state.selectedScene," in body
