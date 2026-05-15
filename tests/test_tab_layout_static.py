"""
test_tab_layout_static.py

P13-B4-REGRESSION-FIX1: Static regression tests for tab layout.
Verifies that all 6 tab-content divs are proper siblings and that
sampleSidebarRoot is correctly placed inside tab-workspace only.
"""

import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, 'app', 'static', 'index.html')


def read():
    return open(INDEX_HTML_PATH, 'r', encoding='utf-8').read()


def tag_ranges(html):
    """Return list of (start, end, tag_name, id_attr) for all div tags."""
    results = []
    pos = 0
    while pos < len(html):
        next_div = html.find('<div', pos)
        if next_div == -1:
            break
        # Check if this is a closing tag
        if html[next_div:next_div+6] == '</div>':
            pos = next_div + 6
            continue
        # Find the end of this tag
        gt = html.find('>', next_div)
        if gt == -1:
            break
        tag = html[next_div:gt+1]
        # Extract id if present
        id_match = re.search(r'\sid="([^"]+)"', tag)
        id_val = id_match.group(1) if id_match else None
        # Find matching close tag
        depth = 1
        search_pos = gt + 1
        close_pos = None
        while search_pos < len(html) and depth > 0:
            next_open = html.find('<div', search_pos)
            next_close = html.find('</div>', search_pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                search_pos = next_open + 1
            else:
                depth -= 1
                if depth == 0:
                    close_pos = next_close + 6
                    break
                search_pos = next_close + 1
        if close_pos:
            results.append((next_div, close_pos, 'div', id_val))
            pos = close_pos
        else:
            pos = gt + 1
    return results


def find_tab_range(html, tab_id):
    """Return (start, end) of the tab-content div with given id, or None."""
    pattern = '<div class="tab-content' + '[^>]*id="' + tab_id + '"'
    m = re.search(pattern, html)
    if not m:
        return None
    start = m.start()
    # Find closing </div>
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
    """Return True if outer range contains inner range (strict ancestor)."""
    return outer_start < inner_start and inner_end < outer_end


class TestSixTabsExist:
    """All 6 tab-content divs must exist in index.html."""

    def test_tab_workspace(self):
        c = read()
        assert 'id="tab-workspace"' in c
        assert 'tab-content' in c

    def test_tab_longtext(self):
        c = read()
        assert 'id="tab-longtext"' in c

    def test_tab_script(self):
        c = read()
        assert 'id="tab-script"' in c

    def test_tab_voices(self):
        c = read()
        assert 'id="tab-voices"' in c

    def test_tab_history(self):
        c = read()
        assert 'id="tab-history"' in c

    def test_tab_advanced(self):
        c = read()
        assert 'id="tab-advanced"' in c


class TestTabSiblingStructure:
    """All 6 tab-content divs must be siblings (not nested inside each other)."""

    def test_tab_longtext_not_in_workspace(self):
        html = read()
        ws = find_tab_range(html, 'tab-workspace')
        lt = find_tab_range(html, 'tab-longtext')
        assert ws is not None
        assert lt is not None
        # lt must NOT be inside ws
        assert not is_ancestor(ws[0], ws[1], lt[0], lt[1]), \
            'tab-longtext must not be nested inside tab-workspace'

    def test_tab_script_not_in_workspace(self):
        html = read()
        ws = find_tab_range(html, 'tab-workspace')
        sc = find_tab_range(html, 'tab-script')
        assert ws is not None
        assert sc is not None
        assert not is_ancestor(ws[0], ws[1], sc[0], sc[1]), \
            'tab-script must not be nested inside tab-workspace'

    def test_tab_script_not_in_longtext(self):
        html = read()
        lt = find_tab_range(html, 'tab-longtext')
        sc = find_tab_range(html, 'tab-script')
        assert lt is not None
        assert sc is not None
        assert not is_ancestor(lt[0], lt[1], sc[0], sc[1]), \
            'tab-script must not be nested inside tab-longtext'

    def test_tab_voices_not_in_workspace(self):
        html = read()
        ws = find_tab_range(html, 'tab-workspace')
        vo = find_tab_range(html, 'tab-voices')
        assert ws is not None
        assert vo is not None
        assert not is_ancestor(ws[0], ws[1], vo[0], vo[1]), \
            'tab-voices must not be nested inside tab-workspace'

    def test_tab_history_not_in_workspace(self):
        html = read()
        ws = find_tab_range(html, 'tab-workspace')
        hi = find_tab_range(html, 'tab-history')
        assert ws is not None
        assert hi is not None
        assert not is_ancestor(ws[0], ws[1], hi[0], hi[1]), \
            'tab-history must not be nested inside tab-workspace'

    def test_tab_advanced_not_in_workspace(self):
        html = read()
        ws = find_tab_range(html, 'tab-workspace')
        ad = find_tab_range(html, 'tab-advanced')
        assert ws is not None
        assert ad is not None
        assert not is_ancestor(ws[0], ws[1], ad[0], ad[1]), \
            'tab-advanced must not be nested inside tab-workspace'

    def test_all_tabs_are_siblings(self):
        """All 6 tabs should be at the same depth level."""
        html = read()
        tabs = ['tab-workspace', 'tab-longtext', 'tab-script',
                'tab-voices', 'tab-history', 'tab-advanced']
        ranges = {}
        for tab in tabs:
            r = find_tab_range(html, tab)
            assert r is not None, f'{tab} not found'
            ranges[tab] = r
        # All tabs should close before any non-tab-content div that is NOT inside any tab
        # The simplest check: verify no tab range contains any other tab range
        for i, t1 in enumerate(tabs):
            for t2 in tabs[i+1:]:
                assert not is_ancestor(ranges[t1][0], ranges[t1][1],
                                       ranges[t2][0], ranges[t2][1]), \
                    f'{t2} must not be inside {t1}'
                assert not is_ancestor(ranges[t2][0], ranges[t2][1],
                                       ranges[t1][0], ranges[t1][1]), \
                    f'{t1} must not be inside {t2}'


class TestSampleSidebarPlacement:
    """sampleSidebarRoot must be inside tab-workspace and nowhere else."""

    def test_sampleSidebarRoot_in_workspace(self):
        html = read()
        ws = find_tab_range(html, 'tab-workspace')
        assert ws is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0, 'sampleSidebarRoot not found'
        assert ws[0] < ss_pos < ws[1], \
            'sampleSidebarRoot must be inside tab-workspace'

    def test_sampleSidebarRoot_not_in_longtext(self):
        html = read()
        lt = find_tab_range(html, 'tab-longtext')
        assert lt is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(lt[0], lt[1], ss_pos, ss_pos+1), \
            'sampleSidebarRoot must not be inside tab-longtext'

    def test_sampleSidebarRoot_not_in_script(self):
        html = read()
        sc = find_tab_range(html, 'tab-script')
        assert sc is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(sc[0], sc[1], ss_pos, ss_pos+1), \
            'sampleSidebarRoot must not be inside tab-script'

    def test_sampleSidebarRoot_not_in_voices(self):
        html = read()
        vo = find_tab_range(html, 'tab-voices')
        assert vo is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(vo[0], vo[1], ss_pos, ss_pos+1), \
            'sampleSidebarRoot must not be inside tab-voices'

    def test_sampleSidebarRoot_not_in_history(self):
        html = read()
        hi = find_tab_range(html, 'tab-history')
        assert hi is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(hi[0], hi[1], ss_pos, ss_pos+1), \
            'sampleSidebarRoot must not be inside tab-history'

    def test_sampleSidebarRoot_not_in_advanced(self):
        html = read()
        ad = find_tab_range(html, 'tab-advanced')
        assert ad is not None
        ss_pos = html.find('id="sampleSidebarRoot"')
        assert ss_pos >= 0
        assert not is_ancestor(ad[0], ad[1], ss_pos, ss_pos+1), \
            'sampleSidebarRoot must not be inside tab-advanced'


class TestWorkspaceLayout:
    """workspace-layout and workspace-main must be inside tab-workspace."""

    def test_workspace_layout_in_workspace(self):
        html = read()
        ws = find_tab_range(html, 'tab-workspace')
        assert ws is not None
        wl_pos = html.find('class="workspace-layout"')
        assert wl_pos >= 0, 'workspace-layout not found'
        assert ws[0] < wl_pos < ws[1], \
            'workspace-layout must be inside tab-workspace'

    def test_workspace_main_in_workspace_layout(self):
        html = read()
        wl_pos = html.find('class="workspace-layout"')
        assert wl_pos >= 0
        wm_pos = html.find('class="workspace-main"')
        assert wm_pos >= 0, 'workspace-main not found'
        assert wl_pos < wm_pos, \
            'workspace-main must appear after workspace-layout'


class TestTabButtons:
    """Each tab button must reference an existing tab-content id."""

    def test_all_tab_buttons_have_targets(self):
        html = read()
        # Find all tab-btn data-tab values
        tab_names = re.findall(r'data-tab="([^"]+)"', html)
        for name in tab_names:
            target_id = 'tab-' + name
            assert 'id="' + target_id + '"' in html, \
                'tab button data-tab="' + name + '" must have corresponding id="tab-' + name + '"'
