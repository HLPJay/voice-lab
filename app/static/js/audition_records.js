(function () {
  'use strict';

  // ── state on window for E2E test compatibility ─────────────────────
  window._auditionRecords = window._auditionRecords || [];

  // ── local esc helper ──────────────────────────────────────────────
  function arEsc(s) {
    if (s == null) return '';
    var d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  // ── render audition records ──────────────────────────────────────

  window.renderAuditionRecords = function () {
    var container = document.getElementById('auditionRecordsTable');
    var countEl = document.getElementById('auditionCount');
    if (!container) return;
    var records = window._auditionRecords || [];
    if (countEl) {
      countEl.textContent = records.length > 0 ? '（共 ' + records.length + ' 条）' : '';
    }
    if (records.length === 0) {
      container.innerHTML = '<div style="font-size:0.78rem;color:#a0aec0;text-align:center;padding:10px 8px;border:1px dashed #e2e8f0;border-radius:8px">暂无试听记录</div>';
      return;
    }
    var cardsHtml = records.map(function (r, i) {
      var textPreview = r.text.length > 20 ? r.text.substring(0, 20) + '…' : r.text;
      var audioHtml = r.audioUrl
        ? '<audio controls style="height:28px;width:160px"><source src="' + arEsc(r.audioUrl) + '" type="audio/mpeg"></audio>'
        : '<span style="color:#a0aec0;font-size:0.72rem">无音频</span>';
      return '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;margin-bottom:8px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;box-shadow:0 1px 3px rgba(0,0,0,0.04)">\n        <div style="flex:1;min-width:160px">\n          <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">\n            <code style="font-size:0.75rem;background:#f7fafc;color:#4a5568;padding:1px 5px;border-radius:3px">' + arEsc(r.voiceId) + '</code>\n            ' + (r.voiceName ? '<span style="font-size:0.72rem;color:#718096">' + arEsc(r.voiceName) + '</span>' : '') + '\n          </div>\n          <div>' + audioHtml + '</div>\n        </div>\n        <div style="flex:1;min-width:120px">\n          <div style="font-size:0.72rem;color:#a0aec0;margin-bottom:3px">文本预览</div>\n          <div style="font-size:0.78rem;color:#4a5568" title="' + arEsc(r.text) + '">' + arEsc(textPreview) + '</div>\n        </div>\n        <div style="display:flex;flex-direction:column;gap:4px;align-items:flex-end">\n          <button class="btn-sm" data-delete="' + i + '" style="margin:0;color:#e53e3e;font-size:0.7rem;padding:2px 6px">删除</button>\n        </div>\n      </div>';
    }).join('');
    container.innerHTML = cardsHtml;
  };

  // ── delete a single record by index ──────────────────────────────
  window.deleteAuditionRecord = function (idx) {
    if (window._auditionRecords && window._auditionRecords.splice) {
      window._auditionRecords.splice(idx, 1);
    }
    window.renderAuditionRecords();
  };

  // ── clear all records ───────────────────────────────────────────
  window.clearAuditionRecords = function () {
    window._auditionRecords = [];
    window.renderAuditionRecords();
  };
})();
