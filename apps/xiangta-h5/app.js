"use strict";

function setBrowserScreenState(screen, mode) {
  if (!window.history || state.navSuppressPush) return;
  const hash = "#" + screen;
  const payload = { xiangtaScreen: screen };
  if (mode === "replace") {
    window.history.replaceState(payload, "", hash);
    return;
  }
  if (window.location.hash === hash && window.history.state?.xiangtaScreen === screen) {
    return;
  }
  window.history.pushState(payload, "", hash);
}

function getBackTargetForScreen(screen) {
  if (screen === "compose") return "home";
  if (screen === "suggest") return "compose";
  if (screen === "voice") return "suggest";
  if (screen === "result") return "voice";
  if (screen === "settings") return "home";
  if (screen === "letterDetail") return "history";
  if (screen === "history") {
    if (
      state.historyReturnTo === "result" &&
      state.ttsResult &&
      state.ttsResult.status === "completed" &&
      state.ttsResult.audioUrl
    ) {
      return "result";
    }
    return "home";
  }
  return null;
}

function initBrowserNavigation() {
  if (state.navHistoryReady) return;
  state.navHistoryReady = true;
  setBrowserScreenState(state.screen || "home", "replace");
  window.addEventListener("popstate", function() {
    const current = state.screen || "home";
    const target = getBackTargetForScreen(current);
    if (!target) return;
    state.navSuppressPush = true;
    try {
      showScreen(target, { skipHistory: true });
    } finally {
      state.navSuppressPush = false;
      setBrowserScreenState(target, "replace");
    }
  });
}

function applyModeUi() {
  const isDev = state.mode === "dev";
  const devPanel = el("devPanel");
  const devTtsSection = el("devTtsSection");
  if (devPanel) devPanel.classList.toggle("hidden", !isDev);
  if (devTtsSection) devTtsSection.classList.toggle("hidden", !isDev);
  document.body.setAttribute("data-mode", state.mode);
}

function showScreen(screen, options = {}) {
  const fromScreen = state.screen;
  cleanupBeforeScreenChange(fromScreen, screen);
  document.querySelectorAll(".screen").forEach((node) => node.classList.remove("active"));
  const target = el("screen" + screen.charAt(0).toUpperCase() + screen.slice(1));
  if (target) target.classList.add("active");
  state.screen = screen;
  if (screen === "history") {
    setupHistoryScreen();
    loadLetters();
  }
  if (screen === "settings") {
    renderSettingsScreen();
  }
  if (screen === "result") {
    if (state.ttsResult && state.ttsResult.status === "completed" && state.ttsResult.audioUrl) {
      renderResultScreen(state.ttsResult);
    } else {
      showToast("还没有生成可查看的信笺");
      showScreen("voice", { skipHistory: true });
      return;
    }
  }
  if (screen === "letterDetail") {
    // Pause history audio to avoid conflict
    const histAudio = el("historyAudio");
    if (histAudio) histAudio.pause();
    // Fallback: if activeLetterDetail exists, re-render it
    if (state.activeLetterDetail) {
      renderLetterDetailScreen(state.activeLetterDetail);
    } else if (state.activeLetterDetailId) {
      // Try to recover from letters array
      const letter = (state.letters || []).find(function(item) {
        return (item.id || item.letterId) === state.activeLetterDetailId;
      });
      if (letter) {
        state.activeLetterDetail = letter;
        renderLetterDetailScreen(letter);
      } else {
        showToast("没有找到这封信笺");
        showScreen("history", { skipHistory: true });
        return;
      }
    } else {
      showToast("没有选择信笺");
      showScreen("history", { skipHistory: true });
      return;
    }
  }
  if (!options.skipHistory && state.navHistoryReady) {
    setBrowserScreenState(screen, "push");
  }
}

function cleanupBeforeScreenChange(fromScreen, toScreen) {
  if (fromScreen === toScreen) return;
  if (fromScreen === "home" && toScreen !== "home") {
    pauseHomeRecentAudio();
  }
  if (fromScreen === "result" && toScreen !== "result") {
    const resultAudio = el("resultAudio");
    if (resultAudio) resultAudio.pause();
  }
  if (fromScreen === "history" && toScreen !== "history") {
    const historyAudio = el("historyAudio");
    if (historyAudio) historyAudio.pause();
    hideHistoryMiniPlayer();
  }
  if (fromScreen === "letterDetail" && toScreen !== "letterDetail") {
    const detailAudio = el("letterDetailAudio");
    if (detailAudio) detailAudio.pause();
  }
  if (fromScreen === "voice" && toScreen !== "voice") {
    state.ttsPollToken += 1;
  }
}

function setBusy(buttonId, busy, label) {
  const button = el(buttonId);
  if (!button) return;
  if (label !== undefined) button.textContent = label;
  button.disabled = busy;
}

function setStatus(message, kind) {
  const node = el("statusBar");
  if (!node) return;
  node.textContent = message;
  node.className = "status-bar status-" + (kind || "idle");
}

/**
 * Normalize an audio URL to a same-origin proxy URL when the original URL is
 * a localhost / 127.0.0.1 / 0.0.0.0 address that is unreachable from mobile.
 *
 * Rules:
 *   "" / null / undefined  → ""
 *   Already a proxy URL    → unchanged
 *   localhost / 127.0.0.1 / 0.0.0.0 (any scheme+port) → /api/xiangta/audio/proxy?url=<encoded>
 *   Everything else        → unchanged
 */
function normalizePlayableAudioUrl(audioUrl) {
  if (!audioUrl) return "";
  if (audioUrl.startsWith("/api/xiangta/audio/proxy")) return audioUrl;
  try {
    const parsed = new URL(audioUrl);
    const host = parsed.hostname;
    if (host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0") {
      return "/api/xiangta/audio/proxy?url=" + encodeURIComponent(audioUrl);
    }
  } catch (_) {
    // Not a parseable absolute URL — return as-is
  }
  return audioUrl;
}

function showToast(message) {
  let toast = el("toastEl");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toastEl";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.remove("hidden");
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => toast.classList.add("hidden"), 2800);
}


/**
 * Render letter body text with line breaks after Chinese punctuation,
 * mirroring the prototype: finalText.replace(/([。，！？])/g, '$1\n').split('\n')
 * Uses safe DOM nodes (no innerHTML with raw text).
 */
function renderLetterBodyLines(node, text) {
  if (!node) return;
  const lines = (text || "")
    .replace(/([。，！？])/g, "$1\n")
    .split("\n")
    .filter(Boolean);
  node.innerHTML = "";
  lines.forEach((line, i) => {
    node.appendChild(document.createTextNode(line));
    if (i < lines.length - 1) {
      node.appendChild(document.createElement("br"));
    }
  });
}

function renderHomeDateLine() {
  const node = el("homeDateLine");
  if (!node) return;
  const now = new Date();
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  const hour = now.getHours();
  const minute = String(now.getMinutes()).padStart(2, "0");
  let period = "深夜";
  if (hour >= 5 && hour < 8) period = "清晨";
  else if (hour < 12) period = "上午";
  else if (hour < 14) period = "中午";
  else if (hour < 18) period = "下午";
  else if (hour < 21) period = "傍晚";
  else if (hour < 24) period = "晚上";
  node.textContent = `${now.getMonth() + 1} / ${now.getDate()} · ${weekdays[now.getDay()]} · ${hour}:${minute}`;
}

function renderStatusPill(providerStatus) {
  const node = el("statusPill");
  if (!node) return;
  if (!providerStatus) {
    node.textContent = "MiniMax · 检查中";
    node.className = "status-pill pill-mute";
    return;
  }
  const kind = providerStatus.kind || "unknown";
  node.className = "status-pill";
  if (kind === "quota" || kind === "degraded" || kind === "not_integrated") node.classList.add("pill-warn");
  if (kind === "error") node.classList.add("pill-error");
  if (kind === "unknown") node.classList.add("pill-mute");
  node.textContent = `MiniMax · ${providerStatus.label || providerStatus.detail || "待接入"}`;
}

function renderProviderStatus(providerStatus) {
  const node = el("providerStatus");
  if (!node || !providerStatus) return;
  node.className = "provider-status";
  if (providerStatus.kind === "ok") node.classList.add("provider-ok");
  if (providerStatus.kind === "quota" || providerStatus.kind === "degraded" || providerStatus.kind === "not_integrated") node.classList.add("provider-warn");
  if (providerStatus.kind === "error") node.classList.add("provider-error");
  node.textContent = `${providerStatus.label || "待接入"} · ${providerStatus.detail || ""}`;
}

function renderStepDots(containerId, active, labels) {
  const node = el(containerId);
  if (!node) return;
  const total = labels.length;
  const pct = total > 1 ? (active / (total - 1)) * 100 : 0;
  let html = '<div class="step-track"><div class="step-track-bg"></div><div class="step-track-fill" style="width:' + pct + '%"></div>';
  for (let i = 0; i < total; i += 1) {
    const left = total > 1 ? (i / (total - 1)) * 100 : 50;
    let cls = "step-dot";
    if (i < active) cls += " done";
    if (i === active) cls += " active";
    html += `<span class="${cls}" style="left:${left}%"></span>`;
  }
  html += '</div><div class="step-labels">';
  labels.forEach((label, index) => {
    const align = index === 0 ? "left" : (index === labels.length - 1 ? "right" : "center");
    html += `<span class="step-label${index <= active ? ' active' : ''}" style="text-align:${align}">${escHtml(label)}</span>`;
  });
  html += "</div>";
  node.innerHTML = html;
}

function detectRisk(text) {
  if (!text) return null;
  const lower = text.toLowerCase();
  const groups = [
    {
      words: ["都是你", "都怪你", "凭什么", "你从来", "你就是"],
      body: "这里有一点点责怪的味道。可以试试把焦点改成“我那一刻其实很难受”。",
    },
    {
      words: ["必须", "不准", "不许", "听我的", "我说了算"],
      body: "这句话听起来有些命令感。换成“我希望……”会更容易被听见。",
    },
    {
      words: ["随便你", "算了", "你猜", "没什么好说"],
      body: "这类表达容易把真正想说的话藏起来。可以试着再具体一点点。",
    },
  ];
  for (const group of groups) {
    if (group.words.some((word) => lower.includes(word.toLowerCase()))) {
      return group.body;
    }
  }
  return null;
}

function renderRiskHint(containerId, text) {
  const node = el(containerId);
  if (!node) return;
  const risk = detectRisk(text);
  if (!risk) {
    node.classList.add("hidden");
    node.innerHTML = "";
    return;
  }
  node.classList.remove("hidden");
  node.innerHTML = `<div>${escHtml(risk)}</div>`;
}


function updateHomeStartButton() {
  const button = el("btnStartCompose");
  if (!button) return;
  button.disabled = !(state.selectedRecipient && state.selectedScene);
}

function selectRecipient(id) {
  state.selectedRecipient = id;
  document.querySelectorAll("[data-recipient]").forEach((node) => {
    node.classList.toggle("selected", node.getAttribute("data-recipient") === id);
  });
  updateHomeStartButton();
}

function selectScene(id) {
  state.selectedScene = id;
  document.querySelectorAll("[data-scene]").forEach((node) => {
    node.classList.toggle("selected", node.getAttribute("data-scene") === id);
  });
  updateHomeStartButton();
}

function renderRecipientGrid(recipients) {
  const node = el("recipientGrid");
  if (!node) return;
  node.innerHTML = "";
  recipients.forEach((recipient) => {
    const meta = RECIPIENT_META[recipient.id] || {};
    const card = document.createElement("button");
    card.type = "button";
    card.className = "recipient-card";
    card.setAttribute("data-recipient", recipient.id);
    card.innerHTML =
      `<div class="recipient-card-icon">${meta.icon || ""}</div>` +
      `<div class="recipient-card-label">${escHtml(recipient.label || meta.label || recipient.id)}</div>` +
      `<div class="recipient-card-hint">${escHtml(meta.hint || "")}</div>`;
    card.addEventListener("click", () => selectRecipient(recipient.id));
    node.appendChild(card);
  });
}

function renderSceneGrid(scenes) {
  const node = el("sceneGrid");
  if (!node) return;
  node.innerHTML = "";
  scenes.forEach((scene) => {
    const meta = SCENE_META[scene.id] || {};
    const card = document.createElement("button");
    card.type = "button";
    card.className = "scene-chip";
    card.setAttribute("data-scene", scene.id);
    card.innerHTML =
      `<div class="scene-chip-label">${escHtml(scene.label || meta.label || scene.id)}</div>` +
      `<div class="scene-chip-hint">${escHtml(meta.hint || "")}</div>`;
    card.addEventListener("click", () => selectScene(scene.id));
    node.appendChild(card);
  });
}

async function loadBootstrap() {
  const response = await apiFetch("/api/xiangta/bootstrap");
  if (!response) {
    if (apiFetch.lastErrorKind !== "timeout") {
      setStatus("启动配置加载失败，请刷新重试", "warn");
      showToast("启动配置加载失败，请刷新重试");
    }
    return;
  }
  state.bootstrap = response.data;
  renderRecipientGrid(state.bootstrap.recipients || []);
  renderSceneGrid(state.bootstrap.scenes || []);
  state.selectedVoice = state.bootstrap.voicePresets?.[0]?.id || state.selectedVoice;
  state.selectedTone = state.bootstrap.tonePresets?.find((tone) => tone.id === "gentle")?.id || state.bootstrap.tonePresets?.[0]?.id || state.selectedTone;
  renderStatusPill(state.bootstrap.providerStatus);
  renderProviderStatus(state.bootstrap.providerStatus);
  updateHomeStartButton();
  renderHomeRecentLetter();
  // Load voice binding status for Step 3 display
  await loadVoiceBindingStatus();
  if (state.mode === "dev") {
    await loadCoreProfiles();
  }
}

async function loadVoiceBindingStatus() {
  const response = await apiFetch("/api/xiangta/voice-bindings/status");
  if (!response) {
    state.voiceBindingStatus = null;
    return;
  }
  state.voiceBindingStatus = response.data || null;
}

async function loadCoreProfiles() {
  const response = await apiFetch("/api/xiangta/core/profiles");
  if (!response) {
    state.coreProfiles = [];
    return;
  }
  state.coreProfiles = response.data.profiles || [];
  renderCoreProfileSelect(response.data);
}

function renderCoreProfileSelect(data) {
  const node = el("coreProfileSelect");
  if (!node) return;
  node.innerHTML = "";
  if (data.source === "not_integrated") {
    node.innerHTML = '<option value="">未接入 Core</option>';
    return;
  }
  node.innerHTML = '<option value="">请选择人设...</option>';
  state.coreProfiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.id || "";
    option.textContent = `${profile.name || profile.id} (${profile.id || ""})`;
    node.appendChild(option);
  });
}

function renderGuidancePrompts(sceneId) {
  const node = el("guidancePrompts");
  if (!node) return;
  const prompts = GUIDANCE_PROMPTS[sceneId] || GUIDANCE_PROMPTS.miss;
  node.innerHTML = "";
  prompts.forEach((prompt, index) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "prompt-card";
    card.innerHTML =
      `<span class="prompt-index">0${index + 1}</span>` +
      `<span class="prompt-text">${escHtml(prompt)}</span>` +
      '<span class="prompt-tail">+</span>';
    card.addEventListener("click", () => {
      const textarea = el("rawTextArea");
      if (!textarea) return;
      // Preserve trailing newline so cursor lands on a blank line ready to type.
      // Mirrors prototype appendPrompt: raw ? `${raw}\n\n${p}\n` : `${p}\n`
      const existing = textarea.value;
      const newVal = existing.trim()
        ? `${existing.trimEnd()}\n\n${prompt}\n`
        : `${prompt}\n`;
      const clamped = newVal.slice(0, 500);
      textarea.value = clamped;
      updateComposeState();
      // Position cursor at end so user can continue typing immediately.
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(clamped.length, clamped.length);
      }, 50);
    });
    node.appendChild(card);
  });
}

function updateComposeState() {
  const textarea = el("rawTextArea");
  if (!textarea) return;
  const value = textarea.value || "";
  const trimmed = value.trim();
  const count = el("rawTextCount");
  const wrap = el("rawTextWrap");
  const button = el("btnGenSuggestions");
  const hint = el("composeCTAHint");
  if (
    state.demoFixtureActive &&
    state.demoFixtureKey &&
    typeof DEMO_FIXTURES !== "undefined" &&
    DEMO_FIXTURES[state.demoFixtureKey]
  ) {
    const fixtureRaw = (DEMO_FIXTURES[state.demoFixtureKey].rawText || "").trim();
    if (trimmed !== fixtureRaw) {
      state.demoFixtureActive = false;
      state.demoFixtureKey = null;
    }
  }
  if (count) count.textContent = String(value.length);
  if (wrap) wrap.classList.toggle("has-text", trimmed.length > 0);
  if (button) button.disabled = trimmed.length < 4;
  if (hint) {
    hint.textContent = value.trim().length >= 4 ? "会给你 3 种表达 · 你来挑一个最像自己的" : "写几个字试试 · 不用一次写完";
  }
  renderRiskHint("riskHint", value);
}

function goCompose() {
  if (!state.selectedRecipient) {
    setStatus("先选一个想说话的人", "warn");
    return;
  }
  if (!state.selectedScene) {
    setStatus("先选一种想表达的心情", "warn");
    return;
  }
  const recipientLabel = getBootstrapRecipientLabel(state.selectedRecipient);
  const sceneLabel = getBootstrapSceneLabel(state.selectedScene);
  el("composeTitle").textContent = `${sceneLabel} · 给${recipientLabel}`;
  renderStepDots("composeStepDots", 0, STEP_LABELS);
  renderGuidancePrompts(state.selectedScene);
  const textarea = el("rawTextArea");
  if (textarea) {
    textarea.value = "";
    textarea.placeholder = `比如：${RAW_EXAMPLES[state.selectedScene] || RAW_EXAMPLES.miss}`;
  }
  state.finalText = "";
  state.suggestions = [];
  state.selectedIndex = -1;
  updateComposeState();
  showScreen("compose");
}

function buildSuggestionViewModel(data) {
  if (data.suggestions && Array.isArray(data.suggestions)) {
    return data.suggestions.map((item, index) => {
      const normalizedText = normalizeCopyText(item.text || "");
      return {
        text: normalizedText,
        style: item.style || ["restrained", "gentle", "sincere"][index] || "gentle",
        styleLabel: item.styleLabel || STYLE_LABELS[item.style] || `版本 ${index + 1}`,
        fitsFor: item.fitsFor || "适合想把话说得更稳一些的时候",
        charCount: normalizedText.length,
      };
    });
  }
  return [];
}

function renderSuggestionCards(meta) {
  const insight = el("aiUnderstanding");
  const list = el("suggestionsArea");
  if (!list || !insight) return;
  insight.innerHTML =
    '<div class="insight-label"><span class="insight-dot"></span><span>我读到的是</span></div>' +
    `<div class="insight-summary">${escHtml(meta.summary || "你想把没说完的话，说得更稳一些。")}</div>` +
    '<div class="insight-divider"></div>' +
    `<div class="insight-intent">表达目标 · ${escHtml(meta.intent || "更贴近关系，也更贴近你")}</div>`;
  list.innerHTML = "";
  state.suggestions.forEach((item, index) => {
    const selected = state.selectedIndex === index;
    const delay = (0.2 + index * 0.13).toFixed(2);
    const card = document.createElement("article");
    card.setAttribute("data-suggestion-index", String(index));
    card.className = "suggestion-card" + (selected ? " selected" : "");
    card.style.animation = `spaCardIn 0.42s ${delay}s both`;
    const dotHtml = selected ? '<span class="suggestion-dot"></span>' : "";
    card.innerHTML =
      '<div class="suggestion-meta">' +
      '<div class="suggestion-style-row">' +
      `<span class="suggestion-style">${escHtml(item.styleLabel)}</span>` +
      dotHtml +
      "</div>" +
      `<span class="suggestion-count">${item.charCount}字</span>` +
      "</div>" +
      `<div class="suggestion-text">${escHtml(item.text)}</div>` +
      `<div class="suggestion-fit">适合：${escHtml(item.fitsFor)}</div>` +
      '<div class="suggestion-actions">' +
      '<div class="suggestion-action-left">' +
      `<button type="button" class="small-pill-btn" data-index="${index}" data-action="edit">编辑</button>` +
      `<button type="button" class="small-pill-btn" data-index="${index}" data-action="copy">复制</button>` +
      "</div>" +
      `<button type="button" class="expr-select-btn" data-index="${index}" data-action="select">${selected ? "已选择" : "选这条"}</button>` +
      "</div>";
    card.addEventListener("click", () => selectSuggestion(index));
    card.querySelector('[data-action="edit"]')?.addEventListener("click", (event) => editSuggestion(index, event));
    const copyBtn = card.querySelector('[data-action="copy"]');
    copyBtn?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      copySuggestion(index, event, copyBtn);
    });
    card.querySelector('[data-action="select"]')?.addEventListener("click", (event) => {
      event.stopPropagation();
      selectSuggestion(index);
    });
    list.appendChild(card);
  });
}

function updateSuggestionCardContent(index) {
  const suggestion = state.suggestions[index];
  if (!suggestion) return;
  const card = document.querySelector(`.suggestion-card[data-suggestion-index="${index}"]`);
  if (!card) return;
  const countNode = card.querySelector(".suggestion-count");
  if (countNode) countNode.textContent = `${suggestion.charCount}字`;
  const textNode = card.querySelector(".suggestion-text");
  if (textNode) textNode.textContent = suggestion.text;
}

function updateSuggestionSelectionUi(prevIndex, nextIndex) {
  const list = el("suggestionsArea");
  if (!list) return;
  const updateCard = function(card, selected) {
    if (!card) return;
    card.classList.toggle("selected", selected);
    const styleRow = card.querySelector(".suggestion-style-row");
    if (styleRow) {
      const existingDot = styleRow.querySelector(".suggestion-dot");
      if (selected) {
        if (!existingDot) {
          const dot = document.createElement("span");
          dot.className = "suggestion-dot";
          styleRow.appendChild(dot);
        }
      } else if (existingDot) {
        existingDot.remove();
      }
    }
    const selectBtn = card.querySelector('[data-action="select"]');
    if (selectBtn) {
      selectBtn.textContent = selected ? "已选择" : "选这条";
    }
  };
  if (typeof prevIndex === "number" && prevIndex >= 0) {
    updateCard(list.querySelector(`.suggestion-card[data-suggestion-index="${prevIndex}"]`), false);
  }
  if (typeof nextIndex === "number" && nextIndex >= 0) {
    updateCard(list.querySelector(`.suggestion-card[data-suggestion-index="${nextIndex}"]`), true);
  }
}

function markSuggestionCopyButtonCopied(button) {
  if (!button) return;
  const originalText = button.dataset.copyOriginalText || button.textContent || "复制";
  button.dataset.copyOriginalText = originalText;
  button.textContent = "已复制";
  button.classList.add("copied");
  if (button._copyRestoreTimer) {
    clearTimeout(button._copyRestoreTimer);
  }
  button._copyRestoreTimer = setTimeout(() => {
    button.textContent = button.dataset.copyOriginalText || "复制";
    button.classList.remove("copied");
    button._copyRestoreTimer = null;
  }, 1000);
}

async function copySuggestion(index, event, button) {
  event?.preventDefault?.();
  event?.stopPropagation?.();
  const suggestion = state.suggestions[index];
  if (!suggestion?.text) {
    showToast("没有可复制的内容");
    return;
  }

  const textToCopy = normalizeCopyText(suggestion.text);
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(textToCopy);
      markSuggestionCopyButtonCopied(button);
      return;
    }
  } catch (error) {
    // Fallback below.
  }

  let area = null;
  try {
    area = document.createElement("textarea");
    area.value = textToCopy;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    area.style.top = "0";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.focus();
    area.select();
    if (typeof area.setSelectionRange === "function") {
      area.setSelectionRange(0, area.value.length);
    }
    const ok = document.execCommand("copy");
    if (ok) {
      markSuggestionCopyButtonCopied(button);
    } else {
      showToast("复制失败，请长按文字手动复制");
    }
  } catch (error) {
    showToast("复制失败，请长按文字手动复制");
  } finally {
    if (area && area.parentNode) {
      area.parentNode.removeChild(area);
    }
  }
}

function editSuggestion(index, event) {
  event?.stopPropagation();
  const suggestion = state.suggestions[index];
  if (!suggestion) return;
  const nextText = window.prompt("编辑这段表达", suggestion.text);
  if (nextText === null) return;
  const text = nextText.trim();
  if (!text) {
    showToast("内容不能为空");
    return;
  }
  const normalizedText = normalizeCopyText(text);
  state.suggestions[index] = {
    ...suggestion,
    text: normalizedText,
    charCount: normalizedText.length,
  };
  updateSuggestionCardContent(index);
  selectSuggestion(index);
}

async function generateSuggestions() {
  const rawText = (el("rawTextArea")?.value || "").trim();
  if (rawText.length < 4) {
    setStatus("先写下至少 4 个字", "warn");
    return;
  }

  // Demo fixture bypass: use local preset suggestions when rawText matches the example exactly.
  // If user has edited the text, rawText won't match and we fall through to the real API.
  if (
    state.demoFixtureActive &&
    state.demoFixtureKey &&
    typeof DEMO_FIXTURES !== "undefined" &&
    DEMO_FIXTURES[state.demoFixtureKey] &&
    rawText === DEMO_FIXTURES[state.demoFixtureKey].rawText.trim()
  ) {
    const fixture = DEMO_FIXTURES[state.demoFixtureKey];
    setBusy("btnGenSuggestions", true, "整理中...");
    state.suggestionMeta = fixture.suggestionMeta;
    state.suggestions = buildSuggestionViewModel(fixture);
    state.selectedIndex = -1;
    state.finalText = "";
    state.selectedStyle = fixture.suggestions[fixture.preferredIndex]?.style || "gentle";
    el("suggestSubtitle").textContent = `给${getBootstrapRecipientLabel(state.selectedRecipient)} · ${getBootstrapSceneLabel(state.selectedScene)}`;
    renderStepDots("suggestStepDots", 1, STEP_LABELS);
    renderSuggestionCards(fixture.suggestionMeta);
    renderRiskHint("suggestRiskHint", rawText);
    setBusy("btnGenSuggestions", false, "帮我整理表达");
    setBusy("btnToVoice", false, "用这条 · 生成语音");
    // Auto-select the preferred suggestion
    const preferredIndex = typeof fixture.preferredIndex === "number" ? fixture.preferredIndex : -1;
    if (preferredIndex >= 0 && preferredIndex < state.suggestions.length) {
      selectSuggestion(preferredIndex);
    } else {
      el("btnToVoice").disabled = true;
    }
    showScreen("suggest");
    return;
  }

  setBusy("btnGenSuggestions", true, "整理中...");
  const response = await apiFetch("/api/xiangta/suggestions", {
    method: "POST",
    body: JSON.stringify({
      recipient: state.selectedRecipient,
      scene: state.selectedScene,
      rawText: rawText,
    }),
  }, {
    timeoutMs: 12000,
    timeoutMessage: "这次整理超时了，可以稍后重试",
  });
  setBusy("btnGenSuggestions", false, "帮我整理表达");
  if (!response) return;
  state.suggestionMeta = response.data;
  state.suggestions = buildSuggestionViewModel(response.data);
  state.selectedIndex = -1;
  state.finalText = "";
  state.selectedStyle = "gentle";
  el("suggestSubtitle").textContent = `给${getBootstrapRecipientLabel(state.selectedRecipient)} · ${getBootstrapSceneLabel(state.selectedScene)}`;
  renderStepDots("suggestStepDots", 1, STEP_LABELS);
  renderSuggestionCards(response.data);
  renderRiskHint("suggestRiskHint", rawText);
  setBusy("btnToVoice", false, "用这条 · 生成语音");
  el("btnToVoice").disabled = true;
  showScreen("suggest");
}

function selectSuggestion(index) {
  const prevIndex = state.selectedIndex;
  state.selectedIndex = index;
  const suggestion = state.suggestions[index];
  if (!suggestion) return;
  const normalizedText = normalizeCopyText(suggestion.text);
  state.finalText = normalizedText;
  state.selectedStyle = suggestion.style;
  const finalTextArea = el("finalTextArea");
  if (finalTextArea) finalTextArea.value = normalizedText;
  updateSuggestionSelectionUi(prevIndex, index);
  const button = el("btnToVoice");
  if (button) button.disabled = false;
}

function buildVoiceOptions() {
  const presets = state.bootstrap?.voicePresets || [];
  if (presets.length > 0) {
    return presets.map((preset) => ({
      id: preset.id,
      name: preset.label,
      desc: preset.desc || "适合这一刻的表达",
    }));
  }
  return [
    { id: "female-gentle", name: "温柔女声", desc: "适合想念、晚安、轻声表达" },
    { id: "male-gentle", name: "温柔男声", desc: "更沉静，也更像夜里的电话" },
    { id: "female-bright", name: "明亮女声", desc: "适合更轻盈、更直接的表达" },
    { id: "male-mature", name: "成熟男声", desc: "更稳，更像一封慢慢打开的信" },
  ];
}

function renderVoiceTextPreview() {
  const node = el("voiceTextPreview");
  if (!node) return;
  const recLabel = getBootstrapRecipientLabel(state.selectedRecipient) || "恋人";
  const sceneLabel = getBootstrapSceneLabel(state.selectedScene);
  const styleLabel = STYLE_LABELS[state.selectedStyle] || "温柔版";
  node.innerHTML =
    '<div class="voice-copy-meta">' +
    `<span class="voice-copy-tag">给${escHtml(recLabel)} · ${escHtml(sceneLabel)} · ${escHtml(styleLabel)}</span>` +
    '<button class="voice-copy-edit" type="button" onclick="showScreen(\'suggest\')">编辑文字</button>' +
    "</div>" +
    `<div class="voice-copy-text">${escHtml(state.finalText)}</div>`;
}

function renderVoicePicker() {
  const node = el("voicePicker");
  if (!node) return;
  node.innerHTML = "";
  buildVoiceOptions().forEach((voice) => {
    const selected = voice.id === state.selectedVoice;
    // Look up binding status for this voice preset
    const bindingInfo = getVoiceBindingInfo(voice.id);
    const isBound = bindingInfo && bindingInfo.bound;
    // Disable unbound voices in formal H5 (dev mode can still use unbound)
    const disabled = state.mode !== "dev" && !isBound;
    const option = document.createElement("button");
    option.type = "button";
    option.disabled = disabled;
    option.className = "voice-option" + (selected ? " selected" : "") + (disabled ? " disabled" : "");
    option.title = disabled ? "此声音尚未绑定 Core profile，请先在 Admin 配置页绑定" : (voice.desc || "");

    let badgeHtml = "";
    if (bindingInfo) {
      if (!bindingInfo.bound) {
        const badgeClass = bindingInfo.reason && bindingInfo.reason.includes("失效") ? "voice-bind-badge invalid" : "voice-bind-badge unbound";
        badgeHtml = '<span class="' + badgeClass + '">' + escHtml(bindingInfo.reason || "待绑定") + '</span>';
      } else if (bindingInfo.coreAvailable === false) {
        badgeHtml = '<span class="voice-bind-badge invalid">绑定失效</span>';
      } else {
        badgeHtml = '<span class="voice-bind-badge bound">已绑定</span>';
      }
    }

    const checkSvg = selected
      ? '<svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 5l2 2 4-4" stroke="white" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      : "";
    option.innerHTML =
      '<span class="voice-wave"><span class="voice-wave-bar" style="height:40%"></span><span class="voice-wave-bar" style="height:80%"></span><span class="voice-wave-bar" style="height:50%"></span><span class="voice-wave-bar" style="height:100%"></span><span class="voice-wave-bar" style="height:60%"></span></span>' +
      '<span class="voice-option-info">' +
      `<span class="voice-option-name">${escHtml(voice.name)}</span>` +
      `<span class="voice-option-desc">${escHtml(voice.desc || "")}</span>` +
      badgeHtml +
      "</span>" +
      `<span class="voice-option-check">${checkSvg}</span>`;
    option.addEventListener("click", () => {
      if (disabled) return;
      state.selectedVoice = voice.id;
      renderVoicePicker();
      updateGenTtsButton();
    });
    node.appendChild(option);
  });

  // Show hint when all voices are unbound in formal mode
  const hintNode = el("voiceBindHint");
  if (hintNode) {
    const bindingItems = state.voiceBindingStatus?.items || [];
    const allUnbound = bindingItems.length > 0 && bindingItems.every(function(item) { return !item.bound; });
    if (state.mode !== "dev" && allUnbound) {
      hintNode.textContent = "当前还没有绑定真实声音，请先到 Admin 配置页绑定 Core profile。";
      hintNode.classList.remove("hidden");
    } else {
      hintNode.classList.add("hidden");
    }
  }
}

function getVoiceBindingInfo(voicePresetId) {
  if (!state.voiceBindingStatus) return null;
  const items = state.voiceBindingStatus.items || [];
  return items.find(function(item) { return item.voicePreset === voicePresetId; }) || null;
}

function renderToneChips() {
  const tones = state.bootstrap?.tonePresets || TONE_META;
  const node = el("toneChips");
  if (!node) return;
  node.innerHTML = "";
  tones.forEach((tone) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "tone-chip" + (tone.id === state.selectedTone ? " selected" : "");
    chip.textContent = tone.label;
    chip.addEventListener("click", () => {
      state.selectedTone = tone.id;
      renderToneChips();
    });
    node.appendChild(chip);
  });
}

function renderDurationEstimate() {
  const node = el("durationEstimate");
  if (!node) return;
  const seconds = Math.max(3, Math.round((state.finalText || "").length * 0.28 + 1.5));
  const min = Math.floor(seconds / 60);
  const sec = String(seconds % 60).padStart(2, "0");
  node.innerHTML =
    '<span class="duration-estimate-label">预计时长</span>' +
    `<span class="duration-estimate-value">≈ ${min}:${sec}</span>`;
}

function autoSelectBoundVoice() {
  if (!state.voiceBindingStatus) return;
  const items = state.voiceBindingStatus.items || [];
  const currentBound = items.find(function(item) {
    return item.voicePreset === state.selectedVoice && item.bound;
  });
  if (currentBound) return; // current voice is bound, no change needed
  // Find first bound voice preset
  const firstBound = items.find(function(item) { return item.bound; });
  if (firstBound) {
    state.selectedVoice = firstBound.voicePreset;
  }
}

function updateGenTtsButton() {
  const btn = el("btnGenTtsTask");
  if (!btn) return;
  // Check if selected voice is bound
  if (!state.voiceBindingStatus) {
    btn.disabled = false;
    return;
  }
  const items = state.voiceBindingStatus.items || [];
  const currentBinding = items.find(function(item) {
    return item.voicePreset === state.selectedVoice;
  });
  if (!currentBinding || !currentBinding.bound) {
    btn.disabled = true;
    btn.title = "当前声音尚未绑定 Core profile，请先在 Admin 配置页绑定";
  } else {
    btn.disabled = false;
    btn.title = "";
  }
}

function resetVoiceTransientUi() {
  setBusy("btnGenTtsTask", false, "生成语音");
  const ttsResult = el("ttsResult");
  if (ttsResult) {
    ttsResult.classList.add("hidden");
    ttsResult.innerHTML = "";
  }
  const saveSection = el("saveLetterSection");
  if (saveSection) {
    saveSection.classList.add("hidden");
  }
  updateGenTtsButton();
}

function returnToVoiceFresh() {
  state.ttsPollToken += 1;
  state.ttsTask = null;
  state.ttsResult = null;
  resetVoiceTransientUi();
  showScreen("voice");
}

async function goVoice() {
  if (!state.finalText) {
    setStatus("先选一条最像你的表达", "warn");
    return;
  }
  // Refresh voice binding status before entering Step 3
  await loadVoiceBindingStatus();
  // Auto-select first bound voice preset if current is unbound
  autoSelectBoundVoice();
  renderStepDots("voiceStepDots", 2, STEP_LABELS);
  el("voiceSubtitle").textContent = `${getBootstrapSceneLabel(state.selectedScene)} · ${STYLE_LABELS[state.selectedStyle] || "温柔版"}`;
  state.ttsPollToken += 1;
  state.ttsTask = null;
  state.ttsResult = null;
  resetVoiceTransientUi();
  renderVoiceTextPreview();
  renderVoicePicker();
  renderToneChips();
  renderDurationEstimate();
  showScreen("voice");
}

async function generateTtsTask() {
  const rawText = state.finalText || (el("finalTextArea")?.value || "").trim();
  const text = normalizeCopyText(rawText);
  if (!text) {
    setStatus("先确认要生成语音的文字", "warn");
    return;
  }
  const token = ++state.ttsPollToken;
  const payload = {
    text: text,
    voicePreset: state.selectedVoice,
    tone: state.selectedTone,
    recipient: state.selectedRecipient,
    scene: state.selectedScene,
  };
  const profileId = el("coreProfileSelect")?.value || null;
  if (state.mode === "dev" && profileId) {
    payload.profileId = profileId;
  }
  setBusy("btnGenTtsTask", true, "生成中...");
  const response = await apiFetch("/api/xiangta/tts/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!response) {
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }
  if (token !== state.ttsPollToken) return;
  // Fetch full task detail to ensure we have audioUrl/durationMs before rendering
  const created = response.data;
  const detailed = await fetchTtsTaskDetail(created);
  if (token !== state.ttsPollToken) return;
  state.ttsTask = detailed;
  renderTtsTask(detailed);
  if (detailed && detailed.status !== "completed" && detailed.status !== "failed") {
    window.setTimeout(() => pollTtsTask(detailed, token), 1500);
  }
  setBusy("btnGenTtsTask", false, "生成语音");
}

async function fetchTtsTaskDetail(task) {
  if (!task) return task;
  const pollUrl = task.pollUrl || (task.taskId ? `/api/xiangta/tts/tasks/${task.taskId}` : null);
  if (!pollUrl) return task;
  const response = await apiFetch(pollUrl);
  if (!response) return task;
  const detail = response.data || response;
  detail.pollUrl = pollUrl;
  return detail;
}

async function pollTtsTask(task, token) {
  if (token !== state.ttsPollToken) return;
  if (!task) return;
  const status = task.status;
  const pollUrl = task.pollUrl || `/api/xiangta/tts/tasks/${task.taskId}`;
  if (status === "completed" || status === "failed") {
    // Completed/failed synchronously — fetch detail to ensure audioUrl is populated
    const detailed = await fetchTtsTaskDetail(task);
    if (token !== state.ttsPollToken) return;
    state.ttsTask = detailed;
    renderTtsTask(detailed);
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }
  setBusy("btnGenTtsTask", true, `生成中...（${status}）`);
  const response = await apiFetch(pollUrl);
  if (token !== state.ttsPollToken) return;
  if (!response) {
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }
  const updated = response.data || response;
  updated.pollUrl = pollUrl;
  state.ttsTask = updated;
  if (updated.status === "completed" || updated.status === "failed") {
    renderTtsTask(updated);
    setBusy("btnGenTtsTask", false, "生成语音");
  } else {
    window.setTimeout(() => pollTtsTask(updated, token), 1500);
  }
}

function revealSaveLetterSection() {
  const section = el("saveLetterSection");
  if (!section || !state.finalText) return;
  section.classList.remove("hidden");
  const subtitle = section.querySelector(".save-letter-subtitle");
  if (!subtitle) return;
  if (state.ttsResult?.status === "failed" || !state.ttsResult?.audioUrl) {
    subtitle.textContent = "语音暂未生成，也可以先保存文字信笺。";
  } else {
    subtitle.textContent = "这段话和声音都可以一起保存下来。";
  }
}

function renderTtsTask(result) {
  const div = el("ttsResult");
  if (!div) return;
  state.ttsResult = result;

  // Success case: navigate to result screen instead of showing inline card
  if (result.status === "completed" && result.audioUrl) {
    state.resultSaved = false;
    state.resultFavorited = false;
    state.resultSavedLetterId = null;
    state.resultSavedLetter = null;
    renderResultScreen(result);
    showScreen("result");
    return;
  }

  // Failure / no-audio case: show inline diagnostic card
  div.classList.remove("hidden");
  div.innerHTML = "";
  const badgeClass = result.status === "failed" ? "failed" : "";
  let html =
    '<div class="tts-state-card">' +
    '<div class="tts-state-top">' +
    `<div class="tts-state-title">${result.status === "failed" ? "这次语音还没顺利生成" : "语音结果"}</div>` +
    `<div class="tts-state-badge ${badgeClass}">${escHtml(result.status || "processing")}</div>` +
    "</div>" +
    '<div class="tts-meta-list">';
  if (result.taskId) html += `<div class="tts-meta-row"><span class="tts-meta-key">任务 ID</span><span class="tts-meta-value">${escHtml(result.taskId)}</span></div>`;
  if (result.durationMs) html += `<div class="tts-meta-row"><span class="tts-meta-key">时长</span><span class="tts-meta-value">${(result.durationMs / 1000).toFixed(1)} 秒</span></div>`;
  if (result.message) html += `<div class="tts-meta-row"><span class="tts-meta-key">说明</span><span class="tts-meta-value">${escHtml(result.message)}</span></div>`;
  html += "</div>";
  if (result.audioUrl) {
    html += `<div class="tts-audio"><audio controls preload="none" src="${escHtml(normalizePlayableAudioUrl(result.audioUrl))}"></audio></div>`;
  } else if (result.status === "completed") {
    html += '<div class="tts-hint">任务已完成，但没有返回可播放音频地址。请检查 Core render 返回的 audio_asset.url。</div>';
  } else {
    html += '<div class="tts-hint">语音暂未生成，可先保存文字信笺。</div>';
  }
  html += "</div>";
  div.innerHTML = html;
  revealSaveLetterSection();
}

// ─────────────────────────────────────────────────────────────
// Result screen — "今晚的信笺" — rendered after TTS success
// ─────────────────────────────────────────────────────────────
function renderResultMetaPills() {
  const pillsNode = el("resultMetaPills");
  if (!pillsNode) return;

  const recipientLabel = getBootstrapRecipientLabel(state.selectedRecipient) || RECIPIENT_META[state.selectedRecipient]?.label || "恋人";
  const sceneLabel = getBootstrapSceneLabel(state.selectedScene) || SCENE_META[state.selectedScene]?.label || "想念";
  const styleLabel = STYLE_LABELS[state.selectedStyle] || "温柔版";

  let html =
    `<span class="result-pill active">给${escHtml(recipientLabel)}</span>` +
    `<span class="result-pill">${escHtml(sceneLabel)}</span>` +
    `<span class="result-pill">${escHtml(styleLabel)}</span>`;

  if (state.resultSaved && state.resultFavorited) {
    html += `<span class="result-pill favorited">★ 收藏</span>`;
  }

  pillsNode.innerHTML = html;
  updateResultFavoriteSeal();
}

function updateResultFavoriteSeal() {
  const seal = document.querySelector("#resultLetterCard .result-letter-seal");
  if (!seal) return;
  seal.classList.toggle("favorited", !!(state.resultSaved && state.resultFavorited));
}

function renderResultScreen(result) {
  const finalText = state.finalText || (el("finalTextArea")?.value || "").trim();
  const audioUrl = normalizePlayableAudioUrl(result.audioUrl || "");
  const durationMs = result.durationMs || 0;
  const durationSecs = durationMs / 1000;

  // Meta labels
  const recipientLabel = getBootstrapRecipientLabel(state.selectedRecipient) || RECIPIENT_META[state.selectedRecipient]?.label || "恋人";
  const sceneLabel = getBootstrapSceneLabel(state.selectedScene) || SCENE_META[state.selectedScene]?.label || "想念";
  const styleLabel = STYLE_LABELS[state.selectedStyle] || "温柔版";
  const voiceLabel = getBootstrapVoiceLabel(state.selectedVoice);
  const toneLabel = getBootstrapToneLabel(state.selectedTone);

  // Date string
  const now = new Date();
  const dateStr = `${now.getFullYear()} · ${String(now.getMonth() + 1).padStart(2, '0')} · ${String(now.getDate()).padStart(2, '0')}  ·  ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const signatureStr = now.getHours() >= 18 || now.getHours() < 5 ? "今晚" : "今天";

  // Render meta pills
  renderResultMetaPills();

  // Render letter date
  const dateNode = el("resultLetterDate");
  if (dateNode) dateNode.textContent = dateStr;

  // Render letter body — break at Chinese punctuation like prototype
  const bodyNode = el("resultLetterBody");
  renderLetterBodyLines(bodyNode, finalText);

  // Render signature
  const sigNode = el("resultLetterSignature");
  if (sigNode) sigNode.textContent = `—— 写于${signatureStr}`;

  // Render audio
  const voiceNameNode = el("resultVoiceName");
  if (voiceNameNode) voiceNameNode.textContent = `${voiceLabel} · ${toneLabel}`;

  const audioTimeNode = el("resultAudioTime");
  if (audioTimeNode) {
    const mins = Math.floor(durationSecs / 60);
    const secs = Math.floor(durationSecs % 60);
    audioTimeNode.textContent = `${mins}:${String(secs).padStart(2, '0')}`;
  }

  const audioNode = el("resultAudio");
  if (audioNode) {
    audioNode.src = audioUrl;
    audioNode.load();
  }

  // Update save button state
  updateResultSaveButton();
}


function ensureResultSaveButtonDom() {
  const btn = el("btnResultSave");
  if (!btn) return null;
  let label = el("resultSaveLabel");
  if (!label) {
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 2l1.8 3.7 4.2.6-3 3 .7 4.2L8 11.5l-3.7 2 .7-4.2-3-3 4.2-.6L8 2z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"></path>
      </svg>
      <span id="resultSaveLabel">保存到信笺夹</span>
    `;
    label = el("resultSaveLabel");
  }
  return { btn, label };
}

function setResultSaveBusy(busy, labelText) {
  const { btn, label } = ensureResultSaveButtonDom() || {};
  if (!btn || !label) return;
  label.textContent = labelText;
  btn.disabled = busy;
}

function updateResultSaveButton() {
  const { btn, label } = ensureResultSaveButtonDom() || {};
  const viewHistoryBtn = el("resultViewHistoryBtn");
  if (!btn || !label) return;

  if (!state.resultSaved) {
    btn.classList.remove("saved");
    label.textContent = "保存到信笺夹";
    btn.disabled = false;
    btn.onclick = function() { resultSave(); };
    if (viewHistoryBtn) viewHistoryBtn.classList.add("hidden");
  } else if (!state.resultFavorited) {
    btn.classList.remove("saved");
    label.textContent = "加入收藏";
    btn.disabled = false;
    btn.onclick = function() { toggleResultFavorite(); };
    if (viewHistoryBtn) viewHistoryBtn.classList.add("hidden");
  } else {
    btn.classList.remove("saved");
    label.textContent = "已收藏";
    btn.disabled = false;
    btn.onclick = function() { toggleResultFavorite(); };
    if (viewHistoryBtn) viewHistoryBtn.classList.add("hidden");
  }
}

// Result screen action handlers
function resultGoBack() {
  returnToVoiceFresh();
}

function handleHistoryBack() {
  if (
    state.historyReturnTo === "result" &&
    state.ttsResult &&
    state.ttsResult.status === "completed" &&
    state.ttsResult.audioUrl
  ) {
    state.historyReturnTo = "home";
    showScreen("result");
    return;
  }
  state.historyReturnTo = "home";
  showScreen("home");
}

function openHistoryFromHome() {
  state.historyReturnTo = "home";
  showScreen("history");
}

function openHistoryFromResult() {
  state.historyReturnTo = "result";
  showScreen("history");
}

async function toggleResultFavorite() {
  if (!state.resultSavedLetterId) return;
  const letterId = state.resultSavedLetterId;
  const newValue = !state.resultFavorited;

  // Optimistic update
  state.resultFavorited = newValue;
  var letters = state.letters || [];
  for (var i = 0; i < letters.length; i++) {
    var item = letters[i];
    if ((item.id || item.letterId) === letterId) {
      item.favorited = newValue;
      break;
    }
  }
  if (state.resultSavedLetter) {
    state.resultSavedLetter.favorited = newValue;
  }
  updateResultSaveButton();
  renderResultMetaPills();
  if (typeof renderHistoryFilterChips === "function") renderHistoryFilterChips();
  if (typeof renderLetters === "function") renderLetters();
  showToast(newValue ? "已收藏" : "已取消收藏");

  // Persist to backend
  var response = await apiFetch("/api/xiangta/letters/" + encodeURIComponent(letterId) + "/favorite", {
    method: "PATCH",
    body: JSON.stringify({ favorited: newValue }),
  });
  if (!response) {
    showToast("收藏更新失败，请稍后重试");
    // Restore on failure
    state.resultFavorited = !newValue;
    for (var j = 0; j < letters.length; j++) {
      var it = letters[j];
      if ((it.id || it.letterId) === letterId) {
        it.favorited = !newValue;
        break;
      }
    }
    if (state.resultSavedLetter) state.resultSavedLetter.favorited = !newValue;
    updateResultSaveButton();
    renderResultMetaPills();
    if (typeof renderHistoryFilterChips === "function") renderHistoryFilterChips();
    if (typeof renderLetters === "function") renderLetters();
    return;
  }

  // Sync with authoritative server data
  if (response.data) {
    state.resultFavorited = !!response.data.favorited;
    for (var k = 0; k < letters.length; k++) {
      var ltr = letters[k];
      if ((ltr.id || ltr.letterId) === letterId) {
        ltr.favorited = !!response.data.favorited;
        break;
      }
    }
    if (state.resultSavedLetter) state.resultSavedLetter.favorited = !!response.data.favorited;
    updateResultSaveButton();
    renderResultMetaPills();
    if (typeof renderHistoryFilterChips === "function") renderHistoryFilterChips();
    if (typeof renderLetters === "function") renderLetters();
  }
}

async function resultRestart() {
  const audio = el("resultAudio");
  if (!audio) return;
  try {
    audio.currentTime = 0;
    await audio.play();
  } catch (e) {
    showToast("请手动点击播放");
  }
}

function resultDownload() {
  const audioUrl = state.ttsResult?.audioUrl;
  if (!audioUrl) {
    showToast("没有可下载的音频");
    return;
  }
  const a = document.createElement("a");
  a.href = audioUrl;
  a.download = "xiangta-letter.mp3";
  a.target = "_blank";
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

async function resultCopy() {
  const finalText = state.finalText || (el("finalTextArea")?.value || "").trim();
  if (!finalText) {
    showToast("没有可复制的文字");
    return;
  }
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(finalText);
      showToast("已复制文字");
      return;
    }
  } catch (e) {
    // Fall through to textarea fallback
  }
  try {
    const area = document.createElement("textarea");
    area.value = finalText;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    showToast(ok ? "已复制文字" : "复制失败，请手动复制");
  } catch (e) {
    showToast("复制失败，请手动复制");
  }
}

async function resultShare() {
  const finalText = state.finalText || (el("finalTextArea")?.value || "").trim();
  const body = `${finalText}\n\n— 由 想Ta了 写下`;

  if (navigator.share) {
    try {
      await navigator.share({ title: "今晚的信笺", text: body });
      return;
    } catch (e) {
      if (e?.name === "AbortError") return;
    }
  }
  // Fallback: copy to clipboard
  await resultCopy();
  showToast("系统不支持分享，已复制文字");
}

function resultReEdit() {
  // Go back to compose screen, preserve rawText
  showScreen("compose");
}

function resultChangeTone() {
  // Go back to voice screen, reset saved state
  state.resultSaved = false;
  returnToVoiceFresh();
}

function buildSavedLetterViewModel(responseData) {
  // Try response.data first, then response.data.letter, then response itself
  const src = (responseData && responseData.data)
    ? (responseData.data.letter || responseData.data)
    : (responseData || {});
  const letter = {
    id: src.id || src.letterId || null,
    letterId: src.letterId || src.id || null,
    recipient: state.selectedRecipient,
    scene: state.selectedScene,
    style: src.style || state.selectedStyle || null,
    rawText: (el("rawTextArea")?.value || "").trim(),
    finalText: state.finalText || (el("finalTextArea")?.value || "").trim(),
    voicePreset: state.selectedVoice || src.voicePreset || null,
    tone: state.selectedTone || src.tone || null,
    audioUrl: normalizePlayableAudioUrl(state.ttsResult ? (state.ttsResult.audioUrl || "") : (src.audioUrl || "")) || null,
    durationSecs: state.ttsResult ? (state.ttsResult.durationMs ? state.ttsResult.durationMs / 1000 : null) : (src.durationSecs || null),
    title: src.title || null,
    createdAt: src.createdAt || new Date().toISOString(),
    favorited: !!src.favorited,
  };
  return letter;
}

function upsertLetterIntoState(letter) {
  if (!letter || !(letter.id || letter.letterId)) return;
  const id = letter.id || letter.letterId;
  const existing = (state.letters || []).findIndex(function(item) {
    return (item.id || item.letterId) === id;
  });
  if (existing >= 0) {
    state.letters[existing] = letter;
  } else {
    state.letters.unshift(letter);
  }
}

function initOpeningOverlay() {
  const overlay = el("openingOverlay");
  if (!overlay) return;
  overlay.classList.add("hidden");
  overlay.classList.remove("visible");
  try {
    if (localStorage.getItem("xiangta_opening_seen") !== "1") {
      overlay.classList.remove("hidden");
      overlay.classList.add("visible");
    }
  } catch (e) {
    // fail open: keep overlay hidden to avoid blocking app
    overlay.classList.add("hidden");
    overlay.classList.remove("visible");
  }
}

function dismissOpeningOverlay() {
  const overlay = el("openingOverlay");
  if (overlay) {
    overlay.classList.add("hidden");
    overlay.classList.remove("visible");
  }
  try {
    localStorage.setItem("xiangta_opening_seen", "1");
  } catch (e) {
    // ignore — fail open
  }
}

function showResultSavedMoment() {
  const overlay = el("resultSaveSealOverlay");
  if (!overlay) return;
  overlay.classList.remove("hidden");
  overlay.classList.remove("result-save-seal-fadeout");
  void overlay.offsetWidth;
  setTimeout(function() {
    overlay.classList.add("result-save-seal-fadeout");
    setTimeout(function() {
      overlay.classList.add("hidden");
      overlay.classList.remove("result-save-seal-fadeout");
    }, 240);
  }, 900);
}

function showResultSaveSealThenOpenHistory(letter) {
  var letterId = letter.id || letter.letterId;
  state.resultSavedLetterId = letterId;
  state.resultSavedLetter = letter;
  state.resultFavorited = !!letter.favorited;

  var overlay = el("resultSaveSealOverlay");
  if (!overlay) {
    // Fallback: go directly to history
    state.historyReturnTo = "result";
    showScreen("history");
    return;
  }
  overlay.classList.remove("hidden");
  overlay.classList.remove("result-save-seal-fadeout");
  void overlay.offsetWidth;
  setTimeout(function() {
    overlay.classList.add("result-save-seal-fadeout");
    setTimeout(function() {
      overlay.classList.add("hidden");
      overlay.classList.remove("result-save-seal-fadeout");
      state.historyReturnTo = "result";
      showScreen("history");
    }, 240);
  }, 900);
}

async function resultSave() {
  if (state.resultSaved) return;
  const finalText = state.finalText || (el("finalTextArea")?.value || "").trim();
  if (!finalText) {
    setStatus("没有可保存的文字", "warn");
    return;
  }
  setResultSaveBusy(true, "正在收好...");
  const suggestion = state.suggestions[state.selectedIndex];
  const audioUrl = normalizePlayableAudioUrl(state.ttsResult ? (state.ttsResult.audioUrl || "") : "") || null;
  const durationMs = state.ttsResult ? (state.ttsResult.durationMs || null) : null;

  const response = await apiFetch("/api/xiangta/letters", {
    method: "POST",
    body: JSON.stringify({
      recipient: state.selectedRecipient,
      scene: state.selectedScene,
      style: suggestion?.style || state.selectedStyle || "gentle",
      rawText: (el("rawTextArea")?.value || "").trim(),
      finalText: finalText,
      voicePreset: state.selectedVoice || null,
      tone: state.selectedTone || null,
      audioUrl: audioUrl,
      durationSecs: durationMs ? durationMs / 1000 : null,
      title: null,
    }),
  }, {
    timeoutMs: 12000,
    timeoutMessage: "保存有点慢，请稍后重试",
  });

  if (!response) {
    state.resultSaved = false;
    setResultSaveBusy(false, "保存到信笺夹");
    return;
  }

  const savedLetter = buildSavedLetterViewModel(response);

  state.resultSaved = true;
  state.resultSavedLetterId = savedLetter.id || savedLetter.letterId;
  state.resultSavedLetter = savedLetter;
  state.resultFavorited = !!savedLetter.favorited;

  upsertLetterIntoState(savedLetter);
  showToast("已保存到信笺夹");
  updateResultSaveButton();
  showResultSaveSealThenOpenHistory(savedLetter);
}

async function generateTts() {
  const text = state.finalText || (el("finalTextArea")?.value || "").trim();
  if (!text) {
    setStatus("先确认要生成的文字", "warn");
    return;
  }
  const payload = {
    text: text,
    voicePreset: state.selectedVoice,
    tone: state.selectedTone,
    recipient: state.selectedRecipient,
    scene: state.selectedScene,
  };
  const profileId = el("coreProfileSelect")?.value || null;
  if (state.mode === "dev" && profileId) {
    payload.profileId = profileId;
  }
  const response = await apiFetch("/api/xiangta/tts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!response) return;
  state.ttsTask = response.data;
  renderTtsTask(response.data);
}

async function saveLetter() {
  const rawFinal = state.finalText || (el("finalTextArea")?.value || "").trim();
  const finalText = normalizeCopyText(rawFinal);
  if (!finalText) {
    setStatus("没有可保存的文字", "warn");
    return;
  }
  setBusy("btnSaveLetter", true, "保存中...");
  const suggestion = state.suggestions[state.selectedIndex];
  const audioUrl = normalizePlayableAudioUrl(state.ttsResult ? (state.ttsResult.audioUrl || "") : "") || null;
  const durationMs = state.ttsResult ? (state.ttsResult.durationMs || null) : null;
  const response = await apiFetch("/api/xiangta/letters", {
    method: "POST",
    body: JSON.stringify({
      recipient: state.selectedRecipient,
      scene: state.selectedScene,
      style: suggestion?.style || state.selectedStyle || "gentle",
      rawText: (el("rawTextArea")?.value || "").trim(),
      finalText: finalText,
      voicePreset: state.selectedVoice || null,
      tone: state.selectedTone || null,
      audioUrl: audioUrl,
      durationSecs: durationMs ? durationMs / 1000 : null,
      title: (el("titleInput")?.value || "").trim() || null,
    }),
  });
  setBusy("btnSaveLetter", false, "保存信笺");
  if (!response) return;
  showToast("已保存到信笺夹");
  setStatus("信笺已保存", "ok");
  if (el("titleInput")) el("titleInput").value = "";
}

function formatLetterDate(value) {
  if (!value) return "";
  return String(value).replace("T", " ").slice(0, 16);
}

async function loadLetters() {
  const response = await apiFetch("/api/xiangta/letters?limit=20&offset=0");
  if (!response) return;
  state.letters = response.data.letters || [];
  if (state.screen === "history") {
    renderHistoryFilterChips();
  }
  renderLetters();
  renderHomeRecentLetter();
}

function renderLetters() {
  const list = el("lettersArea");
  const countNode = el("historyCount");
  if (!list) return;

  const letters = getFilteredLetters();
  const total = state.letters.length;

  if (countNode) {
    countNode.textContent = total > 0 ? `${total} 封 · 已保存到当前服务` : "";
  }

  if (state.letters.length === 0) {
    list.innerHTML = `
      <div class="history-empty-state">
        <div class="history-empty-icon">
          <svg width="28" height="28" viewBox="0 0 22 22" fill="none">
            <rect x="2" y="2" width="18" height="18" rx="4" stroke="currentColor" stroke-width="1" opacity="0.4"/>
            <rect x="6" y="6" width="10" height="10" rx="1.5" stroke="currentColor" stroke-width="1"/>
            <path d="M11 8v6M8 11h6" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.7"/>
          </svg>
        </div>
        <div class="history-empty-title">还没有写过一封信</div>
        <div class="history-empty-body">
          想说的话，写下来之后<br/>就会变成一封小信笺，<br/>留在这里。
        </div>
        <button class="xt-btn primary history-empty-cta" onclick="showScreen('home')">写第一封</button>
      </div>`;
    hideHistoryMiniPlayer();
    return;
  }

  if (letters.length === 0) {
    list.innerHTML = `<div class="history-empty-state"><div class="history-empty-title">这个筛选下还没有信笺。</div></div>`;
    return;
  }

  list.innerHTML = "";
  letters.forEach((letter, index) => {
    const card = document.createElement("div");
    card.className = "prototype-history-card";
    card.style.animationDelay = `${index * 0.05}s`;
    card.onclick = () => openLetterDetail(letter.id || letter.letterId);

    const recipientLabel = getBootstrapRecipientLabel(letter.recipient) || letter.recipient || "";
    const sceneLabel = getBootstrapSceneLabel(letter.scene) || letter.scene || "";
    const title = letter.title || getLetterTitle(letter);
    const preview = (letter.finalText || "").slice(0, 42);
    const durationStr = letter.durationSecs ? formatDuration(letter.durationSecs) : "";

    const iconHtml = letter.audioUrl
      ? `<button class="prototype-history-card-playbtn" type="button" aria-label="播放"><svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M3 2l9 5-9 5V2z" fill="currentColor"/></svg></button>`
      : `<div class="prototype-history-card-icon no-audio"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 2l9 5-9 5V2z" fill="currentColor" opacity="0.4"/></svg></div>`;

    card.innerHTML =
      iconHtml +
      `<div class="prototype-history-card-info">` +
      `<div class="prototype-history-card-title">${escHtml(title)}</div>` +
      `<div class="prototype-history-card-meta">` +
      `<span>${escHtml(recipientLabel)}</span>` +
      `<span class="separator">·</span>` +
      `<span>${escHtml(sceneLabel)}</span>` +
      `<span class="separator">·</span>` +
      `<span>${escHtml(letterTime(letter.createdAt))}</span>` +
      `</div>` +
      `</div>` +
      `<div class="prototype-history-card-right">` +
      (durationStr ? `<span class="prototype-history-card-duration">${durationStr}</span>` : `<span class="prototype-history-card-duration" style="color: var(--xt-text-4)">仅文字</span>`) +
      `<span class="prototype-history-card-star ${letter.favorited ? 'active' : ''}" data-letter-id="${letter.id || letter.letterId}">${letter.favorited ? '★' : '☆'}</span>` +
      `</div>`;

    list.appendChild(card);

    // Safe event binding — no inline onclick string concatenation
    if (letter.audioUrl) {
      const playBtn = card.querySelector(".prototype-history-card-playbtn");
      if (playBtn) {
        playBtn.addEventListener("click", function(event) {
          event.stopPropagation();
          playHistoryLetter(letter);
        });
      }
    }

    // Star click handler — toggle favorite without opening detail
    const starEl = card.querySelector(".prototype-history-card-star");
    if (starEl) {
      starEl.addEventListener("click", function(event) {
        event.stopPropagation();
        toggleHistoryLetterFavorite(letter.id || letter.letterId);
      });
    }
  });

  // Show mini player only for the currently active letter, not auto-selection
  const activeLetter = (state.letters || []).find(function(l) {
    return (l.id || l.letterId) === state.activeHistoryLetterId;
  });
  if (activeLetter && activeLetter.audioUrl) {
    renderHistoryMiniPlayer(activeLetter);
  } else {
    hideHistoryMiniPlayer();
  }
}

function getLetterTitle(letter) {
  if (letter.title) return letter.title;
  const text = letter.finalText || "";
  const firstLine = text.split(/[。！？\n]/)[0] || text;
  return firstLine.slice(0, 20) + (firstLine.length > 20 ? "..." : "");
}

function renderHomeRecentLetter() {
  const container = el("homeRecentLetter");
  if (!container) return;
  const letters = state.letters || [];
  const recent = letters[0];
  const section = el("homeRecentSection");

  if (!recent) {
    if (section) section.style.display = "none";
    container.innerHTML = "";
    return;
  }

  if (section) section.style.display = "";

  const title = getLetterTitle(recent);
  const recipientLabel = RECIPIENT_META[recent.recipient]?.label || "";
  const sceneLabel = SCENE_META[recent.scene]?.label || "";
  const timeStr = letterTime(recent.createdAt);
  const hasAudio = !!recent.audioUrl;
  const recentId = recent.id || recent.letterId;
  const isRecentPlaying =
    hasAudio &&
    state.homeRecentLetterId === recentId &&
    state.homeRecentAudioPlaying;
  const metaText = [recipientLabel, sceneLabel, timeStr].filter(Boolean).join(" · ");

  container.innerHTML = `
    <div class="home-recent-card" onclick="openHistoryFromHome()">
      <button class="home-recent-icon ${hasAudio ? 'has-audio' : ''}" type="button" ${hasAudio ? `aria-label="${isRecentPlaying ? "pause-recent-letter" : "play-recent-letter"}"` : 'aria-label="recent-letter-no-audio" disabled'}>
        ${hasAudio
          ? (isRecentPlaying
            ? '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="3" y="2" width="3" height="10" fill="currentColor"/><rect x="8" y="2" width="3" height="10" fill="currentColor"/></svg>'
            : '<svg width=\"14\" height=\"14\" viewBox=\"0 0 14 14\" fill="none"><path d="M3 2l9 5-9 5V2z" fill="currentColor"/></svg>')
          : '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="3" y="4" width="12" height="10" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M3 6l6 4 6-4" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>'}
      </button>
      <div class="home-recent-info">
        <div class="home-recent-title">${escHtml(title)}</div>
        <div class="home-recent-meta">${escHtml(metaText)}</div>
      </div>
      ${hasAudio ? `<div class="home-recent-duration">${formatDuration(Math.round((recent.finalText || "").length * 0.28 + 1.5))}</div>` : ""}
    </div>`;

  const playBtn = container.querySelector(".home-recent-icon");
  if (playBtn) {
    playBtn.addEventListener("click", function(event) {
      event.stopPropagation();
      playHomeRecentLetter(recent);
    });
  }
}


function getFilteredLetters() {
  let letters = state.letters || [];

  // Apply filter
  if (state.historyFilter === "fav") {
    letters = letters.filter(l => l.favorited);
  } else if (state.historyFilter !== "all") {
    letters = letters.filter(l => l.recipient === state.historyFilter);
  }

  // Apply search
  if (state.historySearchQuery.trim()) {
    const q = state.historySearchQuery.toLowerCase();
    letters = letters.filter(l => {
      const recipientLabel = getBootstrapRecipientLabel(l.recipient) || "";
      const sceneLabel = getBootstrapSceneLabel(l.scene) || "";
      const haystack = [
        l.finalText || "",
        l.title || "",
        recipientLabel,
        sceneLabel,
        l.recipient || "",
        l.scene || ""
      ].join(" ").toLowerCase();
      return haystack.includes(q);
    });
  }

  return letters;
}

function setupHistoryScreen() {
  // Reset history page state when entering
  state.historySearchOpen = false;
  state.historySearchQuery = "";
  state.activeHistoryLetterId = null;
  state.historyAudioPlaying = false;
  state.historyAudioCurrentTime = 0;
  state.historyAudioDuration = 0;

  // Hide search box
  const searchBox = el("historySearchBox");
  if (searchBox) searchBox.classList.add("hidden");

  // Clear search input
  const searchInput = el("historySearchInput");
  if (searchInput) searchInput.value = "";

  // Setup audio listeners
  setupHistoryAudioListeners();

  // Render filter chips
  renderHistoryFilterChips();
}

function toggleHistorySearch() {
  state.historySearchOpen = !state.historySearchOpen;
  const searchBox = el("historySearchBox");
  if (!searchBox) return;

  if (state.historySearchOpen) {
    searchBox.classList.remove("hidden");
    searchBox.style.animation = "spaCardIn 0.22s both";
    const input = el("historySearchInput");
    if (input) input.focus();
  } else {
    searchBox.classList.add("hidden");
    state.historySearchQuery = "";
    const input = el("historySearchInput");
    if (input) input.value = "";
    renderLetters();
  }
}

function onHistorySearchInput(value) {
  state.historySearchQuery = value;
  renderLetters();
}

function renderHistoryFilterChips() {
  const container = el("historyFilterChips");
  if (!container) return;

  const letters = state.letters || [];
  const counts = { lover: 0, family: 0, friend: 0, self: 0, fav: 0 };
  letters.forEach(l => {
    if (l.recipient && counts.hasOwnProperty(l.recipient)) counts[l.recipient]++;
    if (l.favorited) counts.fav++;
  });

  const filters = [
    { id: "all", label: "全部", count: letters.length },
    { id: "lover", label: "恋人", count: counts.lover },
    { id: "family", label: "父母", count: counts.family },
    { id: "friend", label: "朋友", count: counts.friend },
    { id: "self", label: "自己", count: counts.self },
    { id: "fav", label: "收藏", count: counts.fav },
  ];

  container.innerHTML = "";
  filters.forEach(f => {
    // Show "all" always, others only if count > 0
    if (f.id !== "all" && f.count === 0) return;

    const chip = document.createElement("button");
    chip.className = "history-filter-chip" + (state.historyFilter === f.id ? " active" : "");
    chip.textContent = f.label + (f.count > 0 && state.historyFilter !== f.id ? ` · ${f.count}` : "");
    chip.onclick = () => {
      state.historyFilter = f.id;
      renderHistoryFilterChips();
      renderLetters();
    };
    container.appendChild(chip);
  });
}

async function toggleHistoryLetterFavorite(letterId) {
  const letters = state.letters || [];
  const letter = letters.find(function(l) { return (l.id || l.letterId) === letterId; });
  if (!letter) return;

  const previousValue = !!letter.favorited;
  const newValue = !letter.favorited;

  // Optimistic update
  letter.favorited = newValue;

  // Sync result screen if this is the current result letter
  if (state.resultSavedLetterId === letterId) {
    state.resultFavorited = newValue;
    if (state.resultSavedLetter) state.resultSavedLetter.favorited = newValue;
    updateResultSaveButton();
    renderResultMetaPills();
  }

  // Sync letter detail if open
  if (state.activeLetterDetailId === letterId) {
    state.letterDetailFavoritedMap[letterId] = newValue;
    if (state.activeLetterDetail) state.activeLetterDetail.favorited = newValue;
    renderLetterDetailMetaPills(state.activeLetterDetail);
    renderLetterDetailFavoriteButton();
  }

  updateHistoryFavoriteStarUi(letterId, newValue);
  renderHistoryFilterChips();
  if (shouldRenderLettersAfterFavoriteChange(previousValue, newValue)) {
    renderLetters();
  }
  showToast(newValue ? "已收藏" : "已取消收藏");

  // Persist to backend
  var response = await apiFetch("/api/xiangta/letters/" + encodeURIComponent(letterId) + "/favorite", {
    method: "PATCH",
    body: JSON.stringify({ favorited: newValue }),
  });

  if (!response) {
    showToast("收藏更新失败，请稍后重试");
    // Restore on failure
    letter.favorited = !newValue;
    if (state.resultSavedLetterId === letterId) {
      state.resultFavorited = !newValue;
      if (state.resultSavedLetter) state.resultSavedLetter.favorited = !newValue;
      updateResultSaveButton();
      renderResultMetaPills();
    }
    if (state.activeLetterDetailId === letterId) {
      state.letterDetailFavoritedMap[letterId] = !newValue;
      if (state.activeLetterDetail) state.activeLetterDetail.favorited = !newValue;
      renderLetterDetailMetaPills(state.activeLetterDetail);
      renderLetterDetailFavoriteButton();
    }
    updateHistoryFavoriteStarUi(letterId, !newValue);
    renderHistoryFilterChips();
    if (shouldRenderLettersAfterFavoriteChange(newValue, !newValue)) {
      renderLetters();
    }
    return;
  }

  // Sync with authoritative server data
  if (response.data) {
    var authoritativeValue = !!response.data.favorited;
    letter.favorited = authoritativeValue;
    if (state.resultSavedLetterId === letterId) {
      state.resultFavorited = authoritativeValue;
      if (state.resultSavedLetter) state.resultSavedLetter.favorited = !!response.data.favorited;
      updateResultSaveButton();
      renderResultMetaPills();
    }
    if (state.activeLetterDetailId === letterId) {
      state.letterDetailFavoritedMap[letterId] = authoritativeValue;
      if (state.activeLetterDetail) state.activeLetterDetail.favorited = !!response.data.favorited;
      renderLetterDetailMetaPills(state.activeLetterDetail);
      renderLetterDetailFavoriteButton();
    }
    updateHistoryFavoriteStarUi(letterId, authoritativeValue);
    renderHistoryFilterChips();
    if (
      authoritativeValue !== newValue &&
      shouldRenderLettersAfterFavoriteChange(newValue, authoritativeValue)
    ) {
      renderLetters();
    }
  }
}

function shouldRenderLettersAfterFavoriteChange(previousValue, nextValue) {
  return state.historyFilter === "fav" && previousValue !== nextValue;
}

function updateHistoryFavoriteStarUi(letterId, favorited) {
  var stars = document.querySelectorAll(".prototype-history-card-star");
  stars.forEach(function(star) {
    if (star.getAttribute("data-letter-id") !== String(letterId)) return;
    star.classList.toggle("active", !!favorited);
    star.textContent = favorited ? "★" : "☆";
  });
}

function onHistoryCardClick(letter) {
  if (letter.audioUrl) {
    playHistoryLetter(letter.id || letter);
  }
}

// History audio playback
function setupHistoryAudioListeners() {
  if (state.historyAudioListenersBound) return;
  const audio = el("historyAudio");
  if (!audio) return;

  audio.addEventListener("loadedmetadata", function() {
    state.historyAudioDuration = audio.duration;
    var activeLetter = (state.letters || []).find(function(l) {
      return (l.id || l.letterId) === state.activeHistoryLetterId;
    });
    if (activeLetter) {
      renderHistoryMiniPlayer(activeLetter);
    }
    renderHistoryMiniPlayerProgress();
  });

  audio.addEventListener("timeupdate", function() {
    state.historyAudioCurrentTime = audio.currentTime;
    renderHistoryMiniPlayerProgress();
  });

  audio.addEventListener("play", function() {
    state.historyAudioPlaying = true;
    updateHistoryPlayIcon(true);
  });

  audio.addEventListener("pause", function() {
    state.historyAudioPlaying = false;
    updateHistoryPlayIcon(false);
  });

  audio.addEventListener("ended", function() {
    state.historyAudioPlaying = false;
    state.historyAudioCurrentTime = 0;
    updateHistoryPlayIcon(false);
    renderHistoryMiniPlayerProgress();
  });

  audio.addEventListener("error", function() {
    state.historyAudioPlaying = false;
    showToast("音频链接暂不可访问");
    hideHistoryMiniPlayer();
  });

  state.historyAudioListenersBound = true;
}

function playHistoryLetter(letterOrId) {
  pauseHomeRecentAudio();
  let letter;
  if (typeof letterOrId === "object") {
    letter = letterOrId;
  } else {
    letter = state.letters.find(l => (l.id || "") === letterOrId);
  }

  if (!letter || !letter.audioUrl) {
    showToast("这封信没有音频");
    return;
  }

  const audio = el("historyAudio");
  if (!audio) return;

  const letterId = letter.id || letter.letterId;
  if (!letterId) {
    showToast("这封信暂时无法播放");
    return;
  }

  setupHistoryAudioListeners();

  audio.src = normalizePlayableAudioUrl(letter.audioUrl);
  state.activeHistoryLetterId = letterId;
  state.historyAudioPlaying = false;
  state.historyAudioCurrentTime = 0;
  state.historyAudioDuration = 0;

  audio.load();

  audio.play().catch(function() {
    showToast("请手动点击播放");
  });

  renderHistoryMiniPlayer(letter);
}

function playHomeRecentLetter(letter) {
  if (!letter || !letter.audioUrl) {
    showToast("这封信没有音频");
    return;
  }

  if (!state.homeRecentAudio) {
    state.homeRecentAudio = new Audio();
  }

  var letterId = letter.id || letter.letterId;
  var audio = state.homeRecentAudio;

  if (state.homeRecentLetterId === letterId && !audio.paused) {
    audio.pause();
    state.homeRecentAudioPlaying = false;
    renderHomeRecentLetter();
    return;
  }

  state.homeRecentLetterId = letterId;
  state.homeRecentAudioPlaying = false;
  audio.src = normalizePlayableAudioUrl(letter.audioUrl);
  audio.currentTime = 0;

  audio.play().then(function() {
    state.homeRecentAudioPlaying = true;
    renderHomeRecentLetter();
  }).catch(function() {
    showToast("请手动点击播放");
    renderHomeRecentLetter();
  });

  audio.onended = function() {
    state.homeRecentAudioPlaying = false;
    renderHomeRecentLetter();
  };
}

function pauseHomeRecentAudio() {
  if (state.homeRecentAudio) {
    state.homeRecentAudio.pause();
  }
  state.homeRecentAudioPlaying = false;
}

function toggleHistoryPlayback() {
  const audio = el("historyAudio");
  if (!audio || !audio.src) return;

  if (state.historyAudioPlaying) {
    audio.pause();
  } else {
    audio.play().catch(e => {
      showToast("请手动点击播放");
    });
  }
}

function renderHistoryMiniPlayer(letter) {
  const player = el("historyMiniPlayer");
  if (!player || !letter) return;

  const title = letter.title || getLetterTitle(letter);
  const recipientLabel = getBootstrapRecipientLabel(letter.recipient) || "";
  const sceneLabel = getBootstrapSceneLabel(letter.scene) || "";
  const timeStr = `${formatTime(state.historyAudioCurrentTime)} / ${formatTime(state.historyAudioDuration)}`;

  const titleNode = el("historyMiniTitle");
  const subtitleNode = el("historyMiniSubtitle");
  if (titleNode) titleNode.textContent = title;
  if (subtitleNode) subtitleNode.textContent = `${recipientLabel} · ${sceneLabel} · ${timeStr}`;

  player.classList.remove("hidden");
  player.style.animation = "spaMiniPlayerUp 0.22s cubic-bezier(0.2, 0.8, 0.3, 1) both";
}

function renderHistoryMiniPlayerProgress() {
  const fill = el("historyMiniProgress");
  if (!fill) return;
  const pct = state.historyAudioDuration > 0
    ? Math.min(100, (state.historyAudioCurrentTime / state.historyAudioDuration) * 100)
    : 0;
  fill.style.width = `${pct}%`;

  // Update subtitle time
  const subtitleNode = el("historyMiniSubtitle");
  if (subtitleNode) {
    const letter = state.letters.find(l => (l.id || l) === state.activeHistoryLetterId);
    if (letter) {
      const recipientLabel = getBootstrapRecipientLabel(letter.recipient) || "";
      const sceneLabel = getBootstrapSceneLabel(letter.scene) || "";
      const timeStr = `${formatTime(state.historyAudioCurrentTime)} / ${formatTime(state.historyAudioDuration)}`;
      subtitleNode.textContent = `${recipientLabel} · ${sceneLabel} · ${timeStr}`;
    }
  }
}

function hideHistoryMiniPlayer() {
  const player = el("historyMiniPlayer");
  if (player) player.classList.add("hidden");
}

function updateHistoryPlayIcon(isPlaying) {
  const icon = el("historyPlayIcon");
  if (!icon) return;
  if (isPlaying) {
    icon.innerHTML = `<svg width=\"14\" height=\"14\" viewBox=\"0 0 14 14\" fill="none"><rect x="3" y="2" width="3" height="10" rx="1" fill="white"/><rect x="8" y="2" width="3" height="10" rx="1" fill="white"/></svg>`;
  } else {
    icon.innerHTML = `<svg width=\"14\" height=\"14\" viewBox=\"0 0 14 14\" fill="none"><path d="M3 2l9 5-9 5V2z" fill="white"/></svg>`;
  }
}


function initComposeListeners() {
  const textarea = el("rawTextArea");
  if (textarea) {
    textarea.addEventListener("input", updateComposeState);
  }
  const fillExampleLink = el("fillExampleLink");
  if (fillExampleLink) {
    fillExampleLink.addEventListener("click", fillSceneExample);
  }
}

function fillSceneExample() {
  const textarea = el("rawTextArea");
  if (!textarea) return;
  const example = FLOW_EXAMPLES[state.selectedScene] || FLOW_EXAMPLES.miss;
  if (!example) return;
  const current = (textarea.value || "").trim();
  if (current.length === 0) {
    textarea.value = example.rawText;
  } else if (!current.includes(example.rawText)) {
    textarea.value = (current + "\n\n" + example.rawText).slice(0, 500);
  }
  // Pre-fill title if title input is empty
  const titleInput = el("titleInput");
  if (titleInput && !titleInput.value.trim() && example.title) {
    titleInput.value = example.title;
  }
  // Auto-select preferred style/voice/tone
  if (example.preferredStyle) {
    state.selectedStyle = example.preferredStyle;
  }
  if (example.preferredVoice) {
    state.selectedVoice = example.preferredVoice;
  }
  if (example.preferredTone) {
    state.selectedTone = example.preferredTone;
  }
  // Mark demo fixture active — generateSuggestions() will bypass API when rawText matches
  state.demoFixtureKey = state.selectedScene || "miss";
  state.demoFixtureActive = true;
  updateComposeState();
  textarea.focus();
  showToast("已放入一个完整例子，可以直接改成你的话");
}

// ─── Settings Screen ─────────────────────────────────────────

function renderSettingsScreen() {
  const container = el("settingsContent");
  if (!container) return;

  const providerStatus = state.bootstrap?.providerStatus;
  const voiceStatus = state.voiceBindingStatus;
  const lettersCount = (state.letters || []).length;

  // Provider status
  const providerKind = providerStatus?.kind || "unknown";
  const providerOk   = providerKind === "ok";
  const providerWarn = providerKind === "quota" || providerKind === "degraded" || providerKind === "not_integrated";
  const providerError = providerKind === "error";
  const providerLabel = providerOk ? "正常" : providerWarn ? "额度紧张" : providerError ? "未连接" : "检查中";
  const providerDetail = providerStatus?.detail || "";
  const pillTone = providerOk ? "ok" : providerWarn ? "warn" : providerError ? "error" : "mute";
  const providerDotClass = providerOk ? "status-dot-ok" : providerWarn ? "status-dot-warn" : providerError ? "status-dot-error" : "status-dot-idle";
  const quotaPct = providerStatus?.quotaPct ?? 1;
  const quotaDisplay = providerKind === "quota" ? "不足" : providerKind === "no_provider" ? "—" : Math.round(quotaPct * 100) + "%";
  const quotaBarColor = providerWarn ? "var(--warn)" : providerError ? "var(--danger)" : "var(--xt-accent)";

  // Voice binding
  const bindingItems = voiceStatus?.items || [];
  const boundCount = bindingItems.filter(function(i) { return i.bound; }).length;
  const totalVoices = 4;
  const voiceNames = { "female-gentle": "温柔女声", "male-gentle": "温柔男声", "female-bright": "明亮女声", "male-mature": "成熟男声" };
  const voiceOrder = ["female-gentle", "male-gentle", "female-bright", "male-mature"];

  let bindingRowsHtml = "";
  voiceOrder.forEach(function(voiceId) {
    const item = bindingItems.find(function(i) { return i.voicePreset === voiceId; });
    const bound = item ? item.bound : false;
    const badgeClass = bound ? "binding-badge-ok" : "binding-badge-warn";
    const badgeText  = bound ? "已绑定" : "未绑定";
    bindingRowsHtml +=
      "<div class=\"settings-binding-row\">" +
        "<span class=\"settings-binding-name\">" + escHtml(voiceNames[voiceId] || voiceId) + "</span>" +
        "<span class=\"settings-binding-badge " + badgeClass + "\">" + badgeText + "</span>" +
      "</div>";
  });
  if (!bindingRowsHtml) bindingRowsHtml = "<div class=\"settings-binding-empty\">加载中...</div>";

  container.innerHTML =
    // ── 服务连接
    "<div class=\"xt-section-h\">服务状态</div>" +
    "<div style=\"padding: 0 16px;\">" +
      "<div class=\"xt-card\" style=\"padding: 16px;\">" +
        "<div class=\"settings-provider-row\">" +
          "<div>" +
            "<div class=\"settings-provider-name\">语音与整理服务</div>" +
            (providerDetail ? "<div class=\"settings-provider-detail\">" + escHtml(providerDetail) + "</div>" : "") +
          "</div>" +
          "<span class=\"settings-status-pill settings-status-pill-" + pillTone + "\">" +
            "<span class=\"settings-status-dot " + providerDotClass + "\"></span>" +
            escHtml(providerLabel) +
          "</span>" +
        "</div>" +
        "<div class=\"settings-hairline\"></div>" +
        "<div class=\"settings-quota-label\">" +
          "<span>本月剩余额度</span>" +
          "<span class=\"settings-quota-pct\">" + quotaDisplay + "</span>" +
        "</div>" +
        "<div class=\"settings-quota-track\" style=\"margin-top: 8px;\">" +
          "<div class=\"settings-quota-fill\" style=\"width:" + Math.round(quotaPct * 100) + "%;background:" + quotaBarColor + ";\"></div>" +
        "</div>" +
      "</div>" +
    "</div>" +

    // ── 声线绑定
    "<div class=\"xt-section-h\">声线配置</div>" +
    "<div style=\"padding: 0 16px;\">" +
      "<div class=\"xt-card\" style=\"padding: 16px;\">" +
        "<div class=\"settings-provider-row\" style=\"margin-bottom: 12px;\">" +
          "<div class=\"settings-provider-name\">声线配置状态</div>" +
          "<span style=\"font-size: 12px; color: var(--xt-text-3);\">" + boundCount + " / " + totalVoices + " 已绑定</span>" +
        "</div>" +
        "<div class=\"settings-binding-list\">" + bindingRowsHtml + "</div>" +
        "<button class=\"ghost-button settings-voice-bind-btn\" type=\"button\" onclick=\"window.location.href='/h5/admin-voice-bindings.html'\">" +
          "打开声线配置页" +
        "</button>" +
      "</div>" +
    "</div>" +

    // ── 云同步（即将开放）
    "<div class=\"xt-section-h\">云同步 · 即将开放</div>" +
    "<div style=\"padding: 0 16px;\">" +
      "<div class=\"settings-sync-card\">" +
        "<div class=\"settings-provider-row\">" +
          "<span class=\"settings-provider-name\" style=\"opacity: 0.7;\">多设备同步</span>" +
          "<span class=\"xt-pill\" style=\"font-size: 10px; padding: 3px 8px;\">之后开放</span>" +
        "</div>" +
        "<div class=\"settings-provider-detail\" style=\"margin-top: 6px; opacity: 0.7;\">" +
          "信笺会在你自己的设备之间安静地同步，不会被任何人读到。" +
        "</div>" +
      "</div>" +
    "</div>" +

    // ── 本地数据
    "<div class=\"xt-section-h\">信笺保存</div>" +
    "<div style=\"padding: 0 16px;\">" +
      "<div class=\"xt-card\" style=\"padding: 0; overflow: hidden;\">" +
        "<div class=\"settings-data-row\" style=\"border-bottom: 1px solid var(--xt-hairline);\">" +
          "<span>已保存信笺</span>" +
          "<span style=\"font-family: var(--xt-mono); font-size: 12px; color: var(--xt-text-3);\">" + lettersCount + " 封</span>" +
        "</div>" +
        "<div class=\"settings-data-row\" style=\"border-bottom: 1px solid var(--xt-hairline);\">" +
          "<span style=\"color: var(--xt-text-2);\">保存在当前服务中 · 不会替你发送</span>" +
        "</div>" +
        "<div class=\"settings-data-row\">" +
          "<span style=\"color: var(--xt-text-3); font-size: 12px;\">不会自动发给对方，你可以随时回来查看</span>" +
        "</div>" +
      "</div>" +
    "</div>" +

    // ── 版本
    "<div class=\"settings-version\">想Ta了 · v0.1 · 信笺保存已开启</div>";
}

async function refreshSettingsStatus() {
  // Reload bootstrap for provider status
  const response = await apiFetch("/api/xiangta/bootstrap");
  if (response) {
    state.bootstrap = response.data;
  }
  // Reload voice binding status
  await loadVoiceBindingStatus();
  // Reload letters count
  const lettersResp = await apiFetch("/api/xiangta/letters?limit=1&offset=0");
  if (lettersResp) {
    state.letters = lettersResp.data?.letters || [];
  }
  renderSettingsScreen();
}

// ─── Letter Detail Screen ─────────────────────────────────────

function openLetterDetail(letterId) {
  const letter = (state.letters || []).find(function(item) {
    return (item.id || item.letterId) === letterId;
  });
  if (!letter) {
    showToast("没有找到这封信笺");
    return;
  }
  state.activeLetterDetailId = letterId;
  state.activeLetterDetail = letter;
  // Initialize favorite map from letter.favorited
  state.letterDetailFavoritedMap[letterId] = !!letter.favorited;
  renderLetterDetailScreen(letter);
  showScreen("letterDetail");
}

function renderLetterDetailMetaPills(letter) {
  const pillsEl = el("letterDetailMetaPills");
  if (!pillsEl || !letter) return;
  const recipientLabel = getBootstrapRecipientLabel(letter.recipient) || RECIPIENT_META[letter.recipient]?.label || "";
  const sceneLabel = getBootstrapSceneLabel(letter.scene) || SCENE_META[letter.scene]?.label || "";
  const styleLabel = letter.style ? (STYLE_LABELS[letter.style] || getBootstrapToneLabel(letter.style)) : "";
  const voiceLabel = letter.voicePreset ? getBootstrapVoiceLabel(letter.voicePreset) : "";
  const toneLabel = letter.tone ? getBootstrapToneLabel(letter.tone) : "";
  const isFavorited = !!(state.letterDetailFavoritedMap[letter.id || letter.letterId]);
  const parts = [
    { text: "给" + recipientLabel, accent: true },
    { text: sceneLabel, accent: false },
    { text: styleLabel, accent: false },
    { text: voiceLabel, accent: false },
    { text: toneLabel, accent: false },
  ].filter(function(p) { return p.text; });
  if (isFavorited) {
    parts.push({ text: "★ 收藏", accent: false, favorited: true });
  }
  pillsEl.innerHTML = parts.map(function(p) {
    var cls = "letter-meta-pill" + (p.accent ? " letter-meta-pill-accent" : "") + (p.favorited ? " letter-meta-pill-favorited" : "");
    return "<span class=\"" + cls + "\">" + escHtml(p.text) + "</span>";
  }).join("");
  updateLetterDetailFavoriteSeal(isFavorited);
}

function updateLetterDetailFavoriteSeal(favorited) {
  const seal = document.querySelector("#screenLetterDetail .letter-detail-seal");
  if (!seal) return;
  seal.classList.toggle("favorited", !!favorited);
}

function renderLetterDetailScreen(letter) {
  // Title in appbar
  const titleEl = el("letterDetailTitle");
  if (titleEl) {
    titleEl.textContent = letter.title || "今晚的信笺";
  }

  // Subtitle: recipient · scene
  const recipientLabel = getBootstrapRecipientLabel(letter.recipient) || RECIPIENT_META[letter.recipient]?.label || "";
  const sceneLabel = getBootstrapSceneLabel(letter.scene) || SCENE_META[letter.scene]?.label || "";
  const subtitle = [recipientLabel, sceneLabel].filter(Boolean).join(" · ") || "—";
  const subtitleEl = el("letterDetailSubtitle");
  if (subtitleEl) subtitleEl.textContent = subtitle;

  renderLetterDetailMetaPills(letter);

  // Date with separator line
  const dateRowEl = el("letterDetailDate");
  if (dateRowEl) {
    if (letter.createdAt) {
      const d = new Date(letter.createdAt);
      dateRowEl.textContent =
        String(d.getFullYear()) + " · " +
        String(d.getMonth() + 1).padStart(2, "0") + " · " +
        String(d.getDate()).padStart(2, "0") + " · " +
        String(d.getHours()).padStart(2, "0") + ":" +
        String(d.getMinutes()).padStart(2, "0");
    } else {
      dateRowEl.textContent = "";
    }
  }

  // Body — break at Chinese punctuation like prototype
  const bodyEl = el("letterDetailBody");
  renderLetterBodyLines(bodyEl, letter.finalText || "");

  // Signature
  const sigEl = el("letterDetailSignature");
  if (sigEl) {
    if (letter.createdAt) {
      const d = new Date(letter.createdAt);
      const period = (d.getHours() >= 18 || d.getHours() < 5) ? "今晚" : "今天";
      sigEl.textContent = "—— 写于" + period;
    } else {
      sigEl.textContent = "—— 写于信笺夹";
    }
  }

  // Audio section
  const audioSection = el("letterDetailAudioSection");
  const emptyAudio = el("letterDetailEmptyAudio");
  const audio = el("letterDetailAudio");

  if (letter.audioUrl) {
    if (audioSection) audioSection.classList.remove("hidden");
    if (emptyAudio) emptyAudio.classList.add("hidden");
    if (audio) {
      audio.src = normalizePlayableAudioUrl(letter.audioUrl || "");
      audio.load();
    }
    // Voice name and time
    const voiceEl = el("letterDetailVoiceName");
    if (voiceEl) {
      voiceEl.textContent = letter.voiceLabel || getBootstrapVoiceLabel(letter.voicePreset) || "未知声音";
    }
    const timeEl = el("letterDetailAudioTime");
    if (timeEl) {
      timeEl.textContent = letter.durationSecs ? formatDuration(letter.durationSecs) : "--:--";
    }
  } else {
    if (audioSection) audioSection.classList.add("hidden");
    if (emptyAudio) emptyAudio.classList.remove("hidden");
  }

  // Favorite button
  renderLetterDetailFavoriteButton();
}

function renderLetterDetailFavoriteButton() {
  const letterId = state.activeLetterDetailId;
  const isFavorited = state.letterDetailFavoritedMap[letterId] || false;
  const labelEl = el("letterDetailFavoriteLabel");
  const btn = el("btnLetterDetailFavorite");
  if (labelEl) {
    labelEl.textContent = isFavorited ? "已收藏" : "加入收藏";
  }
  if (btn) {
    if (isFavorited) {
      btn.classList.add("favorited");
    } else {
      btn.classList.remove("favorited");
    }
  }
}

async function toggleLetterDetailFavorite() {
  const letterId = state.activeLetterDetailId;
  if (!letterId) return;
  const newValue = !state.letterDetailFavoritedMap[letterId];

  // Optimistic update
  state.letterDetailFavoritedMap[letterId] = newValue;
  var letters = state.letters || [];
  for (var i = 0; i < letters.length; i++) {
    var item = letters[i];
    if ((item.id || item.letterId) === letterId) {
      item.favorited = newValue;
      break;
    }
  }
  if (state.activeLetterDetail) state.activeLetterDetail.favorited = newValue;
  renderLetterDetailFavoriteButton();
  renderLetterDetailMetaPills(state.activeLetterDetail);
  if (typeof renderHistoryFilterChips === "function") renderHistoryFilterChips();
  if (typeof renderLetters === "function") renderLetters();
  showToast(newValue ? "已收藏" : "已取消收藏");

  // Persist to backend
  var response = await apiFetch("/api/xiangta/letters/" + encodeURIComponent(letterId) + "/favorite", {
    method: "PATCH",
    body: JSON.stringify({ favorited: newValue }),
  });
  if (!response) {
    showToast("收藏更新失败，请稍后重试");
    // Restore on failure
    state.letterDetailFavoritedMap[letterId] = !newValue;
    for (var j = 0; j < letters.length; j++) {
      var it = letters[j];
      if ((it.id || it.letterId) === letterId) {
        it.favorited = !newValue;
        break;
      }
    }
    if (state.activeLetterDetail) state.activeLetterDetail.favorited = !newValue;
    renderLetterDetailFavoriteButton();
    renderLetterDetailMetaPills(state.activeLetterDetail);
    if (typeof renderHistoryFilterChips === "function") renderHistoryFilterChips();
    if (typeof renderLetters === "function") renderLetters();
    return;
  }

  // Sync with authoritative server data
  if (response.data) {
    state.letterDetailFavoritedMap[letterId] = !!response.data.favorited;
    for (var k = 0; k < letters.length; k++) {
      var ltr = letters[k];
      if ((ltr.id || ltr.letterId) === letterId) {
        ltr.favorited = !!response.data.favorited;
        break;
      }
    }
    if (state.activeLetterDetail) state.activeLetterDetail.favorited = !!response.data.favorited;
    renderLetterDetailFavoriteButton();
    renderLetterDetailMetaPills(state.activeLetterDetail);
    if (typeof renderHistoryFilterChips === "function") renderHistoryFilterChips();
    if (typeof renderLetters === "function") renderLetters();
  }
}

async function restartLetterDetailAudio() {
  const audio = el("letterDetailAudio");
  if (!audio || !audio.src) {
    showToast("请手动点击播放");
    return;
  }
  audio.currentTime = 0;
  try {
    await audio.play();
  } catch (e) {
    showToast("请手动点击播放");
  }
}

function downloadLetterDetailAudio() {
  const letter = state.activeLetterDetail;
  if (!letter || !letter.audioUrl) {
    showToast("这封信笺没有音频");
    return;
  }
  const a = document.createElement("a");
  a.href = letter.audioUrl;
  a.download = "xiangta-letter.mp3";
  a.target = "_blank";
  a.rel = "noopener";
  a.click();
}

async function copyLetterDetailText() {
  const letter = state.activeLetterDetail;
  if (!letter || !letter.finalText) {
    showToast("没有可复制的文字");
    return;
  }
  const text = letter.finalText;
  try {
    await navigator.clipboard.writeText(text);
    showToast("文字已复制");
    return;
  } catch (e) {
    // Fallback
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      showToast("文字已复制");
    } catch (e2) {
      showToast("复制失败");
    }
    document.body.removeChild(ta);
  }
}

async function shareLetterDetail() {
  const letter = state.activeLetterDetail;
  if (!letter || !letter.finalText) {
    showToast("没有可分享的内容");
    return;
  }
  const text = letter.finalText;
  const shareData = {
    title: "一封信笺",
    text: text,
  };
  if (navigator.share) {
    try {
      await navigator.share(shareData);
      return;
    } catch (e) {
      if (e.name === "AbortError") return;
    }
  }
  // Fallback to copy
  await copyLetterDetailText();
  showToast("系统不支持分享，已复制文字");
}

function retoneLetterDetail() {
  const letter = state.activeLetterDetail;
  if (!letter) return;
  state.finalText = letter.finalText || "";
  if (letter.recipient) state.selectedRecipient = letter.recipient;
  if (letter.scene) state.selectedScene = letter.scene;
  if (letter.voicePreset) state.selectedVoice = letter.voicePreset;
  if (letter.tone) state.selectedTone = letter.tone;
  goVoice();
}

function writeAnotherFromLetterDetail() {
  const letter = state.activeLetterDetail;
  if (!letter) {
    showScreen("home");
    return;
  }
  // Preserve recipient and scene for quick re-compose
  if (letter.recipient) state.selectedRecipient = letter.recipient;
  if (letter.scene) state.selectedScene = letter.scene;
  // Reset all downstream state — no suggestions, no TTS
  state.finalText = "";
  state.suggestions = [];
  state.selectedIndex = -1;
  state.ttsTask = null;
  state.ttsResult = null;
  state.resultSaved = false;
  showScreen("compose");
}

function initKeyboardSafeInset() {
  var docEl = document.documentElement;
  function setKbInset(px) {
    var next = Math.max(0, Number(px) || 0);
    docEl.style.setProperty("--xt-kb", next + "px");
  }

  if (!window.visualViewport) {
    setKbInset(0);
    return;
  }

  function syncFromVisualViewport() {
    var vv = window.visualViewport;
    var viewportBottom = vv.height + vv.offsetTop;
    var keyboardHeight = window.innerHeight - viewportBottom;
    setKbInset(keyboardHeight);
  }

  window.visualViewport.addEventListener("resize", syncFromVisualViewport);
  window.visualViewport.addEventListener("scroll", syncFromVisualViewport);
  syncFromVisualViewport();
}

document.addEventListener("DOMContentLoaded", async () => {
  state.mode = getAppMode();
  initBrowserNavigation();
  initKeyboardSafeInset();
  applyModeUi();
  initOpeningOverlay();
  initComposeListeners();
  renderHomeDateLine();
  renderStepDots("composeStepDots", 0, STEP_LABELS);
  renderStepDots("suggestStepDots", 1, STEP_LABELS);
  renderStepDots("voiceStepDots", 2, STEP_LABELS);
  await loadBootstrap();
});
