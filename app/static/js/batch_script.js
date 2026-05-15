/**
 * batch_script.js
 *
 * Phase 1: Extract handleBatchScriptSubmit() from index.html.
 *
 * Responsibilities:
 * - Script batch submit entry point
 * - Collect _scriptRows state and build mode='script' payload
 * - Call shared batch progress functions (showBatchProgress / startBatchPoll)
 *
 * Remains in index.html:
 * - addScriptLine / removeScriptLine / updateScriptLineLimitState
 * - _scriptRows / _scriptLineCount / MAX_SCRIPT_LINES
 * - scriptLines event delegation (input/change/click listeners)
 * - populateProfileSelect / loadProfiles / _cachedProfiles
 * - Shared batch polling/rendering functions
 * - Shared batch state variables
 */

(function() {
  // Local HTML escaper (equivalent to index.html's esc())
  function bsEsc(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  window.handleBatchScriptSubmit = async function() {
    // Sync DOM values into _scriptRows state before collecting
    document.querySelectorAll('[id^="scriptLine_"]').forEach(function(row) {
      var id = parseInt(row.id.split('_')[1]);
      var state = _scriptRows.find(function(r) { return r.id === id; });
      if (!state) return;
      var roleEl = document.getElementById('scriptRole_' + id);
      var textEl = document.getElementById('scriptText_' + id);
      var profileEl = document.getElementById('scriptProfile_' + id);
      if (roleEl) state.role = roleEl.value;
      if (textEl) state.text = textEl.value;
      if (profileEl) state.profileId = profileEl.value;
    });

    var lines = [];
    _scriptRows.forEach(function(state) {
      if (state.text && state.text.trim()) {
        lines.push({ role: state.role || '', text: state.text.trim(), profile_id: state.profileId || '', params: {} });
      }
    });

    // Validation
    var resultsEl = document.getElementById('batchScriptResult');
    var showResult = function(html) {
      if (resultsEl) { resultsEl.style.display = ''; resultsEl.innerHTML = html; }
    };
    var clearResult = function() { if (resultsEl) { resultsEl.style.display = 'none'; resultsEl.innerHTML = ''; } };

    if (lines.length === 0) {
      showResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">请至少填写一行台词</div>');
      return;
    }
    // Per-row empty text validation with visual feedback
    var firstEmptyRowIdx = -1;
    _scriptRows.forEach(function(state, idx) {
      var textEl = document.getElementById('scriptText_' + state.id);
      if (textEl) {
        textEl.style.borderColor = '';
        textEl.title = '';
      }
      if (!state.text || !state.text.trim()) {
        if (firstEmptyRowIdx === -1) firstEmptyRowIdx = idx;
        if (textEl) {
          textEl.style.borderColor = '#e53e3e';
          textEl.title = '第 ' + (idx + 1) + ' 行缺少台词文本';
        }
      }
    });
    if (firstEmptyRowIdx !== -1) {
      showResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">第 ' + (firstEmptyRowIdx + 1) + ' 行缺少台词文本</div>');
      return;
    }
    var missingProfile = lines.filter(function(l) { return !l.profile_id; });
    if (missingProfile.length > 0) {
      showResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">第 ' + (lines.indexOf(missingProfile[0]) + 1) + ' 行缺少声音人设</div>');
      return;
    }

    var provider = document.getElementById('batchScriptProvider').value;
    var silence = parseInt(document.getElementById('batchScriptSilence').value) || 500;
    var outputFormat = document.getElementById('batchScriptOutputFormat').value;
    var needSubtitle = document.getElementById('batchScriptNeedSubtitle').checked;

    var btn = document.getElementById('batchScriptSubmit');
    btn.disabled = true;
    btn.textContent = '提交中…';
    clearResult();

    try {
      var resp = await guardedJsonFetch('/api/voice/batch/submit', {
        mode: 'script',
        script: lines,
        provider: provider,
        silence_between_ms: silence,
        output_format: 'hex',
        audio_format: outputFormat,
        need_subtitle: needSubtitle,
        confirm_cost: false,
      }, { provider: provider, operation: 'batch_script', highRisk: true });

      if (!resp.ok) {
        var err = await parseApiError(resp);
        if (err.code === 'RESOURCE_LIMIT_EXCEEDED') {
          showResult(window.renderApiError(err));
        } else if (err.code === 'VALIDATION_ERROR') {
          showResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">' + bsEsc(err.message) + '</div>');
        } else {
          showResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">提交失败：' + bsEsc(formatApiError(err)) + '</div>');
        }
        btn.disabled = false;
        btn.textContent = '提交批量任务';
        return;
      }

      var data = await resp.json();
      _currentBatchId = data.batch_id;

      // Show success inline — stay on script tab
      showResult('<div style="background:#f0fff4;border:1px solid #9ae6b4;border-radius:8px;padding:14px 16px;font-size:0.85rem;color:#276749">' +
        '<div style="font-weight:600;margin-bottom:6px">批量剧本任务已提交</div>' +
        '<div>任务ID：<code style="font-size:0.78rem;background:#edf2f7;padding:1px 4px;border-radius:3px">' + bsEsc(data.batch_id) + '</code></div>' +
        '<div>状态：' + bsEsc(data.status || 'pending') + ' &nbsp;|&nbsp; 总段数：' + (data.total_segments || lines.length) + '</div>' +
        '<div style="margin-top:8px;font-size:0.78rem;color:#718096">批量进度如下方显示</div>' +
        '</div>');

      showBatchProgress(data.batch_id, 'batchScriptProgressPanel');
      startBatchPoll(data.batch_id, 'batchScriptProgressPanel');
      loadRuntimeStatus();
    } catch (e) {
      if (e.message !== 'USER_CANCELLED') {
        if (e && e.code === 'RESOURCE_LIMIT_EXCEEDED') {
          showResult(window.renderApiError(e));
        } else {
          showResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">提交失败：' + bsEsc(e && e.message ? e.message : String(e)) + '</div>');
        }
      }
    } finally {
      if (btn.disabled) {
        btn.disabled = false;
        btn.textContent = '提交批量任务';
      }
    }
  };
})();
