/**
 * voice_import.js
 *
 * Phase 1: Extract voice import functions from index.html.
 *
 * Responsibilities:
 * - Remote voice import entry (handleImportRemoteVoice)
 * - Handles both clone import and design import via source parameter
 * - Calls /api/voice/provider-voices/import
 * - Renders import success/error results
 * - Renders quick bind panel
 * - Calls shared profile/binding/voice-list helpers
 *
 * Uses window helpers from index.html (G3 exports):
 * - window.loadProfiles
 * - window.populateProfileSelect
 * - window.renderInlineCreateProfile
 * - window.bindVoiceToProfile
 * - window.refreshVoiceBindStatus
 * - window.handleListVoices
 *
 * Uses shared helpers from index.html:
 * - guardedJsonFetch, parseApiError, formatApiError
 * - friendlyErrorMessage, renderApiError, renderValidationError
 * - esc
 */

(function () {
  // Import Tab: remote voice import

  window.handleImportRemoteVoice = async function (source) {
    const isClone = source === 'clone';
    const prefix = isClone ? 'importClone' : 'importDesign';
    const provider = document.getElementById(prefix + 'Provider').value;
    const voiceId = document.getElementById(prefix + 'VoiceId').value.trim();
    const name = document.getElementById(prefix + 'Name').value.trim() || null;
    const model = document.getElementById(prefix + 'Model').value;
    const audioFormat = window.getDefaultAudioFormat ? window.getDefaultAudioFormat(provider) : 'mp3';
    const previewText = document.getElementById(prefix + 'PreviewText').value.trim();
    const verify = document.getElementById(prefix + 'Verify').checked;
    const resultsEl = document.getElementById(prefix + 'Result');
    const btn = document.getElementById(prefix + 'Btn');

    if (!voiceId) {
      resultsEl.innerHTML = '<div class="error-msg">请输入 voice_id</div>';
      return;
    }
    if (!previewText) {
      resultsEl.innerHTML = '<div class="error-msg">请输入试听文本</div>';
      return;
    }

    await window.loadProfiles();

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>导入中…';
    resultsEl.innerHTML = '<p style="font-size:0.85rem;color:#718096;margin-top:10px"><span class="spinner"></span>导入中…</p>';

    try {
      const payload = {
        provider,
        provider_voice_id: voiceId,
        voice_type: isClone ? 'voice_cloning' : 'voice_generation',
        verify,
        model,
        audio_format: audioFormat,
        preview_text: previewText,
        confirm_cost: false,
      };
      if (name) payload.name = name;
      if (!verify) {
        payload.description = isClone ? '手动导入的克隆音色' : '手动导入的设计音色';
      }

      const resp = await guardedJsonFetch(
        '/api/voice/provider-voices/import',
        payload,
        { provider, operation: 'provider_voice_import_verify', highRisk: true }
      );

      if (!resp.ok) {
        const err = await parseApiError(resp);
        if (err.code === 'VALIDATION_ERROR') {
          resultsEl.innerHTML = renderValidationError(err.message);
        } else {
          resultsEl.innerHTML = '<div class="error-msg">导入失败：' + esc(friendlyErrorMessage(formatApiError(err))) + '</div>';
        }
        btn.disabled = false;
        btn.innerHTML = '验证并导入';
        return;
      }
      const data = await resp.json();

      let html = '<div class="success-msg">' +
        '导入成功：voice_id=<code>' + esc(data.provider_voice_id) + '</code>，voice_type=' + esc(data.voice_type) + '，status=' + esc(data.status) +
      '</div>';

      if (data.audio_asset && data.audio_asset.url) {
        var _dur = data.audio_asset.duration_ms ? (data.audio_asset.duration_ms / 1000).toFixed(1) + 's' : '';
        html += '<div style="margin-top:10px">' +
          (_dur ? '<div style="font-size:0.78rem;color:#718096;margin-bottom:4px">导入试听' + (_dur ? ' · 时长 ' + _dur : '') + '</div>' : '') +
          '<audio class="audio-player" controls preload="metadata">' +
            '<source src="' + esc(data.audio_asset.url) + '" type="' + (window.getAudioMediaType ? window.getAudioMediaType(data.audio_asset.format) : 'audio/mpeg') + '">' +
            '您的浏览器不支持音频播放</audio>' +
        '</div>';
      }

      if (!verify) {
        html += '<div style="margin-top:8px;font-size:0.80rem;color:#c53030">未验证导入：建议仅在你确认该 voice_id 可用时使用。</div>';
      }

      // Quick bind panel
      html += '<div style="margin-top:12px;padding:12px;background:#f7fafc;border-radius:8px">' +
        '<div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速绑定到人设</div>' +
        '<div style="display:flex;flex-direction:column;gap:8px">' +
          '<div id="importProfileWrap" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"></div>' +
          '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
            '<select id="importBindModel" style="min-width:160px;padding:6px;border:1px solid #e2e8f0;border-radius:6px">' +
              (window.getModelOptionsHtml ? window.getModelOptionsHtml(provider) : '<option value="speech-2.8-hd" selected>speech-2.8-hd</option>') +
            '</select>' +
            '<button class="btn-primary" id="importBindBtn" style="margin:0;white-space:nowrap">绑定</button>' +
          '</div>' +
        '</div>' +
        '<div id="importBindResult" style="margin-top:6px;font-size:0.82rem"></div>' +
      '</div>';

      // Quick preview block
      html += '<div style="margin-top:12px;padding:12px;background:#f0fff4;border-radius:8px">' +
        '<div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速试听</div>' +
        '<div style="display:flex;gap:8px;align-items:center">' +
          '<input type="text" id="importQuickText" placeholder="输入试听文本" value="你好，这是一段测试语音。"' +
            ' style="flex:1;padding:6px;border:1px solid #e2e8f0;border-radius:6px;font-size:0.85rem">' +
          '<button class="btn-primary" id="importQuickBtn" style="margin:0;white-space:nowrap">试听</button>' +
        '</div>' +
        '<div id="importQuickResult" style="margin-top:8px"></div>' +
      '</div>';

      resultsEl.innerHTML = html;

      setTimeout(function () {
        var profileWrap = document.getElementById('importProfileWrap');
        var sel = document.createElement('select');
        sel.id = 'importBindProfile';
        sel.style.cssText = 'min-width:180px;max-width:100%;padding:6px;border:1px solid #e2e8f0;border-radius:6px';
        profileWrap.appendChild(sel);
        window.populateProfileSelect(sel);
        window.renderInlineCreateProfile(profileWrap, sel, 'import');
        if (window.refreshModelSelectForProvider) {
          window.refreshModelSelectForProvider('importBindModel', provider);
        }
        var bindBtn = document.getElementById('importBindBtn');
        if (bindBtn) {
          bindBtn.onclick = async function () {
            var profileId = document.getElementById('importBindProfile').value;
            var bindModel = document.getElementById('importBindModel').value;
            if (!profileId) { alert('请选择人设'); return; }
            var resultDiv = document.getElementById('importBindResult');
            try {
              await window.bindVoiceToProfile(data.provider_voice_id, provider, profileId, bindModel);
              resultDiv.innerHTML = '<div style="background:#f0fff4;border:1px solid #c6f6d5;border-radius:6px;padding:8px 10px;font-size:0.78rem;color:#2f855a">✓ 绑定成功。可回到创作工作台，选择该声音人设进行生成。 <button type="button" id="importBindGoCreateBtn" style="margin-left:8px;font-size:0.75rem;padding:2px 8px;cursor:pointer">去创作</button></div>';
              var goBtn = document.getElementById('importBindGoCreateBtn');
              if (goBtn) {
                goBtn.addEventListener('click', function () {
                  var wsBtn = document.querySelector('.tab-btn[data-tab="workspace"]');
                  if (wsBtn) wsBtn.click();
                });
              }
              await window.refreshVoiceBindStatus(data.provider_voice_id);
            } catch (e) {
              resultDiv.innerHTML = '<span style="color:#e53e3e">绑定失败: ' + esc(e.message) + '</span>';
            }
          };
        }
        var quickBtn = document.getElementById('importQuickBtn');
        if (quickBtn) {
          quickBtn.addEventListener('click', function () {
            var text = document.getElementById('importQuickText').value.trim();
            if (!text) return;
            var resultDiv = document.getElementById('importQuickResult');
            var profileId = document.getElementById('importBindProfile').value;
            if (!profileId) {
              resultDiv.innerHTML = '<span style="color:#ed8936;font-size:0.82rem">请先在上方绑定到人设后再试听</span>';
              return;
            }
            resultDiv.innerHTML = '<span class="spinner"></span> 生成中…';
            // P16-CANCEL-FIX1: confirm before fetch — inline pattern matching handleGenerate
            if (window.isRealCostProvider && window.isRealCostProvider(provider) && !confirm('真实试听会调用云端 TTS，可能产生字符费用，是否继续？')) {
              resultDiv.innerHTML = '';
              return;
            }
            fetch('/api/voice/render', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: text, profile_id: profileId, provider: provider, audio_format: audioFormat, confirm_cost: window.isRealCostProvider ? window.isRealCostProvider(provider) : false }),
            }).then(function (r) {
              return r.json().then(function (rd) {
                if (!r.ok) {
                  resultDiv.innerHTML = '<span style="color:#e53e3e;font-size:0.82rem">试听失败: ' + esc(rd.error && rd.error.message ? rd.error.message : JSON.stringify(rd)) + '</span>';
                  return;
                }
                if (rd.audio_asset && rd.audio_asset.url) {
                  var _dur = rd.audio_asset.duration_ms ? (rd.audio_asset.duration_ms / 1000).toFixed(1) + 's' : '';
                  resultDiv.innerHTML = (_dur ? '<div style="font-size:0.78rem;color:#718096;margin-bottom:4px">快速试听' + (_dur ? ' · 时长 ' + _dur : '') + '</div>' : '') +
                    '<audio class="audio-player" controls autoplay preload="metadata">' +
                    '<source src="' + esc(rd.audio_asset.url) + '" type="' + (window.getAudioMediaType ? window.getAudioMediaType(rd.audio_asset.format) : 'audio/mpeg') + '">' +
                  '</audio>';
                } else {
                  resultDiv.innerHTML = '<span style="color:#718096;font-size:0.82rem">未返回音频数据</span>';
                }
              });
            }).catch(function (e) {
              resultDiv.innerHTML = '<span style="color:#e53e3e;font-size:0.82rem">网络错误: ' + esc(e.message) + '</span>';
            });
          });
        }
      }, 0);

      window.handleListVoices(true).catch(function () {});

    } catch (e) {
      if (e.message === 'USER_CANCELLED') {
        resultsEl.innerHTML = '';
      } else {
        resultsEl.innerHTML = '<div class="error-msg">导入失败：' + esc(e.message) + '</div>';
      }
    } finally {
      btn.disabled = false;
      btn.innerHTML = '验证并导入';
    }
  };
})();
