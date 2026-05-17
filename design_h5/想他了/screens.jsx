// 7 mobile screens for 想Ta了
// Each is a pure-presentational component used inside IOSDevice.

// ─────────────────────────────────────────────────────────────
// Screen 1 — Home (情绪入口)
// ─────────────────────────────────────────────────────────────
function HomeScreen() {
  const [recipient, setRecipient] = React.useState('lover');
  const [scene, setScene] = React.useState('miss');
  return (
    <div className="xt-screen" style={{
      paddingTop: 56, paddingBottom: 92,
      backgroundImage: `radial-gradient(120% 60% at 50% -10%, rgba(155,77,202,0.10), transparent 60%)`,
    }}>
      {/* top brand row */}
      <div className="xt-row" style={{ padding: '0 20px', justifyContent: 'space-between' }}>
        <div className="xt-row xt-gap-2">
          <LetterSeal size={18} color={T.text2} />
          <span style={{ fontFamily: T.serif, fontSize: 15, letterSpacing: 0.16, color: T.text2 }}>想Ta了</span>
        </div>
        <div className="xt-row xt-gap-3" style={{ color: T.text3 }}>
          {I.history}{I.settings}
        </div>
      </div>

      {/* Literary greeting — single anchor, generous breathing */}
      <div style={{ padding: '52px 24px 4px' }}>
        <div className="xt-row xt-gap-2" style={{ marginBottom: 14, color: T.text3 }}>
          <span style={{
            display: 'inline-block', width: 18, height: 1,
            background: T.text4, verticalAlign: 'middle',
          }} />
          <span style={{ fontSize: 11, letterSpacing: 0.24, fontFamily: T.mono }}>
            5 / 17 · 周日 · 23:42
          </span>
        </div>
        <div style={{ fontFamily: T.serif, fontSize: 34, lineHeight: 1.35, fontWeight: 500, color: T.text, letterSpacing: 0.02 }}>
          今晚，<br/>
          想对谁说话？
        </div>
        <div style={{ fontSize: 13, color: T.text3, marginTop: 14, lineHeight: 1.75, maxWidth: 280 }}>
          把想说的话，<br/>
          变成更合适的文字和语音。
        </div>
      </div>

      {/* Recipient */}
      <div className="xt-section-h">说给谁</div>
      <div style={{ padding: '0 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <RecipientCard id="lover"  label="恋人"  hint="想他、想她"     active={recipient==='lover'}  />
        <RecipientCard id="family" label="父母"  hint="爸爸、妈妈"     active={recipient==='family'} />
        <RecipientCard id="friend" label="朋友"  hint="老朋友、新朋友" active={recipient==='friend'} />
        <RecipientCard id="self"   label="自己"  hint="写给自己的话"   active={recipient==='self'}   />
      </div>

      {/* Scene — horizontally scrolled chip row, more breathing */}
      <div className="xt-section-h">想表达什么</div>
      <div style={{
        padding: '0 16px',
        display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8,
      }}>
        <SceneChip label="想念"  hint="不知不觉就想了" active={scene==='miss'} />
        <SceneChip label="道歉"  hint="那天，是我不好" />
        <SceneChip label="感谢"  hint="一直没好好说"   />
        <SceneChip label="安慰"  hint="陪你一会儿"     />
        <SceneChip label="晚安"  hint="睡前的一句话"   />
      </div>

      {/* Recent letter — quieter card, treated like a saved memo */}
      <div className="xt-section-h">最近的信笺</div>
      <div style={{ padding: '0 16px' }}>
        <div className="xt-card" style={{
          padding: '14px 14px', display: 'flex', gap: 12, alignItems: 'center',
          background: 'transparent', border: `1px dashed ${T.hairline2}`,
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: T.accentSoft, color: T.accentInk,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>{I.play}</div>
          <div className="xt-grow" style={{ minWidth: 0 }}>
            <div style={{
              fontFamily: T.serif, fontSize: 14, color: T.text, fontWeight: 500,
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>给妈妈，晚安。</div>
            <div style={{ fontSize: 11, color: T.text3, marginTop: 3 }}>
              父母 · 晚安 · 昨晚 23:20
            </div>
          </div>
          <span style={{ fontSize: 11, color: T.text3, fontFamily: T.mono }}>0:48</span>
        </div>
      </div>

      {/* Fixed-feeling CTA at bottom */}
      <div style={{
        position: 'sticky', bottom: 0,
        padding: '20px 16px 18px',
        background: `linear-gradient(to top, ${T.bg} 55%, transparent)`,
        marginTop: 24,
      }}>
        <button className="xt-btn primary full" style={{ height: 54, fontSize: 16, fontFamily: T.serif, letterSpacing: 0.08 }}>
          开始表达
        </button>
        <div className="xt-row" style={{ justifyContent: 'center', marginTop: 12, gap: 10 }}>
          <StatusPill tone="ok" label="MiniMax · 已连接" />
          <span style={{ fontSize: 11, color: T.text4 }}>本机保存 · 不替你发送</span>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 2 — Input (输入真实想法)
// ─────────────────────────────────────────────────────────────
function InputScreen() {
  return (
    <div className="xt-screen">
      <AppBar title="想念 · 给恋人" subtitle="第 1 步 / 共 3 步" leftAction="back" rightAction="close" />
      <StepDots active={0} total={3} labels={['整理想法', '挑选表达', '生成语音']} />

      <div style={{ padding: '24px 20px 4px' }}>
        <div style={{ fontFamily: T.serif, fontSize: 22, lineHeight: 1.5, color: T.text, marginBottom: 8 }}>
          先说说，<br/>
          你现在最想说的一句话？
        </div>
        <div style={{ fontSize: 12, color: T.text3, lineHeight: 1.7 }}>
          写得粗糙、不通顺、零碎都没关系 — 之后会帮你整理。
        </div>
      </div>

      {/* Textarea */}
      <div style={{ padding: '14px 16px' }}>
        <div style={{
          background: T.surface, border: `1px solid ${T.hairline2}`,
          borderRadius: 18, padding: 16,
          minHeight: 160,
        }}>
          <div className="xt-letter" style={{ fontSize: 16, color: T.text }}>
            今天又下雨了，<br/>
            突然想起我们一起淋雨的那天，<br/>
            其实那时候我没说，<br/>
            那一刻我觉得跟你在一起好幸福……
          </div>
          <div style={{
            display: 'inline-block', width: 2, height: 18, background: T.accent,
            marginLeft: 2, marginTop: 6, verticalAlign: 'middle',
            animation: 'xt-blink 1s steps(2) infinite',
          }} />
        </div>
        <style>{`@keyframes xt-blink { 0%,50% { opacity: 1 } 50.01%,100% { opacity: 0 } }`}</style>
        <div className="xt-row" style={{ justifyContent: 'space-between', marginTop: 8 }}>
          <span style={{ fontSize: 11, color: T.text3 }}>越具体越好，AI 帮你保留语气</span>
          <span style={{ fontSize: 11, color: T.text3, fontFamily: T.mono }}>62 / 500</span>
        </div>
      </div>

      {/* Guidance prompts */}
      <div className="xt-section-h">想再说几句也可以</div>
      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[
          '你希望 Ta 听完之后，感受到什么？',
          '有没有不想说得太重、太直接的部分？',
          '上一次你们好好说话，是什么时候？',
        ].map((p, i) => (
          <div key={i} className="xt-card" style={{
            padding: '12px 14px',
            fontSize: 13, color: T.text2,
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <span style={{ fontFamily: T.mono, fontSize: 10, color: T.text3 }}>0{i+1}</span>
            <span className="xt-grow">{p}</span>
            <span style={{ color: T.text3 }}>＋</span>
          </div>
        ))}
      </div>

      {/* CTA — floating */}
      <div style={{ padding: '24px 16px 28px' }}>
        <button className="xt-btn primary full" style={{ height: 52 }}>
          帮我整理表达
        </button>
        <div style={{ fontSize: 11, color: T.text3, textAlign: 'center', marginTop: 10 }}>
          会给你 3 个版本 · 你来挑
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 3 — Suggestions (表达建议)
// ─────────────────────────────────────────────────────────────
function SuggestionsScreen() {
  return (
    <div className="xt-screen" style={{ paddingBottom: 100 }}>
      <AppBar title="挑一个最像你的版本" subtitle="第 2 步 / 共 3 步" />
      <StepDots active={1} total={3} labels={['整理想法', '挑选表达', '生成语音']} />

      {/* AI understanding */}
      <div style={{ padding: '20px 16px 4px' }}>
        <div className="xt-card-elev" style={{ padding: 16 }}>
          <div className="xt-row xt-gap-2" style={{ marginBottom: 8 }}>
            <Dot c={T.accentInk} />
            <span style={{ fontSize: 11, color: T.text3, letterSpacing: 0.12, textTransform: 'uppercase' }}>
              我读到的是
            </span>
          </div>
          <div style={{ fontFamily: T.serif, fontSize: 15, lineHeight: 1.75, color: T.text }}>
            "雨让你想起一次温柔的相处， <br/>
            你其实没有要责怪谁， <br/>
            只是想让他知道：那天，你很幸福。"
          </div>
          <div style={{ fontSize: 11, color: T.text3, marginTop: 12, lineHeight: 1.7, borderTop: `1px solid ${T.hairline}`, paddingTop: 10 }}>
            表达目标 · 想念 + 轻轻的告白，不带索取
          </div>
        </div>
      </div>

      {/* 3 expression cards */}
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <ExpressionCard
          style="克制版"
          fitsFor="想说，但不想给对方压力"
          length="38字"
          text="今天又下雨了。突然想起我们一起淋雨的那天 — 那时候没说，但其实挺幸福的。"
        />
        <ExpressionCard
          style="温柔版"
          fitsFor="想让对方感觉到温度"
          length="54字"
          text="下了一天的雨，路过那条街的时候，又想起跟你一起淋雨那次。那天我没说，但站在你旁边的时候，我心里其实很满。"
          active
        />
        <ExpressionCard
          style="真诚版"
          fitsFor="想认真表达，不绕弯"
          length="76字"
          text="今晚下雨，让我想起跟你一起淋雨那一天。我那时候没告诉你，那一刻我觉得跟你在一起好幸福。我不一定要你回什么，只是想让你知道，这个雨夜，我想到的人是你。"
        />
      </div>

      {/* Risk reminder — soft */}
      <div style={{ padding: '4px 16px 0' }}>
        <div style={{
          background: T.warmSoft, border: `1px solid rgba(224,168,123,0.28)`,
          borderRadius: 14, padding: '12px 14px',
          display: 'flex', gap: 10, alignItems: 'flex-start',
        }}>
          <span style={{ color: T.warm, marginTop: 1 }}>{I.warning}</span>
          <div>
            <div style={{ fontSize: 12, color: T.warm, fontWeight: 500, marginBottom: 4 }}>
              你原话里有一点"我没说，但……"
            </div>
            <div style={{ fontSize: 12, color: T.text2, lineHeight: 1.65 }}>
              这里有一点点埋怨的语气。已经帮你换成 "那一刻很幸福"。如果你更想直接，可以选真诚版。
            </div>
          </div>
        </div>
      </div>

      {/* CTA fixed-feeling bottom */}
      <div style={{
        position: 'sticky', bottom: 0,
        padding: '14px 16px 22px',
        background: `linear-gradient(to top, ${T.bg} 60%, transparent)`,
        marginTop: 16,
      }}>
        <button className="xt-btn primary full" style={{ height: 52 }}>
          用这条 · 生成语音
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 4 — TTS Generation
// ─────────────────────────────────────────────────────────────
function VoiceScreen({ state = 'idle' }) {
  // state: idle | generating | done | failed | quota | no-provider
  return (
    <div className="xt-screen" style={{ paddingBottom: 28 }}>
      <AppBar title="给这段话，配一个声音" subtitle="第 3 步 / 共 3 步" />
      <StepDots active={2} total={3} labels={['整理想法', '挑选表达', '生成语音']} />

      {/* Final text preview */}
      <div style={{ padding: '18px 16px 4px' }}>
        <div className="xt-card" style={{ padding: 16, position: 'relative' }}>
          <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 11, color: T.text3, letterSpacing: 0.12 }}>给恋人 · 想念 · 温柔版</span>
            <button style={{
              background: 'transparent', border: `1px solid ${T.hairline}`,
              color: T.text2, fontSize: 11, padding: '2px 10px',
              borderRadius: 999, cursor: 'pointer',
            }}>编辑文字</button>
          </div>
          <div className="xt-letter" style={{ fontSize: 14, lineHeight: 1.8 }}>
            下了一天的雨，路过那条街的时候，又想起跟你一起淋雨那次。那天我没说，但站在你旁边的时候，我心里其实很满。
          </div>
        </div>
      </div>

      {/* Voice picker */}
      <div className="xt-section-h">声音</div>
      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[
          { name: '温柔女声', desc: '清晰、靠近、稍慢', sel: true },
          { name: '温柔男声', desc: '低、安静、像夜里的电话' },
          { name: '清亮女声', desc: '年轻，适合朋友、自己' },
          { name: '成熟男声', desc: '稳，适合父母' },
        ].map((v, i) => (
          <div key={i} className="xt-row" style={{
            padding: '12px 14px', borderRadius: 14,
            background: v.sel ? T.accentSoft : T.surface,
            border: `1px solid ${v.sel ? T.accentDeep : T.hairline}`,
            gap: 12,
          }}>
            {/* tiny waveform avatar */}
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: T.surface3, display: 'flex', alignItems: 'center',
              justifyContent: 'center', gap: 2, padding: '0 6px',
            }}>
              {[0.4, 0.8, 0.5, 1, 0.6].map((h, k) => (
                <div key={k} style={{
                  width: 2, height: `${h*60}%`,
                  background: v.sel ? T.accent : T.text3, borderRadius: 1,
                }} />
              ))}
            </div>
            <div className="xt-grow">
              <div style={{ fontSize: 14, color: v.sel ? T.accentInk : T.text, fontWeight: 500 }}>{v.name}</div>
              <div style={{ fontSize: 11, color: T.text3, marginTop: 2 }}>{v.desc}</div>
            </div>
            <div style={{
              width: 22, height: 22, borderRadius: 999,
              border: `1.5px solid ${v.sel ? T.accent : T.hairline2}`,
              background: v.sel ? T.accent : 'transparent',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {v.sel && <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 5l2 2 4-4" stroke="white" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>}
            </div>
          </div>
        ))}
      </div>

      {/* Tone chips */}
      <div className="xt-section-h">语气</div>
      <div style={{ padding: '0 16px', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {[
          { l: '克制' },{ l: '温柔', a: true },{ l: '真诚' },{ l: '轻声' },{ l: '睡前' },
        ].map((c, i) => (
          <span key={i} className={`xt-pill ${c.a ? 'active' : ''}`} style={{ padding: '8px 14px', fontSize: 13 }}>
            {c.l}
          </span>
        ))}
      </div>

      {/* Estimated duration */}
      <div style={{ padding: '18px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: T.text3 }}>预计时长</span>
        <span style={{ fontFamily: T.mono, fontSize: 13, color: T.text2 }}>≈ 0:24</span>
      </div>

      {/* generating state preview */}
      {state === 'generating' && (
        <div style={{ padding: '0 16px 8px' }}>
          <div className="xt-card-elev" style={{ padding: 18 }}>
            <div className="xt-row xt-gap-3" style={{ alignItems: 'center' }}>
              <div style={{
                width: 28, height: 28, borderRadius: 999,
                background: `conic-gradient(${T.accent} 70%, ${T.hairline2} 30%)`,
                animation: 'xt-spin 1.2s linear infinite',
              }} />
              <div>
                <div style={{ fontSize: 13, color: T.text }}>正在为你慢慢念出来…</div>
                <div style={{ fontSize: 11, color: T.text3, marginTop: 2 }}>大约 5 秒 · 不需要等到完成也可以离开</div>
              </div>
            </div>
            <style>{`@keyframes xt-spin { to { transform: rotate(360deg) } }`}</style>
          </div>
        </div>
      )}

      {/* CTA */}
      <div style={{ padding: '6px 16px 14px' }}>
        <button className="xt-btn primary full" style={{ height: 54, fontSize: 16 }}>
          生成语音
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 5 — Result / Letter detail
// ─────────────────────────────────────────────────────────────
function LetterScreen() {
  return (
    <div className="xt-screen" style={{
      paddingBottom: 36,
      backgroundImage: `radial-gradient(140% 50% at 50% -10%, rgba(155,77,202,0.10), transparent 70%)`,
    }}>
      <AppBar title="今晚的信笺" rightAction="more" transparent />

      {/* meta strip */}
      <div style={{ padding: '8px 20px 0' }}>
        <div className="xt-row xt-gap-2" style={{ flexWrap: 'wrap', marginBottom: 16 }}>
          <span className="xt-pill" style={{ background: T.accentSoft, color: T.accentInk, borderColor: T.accentDeep }}>给恋人</span>
          <span className="xt-pill">想念</span>
          <span className="xt-pill">温柔版</span>
        </div>
      </div>

      {/* Letter paper — ruled, with cross-hatch seal */}
      <div style={{ padding: '0 16px 18px' }}>
        <div style={{
          background:
            // faint ruled lines on a warm-leaning paper
            `linear-gradient(${T.surface2} 0%, ${T.surface} 100%)`,
          border: `1px solid ${T.hairline2}`,
          borderRadius: '22px 22px 22px 22px',
          padding: '24px 26px 26px',
          position: 'relative', overflow: 'hidden',
        }}>
          {/* ruled-paper underlay */}
          <div style={{
            position: 'absolute', inset: '60px 26px 70px 26px',
            backgroundImage: `repeating-linear-gradient(to bottom, transparent 0, transparent 33px, ${T.hairline} 33px, ${T.hairline} 34px)`,
            pointerEvents: 'none', opacity: 0.6,
          }} />
          {/* corner mark */}
          <div style={{
            position: 'absolute', top: 14, right: 16,
            opacity: 0.45,
          }}>
            <LetterSeal size={18} color={T.text3} />
          </div>

          {/* tiny date marker */}
          <div style={{
            fontSize: 11, color: T.text3, letterSpacing: 0.16,
            marginBottom: 18, fontFamily: T.mono,
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span style={{ width: 12, height: 1, background: T.text4 }} />
            2026 · 05 · 17  ·  23:48
          </div>

          <div className="xt-letter" style={{ fontSize: 17, lineHeight: '34px', fontWeight: 400, position: 'relative' }}>
            下了一天的雨，<br/>
            路过那条街的时候，<br/>
            又想起跟你一起淋雨那次。<br/>
            <br/>
            那天我没说，<br/>
            但站在你旁边的时候，<br/>
            我心里其实很满。
          </div>
          {/* signature */}
          <div style={{
            marginTop: 26, textAlign: 'right',
            fontFamily: T.serif, fontSize: 13, color: T.text2,
            letterSpacing: 0.16,
            position: 'relative',
          }}>
            —— 写于今晚
          </div>
        </div>
      </div>

      {/* full audio player */}
      <FullPlayer voice="温柔女声" tone="温柔" />

      {/* actions */}
      <div style={{ padding: '18px 16px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <button className="xt-btn ghost">{I.copy}<span>复制文字</span></button>
        <button className="xt-btn ghost">{I.download}<span>下载音频</span></button>
        <button className="xt-btn ghost">{I.edit}<span>重新编辑</span></button>
        <button className="xt-btn ghost">{I.refresh}<span>换个语气</span></button>
      </div>

      <div style={{ padding: '14px 16px 0' }}>
        <button className="xt-btn full" style={{ background: T.surface3, border: 'none' }}>
          {I.star}<span>收藏到信笺夹</span>
        </button>
      </div>

      <div style={{ fontSize: 11, color: T.text3, textAlign: 'center', marginTop: 18, lineHeight: 1.7, padding: '0 32px' }}>
        发送给对方的动作，<br/>
        永远由你自己来按。
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 6 — History (信笺夹)
// ─────────────────────────────────────────────────────────────
function HistoryScreen() {
  const items = [
    { t: '给妈妈，晚安。',          rec: '父母', sc: '晚安', when: '昨晚 23:20', dur: '0:48', fav: true,  has: true  },
    { t: '那天的话，是我说重了。', rec: '恋人', sc: '道歉', when: '前天 22:11', dur: '1:12', fav: false, has: true  },
    { t: '谢谢你那次没让我自己待着。', rec: '朋友', sc: '感谢', when: '5月14日', dur: '0:36', fav: true,  has: true  },
    { t: '其实，今天我有点撑不住。',  rec: '自己', sc: '安慰', when: '5月12日', dur: '—',    fav: false, has: false },
    { t: '今晚的月色，让我想起你。',   rec: '恋人', sc: '想念', when: '5月10日', dur: '0:22', fav: false, has: true  },
  ];

  return (
    <div className="xt-screen">
      <div style={{ padding: '54px 20px 6px' }}>
        <div style={{ fontFamily: T.serif, fontSize: 26, fontWeight: 500 }}>信笺夹</div>
        <div style={{ fontSize: 12, color: T.text3, marginTop: 6 }}>
          12 封 · 本地保存，不会上传
        </div>
      </div>

      {/* filter tabs */}
      <div className="xt-row xt-gap-2" style={{ padding: '14px 16px 8px', overflowX: 'auto' }}>
        <span className="xt-pill active">全部</span>
        <span className="xt-pill">恋人 · 4</span>
        <span className="xt-pill">父母 · 3</span>
        <span className="xt-pill">朋友 · 2</span>
        <span className="xt-pill">自己 · 3</span>
        <span className="xt-pill">收藏</span>
      </div>

      {/* list */}
      <div style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {items.map((it, i) => (
          <div key={i} className="xt-card" style={{ padding: 14, display: 'flex', gap: 12 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12, flexShrink: 0,
              background: it.has ? T.accentSoft : T.surface3,
              color: it.has ? T.accentInk : T.text3,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>{it.has ? I.play : <span style={{fontSize: 18, fontFamily: T.serif}}>文</span>}</div>
            <div className="xt-grow" style={{ minWidth: 0 }}>
              <div style={{
                fontFamily: T.serif, fontSize: 14, color: T.text, fontWeight: 500,
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}>{it.t}</div>
              <div className="xt-row" style={{ marginTop: 4, gap: 6, fontSize: 11, color: T.text3 }}>
                <span>{it.rec}</span>
                <span style={{ color: T.text4 }}>·</span>
                <span>{it.sc}</span>
                <span style={{ color: T.text4 }}>·</span>
                <span>{it.when}</span>
              </div>
            </div>
            <div className="xt-col" style={{ alignItems: 'flex-end', gap: 6 }}>
              <span style={{ fontFamily: T.mono, fontSize: 10, color: T.text3 }}>{it.dur}</span>
              {it.fav && <span style={{ color: T.accent }}>{I.star}</span>}
            </div>
          </div>
        ))}
      </div>

      <div style={{ height: 90 }} />
      {/* docked mini player */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 34 }}>
        <MiniPlayer
          title="给妈妈，晚安。"
          recipient="父母" scene="晚安"
        />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 7 — Settings / Status
// ─────────────────────────────────────────────────────────────
function SettingsScreen() {
  return (
    <div className="xt-screen" style={{ paddingBottom: 40 }}>
      <div style={{ padding: '54px 20px 6px' }}>
        <div style={{ fontFamily: T.serif, fontSize: 26, fontWeight: 500 }}>本机状态</div>
        <div style={{ fontSize: 12, color: T.text3, marginTop: 6 }}>
          这里看到的所有信息，只在你自己的设备上。
        </div>
      </div>

      <div className="xt-section-h">服务连接</div>
      <div style={{ padding: '0 16px' }}>
        <div className="xt-card" style={{ padding: 16 }}>
          <div className="xt-row" style={{ justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 14, color: T.text, fontWeight: 500 }}>语音与文案服务</div>
              <div style={{ fontSize: 11, color: T.text3, marginTop: 4 }}>MiniMax · speech-2.5-hd</div>
            </div>
            <StatusPill tone="ok" label="正常" />
          </div>
          <div style={{ height: 1, background: T.hairline, margin: '14px 0' }} />
          <div className="xt-row" style={{ justifyContent: 'space-between' }}>
            <div style={{ fontSize: 12, color: T.text2 }}>本月剩余额度</div>
            <div style={{ fontSize: 12, color: T.text2, fontFamily: T.mono }}>充足</div>
          </div>
          <div style={{
            height: 4, borderRadius: 999, marginTop: 8,
            background: T.hairline2, overflow: 'hidden', position: 'relative',
          }}>
            <div style={{ position: 'absolute', inset: 0, width: '72%', background: T.accent, borderRadius: 999 }}/>
          </div>
        </div>
      </div>

      <div className="xt-section-h">默认偏好</div>
      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[
          { l: '默认声音',     v: '温柔女声' },
          { l: '默认语气',     v: '温柔' },
          { l: '默认表达风格', v: '温柔版' },
          { l: '语速',         v: '稍慢' },
        ].map((r, i) => (
          <div key={i} className="xt-card" style={{
            padding: '14px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: 14, color: T.text }}>{r.l}</span>
            <span className="xt-row xt-gap-2" style={{ color: T.text2, fontSize: 13 }}>
              {r.v}
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M5 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </span>
          </div>
        ))}
      </div>

      <div className="xt-section-h">最近的小问题</div>
      <div style={{ padding: '0 16px' }}>
        <div className="xt-card" style={{ padding: 14 }}>
          <div className="xt-row xt-gap-2" style={{ marginBottom: 6 }}>
            <span style={{ color: T.warm }}>{I.warning}</span>
            <span style={{ fontSize: 13, color: T.text }}>5月15日 · 一次生成失败</span>
          </div>
          <div style={{ fontSize: 12, color: T.text3, lineHeight: 1.7, paddingLeft: 24 }}>
            网络中断了。你的文字已经保存，回到信笺夹可以重试。
          </div>
        </div>
      </div>

      <div className="xt-section-h">本地数据</div>
      <div style={{ padding: '0 16px' }}>
        <div className="xt-card" style={{ padding: 0 }}>
          <div style={{ padding: '14px 16px', borderBottom: `1px solid ${T.hairline}`, display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 14 }}>导出全部信笺</span>
            <span style={{ color: T.text3 }}>›</span>
          </div>
          <div style={{ padding: '14px 16px', borderBottom: `1px solid ${T.hairline}`, display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 14, color: T.danger }}>清除本地数据</span>
          </div>
          <div style={{ padding: '14px 16px', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 14, color: T.text3 }}>开发者面板</span>
            <span style={{ fontSize: 11, color: T.text4, fontFamily: T.mono }}>Debug</span>
          </div>
        </div>
      </div>

      <div style={{ fontSize: 10, color: T.text4, textAlign: 'center', marginTop: 22, fontFamily: T.mono, letterSpacing: 0.2 }}>
        想Ta了 · v0.1.0 · build 0517
      </div>
    </div>
  );
}

Object.assign(window, {
  HomeScreen, InputScreen, SuggestionsScreen, VoiceScreen,
  LetterScreen, HistoryScreen, SettingsScreen,
});
