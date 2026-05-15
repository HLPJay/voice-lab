/**
 * sample_store.js
 *
 * Phase B1: Independent sample storage module.
 *
 * Responsibilities:
 * - Read/write recent sample metadata to localStorage
 * - Normalize, validate and cap sample entries
 * - Expose SampleStore API to window
 *
 * Does NOT:
 * - Depend on index.html
 * - Call any backend API
 * - Read/write recentJobs
 * - Save audio blobs
 * - Save blob: URLs
 * - Save API keys or sensitive payloads
 * - Depend on DOM
 */

(function () {
  'use strict';

  // ── constants ───────────────────────────────────────────────────────
  var STORAGE_KEY = 'voice_lab_recent_samples_v1';
  var MAX_SAMPLES = 200;
  var TEXT_PREVIEW_MAX = 100;

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

  function parseSamples(raw) {
    try {
      var parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed;
    } catch (e) {
      return [];
    }
  }

  // ── normalizeSample ────────────────────────────────────────────────

  /**
   * Normalize and validate a sample input.
   * - Generates sample_id if missing
   * - Generates created_at if missing
   * - Truncates text_preview to TEXT_PREVIEW_MAX chars
   * - Strips blob: download_url
   * - Ensures tags is an array
   * - Does NOT throw
   */
  function normalizeSample(input) {
    if (!input || typeof input !== 'object') input = {};

    var textPreview = input.text_preview == null ? '' : String(input.text_preview);
    if (textPreview.length > TEXT_PREVIEW_MAX) {
      textPreview = textPreview.substring(0, TEXT_PREVIEW_MAX) + '…';
    }

    var downloadUrl = input.download_url == null ? null : String(input.download_url);
    // Discard blob: URLs — they are session-scoped and not persistent
    if (downloadUrl && downloadUrl.indexOf('blob:') === 0) {
      downloadUrl = null;
    }

    return {
      sample_id: input.sample_id || (window.crypto && window.crypto.randomUUID ? window.crypto.randomUUID() : (Date.now().toString(36) + Math.random().toString(36).substring(2))),
      created_at: input.created_at || new Date().toISOString(),
      source: input.source || 'unknown',
      job_id: input.job_id != null ? input.job_id : null,
      batch_id: input.batch_id != null ? input.batch_id : null,
      segment_id: input.segment_id != null ? input.segment_id : null,
      asset_id: input.asset_id != null ? input.asset_id : null,
      download_url: downloadUrl,
      text_preview: textPreview,
      profile_id: input.profile_id != null ? input.profile_id : null,
      profile_name: input.profile_name != null ? input.profile_name : null,
      provider: input.provider != null ? input.provider : null,
      model: input.model != null ? input.model : null,
      voice_id: input.voice_id != null ? input.voice_id : null,
      voice_name: input.voice_name != null ? input.voice_name : null,
      duration_ms: input.duration_ms != null ? input.duration_ms : null,
      audio_format: input.audio_format || 'mp3',
      status: input.status || 'completed',
      tags: Array.isArray(input.tags) ? input.tags : [],
      context_id: input.context_id != null ? String(input.context_id) : null,
    };
  }

  // ── trimSamples ───────────────────────────────────────────────────

  /**
   * Sort samples by created_at descending (newest first)
   * and keep at most MAX_SAMPLES entries.
   * Does NOT write to localStorage — caller decides when to persist.
   */
  function trimSamples(samples) {
    if (!Array.isArray(samples)) samples = [];
    // Sort newest first
    samples.sort(function (a, b) {
      var ta = a && a.created_at ? new Date(a.created_at).getTime() : 0;
      var tb = b && b.created_at ? new Date(b.created_at).getTime() : 0;
      return tb - ta;
    });
    if (samples.length > MAX_SAMPLES) {
      samples = samples.slice(0, MAX_SAMPLES);
    }
    return samples;
  }

  // ── getSamples ────────────────────────────────────────────────────

  /**
   * Read all samples from localStorage.
   * Returns [] if unavailable, malformed, or not an array.
   * Returned array is sorted newest-first by created_at and trimmed to MAX_SAMPLES.
   * Does NOT write to localStorage.
   */
  function getSamples() {
    var raw = safeGetItem(STORAGE_KEY);
    if (!raw) return [];
    return trimSamples(parseSamples(raw));
  }

  // ── pushSample ────────────────────────────────────────────────────

  /**
   * Normalize input, prepend to sample list, trim to MAX_SAMPLES,
   * and persist to localStorage.
   * Returns the normalized sample entry.
   */
  function pushSample(input) {
    var samples = getSamples();
    var normalized = normalizeSample(input);
    samples.unshift(normalized); // newest first
    samples = trimSamples(samples);
    safeSetItem(STORAGE_KEY, JSON.stringify(samples));
    return normalized;
  }

  // ── deleteSample ──────────────────────────────────────────────────

  /**
   * Remove the sample with the given sample_id.
   * Returns the updated samples array.
   */
  function deleteSample(sampleId) {
    var samples = getSamples();
    var before = samples.length;
    samples = samples.filter(function (s) {
      return s && s.sample_id !== sampleId;
    });
    if (samples.length !== before) {
      safeSetItem(STORAGE_KEY, JSON.stringify(samples));
    }
    return samples;
  }

  // ── clearSamples ─────────────────────────────────────────────────

  /**
   * Clear all samples — write empty array.
   * Returns [].
   */
  function clearSamples() {
    safeSetItem(STORAGE_KEY, '[]');
    return [];
  }

  // ── expose to window ─────────────────────────────────────────────

  window.SampleStore = {
    pushSample: pushSample,
    getSamples: getSamples,
    deleteSample: deleteSample,
    clearSamples: clearSamples,
    normalizeSample: normalizeSample,
    trimSamples: trimSamples,
  };

})();
