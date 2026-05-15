/**
 * sample_sidebar.js
 *
 * Phase B4: Sample observation sidebar UI module.
 *
 * Responsibilities:
 * - Render sample cards from SampleStore in the sidebar container
 * - Provide play / copy / fill / delete / clear actions
 * - Sync with SampleStore changes via localStorage events
 *
 * Does NOT:
 * - Depend on index.html internal state
 * - Call any backend API
 * - Save audio blobs or blob: URLs
 */

(function () {
  'use strict';

  var ROOT_ID = 'sampleSidebarRoot';
  var MAX_VISIBLE = 20;

  var _storageListener = null;
  var _eventsBound = false;

  // ── helpers ─────────────────────────────────────────────────────────

  function getRoot() {
    return document.getElementById(ROOT_ID);
  }

  /**
   * HTML escape for text content (innerHTML text nodes and text children).
   * Uses textContent pattern — safe for all browsers, no regex edge-cases.
   */
  function esc(s) {
    var div = document.createElement('div');
    div.textContent = s == null ? '' : String(s);
    return div.innerHTML;
  }

  /**
   * HTML attribute value escape — escapes & " ' < > for use inside
   * quoted attribute values (data-* attributes, title, href, src, etc.).
   */
  function attr(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /**
   * Get samples exclusively through SampleStore — never read localStorage directly.
   */
  function getSamplesSafe() {
    try {
      if (!window.SampleStore || typeof window.SampleStore.getSamples !== 'function') return [];
      return window.SampleStore.getSamples();
    } catch (e) {
      return [];
    }
  }

  function formatDuration(ms) {
    if (ms == null || isNaN(ms)) return '';
    var totalSec = Math.round(ms / 1000);
    var min = Math.floor(totalSec / 60);
    var sec = totalSec % 60;
    if (min > 0) {
      return min + '′' + sec + '″';
    }
    return sec + '″';
  }

  function formatCreatedAt(value) {
    if (!value) return '';
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return '';
      return d.toLocaleString();
    } catch (e) {
      return '';
    }
  }

  /**
   * URL safety check for audio sources.
   * Rejects: blob:, javascript:, data:
   * Allows: /api/..., http://..., https://...
   */
  function isSafeAudioUrl(url) {
    if (!url) return false;
    var s = String(url).trim().toLowerCase();
    if (s.indexOf('blob:') === 0) return false;
    if (s.indexOf('javascript:') === 0) return false;
    if (s.indexOf('data:') === 0) return false;
    return s.indexOf('/api/') === 0 ||
           s.indexOf('http://') === 0 ||
           s.indexOf('https://') === 0;
  }

  /**
   * Map source tag to human-readable label. Receives raw source string.
   * Returns escaped label for display.
   */
  function sourceLabel(source) {
    var map = {
      workspace_sync: '单条',
      workspace_async: '异步',
      workspace_stream: '流式',
      workspace_variant: '多版本',
      audition: '试听',
      batch_longtext_merged: '长文合并',
      batch_script_merged: '剧本合并',
      batch_longtext_segment: '长文分段',
      batch_script_segment: '剧本分段',
    };
    return map[source] || esc(source) || '';
  }

  function truncateText(text, maxLen) {
    if (!text) return '';
    if (text.length <= maxLen) return text;
    return text.substring(0, maxLen) + '…';
  }

  // ── card builder ────────────────────────────────────────────────────

  function buildCard(sample) {
    // Raw values
    var idRaw = sample.sample_id || '';
    var textRaw = sample.text_preview || '';
    var sourceRaw = sample.source || '';
    var providerRaw = sample.provider || '';
    var modelRaw = sample.model || '';
    var createdAtRaw = sample.created_at || '';
    var profileNameRaw = sample.profile_name || sample.profile_id || '';
    var voiceNameRaw = sample.voice_name || sample.voice_id || '';
    var downloadUrl = sample.download_url || '';
    var canPlay = isSafeAudioUrl(downloadUrl);
    var canDownload = isSafeAudioUrl(downloadUrl);

    // Escaped display values
    var idAttr = attr(idRaw);
    var textEsc = esc(truncateText(textRaw, 60));
    var textTitleAttr = attr(textRaw);
    var sourceBadge = sourceLabel(sourceRaw); // sourceLabel calls esc internally
    var durationEsc = esc(formatDuration(sample.duration_ms));
    var providerEsc = esc(providerRaw);
    var modelEsc = esc(modelRaw);
    var createdAtEsc = esc(formatCreatedAt(createdAtRaw));
    var profileNameEsc = esc(profileNameRaw);
    var voiceNameEsc = esc(voiceNameRaw);
    var downloadUrlAttr = attr(downloadUrl);
    var downloadName = attr(sample.asset_id || sample.sample_id || 'sample-audio');

    var html = '<div class="sample-card" data-sample-id="' + idAttr + '">';

    // Header row: source badge + duration
    if (sourceBadge || durationEsc) {
      html += '<div class="sample-card-meta">';
      if (sourceBadge) {
        html += '<span class="sample-source-badge">' + sourceBadge + '</span>';
      }
      if (durationEsc) {
        html += '<span class="sample-duration">' + durationEsc + '</span>';
      }
      html += '</div>';
    }

    // Text preview
    if (textEsc) {
      html += '<div class="sample-text" title="' + textTitleAttr + '">' + textEsc + '</div>';
    }

    // Secondary metadata: provider / model / created_at
    if (providerEsc || modelEsc || createdAtEsc) {
      html += '<div class="sample-card-meta sample-card-meta-secondary">';
      if (providerEsc) {
        html += '<span class="sample-meta-item"><span class="sample-meta-label">Provider:</span> ' + providerEsc + '</span>';
      }
      if (modelEsc) {
        html += '<span class="sample-meta-item"><span class="sample-meta-label">Model:</span> ' + modelEsc + '</span>';
      }
      if (createdAtEsc) {
        html += '<span class="sample-meta-item"><span class="sample-meta-label">时间:</span> ' + createdAtEsc + '</span>';
      }
      html += '</div>';
    }

    // Profile + voice
    if (profileNameEsc || voiceNameEsc) {
      html += '<div class="sample-profile">';
      if (profileNameEsc) {
        html += '<span class="sample-profile-name">' + profileNameEsc + '</span>';
      }
      if (voiceNameEsc) {
        html += ' › <span class="sample-voice-name">' + voiceNameEsc + '</span>';
      }
      html += '</div>';
    }

    // Action buttons — play uses data-id (not data-url) for in-card playback
    html += '<div class="sample-card-actions">';
    if (canPlay) {
      html += '<button class="sample-btn-play" data-id="' + idAttr + '" title="播放">▶</button>';
    }
    if (canDownload) {
      html += '<a class="sample-btn-download" href="' + downloadUrlAttr + '" download="' + downloadName + '" title="下载">⇩</a>';
    }
    if (sample.context_id) {
      html += '<button class="sample-btn-detail" data-id="' + idAttr + '" title="详情">ⓘ</button>';
    }
    html += '<button class="sample-btn-copy" data-text="' + encodeURIComponent(textRaw) + '" title="复制文本">⎘</button>';
    html += '<button class="sample-btn-fill" data-text="' + encodeURIComponent(textRaw) + '" title="填入工作台">↓</button>';
    html += '<button class="sample-btn-delete" data-id="' + idAttr + '" title="删除">✕</button>';
    html += '</div>';

    html += '</div>';
    return html;
  }

  // ── render ─────────────────────────────────────────────────────────

  function ensureActionEventsBound(root) {
    if (!_eventsBound && root) {
      bindActionEvents(root);
      _eventsBound = true;
    }
  }

  function render() {
    var root = getRoot();
    if (!root) return;

    ensureActionEventsBound(root);

    var allSamples = getSamplesSafe();
    var visibleSamples = allSamples.slice(0, MAX_VISIBLE);
    var total = allSamples.length;
    var showing = visibleSamples.length;

    if (total === 0) {
      root.innerHTML =
        '<div class="sample-sidebar-card">' +
          '<div class="sample-sidebar-header">' +
            '<span class="sample-sidebar-title">最近样本</span>' +
            '<button class="sample-btn-refresh" id="sampleSidebarRefreshBtn" title="刷新">↻</button>' +
          '</div>' +
          '<div class="sample-sidebar-empty">暂无样本</div>' +
        '</div>';
      return;
    }

    var html =
      '<div class="sample-sidebar-card">' +
        '<div class="sample-sidebar-header">' +
          '<span class="sample-sidebar-title">最近样本 <em>(' + showing + '/' + total + ')</em></span>' +
          '<button class="sample-btn-refresh" id="sampleSidebarRefreshBtn" title="刷新">↻</button>' +
          '<button class="sample-btn-clear" id="sampleSidebarClearBtn">清空</button>' +
        '</div>' +
        '<div class="sample-sidebar-list">';

    for (var i = 0; i < visibleSamples.length; i++) {
      html += buildCard(visibleSamples[i]);
    }

    html += '</div></div>';

    root.innerHTML = html;
  }

  // ── event binding (delegated) ───────────────────────────────────────

  function bindActionEvents(root) {
    root.addEventListener('click', function (e) {
      var target = e.target || e.srcElement;
      if (!target || target === root) return;

      var text = target.getAttribute ? target.getAttribute('data-text') : null;
      var sampleId = target.getAttribute ? target.getAttribute('data-id') : null;

      // Play — uses data-id to find sample and render in-card audio
      if (target.classList.contains('sample-btn-play') && sampleId) {
        playSample(sampleId);
        return;
      }

      // Copy text
      if (target.classList.contains('sample-btn-copy') && text) {
        copyText(decodeURIComponent(text));
        return;
      }

      // Fill text input
      if (target.classList.contains('sample-btn-fill') && text) {
        fillTextInput(decodeURIComponent(text));
        return;
      }

      // Delete single sample
      if (target.classList.contains('sample-btn-delete') && sampleId) {
        deleteSample(sampleId);
        return;
      }

      // Detail view
      if (target.classList.contains('sample-btn-detail') && sampleId) {
        showSampleDetail(sampleId);
        return;
      }

      // Refresh
      if (target.id === 'sampleSidebarRefreshBtn') {
        render();
        return;
      }

      // Clear all
      if (target.id === 'sampleSidebarClearBtn') {
        clearSamples();
        return;
      }
    });
  }

  // ── playSample(sampleId) — in-card audio ───────────────────────────

  function playSample(sampleId) {
    if (!sampleId) return;

    var samples = getSamplesSafe();
    var sample = null;
    for (var i = 0; i < samples.length; i++) {
      if (samples[i] && samples[i].sample_id === sampleId) {
        sample = samples[i];
        break;
      }
    }
    if (!sample) {
      window.alert && window.alert('未找到该样本');
      return;
    }
    var downloadUrl = sample.download_url;
    if (!isSafeAudioUrl(downloadUrl)) {
      return;
    }

    // Find the card element
    var card = null;
    var allCards = (getRoot() && getRoot().querySelectorAll) ? getRoot().querySelectorAll('.sample-card') : [];
    for (var j = 0; j < allCards.length; j++) {
      if (allCards[j].getAttribute && allCards[j].getAttribute('data-sample-id') === sampleId) {
        card = allCards[j];
        break;
      }
    }
    if (!card) return;

    // Toggle: if player already exists, remove it
    var existing = card.querySelector('.sample-card-player');
    if (existing) {
      existing.remove();
      return;
    }

    // Build in-card audio player — use attr() for the src attribute
    var player = document.createElement('div');
    player.className = 'sample-card-player';
    var audioSrcAttr = attr(downloadUrl);
    player.innerHTML =
      '<audio controls autoplay style="width:100%;height:32px;margin-top:8px">' +
        '<source src="' + audioSrcAttr + '" type="audio/mpeg">' +
        '您的浏览器不支持音频播放</audio>';
    card.appendChild(player);
  }

  // ── copyText ───────────────────────────────────────────────────────

  function copyText(text) {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(function () {});
      return;
    }
    // Fallback for older browsers
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  // ── fillTextInput ──────────────────────────────────────────────────

  function fillTextInput(text) {
    var input = document.getElementById('textInput');
    if (input) {
      input.value = text;
      input.focus();
      if (typeof Event === 'function') {
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  }

  // ── deleteSample ───────────────────────────────────────────────────

  function deleteSample(sampleId) {
    if (!sampleId) return;
    if (!window.SampleStore || typeof window.SampleStore.deleteSample !== 'function') return;
    window.SampleStore.deleteSample(sampleId);
    render();
  }

  // ── clearSamples ───────────────────────────────────────────────────

  function clearSamples() {
    if (!window.confirm || !window.confirm('确定清空最近样本？')) return;
    if (!window.SampleStore || typeof window.SampleStore.clearSamples !== 'function') return;
    window.SampleStore.clearSamples();
    render();
  }

  // ── refresh ─────────────────────────────────────────────────────────

  function refresh() {
    render();
  }

  // ── showSampleDetail ─────────────────────────────────────────────────

  function showSampleDetail(sampleId) {
    if (!sampleId) return;
    var samples = getSamplesSafe();
    var sample = null;
    for (var i = 0; i < samples.length; i++) {
      if (samples[i] && samples[i].sample_id === sampleId) {
        sample = samples[i];
        break;
      }
    }
    if (!sample) return;
    var contextId = sample.context_id;
    if (!contextId) return;

    var context = null;
    try {
      if (window.ContextStore && typeof window.ContextStore.getContext === 'function') {
        context = window.ContextStore.getContext(contextId);
      }
    } catch (e) {
      context = null;
    }

    var root = getRoot();
    if (!root) return;

    // Remove any existing detail panel
    var existing = root.querySelector('.sample-detail-panel');
    if (existing) existing.remove();

    var panel = document.createElement('div');
    panel.className = 'sample-detail-panel';

    if (!context) {
      panel.innerHTML =
        '<div class="sample-detail-header">' +
          '<span class="sample-detail-title">详情</span>' +
          '<button class="sample-detail-close" title="关闭">✕</button>' +
        '</div>' +
        '<div class="sample-detail-body">' +
          '<div class="sample-detail-empty">完整上下文不可用</div>' +
        '</div>';
      root.appendChild(panel);
      var closeBtn = panel.querySelector('.sample-detail-close');
      if (closeBtn) closeBtn.addEventListener('click', function () { panel.remove(); });
      return;
    }

    var sourceEsc = esc(context.source || '');
    var createdAtEsc = esc(formatCreatedAt(context.created_at));
    var providerEsc = esc(context.provider || '');
    var profileIdEsc = esc(context.profile_id || '');
    var fullTextEsc = esc(context.full_text || '');
    var charCount = context.full_text ? context.full_text.length : 0;
    var sourceLabelText = sourceLabel(context.source || '');
    var sourceBadgeEsc = esc(sourceLabelText);

    panel.innerHTML =
      '<div class="sample-detail-header">' +
        '<span class="sample-detail-title">详情</span>' +
        '<button class="sample-detail-close" title="关闭">✕</button>' +
      '</div>' +
      '<div class="sample-detail-meta">' +
        '<div class="sample-detail-meta-row">' +
          '<span class="sample-detail-meta-label">来源:</span>' +
          '<span class="sample-detail-meta-value">' + sourceBadgeEsc + '</span>' +
        '</div>' +
        (createdAtEsc ? '<div class="sample-detail-meta-row">' +
          '<span class="sample-detail-meta-label">创建:</span>' +
          '<span class="sample-detail-meta-value">' + createdAtEsc + '</span>' +
        '</div>' : '') +
        (providerEsc ? '<div class="sample-detail-meta-row">' +
          '<span class="sample-detail-meta-label">Provider:</span>' +
          '<span class="sample-detail-meta-value">' + providerEsc + '</span>' +
        '</div>' : '') +
        (profileIdEsc ? '<div class="sample-detail-meta-row">' +
          '<span class="sample-detail-meta-label">Profile:</span>' +
          '<span class="sample-detail-meta-value">' + profileIdEsc + '</span>' +
        '</div>' : '') +
        '<div class="sample-detail-meta-row">' +
          '<span class="sample-detail-meta-label">字数:</span>' +
          '<span class="sample-detail-meta-value">' + esc(String(charCount)) + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="sample-detail-text-label">完整文本</div>' +
      '<div class="sample-detail-text-wrap">' +
        '<div class="sample-detail-text">' + fullTextEsc + '</div>' +
      '</div>';

    root.appendChild(panel);

    var closeBtn = panel.querySelector('.sample-detail-close');
    if (closeBtn) closeBtn.addEventListener('click', function () { panel.remove(); });
  }

  // ── init ────────────────────────────────────────────────────────────

  function init() {
    render();

    // Listen for cross-tab storage changes
    if (window.addEventListener && !_storageListener) {
      _storageListener = function (e) {
        if (e && e.key === 'voice_lab_recent_samples_v1') {
          render();
        }
      };
      window.addEventListener('storage', _storageListener);
    }
  }

  // ── expose to window ───────────────────────────────────────────────

  window.SampleSidebar = {
    init: init,
    render: render,
    refresh: refresh,
    playSample: playSample,
    deleteSample: deleteSample,
    clearSamples: clearSamples,
    copyText: copyText,
    fillTextInput: fillTextInput,
    showSampleDetail: showSampleDetail,
  };

})();
