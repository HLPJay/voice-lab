(function () {
  'use strict';

  // ── state on window for E2E test compatibility ─────────────────────
  window._historyJobs = window._historyJobs || [];
  window._historyOffset = window._historyOffset || 0;
  window._historyTotal = window._historyTotal || 0;
  window._historyLoading = window._historyLoading || false;
  window._historySearch = window._historySearch || '';
  window._historyStatusFilter = window._historyStatusFilter || 'all';
  window._activeHistoryAudioRow = window._activeHistoryAudioRow || null;

  // ── local esc helper (duplicates index.html's esc() logic) ───────────
  function hEsc(s) {
    if (s == null) return '';
    var d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  // ── local copy helper (duplicates index.html's copyJobId() logic) ────
  function hCopyJobId(jobId, btnEl) {
    var id = jobId || '';
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(id).then(function () {
        var btn = btnEl || document.getElementById('copyJobIdBtn');
        if (btn) {
          btn.textContent = '已复制';
          setTimeout(function () { if (btn) btn.textContent = '复制'; }, 1500);
        }
      }).catch(function () { window.prompt('Job ID:', id); });
    } else {
      window.prompt('Job ID:', id);
    }
  }

  // ── local display helpers (duplicates index.html equivalents) ─────────

  function hParseBackendTime(value) {
    if (!value) return null;
    if (value instanceof Date) return value;
    var raw = String(value);
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(raw)) {
      return new Date(raw + 'Z');
    }
    return new Date(raw);
  }

  function hFormatLocalDateTime(value) {
    var d = hParseBackendTime(value);
    if (!d || Number.isNaN(d.getTime())) return '—';
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    var hh = String(d.getHours()).padStart(2, '0');
    var mm = String(d.getMinutes()).padStart(2, '0');
    var ss = String(d.getSeconds()).padStart(2, '0');
    return y + '-' + m + '-' + day + ' ' + hh + ':' + mm + ':' + ss;
  }

  function hUtcTitle(value) {
    if (!value) return '';
    return '原始 UTC：' + String(value);
  }

  function hStatusLabel(s) {
    var m = { success: '已完成', failed: '失败', running: '生成中', pending: '等待中', processing: '处理中' };
    return m[s] || s;
  }

  function hStatusClass(s) {
    return 'job-status status-' + s;
  }

  function hAudioPlayerHtml(assetId) {
    return '<audio class="audio-player" controls preload="none">\n      <source src="/api/voice/assets/' + encodeURIComponent(assetId) + '/download" type="audio/mpeg">\n      您的浏览器不支持音频播放</audio>';
  }

  function hDownloadBtnHtml(assetId) {
    return '<a class="btn-sm" href="/api/voice/assets/' + encodeURIComponent(assetId) + '/download" download>下载音频</a>';
  }

  // ── history state helpers ───────────────────────────────────────────

  function hIsSuccessStatus(status) {
    return status === 'success' || status === 'completed';
  }

  function hIsFailedStatus(status) {
    return status === 'failed' || status === 'error';
  }

  function hIsProcessingStatus(status) {
    return ['queued', 'pending', 'running', 'processing'].indexOf(status) !== -1;
  }

  // ── history state variable aliases (local refs for use in closures) ──

  // These are re-read from window at call time to avoid staleness
  function getHistoryJobs() { return window._historyJobs; }
  function getHistoryOffset() { return window._historyOffset; }
  function getHistoryTotal() { return window._historyTotal; }
  function getHistoryLoading() { return window._historyLoading; }
  function getHistorySearch() { return window._historySearch; }
  function getHistoryStatusFilter() { return window._historyStatusFilter; }
  function getActiveHistoryAudioRow() { return window._activeHistoryAudioRow; }

  function setHistoryLoading(v) { window._historyLoading = v; }
  function setHistoryOffset(v) { window._historyOffset = v; }
  function setHistoryTotal(v) { window._historyTotal = v; }
  function setHistorySearch(v) { window._historySearch = v; }
  function setHistoryStatusFilter(v) { window._historyStatusFilter = v; }
  function setHistoryJobs(v) { window._historyJobs = v; }
  function setActiveHistoryAudioRow(v) { window._activeHistoryAudioRow = v; }

  // ── HTML generators ────────────────────────────────────────────────

  function historyAudioPlayerHtml(assetId) {
    return '<div class="history-audio-status">音频加载中…</div>\n      <audio class="audio-player" controls preload="metadata" src="/api/voice/assets/' + encodeURIComponent(assetId) + '/download">\n      您的浏览器不支持音频播放</audio>';
  }

  function attachHistoryAudioEvents(audioEl, statusEl, assetId) {
    audioEl.addEventListener('loadedmetadata', function () {
      statusEl.textContent = '音频已就绪';
      statusEl.className = 'history-audio-status muted';
    });
    audioEl.addEventListener('canplay', function () {
      statusEl.textContent = '';
      statusEl.className = 'history-audio-status';
    });
    audioEl.addEventListener('error', function () {
      statusEl.innerHTML = '音频加载失败，可尝试 <a href="/api/voice/assets/' + encodeURIComponent(assetId) + '/download" target="_blank">下载</a>';
      statusEl.className = 'history-audio-status error';
    });
    audioEl.addEventListener('emptied', function () {
      statusEl.textContent = '';
    });
  }

  function historyDownloadEntryHtml(job) {
    var assetId = getHistoryAudioAssetId(job);
    if (assetId) {
      return '<div style="margin-top:10px">\n        <div style="font-size:0.78rem;color:#718096;margin-bottom:6px">下载入口</div>\n        <div class="action-row">' + hDownloadBtnHtml(assetId) + '</div>\n      </div>';
    }
    return '<div style="margin-top:10px">\n      <div style="font-size:0.78rem;color:#718096;margin-bottom:6px">下载入口</div>\n      <p style="font-size:0.82rem;color:#a0aec0">当前历史记录未返回可下载音频资产。</p>\n    </div>';
  }

  function historyEmptyStateHtml() {
    return '<div style="text-align:center;padding:32px 16px;color:#718096">\n      <div style="font-size:0.88rem;margin-bottom:8px">暂无历史记录</div>\n      <div style="font-size:0.82rem">完成一次音频生成后，历史任务会出现在这里。</div>\n    </div>';
  }

  function historyLoadErrorHtml(message) {
    var msg = message ? hEsc(message) : '';
    return '<div style="text-align:center;padding:24px 16px;color:#c53030">\n      <div style="font-size:0.88rem;margin-bottom:8px">历史记录加载失败</div>\n      <div style="font-size:0.82rem;color:#718096">请确认本地服务仍在运行，稍后再试。</div>\n      ' + (msg ? '<div style="font-size:0.78rem;margin-top:8px;color:#c53030">' + msg + '</div>' : '') + '\n    </div>';
  }

  function historyEndStateHtml() {
    return '<div style="text-align:center;padding:16px;color:#a0aec0;font-size:0.82rem">没有更多历史记录了。</div>';
  }

  function historyFilteredEmptyStateHtml() {
    return '<div style="text-align:center;padding:32px 16px;color:#718096">\n      <div style="font-size:0.88rem;margin-bottom:8px">没有匹配的历史记录</div>\n      <div style="font-size:0.82rem">请调整搜索关键词或状态筛选。</div>\n    </div>';
  }

  function getHistoryAudioAssetId(job) {
    if (job.audio_asset && job.audio_asset.id) return job.audio_asset.id;
    if (job.audio_asset_id) return job.audio_asset_id;
    if (job.asset_id) return job.asset_id;
    return null;
  }

  function historyJobCardHtml(job) {
    var typeMap = { sync_render: '单条', async_render: '异步', stream_render: '流式' };
    var typeLabel = typeMap[job.job_type] || job.job_type || '-';
    var time = job.created_at ? hFormatLocalDateTime(job.created_at) : '-';
    var rawText = job.input_text || '';
    var textSnippet = rawText ? (rawText.slice(0, 50) + (rawText.length > 50 ? '…' : '')) : '<span style="color:#a0aec0">-</span>';
    var rawJobId = job.id || job.job_id || '';
    var jobIdShort = rawJobId ? (rawJobId.slice(0, 16) + (rawJobId.length > 16 ? '…' : '')) : '-';
    var statusBadge = '<span class="' + hStatusClass(job.status) + '">' + hStatusLabel(job.status) + '</span>';

    var assetId = getHistoryAudioAssetId(job);
    var playDisabled = !assetId ? ' disabled title="该历史记录暂无可播放音频"' : ' data-asset-id="' + hEsc(assetId) + '"';
    var playBtn = '<button class="btn-sm" data-action="play-history"' + playDisabled + ' title="播放音频">播放</button>';
    var downloadBtn = assetId
      ? '<a class="btn-sm" href="/api/voice/assets/' + encodeURIComponent(assetId) + '/download" target="_blank" title="下载音频">下载</a>'
      : '<button class="btn-sm" disabled title="该历史记录暂无可下载音频">下载</button>';
    var copyBtn = '<button class="btn-sm" title="复制 job_id" data-action="copy-job-id" data-job-id="' + hEsc(rawJobId) + '">复制</button>';
    var deleteBtn = '<button class="btn-sm" data-action="delete-history" data-job-id="' + hEsc(rawJobId) + '" title="删除历史记录，不删除音频文件">删除</button>';

    return '<div class="history-row" data-job-id="' + hEsc(rawJobId) + '">\n      <span class="history-type">' + hEsc(typeLabel) + '</span>\n      ' + statusBadge + '\n      <span class="history-time" title="' + hUtcTitle(job.created_at) + '">' + hEsc(time) + '</span>\n      <span class="history-text" title="' + hEsc(rawText) + '">' + textSnippet + '</span>\n      <span class="history-job-id" title="' + hEsc(rawJobId) + '">' + hEsc(jobIdShort) + '</span>\n      <span class="history-actions">\n        ' + playBtn + '\n        ' + downloadBtn + '\n        ' + copyBtn + '\n        ' + deleteBtn + '\n      </span>\n    </div>';
  }

  // ── filter helpers ────────────────────────────────────────────────

  function filterHistoryJobs(jobs) {
    var filtered = jobs;
    var statusFilter = getHistoryStatusFilter();
    if (statusFilter !== 'all') {
      filtered = filtered.filter(function (job) {
        if (statusFilter === 'success') return hIsSuccessStatus(job.status);
        if (statusFilter === 'processing') return hIsProcessingStatus(job.status);
        if (statusFilter === 'failed') return hIsFailedStatus(job.status);
        return true;
      });
    }
    var search = getHistorySearch();
    if (search.trim()) {
      var q = search.toLowerCase();
      filtered = filtered.filter(function (job) {
        var fields = [job.input_text, job.processed_text, job.provider, job.model, job.job_id, job.id, job.job_type, job.status].filter(Boolean).join(' ').toLowerCase();
        return fields.indexOf(q) !== -1;
      });
    }
    return filtered;
  }

  function updateHistoryFilterHint() {
    var hintEl = document.getElementById('historyFilterHint');
    var clearBtn = document.getElementById('historyClearFilters');
    if (!hintEl) return;
    var hasFilter = getHistorySearch().trim() || getHistoryStatusFilter() !== 'all';
    if (clearBtn) clearBtn.style.display = hasFilter ? '' : 'none';
    var jobs = getHistoryJobs();
    if (!jobs || jobs.length === 0) {
      hintEl.textContent = '';
      return;
    }
    var filtered = filterHistoryJobs(jobs);
    if (hasFilter) {
      hintEl.textContent = '已加载 ' + jobs.length + ' 条，当前显示 ' + filtered.length + ' 条。筛选仅作用于已加载历史记录。';
    } else {
      hintEl.textContent = '已加载 ' + jobs.length + ' 条历史记录。';
    }
  }

  // ── render ────────────────────────────────────────────────────────

  function renderHistoryList() {
    var listEl = document.getElementById('historyList');
    var moreBtn = document.getElementById('loadMoreHistory');
    if (!listEl) return;
    var jobs = getHistoryJobs();
    var filtered = filterHistoryJobs(jobs);
    if (!jobs || jobs.length === 0) {
      listEl.innerHTML = historyEmptyStateHtml();
      if (moreBtn) moreBtn.style.display = 'none';
      updateHistoryFilterHint();
      return;
    }
    if (filtered.length === 0) {
      listEl.innerHTML = historyFilteredEmptyStateHtml();
      if (moreBtn) moreBtn.style.display = getHistoryOffset() < getHistoryTotal() ? '' : 'none';
      updateHistoryFilterHint();
      return;
    }
    var fragment = document.createDocumentFragment();
    filtered.forEach(function (job) {
      var div = document.createElement('div');
      div.innerHTML = historyJobCardHtml(job);
      fragment.appendChild(div.firstElementChild);
    });
    listEl.innerHTML = '';
    listEl.appendChild(fragment);
    var hasMore = getHistoryOffset() < getHistoryTotal();
    if (moreBtn) moreBtn.style.display = hasMore ? '' : 'none';
    if (!hasMore && getHistoryTotal() > 0) {
      var endHint = document.createElement('div');
      endHint.innerHTML = historyEndStateHtml();
      listEl.appendChild(endHint);
    }
    updateHistoryFilterHint();
  }

  // ── filter input handlers ──────────────────────────────────────────

  function handleHistorySearchInput() {
    var searchEl = document.getElementById('historySearch');
    if (searchEl) setHistorySearch(searchEl.value);
    renderHistoryList();
  }

  function handleHistoryStatusFilterChange() {
    var filterEl = document.getElementById('historyStatusFilter');
    if (filterEl) setHistoryStatusFilter(filterEl.value);
    renderHistoryList();
  }

  function clearHistoryFilters() {
    var searchEl = document.getElementById('historySearch');
    var filterEl = document.getElementById('historyStatusFilter');
    if (searchEl) searchEl.value = '';
    if (filterEl) filterEl.value = 'all';
    setHistorySearch('');
    setHistoryStatusFilter('all');
    renderHistoryList();
  }

  // ── core load / refresh ────────────────────────────────────────────

  window.loadHistory = async function (offset) {
    if (offset === undefined) offset = 0;
    if (getHistoryLoading()) return;
    var listEl = document.getElementById('historyList');
    var moreBtn = document.getElementById('loadMoreHistory');
    if (offset === 0) {
      setHistoryOffset(0);
      setHistoryTotal(0);
      setHistoryJobs([]);
      if (listEl) listEl.innerHTML = '<div style="font-size:0.82rem;color:#718096">加载中…</div>';
    }
    setHistoryLoading(true);
    try {
      var resp = await fetch('/api/voice/jobs?limit=10&offset=' + offset);
      var data = await resp.json();
      if (!resp.ok) return;
      setHistoryTotal(data.total || 0);
      var jobs = data.jobs || [];

      if (offset === 0 && jobs.length === 0) {
        setHistoryJobs([]);
        if (listEl) listEl.innerHTML = historyEmptyStateHtml();
        if (moreBtn) moreBtn.style.display = 'none';
        updateHistoryFilterHint();
        return;
      }

      var existing = getHistoryJobs();
      setHistoryJobs(existing.concat(jobs));
      setHistoryOffset(offset + jobs.length);
      renderHistoryList();
    } catch (e) {
      if (offset === 0) {
        setHistoryJobs([]);
        if (listEl) listEl.innerHTML = historyLoadErrorHtml(e.message || '');
        updateHistoryFilterHint();
      }
    } finally {
      setHistoryLoading(false);
    }
  };

  window.loadMoreHistory = function () {
    if (getHistoryLoading()) return;
    window.loadHistory(getHistoryOffset());
  };

  window.refreshHistory = async function () {
    setHistoryJobs([]);
    setHistoryOffset(0);
    setHistoryTotal(0);
    setHistoryLoading(false);
    var listEl = document.getElementById('historyList');
    if (listEl) listEl.innerHTML = '<div style="font-size:0.82rem;color:#718096">加载中…</div>';
    updateHistoryFilterHint();
    await window.loadHistory(0);
  };

  // ── audio toggle / delete ─────────────────────────────────────────

  window.toggleHistoryAudio = function (assetId, jobId, historyRow) {
    if (!assetId) {
      window.alert('该历史记录暂无可播放音频');
      return;
    }
    var audioRow = historyRow.nextElementSibling;
    if (!audioRow || !audioRow.classList.contains('history-audio-row')) {
      audioRow = document.createElement('div');
      audioRow.className = 'history-audio-row';
      historyRow.parentNode.insertBefore(audioRow, historyRow.nextSibling);
    }

    var activeRow = getActiveHistoryAudioRow();
    if (activeRow && activeRow !== audioRow && activeRow.classList.contains('visible')) {
      activeRow.classList.remove('visible');
      activeRow.innerHTML = '';
    }

    if (audioRow.classList.contains('visible')) {
      audioRow.classList.remove('visible');
      audioRow.innerHTML = '';
      setActiveHistoryAudioRow(null);
    } else {
      audioRow.innerHTML = '<div style="padding:8px 0">' + historyAudioPlayerHtml(assetId) + '</div>';
      audioRow.classList.add('visible');
      setActiveHistoryAudioRow(audioRow);
      var audioEl = audioRow.querySelector('audio');
      var statusEl = audioRow.querySelector('.history-audio-status');
      if (audioEl && statusEl) {
        attachHistoryAudioEvents(audioEl, statusEl, assetId);
        var playPromise = audioEl.play();
        if (playPromise && typeof playPromise.catch === 'function') {
          playPromise.catch(function () {
            statusEl.textContent = '浏览器阻止了自动播放，请点击播放器开始播放。';
            statusEl.className = 'history-audio-status muted';
          });
        }
      }
    }
  };

  window.deleteHistoryJob = async function (jobId, historyRow) {
    if (!jobId) return;
    if (!window.confirm('确认删除这条历史记录？音频文件不会被物理删除。')) return;
    var delBtn = historyRow.querySelector('[data-action="delete-history"]');
    if (delBtn) { delBtn.disabled = true; delBtn.textContent = '删除中…'; }
    try {
      var resp = await fetch('/api/voice/jobs/' + encodeURIComponent(jobId), { method: 'DELETE' });
      if (resp.status === 404) {
        window.alert('历史记录不存在或已删除。');
        await window.refreshHistory();
        return;
      }
      if (!resp.ok) {
        var data;
        try { data = await resp.json(); } catch (_) { data = {}; }
        window.alert('删除失败：' + (data.detail || data.message || 'HTTP ' + resp.status));
        return;
      }
      var nextSibling = historyRow.nextElementSibling;
      if (nextSibling && nextSibling.classList.contains('history-audio-row')) {
        if (getActiveHistoryAudioRow() === nextSibling) setActiveHistoryAudioRow(null);
        nextSibling.remove();
      }
      historyRow.remove();
      if (getHistoryOffset() > 0) setHistoryOffset(getHistoryOffset() - 1);
      if (getHistoryTotal() > 0) setHistoryTotal(getHistoryTotal() - 1);
      updateHistoryFilterHint();
      if (typeof window.showToast === 'function') {
        window.showToast('已删除历史记录');
      }
    } catch (e) {
      window.alert('删除失败：' + (e.message || '网络错误'));
    } finally {
      if (delBtn) { delBtn.disabled = false; delBtn.textContent = '删除'; }
    }
  };

  // ── expose onclick-compatible handlers ─────────────────────────────

  // copyJobId is called from event delegation in index.html as copyJobId(jobId, btn)
  window.copyJobId = function (jobId, btnEl) {
    hCopyJobId(jobId, btnEl);
  };

  // expose filter handlers for HTML onclick attributes
  window.handleHistorySearchInput = handleHistorySearchInput;
  window.handleHistoryStatusFilterChange = handleHistoryStatusFilterChange;
  window.clearHistoryFilters = clearHistoryFilters;
  window.renderHistoryList = renderHistoryList;
  window.filterHistoryJobs = filterHistoryJobs;

  // ── init: load history on page load ────────────────────────────────
  window.loadHistory(0);
})();
