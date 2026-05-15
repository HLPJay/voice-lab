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
  var STORAGE_KEY = 'voice_lab_recent_samples_v1';

  var _storageListener = null;
  var _eventsBound = false;

  // ── helpers ─────────────────────────────────────────────────────────

  function getRoot() {
    return document.getElementById(ROOT_ID);
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
    return map[source] || source || '';
  }

  function truncateText(text, maxLen) {
    if (!text) return '';
    if (text.length <= maxLen) return text;
    return text.substring(0, maxLen) + '…';
  }

  // ── card builder ────────────────────────────────────────────────────

  function buildCard(sample) {
    var id = sample.sample_id || '';
    var text = truncateText(sample.text_preview || '', 60);
    var profileName = sample.profile_name || sample.profile_id || '';
    var voiceName = sample.voice_name || sample.voice_id || '';
    var source = sample.source || '';
    var duration = formatDuration(sample.duration_ms);
    var downloadUrl = sample.download_url || '';
    var canPlay = downloadUrl && downloadUrl.indexOf('blob:') !== 0;

    var sourceBadge = sourceLabel(source);

    var html = '<div class="sample-card" data-sample-id="' + id + '">';

    // Header row: source badge + duration
    if (sourceBadge || duration) {
      html += '<div class="sample-card-meta">';
      if (sourceBadge) {
        html += '<span class="sample-source-badge">' + sourceBadge + '</span>';
      }
      if (duration) {
        html += '<span class="sample-duration">' + duration + '</span>';
      }
      html += '</div>';
    }

    // Text preview
    if (text) {
      html += '<div class="sample-text" title="' + (sample.text_preview || '') + '">' + text + '</div>';
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

    // Action buttons
    html += '<div class="sample-card-actions">';
    if (canPlay) {
      html += '<button class="sample-btn-play" data-url="' + encodeURIComponent(downloadUrl) + '" title="播放">▶</button>';
    }
    html += '<button class="sample-btn-copy" data-text="' + encodeURIComponent(sample.text_preview || '') + '" title="复制文本">⎘</button>';
    html += '<button class="sample-btn-fill" data-text="' + encodeURIComponent(sample.text_preview || '') + '" title="填入工作台">↓</button>';
    html += '<button class="sample-btn-delete" data-id="' + id + '" title="删除">✕</button>';
    html += '</div>';

    html += '</div>';
    return html;
  }

  // ── render ─────────────────────────────────────────────────────────

  function render() {
    var root = getRoot();
    if (!root) return;

    var samples = [];
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        samples = JSON.parse(raw);
        if (!Array.isArray(samples)) samples = [];
      }
    } catch (e) {
      samples = [];
    }

    if (samples.length === 0) {
      root.innerHTML = '<div class="sample-sidebar-empty">暂无样本</div>';
      return;
    }

    var html = '<div class="sample-sidebar-header">';
    html += '<span class="sample-sidebar-title">最近样本 <em>(' + samples.length + ')</em></span>';
    html += '<button class="sample-btn-clear" id="sampleSidebarClearBtn">清空</button>';
    html += '</div>';

    for (var i = 0; i < samples.length; i++) {
      html += buildCard(samples[i]);
    }

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

      var url = target.getAttribute ? target.getAttribute('data-url') : null;
      var text = target.getAttribute ? target.getAttribute('data-text') : null;
      var sampleId = target.getAttribute ? target.getAttribute('data-id') : null;

      // Play
      if (target.classList.contains('sample-btn-play') && url) {
        playSample(decodeURIComponent(url));
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

      // Clear all
      if (target.id === 'sampleSidebarClearBtn') {
        clearSamples();
        return;
      }
    });
  }

  // ── playSample ─────────────────────────────────────────────────────

  function playSample(url) {
    if (!url) return;
    // Reuse the shared audio player in index.html if available
    if (window._sharedAudioPlayer) {
      window._sharedAudioPlayer(url);
      return;
    }
    // Fallback: create a temporary audio element
    var audio = new Audio(url);
    audio.play().catch(function () {
      // fail silently — browser autoplay policy may block
    });
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
      // Trigger input event so char-count updates
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
        if (e && e.key === STORAGE_KEY) {
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
