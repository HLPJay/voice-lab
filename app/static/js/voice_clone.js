/**
 * voice_clone.js
 *
 * Phase 1: Extract voice clone functions from index.html.
 *
 * Responsibilities:
 * - Audio file upload (handleUploadAudio)
 * - voice_id auto-generation (handleCloneAutoId)
 * - Clone button state validation (updateCloneBtnState)
 * - Voice clone submission (handleCloneVoice)
 * - Clone result display (success/error HTML)
 *
 * Uses window helpers from index.html / G3:
 * - window.isValidVoiceId
 * - window.populateProfileSelect
 * - window.renderInlineCreateProfile
 * - window.bindVoiceToProfile
 * - window.hexToBlobUrl
 *
 * Uses shared helpers from index.html:
 * - guardedJsonFetch, parseApiError, formatApiError
 * - friendlyErrorMessage, renderApiError, renderValidationError
 * - esc, showToast
 * - loadRuntimeStatus, refreshRuntimeStatusAfterGeneration
 * - window.handleListVoices
 */

(function () {
  // ── Clone Tab: audio upload ──────────────────────────────────────────────

  window.handleUploadAudio = async function () {
    var provider = document.getElementById('cloneProvider').value;
    var purpose = document.getElementById('clonePurpose').value;
    var fileInput = document.getElementById('cloneFile');
    var resultsEl = document.getElementById('uploadResult');
    var btn = document.getElementById('uploadBtn');

    if (!fileInput.files || !fileInput.files[0]) {
      resultsEl.innerHTML = '<div class="error-msg">请先选择音频文件</div>';
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>上传中…';
    resultsEl.innerHTML = '<p style="font-size:0.85rem;color:#718096;margin-top:10px"><span class="spinner"></span>上传中…</p>';

    try {
      var formData = new FormData();
      formData.append('purpose', purpose);
      formData.append('provider', provider);
      formData.append('file', fileInput.files[0]);

      var resp = await fetch('/api/voice/clone/upload', {
        method: 'POST',
        body: formData
      });

      if (!resp.ok) {
        var err = await parseApiError(resp);
        if (err.code === 'RESOURCE_LIMIT_EXCEEDED') {
          resultsEl.innerHTML = renderApiError(err);
        } else {
          resultsEl.innerHTML = '<div class="error-msg">上传失败：' + esc(formatApiError(err)) + '</div>';
        }
        return;
      }

      var data = await resp.json();

      document.getElementById('cloneFileId').value = data.file_id;
      if (typeof updateCloneBtnState === 'function') updateCloneBtnState();

      resultsEl.innerHTML = '<div class="success-msg">' +
        '上传成功，file_id 已填入步骤 2，可继续执行克隆。file_id=<code>' + esc(data.file_id) + '</code>，文件名=' + esc(data.filename) + '，大小=' + data.bytes + ' bytes' +
      '</div>';
    } catch (e) {
      resultsEl.innerHTML = '<div class="error-msg">网络错误：' + esc(e.message) + '</div>';
    } finally {
      btn.disabled = false;
      btn.innerHTML = '上传';
    }
  };

  // ── Clone Tab: auto-generate voice_id ────────────────────────────────────

  window.handleCloneAutoId = function () {
    var now = new Date();
    var pad = function (n, l) { return String(n).padStart(l, '0'); };
    var yyyy = now.getFullYear();
    var mm = pad(now.getMonth() + 1, 2);
    var dd = pad(now.getDate(), 2);
    var hh = pad(now.getHours(), 2);
    var nn = pad(now.getMinutes(), 2);
    var ss = pad(now.getSeconds(), 2);
    var rand = Math.random().toString(36).substring(2, 8);
    var id = 'voice_clone_' + yyyy + mm + dd + hh + nn + ss + '_' + rand;
    document.getElementById('cloneVoiceId').value = id;
    updateCloneBtnState();
  };

  // ── Clone Tab: button state validation ─────────────────────────────────────

  window.updateCloneBtnState = function () {
    var btn = document.getElementById('cloneBtn');
    if (!btn) return;
    var fileId = document.getElementById('cloneFileId').value.trim();
    var voiceId = document.getElementById('cloneVoiceId').value.trim();
    var previewText = document.getElementById('clonePreviewText').value.trim();
    var model = document.getElementById('cloneModel').value.trim();
    var promptFileId = document.getElementById('clonePromptFileId').value.trim();
    var fileIdNum = Number(fileId);
    var promptFileIdNum = Number(promptFileId);
    var voiceIdValid = window.isValidVoiceId(voiceId);
    var fileIdValid = fileId !== '' && Number.isInteger(fileIdNum) && fileIdNum > 0;
    var promptFileIdValid = promptFileId === '' || (Number.isInteger(promptFileIdNum) && promptFileIdNum > 0);
    var disabled = !voiceIdValid || !fileIdValid || (previewText && !model) || !promptFileIdValid;
    btn.disabled = disabled;
    var hint = document.getElementById('cloneBtnHint');
    var voiceIdHint = document.getElementById('cloneVoiceIdHint');
    if (hint) hint.style.display = disabled ? '' : 'none';
    if (voiceIdHint) {
      if (voiceId && !voiceIdValid) {
        voiceIdHint.textContent = 'voice_id 格式不正确：至少 8 位，必须以字母开头，只能包含字母、数字、下划线和短横线，且不能以短横线或下划线结尾。';
        voiceIdHint.style.display = '';
      } else {
        voiceIdHint.textContent = '';
        voiceIdHint.style.display = 'none';
      }
    }
  };

  // ── Clone Tab: submit voice clone ──────────────────────────────────────────

  window.handleCloneVoice = async function () {
    var provider = document.getElementById('cloneProvider').value;
    var voiceId = document.getElementById('cloneVoiceId').value.trim();
    var fileId = document.getElementById('cloneFileId').value.trim();
    var promptFileId = document.getElementById('clonePromptFileId').value.trim();
    var promptText = document.getElementById('clonePromptText').value.trim();
    var previewText = document.getElementById('clonePreviewText').value.trim();
    var model = document.getElementById('cloneModel').value.trim();
    var needNoiseReduction = document.getElementById('needNoiseReduction').checked;
    var needVolumeNormalization = document.getElementById('needVolumeNormalization').checked;
    var resultsEl = document.getElementById('cloneResult');
    var btn = document.getElementById('cloneBtn');

    if (!voiceId) {
      resultsEl.innerHTML = '<div class="error-msg">请输入 voice_id</div>';
      return;
    }
    if (!fileId) {
      resultsEl.innerHTML = '<div class="error-msg">请先上传音频获取 file_id，或手动输入</div>';
      return;
    }
    var fileIdNum = Number(fileId);
    if (!Number.isInteger(fileIdNum) || fileIdNum <= 0) {
      resultsEl.innerHTML = '<div class="error-msg">file_id 必须是大于 0 的整数。</div>';
      updateCloneBtnState();
      return;
    }
    if (previewText && !model) {
      resultsEl.innerHTML = '<div class="error-msg">preview_text 有值时 model 必填。建议使用 speech-2.8-hd。</div>';
      return;
    }
    if (promptFileId) {
      var promptFileIdNum = Number(promptFileId);
      if (!Number.isInteger(promptFileIdNum) || promptFileIdNum <= 0) {
        resultsEl.innerHTML = '<div class="error-msg">prompt_file_id 必须是大于 0 的整数。</div>';
        updateCloneBtnState();
        return;
      }
    }
    if ((promptFileId && !promptText) || (!promptFileId && promptText)) {
      resultsEl.innerHTML = '<div class="error-msg">prompt_file_id 和 prompt_text 必须同时填写，或同时留空。</div>';
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>克隆中…';
    resultsEl.innerHTML = '<p style="font-size:0.85rem;color:#718096;margin-top:10px"><span class="spinner"></span>克隆中…</p>';

    try {
      var payload = {
        voice_id: voiceId,
        file_id: parseInt(fileId),
        need_noise_reduction: needNoiseReduction,
        need_volume_normalization: needVolumeNormalization,
        confirm_cost: false,
      };
      if (promptFileId) payload.prompt_file_id = parseInt(promptFileId);
      if (promptText) payload.prompt_text = promptText;
      if (previewText) payload.preview_text = previewText;
      if (model) payload.model = model;

      var resp = await guardedJsonFetch(
        '/api/voice/clone/create?provider=' + encodeURIComponent(provider),
        payload,
        { provider: provider, operation: 'voice_clone', highRisk: true }
      );

      if (!resp.ok) {
        var err = await parseApiError(resp);
        if (err.code === 'RESOURCE_LIMIT_EXCEEDED') {
          resultsEl.innerHTML = renderApiError(err);
          btn.disabled = false;
          btn.innerHTML = '克隆';
          return;
        }
        if (err.code === 'VALIDATION_ERROR') {
          resultsEl.innerHTML = renderValidationError(err.message);
          btn.disabled = false;
          btn.innerHTML = '克隆';
          return;
        }
        var errMsg = err.message || '';
        if (errMsg.toLowerCase().indexOf('duplicate') !== -1) {
          resultsEl.innerHTML = '<div class="error-msg">voice_id 已存在，请换一个新的 voice_id，或点击「自动生成」。注意：已删除的 voice_id 也不能复用。</div>';
          btn.disabled = false;
          btn.innerHTML = '克隆';
          return;
        }
        resultsEl.innerHTML = '<div class="error-msg">克隆失败：' + esc(friendlyErrorMessage(formatApiError(err))) + '</div>';
        btn.disabled = false;
        btn.innerHTML = '克隆';
        return;
      }

      var data = await resp.json();

      var html = '<div class="success-msg">' +
        '克隆成功：voice_id=<code>' + esc(data.voice_id) + '</code>，' + (data.message || '') +
      '</div>';
      if (data.demo_audio_url) {
        var _cloneDemoDur = (data.demo_audio_duration_ms || data.duration_ms) ? ((data.demo_audio_duration_ms || data.duration_ms) / 1000).toFixed(1) + 's' : '';
        html += '<div style="margin-top:10px">' +
          '<div style="font-size:0.78rem;color:#718096;margin-bottom:4px">克隆试听' + (_cloneDemoDur ? ' · 时长 ' + _cloneDemoDur : '') + '</div>' +
          '<audio class="audio-player" controls preload="metadata">' +
            '<source src="' + esc(data.demo_audio_url) + '" type="audio/mpeg">' +
            '您的浏览器不支持音频播放</audio>' +
        '</div>';
      }

      // Quick bind panel
      html += '<div style="margin-top:12px;padding:12px;background:#f7fafc;border-radius:8px">' +
        '<div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速绑定到人设</div>' +
        '<div style="display:flex;flex-direction:column;gap:8px">' +
          '<div id="cloneProfileWrap" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"></div>' +
          '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
            '<select id="cloneBindModel" style="min-width:160px;padding:6px;border:1px solid #e2e8f0;border-radius:6px">' +
              '<option value="speech-2.8-hd" selected>speech-2.8-hd</option>' +
              '<option value="speech-2.8-turbo">speech-2.8-turbo</option>' +
              '<option value="speech-2.6-hd">speech-2.6-hd</option>' +
              '<option value="speech-2.6-turbo">speech-2.6-turbo</option>' +
            '</select>' +
            '<button class="btn-primary" id="cloneBindBtn" style="margin:0;white-space:nowrap">绑定</button>' +
          '</div>' +
        '</div>' +
        '<div id="cloneBindResult" style="margin-top:6px;font-size:0.82rem"></div>' +
      '</div>';

      // Quick preview block
      html += '<div style="margin-top:12px;padding:12px;background:#f0fff4;border-radius:8px">' +
        '<div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速试听</div>' +
        '<div style="display:flex;gap:8px;align-items:center">' +
          '<input type="text" id="cloneQuickText" placeholder="输入试听文本" value="你好，这是一段测试语音。"' +
            ' style="flex:1;padding:6px;border:1px solid #e2e8f0;border-radius:6px;font-size:0.85rem">' +
          '<button class="btn-primary" id="cloneQuickBtn" style="margin:0;white-space:nowrap">试听</button>' +
        '</div>' +
        '<div id="cloneQuickResult" style="margin-top:8px"></div>' +
      '</div>';

      resultsEl.innerHTML = html;
      if (window.handleListVoices) window.handleListVoices(true).catch(function () {});

      setTimeout(function () {
        var profileWrap = document.getElementById('cloneProfileWrap');
        var sel = document.createElement('select');
        sel.id = 'cloneBindProfile';
        sel.style.cssText = 'min-width:180px;max-width:100%;padding:6px;border:1px solid #e2e8f0;border-radius:6px';
        profileWrap.appendChild(sel);
        if (window.populateProfileSelect) window.populateProfileSelect(sel);
        if (window.renderInlineCreateProfile) window.renderInlineCreateProfile(profileWrap, sel, 'clone');
        var bindBtn = document.getElementById('cloneBindBtn');
        if (bindBtn) {
          bindBtn.onclick = async function () {
            var profileId = document.getElementById('cloneBindProfile').value;
            var bindModel = document.getElementById('cloneBindModel').value;
            if (!profileId) { alert('请选择人设'); return; }
            var resultDiv = document.getElementById('cloneBindResult');
            try {
              if (window.bindVoiceToProfile) {
                await window.bindVoiceToProfile(data.voice_id, provider, profileId, bindModel);
              }
              resultDiv.innerHTML = '<div style="background:#f0fff4;border:1px solid #c6f6d5;border-radius:6px;padding:8px 10px;font-size:0.78rem;color:#2f855a">✓ 绑定成功。可回到创作工作台，选择该声音人设进行生成。 <button type="button" id="cloneBindGoCreateBtn" style="margin-left:8px;font-size:0.75rem;padding:2px 8px;cursor:pointer">去创作</button></div>';
              var goBtn = document.getElementById('cloneBindGoCreateBtn');
              if (goBtn) {
                goBtn.addEventListener('click', function () {
                  var wsBtn = document.querySelector('.tab-btn[data-tab="workspace"]');
                  if (wsBtn) wsBtn.click();
                });
              }
              if (window.refreshVoiceBindStatus) window.refreshVoiceBindStatus(data.voice_id);
            } catch (e) {
              resultDiv.innerHTML = '<span style="color:#e53e3e">绑定失败: ' + esc(e.message) + '</span>';
            }
          };
        }
        var quickBtn = document.getElementById('cloneQuickBtn');
        if (quickBtn) {
          quickBtn.onclick = async function () {
            var text = document.getElementById('cloneQuickText').value.trim();
            if (!text) return;
            var resultDiv = document.getElementById('cloneQuickResult');
            var profileId = document.getElementById('cloneBindProfile').value;
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
              var r = await fetch('/api/voice/render', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text, profile_id: profileId, provider: provider, confirm_cost: window.isRealCostProvider ? window.isRealCostProvider(provider) : false }),
              });
              var rd = await r.json();
              if (!r.ok) {
                resultDiv.innerHTML = '<span style="color:#e53e3e;font-size:0.82rem">试听失败: ' + esc(rd.error && rd.error.message ? rd.error.message : JSON.stringify(rd)) + '</span>';
                return;
              }
              if (rd.audio_asset && rd.audio_asset.url) {
                var _qDur = rd.audio_asset.duration_ms ? (rd.audio_asset.duration_ms / 1000).toFixed(1) + 's' : '';
                resultDiv.innerHTML = (_qDur ? '<div style="font-size:0.78rem;color:#718096;margin-bottom:4px">快速试听' + (_qDur ? ' · 时长 ' + _qDur : '') + '</div>' : '') +
                  '<audio class="audio-player" controls autoplay preload="metadata">' +
                  '<source src="' + esc(rd.audio_asset.url) + '" type="audio/mpeg">' +
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
      btn.innerHTML = '克隆';
    }
  };
})();
