"""
test_usage_stats_semantics_static.py

P16-V1-CLOSEOUT-USAGE-STATS-SEMANTICS-D4-F1/D4-F1A: Static contract tests
for usage/cost/stats display semantics and provider filter init order.

Covers:
1. runtime_status.js today/month chip text includes "本地"
2. runtime_status.js chip title includes "本地" and "不代表官方"
3. No misleading official-billing terms in today/month chips
4. admin.html "总字符数" replaced by "本地字符数" or "本地记录字符数"
5. admin.html Provider table column renamed to "本地字符"
6. admin.html trend tab renamed from "字符数"
7. admin.html call logs column renamed
8. admin.html has official-billing disclaimer
9. admin.html URL provider param is read
10. admin.html loadLogs passes provider param
11. admin.html loadErrors passes provider param
12. cost_guard_service non-minimax warning mentions "不代表官方扣费"
13. StatsService by_provider grouping works for multiple providers
14. applyFocusFromURL() called before requestAnimationFrame(loadAll) [D4-F1A]
15. loadAll deferred inside requestAnimationFrame, not before applyFocusFromURL [D4-F1A]
16. applyFocusFromURL not inside requestAnimationFrame (must run synchronously) [D4-F1A]
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_STATUS_JS = os.path.join(REPO_ROOT, 'app', 'static', 'js', 'runtime_status.js')
ADMIN_HTML = os.path.join(REPO_ROOT, 'app', 'static', 'admin.html')
COST_GUARD_PY = os.path.join(REPO_ROOT, 'app', 'services', 'cost_guard_service.py')


def read_file(path):
    return open(path, 'r', encoding='utf-8').read()


# ── runtime_status.js chip semantics ─────────────────────────────────────────

class TestRuntimeStatusChipSemantics:
    def test_today_chip_text_includes_local(self):
        content = read_file(RUNTIME_STATUS_JS)
        assert re.search(r"今日本地\s*'", content) or '今日本地 ' in content, \
            'today chip textContent must include "今日本地"'

    def test_month_chip_text_includes_local(self):
        content = read_file(RUNTIME_STATUS_JS)
        assert re.search(r"本月本地\s*'", content) or '本月本地 ' in content, \
            'month chip textContent must include "本月本地"'

    def test_today_chip_title_mentions_local(self):
        content = read_file(RUNTIME_STATUS_JS)
        idx = content.find('chipToday')
        assert idx >= 0
        region = content[idx:idx + 300]
        assert '本地' in region, 'today chip title must mention "本地"'
        assert '不代表' in region, 'today chip title must contain "不代表"'

    def test_month_chip_title_mentions_local(self):
        content = read_file(RUNTIME_STATUS_JS)
        idx = content.find('chipMonth')
        assert idx >= 0
        region = content[idx:idx + 300]
        assert '本地' in region, 'month chip title must mention "本地"'
        assert '不代表' in region, 'month chip title must contain "不代表"'

    def test_no_misleading_official_billing_terms_in_chips(self):
        """Today/month chip section must not say 真实消耗/官方用量/剩余额度 in text."""
        content = read_file(RUNTIME_STATUS_JS)
        for forbidden in ['真实消耗', '官方用量']:
            assert forbidden not in content, \
                f'runtime_status.js must not contain misleading term: {forbidden!r}'

    def test_chip_title_mentions_not_official_account(self):
        content = read_file(RUNTIME_STATUS_JS)
        # title should say "不代表 Provider 官方账单" or similar
        assert '不代表' in content and ('官方' in content), \
            'chip title must clarify it does not represent official billing'


# ── admin.html copy changes ───────────────────────────────────────────────────

class TestAdminHtmlCopy:
    def test_total_chars_label_not_main_label(self):
        """'总字符数' must no longer be a primary stat label."""
        content = read_file(ADMIN_HTML)
        # The old <div class="stat-label">总字符数</div> should be gone
        assert '<div class="stat-label">总字符数</div>' not in content, \
            '"总字符数" must not appear as a primary stat-label'

    def test_local_chars_label_present(self):
        content = read_file(ADMIN_HTML)
        assert '本地字符数' in content or '本地记录字符' in content, \
            'admin.html must have "本地字符数" or "本地记录字符" label'

    def test_provider_table_column_local_chars(self):
        content = read_file(ADMIN_HTML)
        assert '本地字符' in content, \
            'Provider stats table must have "本地字符" column header'
        # Old "字符数" standalone header should be gone
        assert '<th>字符数</th>' not in content, \
            '"字符数" standalone th must be replaced'

    def test_trend_tab_not_plain_chars(self):
        content = read_file(ADMIN_HTML)
        assert '>字符数<' not in content, \
            'trend tab button must not have plain "字符数" label (use "本地字符")'

    def test_trend_tab_local_chars(self):
        content = read_file(ADMIN_HTML)
        assert '本地字符' in content, \
            'trend tab must include "本地字符" label'

    def test_call_logs_column_local_chars(self):
        """Call logs table must have '本地字符' column header."""
        content = read_file(ADMIN_HTML)
        # Find the logs section header row
        idx = content.find('最近调用记录')
        assert idx >= 0
        region = content[idx:idx + 800]
        assert '本地字符' in region, \
            'call logs table header must have "本地字符" column'

    def test_disclaimer_present(self):
        content = read_file(ADMIN_HTML)
        assert '不代表' in content and ('官方账单' in content or '官方扣费' in content), \
            'admin.html must have a disclaimer about not representing official billing'

    def test_disclaimer_mentions_local_db(self):
        content = read_file(ADMIN_HTML)
        assert '本地' in content and 'Voice Lab' in content, \
            'disclaimer must mention local Voice Lab database'

    def test_no_total_chars_as_official_billing(self):
        """admin.html must not present total chars as official billing amount."""
        content = read_file(ADMIN_HTML)
        for forbidden in ['真实消耗', '官方账单余额', '剩余额度']:
            assert forbidden not in content, \
                f'admin.html must not contain misleading billing term: {forbidden!r}'


# ── admin.html provider filter ────────────────────────────────────────────────

class TestAdminHtmlProviderFilter:
    def test_url_provider_param_is_read(self):
        content = read_file(ADMIN_HTML)
        assert "params.get('provider')" in content or 'params.get("provider")' in content, \
            'admin.html must read "provider" from URL params'

    def test_currentProviderFilter_variable_exists(self):
        content = read_file(ADMIN_HTML)
        assert 'currentProviderFilter' in content, \
            'admin.html must declare currentProviderFilter variable'

    def test_loadLogs_passes_provider(self):
        content = read_file(ADMIN_HTML)
        idx = content.find('async function loadLogs')
        assert idx >= 0
        region = content[idx:idx + 400]
        assert 'currentProviderFilter' in region or 'provider:' in region, \
            'loadLogs must pass currentProviderFilter to API call'

    def test_loadErrors_passes_provider(self):
        content = read_file(ADMIN_HTML)
        idx = content.find('async function loadErrors')
        assert idx >= 0
        region = content[idx:idx + 400]
        assert 'currentProviderFilter' in region or 'provider:' in region, \
            'loadErrors must pass currentProviderFilter to API call'

    def test_provider_filter_banner_element_exists(self):
        content = read_file(ADMIN_HTML)
        assert 'providerFilterBanner' in content, \
            'admin.html must have providerFilterBanner element'

    def test_provider_filter_applied_in_applyFocusFromURL(self):
        content = read_file(ADMIN_HTML)
        idx = content.find('applyFocusFromURL')
        assert idx >= 0
        # Find the function body
        func_start = content.find('function applyFocusFromURL', idx)
        if func_start < 0:
            func_start = idx
        region = content[func_start:func_start + 600]
        assert 'provider' in region, \
            'applyFocusFromURL must read and apply the provider URL param'

    def test_applyFocusFromURL_called_before_requestAnimationFrame_loadAll(self):
        """applyFocusFromURL() must be called synchronously before requestAnimationFrame(loadAll).

        This ensures currentProviderFilter is set before the first loadLogs/loadErrors fetch.
        """
        content = read_file(ADMIN_HTML)
        # Find the init block: applyFocusFromURL call site (not the definition)
        # Look for the pattern where applyFocusFromURL(); appears before requestAnimationFrame
        # Both must appear in the init section (after the function definitions)
        init_idx = content.rfind('applyFocusFromURL()')
        raf_idx = content.rfind('requestAnimationFrame')
        assert init_idx >= 0, 'applyFocusFromURL() must be called in init section'
        assert raf_idx >= 0, 'requestAnimationFrame must be present'
        assert init_idx < raf_idx, (
            'applyFocusFromURL() must be called BEFORE requestAnimationFrame so that '
            'currentProviderFilter is set before loadAll runs. '
            f'applyFocusFromURL at {init_idx}, requestAnimationFrame at {raf_idx}'
        )

    def test_loadAll_inside_requestAnimationFrame_not_before(self):
        """loadAll must be deferred inside requestAnimationFrame, not called synchronously before it."""
        content = read_file(ADMIN_HTML)
        # The last requestAnimationFrame call should contain loadAll
        raf_idx = content.rfind('requestAnimationFrame')
        assert raf_idx >= 0
        raf_region = content[raf_idx:raf_idx + 100]
        assert 'loadAll' in raf_region, (
            'loadAll() must be inside requestAnimationFrame callback, not called '
            'synchronously before applyFocusFromURL. '
            f'requestAnimationFrame region: {raf_region!r}'
        )

    def test_applyFocusFromURL_not_inside_requestAnimationFrame(self):
        """applyFocusFromURL must not be inside requestAnimationFrame — it must run synchronously."""
        content = read_file(ADMIN_HTML)
        raf_idx = content.rfind('requestAnimationFrame')
        assert raf_idx >= 0
        raf_region = content[raf_idx:raf_idx + 100]
        assert 'applyFocusFromURL' not in raf_region, (
            'applyFocusFromURL must NOT be inside requestAnimationFrame. '
            'It must run synchronously so currentProviderFilter is set before loadAll. '
            f'requestAnimationFrame region: {raf_region!r}'
        )


# ── cost_guard_service semantics ──────────────────────────────────────────────

class TestCostGuardSemantics:
    def test_non_minimax_warning_not_official_billing(self):
        from app.services.cost_guard_service import estimate_t2a_cost
        est = estimate_t2a_cost('xiaomi_mimo', 'mimo-v2.5-tts', '你好')
        assert len(est['warnings']) > 0
        warning = est['warnings'][0]
        assert '不代表官方扣费' in warning, \
            f'non-minimax warning must include "不代表官方扣费", got: {warning!r}'

    def test_minimax_still_has_known_price(self):
        from app.services.cost_guard_service import estimate_t2a_cost
        est = estimate_t2a_cost('minimax', 'speech-2.8-hd', '你好')
        assert est['unknown_price'] is False
        assert est['estimated_cost_cny'] is not None

    def test_xiaomi_mimo_no_price_fabricated(self):
        from app.services.cost_guard_service import estimate_t2a_cost
        est = estimate_t2a_cost('xiaomi_mimo', 'mimo-v2.5-tts', '你好世界')
        assert est['unknown_price'] is True
        assert est['estimated_cost_cny'] is None
        assert est['unit_price_cny_per_10k_chars'] is None

    def test_cost_guard_py_warning_text(self):
        """Static check: the warning string in source code is updated."""
        content = read_file(COST_GUARD_PY)
        assert '不代表官方扣费' in content, \
            'cost_guard_service.py warning must include "不代表官方扣费"'


# ── StatsService by_provider multi-provider check ─────────────────────────────

class TestStatsServiceMultiProvider:
    def test_by_provider_groups_multiple_providers(self):
        """StatsService.by_provider groups by ProviderCallLog.provider, not MiniMax-only."""
        import os
        import tempfile
        from sqlmodel import Session, SQLModel, create_engine
        from app.models.provider_call_log import ProviderCallLog
        from app.services.stats_service import StatsService

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        try:
            engine = create_engine(f'sqlite:///{path}', connect_args={'check_same_thread': False})
            SQLModel.metadata.create_all(engine)

            ts = '2026-05-17T10:00:00Z'
            with Session(engine) as session:
                session.add(ProviderCallLog(
                    id='log_mm', provider='minimax',
                    api_path='/v1/t2a_v2', method='POST',
                    usage_characters=100, created_at=ts,
                ))
                session.add(ProviderCallLog(
                    id='log_xm', provider='xiaomi_mimo',
                    api_path='/v1/chat/completions', method='POST',
                    usage_characters=50, created_at=ts,
                ))
                session.commit()

            with Session(engine) as session:
                svc = StatsService()
                result = svc.get_summary(session)

            bp = result['by_provider']
            assert 'minimax' in bp, 'minimax must appear in by_provider'
            assert 'xiaomi_mimo' in bp, 'xiaomi_mimo must appear in by_provider'
        finally:
            engine.dispose()
            os.unlink(path)

    def test_by_provider_not_minimax_only(self):
        """by_provider is driven by ProviderCallLog.provider, not a hardcoded list."""
        import os
        import tempfile
        from sqlmodel import Session, SQLModel, create_engine
        from app.models.provider_call_log import ProviderCallLog
        from app.services.stats_service import StatsService

        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        try:
            engine = create_engine(f'sqlite:///{path}', connect_args={'check_same_thread': False})
            SQLModel.metadata.create_all(engine)

            ts = '2026-05-17T10:00:00Z'
            with Session(engine) as session:
                session.add(ProviderCallLog(
                    id='log_future', provider='future_provider',
                    api_path='/v1/tts', method='POST',
                    usage_characters=200, created_at=ts,
                ))
                session.commit()

            with Session(engine) as session:
                svc = StatsService()
                result = svc.get_summary(session)

            assert 'future_provider' in result['by_provider'], \
                'by_provider must include any provider from ProviderCallLog, not just minimax'
        finally:
            engine.dispose()
            os.unlink(path)
