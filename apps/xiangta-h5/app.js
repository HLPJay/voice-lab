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

// Full-flow examples: when user clicks "用一个例子开始"，pre-fill entire 3-step flow
const FLOW_EXAMPLES = {
  miss: {
    recipient: "lover",
    scene: "miss",
    rawText: "今天下雨了，我突然想起你。那天一起淋雨的时候，其实我心里很安静，也很想靠近你。",
    preferredStyle: "gentle",
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "雨天的想念",
    sampleGoal: "把模糊的想念说成一句温柔的话",
  },
  sorry: {
    recipient: "lover",
    scene: "sorry",
    rawText: "昨天那句话我说重了。后来我一直在想，我不是想伤害你，只是当时没处理好自己的情绪。",
    preferredStyle: "sincere",
    preferredVoice: "male-gentle",
    preferredTone: "sincere",
    title: "认真的道歉",
    sampleGoal: "把道歉说成更真诚、更清楚的一句",
  },
  thanks: {
    recipient: "friend",
    scene: "thanks",
    rawText: "那天你没有问太多，就一直在我身边。后来我想了很久，还是想认真跟你说一声谢谢。",
    preferredStyle: "gentle",
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "一句迟到的谢谢",
    sampleGoal: "把感谢说成温暖的陪伴",
  },
  comfort: {
    recipient: "friend",
    scene: "comfort",
    rawText: "如果你今天很累，就先不用解释。想说的时候我会听，不想说也没有关系。",
    preferredStyle: "restrained",
    preferredVoice: "male-gentle",
    preferredTone: "restrained",
    title: "陪你一会儿",
    sampleGoal: "把安慰说成不带压力的陪伴",
  },
  night: {
    recipient: "lover",
    scene: "night",
    rawText: "今天先到这里吧。别再想工作和烦心的事了，先把自己交给夜晚，好好睡一觉。",
    preferredStyle: "gentle",
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "今晚，说晚安",
    sampleGoal: "把晚安说成温柔的结束语",
  },
};

const state = {
  mode: "formal",
  screen: "home",
  bootstrap: null,
  selectedRecipient: null,
  selectedScene: null,
  suggestions: [],
  suggestionMeta: null,
  selectedIndex: -1,
  selectedStyle: "gentle",
  selectedVoice: "female-gentle",
  selectedTone: "gentle",
  finalText: "",
  ttsTask: null,
  ttsResult: null,
  letters: [],
  coreProfiles: [],
  voiceBindingStatus: null,  // loaded from GET /voice-bindings/status
  resultSaved: false,
  // History page state
  historyFilter: "all",
  historySearchOpen: false,
  historySearchQuery: "",
  activeHistoryLetterId: null,
  historyAudioPlaying: false,
  historyAudioCurrentTime: 0,
  historyAudioDuration: 0,
  // Letter detail state
  activeLetterDetailId: null,
  activeLetterDetail: null,
  letterDetailFavoritedMap: {},
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

// Normalize Chinese emotional copy text:
// 1. Clean duplicate punctuation: 。。→。， ！！→！，？？→？，，→，
// 2. Split into readable paragraphs (1-2 sentences each, max 3 paragraphs)
function normalizeCopyText(text) {
  if (!text) return text;
  // Step 1: clean duplicate punctuation
  let result = text;
  result = result.replace(/。。/g, "。");
  result = result.replace(/！！/g, "！");
  result = result.replace(/？？/g, "？");
  result = result.replace(/，，/g, "，");
  result = result.replace(/、、/g, "、");
  // Step 2: paragraph splitting
  const sentences = [];
  let current = "";
  for (let i = 0; i < result.length; i++) {
    const ch = result[i];
    if ("。！？".includes(ch)) {
      current += ch;
      sentences.push(current);
      current = "";
    } else if (ch === "\n" || ch === "\r") {
      if (current) {
        sentences.push(current);
        current = "";
      }
    } else {
      current += ch;
    }
  }
  if (current) sentences.push(current);
  // Group into paragraphs: 1-2 sentences each, max 3 paragraphs
  const paragraphs = [];
  for (let i = 0; i < sentences.length; i += 2) {
    const chunk = sentences.slice(i, i + 2).join("");
    if (chunk.trim()) paragraphs.push(chunk.trim());
  }
  return paragraphs.slice(0, 3).join("\n");
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
  if (screen === "history") {
    setupHistoryScreen();
    loadLetters();
  }
  if (screen === "settings") {
    renderSettingsScreen();
  }
  if (screen === "result") {
    renderResultScreen();
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
        showScreen("history");
        return;
      }
    } else {
      showToast("没有选择信笺");
      showScreen("history");
      return;
    }
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
    const card = document.createElement("article");
    card.className = "suggestion-card" + (selected ? " selected" : "");
    card.innerHTML =
      '<div class="suggestion-meta">' +
      `<span class="suggestion-style">${escHtml(item.styleLabel)}</span>` +
      `<span class="suggestion-count">${item.charCount} 字</span>` +
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
    card.querySelector('[data-action="copy"]')?.addEventListener("click", (event) => copySuggestion(index, event));
    card.querySelector('[data-action="select"]')?.addEventListener("click", (event) => {
      event.stopPropagation();
      selectSuggestion(index);
    });
    list.appendChild(card);
  });
}

async function copySuggestion(index, event) {
  event?.stopPropagation();
  const suggestion = state.suggestions[index];
  if (!suggestion?.text) {
    showToast("没有可复制的内容");
    return;
  }
  const textToCopy = normalizeCopyText(suggestion.text);
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(textToCopy);
      showToast("已复制");
      return;
    }
  } catch (error) {
    // Fallback below.
  }

  try {
    const area = document.createElement("textarea");
    area.value = textToCopy;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    showToast(ok ? "已复制" : "复制失败，请手动复制");
  } catch (error) {
    showToast("复制失败，请手动复制");
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
  selectSuggestion(index);
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
  state.selectedIndex = index;
  const suggestion = state.suggestions[index];
  if (!suggestion) return;
  const normalizedText = normalizeCopyText(suggestion.text);
  state.finalText = normalizedText;
  state.selectedStyle = suggestion.style;
  el("finalTextArea").value = normalizedText;
  renderSuggestionCards({
    summary: state.suggestionMeta?.summary || "你已经选中一个更接近此刻心情的版本。",
    intent: state.suggestionMeta?.intent || "下一步可以直接进入语音生成。",
  });
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

    option.innerHTML =
      '<span class="voice-wave"><span class="voice-wave-bar" style="height:12px"></span><span class="voice-wave-bar" style="height:18px"></span><span class="voice-wave-bar" style="height:10px"></span><span class="voice-wave-bar" style="height:20px"></span><span class="voice-wave-bar" style="height:14px"></span></span>' +
      '<span class="voice-option-info">' +
      `<span class="voice-option-name">${escHtml(voice.name)}</span>` +
      `<span class="voice-option-desc">${escHtml(voice.desc || "")}</span>` +
      badgeHtml +
      "</span>" +
      `<span class="voice-option-check">${selected ? "✓" : ""}</span>`;
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
  node.textContent = `预计时长 · ${min}:${sec}`;
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
  state.ttsTask = null;
  state.ttsResult = null;
  el("ttsResult").classList.add("hidden");
  el("saveLetterSection").classList.add("hidden");
  renderVoiceTextPreview();
  renderVoicePicker();
  renderToneChips();
  renderDurationEstimate();
  updateGenTtsButton();
  showScreen("voice");
}

async function generateTtsTask() {
  const rawText = state.finalText || (el("finalTextArea")?.value || "").trim();
  const text = normalizeCopyText(rawText);
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
  // Fetch full task detail to ensure we have audioUrl/durationMs before rendering
  const created = response.data;
  const detailed = await fetchTtsTaskDetail(created);
  state.ttsTask = detailed;
  renderTtsTask(detailed);
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

async function pollTtsTask(task) {
  if (!task) return;
  const status = task.status;
  const pollUrl = task.pollUrl || `/api/xiangta/tts/tasks/${task.taskId}`;
  if (status === "completed" || status === "failed") {
    // Completed/failed synchronously — fetch detail to ensure audioUrl is populated
    const detailed = await fetchTtsTaskDetail(task);
    state.ttsTask = detailed;
    renderTtsTask(detailed);
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

  // Success case: navigate to result screen instead of showing inline card
  if (result.status === "completed" && result.audioUrl) {
    state.resultSaved = false;
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
    html += `<div class="tts-audio"><audio controls preload="none" src="${escHtml(result.audioUrl)}"></audio></div>`;
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
function renderResultScreen(result) {
  const finalText = state.finalText || (el("finalTextArea")?.value || "").trim();
  const audioUrl = result.audioUrl || "";
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
  const pillsNode = el("resultMetaPills");
  if (pillsNode) {
    pillsNode.innerHTML =
      `<span class="result-pill active">给${escHtml(recipientLabel)}</span>` +
      `<span class="result-pill">${escHtml(sceneLabel)}</span>` +
      `<span class="result-pill">${escHtml(styleLabel)}</span>`;
  }

  // Render letter date
  const dateNode = el("resultLetterDate");
  if (dateNode) dateNode.textContent = dateStr;

  // Render letter body
  const bodyNode = el("resultLetterBody");
  if (bodyNode) bodyNode.textContent = finalText;

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

function getBootstrapVoiceLabel(voiceId) {
  const presets = state.bootstrap?.voicePresets || [];
  const found = presets.find(p => p.id === voiceId);
  if (found) return found.label;
  // Fallback hardcoded names
  const names = {
    "female-gentle": "温柔女声",
    "male-gentle": "温柔男声",
    "female-bright": "清亮女声",
    "male-mature": "成熟男声",
  };
  return names[voiceId] || "温柔女声";
}

function getBootstrapToneLabel(toneId) {
  const tones = state.bootstrap?.tonePresets || TONE_META;
  const found = tones.find(t => t.id === toneId);
  if (found) return found.label;
  const names = {
    "restrained": "克制",
    "gentle": "温柔",
    "sincere": "真诚",
    "whisper": "轻声",
    "bedtime": "睡前",
  };
  return names[toneId] || "温柔";
}

function updateResultSaveButton() {
  const btn = el("btnResultSave");
  const label = el("resultSaveLabel");
  if (!btn || !label) return;
  if (state.resultSaved) {
    btn.classList.add("saved");
    label.textContent = "查看信笺";
    btn.disabled = false;
    btn.onclick = function() {
      if (state.activeLetterDetailId) {
        openLetterDetail(state.activeLetterDetailId);
      } else {
        showScreen("history");
      }
    };
  } else {
    btn.classList.remove("saved");
    label.textContent = "保存到信笺夹";
    btn.disabled = false;
    btn.onclick = function() { resultSave(); };
  }
}

// Result screen action handlers
function resultGoBack() {
  // Go back to voice screen
  showScreen("voice");
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
  showScreen("voice");
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
    audioUrl: state.ttsResult ? (state.ttsResult.audioUrl || null) : (src.audioUrl || null),
    durationSecs: state.ttsResult ? (state.ttsResult.durationMs ? state.ttsResult.durationMs / 1000 : null) : (src.durationSecs || null),
    title: src.title || null,
    createdAt: src.createdAt || new Date().toISOString(),
    favorited: true,
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

function showResultSaveSealThenOpenDetail(letter) {
  const overlay = el("resultSaveSealOverlay");
  if (!overlay) {
    // Fallback: go directly to detail
    state.activeLetterDetailId = letter.id || letter.letterId;
    state.activeLetterDetail = letter;
    state.letterDetailFavoritedMap[letter.id || letter.letterId] = true;
    showScreen("letterDetail");
    return;
  }
  overlay.classList.remove("hidden");
  overlay.classList.remove("result-save-seal-fadeout");
  // Force reflow
  void overlay.offsetWidth;
  setTimeout(function() {
    overlay.classList.add("result-save-seal-fadeout");
    setTimeout(function() {
      overlay.classList.add("hidden");
      overlay.classList.remove("result-save-seal-fadeout");
      state.activeLetterDetailId = letter.id || letter.letterId;
      state.activeLetterDetail = letter;
      state.letterDetailFavoritedMap[letter.id || letter.letterId] = true;
      showScreen("letterDetail");
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
  setBusy("btnResultSave", true, "保存中...");
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
      finalText: finalText,
      voicePreset: state.selectedVoice || null,
      tone: state.selectedTone || null,
      audioUrl: audioUrl,
      durationSecs: durationMs ? durationMs / 1000 : null,
      title: null,
    }),
  });

  if (!response) {
    setBusy("btnResultSave", false, "保存到信笺夹");
    return;
  }

  state.resultSaved = true;

  const savedLetter = buildSavedLetterViewModel(response);
  upsertLetterIntoState(savedLetter);

  showResultSaveSealThenOpenDetail(savedLetter);
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
  const audioUrl = state.ttsResult ? (state.ttsResult.audioUrl || null) : null;
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
    countNode.textContent = total > 0 ? `${total} 封 · 本机保存，不会上传` : "";
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
      (letter.favorited ? `<span class="prototype-history-card-star active">★</span>` : `<span class="prototype-history-card-star">☆</span>`) +
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
  });

  // Set up mini player with first letter that has audio
  const firstWithAudio = state.letters.find(l => l.audioUrl);
  if (firstWithAudio) {
    setupHistoryMiniPlayer(firstWithAudio);
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
  const metaText = [recipientLabel, sceneLabel, timeStr].filter(Boolean).join(" · ");

  container.innerHTML = `
    <div class="home-recent-card" onclick="showScreen('history')">
      <div class="home-recent-icon ${hasAudio ? 'has-audio' : ''}">
        ${hasAudio
          ? '<svg width=\"14\" height=\"14\" viewBox=\"0 0 14 14\" fill="none"><path d="M3 2l9 5-9 5V2z" fill="currentColor"/></svg>'
          : '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="3" y="4" width="12" height="10" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M3 6l6 4 6-4" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>'}
      </div>
      <div class="home-recent-info">
        <div class="home-recent-title">${escHtml(title)}</div>
        <div class="home-recent-meta">${escHtml(metaText)}</div>
      </div>
      ${hasAudio ? `<div class="home-recent-duration">${formatDuration(Math.round((recent.finalText || "").length * 0.28 + 1.5))}</div>` : ""}
    </div>`;
}

function formatDuration(secs) {
  const s = Math.round(secs);
  const m = Math.floor(s / 60);
  const ss = s % 60;
  return `${m}:${String(ss).padStart(2, "0")}`;
}

function letterTime(timestamp) {
  if (!timestamp) return "";
  const d = new Date(timestamp);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  if (isToday) {
    return `今天 ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) {
    return `昨天 ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
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

function onHistoryCardClick(letter) {
  if (letter.audioUrl) {
    playHistoryLetter(letter.id || letter);
  }
}

// History audio playback
function setupHistoryAudioListeners() {
  const audio = el("historyAudio");
  if (!audio) return;

  // Remove old listeners by cloning
  const newAudio = audio.cloneNode(false);
  audio.parentNode.replaceChild(newAudio, audio);

  newAudio.addEventListener("loadedmetadata", () => {
    state.historyAudioDuration = newAudio.duration;
    renderHistoryMiniPlayer();
  });

  newAudio.addEventListener("timeupdate", () => {
    state.historyAudioCurrentTime = newAudio.currentTime;
    renderHistoryMiniPlayerProgress();
  });

  newAudio.addEventListener("play", () => {
    state.historyAudioPlaying = true;
    updateHistoryPlayIcon(true);
  });

  newAudio.addEventListener("pause", () => {
    state.historyAudioPlaying = false;
    updateHistoryPlayIcon(false);
  });

  newAudio.addEventListener("ended", () => {
    state.historyAudioPlaying = false;
    state.historyAudioCurrentTime = 0;
    updateHistoryPlayIcon(false);
    renderHistoryMiniPlayerProgress();
  });

  newAudio.addEventListener("error", () => {
    state.historyAudioPlaying = false;
    showToast("音频链接暂不可访问");
    hideHistoryMiniPlayer();
  });
}

function playHistoryLetter(letterOrId) {
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

  audio.src = letter.audioUrl;
  state.activeHistoryLetterId = letter.id || letter;
  state.historyAudioPlaying = false;
  state.historyAudioCurrentTime = 0;

  audio.load();
  setupHistoryAudioListeners();

  audio.play().catch(e => {
    showToast("请手动点击播放");
  });

  renderHistoryMiniPlayer(letter);
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

function formatTime(secs) {
  if (!secs || isNaN(secs)) return "0:00";
  const s = Math.round(secs);
  const m = Math.floor(s / 60);
  const ss = s % 60;
  return `${m}:${String(ss).padStart(2, "0")}`;
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

  // Provider status display
  const providerKind = providerStatus?.kind || "unknown";
  const providerLabel = providerStatus?.label || "检查中";
  const providerDetail = providerStatus?.detail || "";
  const providerOk = providerKind === "ok";
  const providerWarn = providerKind === "quota" || providerKind === "degraded" || providerKind === "not_integrated";
  const providerError = providerKind === "error";
  const providerDotClass = providerOk ? "status-dot-ok" : providerWarn ? "status-dot-warn" : providerError ? "status-dot-error" : "status-dot-idle";

  // Voice binding display
  const bindingItems = voiceStatus?.items || [];
  const boundCount = bindingItems.filter(function(item) { return item.bound; }).length;
  const totalVoices = 4;

  // Build voice binding rows
  const voiceNames = {
    "female-gentle": "温柔女声",
    "male-gentle": "温柔男声",
    "female-bright": "明亮女声",
    "male-mature": "成熟男声",
  };
  const voiceOrder = ["female-gentle", "male-gentle", "female-bright", "male-mature"];

  let bindingRowsHtml = "";
  voiceOrder.forEach(function(voiceId) {
    const item = bindingItems.find(function(i) { return i.voicePreset === voiceId; });
    const bound = item?.bound || false;
    const badgeClass = bound ? "binding-badge-ok" : "binding-badge-warn";
    const badgeText = bound ? "已绑定" : "未绑定";
    const name = voiceNames[voiceId] || voiceId;
    bindingRowsHtml +=
      "<div class=\"settings-binding-row\">" +
        "<span class=\"settings-binding-name\">" + escHtml(name) + "</span>" +
        "<span class=\"settings-binding-badge " + badgeClass + "\">" + badgeText + "</span>" +
      "</div>";
  });

  if (bindingRowsHtml === "") {
    bindingRowsHtml = "<div class=\"settings-binding-empty\">加载中...</div>";
  }

  // Local save note
  const localNoteHtml =
    "<div class=\"settings-card\">" +
      "<div class=\"settings-card-title\">本地保存说明</div>" +
      "<div class=\"settings-card-body\">" +
        "<div class=\"settings-note-row\">" +
          "<svg width=\"14\" height=\"14\" viewBox=\"0 0 14 14\" fill=\"none\"><path d=\"M3 7l3 3 5-6\" stroke=\"currentColor\" stroke-width=\"1.4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>" +
          "<span>本机保存，不替你发送</span>" +
        "</div>" +
        "<div class=\"settings-note-row\">" +
          "<svg width=\"14\" height=\"14\" viewBox=\"0 0 14 14\" fill=\"none\"><path d=\"M3 7l3 3 5-6\" stroke=\"currentColor\" stroke-width=\"1.4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>" +
          "<span>不自动分享给对方</span>" +
        "</div>" +
        "<div class=\"settings-note-row\">" +
          "<svg width=\"14\" height=\"14\" viewBox=\"0 0 14 14\" fill=\"none\"><path d=\"M3 7l3 3 5-6\" stroke=\"currentColor\" stroke-width=\"1.4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>" +
          "<span>信笺仅保存在这台设备</span>" +
        "</div>" +
      "</div>" +
    "</div>";

  // Quota percentage for progress bar
  const quotaPct = providerStatus?.quotaPct ?? 1;
  const quotaDisplay = providerKind === "quota" ? "不足" : providerKind === "no_provider" ? "—" : Math.round(quotaPct * 100) + "%";
  const quotaBarColor = providerKind === "quota" ? "var(--warn)" : providerKind === "error" ? "var(--danger)" : "var(--xt-accent)";

  container.innerHTML =
    // Status overview cards
    "<div class=\"settings-status-grid\">" +
      "<div class=\"settings-status-card\">" +
        "<div class=\"settings-status-label\">文案生成</div>" +
        "<div class=\"settings-status-value\">" +
          "<span class=\"settings-status-dot " + providerDotClass + "\"></span>" +
          escHtml(providerLabel) +
        "</div>" +
        providerDetail ? "<div class=\"settings-status-detail\">" + escHtml(providerDetail) + "</div>" : "" +
      "</div>" +
      "<div class=\"settings-status-card\">" +
        "<div class=\"settings-status-label\">声音绑定</div>" +
        "<div class=\"settings-status-value\">" +
          boundCount + " / " + totalVoices + " 已绑定" +
        "</div>" +
      "</div>" +
      "<div class=\"settings-status-card\">" +
        "<div class=\"settings-status-label\">本地信笺</div>" +
        "<div class=\"settings-status-value\">" + lettersCount + " 封</div>" +
      "</div>" +
    "</div>" +

    // Quota progress bar (prototype parity)
    "<div class=\"settings-quota-bar\">" +
      "<div class=\"settings-quota-label\">" +
        "<span>本月剩余额度</span>" +
        "<span class=\"settings-quota-pct\">" + quotaDisplay + "</span>" +
      "</div>" +
      "<div class=\"settings-quota-track\">" +
        "<div class=\"settings-quota-fill\" style=\"width:" + Math.round(quotaPct * 100) + "%;background:" + quotaBarColor + ";\"></div>" +
      "</div>" +
    "</div>" +

    // Voice binding detail
    "<div class=\"settings-card\">" +
      "<div class=\"settings-card-title\">声线绑定状态</div>" +
      "<div class=\"settings-card-subtitle\">选择你最想听到的声音风格</div>" +
      "<div class=\"settings-binding-list\">" + bindingRowsHtml + "</div>" +
      "<button class=\"ghost-button settings-voice-bind-btn\" type=\"button\" onclick=\"window.location.href='/h5/admin-voice-bindings.html'\">" +
        "打开声线绑定配置页" +
      "</button>" +
    "</div>" +

    // Local save note
    localNoteHtml;
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

  // Meta pills — prototype order: 给{recipient}(accent) · {scene} · {styleLabel} · {voiceLabel} · {toneLabel} [+ ★ 收藏]
  const pillsEl = el("letterDetailMetaPills");
  if (pillsEl) {
    const styleLabel = letter.style ? (STYLE_LABELS[letter.style] || getBootstrapToneLabel(letter.style)) : "";
    const voiceLabel = letter.voicePreset ? getBootstrapVoiceLabel(letter.voicePreset) : "";
    const toneLabel = letter.tone ? getBootstrapToneLabel(letter.tone) : "";
    const isFavorited = !!(letter.favorited || state.letterDetailFavoritedMap[letter.id || letter.letterId]);
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
  }

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

  // Body - safe text rendering, preserve line breaks via CSS white-space
  const bodyEl = el("letterDetailBody");
  if (bodyEl) {
    bodyEl.textContent = letter.finalText || "";
  }

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
      audio.src = letter.audioUrl || "";
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

function toggleLetterDetailFavorite() {
  const letterId = state.activeLetterDetailId;
  if (!letterId) return;
  const newValue = !state.letterDetailFavoritedMap[letterId];
  state.letterDetailFavoritedMap[letterId] = newValue;
  // Sync to letter object and activeLetterDetail so history list reflects the change
  const letter = (state.letters || []).find(function(item) {
    return (item.id || item.letterId) === letterId;
  });
  if (letter) letter.favorited = newValue;
  if (state.activeLetterDetail) state.activeLetterDetail.favorited = newValue;
  renderLetterDetailFavoriteButton();
  showToast(newValue ? "已收藏" : "已取消收藏");
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

document.addEventListener("DOMContentLoaded", async () => {
  state.mode = getAppMode();
  applyModeUi();
  initComposeListeners();
  renderHomeDateLine();
  renderStepDots("composeStepDots", 0, STEP_LABELS);
  renderStepDots("suggestStepDots", 1, STEP_LABELS);
  renderStepDots("voiceStepDots", 2, STEP_LABELS);
  await loadBootstrap();
});
