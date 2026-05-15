(function () {
  'use strict';

  // handleBatchLongtextSubmit — extracted from index.html
  // Dependencies (all available as globals when onclick fires):
  //   guardedJsonFetch, parseApiError, renderApiError, renderValidationError,
  //   formatApiError, esc, showBatchProgress, startBatchPoll, loadRuntimeStatus
  //   (all defined in inline script, accessible as globals after page load)
  //   window.showBatchLongtextResult, window.clearBatchLongtextResult (window.* from index.html)

  window.handleBatchLongtextSubmit = async function () {
    var text = document.getElementById('batchText').value.trim();
    if (!text) {
      window.showBatchLongtextResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">请输入待分段文本</div>');
      return;
    }
    var profileId = document.getElementById('batchProfile').value;
    if (!profileId) {
      window.showBatchLongtextResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">请选择声音人设</div>');
      return;
    }
    var provider = document.getElementById('batchProvider').value;
    var strategy = document.getElementById('batchStrategy').value;
    var maxChars = parseInt(document.getElementById('batchMaxChars').value) || 2000;
    var silence = parseInt(document.getElementById('batchSilence').value) || 300;
    var outputFormat = document.getElementById('batchOutputFormat').value;
    var needSubtitle = document.getElementById('batchNeedSubtitle').checked;

    var params = {};
    var speed = document.getElementById('batchSpeed').value;
    var vol = document.getElementById('batchVol').value;
    var pitch = document.getElementById('batchPitch').value;
    var emotion = document.getElementById('batchEmotion').value;
    if (speed) params.speed = parseFloat(speed);
    if (vol) params.vol = parseFloat(vol);
    if (pitch) params.pitch = parseInt(pitch);
    if (emotion) params.emotion = emotion;

    var btn = document.getElementById('batchLongtextSubmit');
    btn.disabled = true;
    btn.textContent = '提交中…';
    window.clearBatchLongtextResult();

    try {
      var resp = await guardedJsonFetch('/api/voice/batch/submit', {
        mode: 'longtext',
        text: text,
        profile_id: profileId,
        provider: provider,
        segment_strategy: strategy,
        max_segment_chars: maxChars,
        silence_between_ms: silence,
        output_format: 'hex',
        audio_format: outputFormat,
        params: params,
        need_subtitle: needSubtitle,
        confirm_cost: false,
      }, { provider: provider, operation: 'batch_longtext', highRisk: true });

      if (!resp.ok) {
        var err = await parseApiError(resp);
        if (err.code === 'RESOURCE_LIMIT_EXCEEDED') {
          window.showBatchLongtextResult(renderApiError(err));
        } else if (err.code === 'VALIDATION_ERROR') {
          window.showBatchLongtextResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">' + esc(err.message) + '</div>');
        } else {
          window.showBatchLongtextResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">提交失败：' + esc(formatApiError(err)) + '</div>');
        }
        btn.disabled = false;
        btn.textContent = '提交批量任务';
        return;
      }

      var data = await resp.json();
      _currentBatchId = data.batch_id;

      // Save batch sample context for later sample_store write
      if (data && data.batch_id) {
        if (!window._batchSampleContextById) window._batchSampleContextById = {};
        window._batchSampleContextById[data.batch_id] = {
          source: 'batch_longtext_merged',
          mode: 'longtext',
          text_preview: text,
          provider: provider,
          profile_id: profileId || null,
          profile_name: null,
          audio_format: outputFormat || null,
          model: null,
          voice_id: null,
          voice_name: null,
        };
      }

      // Save longtext context to ContextStore (fail-safe, non-blocking)
      try {
        if (window.ContextStore && typeof window.ContextStore.pushContext === 'function' && data && data.batch_id) {
          var contextId = data.batch_id;
          window.ContextStore.pushContext({
            context_id: contextId,
            type: 'longtext',
            source: 'batch_longtext_merged',
            full_text: text,
            provider: provider,
            profile_id: profileId || null,
            segment_strategy: strategy,
            max_segment_chars: maxChars,
            silence_between_ms: silence,
            output_format: 'hex',
            audio_format: outputFormat,
            need_subtitle: needSubtitle,
            params: params,
            batch_id: data.batch_id,
          });
          if (window._batchSampleContextById && window._batchSampleContextById[data.batch_id]) {
            window._batchSampleContextById[data.batch_id].context_id = contextId;
          }
        }
      } catch (e) {
        // fail-safe: context save must not block batch generation
      }

      showBatchProgress(data.batch_id);
      startBatchPoll(data.batch_id);
      loadRuntimeStatus();
    } catch (e) {
      if (e.message !== 'USER_CANCELLED') {
        if (e && e.code === 'RESOURCE_LIMIT_EXCEEDED') {
          window.showBatchLongtextResult(renderApiError(e));
        } else {
          window.showBatchLongtextResult('<div style="color:#c53030;font-size:0.85rem;padding:8px 0">提交失败：' + esc(e && e.message ? e.message : String(e)) + '</div>');
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
