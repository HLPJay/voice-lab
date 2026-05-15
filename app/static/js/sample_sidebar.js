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
   * HTML escape helper — prevents untrusted text from becoming code.
   * Uses a detached div so it works in all browsers without regex munging.
   */
  function esc(s) {
    var div = document.createElement('div');
    div.textContent = s == null ? '' : String(s);
    return div.innerHTML;
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

  function sourceLabel(source) {
    var map = {
      workspace_sync: '单条',
      workspace_async: '异步',
      workspace_stream: '流式',
      workspace_variant: '多版本',
      audition: '试听',
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
    var id = esc(sample.sample_id || '');
    var textRaw = sample.text_preview || '';
    var text = esc(truncateText(textRaw, 60));
    var textTitle = esc(textRaw);
    var profileName = esc(sample.profile_name || sample.profile_id || '');
    var voiceName = esc(sample.voice_name || sample.voice_id || '');
    var source = esc(sample.source || '');
    var sourceBadge = sourceLabel(source);
    var duration = formatDuration(sample.duration_ms);
    var durationEsc = esc(duration);
    var downloadUrl = sample.download_url || '';
    var canPlay = downloadUrl && downloadUrl.indexOf('blob:') !== 0;

    var html = '<div class="sample-card" data-sample-id="' + id + '">';

    // Header row: source badge + duration
    if (sourceBadge || duration) {
      html += '<div class="sample-card-meta">';
      if (sourceBadge) {
        html += '<span class="sample-source-badge">' + sourceBadge + '</span>';
      }
      if (duration) {
        html += '<span class="sample-duration">' + durationEsc + '</span>';
      }
      html += '</div>';
    }

    // Text preview
    if (text) {
      html += '<div class="sample-text" title="' + textTitle + '">' + text + '</div>';
    }

    // Profile + voice
    if (profileName || voiceName) {
      html += '<div class="sample-profile">';
      if (profileName) {
        html += '<span class="sample-profile-name">' + profileName + '</span>';
      }
      if (voiceName) {
        html += ' › <span class="sample-voice-name">' + voiceName + '</span>';
      }
      html += '</div>';
    }

    // Action buttons — play uses data-id (not data-url) for in-card playback
    html += '<div class="sample-card-actions">';
    if (canPlay) {
      html += '<button class="sample-btn-play" data-id="' + id + '" title="播放">▶</button>';
    }
    html += '<button class="sample-btn-copy" data-text="' + encodeURIComponent(textRaw) + '" title="复制文本">⎘</button>';
    html += '<button class="sample-btn-fill" data-text="' + encodeURIComponent(textRaw) + '" title="填入工作台">↓</button>';
    html += '<button class="sample-btn-delete" data-id="' + id + '" title="删除">✕</button>';
    html += '</div>';

    html += '</div>';
    return html;
  }

  // ── render ─────────────────────────────────────────────────────────

  function render() {
    var root = getRoot();
    if (!root) return;

    var allSamples = getSamplesSafe();
    var visibleSamples = allSamples.slice(0, MAX_VISIBLE);
    var total = allSamples.length;
    var showing = visibleSamples.length;

    if (total === 0) {
      root.innerHTML =
        '<div class="sample-sidebar-card">' +
          '<div class="sample-sidebar-header">' +
            '<span class="sample-sidebar-title">最近样本</span>' +
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

    // Bind action events once (event delegation on root)
    if (!_eventsBound) {
      bindActionEvents(root);
      _eventsBound = true;
    }
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
    if (!downloadUrl || String(downloadUrl).indexOf('blob:') === 0) {
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

    // Build in-card audio player
    var player = document.createElement('div');
    player.className = 'sample-card-player';
    var audioSrc = esc(downloadUrl);
    player.innerHTML =
      '<audio controls autoplay style="width:100%;height:32px;margin-top:8px">' +
        '<source src="' + audioSrc + '" type="audio/mpeg">' +
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
  };

})();
