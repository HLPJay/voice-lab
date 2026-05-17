import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, "app", "static", "index.html")


def read_html():
    return open(INDEX_HTML_PATH, "r", encoding="utf-8").read()


class TestVoiceProfileArchiveStatic:
    def test_archive_api_call_exists(self):
        html = read_html()
        assert "handleArchiveProfile" in html
        assert "/api/voice/profiles/${encodeURIComponent(profileId)}/archive" in html

    def test_archive_uses_patch_method(self):
        html = read_html()
        assert "method: 'PATCH'" in html or 'method: "PATCH"' in html

    def test_archive_confirm_copy_exists(self):
        html = read_html()
        assert "确认归档该人设？" in html
        assert "该人设不会出现在工作台、长文本、剧本的人设下拉中" in html

    def test_archive_confirm_mentions_history_and_assets_are_kept(self):
        html = read_html()
        assert "历史生成记录、音频资产和调用统计不会删除" in html
        assert "已有绑定记录会保留，便于后续追溯" in html

    def test_archive_success_refreshes_profiles(self):
        html = read_html()
        assert "await loadProfiles(true);" in html
        assert "await populateAllProfiles();" in html

    def test_no_profile_delete_endpoint_used(self):
        html = read_html()
        assert "/api/voice/profiles/${encodeURIComponent(profileId)}/archive" in html
        assert "DELETE /api/voice/profiles" not in html
