"use strict";

// ── 配置 ──────────────────────────────────────────────────────────────────────

const API_BASE = "";

// ── 应用状态 ──────────────────────────────────────────────────────────────────

const state = {
  bootstrap:       null,
  suggestions:     [],
  selectedIndex:   -1,
  ttsResult:       null,
  coreProfiles:    [],   // B9: Core profile list
};

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
      const msg = body.message || body.detail || ("HTTP " + res.status);
      setStatus("错误：" + msg, "error");
      return null;
    }
    setStatus("完成", "ok");
    return body;
  } catch (err) {
    setStatus("网络错误：" + err.message, "error");
    return null;
  }
}

function el(id) {
  return document.getElementById(id);
}

function populateSelect(selectId, items, valueFn, labelFn) {
  const sel = el(selectId);
  if (!sel) return;
  sel.innerHTML = "";
  items.forEach(function(item) {
    const opt = document.createElement("option");
    opt.value  = valueFn(item);
    opt.text   = labelFn(item);
    sel.appendChild(opt);
  });
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

async function loadBootstrap() {
  setStatus("加载配置…", "loading");
  const res = await apiFetch("/api/xiangta/bootstrap");
  if (!res) return;

  state.bootstrap = res.data;

  const { recipients, scenes, voicePresets, tonePresets, providerStatus } = res.data;

  populateSelect("recipientSelect", recipients, function(r) { return r.id; }, function(r) { return r.label; });
  populateSelect("sceneSelect",     scenes,     function(s) { return s.id; }, function(s) { return s.label; });
  populateSelect("voicePresetSelect", voicePresets,
    function(v) { return v.id; },
    function(v) { return v.label + (v.genderStyle ? "（" + v.genderStyle + "）" : ""); }
  );
  populateSelect("toneSelect", tonePresets,
    function(t) { return t.id; },
    function(t) { return t.label; }
  );

  renderProviderStatus(providerStatus);
  setStatus("就绪", "ok");

  // B9: load Core profiles after bootstrap
  loadCoreProfiles();
}

function renderProviderStatus(ps) {
  const div = el("providerStatus");
  if (!div || !ps) return;
  const kindClass = {
    ok:              "provider-ok",
    not_integrated:  "provider-warn",
    degraded:        "provider-warn",
    quota:           "provider-warn",
    error:           "provider-error",
    unknown:         "provider-warn",
  }[ps.kind] || "provider-warn";
  div.className   = "provider-status " + kindClass;
  div.textContent = ps.label + "　" + ps.detail;
}

// ── Core Profiles (B9) ──────────────────────────────────────────────────────────

async function loadCoreProfiles() {
  setStatus("加载人设…", "loading");
  const res = await apiFetch("/api/xiangta/core/profiles");
  if (!res) {
    state.coreProfiles = [];
    return;
  }

  state.coreProfiles = res.data.profiles || [];
  renderCoreProfileSelect(res.data);
  setStatus("就绪", "ok");
}

function renderCoreProfileSelect(data) {
  const sel = el("coreProfileSelect");
  if (!sel) return;

  // Clear existing options
  sel.innerHTML = "";

  if (data.source === "not_integrated") {
    const opt = document.createElement("option");
    opt.value  = "";
    opt.text   = "未连接 Core";
    opt.disabled = true;
    sel.appendChild(opt);
    return;
  }

  const profiles = data.profiles || [];
  if (profiles.length === 0) {
    const opt = document.createElement("option");
    opt.value  = "";
    opt.text   = "暂无人设";
    opt.disabled = true;
    sel.appendChild(opt);
    return;
  }

  // Add placeholder
  const placeholderOpt = document.createElement("option");
  placeholderOpt.value  = "";
  placeholderOpt.text   = "请选择人设…";
  placeholderOpt.selected = true;
  sel.appendChild(placeholderOpt);

  profiles.forEach(function(profile) {
    const opt = document.createElement("option");
    opt.value  = profile.id || "";
    opt.text   = (profile.name || profile.id) + "（" + (profile.id || "") + "）";
    sel.appendChild(opt);
  });
}

// ── Suggestions ───────────────────────────────────────────────────────────────

async function generateSuggestions() {
  const recipient = el("recipientSelect").value;
  const scene     = el("sceneSelect").value;
  const rawText   = (el("rawTextArea").value || "").trim();

  if (rawText.length < 4) {
    setStatus("原始心情至少需要 4 个字", "warn");
    return;
  }

  const res = await apiFetch("/api/xiangta/suggestions", {
    method: "POST",
    body: JSON.stringify({ recipient, scene, rawText }),
  });
  if (!res) return;

  state.suggestions   = res.data.suggestions;
  state.selectedIndex = -1;
  renderSuggestions(res.data);
}

function renderSuggestions(data) {
  const area = el("suggestionsArea");
  area.innerHTML = "";
  area.classList.remove("hidden");

  const summaryEl = document.createElement("div");
  summaryEl.className = "sugg-summary";
  summaryEl.style.cssText = "font-size:.82rem;color:#666;margin-bottom:4px;";
  summaryEl.textContent = data.summary + "　" + data.intent;
  area.appendChild(summaryEl);

  data.suggestions.forEach(function(s, i) {
    const card = document.createElement("div");
    card.className = "suggestion-card";
    card.setAttribute("data-index", i);
    card.innerHTML =
      '<div class="sugg-header">'
      + '<span class="sugg-style-label">' + escHtml(s.styleLabel) + '</span>'
      + '<span class="sugg-fits-for">' + escHtml(s.fitsFor) + '</span>'
      + '</div>'
      + '<div class="sugg-text">' + escHtml(s.text) + '</div>'
      + '<div class="sugg-chars">' + s.charCount + ' 字</div>';
    card.addEventListener("click", function() { selectSuggestion(i); });
    area.appendChild(card);
  });
}

function selectSuggestion(index) {
  state.selectedIndex = index;
  const cards = document.querySelectorAll(".suggestion-card");
  cards.forEach(function(c, i) {
    c.classList.toggle("selected", i === index);
  });
  const sugg = state.suggestions[index];
  if (sugg) {
    el("finalTextArea").value = sugg.text;
  }
  setStatus("已选择「" + (sugg ? sugg.styleLabel : "") + "」", "ok");
}

// ── TTS ───────────────────────────────────────────────────────────────────────

async function generateTts() {
  const finalText   = (el("finalTextArea").value || "").trim();
  const rawText     = (el("rawTextArea").value   || "").trim();
  const text        = finalText || rawText;
  const voicePreset = el("voicePresetSelect").value;
  const tone        = el("toneSelect").value;
  const recipient   = el("recipientSelect").value;
  const scene       = el("sceneSelect").value;
  const profileId   = (el("coreProfileSelect") || {}).value || null;

  if (!text) {
    setStatus("请先输入或选择文案", "warn");
    return;
  }

  const payload = { text, voicePreset, tone, recipient, scene };
  // B9: pass profileId if user selected a Core profile
  if (profileId) {
    payload.profileId = profileId;
  }

  const res = await apiFetch("/api/xiangta/tts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!res) return;

  state.ttsResult = res.data;
  renderTtsResult(res.data);
}

function renderTtsResult(d) {
  const div = el("ttsResult");
  let html =
    row("任务 ID", d.taskId)
  + row("状态",   d.status)
  + row("字数",   d.charCount)
  + row("音色",   d.voicePreset)
  + row("语调",   d.tone);

  if (d.durationMs) {
    html += row("时长", (d.durationMs / 1000).toFixed(1) + " s");
  }

  // B9: render audio player using DOM API (no innerHTML concatenation for audioUrl)
  if (d.audioUrl) {
    const audioRow = document.createElement("div");
    audioRow.className = "tts-row";
    const keySpan = document.createElement("span");
    keySpan.className = "tts-key";
    keySpan.textContent = "音频";
    const valSpan = document.createElement("span");
    valSpan.className = "tts-val";
    const audioEl = document.createElement("audio");
    audioEl.controls = true;
    audioEl.preload = "none";
    audioEl.src = d.audioUrl;
    valSpan.appendChild(audioEl);
    audioRow.appendChild(keySpan);
    audioRow.appendChild(valSpan);
    div.appendChild(audioRow);
  }

  if (d.message) {
    html += row("消息", d.message);
  }

  // Keep text rows in innerHTML (audio appended above via DOM API)
  if (html) {
    div.insertAdjacentHTML("beforeend", html);
  }

  div.classList.remove("hidden");
}

function row(key, val) {
  return '<div class="tts-row"><span class="tts-key">' + escHtml(key)
       + '</span><span class="tts-val">' + escHtml(String(val)) + '</span></div>';
}

// ── Save Letter ───────────────────────────────────────────────────────────────

async function saveLetter() {
  const recipient   = el("recipientSelect").value;
  const scene       = el("sceneSelect").value;
  const voicePreset = el("voicePresetSelect").value;
  const tone        = el("toneSelect").value;
  const rawText     = (el("rawTextArea").value   || "").trim();
  const finalText   = (el("finalTextArea").value || "").trim();
  const title       = (el("titleInput").value    || "").trim() || null;

  if (!rawText) {
    setStatus("原始心情不能为空", "warn");
    return;
  }
  if (!finalText) {
    setStatus("最终文案不能为空，请先生成或填写", "warn");
    return;
  }

  const selectedSugg = state.suggestions[state.selectedIndex];
  const style        = selectedSugg ? selectedSugg.style : "gentle";
  const audioUrl     = state.ttsResult ? (state.ttsResult.audioUrl || null) : null;
  const durationMs   = state.ttsResult ? (state.ttsResult.durationMs || null) : null;
  const durationSecs = durationMs ? durationMs / 1000 : null;

  const res = await apiFetch("/api/xiangta/letters", {
    method: "POST",
    body: JSON.stringify({
      recipient, scene, style,
      rawText, finalText,
      voicePreset, tone,
      audioUrl, durationSecs, title,
    }),
  });
  if (!res) return;

  setStatus("信笺已保存 " + res.data.letterId, "ok");
  await loadLetters();
}

// ── Letters history ───────────────────────────────────────────────────────────

async function loadLetters() {
  const res = await apiFetch("/api/xiangta/letters?limit=20&offset=0");
  if (!res) return;
  renderLetters(res.data);
}

function renderLetters(data) {
  const area = el("lettersArea");
  if (!data.letters || data.letters.length === 0) {
    area.innerHTML = '<div class="letters-empty">暂无记录</div>';
    return;
  }

  area.innerHTML = '<div style="font-size:.78rem;color:#888;margin-bottom:8px;">共 '
    + data.total + ' 条，显示最近 ' + data.letters.length + ' 条</div>';

  data.letters.forEach(function(letter) {
    const card = document.createElement("div");
    card.className = "letter-card";

    const dateStr = letter.createdAt
      ? letter.createdAt.replace("T", " ").replace("Z", " UTC")
      : "";
    const titleStr = letter.title || (letter.scene + " · " + letter.recipient);
    const metaStr  = [letter.recipient, letter.scene, letter.style, letter.voicePreset, letter.tone]
      .filter(Boolean).join("  ·  ");

    card.innerHTML =
      '<div class="letter-header">'
      + '<span class="letter-title">' + escHtml(titleStr) + '</span>'
      + '<span class="letter-date">'  + escHtml(dateStr)  + '</span>'
      + '</div>'
      + '<div class="letter-meta">'   + escHtml(metaStr)  + '</div>'
      + '<div class="letter-text">'   + escHtml(letter.finalText || letter.rawText || "") + '</div>';
    area.appendChild(card);
  });
}

// ── 安全工具 ──────────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── 字数统计 ──────────────────────────────────────────────────────────────────

function initCharCounter() {
  const ta = el("rawTextArea");
  if (!ta) return;
  ta.addEventListener("input", function() {
    const cnt = el("rawTextCount");
    if (cnt) cnt.textContent = ta.value.length;
  });
}

// ── 入口 ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function() {
  initCharCounter();
  loadBootstrap();
  loadLetters();
});
