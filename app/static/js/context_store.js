/**
 * context_store.js
 *
 * Phase B1: Independent context storage module.
 *
 * Responsibilities:
 * - Read/write recoverable creation contexts to localStorage
 * - Normalize and validate longtext and script context entries
 * - Cap entries at MAX_CONTEXTS with LRU eviction
 * - Expose ContextStore API to window
 *
 * Does NOT:
 * - Depend on index.html
 * - Call any backend API
 * - Depend on DOM
 * - Reference sample storage or sidebar modules
 * - Call network fetch helpers
 * - Save audio blobs
 */

(function () {
  'use strict';

  // ── constants ───────────────────────────────────────────────────────
  var STORAGE_KEY = 'voice_lab_sample_context_v1';
  var MAX_CONTEXTS = 50;
  var VERSION = 1;
  var MAX_FULL_TEXT_LENGTH = 50000;
  var MAX_SCRIPT_LINES = 200;

  // ── local helpers ──────────────────────────────────────────────────

  function safeGetItem(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function safeSetItem(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {
      // fail-safe: storage full or unavailable
    }
  }

  function generateId() {
    if (window.crypto && window.crypto.randomUUID) {
      return window.crypto.randomUUID();
    }
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  }

  // ── parseContexts ──────────────────────────────────────────────────

  /**
   * Parse raw JSON from localStorage.
   * Tolerates: null, empty string, plain array, {version, contexts}.
   * Returns { version: 1, contexts: [...] } or null on complete failure.
   */
  function parseStorage(raw) {
    if (!raw) return null;
    try {
      var parsed = JSON.parse(raw);
      // Already new format
      if (parsed && typeof parsed === 'object' && Array.isArray(parsed.contexts)) {
        return parsed;
      }
      // Legacy flat array — wrap it
      if (Array.isArray(parsed)) {
        return { version: VERSION, contexts: parsed };
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  // ── normalizeContext ───────────────────────────────────────────────

  /**
   * Normalize and validate a context input.
   * Does NOT throw.
   */
  function normalizeContext(input) {
    if (!input || typeof input !== 'object') input = {};

    var contextId = input.context_id || input.sample_id || generateId();
    var createdAt = input.created_at || new Date().toISOString();
    var type = input.type;
    var source = input.source || '';

    var normalized = {
      version: VERSION,
      context_id: contextId,
      created_at: createdAt,
      type: type,
      source: source,
      batch_id: input.batch_id != null ? input.batch_id : null,
    };

    if (type === 'longtext') {
      normalizeLongtextContext(input, normalized);
    } else if (type === 'script') {
      normalizeScriptContext(input, normalized);
    }
    // unknown type: return minimal fields only

    return normalized;
  }

  function normalizeLongtextContext(input, out) {
    var fullText = input.full_text;
    if (fullText != null) {
      fullText = String(fullText);
      if (fullText.length > MAX_FULL_TEXT_LENGTH) {
        fullText = fullText.substring(0, MAX_FULL_TEXT_LENGTH);
      }
    } else {
      fullText = '';
    }
    out.full_text = fullText;

    out.provider = input.provider != null ? String(input.provider) : null;

    out.profile_id = input.profile_id != null ? String(input.profile_id) : null;

    // segment_strategy
    var strategy = input.segment_strategy;
    if (strategy !== 'auto' && strategy !== 'paragraph' && strategy !== 'sentence' && strategy !== 'line') {
      strategy = 'auto';
    }
    out.segment_strategy = strategy;

    // max_segment_chars
    var maxChars = parseInt(input.max_segment_chars, 10);
    if (isNaN(maxChars)) maxChars = 2000;
    else if (maxChars < 100) maxChars = 100;
    else if (maxChars > 5000) maxChars = 5000;
    out.max_segment_chars = maxChars;

    // silence_between_ms
    var silence = parseInt(input.silence_between_ms, 10);
    if (isNaN(silence) || silence < 0) silence = 300;
    else if (silence > 3000) silence = 3000;
    out.silence_between_ms = silence;

    // output_format
    var of = input.output_format;
    if (of !== 'hex' && of !== 'url') of = 'hex';
    out.output_format = of;

    // audio_format
    var af = input.audio_format;
    if (af !== 'mp3' && af !== 'wav' && af !== 'flac') af = 'mp3';
    out.audio_format = af;

    // need_subtitle
    out.need_subtitle = !!input.need_subtitle;

    // params
    var params = input.params;
    if (!params || typeof params !== 'object') params = {};
    out.params = {
      speed: params.speed != null ? parseFloat(params.speed) : null,
      vol: params.vol != null ? parseFloat(params.vol) : null,
      pitch: params.pitch != null ? parseInt(params.pitch, 10) : null,
      emotion: params.emotion != null ? String(params.emotion) : null,
    };
  }

  function normalizeScriptContext(input, out) {
    // lines — only keep rows with non-empty text
    var rawLines = input.lines;
    var lines = [];
    if (Array.isArray(rawLines)) {
      for (var i = 0; i < rawLines.length; i++) {
        var row = rawLines[i];
        if (!row) continue;
        var text = row.text ? String(row.text).trim() : '';
        if (!text) continue;
        var normalizedRow = {
          role: row.role != null ? String(row.role) : '',
          text: text,
          profile_id: row.profile_id != null ? String(row.profile_id) : '',
          params: {},
        };
        lines.push(normalizedRow);
        if (lines.length >= MAX_SCRIPT_LINES) break;
      }
    }
    out.lines = lines;

    out.provider = input.provider != null ? String(input.provider) : null;

    // silence_between_ms
    var silence = parseInt(input.silence_between_ms, 10);
    if (isNaN(silence) || silence < 0) silence = 500;
    else if (silence > 3000) silence = 3000;
    out.silence_between_ms = silence;

    // output_format
    var of = input.output_format;
    if (of !== 'hex' && of !== 'url') of = 'hex';
    out.output_format = of;

    // audio_format
    var af = input.audio_format;
    if (af !== 'mp3' && af !== 'wav' && af !== 'flac') af = 'mp3';
    out.audio_format = af;

    // need_subtitle
    out.need_subtitle = !!input.need_subtitle;
  }

  // ── trimContexts ──────────────────────────────────────────────────

  /**
   * Sort by created_at descending (newest first) and keep at most MAX_CONTEXTS.
   * Does NOT write to localStorage — caller decides when to persist.
   */
  function trimContexts(contexts) {
    if (!Array.isArray(contexts)) contexts = [];
    contexts.sort(function (a, b) {
      var ta = a && a.created_at ? new Date(a.created_at).getTime() : 0;
      var tb = b && b.created_at ? new Date(b.created_at).getTime() : 0;
      return tb - ta;
    });
    if (contexts.length > MAX_CONTEXTS) {
      contexts = contexts.slice(0, MAX_CONTEXTS);
    }
    return contexts;
  }

  // ── getContexts ───────────────────────────────────────────────────

  /**
   * Read all contexts from localStorage.
   * Returns [] if unavailable or malformed.
   * Returned array is sorted newest-first and trimmed to MAX_CONTEXTS.
   * Does NOT write to localStorage.
   */
  function getContexts() {
    var raw = safeGetItem(STORAGE_KEY);
    var stored = parseStorage(raw);
    if (!stored || !Array.isArray(stored.contexts)) return [];
    return trimContexts(stored.contexts.slice());
  }

  // ── getContext ────────────────────────────────────────────────────

  /**
   * Find a single context by context_id.
   * Returns null if not found or storage is unavailable.
   */
  function getContext(contextId) {
    if (!contextId) return null;
    var contexts = getContexts();
    for (var i = 0; i < contexts.length; i++) {
      if (contexts[i] && contexts[i].context_id === contextId) {
        return contexts[i];
      }
    }
    return null;
  }

  // ── pushContext ───────────────────────────────────────────────────

  /**
   * Normalize input, upsert into context list, trim to MAX_CONTEXTS,
   * and persist to localStorage.
   * Returns the normalized context entry.
   */
  function pushContext(input) {
    var normalized = normalizeContext(input);
    var stored = parseStorage(safeGetItem(STORAGE_KEY));
    var contexts = stored && Array.isArray(stored.contexts) ? stored.contexts : [];

    // Upsert: replace existing context_id, otherwise prepend
    var inserted = false;
    for (var i = 0; i < contexts.length; i++) {
      if (contexts[i] && contexts[i].context_id === normalized.context_id) {
        contexts[i] = normalized;
        inserted = true;
        break;
      }
    }
    if (!inserted) {
      contexts.unshift(normalized);
    }

    contexts = trimContexts(contexts);
    safeSetItem(STORAGE_KEY, JSON.stringify({ version: VERSION, contexts: contexts }));
    return normalized;
  }

  // ── deleteContext ─────────────────────────────────────────────────

  /**
   * Remove the context with the given context_id.
   * Persists the updated contexts array when a matching context is removed.
   * Returns the updated contexts array.
   */
  function deleteContext(contextId) {
    if (!contextId) return getContexts();
    var contexts = getContexts();
    var before = contexts.length;
    contexts = contexts.filter(function (c) {
      return c && c.context_id !== contextId;
    });
    if (contexts.length !== before) {
      safeSetItem(STORAGE_KEY, JSON.stringify({ version: VERSION, contexts: contexts }));
    }
    return contexts;
  }

  // ── clearContexts ─────────────────────────────────────────────────

  /**
   * Clear all contexts — write empty wrapper.
   * Returns [].
   */
  function clearContexts() {
    safeSetItem(STORAGE_KEY, JSON.stringify({ version: VERSION, contexts: [] }));
    return [];
  }

  // ── expose to window ─────────────────────────────────────────────

  window.ContextStore = {
    pushContext: pushContext,
    getContext: getContext,
    getContexts: getContexts,
    deleteContext: deleteContext,
    clearContexts: clearContexts,
    normalizeContext: normalizeContext,
    trimContexts: trimContexts,
  };

})();
