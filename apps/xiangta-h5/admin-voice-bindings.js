"use strict";

const API_BASE = "";
const ADMIN_TOKEN_KEY = "xiangta_admin_token";

const state = {
  adminToken: null,
  coreProfiles: [],
  coreSource: null,
  coreConnected: false,
  voiceMappings: [],
  saving: {},
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

function getAdminToken() {
  if (state.adminToken) return state.adminToken;
  return sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
}

function saveAdminToken(token) {
  state.adminToken = token;
  sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
}

function adminHeaders() {
  return {
    "Content-Type": "application/json",
    "X-XiangTa-Admin-Token": getAdminToken(),
  };
}

async function apiFetch(path, options) {
  try {
    const response = await fetch(API_BASE + path, {
      ...options,
      headers: {
        ...(options?.headers || {}),
        "Content-Type": "application/json",
      },
    });
    const body = await response.json();
    if (!response.ok || body.ok === false) {
      const message = body.message || body.errorKind || ("HTTP " + response.status);
      showError(message + (response.status === 403 ? " — Token 无效或未配置 Admin" : ""));
      return null;
    }
    clearError();
    return body;
  } catch (err) {
    showError("网络错误：" + err.message);
    return null;
  }
}

function showError(msg) {
  const section = el("errorSection");
  const msgEl = el("errorMessage");
  if (section && msgEl) {
    msgEl.textContent = msg;
    section.classList.remove("hidden");
  }
}

function clearError() {
  const section = el("errorSection");
  if (section) section.classList.add("hidden");
}

function showToast(msg) {
  const existing = document.querySelector(".save-success-toast");
  if (existing) existing.remove();
  const toast = document.createElement("div");
  toast.className = "save-success-toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

function renderTokenStatus() {
  const statusEl = el("tokenStatus");
  if (!statusEl) return;
  const token = getAdminToken();
  if (!token) {
    statusEl.textContent = "未配置 Token";
    statusEl.className = "token-status";
    return;
  }
  statusEl.textContent = "Token 已配置（已脱敏）";
  statusEl.className = "token-status ok";
}

// ── Core Profiles ──────────────────────────────────────────────────────────────

async function loadCoreProfiles() {
  const response = await apiFetch("/api/xiangta/core/profiles");
  if (!response) {
    state.coreProfiles = [];
    state.coreSource = "error";
    state.coreConnected = false;
  } else {
    state.coreProfiles = response.data.profiles || [];
    state.coreSource = response.data.source || "unknown";
    state.coreConnected = state.coreSource === "core";
  }
  renderCoreStatus();
  renderBindings();
}

function renderCoreStatus() {
  const dot = el("coreStatusDot");
  const label = el("coreStatusLabel");
  const summary = el("coreProfilesSummary");

  if (!dot || !label) return;

  dot.className = "core-status-dot";

  if (state.coreConnected) {
    dot.classList.add("connected");
    label.textContent = `已连接 · ${state.coreProfiles.length} 个 profile`;
    if (summary) {
      const active = state.coreProfiles.filter(function(p) { return p.isActive !== false; }).length;
      summary.textContent = `活跃 ${active} / 总计 ${state.coreProfiles.length} 个 profile`;
    }
  } else {
    dot.classList.add("disconnected");
    label.textContent = "Core 未连接";
    if (summary) summary.textContent = "请配置 XIANGTA_CORE_BASE_URL";
  }
}

// ── Voice Mappings ─────────────────────────────────────────────────────────────

async function loadVoiceMappings() {
  const headers = adminHeaders();
  const response = await apiFetch("/api/xiangta/admin/voice-mappings", {
    headers: headers,
  });
  if (!response) {
    state.voiceMappings = [];
    return;
  }
  state.voiceMappings = response.data || [];
  renderBindings();
}

function renderBindings() {
  const area = el("bindingsArea");
  if (!area) return;

  if (state.voiceMappings.length === 0) {
    area.innerHTML = '<div class="empty-hint">暂无声音映射配置</div>';
    return;
  }

  area.innerHTML = "";

  state.voiceMappings.forEach(function(mapping) {
    const card = buildBindingCard(mapping);
    area.appendChild(card);
  });
}

function buildBindingCard(mapping) {
  const card = document.createElement("div");
  card.className = "binding-card";
  card.dataset.id = mapping.id;

  const statusInfo = getBindingStatusInfo(mapping);
  const profileOptions = buildProfileOptions(mapping);

  card.innerHTML =
    '<div class="binding-card-header">' +
      '<div>' +
        '<div class="binding-card-title">' + escHtml(mapping.label) + '</div>' +
        '<div class="binding-card-desc">' + escHtml(mapping.desc || "") + '</div>' +
        (mapping.coreProfileId && !isPlaceholder(mapping.coreProfileId)
          ? '<div class="core-profile-tag">已绑定: ' + escHtml(mapping.coreProfileId) + '</div>'
          : '<div class="core-profile-tag">未绑定</div>') +
      '</div>' +
      '<span class="binding-status-badge ' + escHtml(statusInfo.badgeClass) + '">' +
        escHtml(statusInfo.label) +
      '</span>' +
    '</div>' +
    '<div class="binding-select-row">' +
      '<span class="binding-select-label">Core Profile</span>' +
      '<select class="binding-select" id="select-' + escHtml(mapping.id) + '">' +
        '<option value="">— 选择 Core profile —</option>' +
        profileOptions +
      '</select>' +
    '</div>' +
    '<input type="text" class="binding-notes-input" id="notes-' + escHtml(mapping.id) + '" ' +
      'placeholder="备注（可选）" value="' + escHtml(mapping.notes || "") + '" maxlength="500" />' +
    '<div class="binding-actions">' +
      '<button class="btn-bind-save" type="button" id="save-' + escHtml(mapping.id) + '">保存绑定</button>' +
    '</div>';

  // Pre-select current profile
  const select = card.querySelector("select");
  if (select && mapping.coreProfileId && !isPlaceholder(mapping.coreProfileId)) {
    select.value = mapping.coreProfileId;
  }

  // Attach save handler
  const saveBtn = card.querySelector("button");
  if (saveBtn) {
    saveBtn.addEventListener("click", function() {
      saveBinding(mapping.id);
    });
  }

  return card;
}

function buildProfileOptions(mapping) {
  if (!state.coreConnected || state.coreProfiles.length === 0) {
    return '<option value="" disabled>Core 未连接，无可选项</option>';
  }

  let options = "";
  state.coreProfiles.forEach(function(profile) {
    const isActive = profile.isActive !== false;
    const tagParts = [
      profile.genderStyle || "",
      profile.toneStyle || "",
      isActive ? "active" : "inactive",
    ].filter(Boolean).join(" · ");

    const displayName = profile.name || profile.id;
    const label = displayName + (tagParts ? " · " + tagParts : "");

    options += '<option value="' + escHtml(profile.id) + '">' + escHtml(label) + '</option>';
  });
  return options;
}

function getBindingStatusInfo(mapping) {
  const coreId = mapping.coreProfileId || "";
  const isPh = isPlaceholder(coreId);

  if (!state.coreConnected) {
    if (!coreId || isPh) {
      return { label: "未绑定", badgeClass: "unbound" };
    }
    return { label: "绑定离线", badgeClass: "core-offline" };
  }

  if (!coreId || isPh) {
    return { label: "待绑定", badgeClass: "unbound" };
  }

  const exists = state.coreProfiles.some(function(p) { return p.id === coreId; });
  if (!exists) {
    return { label: "绑定失效", badgeClass: "invalid" };
  }
  return { label: "已绑定", badgeClass: "bound" };
}

function isPlaceholder(value) {
  if (!value) return true;
  const s = String(value).trim();
  if (!s) return true;
  if (s === "<core_profile_id_from_core_profiles>") return true;
  if (s.includes("<") || s.includes(">")) return true;
  if (s.toLowerCase().startsWith("todo")) return true;
  return false;
}

async function saveBinding(id) {
  const select = el("select-" + id);
  const notesEl = el("notes-" + id);
  const saveBtn = el("save-" + id);

  if (!select || !saveBtn) return;

  const coreProfileId = (select.value || "").trim();
  const notes = (notesEl ? notesEl.value : "").trim();

  // Validation: if selecting a profile, must not be placeholder
  if (coreProfileId && isPlaceholder(coreProfileId)) {
    showError("不能选择占位值为 coreProfileId");
    return;
  }

  saveBtn.disabled = true;
  saveBtn.textContent = "保存中...";

  const headers = adminHeaders();
  const payload = {
    coreProfileId: coreProfileId || null,
    providerPolicy: "default",
    notes: notes || null,
  };

  const response = await apiFetch("/api/xiangta/admin/voice-mappings/" + encodeURIComponent(id), {
    method: "PUT",
    headers: headers,
    body: JSON.stringify(payload),
  });

  saveBtn.disabled = false;
  saveBtn.textContent = "保存绑定";

  if (response) {
    showToast("保存成功");
    // Reload mappings to reflect new state
    await loadVoiceMappings();
    await loadCoreProfiles();
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

async function loadAll() {
  clearError();
  renderTokenStatus();
  await Promise.all([loadVoiceMappings(), loadCoreProfiles()]);
}

// ── Event Handlers ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function() {
  // Pre-fill token from sessionStorage
  const savedToken = sessionStorage.getItem(ADMIN_TOKEN_KEY);
  const tokenInput = el("adminTokenInput");
  if (tokenInput && savedToken) {
    tokenInput.value = savedToken;
  }

  // Save token
  el("btnSaveToken")?.addEventListener("click", function() {
    const token = (el("adminTokenInput")?.value || "").trim();
    saveAdminToken(token);
    renderTokenStatus();
    showToast("Token 已保存");
  });

  // Refresh
  el("btnRefreshAll")?.addEventListener("click", function() {
    loadAll();
  });

  loadAll();
});
