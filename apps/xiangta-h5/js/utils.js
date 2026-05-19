"use strict";

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

function formatTime(secs) {
  if (!secs || isNaN(secs)) return "0:00";
  const s = Math.round(secs);
  const m = Math.floor(s / 60);
  const ss = s % 60;
  return `${m}:${String(ss).padStart(2, "0")}`;
}
