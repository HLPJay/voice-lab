// Shared UI atoms — buttons, recipient/scene cards, mini audio player, etc.
// Used across mobile screens and component showcase.

// ─────────────────────────────────────────────────────────────
// Recipient (对象身份) card — 恋人/父母/朋友/自己
// ─────────────────────────────────────────────────────────────
function RecipientCard({ id, label, hint, active, onClick }) {
  // Abstract glyphs — typographic / geometric, not pictographic.
  // Treat them as small "seals" you'd see on stationery.
  const glyphs = {
    lover:  <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <circle cx="10" cy="13" r="6" stroke="currentColor" strokeWidth="1.1" opacity="0.55"/>
              <circle cx="16" cy="13" r="6" stroke="currentColor" strokeWidth="1.1"/>
              <circle cx="13" cy="13" r="1" fill="currentColor"/>
            </svg>,
    family: <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <path d="M4 21V11l9-6 9 6v10" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round"/>
              <path d="M10 21v-5h6v5" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round"/>
            </svg>,
    friend: <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <path d="M5 19v-5a4 4 0 014-4M21 19v-5a4 4 0 00-4-4M9 10V8a2 2 0 014 0M13 8a2 2 0 014 0v2" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>,
    self:   <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <circle cx="13" cy="13" r="9" stroke="currentColor" strokeWidth="1.1" opacity="0.45"/>
              <path d="M13 6v14M6 13h14" stroke="currentColor" strokeWidth="1.1" opacity="0.45"/>
              <circle cx="13" cy="13" r="2.5" fill="currentColor"/>
            </svg>,
  };
  return (
    <div
      onClick={onClick}
      style={{
        flex: 1, padding: '16px 14px', borderRadius: 16,
        background: active ? T.accentSoft : T.surface,
        border: `1px solid ${active ? T.accentDeep : T.hairline}`,
        cursor: 'pointer', transition: 'all .15s',
        display: 'flex', flexDirection: 'column', gap: 10,
        minWidth: 0,
      }}
    >
      <div style={{ color: active ? T.accentInk : T.text2 }}>
        {glyphs[id]}
      </div>
      <div>
        <div style={{ fontSize: 15, fontWeight: 500, color: active ? T.accentInk : T.text, marginBottom: 2 }}>
          {label}
        </div>
        <div style={{ fontSize: 11, color: T.text3, letterSpacing: 0.04 }}>{hint}</div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Scene (情绪场景) chip — 想念/道歉/感谢/安慰/晚安
// ─────────────────────────────────────────────────────────────
function SceneChip({ label, active, hint, onClick }) {
  return (
    <div onClick={onClick} style={{
      padding: '12px 14px', borderRadius: 14, cursor: 'pointer',
      background: active ? T.accentSoft : T.surface,
      border: `1px solid ${active ? T.accentDeep : T.hairline}`,
      transition: 'all .15s', minWidth: 0,
      display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <div style={{
        fontFamily: T.serif, fontSize: 17, fontWeight: 500,
        color: active ? T.accentInk : T.text, letterSpacing: 0.04,
      }}>{label}</div>
      <div style={{ fontSize: 11, color: T.text3 }}>{hint}</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Mini audio player (bottom-stuck or inline)
// ─────────────────────────────────────────────────────────────
function MiniPlayer({ title, recipient, scene, playing = true, t = '0:24', total = '1:08', progress = 0.36 }) {
  return (
    <div style={{
      background: 'rgba(26,21,33,0.92)',
      backdropFilter: 'blur(20px) saturate(160%)',
      WebkitBackdropFilter: 'blur(20px) saturate(160%)',
      borderTop: `1px solid ${T.hairline}`,
      padding: '10px 14px 12px',
    }}>
      <div className="xt-row xt-gap-3">
        {/* play btn */}
        <div style={{
          width: 40, height: 40, borderRadius: 999,
          background: T.accent, display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 14px rgba(155,77,202,0.32)',
          flexShrink: 0,
        }}>
          {playing
            ? <svg width="14" height="14" viewBox="0 0 14 14"><rect x="3" y="2" width="3" height="10" rx="1" fill="white"/><rect x="8" y="2" width="3" height="10" rx="1" fill="white"/></svg>
            : <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 2l9 5-9 5V2z" fill="white"/></svg>}
        </div>
        <div className="xt-grow" style={{ minWidth: 0 }}>
          <div style={{
            fontSize: 13, color: T.text, fontWeight: 500,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            fontFamily: T.serif,
          }}>{title}</div>
          <div style={{ fontSize: 11, color: T.text3, marginTop: 1, letterSpacing: 0.04 }}>
            {recipient} · {scene} · {t} / {total}
          </div>
        </div>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ color: T.text3, flexShrink: 0 }}>
          <path d="M6 8l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      {/* progress */}
      <div style={{
        height: 2, marginTop: 10, borderRadius: 999,
        background: T.hairline2, position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 0, width: `${progress * 100}%`,
          background: T.accent, borderRadius: 999,
        }} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Expanded audio player (for result page / TTS gen)
// ─────────────────────────────────────────────────────────────
function FullPlayer({ progress = 0.32, t = '0:21', total = '1:08', voice = '温柔女声', tone = '真诚' }) {
  // Speech-like envelope: low-energy edges, syllable clusters in the middle.
  // Two summed sine groups + envelope decay → looks like a real waveform, not noise.
  const bars = React.useMemo(() => {
    const N = 64;
    return Array.from({length: N}, (_, i) => {
      const u = i / (N - 1);                                 // 0..1
      const env = Math.sin(Math.PI * u) ** 0.6;              // bell envelope
      const syl = 0.55 + 0.45 * Math.sin(i * 0.42 + 1.3);    // syllables
      const fine = 0.5 + 0.5 * Math.sin(i * 1.18);           // micro detail
      const gap = (i === 21 || i === 22 || i === 44) ? 0.18 : 1; // breath pauses
      const v = env * (syl * 0.65 + fine * 0.35) * gap;
      return Math.max(0.06, Math.min(1, v));
    });
  }, []);
  const playedBars = Math.floor(bars.length * progress);

  return (
    <div className="xt-card-elev" style={{ padding: 18, margin: '0 16px' }}>
      <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 14 }}>
        <div className="xt-row xt-gap-2">
          <Dot c={T.accent} />
          <span style={{ fontSize: 12, color: T.text2, letterSpacing: 0.06 }}>{voice} · {tone}</span>
        </div>
        <span style={{ fontSize: 11, color: T.text3, fontFamily: T.mono }}>{t} / {total}</span>
      </div>
      {/* mirrored waveform — top + bottom for body */}
      <div style={{ position: 'relative', height: 52, marginBottom: 14 }}>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', gap: 2,
        }}>
          {bars.map((v, i) => {
            const played = i < playedBars;
            const isHead = i === playedBars && playedBars > 0;
            return (
              <div key={i} style={{
                flex: 1, height: `${v * 92}%`, borderRadius: 1.2,
                background: played
                  ? (isHead ? T.accentInk : T.accent)
                  : T.hairline2,
                opacity: played ? 1 : 0.85,
                transition: 'background .12s',
              }} />
            );
          })}
        </div>
        {/* playhead line */}
        <div style={{
          position: 'absolute', top: '8%', bottom: '8%',
          left: `calc(${(playedBars / bars.length) * 100}% - 1px)`,
          width: 1.5, background: T.accentInk,
          boxShadow: `0 0 8px ${T.accent}`,
        }} />
      </div>
      <div className="xt-row" style={{ justifyContent: 'space-between', gap: 16 }}>
        <button className="xt-btn ghost" style={{ flex: 1, padding: '10px 12px' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 8l4-4v3h8v2H6v3l-4-4z" fill="currentColor"/>
          </svg>
          重新生成
        </button>
        <div style={{
          width: 56, height: 56, borderRadius: 999, background: T.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 10px 28px rgba(155,77,202,0.32), inset 0 1px 0 rgba(255,255,255,0.16)',
        }}>
          <svg width="20" height="20" viewBox="0 0 20 20"><rect x="5" y="3" width="3.5" height="14" rx="1" fill="white"/><rect x="11.5" y="3" width="3.5" height="14" rx="1" fill="white"/></svg>
        </div>
        <button className="xt-btn ghost" style={{ flex: 1, padding: '10px 12px' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 2v9m0 0L4 7m4 4l4-4M2 13h12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          下载
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Expression (表达版本) card — 克制 / 温柔 / 真诚
// ─────────────────────────────────────────────────────────────
function ExpressionCard({ style, fitsFor, text, active, length = '32字' }) {
  return (
    <div style={{
      padding: 18, borderRadius: 18,
      background: active ? T.surface2 : T.surface,
      border: `1px solid ${active ? T.accentDeep : T.hairline}`,
      position: 'relative',
    }}>
      <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
        <div className="xt-row xt-gap-2">
          <span style={{
            fontFamily: T.serif, fontSize: 15, fontWeight: 500,
            color: active ? T.accentInk : T.text,
          }}>{style}</span>
          {active && <Dot c={T.accent} />}
        </div>
        <span style={{ fontSize: 10, color: T.text3, fontFamily: T.mono }}>{length}</span>
      </div>
      <div className="xt-letter" style={{ fontSize: 15, lineHeight: 1.85, marginBottom: 14 }}>
        {text}
      </div>
      <div style={{ fontSize: 11, color: T.text3, marginBottom: 14, letterSpacing: 0.04 }}>
        适合：{fitsFor}
      </div>
      <div className="xt-row xt-gap-2" style={{ flexWrap: 'wrap' }}>
        <button className="xt-btn ghost" style={{ padding: '8px 12px', fontSize: 12, borderRadius: 999 }}>
          编辑
        </button>
        <button className="xt-btn ghost" style={{ padding: '8px 12px', fontSize: 12, borderRadius: 999 }}>
          复制
        </button>
        <div className="xt-grow" />
        <button className="xt-btn" style={{
          padding: '8px 14px', fontSize: 12, borderRadius: 999,
          background: active ? T.accent : T.surface3,
          color: active ? 'white' : T.text,
          border: 'none',
        }}>
          {active ? '已选择' : '选这条'}
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Generic icon set
// ─────────────────────────────────────────────────────────────
const I = {
  back: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M12 4l-6 6 6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  close: <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>,
  more: <svg width="20" height="4" viewBox="0 0 20 4"><circle cx="2" cy="2" r="1.5" fill="currentColor"/><circle cx="10" cy="2" r="1.5" fill="currentColor"/><circle cx="18" cy="2" r="1.5" fill="currentColor"/></svg>,
  history: <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.3"/><path d="M9 5v4l3 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
  settings: <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.3"/><path d="M9 2v2M9 14v2M2 9h2M14 9h2M3.6 3.6l1.4 1.4M13 13l1.4 1.4M3.6 14.4L5 13M13 5l1.4-1.4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
  play: <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 2l9 5-9 5V2z" fill="currentColor"/></svg>,
  copy: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="3" y="3" width="9" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.3"/><path d="M6 1h7v9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
  download: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2v9m0 0L4 7m4 4l4-4M2 13h12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  star: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2l1.8 3.7 4.2.6-3 3 .7 4.2L8 11.5l-3.7 2 .7-4.2-3-3 4.2-.6L8 2z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/></svg>,
  edit: <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 12l1-3 7-7 2 2-7 7-3 1z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/></svg>,
  refresh: <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M12 7a5 5 0 11-1.5-3.5M12 1.5V5h-3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  warning: <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2l6 11H2L8 2z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/><path d="M8 6v3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/><circle cx="8" cy="11.5" r="0.7" fill="currentColor"/></svg>,
};

// ─────────────────────────────────────────────────────────────
// Top app bar (compact, for inner pages)
// ─────────────────────────────────────────────────────────────
function AppBar({ title, leftAction = 'back', rightAction = 'more', subtitle, transparent = false, onTopOf }) {
  return (
    <div style={{
      padding: '50px 16px 12px',
      display: 'flex', alignItems: 'center', gap: 12,
      background: transparent ? 'transparent' : T.bg,
      borderBottom: transparent ? 'none' : `1px solid ${T.hairline}`,
      position: 'relative', zIndex: 5,
    }}>
      <button style={{
        width: 36, height: 36, borderRadius: 999,
        background: T.surface, border: `1px solid ${T.hairline}`,
        color: T.text2, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 0,
      }}>{I[leftAction] || I.back}</button>
      <div className="xt-grow" style={{ textAlign: 'center', minWidth: 0 }}>
        {subtitle && <div style={{ fontSize: 10, color: T.text3, letterSpacing: 0.12, textTransform: 'uppercase' }}>{subtitle}</div>}
        <div style={{ fontSize: 15, color: T.text, fontWeight: 500, fontFamily: T.serif, letterSpacing: 0.04, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</div>
      </div>
      <button style={{
        width: 36, height: 36, borderRadius: 999,
        background: T.surface, border: `1px solid ${T.hairline}`,
        color: T.text2, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 0,
      }}>{I[rightAction] || I.more}</button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Phase steps indicator
// ─────────────────────────────────────────────────────────────
function StepDots({ active = 0, total = 4, labels = [] }) {
  return (
    <div className="xt-row xt-gap-2" style={{ padding: '0 16px', marginTop: 6, alignItems: 'flex-start' }}>
      {Array.from({length: total}).map((_, i) => (
        <div key={i} style={{ flex: 1, opacity: i <= active ? 1 : 0.45 }}>
          <div style={{
            height: 2, borderRadius: 1,
            background: i <= active ? T.accent : T.hairline2,
          }} />
          <div style={{ fontSize: 10, color: i <= active ? T.text2 : T.text3, marginTop: 6, letterSpacing: 0.06 }}>
            {labels[i] || ''}
          </div>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, { RecipientCard, SceneChip, MiniPlayer, FullPlayer, ExpressionCard, I, AppBar, StepDots });
