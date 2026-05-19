/**
 * viewport-fit.js — XiangTa H5 viewport baseline recognition module.
 *
 * Responsibilities:
 *   1. Read visualViewport / innerWidth / innerHeight.
 *   2. Classify width / height / keyboard modes.
 *   3. Write body dataset (data-h5-width, data-h5-height, data-h5-keyboard).
 *   4. Write CSS variables to documentElement.
 *   5. Debounce updates with requestAnimationFrame.
 *   6. Expose window.XiangTaViewportFit = { sync }.
 *
 * Width modes:   narrow (≤375) | normal (376–414) | wide (>414)
 * Height modes:  compact (≤640) | normal (641–720) | comfortable (>720)
 * Keyboard mode: open (offset > 80px) | closed
 *
 * Does NOT: call APIs, modify app state, call showScreen(), touch playback.
 */
"use strict";
(function () {
  var docEl = document.documentElement;
  var _raf = null;

  // ─── Classification ─────────────────────────────────────────────────────

  function classifyWidth(vw) {
    if (vw <= 375) return "narrow";
    if (vw <= 414) return "normal";
    return "wide";
  }

  function classifyHeight(vh) {
    if (vh <= 640) return "compact";
    if (vh <= 720) return "normal";
    return "comfortable";
  }

  // ─── Measurement ────────────────────────────────────────────────────────

  function measure() {
    var vv = window.visualViewport;
    var vw, vh, kbOffset;

    if (vv) {
      vw = vv.width;
      vh = vv.height;
      // Keyboard offset = how much of innerHeight the keyboard has consumed
      var viewportBottom = vv.height + vv.offsetTop;
      kbOffset = Math.max(0, window.innerHeight - viewportBottom);
    } else {
      vw = window.innerWidth;
      vh = window.innerHeight;
      kbOffset = 0;
    }

    return {
      vw: vw,
      vh: vh,
      kbOffset: kbOffset,
      widthMode:  classifyWidth(vw),
      heightMode: classifyHeight(vh),
      kbMode:     kbOffset > 80 ? "open" : "closed",
    };
  }

  // ─── Apply ──────────────────────────────────────────────────────────────

  function apply(m) {
    // body dataset — consumed by CSS selectors
    var b = document.body;
    b.dataset.h5Width    = m.widthMode;
    b.dataset.h5Height   = m.heightMode;
    b.dataset.h5Keyboard = m.kbMode;

    // CSS variables — available to all rules
    docEl.style.setProperty("--h5-vv-width",        m.vw + "px");
    docEl.style.setProperty("--h5-vv-height",        m.vh + "px");
    docEl.style.setProperty("--h5-keyboard-offset",  m.kbOffset + "px");
  }

  // ─── Public sync ────────────────────────────────────────────────────────

  function sync() {
    apply(measure());
  }

  // ─── Debounced handler ──────────────────────────────────────────────────

  function scheduleSync() {
    if (_raf) return;
    _raf = requestAnimationFrame(function () {
      _raf = null;
      sync();
    });
  }

  // ─── Bootstrap ──────────────────────────────────────────────────────────

  // Script is loaded at end of <body> — document.body is available.
  sync();

  // Resize / orientation
  window.addEventListener("resize",            scheduleSync, { passive: true });
  window.addEventListener("orientationchange", scheduleSync, { passive: true });

  // visualViewport (keyboard slide, zoom)
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", scheduleSync, { passive: true });
    window.visualViewport.addEventListener("scroll", scheduleSync, { passive: true });
  }

  // ─── Public API ─────────────────────────────────────────────────────────
  window.XiangTaViewportFit = { sync: sync };
})();
