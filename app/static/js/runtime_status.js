(function () {
  'use strict';

  // ── state variables (kept on window for access from both modules) ───
  window._runtimeStatusTimer = window._runtimeStatusTimer || null;
  window._runtimeStatusErrorNotified = window._runtimeStatusErrorNotified || false;

  // ── esc helper ──────────────────────────────────────────────────
  function rsEsc(s) {
    if (s == null) return '';
    var d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  // ── chip helper ────────────────────────────────────────────────
  function setRuntimeChip(id, text, className, title) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = text || '-';
    el.className = 'runtime-chip ' + (className || 'muted');
    el.title = title || '';
  }

  // ── runtime status loading ─────────────────────────────────────

  window.loadRuntimeStatus = async function () {
    var bar = document.getElementById('runtimeStatusBar');
    if (!bar) return;
    try {
      var resp = await fetch('/api/voice/runtime/status');
      if (!resp.ok) throw new Error('non-200');
      var data = await resp.json();
      window._runtimeStatusErrorNotified = false;

      // Provider chip — follow current page selection, fall back to default
      var chipProvider = document.getElementById('chipProvider');
      if (chipProvider) {
        var defaultProvider = data.current.default_provider || '-';
        var providerEl = document.getElementById('providerSelect');
        var currentProvider = (providerEl && providerEl.value)
          ? providerEl.value
          : defaultProvider;
        chipProvider.textContent = currentProvider;
        chipProvider.title = currentProvider === defaultProvider
          ? '当前 Provider：默认配置'
          : '当前 Provider：页面选择';
        chipProvider.classList.remove('muted');
      }

      // Model chip — must reflect currentProvider, not always the system default_provider's model
      var chipModel = document.getElementById('chipModel');
      if (chipModel) {
        var resolvedModel = null;
        // 1. Try capability-derived model for currentProvider (provider-aware)
        if (typeof window.getDefaultTtsModel === 'function' && currentProvider) {
          resolvedModel = window.getDefaultTtsModel(currentProvider) || null;
        }
        // 2. Fallback: use API default_model only when currentProvider matches default_provider
        if (!resolvedModel) {
          resolvedModel = (currentProvider === (data.current.default_provider || ''))
            ? (data.current.default_model || '-')
            : '-';
        }
        chipModel.textContent = resolvedModel;
        chipModel.title = '当前模型：默认配置（' + resolvedModel + '）';
        chipModel.classList.remove('muted');
      }

      // Today chip
      var chipToday = document.getElementById('chipToday');
      if (chipToday) {
        chipToday.textContent = '今日本地 ' + (data.today.usage_characters || 0) + ' 字';
        chipToday.title = '本地估算用量，不代表 Provider 官方账单或官方剩余额度';
        chipToday.classList.remove('muted');
      }

      // Month chip
      var chipMonth = document.getElementById('chipMonth');
      if (chipMonth) {
        chipMonth.textContent = '本月本地 ' + (data.month.usage_characters || 0) + ' 字';
        chipMonth.title = '本地估算用量，不代表 Provider 官方账单或官方剩余额度';
        chipMonth.classList.remove('muted');
      }

      // Provider status chip
      var chipStatus = document.getElementById('chipProviderStatus');
      if (chipStatus) {
        chipStatus.textContent = data.provider_status.label || '-';
        chipStatus.className = 'runtime-chip muted';
        chipStatus.removeAttribute('title');
        chipStatus.style.cursor = '';
        chipStatus.onclick = null;

        var ps = data.provider_status;
        if (ps.state === 'error') {
          chipStatus.classList.add('error', 'clickable');
          chipStatus.style.cursor = 'pointer';
          var parts = [ps.label || '', ps.detail || '', ps.action_hint || ''].filter(Boolean);
          if (parts.length) {
            chipStatus.title = '最近一次 Provider 调用记录：' + parts.join('。');
          }
          chipStatus.onclick = function () {
            var provEl = document.getElementById('providerSelect');
            var prov = provEl ? provEl.value : '';
            var params = new URLSearchParams({ focus: 'call-logs' });
            if (prov) params.set('provider', prov);
            location.href = '/static/admin.html?' + params.toString();
          };
        } else if (ps.state === 'warning') {
          chipStatus.classList.add('warning', 'clickable');
          chipStatus.style.cursor = 'pointer';
          parts = [ps.label || '', ps.detail || '', ps.action_hint || ''].filter(Boolean);
          if (parts.length) {
            chipStatus.title = '最近一次 Provider 调用记录：' + parts.join('。');
          }
          chipStatus.onclick = function () {
            var provEl = document.getElementById('providerSelect');
            var prov = provEl ? provEl.value : '';
            var params = new URLSearchParams({ focus: 'call-logs' });
            if (prov) params.set('provider', prov);
            location.href = '/static/admin.html?' + params.toString();
          };
        } else if (ps.state === 'available') {
          chipStatus.classList.add('available');
          parts = [ps.detail || ''].filter(Boolean);
          if (parts.length) {
            chipStatus.title = '最近一次 Provider 调用记录：正常。' + parts.join('。');
          } else {
            chipStatus.title = '最近一次 Provider 调用记录：正常。';
          }
        } else {
          chipStatus.classList.add('muted');
          chipStatus.title = '最近一次 Provider 调用记录：无调用记录。';
        }
      }
    } catch (_) {
      var chipTodayErr = document.getElementById('chipToday');
      var chipMonthErr = document.getElementById('chipMonth');
      var chipStatusErr = document.getElementById('chipProviderStatus');
      if (chipTodayErr) chipTodayErr.textContent = '用量统计不可用';
      if (chipMonthErr) chipMonthErr.textContent = '';
      if (chipStatusErr) {
        chipStatusErr.textContent = '点击重试';
        chipStatusErr.className = 'runtime-chip error clickable';
        chipStatusErr.title = '用量统计加载失败，点击重试';
        chipStatusErr.style.cursor = 'pointer';
        chipStatusErr.onclick = function () { window.loadRuntimeStatus(); };
      }
      if (!window._runtimeStatusErrorNotified) {
        window._runtimeStatusErrorNotified = true;
        if (typeof window.showToast === 'function') {
          window.showToast('用量统计加载失败，可点击状态条重试', 'error');
        }
      }
    }
  };

  // ── scheduler (exposed so inline script can call it) ──────────────

  window.scheduleRuntimeStatusRefresh = function () {
    if (window._runtimeStatusTimer) clearTimeout(window._runtimeStatusTimer);
    window._runtimeStatusTimer = setTimeout(function () {
      window.loadRuntimeStatus();
      window.scheduleRuntimeStatusRefresh();
    }, 60000);
  };

  // ── reactive refresh triggers ──────────────────────────────────────

  // Refresh immediately when providerSelect changes so chipModel stays in sync.
  // DOM is already available (script loads after the select element in the HTML).
  (function () {
    var provEl = document.getElementById('providerSelect');
    if (provEl) {
      provEl.addEventListener('change', function () { window.loadRuntimeStatus(); });
    }
  })();

  // Refresh after capabilities load so getDefaultTtsModel() returns valid data.
  // provider-capabilities-applied is fired once per load — no loop risk.
  window.addEventListener('provider-capabilities-applied', function () {
    window.loadRuntimeStatus();
  });
})();
