/**
 * voice_design.js
 *
 * Phase 1: Extract voice design function from index.html.
 *
 * Responsibilities:
 * - Voice design entry (handleDesignVoice)
 * - Calls /api/voice/design/create
 * - Renders design success/error results
 * - Renders quick bind panel + quick preview panel
 * - Calls shared profile/binding/voice-list helpers
 *
 * Uses window helpers from index.html (G3 exports):
 * - window.isValidVoiceId
 * - window.hexToBlobUrl
 * - window.handleListVoices
 * - window.populateProfileSelect
 * - window.renderInlineCreateProfile
 * - window.bindVoiceToProfile
 * - window.refreshVoiceBindStatus
 *
 * Uses shared helpers from index.html:
 * - guardedJsonFetch, parseApiError, formatApiError
 * - friendlyErrorMessage, esc, renderApiError, renderValidationError
 */

(function () {
  window.handleDesignVoice = async function () {
    const provider = document.getElementById('designProvider').value;
    const voiceIdInput = document.getElementById('designVoiceId').value.trim();
    const voiceId = voiceIdInput || null;
    const prompt = document.getElementById('designPrompt').value.trim();
    const previewText = document.getElementById('designPreviewText').value.trim();
    const audioFormat = window.getDefaultAudioFormat ? window.getDefaultAudioFormat(provider) : 'mp3';
    const resultsEl = document.getElementById('designResult');
    const btn = document.getElementById('designBtn');

    if (voiceIdInput && !window.isValidVoiceId(voiceIdInput)) {
      resultsEl.innerHTML = '<div class="error-msg">voice_id 格式不正确：至少 8 位，必须以字母开头，只能包含字母、数字、下划线和短横线，且不能以短横线或下划线结尾。</div>';
      return;
    }
    if (!prompt) {
      resultsEl.innerHTML = '<div class="error-msg">请输入音色描述（prompt）</div>';
      return;
    }
    if (!previewText) {
      resultsEl.innerHTML = '<div class="error-msg">请输入试听文本（preview_text）</div>';
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>生成中…';
    resultsEl.innerHTML = '<p style="font-size:0.85rem;color:#718096;margin-top:10px"><span class="spinner"></span>生成中…</p>';

    try {
      const payload = { prompt, preview_text: previewText, confirm_cost: false };
      if (voiceId) payload.voice_id = voiceId;

      const resp = await guardedJsonFetch(
        '/api/voice/design/create?provider=' + encodeURIComponent(provider),
        payload,
        { provider, operation: 'voice_design', highRisk: true }
      );

      if (!resp.ok) {
        const err = await parseApiError(resp);
        if (err.code === 'RESOURCE_LIMIT_EXCEEDED') {
          resultsEl.innerHTML = renderApiError(err);
        } else if (err.code === 'VALIDATION_ERROR') {
          resultsEl.innerHTML = renderValidationError(err.message);
        } else {
          resultsEl.innerHTML = '<div class="error-msg">设计失败：' + esc(friendlyErrorMessage(formatApiError(err))) + '</div>';
        }
        btn.disabled = false;
        btn.innerHTML = '生成设计';
        return;
      }

      const data = await resp.json();

      let html = '<div class="success-msg">' +
        '设计成功：voice_id=<code>' + esc(data.voice_id) + '</code>，' + (data.message || '') +
      '</div>';

      if (data.trial_audio_hex) {
        const trialBlobUrl = window.hexToBlobUrl(data.trial_audio_hex);
        var _designDur = (data.trial_audio_duration_ms || data.duration_ms) ? ((data.trial_audio_duration_ms || data.duration_ms) / 1000).toFixed(1) + 's' : '';
        html += '<div style="margin-top:10px">' +
          (_designDur ? '<div style="font-size:0.78rem;color:#718096;margin-bottom:4px">设计试听' + (_designDur ? ' · 时长 ' + _designDur : '') + '</div>' : '') +
          (trialBlobUrl
            ? '<audio class="audio-player" controls preload="metadata"><source src="' + trialBlobUrl + '" type="audio/mpeg">您的浏览器不支持音频播放</audio>'
            : '<div class="hex-player">trial_audio_hex 解析失败，无法播放。</div>') +
        '</div>';
      } else if (data.trial_audio_url) {
        var _designDur2 = (data.trial_audio_duration_ms || data.duration_ms) ? ((data.trial_audio_duration_ms || data.duration_ms) / 1000).toFixed(1) + 's' : '';
        html += '<div style="margin-top:10px">' +
          (_designDur2 ? '<div style="font-size:0.78rem;color:#718096;margin-bottom:4px">设计试听' + (_designDur2 ? ' · 时长 ' + _designDur2 : '') + '</div>' : '') +
          '<audio class="audio-player" controls preload="metadata">' +
            '<source src="' + esc(data.trial_audio_url) + '" type="audio/mpeg">' +
            '您的浏览器不支持音频播放</audio>' +
        '</div>';
      }

      // Quick bind panel
      html += '<div style="margin-top:12px;padding:12px;background:#f7fafc;border-radius:8px">' +
        '<div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速绑定到人设</div>' +
        '<div style="display:flex;flex-direction:column;gap:8px">' +
          '<div id="designProfileWrap" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"></div>' +
          '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
            '<select id="designBindModel" style="min-width:160px;padding:6px;border:1px solid #e2e8f0;border-radius:6px">' +
              (window.getModelOptionsHtml ? window.getModelOptionsHtml(provider) : '<option value="speech-2.8-hd" selected>speech-2.8-hd</option>') +
            '</select>' +
            '<button class="btn-primary" id="designBindBtn" style="margin:0;white-space:nowrap">绑定</button>' +
          '</div>' +
        '</div>' +
        '<div id="designBindResult" style="margin-top:6px;font-size:0.82rem"></div>' +
      '</div>';

      // Quick preview block
      html += '<div style="margin-top:12px;padding:12px;background:#f0fff4;border-radius:8px">' +
        '<div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速试听</div>' +
        '<div style="display:flex;gap:8px;align-items:center">' +
          '<input type="text" id="designQuickText" placeholder="输入试听文本" value="你好，这是一段测试语音。"' +
            ' style="flex:1;padding:6px;border:1px solid #e2e8f0;border-radius:6px;font-size:0.85rem">' +
          '<button class="btn-primary" id="designQuickBtn" style="margin:0;white-space:nowrap">试听</button>' +
        '</div>' +
        '<div id="designQuickResult" style="margin-top:8px"></div>' +
      '</div>';

      resultsEl.innerHTML = html;
      window.handleListVoices(true).catch(function () {});

      setTimeout(function () {
        var profileWrap = document.getElementById('designProfileWrap');
        var sel = document.createElement('select');
        sel.id = 'designBindProfile';
        sel.style.cssText = 'min-width:180px;max-width:100%;padding:6px;border:1px solid #e2e8f0;border-radius:6px';
        profileWrap.appendChild(sel);
        window.populateProfileSelect(sel);
        window.renderInlineCreateProfile(profileWrap, sel, 'design');
        if (window.refreshModelSelectForProvider) {
          window.refreshModelSelectForProvider('designBindModel', provider);
        }
        var bindBtn = document.getElementById('designBindBtn');
        if (bindBtn) {
          bindBtn.onclick = async function () {
            var profileId = document.getElementById('designBindProfile').value;
            var model = document.getElementById('designBindModel').value;
            if (!profileId) { alert('请选择人设'); return; }
            var resultDiv = document.getElementById('designBindResult');
            try {
              await window.bindVoiceToProfile(data.voice_id, provider, profileId, model);
              resultDiv.innerHTML = '<div style="background:#f0fff4;border:1px solid #c6f6d5;border-radius:6px;padding:8px 10px;font-size:0.78rem;color:#2f855a">✓ 绑定成功。可回到创作工作台，选择该声音人设进行生成。 <button type="button" id="designBindGoCreateBtn" style="margin-left:8px;font-size:0.75rem;padding:2px 8px;cursor:pointer">去创作</button></div>';
              var goBtn = document.getElementById('designBindGoCreateBtn');
              if (goBtn) {
                goBtn.addEventListener('click', function () {
                  var wsBtn = document.querySelector('.tab-btn[data-tab="workspace"]');
                  if (wsBtn) wsBtn.click();
                });
              }
              await window.refreshVoiceBindStatus(data.voice_id);
            } catch (e) {
              resultDiv.innerHTML = '<span style="color:#e53e3e">绑定失败: ' + esc(e.message) + '</span>';
            }
          };
        }
        var quickBtn = document.getElementById('designQuickBtn');
        if (quickBtn) {
          quickBtn.onclick = async function () {
            var text = document.getElementById('designQuickText').value.trim();
            if (!text) return;
            var resultDiv = document.getElementById('designQuickResult');
            var profileId = document.getElementById('designBindProfile').value;
            if (!profileId) {
              resultDiv.innerHTML = '<span style="color:#ed8936;font-size:0.82rem">请先在上方绑定到人设后再试听</span>';
              return;
            }
            resultDiv.innerHTML = '<span class="spinner"></span> 生成中…';
            try {
              // P16-CANCEL-FIX1: confirm before fetch — inline pattern matching handleGenerate
              if (window.isRealCostProvider && window.isRealCostProvider(provider) && !confirm('真实试听会调用云端 TTS，可能产生字符费用，是否继续？')) {
                resultDiv.innerHTML = '';
                return;
              }
              var resp = await fetch('/api/voice/render', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, profile_id: profileId, provider: provider, audio_format: audioFormat, confirm_cost: window.isRealCostProvider ? window.isRealCostProvider(provider) : false }),
              });
              var rd = await resp.json();
              if (!resp.ok) {
                resultDiv.innerHTML = '<span style="color:#e53e3e;font-size:0.82rem">试听失败: ' + esc(rd.error && rd.error.message ? rd.error.message : JSON.stringify(rd)) + '</span>';
                return;
              }
              if (rd.audio_asset && rd.audio_asset.url) {
                var _qDurD = rd.audio_asset.duration_ms ? (rd.audio_asset.duration_ms / 1000).toFixed(1) + 's' : '';
                resultDiv.innerHTML = (_qDurD ? '<div style="font-size:0.78rem;color:#718096;margin-bottom:4px">快速试听' + (_qDurD ? ' · 时长 ' + _qDurD : '') + '</div>' : '') +
                  '<audio class="audio-player" controls autoplay preload="metadata">' +
                  '<source src="' + esc(rd.audio_asset.url) + '" type="' + (window.getAudioMediaType ? window.getAudioMediaType(rd.audio_asset.format) : 'audio/mpeg') + '">' +
                '</audio>';
              } else {
                resultDiv.innerHTML = '<span style="color:#718096;font-size:0.82rem">未返回音频数据</span>';
              }
            } catch (e) {
              resultDiv.innerHTML = '<span style="color:#e53e3e;font-size:0.82rem">网络错误: ' + esc(e.message) + '</span>';
            }
          };
        }
      }, 0);

    } catch (e) {
      if (e.message === 'USER_CANCELLED') {
        resultsEl.innerHTML = '';
      } else {
        resultsEl.innerHTML = '<div class="error-msg">网络错误：' + esc(e.message) + '</div>';
      }
    } finally {
      btn.disabled = false;
      btn.innerHTML = '生成设计';
    }
  };
})();
