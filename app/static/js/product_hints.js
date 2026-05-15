(function() {
  'use strict';

  // Local HTML escaper (same as index.html's esc())
  function phEsc(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Switch to voices tab (shared by all hint buttons)
  function switchToVoicesTab() {
    var voicesBtn = document.querySelector('.tab-btn[data-tab="voices"]');
    if (voicesBtn) voicesBtn.click();
  }

  // B1: workspace voice binding hint
  // Reads profileSelect and providerSelect via DOM to avoid script-local dependency
  window.updateWorkspaceVoiceBindingHint = function() {
    var profileSelect = document.getElementById('profileSelect');
    var providerSelect = document.getElementById('providerSelect');
    if (!profileSelect || !providerSelect) return;
    var profileId = profileSelect.value;
    var provider = providerSelect.value;
    var hintEl = document.getElementById('workspaceVoiceBindingHint');
    if (!hintEl) return;
    if (!profileId) { hintEl.style.display = 'none'; return; }
    hintEl.style.display = '';
    var bindMap = window._voiceBindMap || {};
    var foundVoiceId = null;
    var foundModel = null;
    for (var voiceId in bindMap) {
      var bindings = bindMap[voiceId] || [];
      for (var i = 0; i < bindings.length; i++) {
        var b = bindings[i];
        if (b.profile_id === profileId && b.provider === provider && b.status === 'available') {
          foundVoiceId = voiceId;
          foundModel = b.model || null;
          break;
        }
      }
      if (foundVoiceId) break;
    }
    if (foundVoiceId) {
      hintEl.innerHTML = '<span style="color:#2f855a">当前音色：' + phEsc(foundVoiceId) + (foundModel ? ' (' + phEsc(foundModel) + ')' : '') + '</span>';
    } else {
      hintEl.innerHTML = '<span style="color:#c53030">该人设尚未绑定音色</span> <button type="button" id="workspaceVoiceBindingSwitchBtn" style="font-size:0.75rem;padding:1px 6px;cursor:pointer;margin-left:4px">去选择音色</button>';
      var switchBtn = document.getElementById('workspaceVoiceBindingSwitchBtn');
      if (switchBtn) {
        switchBtn.addEventListener('click', switchToVoicesTab);
      }
    }
  };

  // B3-longtext: voice binding hint for longtext tab
  window.updateBatchVoiceBindingHint = function() {
    var profileEl = document.getElementById('batchProfile');
    var providerEl = document.getElementById('batchProvider');
    if (!profileEl || !providerEl) return;
    var profileId = profileEl.value;
    var provider = providerEl.value;
    var hintEl = document.getElementById('batchVoiceBindingHint');
    if (!hintEl) return;
    if (!profileId) { hintEl.style.display = 'none'; return; }
    hintEl.style.display = '';
    var bindMap = window._voiceBindMap || {};
    var foundVoiceId = null;
    var foundModel = null;
    for (var voiceId in bindMap) {
      var bindings = bindMap[voiceId] || [];
      for (var i = 0; i < bindings.length; i++) {
        var b = bindings[i];
        if (b.profile_id === profileId && b.provider === provider && b.status === 'available') {
          foundVoiceId = voiceId;
          foundModel = b.model || null;
          break;
        }
      }
      if (foundVoiceId) break;
    }
    if (foundVoiceId) {
      hintEl.innerHTML = '<span style="color:#2f855a">当前音色：' + phEsc(foundVoiceId) + (foundModel ? ' (' + phEsc(foundModel) + ')' : '') + '</span>';
    } else {
      hintEl.innerHTML = '<span style="color:#c53030">该人设尚未绑定音色</span> <button type="button" id="batchVoiceBindingSwitchBtn" style="font-size:0.75rem;padding:1px 6px;cursor:pointer;margin-left:4px">去选择音色</button>';
      var switchBtn = document.getElementById('batchVoiceBindingSwitchBtn');
      if (switchBtn) {
        switchBtn.addEventListener('click', switchToVoicesTab);
      }
    }
  };

  // B3-script: per-line voice binding hint for script tab
  window.updateScriptLineVoiceHint = function(id) {
    var profileEl = document.getElementById('scriptProfile_' + id);
    var providerEl = document.getElementById('batchScriptProvider');
    if (!profileEl || !providerEl) return;
    var profileId = profileEl.value;
    var provider = providerEl.value;
    var hintEl = document.getElementById('scriptVoiceHint_' + id);
    if (!hintEl) return;
    if (!profileId) { hintEl.style.display = 'none'; return; }
    hintEl.style.display = '';
    var bindMap = window._voiceBindMap || {};
    var foundVoiceId = null;
    var foundModel = null;
    for (var voiceId in bindMap) {
      var bindings = bindMap[voiceId] || [];
      for (var i = 0; i < bindings.length; i++) {
        var b = bindings[i];
        if (b.profile_id === profileId && b.provider === provider && b.status === 'available') {
          foundVoiceId = voiceId;
          foundModel = b.model || null;
          break;
        }
      }
      if (foundVoiceId) break;
    }
    if (foundVoiceId) {
      hintEl.innerHTML = '<span style="color:#2f855a">当前音色：' + phEsc(foundVoiceId) + (foundModel ? ' (' + phEsc(foundModel) + ')' : '') + '</span>';
    } else {
      hintEl.innerHTML = '<span style="color:#c53030">尚未绑定</span> <button type="button" class="scriptVoiceSwitchBtn" data-line-id="' + id + '" style="font-size:0.7rem;padding:1px 5px;cursor:pointer;margin-left:2px">去选择音色</button>';
      var btn = hintEl.querySelector('.scriptVoiceSwitchBtn');
      if (btn) {
        btn.addEventListener('click', switchToVoicesTab);
      }
    }
  };
})();
