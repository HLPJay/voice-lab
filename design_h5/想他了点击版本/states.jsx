// State coverage views + global-component showcase
// These are full mobile screens but focused on specific states.

// ─────────────────────────────────────────────────────────────
// Generating / Error / Quota / NoProvider — bottom-sheet variants
// Each is rendered as a mini-screen for the canvas.
// ─────────────────────────────────────────────────────────────

function StateSheet({ tone = 'accent', title, body, primary, secondary, tertiary, illustration, onPrimary, onSecondary, onClose }) {
  const tones = {
    accent: { ring: T.accent,     bg: T.accentSoft,  ink: T.accentInk },
    warm:   { ring: T.warm,       bg: T.warmSoft,    ink: T.warm },
    danger: { ring: T.danger,     bg: T.dangerSoft,  ink: T.danger },
    ok:     { ring: T.ok,         bg: T.okSoft,      ink: T.ok },
  }[tone];
  return (
    <div className="xt-screen" style={{ paddingTop: 64, paddingBottom: 30, position: 'relative', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      {onClose && (
        <button onClick={onClose} style={{
          position: 'absolute', top: 50, left: 16, zIndex: 20,
          width: 36, height: 36, borderRadius: 999,
          background: T.surface, border: `1px solid ${T.hairline}`,
          color: T.text2, cursor: 'pointer', padding: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M12 4l-6 6 6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
      )}
      <div style={{ padding: '0 24px', textAlign: 'center', marginTop: 40 }}>
        <div style={{
          width: 78, height: 78, borderRadius: 999, margin: '0 auto 24px',
          background: tones.bg,
          color: tones.ink,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          border: `1px solid ${tones.ring}`,
        }}>{illustration}</div>
        <div style={{ fontFamily: T.serif, fontSize: 22, color: T.text, fontWeight: 500, marginBottom: 12, lineHeight: 1.5 }}>
          {title}
        </div>
        <div style={{ fontSize: 13, color: T.text2, lineHeight: 1.8 }}>
          {body}
        </div>
      </div>
      <div style={{ flex: 1 }} />
      <div style={{ padding: '36px 16px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {primary   && <button onClick={onPrimary}   className="xt-btn primary full" style={{ height: 50 }}>{primary}</button>}
        {secondary && <button onClick={onSecondary} className="xt-btn ghost full">{secondary}</button>}
        {tertiary  && <div style={{ fontSize: 12, color: T.text3, textAlign: 'center', marginTop: 6 }}>{tertiary}</div>}
      </div>
    </div>
  );
}

function Spin() {
  return (
    <div style={{
      width: 30, height: 30, borderRadius: 999,
      background: `conic-gradient(var(--xt-accent) 70%, transparent 30%)`,
      animation: 'xt-spin 1.1s linear infinite',
      mask: 'radial-gradient(circle, transparent 9px, black 10px)',
      WebkitMask: 'radial-gradient(circle, transparent 9px, black 10px)',
    }} />
  );
}

function StateGenerating({ ctx }) {
  return (
    <StateSheet
      tone="accent"
      illustration={<Spin />}
      title={<>正在为你慢慢念出来…</>}
      body={<>大约还有 4 秒。<br/>不需要等完成也可以离开，<br/>生成好之后会出现在信笺夹。</>}
      secondary="先去做别的"
      tertiary="温柔女声 · 温柔 · ≈ 0:24"
      onSecondary={() => ctx?.nav('back')}
      onClose={() => ctx?.nav('back')}
    />
  );
}

function StateQuota({ ctx }) {
  return (
    <StateSheet
      tone="warm"
      illustration={<svg width="34" height="34" viewBox="0 0 34 34" fill="none">
        <circle cx="17" cy="17" r="13" stroke="currentColor" strokeWidth="1.3"/>
        <path d="M17 9v9l5 3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      </svg>}
      title={<>今天的语音额度，<br/>用得差不多了</>}
      body={<>你今天已经生成了 14 条。<br/>文字已经帮你保存，明天回来还可以接着生成语音。</>}
      primary="只保存文字"
      secondary="查看额度详情"
      onPrimary={() => ctx?.nav('letter')}
      onSecondary={() => ctx?.nav('settings')}
      onClose={() => ctx?.nav('back')}
    />
  );
}

function StateNoProvider({ ctx }) {
  return (
    <StateSheet
      tone="danger"
      illustration={<svg width="34" height="34" viewBox="0 0 34 34" fill="none">
        <rect x="6" y="10" width="22" height="16" rx="3" stroke="currentColor" strokeWidth="1.3"/>
        <path d="M12 10V7a5 5 0 1110 0v3" stroke="currentColor" strokeWidth="1.3"/>
      </svg>}
      title={<>语音服务还没有连上</>}
      body={<>暂时没办法生成声音，<br/>但你写的字、整理好的版本，已经都帮你保留了。</>}
      primary="去填一下配置"
      secondary="只保存文字"
      tertiary="不需要技术参数，跟着指引一步一步来"
      onPrimary={() => ctx?.nav('settings')}
      onSecondary={() => ctx?.nav('letter')}
      onClose={() => ctx?.nav('back')}
    />
  );
}

function StateFailed({ ctx }) {
  return (
    <StateSheet
      tone="warm"
      illustration={<svg width="34" height="34" viewBox="0 0 34 34" fill="none">
        <path d="M17 5l12 22H5L17 5z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
        <path d="M17 14v6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
        <circle cx="17" cy="23.5" r="1" fill="currentColor"/>
      </svg>}
      title={<>这次没能生成成功</>}
      body={<>网络好像不太稳定。<br/>文字已经保存了，再试一次就好。</>}
      primary="再试一次"
      secondary="先放一放"
      onPrimary={() => ctx?.nav('letter')}
      onSecondary={() => ctx?.nav('back')}
      onClose={() => ctx?.nav('back')}
    />
  );
}

function StateEmpty() {
  return (
    <div className="xt-screen" style={{ paddingTop: 54, paddingBottom: 30 }}>
      <div style={{ padding: '0 20px' }}>
        <div style={{ fontFamily: T.serif, fontSize: 26, fontWeight: 500 }}>信笺夹</div>
      </div>
      <div style={{
        margin: '64px 24px 0', padding: '36px 22px',
        border: `1px dashed ${T.hairline2}`,
        borderRadius: 22, textAlign: 'center',
      }}>
        <div style={{
          width: 64, height: 64, borderRadius: 16, margin: '0 auto 18px',
          background: T.surface2, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: T.text3,
        }}>
          <LetterSeal size={28} color={T.text3} />
        </div>
        <div style={{ fontFamily: T.serif, fontSize: 18, color: T.text, marginBottom: 8 }}>
          还没有写过一封信
        </div>
        <div style={{ fontSize: 13, color: T.text2, lineHeight: 1.8 }}>
          想说的话，写下来之后<br/>就会变成一封小信笺，<br/>留在这里。
        </div>
        <button className="xt-btn primary" style={{ marginTop: 22, padding: '12px 28px' }}>
          写第一封
        </button>
      </div>
    </div>
  );
}

function StateSavedToast() {
  return (
    <div className="xt-screen" style={{ paddingTop: 54, position: 'relative', overflow: 'hidden' }}>
      {/* dimmed letter behind */}
      <div style={{ opacity: 0.4, filter: 'blur(0.5px)', pointerEvents: 'none' }}>
        <LetterScreen />
      </div>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'rgba(10,8,14,0.55)', backdropFilter: 'blur(4px)',
      }} />
      {/* sheet */}
      <div style={{
        position: 'absolute', left: 12, right: 12, bottom: 44,
        background: T.surface2,
        border: `1px solid ${T.hairline2}`,
        borderRadius: 24, padding: '22px 22px 18px',
        boxShadow: '0 30px 60px rgba(0,0,0,0.4)',
      }}>
        <div className="xt-row xt-gap-3" style={{ marginBottom: 14 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 999,
            background: T.okSoft, color: T.ok,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: `1px solid ${T.ok}`,
          }}>
            <svg width="18" height="18" viewBox="0 0 18 18"><path d="M3 9l4 4 8-8" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </div>
          <div>
            <div style={{ fontFamily: T.serif, fontSize: 16, fontWeight: 500 }}>已经替你收好了</div>
            <div style={{ fontSize: 12, color: T.text3, marginTop: 2 }}>《今晚的信笺》已保存到信笺夹</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <button className="xt-btn ghost">继续编辑</button>
          <button className="xt-btn ghost">下载音频</button>
          <button className="xt-btn ghost" style={{ gridColumn: 'span 2' }}>回到首页</button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Component-system showcase (button / pill / card etc.) — used outside iOS frame
// ─────────────────────────────────────────────────────────────
function ComponentShowcase() {
  return (
    <div style={{
      background: T.bg, color: T.text, padding: 28, borderRadius: 22,
      border: `1px solid ${T.hairline}`, fontFamily: T.sans,
      width: 520, display: 'flex', flexDirection: 'column', gap: 22,
    }}>
      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>按钮 Buttons</div>
        <div className="xt-row xt-gap-3" style={{ flexWrap: 'wrap' }}>
          <button className="xt-btn primary">主要操作</button>
          <button className="xt-btn">次要操作</button>
          <button className="xt-btn ghost">幽灵按钮</button>
          <button className="xt-btn" style={{ background: T.dangerSoft, color: T.danger, border: 'none' }}>危险操作</button>
        </div>
      </div>

      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>标签 Pills</div>
        <div className="xt-row xt-gap-2" style={{ flexWrap: 'wrap' }}>
          <span className="xt-pill">默认</span>
          <span className="xt-pill active">激活</span>
          <StatusPill tone="ok" label="MiniMax · 已连接" />
          <StatusPill tone="warm" label="额度紧张" />
          <StatusPill tone="danger" label="未配置" />
          <StatusPill tone="mute" label="离线" />
        </div>
      </div>

      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>输入框 Inputs</div>
        <div className="xt-col xt-gap-3">
          <div style={{
            background: T.surface, border: `1px solid ${T.hairline2}`,
            borderRadius: 14, padding: '12px 14px',
            fontFamily: T.serif, fontSize: 15,
          }}>
            <span style={{ color: T.text3 }}>例：今天又下雨了……</span>
          </div>
          <div style={{
            background: T.surface, border: `1px solid ${T.accent}`,
            borderRadius: 14, padding: '12px 14px',
          }}>
            <span style={{ color: T.text }}>站在你旁边的时候，我心里其实很满。</span>
            <span style={{
              display: 'inline-block', width: 2, height: 16, background: T.accent,
              marginLeft: 2, verticalAlign: 'middle',
            }} />
          </div>
        </div>
      </div>

      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>对象选择器 Recipient</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
          <RecipientCard id="lover"  label="恋人"  hint="想他想她" active />
          <RecipientCard id="family" label="父母"  hint="爸妈" />
          <RecipientCard id="friend" label="朋友"  hint="老友" />
          <RecipientCard id="self"   label="自己"  hint="独白" />
        </div>
      </div>

      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>表达卡片 Expression</div>
        <ExpressionCard
          style="温柔版"
          fitsFor="想让对方感觉到温度"
          length="54字"
          text="下了一天的雨，路过那条街的时候，又想起跟你一起淋雨那次。"
          active
        />
      </div>

      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>底部播放器 Mini Player</div>
        <div style={{ borderRadius: 16, overflow: 'hidden', border: `1px solid ${T.hairline}` }}>
          <MiniPlayer title="给妈妈，晚安。" recipient="父母" scene="晚安" t="0:24" total="0:48" progress={0.5} />
        </div>
      </div>

      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>语音配置卡 Voice Config</div>
        <div className="xt-card" style={{ padding: 14 }}>
          <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 13, color: T.text2 }}>声音</span>
            <span style={{ fontSize: 13, color: T.text, fontWeight: 500 }}>温柔女声</span>
          </div>
          <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 13, color: T.text2 }}>语气</span>
            <span style={{ fontSize: 13, color: T.text }}>温柔</span>
          </div>
          <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 13, color: T.text2 }}>语速</span>
            <span style={{ fontSize: 13, color: T.text }}>稍慢</span>
          </div>
          <div className="xt-row" style={{ justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: T.text2 }}>预计时长</span>
            <span style={{ fontSize: 13, color: T.text, fontFamily: T.mono }}>≈ 0:24</span>
          </div>
        </div>
      </div>

      <div>
        <div style={{ fontFamily: T.serif, fontSize: 18, fontWeight: 500, marginBottom: 12 }}>错误解释 Errors</div>
        <div className="xt-col xt-gap-2">
          {[
            { t: '语音服务还没连上',   d: '去填一下配置，跟着指引一步一步来', s: 'danger' },
            { t: 'API Key 还差一点',  d: '到设置 → 服务连接 里粘贴一次就好', s: 'danger' },
            { t: '今天的语音额度紧张', d: '文字已经保存，明天回来还能生成',   s: 'warm'   },
            { t: '网络好像不太稳',     d: '再试一次，文字不会丢',              s: 'warm'   },
            { t: 'TTS 这次没出来',     d: '可以再试一次，或者只保存文字',      s: 'warm'   },
            { t: 'AI 这一版没整理好', d: '换个说法再试，或者直接用你原话',    s: 'warm'   },
            { t: '音频没能存进相册',   d: '检查一下"允许保存到相册"',           s: 'warm'   },
          ].map((r, i) => {
            const c = r.s === 'danger' ? T.danger : T.warm;
            const b = r.s === 'danger' ? T.dangerSoft : T.warmSoft;
            return (
              <div key={i} style={{
                background: b, border: `1px solid ${b}`, borderRadius: 12,
                padding: '10px 12px', display: 'flex', gap: 10,
              }}>
                <span style={{ color: c, marginTop: 2 }}>{I.warning}</span>
                <div>
                  <div style={{ fontSize: 13, color: c, fontWeight: 500 }}>{r.t}</div>
                  <div style={{ fontSize: 11, color: T.text2, marginTop: 2, lineHeight: 1.6 }}>{r.d}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  StateGenerating, StateQuota, StateNoProvider, StateFailed,
  StateEmpty, StateSavedToast, ComponentShowcase, StateSheet,
});
