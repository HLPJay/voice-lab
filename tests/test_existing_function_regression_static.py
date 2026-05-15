"""
test_existing_function_regression_static.py

P13-PRE-B5-REGRESSION-CHECK: Regression tests for existing functions
before B5 batch sample_store integration.

Verifies:
1. 6 tab-content divs exist and are properly structured
2. sampleSidebarRoot only inside tab-workspace
3. textInput / batchText / auditionText maxlengths
4. Workspace four generation modes
5. History exports
6. History audio playback with catch
7. batch longtext/script key DOM ids
8. audition key DOM ids
9. sample_sidebar.js isolation
10. sample_store.js localStorage isolation
11. no duplicate sampleSidebarRoot
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')
SIDEBAR_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_sidebar.js')
SAMPLE_STORE_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'sample_store.js')
HISTORY_JS_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'history.js')


def read_html():
    return open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()


def read_sidebar():
    return open(SIDEBAR_JS_PATH, 'r', encoding='utf-8').read()


def read_sample_store():
    return open(SAMPLE_STORE_JS_PATH, 'r', encoding='utf-8').read()


def read_history():
    return open(HISTORY_JS_PATH, 'r', encoding='utf-8').read()


def find_tab_range(html, tab_id):
    """Return (start, end) of the tab-content div with given id."""
    pattern = '<div class="tab-content' + '[^>]*id="' + tab_id + '"'
    m = re.search(pattern, html)
    if not m:
        return None
    start = m.start()
    depth = 0
    pos = start
    while pos < len(html):
        if html[pos:pos+5] == '<div ':
            depth += 1
            pos += 5
        elif html[pos:pos+6] == '</div>':
            depth -= 1
            if depth == 0:
                return (start, pos + 6)
            pos += 6
        else:
            pos += 1
    return None


def is_ancestor(outer_start, outer_end, inner_start, inner_end):
    return outer_start < inner_start and inner_end < outer_end


# ── 1. Tab navigation ────────────────────────────────────────────────────────

class TestSixTabsExist:
    """All 6 tab-content divs must exist and be properly structured."""

    def test_tab_workspace(self):
        assert 'id="tab-workspace"' in read_html()

    def test_tab_longtext(self):
        assert 'id="tab-longtext"' in read_html()

    def test_tab_script(self):
        assert 'id="tab-script"' in read_html()

    def test_tab_voices(self):
        assert 'id="tab-voices"' in read_html()

    def test_tab_history(self):
        assert 'id="tab-history"' in read_html()

    def test_tab_advanced(self):
        assert 'id="tab-advanced"' in read_html()


class TestTabSiblingStructure:
    """All 6 tabs must be siblings, not nested inside each other."""

    def test_tab_longtext_not_in_workspace(self):
        html = read_html()
        ws = find_tab_range(html, 'tab-workspace')
        lt = find_tab_range(html, 'tab-longtext')
        assert ws is not None and lt is not None
        assert not is_ancestor(ws[0], ws[1], lt[0], lt[1])

    def test_tab_script_not_in_workspace(self):
        html = read_html()
        ws = find_tab_range(html, 'tab-workspace')
        sc = find_tab_range(html, 'tab-script')
        assert ws is not None and sc is not None
        assert not is_ancestor(ws[0], ws[1], sc[0], sc[1])

    def test_tab_script_not_in_longtext(self):
        html = read_html()
        lt = find_tab_range(html, 'tab-longtext')
        sc = find_tab_range(html, 'tab-script')
        assert lt is not None and sc is not None
        assert not is_ancestor(lt[0], lt[1], sc[0], sc[1])

    def test_tab_voices_not_in_workspace(self):
        html = read_html()
        ws = find_tab_range(html, 'tab-workspace')
        vo = find_tab_range(html, 'tab-voices')
        assert ws is not None and vo is not None
        assert not is_ancestor(ws[0], ws[1], vo[0], vo[1])

    def test_tab_history_not_in_workspace(self):
        html = read_html()
        ws = find_tab_range(html, 'tab-workspace')
        hi = find_tab_range(html, 'tab-history')
        assert ws is not None and hi is not None
        assert not is_ancestor(ws[0], ws[1], hi[0], hi[1])

    def test_tab_advanced_not_in_workspace(self):
        html = read_html()
        ws = find_tab_range(html, 'tab-workspace')
        ad = find_tab_range(html, 'tab-advanced')
        assert ws is not None and ad is not None
        assert not is_ancestor(ws[0], ws[1], ad[0], ad[1])

    def test_all_tabs_are_siblings(self):
        html = read_html()
        tabs = ['tab-workspace', 'tab-longtext', 'tab-script',
                'tab-voices', 'tab-history', 'tab-advanced']
        ranges = {t: find_tab_range(html, t) for t in tabs}
        for t in tabs:
            assert ranges[t] is not None, f'{t} not found'
        for i, t1 in enumerate(tabs):
            for t2 in tabs[i+1:]:
                assert not is_ancestor(ranges[t1][0], ranges[t1][1],
                                       ranges[t2][0], ranges[t2][1]), \
                    f'{t2} must not be inside {t1}'
                assert not is_ancestor(ranges[t2][0], ranges[t2][1],
                                       ranges[t1][0], ranges[t1][1]), \
                    f'{t1} must not be inside {t2}'


# ── 2. sampleSidebarRoot placement ───────────────────────────────────────────

class TestSampleSidebarPlacement:
    """sampleSidebarRoot must only be inside tab-workspace."""

    def test_sampleSidebarRoot_in_workspace(self):
        html = read_html()
        ws = find_tab_range(html, 'tab-workspace')
        assert ws is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert ws[0] < ss_pos < ws[1]

    def test_sampleSidebarRoot_not_in_longtext(self):
        html = read_html()
        lt = find_tab_range(html, 'tab-longtext')
        assert lt is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(lt[0], lt[1], ss_pos, ss_pos+1)

    def test_sampleSidebarRoot_not_in_script(self):
        html = read_html()
        sc = find_tab_range(html, 'tab-script')
        assert sc is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(sc[0], sc[1], ss_pos, ss_pos+1)

    def test_sampleSidebarRoot_not_in_voices(self):
        html = read_html()
        vo = find_tab_range(html, 'tab-voices')
        assert vo is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(vo[0], vo[1], ss_pos, ss_pos+1)

    def test_sampleSidebarRoot_not_in_history(self):
        html = read_html()
        hi = find_tab_range(html, 'tab-history')
        assert hi is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(hi[0], hi[1], ss_pos, ss_pos+1)

    def test_sampleSidebarRoot_not_in_advanced(self):
        html = read_html()
        ad = find_tab_range(html, 'tab-advanced')
        assert ad is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(ad[0], ad[1], ss_pos, ss_pos+1)

    def test_no_duplicate_sampleSidebarRoot(self):
        html = read_html()
        count = html.count('id="sampleSidebarRoot"')
        assert count == 1, f'Expected 1 sampleSidebarRoot, found {count}'


# ── 3. Workspace text limits ─────────────────────────────────────────────────

class TestWorkspaceTextLimits:
    def test_textInput_exists(self):
        assert 'id="textInput"' in read_html()

    def test_textInput_maxlength_9500(self):
        html = read_html()
        m = re.search(r'<textarea[^>]+id="textInput"[^>]+maxlength="9500"', html)
        assert m, 'textInput maxlength must be 9500'

    def test_charCount_exists(self):
        assert 'id="charCount"' in read_html()

    def test_costHint_exists(self):
        assert 'id="costHint"' in read_html()

    def test_profileSelect_exists(self):
        assert 'id="profileSelect"' in read_html()

    def test_providerSelect_exists(self):
        assert 'id="providerSelect"' in read_html()

    def test_audioFormat_exists(self):
        assert 'id="audioFormat"' in read_html()

    def test_outputFormat_exists(self):
        assert 'id="outputFormat"' in read_html()

    def test_generateBtn_exists(self):
        assert 'id="generateBtn"' in read_html()

    def test_resultsArea_exists(self):
        assert 'id="resultsArea"' in read_html()


# ── 4. Workspace generation modes ─────────────────────────────────────────────

class TestWorkspaceGenerationModes:
    def test_single_mode_exists(self):
        assert 'value="single"' in read_html()

    def test_async_mode_exists(self):
        assert 'value="async"' in read_html()

    def test_stream_mode_exists(self):
        assert 'value="stream"' in read_html()

    def test_variants_mode_exists(self):
        assert 'value="variants"' in read_html()


# ── 5. Batch longtext DOM ids ────────────────────────────────────────────────

class TestBatchLongtextDOM:
    def test_batchText_exists(self):
        assert 'id="batchText"' in read_html()

    def test_batchText_maxlength_50000(self):
        html = read_html()
        m = re.search(r'<textarea[^>]+id="batchText"[^>]+maxlength="50000"', html)
        assert m, 'batchText maxlength must be 50000'

    def test_batchProfile_exists(self):
        assert 'id="batchProfile"' in read_html()

    def test_batchProvider_exists(self):
        assert 'id="batchProvider"' in read_html()

    def test_batchStrategy_exists(self):
        assert 'id="batchStrategy"' in read_html()

    def test_batchMaxChars_exists(self):
        assert 'id="batchMaxChars"' in read_html()

    def test_batchSilence_exists(self):
        assert 'id="batchSilence"' in read_html()

    def test_batchOutputFormat_exists(self):
        assert 'id="batchOutputFormat"' in read_html()

    def test_batchNeedSubtitle_exists(self):
        assert 'id="batchNeedSubtitle"' in read_html()

    def test_batchLongtextSubmit_exists(self):
        assert 'id="batchLongtextSubmit"' in read_html()

    def test_batchProgressPanel_exists(self):
        assert 'id="batchProgressPanel"' in read_html()

    def test_batchResultPlayer_exists(self):
        assert 'id="batchResultPlayer"' in read_html()

    def test_batchMergedAudio_exists(self):
        assert 'id="batchMergedAudio"' in read_html()

    def test_batchDownloadAudio_exists(self):
        assert 'id="batchDownloadAudio"' in read_html()


# ── 6. Batch script DOM ids ─────────────────────────────────────────────────

class TestBatchScriptDOM:
    def test_batchScriptProvider_exists(self):
        assert 'id="batchScriptProvider"' in read_html()

    def test_batchScriptSilence_exists(self):
        assert 'id="batchScriptSilence"' in read_html()

    def test_batchScriptOutputFormat_exists(self):
        assert 'id="batchScriptOutputFormat"' in read_html()

    def test_batchScriptNeedSubtitle_exists(self):
        assert 'id="batchScriptNeedSubtitle"' in read_html()

    def test_scriptLines_exists(self):
        assert 'id="scriptLines"' in read_html()

    def test_scriptAddLineBtn_exists(self):
        assert 'id="scriptAddLineBtn"' in read_html()

    def test_batchScriptSubmit_exists(self):
        assert 'id="batchScriptSubmit"' in read_html()

    def test_batchScriptProgressPanel_exists(self):
        assert 'id="batchScriptProgressPanel"' in read_html()

    def test_batchScriptMergedAudio_exists(self):
        assert 'id="batchScriptMergedAudio"' in read_html()

    def test_batchScriptDownloadAudio_exists(self):
        assert 'id="batchScriptDownloadAudio"' in read_html()


# ── 7. Audition DOM ids ─────────────────────────────────────────────────────

class TestAuditionDOM:
    def test_auditionText_exists(self):
        assert 'id="auditionText"' in read_html()

    def test_auditionText_maxlength_1000(self):
        html = read_html()
        m = re.search(r'<textarea[^>]+id="auditionText"[^>]+maxlength="1000"', html)
        assert m, 'auditionText maxlength must be 1000'

    def test_auditionModel_exists(self):
        assert 'id="auditionModel"' in read_html()

    def test_auditionGenBtn_exists(self):
        assert 'id="auditionGenBtn"' in read_html()

    def test_auditionResult_exists(self):
        assert 'id="auditionResult"' in read_html()

    def test_auditionRecordsPanel_exists(self):
        assert 'id="auditionRecordsPanel"' in read_html()


# ── 8. History exports ───────────────────────────────────────────────────────

class TestHistoryExports:
    def test_loadHistory_exists(self):
        h = read_history()
        assert re.search(r'window\.loadHistory\s*=', h)

    def test_refreshHistory_exists(self):
        h = read_history()
        assert re.search(r'window\.refreshHistory\s*=', h)

    def test_loadMoreHistory_exists(self):
        h = read_history()
        assert re.search(r'window\.loadMoreHistory\s*=', h)

    def test_toggleHistoryAudio_exists(self):
        h = read_history()
        assert re.search(r'window\.toggleHistoryAudio\s*=', h)

    def test_deleteHistoryJob_exists(self):
        h = read_history()
        assert re.search(r'window\.deleteHistoryJob\s*=', h)

    def test_copyJobId_exists(self):
        h = read_history()
        assert re.search(r'window\.copyJobId\s*=', h)

    def test_toggleHistoryAudio_calls_play(self):
        h = read_history()
        body = h[h.find('window.toggleHistoryAudio'):]
        end = body.find('window.deleteHistoryJob')
        assert 'audioEl.play()' in body[:end]

    def test_toggleHistoryAudio_play_promise_catch(self):
        h = read_history()
        body = h[h.find('window.toggleHistoryAudio'):]
        end = body.find('window.deleteHistoryJob')
        assert '.catch(' in body[:end]

    def test_history_download_uses_api(self):
        h = read_history()
        assert '/api/voice/assets/' in h

    def test_history_delete_uses_delete_method(self):
        h = read_history()
        assert "method: 'DELETE'" in h


# ── 9. sample_sidebar.js isolation ───────────────────────────────────────────

class TestSidebarIsolation:
    def test_no_fetch_in_sidebar(self):
        s = read_sidebar()
        assert 'fetch(' not in s

    def test_no_guardedJsonFetch_in_sidebar(self):
        s = read_sidebar()
        assert 'guardedJsonFetch' not in s

    def test_no_batch_longtext_function_in_sidebar(self):
        """sidebar must not call batch_longtext functions, but sourceLabel entries are allowed."""
        s = read_sidebar()
        assert 'safePushBatchSample' not in s
        assert '_batchSampleContextById' not in s

    def test_no_batch_script_function_in_sidebar(self):
        """sidebar must not call batch_script functions, but sourceLabel entries are allowed."""
        s = read_sidebar()
        assert 'safePushBatchSample' not in s
        assert '_batchSampleContextById' not in s

    def test_no_history_sample_in_sidebar(self):
        s = read_sidebar()
        assert 'history' not in s.lower() or 'sourceLabel' in s

    def test_sidebar_uses_getSamplesSafe(self):
        s = read_sidebar()
        assert 'getSamplesSafe()' in s

    def test_sidebar_no_localStorage_directly(self):
        s = read_sidebar()
        body = s[s.find('function render'):s.find('function render')+2000]
        assert 'localStorage.getItem' not in body

    def test_sidebar_no_JSON_parse_directly(self):
        s = read_sidebar()
        body = s[s.find('function render'):s.find('function render')+2000]
        assert 'JSON.parse' not in body


# ── 10. sample_store.js localStorage isolation ────────────────────────────────

class TestSampleStoreIsolation:
    def test_sample_store_uses_correct_key(self):
        s = read_sample_store()
        assert 'voice_lab_recent_samples_v1' in s

    def test_sample_store_no_recentJobs_reference(self):
        """sample_store.js must not reference recentJobs variable or storage key."""
        s = read_sample_store()
        # Exclude comment lines - recentJobs appears in "Does NOT" comment
        code_lines = [l for l in s.split('\n') if not l.strip().startswith('*') and not l.strip().startswith('//')]
        code = '\n'.join(code_lines)
        assert 'recentJobs' not in code, \
            'sample_store.js must not reference recentJobs in actual code'


# ── 11. Audition safePushAuditionSample integration ───────────────────────────

class TestAuditionSampleIntegration:
    def test_safePushAuditionSample_exists_in_index(self):
        html = read_html()
        assert 'safePushAuditionSample' in html

    def test_safePushAuditionSample_in_success_branch_only(self):
        """safePushAuditionSample must only be called after data.audio_asset.url check."""
        html = read_html()
        # Find the success branch condition
        success_branch = html[html.find('if (data.audio_asset && data.audio_asset.url)'):]
        # Find the next branching point
        next_branch = success_branch.find('} else {')
        success_block = success_branch[:next_branch] if next_branch > 0 else success_branch
        assert 'safePushAuditionSample' in success_block

    def test_safePushAuditionSample_rejects_blob(self):
        s = read_sidebar()
        # safePushAuditionSample is in audition_records.js
        audition_records_path = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'audition_records.js')
        if os.path.exists(audition_records_path):
            ar = open(audition_records_path, 'r', encoding='utf-8').read()
            assert 'blob:' in ar or 'startsWith' in ar


# ── 12. Workspace sample integration ────────────────────────────────────────

class TestWorkspaceSampleIntegration:
    def test_safePushWorkspaceSample_stream_guards_asset_id(self):
        html = read_html()
        # Find stream push
        stream_push = html[html.find("safePushWorkspaceSample('workspace_stream'"):]
        stream_push = stream_push[:stream_push.find('\n    }')]
        assert 'asset_id' in stream_push or 'asset.id' in stream_push

    def test_safePushWorkspaceSample_stream_only_if_asset_exists(self):
        html = read_html()
        # Should be inside "if (asset && asset.id)" guard
        stream_section = html[html.find("safePushWorkspaceSample('workspace_stream'"):]
        stream_section = stream_section[:stream_section.find('\n  }')]
        assert 'asset' in stream_section and ('asset.id' in stream_section or 'asset_id' in stream_section)

    def test_variants_iterates_and_pushes_each(self):
        html = read_html()
        variants_section = html[html.find('data.variants.forEach'):]
        variants_section = variants_section[:variants_section.find('\n    } else {') if variants_section.find('\n    } else {') > 0 else len(variants_section)]
        assert 'safePushWorkspaceSample' in variants_section
        assert 'audio_asset_id' in variants_section

    def test_workspace_sample_uses_buildAssetDownloadUrl(self):
        html = read_html()
        fn = html[html.find('function safePushWorkspaceSample'):]
        fn = fn[:fn.find('\n  }')]
        assert 'buildAssetDownloadUrl' in fn or 'asset_id' in fn


# ── 13. Tab buttons reference existing tabs ─────────────────────────────────

class TestTabButtons:
    def test_all_tab_buttons_have_targets(self):
        html = read_html()
        tab_names = re.findall(r'data-tab="([^"]+)"', html)
        for name in tab_names:
            target_id = 'tab-' + name
            assert 'id="' + target_id + '"' in html, \
                'tab button data-tab="' + name + '" must have corresponding id="tab-' + name + '"'
