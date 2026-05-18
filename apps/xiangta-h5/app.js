"use strict";

// ── 配置 ──────────────────────────────────────────────────────────────────────

const API_BASE = "";

// ── 应用状态 ──────────────────────────────────────────────────────────────────

const state = {
  mode:            "formal",
  screen:          "home",
  bootstrap:       null,
  selectedScene:   null,
  selectedRecipient: null,
  suggestions:     [],
  selectedIndex:   -1,
  ttsTask:         null,
  ttsResult:       null,
  letters:         [],
  coreProfiles:    [],
};

// ── Mode detection ─────────────────────────────────────────────────────────────

function getAppMode() {
  const params = new URLSearchParams(window.location.search || "");
  return params.get("mode") === "dev" ? "dev" : "formal";
}

function applyModeUi() {
  const devPanel = el("devPanel");
  if (devPanel) {
    devPanel.classList.toggle("hidden", state.mode !== "dev");
  }
  document.body.setAttribute("data-mode", state.mode);
}

// ── Screen navigation ─────────────────────────────────────────────────────────

function showScreen(screen) {
  document.querySelectorAll(".screen").forEach(function(s) {
    s.classList.remove("active");
  });
  const target = el("screen" + capitalize(screen));
  if (target) {
    target.classList.add("active");
  }
  state.screen = screen;
  setStatus("准备就绪", "idle");

  // Per-screen init
  if (screen === "history") {
    loadLetters();
  }
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ── 按钮锁 ───────────────────────────────────────────────────────────────────

function setBusy(buttonId, busy, text) {
  const btn = el(buttonId);
  if (!btn) return;
  if (text !== undefined) {
    btn.textContent = text;
  }
  btn.disabled = busy;
}

// ── 工具函数 ──────────────────────────────────────────────────────────────────

function setStatus(message, kind) {
  const bar = document.getElementById("statusBar");
  if (!bar) return;
  bar.textContent = message;
  bar.className = "status-bar status-" + (kind || "idle");
}

async function apiFetch(path, options) {
  setStatus("请求中…", "loading");
  try {
    const res = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const body = await res.json();
    if (!res.ok || body.ok === false) {
      const msg = body.message || body.errorKind || body.detail || ("HTTP " + res.status);
      setStatus("错误：" + msg, "error");
      showToast("错误：" + msg);
      return null;
    }
    setStatus("完成", "ok");
    return body;
  } catch (err) {
    setStatus("网络错误：" + err.message, "error");
    showToast("网络错误");
    return null;
  }
}

function el(id) {
  return document.getElementById(id);
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showToast(msg) {
  // Lightweight toast - create if not exists
  var existing = document.getElementById("toastEl");
  if (existing) {
    existing.textContent = msg;
    existing.classList.remove("hidden");
    return;
  }
  var toast = document.createElement("div");
  toast.id = "toastEl";
  toast.className = "toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(function() {
    toast.classList.add("hidden");
  }, 3000);
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

async function loadBootstrap() {
  setStatus("加载配置…", "loading");
  const res = await apiFetch("/api/xiangta/bootstrap");
  if (!res) return;

  state.bootstrap = res.data;
  var data = res.data;

  // Render scene grid on home
  renderSceneGrid(data.scenes || []);

  // Render recipient grid on home
  renderRecipientGrid(data.recipients || []);

  // Populate compose selects (for later use)
  populateSelect("sceneSelect", data.scenes, function(s) { return s.id; }, function(s) { return s.label; });
  populateSelect("recipientSelect", data.recipients, function(r) { return r.id; }, function(r) { return r.label; });
  populateSelect("voicePresetSelect", data.voicePresets,
    function(v) { return v.id; },
    function(v) { return v.label + (v.genderStyle ? "（" + v.genderStyle + "）" : ""); }
  );
  populateSelect("toneSelect", data.tonePresets,
    function(t) { return t.id; },
    function(t) { return t.label; }
  );

  renderProviderStatus(data.providerStatus);
  setStatus("就绪", "ok");

  // Load Core profiles only in dev mode
  if (state.mode === "dev") {
    loadCoreProfiles();
  }
}

function renderSceneGrid(scenes) {
  var container = el("sceneGrid");
  if (!container) return;
  container.innerHTML = "";
  scenes.forEach(function(scene) {
    var chip = document.createElement("button");
    chip.className = "choice-chip";
    chip.setAttribute("data-scene", scene.id);
    chip.textContent = scene.label;
    chip.addEventListener("click", function() {
      selectScene(scene.id, scene.label);
    });
    container.appendChild(chip);
  });
}

function renderRecipientGrid(recipients) {
  var container = el("recipientGrid");
  if (!container) return;
  container.innerHTML = "";
  recipients.forEach(function(r) {
    var chip = document.createElement("button");
    chip.className = "choice-chip";
    chip.setAttribute("data-recipient", r.id);
    chip.textContent = r.label;
    chip.addEventListener("click", function() {
      selectRecipient(r.id, r.label);
    });
    container.appendChild(chip);
  });
}

function selectScene(id, label) {
  state.selectedScene = id;
  document.querySelectorAll("[data-scene]").forEach(function(c) {
    c.classList.toggle("selected", c.getAttribute("data-scene") === id);
  });
}

function selectRecipient(id, label) {
  state.selectedRecipient = id;
  document.querySelectorAll("[data-recipient]").forEach(function(c) {
    c.classList.toggle("selected", c.getAttribute("data-recipient") === id);
  });
}

function renderProviderStatus(ps) {
  var div = el("providerStatus");
  if (!div || !ps) return;
  var kindClass = {
    ok:             "provider-ok",
    not_integrated: "provider-warn",
    degraded:       "provider-warn",
    quota:          "provider-warn",
    error:          "provider-error",
    unknown:        "provider-warn",
  }[ps.kind] || "provider-warn";
  div.className = "provider-status " + kindClass;
  div.textContent = ps.label + "　" + ps.detail;
}

function populateSelect(selectId, items, valueFn, labelFn) {
  var sel = el(selectId);
  if (!sel) return;
  sel.innerHTML = "";
  items.forEach(function(item) {
    var opt = document.createElement("option");
    opt.value = valueFn(item);
    opt.text = labelFn(item);
    sel.appendChild(opt);
  });
}

// ── Core Profiles (dev mode) ──────────────────────────────────────────────────

async function loadCoreProfiles() {
  setStatus("加载人设…", "loading");
  var res = await apiFetch("/api/xiangta/core/profiles");
  if (!res) {
    state.coreProfiles = [];
    return;
  }
  state.coreProfiles = res.data.profiles || [];
  renderCoreProfileSelect(res.data);
  setStatus("就绪", "ok");
}

function renderCoreProfileSelect(data) {
  var sel = el("coreProfileSelect");
  if (!sel) return;
  sel.innerHTML = "";

  if (data.source === "not_integrated") {
    var opt = document.createElement("option");
    opt.value = "";
    opt.text = "未连接 Core";
    opt.disabled = true;
    sel.appendChild(opt);
    return;
  }

  var profiles = data.profiles || [];
  if (profiles.length === 0) {
    var opt = document.createElement("option");
    opt.value = "";
    opt.text = "暂无人设";
    opt.disabled = true;
    sel.appendChild(opt);
    return;
  }

  var placeholderOpt = document.createElement("option");
  placeholderOpt.value = "";
  placeholderOpt.text = "请选择人设…";
  placeholderOpt.selected = true;
  sel.appendChild(placeholderOpt);

  profiles.forEach(function(profile) {
    var opt = document.createElement("option");
    opt.value = profile.id || "";
    opt.text = (profile.name || profile.id) + "（" + (profile.id || "") + "）";
    sel.appendChild(opt);
  });
}

// ── Navigation helpers ────────────────────────────────────────────────────────

function goCompose() {
  if (!state.selectedScene) {
    setStatus("请选择心情", "warn");
    return;
  }
  if (!state.selectedRecipient) {
    setStatus("请选择想说给谁", "warn");
    return;
  }

  // Render meta info on compose screen
  var metaRow = el("composeMetaRow");
  if (metaRow) {
    var scene = (state.bootstrap && state.bootstrap.scenes || [])
      .find(function(s) { return s.id === state.selectedScene; });
    var recipient = (state.bootstrap && state.bootstrap.recipients || [])
      .find(function(r) { return r.id === state.selectedRecipient; });
    metaRow.innerHTML =
      '<span class="meta-chip">' + escHtml(scene ? scene.label : state.selectedScene) + '</span>'
      + '<span class="meta-chip">' + escHtml(recipient ? recipient.label : state.selectedRecipient) + '</span>';
  }

  // Reset compose state
  el("rawTextArea").value = "";
  el("rawTextCount").textContent = "0";

  showScreen("compose");
}

function goVoice() {
  var finalText = (el("finalTextArea").value || "").trim();
  if (!finalText) {
    setStatus("请先生成或填写文案", "warn");
    return;
  }

  // Render meta on voice screen
  var metaRow = el("voiceMeta");
  if (metaRow) {
    var scene = (state.bootstrap && state.bootstrap.scenes || [])
      .find(function(s) { return s.id === state.selectedScene; });
    var recipient = (state.bootstrap && state.bootstrap.recipients || [])
      .find(function(r) { return r.id === state.selectedRecipient; });
    var voicePreset = (state.bootstrap && state.bootstrap.voicePresets || [])
      .find(function(v) { return v.id === (el("voicePresetSelect") || {}).value; });
    var tone = (state.bootstrap && state.bootstrap.tonePresets || [])
      .find(function(t) { return t.id === (el("toneSelect") || {}).value; });
    metaRow.innerHTML =
      '<span class="meta-chip">' + escHtml(recipient ? recipient.label : state.selectedRecipient) + '</span>'
      + '<span class="meta-chip">' + escHtml(scene ? scene.label : state.selectedScene) + '</span>'
      + '<span class="meta-chip">' + escHtml(voicePreset ? voicePreset.label : "") + '</span>'
      + '<span class="meta-chip">' + escHtml(tone ? tone.label : "") + '</span>';
  }

  // Reset voice screen state
  state.ttsTask = null;
  state.ttsResult = null;
  el("ttsResult").classList.add("hidden");
  el("ttsResult").innerHTML = "";
  el("saveLetterSection").classList.add("hidden");
  setBusy("btnGenTtsTask", false, "生成语音");

  showScreen("voice");
}

// ── Suggestions ───────────────────────────────────────────────────────────────

async function generateSuggestions() {
  var rawText = (el("rawTextArea").value || "").trim();

  if (rawText.length < 4) {
    setStatus("原始心情至少需要 4 个字", "warn");
    return;
  }

  setBusy("btnGenSuggestions", true, "生成中…");

  var res = await apiFetch("/api/xiangta/suggestions", {
    method: "POST",
    body: JSON.stringify({
      recipient:   state.selectedRecipient,
      scene:       state.selectedScene,
      rawText:     rawText,
    }),
  });

  setBusy("btnGenSuggestions", false, "生成文案建议");

  if (!res) return;

  state.suggestions = res.data.suggestions || [];
  state.selectedIndex = -1;

  renderSuggestions(res.data);
  showScreen("suggest");
}

function renderSuggestions(data) {
  var area = el("suggestionsArea");
  area.innerHTML = "";

  var summaryEl = el("suggSummary");
  if (summaryEl) {
    summaryEl.textContent = (data.summary || "") + "　" + (data.intent || "");
    summaryEl.className = "sugg-summary";
  }

  if (!state.suggestions || state.suggestions.length === 0) {
    area.innerHTML = '<div class="sugg-empty">暂无建议</div>';
    return;
  }

  state.suggestions.forEach(function(s, i) {
    var card = document.createElement("div");
    card.className = "suggestion-card";
    card.setAttribute("data-index", i);
    card.innerHTML =
      '<div class="sugg-header">'
      + '<span class="sugg-style-label">' + escHtml(s.styleLabel || "") + '</span>'
      + '<span class="sugg-fits-for">' + escHtml(s.fitsFor || "") + '</span>'
      + '</div>'
      + '<div class="sugg-text">' + escHtml(s.text || "") + '</div>'
      + '<div class="sugg-chars">' + (s.charCount || 0) + ' 字</div>';
    card.addEventListener("click", function() { selectSuggestion(i); });
    area.appendChild(card);
  });
}

function selectSuggestion(index) {
  state.selectedIndex = index;
  var cards = document.querySelectorAll(".suggestion-card");
  cards.forEach(function(c, i) {
    c.classList.toggle("selected", i === index);
  });
  var sugg = state.suggestions[index];
  if (sugg) {
    el("finalTextArea").value = sugg.text || "";
  }
  setStatus("已选择「" + (sugg ? sugg.styleLabel : "") + "」", "ok");
}

// ── TTS Task API (C7) ─────────────────────────────────────────────────────────

async function generateTtsTask() {
  var finalText = (el("finalTextArea").value || "").trim();
  var rawText   = (el("rawTextArea").value   || "").trim();
  var text      = finalText || rawText;

  if (!text) {
    setStatus("请先输入或选择文案", "warn");
    return;
  }

  setBusy("btnGenTtsTask", true, "生成中…");

  var voicePreset = (el("voicePresetSelect") || {}).value || null;
  var tone        = (el("toneSelect")        || {}).value || null;
  var profileId   = (el("coreProfileSelect") || {}).value || null;

  var payload = {
    text:        text,
    voicePreset: voicePreset,
    tone:        tone,
    recipient:   state.selectedRecipient,
    scene:       state.selectedScene,
  };

  // Pass profileId only in dev mode when explicitly selected
  if (state.mode === "dev" && profileId) {
    payload.profileId = profileId;
  }

  var res = await apiFetch("/api/xiangta/tts/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!res) {
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }

  state.ttsTask = res.data;
  pollTtsTask(res.data);
}

async function pollTtsTask(task) {
  if (!task) return;

  var pollUrl = task.pollUrl || ("/api/xiangta/tts/tasks/" + task.taskId);
  var status  = task.status;

  if (status === "completed") {
    renderTtsTask(task);
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }

  if (status === "failed") {
    renderTtsTask(task);
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }

  // pending/running/queued - poll
  setBusy("btnGenTtsTask", true, "生成中…（" + status + "）");

  var res = await apiFetch(pollUrl);
  if (!res) {
    setBusy("btnGenTtsTask", false, "生成语音");
    return;
  }

  var updated = res.data || res;
  updated.pollUrl = pollUrl; // preserve

  if (updated.status === "completed" || updated.status === "failed") {
    state.ttsTask = updated;
    renderTtsTask(updated);
    setBusy("btnGenTtsTask", false, "生成语音");
  } else {
    // Schedule next poll
    state.ttsTask = updated;
    setTimeout(function() { pollTtsTask(updated); }, 1500);
  }
}

function revealSaveLetterSection() {
  var finalText = (el("finalTextArea").value || "").trim();
  var section = el("saveLetterSection");
  if (!section || !finalText) return;
  section.classList.remove("hidden");
}

function renderTtsTask(d) {
  var div = el("ttsResult");
  div.innerHTML = "";
  div.classList.remove("hidden");

  // Always allow saving text letter for any terminal state
  state.ttsResult = d;

  if (d.status === "failed") {
    div.innerHTML =
      '<div class="tts-error">'
      + '<span class="tts-error-kind">' + escHtml(d.errorKind || "生成失败") + '</span>'
      + '<span class="tts-error-msg">' + escHtml(d.message || "") + '</span>'
      + '</div>'
      + '<div class="tts-hint">语音暂未生成，可先保存文字信笺</div>';
    revealSaveLetterSection();
    return;
  }

  var html = "";
  if (d.taskId)    html += row("任务 ID", d.taskId);
  if (d.status)    html += row("状态",    d.status);
  if (d.charCount) html += row("字数",    d.charCount);
  if (d.durationMs) html += row("时长", (d.durationMs / 1000).toFixed(1) + " s");

  if (d.audioUrl) {
    var audioRow = document.createElement("div");
    audioRow.className = "tts-row tts-audio-row";
    var keySpan = document.createElement("span");
    keySpan.className = "tts-key";
    keySpan.textContent = "音频";
    var valSpan = document.createElement("span");
    valSpan.className = "tts-val";
    var audioEl = document.createElement("audio");
    audioEl.controls = true;
    audioEl.preload = "none";
    audioEl.src = d.audioUrl;
    valSpan.appendChild(audioEl);
    audioRow.appendChild(keySpan);
    audioRow.appendChild(valSpan);
    div.appendChild(audioRow);
  } else {
    div.insertAdjacentHTML("beforeend", '<div class="tts-hint">语音暂未生成，可先保存文字信笺</div>');
  }

  if (html) {
    div.insertAdjacentHTML("beforeend", html);
  }

  // Allow saving text letter even without audioUrl
  revealSaveLetterSection();
}

function row(key, val) {
  return '<div class="tts-row"><span class="tts-key">' + escHtml(key)
       + '</span><span class="tts-val">' + escHtml(String(val)) + '</span></div>';
}

// ── TTS dry-run (dev only alias) ─────────────────────────────────────────────

async function generateTts() {
  // Dev-only fallback - not used in formal path
  var finalText = (el("finalTextArea").value || "").trim();
  var rawText   = (el("rawTextArea").value   || "").trim();
  var text      = finalText || rawText;
  var voicePreset = (el("voicePresetSelect") || {}).value || null;
  var tone        = (el("toneSelect")        || {}).value || null;
  var profileId   = (el("coreProfileSelect") || {}).value || null;

  if (!text) {
    setStatus("请先输入或选择文案", "warn");
    return;
  }

  var payload = { text: text, voicePreset: voicePreset, tone: tone,
                  recipient: state.selectedRecipient, scene: state.selectedScene };
  if (state.mode === "dev" && profileId) {
    payload.profileId = profileId;
  }

  var res = await apiFetch("/api/xiangta/tts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!res) return;

  state.ttsResult = res.data;
  state.ttsTask  = res.data;
  renderTtsTask(res.data);
}

// ── Save Letter ───────────────────────────────────────────────────────────────

async function saveLetter() {
  var finalText   = (el("finalTextArea").value || "").trim();
  var rawText     = (el("rawTextArea").value   || "").trim();
  var title       = (el("titleInput").value    || "").trim() || null;

  if (!finalText) {
    setStatus("最终文案不能为空", "warn");
    return;
  }

  setBusy("btnSaveLetter", true, "保存中…");

  var selectedSugg  = state.suggestions[state.selectedIndex];
  var style         = selectedSugg ? selectedSugg.style : "gentle";
  var audioUrl      = state.ttsResult ? (state.ttsResult.audioUrl || null) : null;
  var durationMs    = state.ttsResult ? (state.ttsResult.durationMs || null) : null;
  var durationSecs  = durationMs ? durationMs / 1000 : null;

  var res = await apiFetch("/api/xiangta/letters", {
    method: "POST",
    body: JSON.stringify({
      recipient:    state.selectedRecipient,
      scene:        state.selectedScene,
      style:        style,
      rawText:      rawText,
      finalText:    finalText,
      voicePreset:  (el("voicePresetSelect") || {}).value || null,
      tone:         (el("toneSelect") || {}).value || null,
      audioUrl:     audioUrl,
      durationSecs: durationSecs,
      title:        title,
    }),
  });

  setBusy("btnSaveLetter", false, "保存信笺");

  if (!res) return;

  setStatus("信笺已保存", "ok");
  showToast("信笺已保存");
  el("titleInput").value = "";
}

// ── Letters history ────────────────────────────────────────────────────────────

async function loadLetters() {
  setBusy("btnRefreshHistory", true, "加载中…");

  var res = await apiFetch("/api/xiangta/letters?limit=20&offset=0");

  setBusy("btnRefreshHistory", false, "刷新历史");

  if (!res) return;
  state.letters = res.data.letters || [];
  renderLetters(res.data);
}

function renderLetters(data) {
  var area = el("lettersArea");
  if (!area) return;

  if (!data.letters || data.letters.length === 0) {
    area.innerHTML = '<div class="letters-empty">还没有保存过信笺</div>';
    return;
  }

  area.innerHTML = '<div class="letters-count">共 ' + data.total + ' 条</div>';

  data.letters.forEach(function(letter) {
    var card = document.createElement("div");
    card.className = "letter-card";

    var dateStr  = letter.createdAt ? letter.createdAt.replace("T", " ").replace("Z", " UTC") : "";
    var titleStr = letter.title || (letter.scene + " · " + letter.recipient);
    var metaArr  = [letter.recipient, letter.scene, letter.style, letter.voicePreset, letter.tone]
      .filter(Boolean);
    var metaStr  = metaArr.join(" · ");

    card.innerHTML =
      '<div class="letter-header">'
      + '<span class="letter-title">' + escHtml(titleStr) + '</span>'
      + '<span class="letter-date">' + escHtml(dateStr) + '</span>'
      + '</div>'
      + '<div class="letter-meta">' + escHtml(metaStr) + '</div>'
      + '<div class="letter-text">' + escHtml(letter.finalText || letter.rawText || "") + '</div>';

    if (letter.audioUrl) {
      var audioDiv = document.createElement("div");
      audioDiv.className = "letter-audio";
      var audioEl = document.createElement("audio");
      audioEl.controls = true;
      audioEl.preload = "none";
      audioEl.src = letter.audioUrl;
      audioDiv.appendChild(audioEl);
      card.appendChild(audioDiv);
    }

    area.appendChild(card);
  });
}

// ── 字数统计 ──────────────────────────────────────────────────────────────────

function initCharCounter() {
  var ta = el("rawTextArea");
  if (!ta) return;
  ta.addEventListener("input", function() {
    var cnt = el("rawTextCount");
    if (cnt) cnt.textContent = ta.value.length;
  });
}

// ── 入口 ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function() {
  state.mode = getAppMode();
  applyModeUi();
  initCharCounter();
  loadBootstrap();
});
