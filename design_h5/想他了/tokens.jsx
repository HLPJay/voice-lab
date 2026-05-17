// Design tokens for 想Ta了 — dark warm-purple, single accent, literary
// Used everywhere; kept on window for cross-file access.

// Palettes — accent groupings. Default = purple.
const PALETTES = {
  purple: { accent: '#9B4DCA', soft: 'rgba(155,77,202,0.18)', deep: 'rgba(155,77,202,0.32)', ink: '#E8C9F4', hue: 281 },
  amber:  { accent: '#D9954A', soft: 'rgba(217,149,74,0.18)',  deep: 'rgba(217,149,74,0.32)',  ink: '#F4D9A8', hue: 32  },
  sage:   { accent: '#6FA582', soft: 'rgba(111,165,130,0.18)', deep: 'rgba(111,165,130,0.32)', ink: '#C8E0CF', hue: 142 },
  rose:   { accent: '#C77191', soft: 'rgba(199,113,145,0.18)', deep: 'rgba(199,113,145,0.32)', ink: '#EFC5D3', hue: 340 },
};

const T = {
  // Surfaces (warm-leaning, very slight purple cast)
  bg:        '#100D14',
  bgDeep:    '#0A080E',
  surface:   '#1A1521',
  surface2:  '#221C2C',
  surface3:  '#2C2438',
  hairline:  'rgba(255,255,255,0.07)',
  hairline2: 'rgba(255,255,255,0.12)',

  // Text
  text:      '#F4EFE6',
  text2:     'rgba(244,239,230,0.62)',
  text3:     'rgba(244,239,230,0.38)',
  text4:     'rgba(244,239,230,0.22)',

  // Accent — purple (default, mutable via applyPalette)
  accent:    PALETTES.purple.accent,
  accentSoft:PALETTES.purple.soft,
  accentDeep:PALETTES.purple.deep,
  accentInk: PALETTES.purple.ink,

  // Semantic
  warm:      '#E0A87B',     // gentle warning (risk hint)
  warmSoft:  'rgba(224,168,123,0.16)',
  danger:    '#D17A7A',
  dangerSoft:'rgba(209,122,122,0.14)',
  ok:        '#8FBF9F',
  okSoft:    'rgba(143,191,159,0.14)',

  // Type
  serif:     '"Noto Serif SC", "Songti SC", "Source Han Serif SC", serif',
  sans:      '"Noto Sans SC", -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
  mono:      '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace',

  // Spacing rhythm
  r:         (n) => `${n * 4}px`,
};

window.T = T;
window.PALETTES = PALETTES;

// Apply a palette: mutates T's accent group + sets CSS vars on documentElement.
// Components using T.accent re-read on next render; CSS classes use var(--xt-accent).
function applyPalette(name) {
  const p = PALETTES[name] || PALETTES.purple;
  T.accent     = p.accent;
  T.accentSoft = p.soft;
  T.accentDeep = p.deep;
  T.accentInk  = p.ink;
  if (typeof document !== 'undefined') {
    const r = document.documentElement;
    r.style.setProperty('--xt-accent',      p.accent);
    r.style.setProperty('--xt-accent-soft', p.soft);
    r.style.setProperty('--xt-accent-deep', p.deep);
    r.style.setProperty('--xt-accent-ink',  p.ink);
  }
}
window.applyPalette = applyPalette;
applyPalette('purple');

// Global page styles + font import
if (typeof document !== 'undefined' && !document.getElementById('xt-base')) {
  const s = document.createElement('style');
  s.id = 'xt-base';
  s.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');

    body, html { margin: 0; padding: 0; background: ${T.bgDeep}; font-family: ${T.sans}; color: ${T.text}; -webkit-font-smoothing: antialiased; }
    * { box-sizing: border-box; }

    /* Custom scrollbar inside screens (hidden, but cards still scroll) */
    .xt-scroll::-webkit-scrollbar { width: 0; height: 0; }
    .xt-scroll { scrollbar-width: none; }

    /* Mobile screen wrapper (inside ios frame content area) */
    .xt-screen {
      background: ${T.bg};
      color: ${T.text};
      min-height: 100%;
      font-family: ${T.sans};
      letter-spacing: 0.01em;
    }
    .xt-screen.serif { font-family: ${T.serif}; }

    /* utility */
    .xt-row { display: flex; align-items: center; }
    .xt-col { display: flex; flex-direction: column; }
    .xt-gap-1 { gap: 4px; } .xt-gap-2 { gap: 8px; } .xt-gap-3 { gap: 12px; }
    .xt-gap-4 { gap: 16px; } .xt-gap-5 { gap: 20px; } .xt-gap-6 { gap: 24px; }
    .xt-grow { flex: 1; }

    /* Subtle hover-able card baseline */
    .xt-card {
      background: ${T.surface};
      border: 1px solid ${T.hairline};
      border-radius: 16px;
    }
    .xt-card-elev {
      background: ${T.surface2};
      border: 1px solid ${T.hairline2};
      border-radius: 20px;
    }

    .xt-pill {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 12px; border-radius: 999px;
      font-size: 12px; letter-spacing: 0.02em;
      border: 1px solid ${T.hairline};
      color: ${T.text2};
      background: rgba(255,255,255,0.02);
    }
    .xt-pill.active {
      background: var(--xt-accent-soft);
      border-color: var(--xt-accent-deep);
      color: var(--xt-accent-ink);
    }

    .xt-btn {
      display: inline-flex; align-items: center; justify-content: center;
      gap: 8px; padding: 14px 18px;
      border-radius: 14px; font-family: ${T.sans};
      font-size: 15px; font-weight: 500; letter-spacing: 0.02em;
      border: 1px solid transparent; cursor: pointer;
      background: ${T.surface2}; color: ${T.text}; user-select: none;
    }
    .xt-btn.primary {
      background: var(--xt-accent); color: white; border-color: var(--xt-accent);
      box-shadow: 0 8px 24px var(--xt-accent-soft), inset 0 1px 0 rgba(255,255,255,0.18);
    }
    .xt-btn.ghost {
      background: transparent; color: ${T.text2};
      border-color: ${T.hairline2};
    }
    .xt-btn.full { width: 100%; }

    /* Letter-paper feel for serif text blocks */
    .xt-letter {
      font-family: ${T.serif};
      font-size: 17px; line-height: 1.85; letter-spacing: 0.02em;
      color: ${T.text};
    }

    /* Mini header for sections */
    .xt-section-h {
      display: flex; align-items: center; gap: 8px;
      padding: 0 20px; margin: 22px 0 10px;
      font-size: 12px; color: ${T.text3};
      letter-spacing: 0.16em; text-transform: uppercase;
    }
    .xt-section-h::before {
      content: ''; width: 14px; height: 1px; background: ${T.text4};
    }

    /* Inline icon helper */
    .xt-ico { display: inline-flex; align-items: center; justify-content: center; }
  `;
  document.head.appendChild(s);
}

// Small atoms used everywhere
function Dot({ c = T.accent, size = 6 }) {
  return <span style={{
    display: 'inline-block', width: size, height: size, borderRadius: 999,
    background: c, flexShrink: 0,
  }} />;
}

function StatusPill({ tone = 'ok', label }) {
  const m = {
    ok:      { c: T.ok,     b: T.okSoft },
    warm:    { c: T.warm,   b: T.warmSoft },
    danger:  { c: T.danger, b: T.dangerSoft },
    accent:  { c: T.accentInk, b: T.accentSoft },
    mute:    { c: T.text2,  b: 'rgba(255,255,255,0.04)' },
  }[tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 10px', borderRadius: 999,
      background: m.b, color: m.c,
      fontSize: 11, letterSpacing: 0.04, fontFamily: T.sans,
      border: `1px solid ${m.b}`,
    }}>
      <Dot c={m.c} size={5} /> {label}
    </span>
  );
}

// Tiny seal/stamp glyph for letter cards — abstract square, no AI-slop iconography
function LetterSeal({ size = 22, color = T.accent }) {
  return (
    <svg width={size} height={size} viewBox="0 0 22 22" fill="none">
      <rect x="2" y="2" width="18" height="18" rx="4" stroke={color} strokeWidth="1" opacity="0.4"/>
      <rect x="6" y="6" width="10" height="10" rx="1.5" stroke={color} strokeWidth="1"/>
      <path d="M11 8v6M8 11h6" stroke={color} strokeWidth="1" strokeLinecap="round" opacity="0.7"/>
    </svg>
  );
}

window.Dot = Dot;
window.StatusPill = StatusPill;
window.LetterSeal = LetterSeal;
