// letters-store.jsx — localStorage-backed letter persistence
// Single source of truth for the 信笺夹.
// Schema: { id, recipient, scene, style, finalText, voice, tone,
//           favorited, createdAt, openedAt, openCount, title? }

const LS_KEY = 'xiang-ta-le.letters.v1';
const LS_FLAGS = 'xiang-ta-le.flags.v1';

function _read() {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || '[]'); } catch { return []; }
}
function _write(arr) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(arr)); } catch {}
  window.dispatchEvent(new CustomEvent('xt:letters-changed'));
}
function _flag(key, val) {
  try {
    const obj = JSON.parse(localStorage.getItem(LS_FLAGS) || '{}');
    if (val === undefined) return obj[key];
    obj[key] = val;
    localStorage.setItem(LS_FLAGS, JSON.stringify(obj));
  } catch { return undefined; }
}

const Letters = {
  list: () => _read().sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0)),
  get:  (id) => _read().find(l => l.id === id),

  add: (data) => {
    const arr = _read();
    const id = data.id || `L_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
    const item = {
      id,
      favorited: false,
      openCount: 0,
      createdAt: Date.now(),
      ...data,
    };
    _write([item, ...arr]);
    return item;
  },

  update: (id, patch) => {
    const arr = _read();
    const i = arr.findIndex(l => l.id === id);
    if (i < 0) return null;
    const next = { ...arr[i], ...patch };
    arr[i] = next;
    _write(arr);
    return next;
  },

  remove: (id) => _write(_read().filter(l => l.id !== id)),

  touch: (id) => {
    // Open-counter for "想说的还没说" features later
    const arr = _read();
    const i = arr.findIndex(l => l.id === id);
    if (i < 0) return;
    arr[i] = { ...arr[i], openedAt: Date.now(), openCount: (arr[i].openCount || 0) + 1 };
    _write(arr);
  },

  clearAll: () => {
    _write([]);
    try { localStorage.removeItem(LS_FLAGS); } catch {}
  },

  exportJson: () => JSON.stringify({
    schema: 'xiang-ta-le.v1',
    exportedAt: new Date().toISOString(),
    letters: _read(),
  }, null, 2),
};

// React hook: re-renders when storage changes (same-tab or other-tab)
function useLetters() {
  const [v, setV] = React.useState(() => Letters.list());
  React.useEffect(() => {
    const sync = () => setV(Letters.list());
    window.addEventListener('xt:letters-changed', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('xt:letters-changed', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);
  return v;
}

// First-run seed: pre-populate 3 example letters so the user sees a "lived-in"
// history. Uses a flag so we don't re-seed after the user deletes them.
function seedExampleLettersIfNeeded() {
  if (_flag('seeded-v1')) return;
  _flag('seeded-v1', true);
  const now = Date.now();
  const D = 24 * 60 * 60 * 1000;
  const seeds = [
    {
      recipient: 'family', scene: 'night', style: 'gentle',
      voice: 'female-gentle', tone: 'bedtime',
      finalText: '今天的事都先放下吧。晚安。',
      title: '给妈妈，晚安。',
      favorited: true,
      createdAt: now - 1 * D,
    },
    {
      recipient: 'lover', scene: 'sorry', style: 'sincere',
      voice: 'male-gentle', tone: 'sincere',
      finalText: '昨天的话我说重了。其实我心里一直过不去。不是要你原谅，是想让你知道：我看到自己当时不太好的样子，我也不喜欢。',
      title: '那天的话，是我说重了。',
      favorited: false,
      createdAt: now - 2 * D,
    },
    {
      recipient: 'friend', scene: 'thanks', style: 'gentle',
      voice: 'female-bright', tone: 'gentle',
      finalText: '前几天你帮我那一下，其实我心里一直记着，谢谢你。',
      title: '谢谢你那次没让我自己待着。',
      favorited: true,
      createdAt: now - 3 * D,
    },
  ];
  _write([
    ...seeds.map(s => ({ ...Letters.add({ ...s, _skipDispatch: true }), })),
  ].sort((a, b) => b.createdAt - a.createdAt));
  // Note: Letters.add already wrote each. Final dispatched event is enough.
}

// ─── Provider store ───────────────────────────────────────────────
// Status of TTS / LLM. Single global value, observable via hook.
const ProviderStatus = (() => {
  let value = { kind: 'ok', label: '已连接', detail: 'MiniMax · speech-2.5-hd', quotaPct: 0.72 };
  const listeners = new Set();
  return {
    get: () => value,
    set: (next) => { value = { ...value, ...next }; listeners.forEach(l => l(value)); },
    subscribe: (l) => { listeners.add(l); return () => listeners.delete(l); },
  };
})();
function useProvider() {
  const [v, setV] = React.useState(ProviderStatus.get);
  React.useEffect(() => ProviderStatus.subscribe(setV), []);
  return v;
}

// ─── Playback store ───────────────────────────────────────────────
// Single source of truth for the audio playhead so MiniPlayer in
// HistoryScreen and the docked one anywhere else stay in lock-step
// across navigation.
const Playback = (() => {
  let state = { letterId: null, playing: false, secs: 0, totalSecs: 0 };
  const listeners = new Set();
  let interval = null;

  const tick = () => {
    if (!state.playing) return;
    const nextSecs = state.secs + 0.25;
    if (nextSecs >= state.totalSecs) {
      state = { ...state, secs: state.totalSecs, playing: false };
      stopInterval();
    } else {
      state = { ...state, secs: nextSecs };
    }
    listeners.forEach(l => l(state));
  };
  const startInterval = () => { if (!interval) interval = setInterval(tick, 250); };
  const stopInterval  = () => { if (interval) { clearInterval(interval); interval = null; } };

  return {
    get: () => state,
    subscribe: (l) => { listeners.add(l); return () => listeners.delete(l); },
    setSource: (letterId, totalSecs) => {
      if (state.letterId !== letterId) {
        state = { letterId, playing: false, secs: 0, totalSecs };
        listeners.forEach(l => l(state));
      } else if (state.totalSecs !== totalSecs) {
        state = { ...state, totalSecs };
        listeners.forEach(l => l(state));
      }
    },
    play: () => {
      if (state.secs >= state.totalSecs) state = { ...state, secs: 0 };
      state = { ...state, playing: true };
      listeners.forEach(l => l(state));
      startInterval();
    },
    pause: () => {
      state = { ...state, playing: false };
      listeners.forEach(l => l(state));
      stopInterval();
    },
    toggle: () => state.playing ? Playback.pause() : Playback.play(),
    seek: (ratio) => {
      const r = Math.max(0, Math.min(1, ratio));
      state = { ...state, secs: r * state.totalSecs };
      listeners.forEach(l => l(state));
    },
  };
})();
function usePlayback(letterId, totalSecs) {
  const [v, setV] = React.useState(Playback.get);
  React.useEffect(() => Playback.subscribe(setV), []);
  React.useEffect(() => {
    if (letterId && totalSecs) Playback.setSource(letterId, totalSecs);
  }, [letterId, totalSecs]);
  return v;
}

// Light-touch human-readable timestamp (e.g. "昨晚 23:20", "5月14日")
function letterTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  const yest = new Date(now); yest.setDate(yest.getDate() - 1);
  const isYesterday = d.toDateString() === yest.toDateString();
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  if (sameDay) {
    const h = d.getHours();
    if (h >= 22 || h < 4) return `今晚 ${hh}:${mm}`;
    return `今天 ${hh}:${mm}`;
  }
  if (isYesterday) return `昨晚 ${hh}:${mm}`;
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

// Title fallback: first 12 chars of finalText
function letterTitle(letter) {
  if (letter.title) return letter.title;
  const t = (letter.finalText || '').replace(/[\s\n]+/g, '');
  if (t.length <= 14) return t;
  return t.slice(0, 14) + '…';
}

// Approx duration string from text length: chars × 0.28s + 1.5s
function letterDuration(text) {
  const secs = Math.max(3, Math.round((text || '').length * 0.28 + 1.5));
  const m = Math.floor(secs / 60), s = secs % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

// Risk-word detection in user's raw input — drives the SuggestionsScreen
// warning card. Triggers gentle reminder, not refusal.
function detectRisk(text) {
  if (!text) return null;
  const lower = text.toLowerCase();
  const patterns = [
    { kind: 'blame',   words: ['都怪你', '都是你', '凭什么', '你从来', '你就是', '你这个人', '怪谁'] },
    { kind: 'control', words: ['必须', '不准', '不许', '听我的', '我说了算'] },
    { kind: 'test',    words: ['随便你', '算了', '你猜', '看你怎么说'] },
    { kind: 'cold',    words: ['不说了', '懒得理', '没什么好说', '不重要'] },
  ];
  for (const p of patterns) {
    const hit = p.words.find(w => lower.includes(w));
    if (hit) {
      return {
        kind: p.kind,
        hit,
        title: ({
          blame:   `你原话里有"${hit}"`,
          control: `你原话里有"${hit}"`,
          test:    `你原话里有"${hit}"`,
          cold:    `你原话里有"${hit}"`,
        })[p.kind],
        body: ({
          blame:   '这里有一点点指责的味道。可以试着说"我那时候有点难过"，把感受留给自己。',
          control: '这种说法对方听了容易紧。可以换成"我希望……"，让它是请求，不是命令。',
          test:    '这种话容易让对方猜，反而越说越远。可以直接说出你想要的。',
          cold:    '这听起来像是关上门。如果还想说话，可以试着说"我现在不太想讨论这个，但我没走"。',
        })[p.kind],
      };
    }
  }
  return null;
}

Object.assign(window, { Letters, useLetters, ProviderStatus, useProvider, Playback, usePlayback, seedExampleLettersIfNeeded, letterTime, letterTitle, letterDuration, detectRisk });
