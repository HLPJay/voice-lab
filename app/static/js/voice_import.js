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
            '<source src="' + esc(data.audio_asset.url) + '" type="audio/mpeg">' +
            '您的浏览器不支持音频播放</audio>' +
        '</div>';
      }

      if (!verify) {
        html += '<div style="margin-top:8px;font-size:0.80rem;color:#c53030">未验证导入：建议仅在你确认该 voice_id 可用时使用。</div>';
      }

      // Quick bind panel
      html += '<div style="margin-top:12px;padding:12px;background:#f7fafc;border-radius:8px">' +
        '<div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速绑定到人设</div>' +
        '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
          '<div id="importProfileWrap" style="display:flex;gap:8px;align-items:center;flex:1;min-width:0"></div>' +
          '<select id="importBindModel" style="width:160px;padding:6px;border:1px solid #e2e8f0;border-radius:6px">' +
            '<option value="speech-2.8-hd" selected>speech-2.8-hd</option>' +
            '<option value="speech-2.8-turbo">speech-2.8-turbo</option>' +
            '<option value="speech-2.6-hd">speech-2.6-hd</option>' +
            '<option value="speech-2.6-turbo">speech-2.6-turbo</option>' +
          '</select>' +
          '<button class="btn-primary" id="importBindBtn" style="margin:0;white-space:nowrap">绑定</button>' +
        '</div>' +
        '<div id="importBindResult" style="margin-top:6px;font-size:0.82rem"></div>' +
      '</div>';

      resultsEl.innerHTML = html;

      setTimeout(function () {
        var profileWrap = document.getElementById('importProfileWrap');
        var sel = document.createElement('select');
        sel.id = 'importBindProfile';
        sel.style.cssText = 'flex:1;min-width:0;padding:6px;border:1px solid #e2e8f0;border-radius:6px';
        profileWrap.appendChild(sel);
        window.populateProfileSelect(sel);
        window.renderInlineCreateProfile(profileWrap, sel, 'import');
        var bindBtn = document.getElementById('importBindBtn');
        if (bindBtn) {
          bindBtn.onclick = async function () {
            var profileId = document.getElementById('importBindProfile').value;
            var bindModel = document.getElementById('importBindModel').value;
            if (!profileId) { alert('请选择人设'); return; }
            var resultDiv = document.getElementById('importBindResult');
            try {
              await window.bindVoiceToProfile(data.provider_voice_id, provider, profileId, bindModel);
              resultDiv.innerHTML = '<span style="color:#2f855a">绑定成功!</span>';
              await window.refreshVoiceBindStatus(data.provider_voice_id);
            } catch (e) {
              resultDiv.innerHTML = '<span style="color:#e53e3e">绑定失败: ' + esc(e.message) + '</span>';
            }
          };
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
