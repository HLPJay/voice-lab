"use strict";

const API_BASE = "";
const STEP_LABELS = ["整理想法", "挑选表达", "生成语音"];
const PLACEHOLDER_PROFILE = "<coreProfileIdFromCoreProfiles>";

const RECIPIENT_META = {
  lover: {
    label: "恋人",
    hint: "想他 / 想她",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><circle cx="9.5" cy="13" r="5.5" stroke="currentColor" stroke-width="1.2" opacity="0.6"></circle><circle cx="16.5" cy="13" r="5.5" stroke="currentColor" stroke-width="1.2"></circle><circle cx="13" cy="13" r="1.1" fill="currentColor"></circle></svg>',
  },
  family: {
    label: "父母",
    hint: "爸爸 / 妈妈",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><path d="M4 21v-9.2L13 5l9 6.8V21" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"></path><path d="M10 21v-5h6v5" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"></path></svg>',
  },
  friend: {
    label: "朋友",
    hint: "老朋友 / 新朋友",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><path d="M7 18v-2.2A3.8 3.8 0 0110.8 12h4.4A3.8 3.8 0 0119 15.8V18M10 10.5a2.5 2.5 0 105 0 2.5 2.5 0 00-5 0z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"></path></svg>',
  },
  self: {
    label: "自己",
    hint: "写给自己",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><circle cx="13" cy="13" r="8.5" stroke="currentColor" stroke-width="1.2" opacity="0.58"></circle><circle cx="13" cy="13" r="2.4" fill="currentColor"></circle></svg>',
  },
};

const SCENE_META = {
  miss: { label: "想念", hint: "不知不觉就想起你" },
  sorry: { label: "道歉", hint: "那天，是我不好" },
  thanks: { label: "感谢", hint: "一直没有好好说" },
  comfort: { label: "安慰", hint: "陪你一会儿" },
  night: { label: "晚安", hint: "睡前的一句话" },
};

const RAW_EXAMPLES = {
  miss: "今天下雨了，我突然想起你。那天一起淋雨的时候，其实我心里很安静，也很想靠近你。",
  sorry: "昨天那句话我说重了。后来我一直在想，我不是想伤害你，只是当时没处理好自己的情绪。",
  thanks: "那天你没有问太多，就一直在我身边。后来我想了很久，还是想认真跟你说一声谢谢。",
  comfort: "如果你今天很累，就先不用解释。想说的时候我会听，不想说也没有关系。",
  night: "今天先到这里吧。别再想工作和烦心事了，先把自己交给夜晚，好好睡一觉。",
};

const GUIDANCE_PROMPTS = {
  miss: [
    "你希望 Ta 听完之后，感受到什么？",
    "有没有不想说得太重、太直接的部分？",
    "你们上一次好好说话，是什么时候？",
  ],
  sorry: [
    "你想为哪件事认真道歉？",
    "你希望对方知道，你看到了哪些做得不好的地方？",
    "你不想把这段话说成找借口，最该避开的是什么？",
  ],
  thanks: [
    "你最想感谢的是哪一个细节？",
    "那件事对你来说，到底意味着什么？",
    "有没有一直没说出口的那一句谢谢？",
  ],
  comfort: [
    "对方现在在经历什么？",
    "你想让对方感受到被怎样接住？",
    "有什么是你不想说成说教的？",
  ],
  night: [
    "今天的晚安里，你最想留下什么感觉？",
    "有没有一句话是想让对方放松下来的？",
    "今晚不说重话的话，你会怎么收尾？",
  ],
};

const STYLE_LABELS = {
  restrained: "克制版",
  gentle: "温柔版",
  sincere: "真诚版",
};

const TONE_META = [
  { id: "restrained", label: "克制" },
  { id: "gentle", label: "温柔" },
  { id: "sincere", label: "真诚" },
  { id: "whisper", label: "轻声" },
  { id: "bedtime", label: "睡前" },
];

const state = {
  mode: "formal",
  screen: "home",
  bootstrap: null,
  selectedRecipient: null,
  selectedScene: null,
  suggestions: [],
  selectedIndex: -1,
  selectedStyle: "gentle",
  selectedVoice: "female-gentle",
  selectedTone: "gentle",
  finalText: "",
  ttsTask: null,
  ttsResult: null,
  letters: [],
  coreProfiles: [],
};

function el(id) {
  return document.getElementById(id);
}

function escHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getAppMode() {
  const params = new URLSearchParams(window.location.search || "");
  return params.get("mode") === "dev" ? "dev" : "formal";
}

function applyModeUi() {
  const isDev = state.mode === "dev";
  const devPanel = el("devPanel");
  const devTtsSection = el("devTtsSection");
  if (devPanel) devPanel.classList.toggle("hidden", !isDev);
  if (devTtsSection) devTtsSection.classList.toggle("hidden", !isDev);
  document.body.setAttribute("data-mode", state.mode);
}

function showScreen(screen) {
  document.querySelectorAll(".screen").forEach((node) => node.classList.remove("active"));
  const target = el("screen" + screen.charAt(0).toUpperCase() + screen.slice(1));
  if (target) target.classList.add("active");
  state.screen = screen;
  const topbar = el("appTopbar");
  if (topbar) topbar.style.display = screen === "home" ? "" : "none";
  if (screen === "history") loadLetters();
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

async function apiFetch(path, options) {
  setStatus("正在请求...", "loading");
  try {
    const response = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const body = await response.json();
    if (!response.ok || body.ok === false) {
      const message = body.message || body.errorKind || body.detail || ("HTTP " + response.status);
      setStatus("请求失败：" + message, "error");
      showToast(message);
      return null;
    }
    setStatus("已更新", "ok");
    return body;
  } catch (error) {
    setStatus("网络错误：" + error.message, "error");
    showToast("网络错误，请稍后再试");
    return null;
  }
}

function renderLiteraryGreeting() {
  const node = el("literaryGreeting");
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
  node.textContent = `${now.getMonth() + 1} / ${now.getDate()} · ${weekdays[now.getDay()]} · ${period} · ${hour}:${minute}`;
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

function getBootstrapRecipientLabel(recipientId) {
  const recipients = state.bootstrap?.recipients || [];
  const found = recipients.find((item) => item.id === recipientId);
  return found?.label || RECIPIENT_META[recipientId]?.label || "";
}

function getBootstrapSceneLabel(sceneId) {
  const scenes = state.bootstrap?.scenes || [];
  const found = scenes.find((item) => item.id === sceneId);
  return found?.label || SCENE_META[sceneId]?.label || "";
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
  if (!response) return;
  state.bootstrap = response.data;
  renderRecipientGrid(state.bootstrap.recipients || []);
  renderSceneGrid(state.bootstrap.scenes || []);
  state.selectedVoice = state.bootstrap.voicePresets?.[0]?.id || state.selectedVoice;
  state.selectedTone = state.bootstrap.tonePresets?.find((tone) => tone.id === "gentle")?.id || state.bootstrap.tonePresets?.[0]?.id || state.selectedTone;
  renderStatusPill(state.bootstrap.providerStatus);
  renderProviderStatus(state.bootstrap.providerStatus);
  updateHomeStartButton();
  if (state.mode === "dev") {
    await loadCoreProfiles();
  }
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
      const merged = `${textarea.value.trim()}\n\n${prompt}\n`.trim();
      textarea.value = merged.slice(0, 500);
      updateComposeState();
      textarea.focus();
    });
    node.appendChild(card);
  });
}

function updateComposeState() {
  const textarea = el("rawTextArea");
  if (!textarea) return;
  const value = textarea.value || "";
  const count = el("rawTextCount");
  const wrap = el("rawTextWrap");
  const button = el("btnGenSuggestions");
  const hint = el("composeCTAHint");
  if (count) count.textContent = String(value.length);
  if (wrap) wrap.classList.toggle("has-text", value.trim().length > 0);
  if (button) button.disabled = value.trim().length < 4;
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
    return data.suggestions.map((item, index) => ({
      text: item.text || "",
      style: item.style || ["restrained", "gentle", "sincere"][index] || "gentle",
      styleLabel: item.styleLabel || STYLE_LABELS[item.style] || `版本 ${index + 1}`,
      fitsFor: item.fitsFor || "适合想把话说得更稳一些的时候",
      charCount: item.charCount || (item.text || "").length,
    }));
  }
  return [];
}

function renderSuggestionCards(meta) {
  const insight = el("aiUnderstanding");
  const list = el("suggestionsArea");
  if (!list || !insight) return;
  insight.innerHTML =
    `<div class="insight-label">我读到的是</div>` +
    `<div class="insight-summary">${escHtml(meta.summary || "你想把没说完的话，说得更稳一些。")}</div>` +
    '<div class="insight-divider"></div>' +
    `<div class="insight-intent">表达目标 · ${escHtml(meta.intent || "更贴近关系，也更贴近你")}</div>`;
  list.innerHTML = "";
  state.suggestions.forEach((item, index) => {
    const selected = state.selectedIndex === index;
    const card = document.createElement("button");
    card.type = "button";
    card.className = "suggestion-card" + (selected ? " selected" : "");
    card.innerHTML =
      '<div class="suggestion-meta">' +
      `<span class="suggestion-style">${escHtml(item.styleLabel)}</span>` +
      `<span class="suggestion-count">${item.charCount} 字</span>` +
      "</div>" +
      `<div class="suggestion-text">${escHtml(item.text)}</div>` +
      `<div class="suggestion-fit">适合：${escHtml(item.fitsFor)}</div>` +
      '<div class="suggestion-actions"><span class="expr-select-btn">' + (selected ? "已选择" : "选这条") + "</span></div>";
    card.addEventListener("click", () => selectSuggestion(index));
    list.appendChild(card);
  });
}

async function generateSuggestions() {
  const rawText = (el("rawTextArea")?.value || "").trim();
  if (rawText.length < 4) {
    setStatus("先写下至少 4 个字", "warn");
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
  });
  setBusy("btnGenSuggestions", false, "帮我整理表达");
  if (!response) return;
  state.suggestions = buildSuggestionViewModel(response.data);
  state.selectedIndex = -1;
  state.finalText = "";
  state.selectedStyle = "gentle";
  el("suggestSubtitle").textContent = `${getBootstrapSceneLabel(state.selectedScene)} · 给${getBootstrapRecipientLabel(state.selectedRecipient)}`;
  renderStepDots("suggestStepDots", 1, STEP_LABELS);
  renderSuggestionCards(response.data);
  renderRiskHint("suggestRiskHint", rawText);
  setBusy("btnToVoice", false, "用这条 · 生成语音");
  el("btnToVoice").disabled = true;
  showScreen("suggest");
}

function selectSuggestion(index) {
  state.selectedIndex = index;
  const suggestion = state.suggestions[index];
  if (!suggestion) return;
  state.finalText = suggestion.text;
  state.selectedStyle = suggestion.style;
  el("finalTextArea").value = suggestion.text;
  renderSuggestionCards({ summary: "你已经选中一个更接近此刻心情的版本。", intent: "下一步可以直接进入语音生成。" });
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
  node.innerHTML =
    '<div class="voice-copy-meta">' +
    `<span class="voice-copy-tag">${escHtml(getBootstrapSceneLabel(state.selectedScene))} · ${escHtml(STYLE_LABELS[state.selectedStyle] || "温柔版")}</span>` +
    '<button class="voice-copy-edit" type="button" onclick="showScreen(\'suggest\')">返回改字</button>' +
    "</div>" +
    `<div class="voice-copy-text">${escHtml(state.finalText)}</div>`;
}

function renderVoicePicker() {
  const node = el("voicePicker");
  if (!node) return;
  node.innerHTML = "";
  buildVoiceOptions().forEach((voice) => {
    const selected = voice.id === state.selectedVoice;
    const option = document.createElement("button");
    option.type = "button";
    option.className = "voice-option" + (selected ? " selected" : "");
    option.innerHTML =
      '<span class="voice-wave"><span class="voice-wave-bar" style="height:12px"></span><span class="voice-wave-bar" style="height:18px"></span><span class="voice-wave-bar" style="height:10px"></span><span class="voice-wave-bar" style="height:20px"></span><span class="voice-wave-bar" style="height:14px"></span></span>' +
      '<span class="voice-option-info">' +
      `<span class="voice-option-name">${escHtml(voice.name)}</span>` +
      `<span class="voice-option-desc">${escHtml(voice.desc)}</span>` +
      "</span>" +
      `<span class="voice-option-check">${selected ? "✓" : ""}</span>`;
    option.addEventListener("click", () => {
      state.selectedVoice = voice.id;
      renderVoicePicker();
    });
    node.appendChild(option);
  });
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
  node.textContent = `预计时长 · ${min}:${sec}`;
}

function goVoice() {
  if (!state.finalText) {
    setStatus("先选一条最像你的表达", "warn");
    return;
  }
  renderStepDots("voiceStepDots", 2, STEP_LABELS);
  el("voiceSubtitle").textContent = `${getBootstrapSceneLabel(state.selectedScene)} · ${STYLE_LABELS[state.selectedStyle] || "温柔版"}`;
  state.ttsTask = null;
  state.ttsResult = null;
  el("ttsResult").classList.add("hidden");
  el("saveLetterSection").classList.add("hidden");
  renderVoiceTextPreview();
  renderVoicePicker();
  renderToneChips();
  renderDurationEstimate();
  showScreen("voice");
}

async function generateTtsTask() {
  const text = state.finalText || (el("finalTextArea")?.value || "").trim();
  if (!text) {
    setStatus("先确认要生成语音的文字", "warn");
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
  setBusy("btnGenTtsTask", true, "生成中...");
  const response = await apiFetch("/api/xiangta/tts/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!response) {
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }
  state.ttsTask = response.data;
  await pollTtsTask(response.data);
}

async function pollTtsTask(task) {
  if (!task) return;
  const status = task.status;
  const pollUrl = task.pollUrl || `/api/xiangta/tts/tasks/${task.taskId}`;
  if (status === "completed" || status === "failed") {
    renderTtsTask(task);
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }
  setBusy("btnGenTtsTask", true, `生成中...（${status}）`);
  const response = await apiFetch(pollUrl);
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
    window.setTimeout(() => pollTtsTask(updated), 1500);
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
  div.classList.remove("hidden");
  div.innerHTML = "";
  const badgeClass = result.status === "completed" ? "completed" : (result.status === "failed" ? "failed" : "");
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
    html += `<div class="tts-audio"><audio controls preload="none" src="${escHtml(result.audioUrl)}"></audio></div>`;
  } else {
    html += '<div class="tts-hint">语音暂未生成，可先保存文字信笺。</div>';
  }
  html += "</div>";
  div.innerHTML = html;
  revealSaveLetterSection();
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
  if (!state.finalText) {
    setStatus("没有可保存的文字", "warn");
    return;
  }
  setBusy("btnSaveLetter", true, "保存中...");
  const suggestion = state.suggestions[state.selectedIndex];
  const audioUrl = state.ttsResult ? (state.ttsResult.audioUrl || null) : null;
  const durationMs = state.ttsResult ? (state.ttsResult.durationMs || null) : null;
  const response = await apiFetch("/api/xiangta/letters", {
    method: "POST",
    body: JSON.stringify({
      recipient: state.selectedRecipient,
      scene: state.selectedScene,
      style: suggestion?.style || state.selectedStyle || "gentle",
      rawText: (el("rawTextArea")?.value || "").trim(),
      finalText: state.finalText,
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
  setBusy("btnRefreshHistory", true);
  const response = await apiFetch("/api/xiangta/letters?limit=20&offset=0");
  setBusy("btnRefreshHistory", false);
  if (!response) return;
  state.letters = response.data.letters || [];
  renderLetters(response.data);
}

function renderLetters(data) {
  const count = el("historyCount");
  const list = el("lettersArea");
  if (!list) return;
  const letters = data.letters || [];
  if (count) {
    count.textContent = letters.length > 0 ? `${data.total} 封 · 本机保存` : "";
  }
  if (letters.length === 0) {
    list.innerHTML = '<div class="empty-state">还没有留下任何信笺。<br>当你写下第一段想说的话，它就会出现在这里。</div>';
    return;
  }
  list.innerHTML = "";
  letters.forEach((letter) => {
    const card = document.createElement("article");
    card.className = "history-card";
    const title = letter.title || `${getBootstrapSceneLabel(letter.scene) || letter.scene} · 给${getBootstrapRecipientLabel(letter.recipient) || letter.recipient}`;
    const preview = (letter.finalText || "").slice(0, 76);
    card.innerHTML =
      '<div class="history-card-head">' +
      `<div class="history-card-title">${escHtml(title)}</div>` +
      `<div class="history-card-date">${escHtml(formatLetterDate(letter.createdAt))}</div>` +
      "</div>" +
      `<div class="history-card-meta">${escHtml(getBootstrapRecipientLabel(letter.recipient) || letter.recipient)} · ${escHtml(getBootstrapSceneLabel(letter.scene) || letter.scene)}${letter.audioUrl ? " · 含语音" : " · 仅文字"}</div>` +
      `<div class="history-card-body">${escHtml(preview)}${(letter.finalText || "").length > preview.length ? "..." : ""}</div>`;
    if (letter.audioUrl) {
      card.innerHTML += `<div class="history-card-audio"><audio controls preload="none" src="${escHtml(letter.audioUrl)}"></audio></div>`;
    }
    list.appendChild(card);
  });
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
  const example = RAW_EXAMPLES[state.selectedScene] || RAW_EXAMPLES.miss || "";
  if (!example) return;
  const current = (textarea.value || "").trim();
  if (current.length === 0) {
    textarea.value = example;
  } else if (!current.includes(example)) {
    textarea.value = (current + "\n\n" + example).slice(0, 500);
  }
  updateComposeState();
  textarea.focus();
  showToast("已放入一个例子，可以直接改成你的话");
}

document.addEventListener("DOMContentLoaded", async () => {
  state.mode = getAppMode();
  applyModeUi();
  initComposeListeners();
  renderLiteraryGreeting();
  renderStepDots("composeStepDots", 0, STEP_LABELS);
  renderStepDots("suggestStepDots", 1, STEP_LABELS);
  renderStepDots("voiceStepDots", 2, STEP_LABELS);
  await loadBootstrap();
});
