(function () {
  'use strict';

  // ── state on window for E2E test compatibility ─────────────────────
  window._providerCapabilities = window._providerCapabilities || null;
  window._providerCapabilitiesByName = window._providerCapabilitiesByName || {};
  window._capabilitiesLoaded = window._capabilitiesLoaded || false;
  window._capabilitiesLoadFailed = window._capabilitiesLoadFailed || false;
  window._capabilitiesLoadAttempted = window._capabilitiesLoadAttempted || false;
  window._capabilitiesFailureNotified = window._capabilitiesFailureNotified || false;

  // ── local esc helper (duplicates index.html's esc() logic) ────────────
  function capEsc(s) {
    if (s == null) return '';
    var d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  // ── capability loading ───────────────────────────────────────────────

  window.loadProviderCapabilities = async function (force) {
    if (force === undefined) force = false;
    if (window._capabilitiesLoadAttempted && !force) return;
    window._capabilitiesLoadAttempted = true;
    try {
      var resp = await fetch('/api/voice/capabilities');
      if (!resp.ok) throw new Error('capabilities load failed');
      var data = await resp.json();

      var providers = Array.isArray(data.providers) ? data.providers : [];
      window._providerCapabilities = providers;
      window._providerCapabilitiesByName = {};
      providers.forEach(function (cap) {
        if (cap && cap.provider) {
          window._providerCapabilitiesByName[cap.provider] = cap;
        }
      });

      window._capabilitiesLoaded = true;
      window._capabilitiesLoadFailed = false;
      window._capabilitiesFailureNotified = false;

      [
        'providerSelect',
        'batchProvider',
        'batchScriptProvider',
        'voiceProvider',
        'cloneProvider',
        'designProvider',
        'newBindingProvider',
        'importCloneProvider',
        'importDesignProvider'
      ].forEach(window.updateProviderSelectOptions);

      window.applyAllProviderCapabilities();
      window.dispatchEvent(new CustomEvent('provider-capabilities-applied'));
    } catch (err) {
      console.warn('loadProviderCapabilities failed', err);
      window._capabilitiesLoaded = false;
      window._capabilitiesLoadFailed = true;
      if (!window._capabilitiesFailureNotified && typeof window.showToast === 'function') {
        window.showToast('Provider 能力加载失败，已使用默认前端配置。', 'warning');
        window._capabilitiesFailureNotified = true;
      }
    }
  };

  // ── capability lookup ────────────────────────────────────────────────

  function getProviderCapability(provider) {
    if (!provider) return null;
    return window._providerCapabilitiesByName[provider] || null;
  }

  window.getProviderCapability = getProviderCapability;

  window.ensureProviderCapability = async function (provider) {
    if (!provider) return null;
    var existing = getProviderCapability(provider);
    if (existing) return existing;

    try {
      var resp = await fetch('/api/voice/capabilities?provider=' + encodeURIComponent(provider));
      if (!resp.ok) throw new Error('capability load failed');
      var cap = await resp.json();
      if (cap && cap.provider) {
        window._providerCapabilitiesByName[cap.provider] = cap;
        if (!Array.isArray(window._providerCapabilities)) {
          window._providerCapabilities = [];
        }
        var replaced = false;
        window._providerCapabilities = window._providerCapabilities.map(function (item) {
          if (item && item.provider === cap.provider) {
            replaced = true;
            return cap;
          }
          return item;
        });
        if (!replaced) {
          window._providerCapabilities.push(cap);
        }
        window.dispatchEvent(new CustomEvent('provider-capabilities-applied'));
        return cap;
      }
    } catch (err) {
      console.warn('ensureProviderCapability failed', provider, err);
    }
    return getProviderCapability(provider);
  };

  // ── helper utilities ──────────────────────────────────────────────────

  function getSelectValue(id, fallback) {
    if (fallback === undefined) fallback = null;
    var el = document.getElementById(id);
    return el ? el.value : fallback;
  }

  function setHintText(id, text, type) {
    if (type === undefined) type = 'muted';
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = text || '';
    el.className = 'capability-hint ' + type;
  }

  function setTextMaxLength(textareaId, maxLength, countId) {
    var el = document.getElementById(textareaId);
    if (!el || !maxLength) return;
    el.maxLength = maxLength;

    if (el.value.length > maxLength) {
      el.value = el.value.slice(0, maxLength);
    }

    if (countId) {
      var countEl = document.getElementById(countId);
      if (countEl) {
        countEl.textContent = el.value.length + ' / ' + maxLength;
      }
    }
  }

  function updateSelectOptions(selectId, allowedValues, labelMap) {
    var el = document.getElementById(selectId);
    if (!el || !Array.isArray(allowedValues) || allowedValues.length === 0) return;

    var current = el.value;
    el.innerHTML = allowedValues.map(function (v) {
      var label = (labelMap && labelMap[v]) ? labelMap[v] : v.toUpperCase();
      return '<option value="' + capEsc(v) + '">' + capEsc(label) + '</option>';
    }).join('');

    if (allowedValues.indexOf(current) !== -1) {
      el.value = current;
    } else {
      el.value = allowedValues[0];
    }
  }

  function setNumberRange(inputId, range, label) {
    var el = document.getElementById(inputId);
    if (!el || !range) return;
    el.min = range.min;
    el.max = range.max;
    el.placeholder = range.min + '-' + range.max;
    el.title = (label || '') + '范围：' + range.min + '-' + range.max;

    if (el.value !== '') {
      var num = Number(el.value);
      if (Number.isFinite(num)) {
        if (num < Number(range.min)) el.value = range.min;
        if (num > Number(range.max)) el.value = range.max;
      }
    }
  }

  function getTtsModels(provider) {
    var cap = getProviderCapability(provider);
    if (cap && cap.tts && cap.tts.models && cap.tts.models.length > 0) {
      return cap.tts.models;
    }
    if (cap && cap.default_model) return [cap.default_model];
    return [];
  }

  function getDefaultTtsModel(provider) {
    var cap = getProviderCapability(provider);
    if (cap && cap.tts && cap.tts.models && cap.tts.models.length > 0) {
      return cap.tts.default_model || cap.default_model || cap.tts.models[0];
    }
    return getTtsModels(provider)[0];
  }

  function getAudioFormats(provider) {
    var cap = getProviderCapability(provider);
    if (cap && cap.tts && cap.tts.audio_formats && cap.tts.audio_formats.length > 0) {
      return cap.tts.audio_formats;
    }
    return ['wav'];
  }

  function getDefaultAudioFormat(provider) {
    return getAudioFormats(provider)[0];
  }

  function getAudioMediaType(format) {
    if (format === 'wav') return 'audio/wav';
    if (format === 'flac') return 'audio/flac';
    return 'audio/mpeg';
  }

  function renderModelOptionsHtml(provider, selected) {
    var models = getTtsModels(provider);
    var def = selected || getDefaultTtsModel(provider);
    return models.map(function (m) {
      var sel = (m === def) ? ' selected' : '';
      return '<option value="' + capEsc(m) + '"' + sel + '>' + capEsc(m) + '</option>';
    }).join('');
  }

  function refreshModelSelectForProvider(selectId, provider, selected) {
    var el = document.getElementById(selectId);
    if (!el) return;
    el.innerHTML = renderModelOptionsHtml(provider, selected);
  }

  window.getTtsModels = getTtsModels;
  window.getDefaultTtsModel = getDefaultTtsModel;
  window.getAudioFormats = getAudioFormats;
  window.getDefaultAudioFormat = getDefaultAudioFormat;
  window.getAudioMediaType = getAudioMediaType;
  window.renderModelOptionsHtml = renderModelOptionsHtml;
  window.refreshModelSelectForProvider = refreshModelSelectForProvider;
  window.getModelOptionsHtml = function (provider) {
    return renderModelOptionsHtml(provider);
  };

  window.setControlDisabled = function (id, disabled, title) {
    if (title === undefined) title = '';
    var el = document.getElementById(id);
    if (!el) return;
    el.disabled = !!disabled;
    el.title = title || '';
  };

  window.updateProviderSelectOptions = function (selectId) {
    var el = document.getElementById(selectId);
    if (!el || !window._providerCapabilities) return;
    var current = el.value;

    el.innerHTML = window._providerCapabilities
      .filter(function (cap) { return cap.enabled; })
      .map(function (cap) {
        return '<option value="' + capEsc(cap.provider) + '">' + capEsc(cap.display_name || cap.provider) + '</option>';
      }).join('');

    var currentCap = window._providerCapabilitiesByName[current];
    if (currentCap && currentCap.enabled) {
      el.value = current;
    }
  };

  // ── apply capabilities per tab ────────────────────────────────────────

  function applyWorkspaceCapability() {
    var provider = getSelectValue('providerSelect', 'mock');
    var cap = getProviderCapability(provider);
    if (!cap || !cap.tts) return;

    var tts = cap.tts;

    setTextMaxLength('textInput', tts.max_text_chars || 10000, 'charCount');

    updateSelectOptions('audioFormat', tts.audio_formats || ['mp3'], {
      mp3: 'MP3',
      wav: 'WAV',
      flac: 'FLAC'
    });

    setNumberRange('paramSpeed', tts.speed, '语速');
    setNumberRange('paramVol', tts.vol, '音量');
    setNumberRange('paramPitch', tts.pitch, '音调');

    window.setControlDisabled(
      'needSubtitle',
      !tts.supports_subtitle,
      tts.supports_subtitle ? '' : '当前 Provider 不支持字幕生成'
    );
    if (!tts.supports_subtitle) {
      var sub = document.getElementById('needSubtitle');
      if (sub) sub.checked = false;
    }

    window.setControlDisabled(
      'paramEmotion',
      !tts.supports_emotion,
      tts.supports_emotion ? '' : '当前 Provider 不支持情绪参数'
    );
    if (!tts.supports_emotion) {
      var emo = document.getElementById('paramEmotion');
      if (emo) emo.value = '';
    }

    document.querySelectorAll('input[name="genMode"]').forEach(function (radio) {
      if (radio.value === 'stream') {
        radio.disabled = !tts.supports_streaming;
        radio.title = tts.supports_streaming ? '' : '当前 Provider 不支持流式生成';
        if (!tts.supports_streaming && radio.checked) {
          var single = document.querySelector('input[name="genMode"][value="single"]');
          if (single) single.checked = true;
        }
      }
      if (radio.value === 'async') {
        radio.disabled = !tts.supports_async;
        radio.title = tts.supports_async ? '' : '当前 Provider 不支持异步生成';
        if (!tts.supports_async && radio.checked) {
          var single = document.querySelector('input[name="genMode"][value="single"]');
          if (single) single.checked = true;
        }
      }
    });
  }

  function applyLongtextCapability() {
    var provider = getSelectValue('batchProvider', getSelectValue('providerSelect', 'mock'));
    var cap = getProviderCapability(provider);
    if (!cap || !cap.batch) return;

    var batch = cap.batch;
    var tts = cap.tts || {};

    if (!batch.supported) {
      window.setControlDisabled('batchLongtextSubmit', true, '当前 Provider 不支持长文本批量生成');
      setHintText('batchCapabilityHint', '当前 Provider 不支持长文本批量生成。', 'error');
      return;
    }
    window.setControlDisabled('batchLongtextSubmit', false, '');
    setHintText('batchCapabilityHint', '', '');

    setTextMaxLength('batchText', batch.max_text_chars || 50000);

    updateSelectOptions('batchStrategy', batch.segment_strategies || ['auto', 'paragraph', 'sentence', 'line'], {
      auto: '自动（按段落合并，推荐长文）',
      paragraph: '按空行分段',
      sentence: '按句子分段',
      line: '每行一段'
    });

    if (batch.max_segment_chars) setNumberRange('batchMaxChars', batch.max_segment_chars, '每段最大字数');
    if (batch.silence_between_ms) setNumberRange('batchSilence', batch.silence_between_ms, '段间静音');

    updateSelectOptions('batchOutputFormat', tts.audio_formats || ['mp3'], {
      mp3: 'MP3',
      wav: 'WAV',
      flac: 'FLAC'
    });

    var supportsSubtitle = !!(batch.supports_merge_subtitle && tts.supports_subtitle);
    window.setControlDisabled(
      'batchNeedSubtitle',
      !supportsSubtitle,
      supportsSubtitle ? '' : '当前 Provider 不支持批量字幕'
    );
    var sub = document.getElementById('batchNeedSubtitle');
    if (sub && !supportsSubtitle) sub.checked = false;
  }

  function applyScriptCapability() {
    var provider = getSelectValue('batchScriptProvider', getSelectValue('providerSelect', 'mock'));
    var cap = getProviderCapability(provider);
    if (!cap || !cap.script) return;

    var script = cap.script;
    var tts = cap.tts || {};

    if (!script.supported) {
      window.setControlDisabled('batchScriptSubmit', true, '当前 Provider 不支持剧本批量生成');
      setHintText('scriptCapabilityHint', '当前 Provider 不支持剧本批量生成。', 'error');
      return;
    }
    window.setControlDisabled('batchScriptSubmit', false, '');
    setHintText('scriptCapabilityHint', '', '');

    // MAX_SCRIPT_LINES is a var on window (changed from let in index.html)
    if (typeof window.MAX_SCRIPT_LINES !== 'undefined') {
      window.MAX_SCRIPT_LINES = script.max_segments || 200;
    }

    if (typeof window.updateScriptLineLimitState === 'function') {
      window.updateScriptLineLimitState();
    }

    if (script.silence_between_ms) setNumberRange('batchScriptSilence', script.silence_between_ms, '段间静音');

    updateSelectOptions('batchScriptOutputFormat', tts.audio_formats || ['mp3'], {
      mp3: 'MP3',
      wav: 'WAV',
      flac: 'FLAC'
    });

    var supportsSubtitle = !!(script.supports_merge_subtitle && tts.supports_subtitle);
    window.setControlDisabled(
      'batchScriptNeedSubtitle',
      !supportsSubtitle,
      supportsSubtitle ? '' : '当前 Provider 不支持剧本字幕'
    );
    var sub = document.getElementById('batchScriptNeedSubtitle');
    if (sub && !supportsSubtitle) sub.checked = false;
  }

  function applyProviderVoiceCapability() {
    var provider = getSelectValue('voiceProvider', getSelectValue('providerSelect', 'mock'));
    var cap = getProviderCapability(provider);
    if (!cap) return;

    var pv = cap.provider_voices || {};
    var tts = cap.tts || {};

    if (pv.preview_text_max) {
      setTextMaxLength('auditionText', pv.preview_text_max);
    }

    refreshModelSelectForProvider('auditionModel', provider);

    setNumberRange('auditionSpeed', tts.speed, '语速');
    setNumberRange('auditionVol', tts.vol, '音量');
    setNumberRange('auditionPitch', tts.pitch, '音调');

    if (tts.supports_subtitle === false) {
      var subEl = document.getElementById('auditionNeedSubtitle');
      if (subEl) {
        subEl.checked = false;
        subEl.disabled = true;
        subEl.title = '当前 Provider 不支持字幕生成';
      }
    }
  }

  function applyVoiceCloneCapability() {
    var provider = getSelectValue('cloneProvider', getSelectValue('providerSelect', 'mock'));
    var cap = getProviderCapability(provider);
    if (!cap || !cap.voice_clone) return;

    var clone = cap.voice_clone;

    if (!clone.supported) {
      setHintText('cloneCapabilityHint', '当前 Provider 不支持声音克隆。', 'error');
      var btn = document.getElementById('cloneBtn');
      if (btn) btn.disabled = true;
      return;
    }

    var hintEl = document.getElementById('cloneCapabilityHint');
    if (hintEl) {
      hintEl.textContent = '';
      hintEl.className = 'capability-hint';
    }
    var cloneBtn = document.getElementById('cloneBtn');
    if (cloneBtn) cloneBtn.disabled = false;

    if (clone.preview_text_max) {
      setTextMaxLength('clonePreviewText', clone.preview_text_max);
    }

    var cloneModel = document.getElementById('cloneModel');
    if (cloneModel) {
      var models = getTtsModels(provider);
      refreshModelSelectForProvider(
        'cloneModel',
        provider,
        models.indexOf(cloneModel.value) === -1 ? null : cloneModel.value
      );
    }

    if (clone.voice_id) {
      var el = document.getElementById('cloneVoiceId');
      if (el) {
        el.minLength = clone.voice_id.min_length;
        el.maxLength = clone.voice_id.max_length;
        el.pattern = clone.voice_id.pattern;
        el.title = clone.voice_id.hint || '';
      }

      var hint = document.getElementById('cloneVoiceIdHint');
      if (hint && clone.voice_id.hint) {
        hint.textContent = clone.voice_id.hint;
        hint.style.display = '';
      }
    }

    window.setControlDisabled(
      'needNoiseReduction',
      !clone.supports_noise_reduction,
      clone.supports_noise_reduction ? '' : '当前 Provider 不支持降噪'
    );

    window.setControlDisabled(
      'needVolumeNormalization',
      !clone.supports_volume_normalization,
      clone.supports_volume_normalization ? '' : '当前 Provider 不支持音量标准化'
    );

    var fileHint = document.getElementById('cloneFileHint');
    if (fileHint && clone.max_file_size_mb) {
      fileHint.textContent = '音频文件最大 ' + clone.max_file_size_mb + ' MB。';
    }

    if (typeof window.updateCloneBtnState === 'function') {
      window.updateCloneBtnState();
    }
  }

  function applyVoiceDesignCapability() {
    var provider = getSelectValue('designProvider', getSelectValue('providerSelect', 'mock'));
    var cap = getProviderCapability(provider);
    if (!cap || !cap.voice_design) return;

    var design = cap.voice_design;

    if (!design.supported) {
      setHintText('designCapabilityHint', '当前 Provider 不支持声音设计。', 'error');
      var btn = document.getElementById('designBtn');
      if (btn) btn.disabled = true;
      return;
    }

    var hintEl = document.getElementById('designCapabilityHint');
    if (hintEl) {
      hintEl.textContent = '';
      hintEl.className = 'capability-hint';
    }
    var designBtn = document.getElementById('designBtn');
    if (designBtn) designBtn.disabled = false;

    if (design.prompt_max) {
      setTextMaxLength('designPrompt', design.prompt_max);
    }

    if (design.preview_text_max) {
      setTextMaxLength('designPreviewText', design.preview_text_max);
    }

    if (design.voice_id) {
      var el = document.getElementById('designVoiceId');
      if (el) {
        el.minLength = design.voice_id.min_length;
        el.maxLength = design.voice_id.max_length;
        el.pattern = design.voice_id.pattern;
        el.title = design.voice_id.hint || '';
      }
    }
  }

  function applyImportVoiceCapability() {
    ['importClone', 'importDesign'].forEach(function (prefix) {
      var provider = getSelectValue(prefix + 'Provider', getSelectValue('providerSelect', 'mock'));
      var cap = getProviderCapability(provider);
      if (!cap || !cap.provider_voices) return;

      var pv = cap.provider_voices;

      if (pv.preview_text_max) {
        setTextMaxLength(prefix + 'PreviewText', pv.preview_text_max);
      }

      refreshModelSelectForProvider(prefix + 'Model', provider);

      var verify = document.getElementById(prefix + 'Verify');
      if (verify && !pv.supports_import_remote_voice) {
        verify.checked = false;
        verify.disabled = true;
        verify.title = 'current provider does not support remote voice import';
      } else if (verify) {
        verify.disabled = false;
        verify.title = '';
      }
    });


  }
  // ── apply all + bind events ───────────────────────────────────────────

  window.applyAllProviderCapabilities = function () {
    applyWorkspaceCapability();
    applyLongtextCapability();
    applyScriptCapability();
    applyProviderVoiceCapability();
    applyVoiceCloneCapability();
    applyVoiceDesignCapability();
    applyImportVoiceCapability();
  };

  window.bindProviderCapabilityEvents = function () {
    var ids = [
      'providerSelect',
      'batchProvider',
      'batchScriptProvider',
      'voiceProvider',
      'cloneProvider',
      'designProvider',
      'newBindingProvider',
      'importCloneProvider',
      'importDesignProvider'
    ];
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.addEventListener('change', function () {
          window.applyAllProviderCapabilities();
        });
      }
    });
  };

  // also expose getProviderCapability for console debugging
  window.getProviderCapability = getProviderCapability;
})();
