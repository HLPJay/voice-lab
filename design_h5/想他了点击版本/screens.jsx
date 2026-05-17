// 7 mobile screens for 想Ta了
// Each is a pure-presentational component used inside IOSDevice.

// ─────────────────────────────────────────────────────────────
// Constants — labels & sample expression bank
// ─────────────────────────────────────────────────────────────
const RECIPIENT_LABELS = { lover: '恋人', family: '父母', friend: '朋友', self: '自己' };
const SCENE_LABELS     = { miss: '想念', sorry: '道歉', thanks: '感谢', comfort: '安慰', night: '晚安' };
const STYLE_LABELS     = { restrained: '克制版', gentle: '温柔版', sincere: '真诚版' };

// Three styles × the 'miss' scene; other scenes share the same shape.
// Real product replaces this with an LLM call.
const EXPRESSION_BANK = {
  miss: {
    summary: '"雨让你想起一次温柔的相处，你其实没有要责怪谁，只是想让他知道：那天，你很幸福。"',
    intent:  '想念 + 轻轻的告白，不带索取',
    restrained: '今天又下雨了。突然想起我们一起淋雨的那天 —— 那时候没说，但其实挺幸福的。',
    gentle:     '下了一天的雨，路过那条街的时候，又想起跟你一起淋雨那次。那天我没说，但站在你旁边的时候，我心里其实很满。',
    sincere:    '今晚下雨，让我想起跟你一起淋雨那一天。我那时候没告诉你，那一刻我觉得跟你在一起好幸福。我不一定要你回什么，只是想让你知道，这个雨夜，我想到的人是你。',
  },
  sorry: {
    summary: '"你知道那天的话说重了，想跟对方说一声对不起，也想让自己心里好过一点。"',
    intent:  '认错 + 自责，不推卸、不解释',
    restrained: '那天的话，是我说重了。对不起。',
    gentle:     '那天的话我反复想过很多次。说出口的时候有刺，是我没控制好。对不起。',
    sincere:    '昨天的话我说重了。其实我心里一直过不去。不是要你原谅，是想让你知道：我看到自己当时不太好的样子，我也不喜欢。',
  },
  thanks: {
    summary: '"有一份感谢一直没说出口，今天想让对方知道。"',
    intent:  '感谢，不夸张、不亏欠',
    restrained: '上次的事，谢谢你。',
    gentle:     '前几天你帮我那一下，其实我心里一直记着，谢谢你。',
    sincere:    '一直没跟你好好说过这句话 —— 谢谢你。那天你没问太多，就站在我旁边，对我来说真的很重要。',
  },
  comfort: {
    summary: '"对方今天不太好，你想安静地陪一会儿，不解决问题。"',
    intent:  '陪伴 + 接住情绪',
    restrained: '我在。',
    gentle:     '今天不用解释，慢慢来。我就在这。',
    sincere:    '不用现在告诉我发生了什么。你想说我就听，不想说我们也可以什么都不说。我不走。',
  },
  night: {
    summary: '"睡前想轻轻说一声晚安，不打扰、不索取。"',
    intent:  '晚安，留一份安静',
    restrained: '晚安。',
    gentle:     '今天的事都先放下吧。晚安。',
    sincere:    '该睡了。今天你做得够多了。明天的事明天再说，先把自己交给被窝。晚安。',
  },
};

const RAW_EXAMPLES = {
  miss:    '今天又下雨了，突然想起我们一起淋雨的那天，其实那时候我没说，那一刻我觉得跟你在一起好幸福。',
  sorry:   '昨天的话我说重了。其实知道你最近本来就累，我还那样说，是我不好。',
  thanks:  '上次我没办法的时候，你一直没多问，就一直在。我后来其实都没好好跟你说过谢谢。',
  comfort: '你今天好像不太对，没逼你说，只是想让你知道，我在的。',
  night:   '今天先到这吧，别再想工作的事了。早点睡。',
};

const GUIDANCE_PROMPTS = {
  miss:    ['你希望 Ta 听完之后，感受到什么？', '有没有不想说得太重、太直接的部分？', '你们上一次好好说话，是什么时候？'],
  sorry:   ['你想为哪件事道歉？', '你希望对方知道你看到了哪些地方做得不好？', '你不想说成是在找借口的部分？'],
  thanks:  ['你想感谢的是哪件事？', '你希望对方知道，那件事对你来说意味着什么？', '有没有以前一直没说出口的话？'],
  comfort: ['对方现在在经历什么？', '你想让对方感受到什么？', '有什么是你不想说的，比如"你要坚强"这种？'],
  night:   ['今天对方过得怎么样？', '想留给对方的，是哪一种放松的感觉？', '有什么是不打算今晚说，留到明天再说的？'],
};

// ─────────────────────────────────────────────────────────────
// Screen 1 — Home (情绪入口)
// ─────────────────────────────────────────────────────────────
function HomeScreen({ ctx }) {
  const [localRecipient, setLocalRecipient] = React.useState('lover');
  const [localScene, setLocalScene] = React.useState('miss');
  const recipient = ctx?.flow?.recipient ?? localRecipient;
  const scene     = ctx?.flow?.scene     ?? localScene;
  const setRecipient = (v) => ctx ? ctx.setFlow(s => ({...s, recipient: v})) : setLocalRecipient(v);
  const setScene     = (v) => ctx ? ctx.setFlow(s => ({...s, scene: v})) : setLocalScene(v);
  const letters = useLetters();
  const recent  = letters[0];
  const provider = useProvider();

  // "Want to revisit?" — pick a letter that's >7 days old and rarely opened.
  // Shows a single gentle prompt at top of recent section.
  const revisit = React.useMemo(() => {
    const week = 7 * 24 * 60 * 60 * 1000;
    const now = Date.now();
    const cand = letters
      .filter(l => l.createdAt && (now - l.createdAt) > week && (l.openCount || 0) < 3)
      .sort((a, b) => (a.openedAt || a.createdAt) - (b.openedAt || b.createdAt));
    return cand[0] || null;
  }, [letters]);

  const openRecent = () => {
    if (!recent) { ctx?.nav('history'); return; }
    ctx.setFlow(s => ({ ...s, letterId: recent.id }));
    ctx.nav('letter');
  };
  const openRevisit = () => {
    ctx.setFlow(s => ({ ...s, letterId: revisit.id }));
    ctx.nav('letter');
  };

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
          <span onClick={() => ctx?.nav('history')} style={{ cursor: 'pointer', padding: 4 }}>{I.history}</span>
          <span onClick={() => ctx?.nav('settings')} style={{ cursor: 'pointer', padding: 4 }}>{I.settings}</span>
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
        <RecipientCard id="lover"  label="恋人"  hint="想他、想她"     active={recipient==='lover'}  onClick={() => setRecipient('lover')} />
        <RecipientCard id="family" label="父母"  hint="爸爸、妈妈"     active={recipient==='family'} onClick={() => setRecipient('family')} />
        <RecipientCard id="friend" label="朋友"  hint="老朋友、新朋友" active={recipient==='friend'} onClick={() => setRecipient('friend')} />
        <RecipientCard id="self"   label="自己"  hint="写给自己的话"   active={recipient==='self'}   onClick={() => setRecipient('self')} />
      </div>

      {/* Scene — horizontally scrolled chip row, more breathing */}
      <div className="xt-section-h">想表达什么</div>
      <div style={{
        padding: '0 16px',
        display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8,
      }}>
        <SceneChip label="想念"  hint="不知不觉就想了" active={scene==='miss'}    onClick={() => setScene('miss')} />
        <SceneChip label="道歉"  hint="那天，是我不好" active={scene==='sorry'}   onClick={() => setScene('sorry')} />
        <SceneChip label="感谢"  hint="一直没好好说"   active={scene==='thanks'}  onClick={() => setScene('thanks')} />
        <SceneChip label="安慰"  hint="陪你一会儿"     active={scene==='comfort'} onClick={() => setScene('comfort')} />
        <SceneChip label="晚安"  hint="睡前的一句话"   active={scene==='night'}   onClick={() => setScene('night')} />
      </div>

      {/* Recent letter — pulls from storage */}
      <div className="xt-section-h">最近的信笺</div>
      <div style={{ padding: '0 16px' }}>
        <div onClick={openRecent} className="xt-card" style={{
          padding: '14px 14px', display: 'flex', gap: 12, alignItems: 'center',
          background: 'transparent', border: `1px dashed ${T.hairline2}`,
          cursor: 'pointer',
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: recent ? T.accentSoft : T.surface3,
            color: recent ? T.accentInk : T.text3,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>{recent ? I.play : <span style={{ fontFamily: T.serif, fontSize: 17 }}>笺</span>}</div>
          <div className="xt-grow" style={{ minWidth: 0 }}>
            <div style={{
              fontFamily: T.serif, fontSize: 14, color: T.text, fontWeight: 500,
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>{recent ? letterTitle(recent) : '还没有保存的信笺'}</div>
            <div style={{ fontSize: 11, color: T.text3, marginTop: 3 }}>
              {recent
                ? `${RECIPIENT_LABELS[recent.recipient] || ''} · ${SCENE_LABELS[recent.scene] || ''} · ${letterTime(recent.createdAt)}`
                : '写第一封 → 它会出现在这里'}
            </div>
          </div>
          {recent && <span style={{ fontSize: 11, color: T.text3, fontFamily: T.mono }}>{letterDuration(recent.finalText)}</span>}
        </div>

        {/* Want-to-revisit gentle nudge */}
        {revisit && revisit.id !== recent?.id && (
          <div onClick={openRevisit} style={{
            marginTop: 10, padding: '12px 14px',
            border: `1px solid ${T.hairline}`,
            borderRadius: 14, cursor: 'pointer',
            display: 'flex', alignItems: 'flex-start', gap: 10,
            background: 'rgba(255,255,255,0.02)',
          }}>
            <span style={{ color: T.accentInk, marginTop: 2 }}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><title>提醒</title><circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.2"/><path d="M7 4v3l2 1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>
            </span>
            <div className="xt-grow" style={{ minWidth: 0 }}>
              <div style={{ fontSize: 12, color: T.text2, lineHeight: 1.7 }}>
                《{letterTitle(revisit)}》写下来{Math.round((Date.now() - revisit.createdAt) / 86400000)} 天了 —— 再读一次？
              </div>
            </div>
            <span style={{ color: T.text3, fontSize: 16 }}>›</span>
          </div>
        )}
      </div>

      {/* Fixed-feeling CTA at bottom */}
      <div style={{
        position: 'sticky', bottom: 0,
        padding: '20px 16px 18px',
        background: `linear-gradient(to top, ${T.bg} 55%, transparent)`,
        marginTop: 24,
      }}>
        <button onClick={() => ctx?.nav('input')} className="xt-btn primary full" style={{ height: 54, fontSize: 16, fontFamily: T.serif, letterSpacing: 0.08 }}>
          开始表达
        </button>
        <div className="xt-row" style={{ justifyContent: 'center', marginTop: 12, gap: 10 }}>
          <StatusPill
            tone={provider.kind === 'ok' ? 'ok' : provider.kind === 'quota' ? 'warm' : 'danger'}
            label={`MiniMax · ${provider.label}`}
          />
          <span style={{ fontSize: 11, color: T.text4 }}>本机保存 · 不替你发送</span>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 2 — Input (输入真实想法)
// ─────────────────────────────────────────────────────────────
function InputScreen({ ctx }) {
  const rec = RECIPIENT_LABELS[ctx?.flow?.recipient] || '恋人';
  const sc  = SCENE_LABELS[ctx?.flow?.scene] || '想念';
  const bank = EXPRESSION_BANK[ctx?.flow?.scene] || EXPRESSION_BANK.miss;
  const raw = ctx?.flow?.rawText || '';
  const setRaw = (v) => ctx?.setFlow(s => ({ ...s, rawText: v.slice(0, 500) }));
  const example = RAW_EXAMPLES[ctx?.flow?.scene] || RAW_EXAMPLES.miss;
  const guidance = GUIDANCE_PROMPTS[ctx?.flow?.scene] || GUIDANCE_PROMPTS.miss;
  const taRef = React.useRef(null);
  const risk = detectRisk(raw);

  const fillExample = () => setRaw(example);
  const appendPrompt = (p) => {
    const newVal = raw ? `${raw}\n\n${p}\n` : `${p}\n`;
    setRaw(newVal);
    setTimeout(() => taRef.current && (taRef.current.focus(), taRef.current.setSelectionRange(newVal.length, newVal.length)), 50);
  };

  const valid = raw.trim().length >= 4;
  const riskHint = detectRisk(raw);

  return (
    <div className="xt-screen">
      <AppBar title={`${sc} · 给${rec}`} subtitle="第 1 步 / 共 3 步" leftAction="back" rightAction="close" onLeft={() => ctx?.nav('back')} onRight={() => ctx?.nav('home')} />
      <StepDots active={0} total={3} labels={['整理想法', '挑选表达', '生成语音']} />

      <div style={{ padding: '24px 20px 4px' }}>
        <div style={{ fontFamily: T.serif, fontSize: 22, lineHeight: 1.5, color: T.text, marginBottom: 8 }}>
          先说说，<br/>
          你现在最想说的一句话？
        </div>
        <div style={{ fontSize: 12, color: T.text3, lineHeight: 1.7 }}>
          写得粗糙、不通顺、零碎都没关系 —— 之后会帮你整理。
        </div>
      </div>

      {/* Real textarea */}
      <div style={{ padding: '14px 16px' }}>
        <div style={{
          background: T.surface, border: `1px solid ${raw ? T.accentDeep : T.hairline2}`,
          borderRadius: 18, padding: 16,
          transition: 'border-color .15s',
        }}>
          <textarea
            ref={taRef}
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder={`例如：${example}`}
            rows={6}
            style={{
              width: '100%', minHeight: 132,
              background: 'transparent', border: 0, outline: 'none',
              color: T.text, resize: 'none',
              fontFamily: T.serif, fontSize: 16, lineHeight: 1.85,
              caretColor: T.accent,
            }}
          />
        </div>
        <div className="xt-row" style={{ justifyContent: 'space-between', marginTop: 8 }}>
          <button
            onClick={fillExample}
            style={{
              background: 'transparent', border: 0, padding: 0,
              fontSize: 11, color: T.accentInk, cursor: 'pointer',
              textDecoration: 'underline', textUnderlineOffset: 3,
              textDecorationColor: T.accentDeep,
            }}
          >用一个例子开始</button>
          <span style={{ fontSize: 11, color: T.text3, fontFamily: T.mono }}>{raw.length} / 500</span>
        </div>

        {/* Real-time gentle risk hint — only appears for flagged phrases. */}
        {riskHint && (
          <div style={{
            marginTop: 10, padding: '10px 12px',
            background: T.warmSoft, border: `1px solid rgba(224,168,123,0.22)`,
            borderRadius: 12, display: 'flex', gap: 8, alignItems: 'flex-start',
            animation: 'spaCardIn .35s both',
          }}>
            <span style={{ color: T.warm, marginTop: 1 }}>{I.warning}</span>
            <div style={{ fontSize: 11.5, color: T.text2, lineHeight: 1.65 }}>
              {riskHint.body}
            </div>
          </div>
        )}
      </div>

      {/* Guidance prompts — tap to append */}
      <div className="xt-section-h">想再说几句也可以</div>
      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {guidance.map((p, i) => (
          <div key={i} onClick={() => appendPrompt(p)} className="xt-card" style={{
            padding: '12px 14px',
            fontSize: 13, color: T.text2,
            display: 'flex', alignItems: 'center', gap: 10,
            cursor: 'pointer',
          }}>
            <span style={{ fontFamily: T.mono, fontSize: 10, color: T.text3 }}>0{i+1}</span>
            <span className="xt-grow">{p}</span>
            <span style={{ color: T.accentInk }}>＋</span>
          </div>
        ))}
      </div>

      {/* Inline risk hint — shown while still writing */}
      {risk && (
        <div style={{ padding: '14px 16px 0' }}>
          <div style={{
            background: T.warmSoft, border: `1px solid rgba(224,168,123,0.28)`,
            borderRadius: 14, padding: '12px 14px',
            display: 'flex', gap: 10, alignItems: 'flex-start',
          }}>
            <span style={{ color: T.warm, marginTop: 1 }}>{I.warning}</span>
            <div>
              <div style={{ fontSize: 12, color: T.warm, fontWeight: 500, marginBottom: 4 }}>
                {risk.title}
              </div>
              <div style={{ fontSize: 12, color: T.text2, lineHeight: 1.65 }}>
                {risk.body}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CTA — sticky, lifted above software keyboard on iOS */}
      <div style={{
        position: 'sticky', bottom: 0,
        padding: '20px 16px 22px',
        paddingBottom: 'calc(22px + max(env(safe-area-inset-bottom), var(--xt-kb, 0px)))',
        background: `linear-gradient(to top, ${T.bg} 55%, transparent)`,
        marginTop: 16,
      }}>
        <button
          onClick={() => valid && ctx?.nav('suggest')}
          disabled={!valid}
          className="xt-btn primary full"
          style={{
            height: 52, opacity: valid ? 1 : 0.4,
            cursor: valid ? 'pointer' : 'not-allowed',
            transition: 'opacity .15s',
          }}
        >
          帮我整理表达
        </button>
        <div style={{ fontSize: 11, color: T.text3, textAlign: 'center', marginTop: 10 }}>
          {valid ? '会给你 3 个版本 · 你来挑' : '写几个字试试 · 不用一次写完'}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 3 — Suggestions (表达建议)
// ─────────────────────────────────────────────────────────────
function SuggestionsScreen({ ctx }) {
  const rec = RECIPIENT_LABELS[ctx?.flow?.recipient] || '恋人';
  const sc  = SCENE_LABELS[ctx?.flow?.scene] || '想念';
  const bank = EXPRESSION_BANK[ctx?.flow?.scene] || EXPRESSION_BANK.miss;
  const picked = ctx?.flow?.style || 'gentle';
  const choose = (style) => ctx?.setFlow(s => ({ ...s, style }));
  const risk = detectRisk(ctx?.flow?.rawText || '');

  return (
    <div className="xt-screen" style={{ paddingBottom: 100 }}>
      <AppBar title="挑一个最像你的版本" subtitle={`给${rec} · ${sc}`} onLeft={() => ctx?.nav('back')} />
      <StepDots active={1} total={3} labels={['整理想法', '挑选表达', '生成语音']} />

      {/* AI understanding — fades in */}
      <div style={{ padding: '20px 16px 4px', animation: 'spaCardIn .4s .05s both' }}>
        <div className="xt-card-elev" style={{ padding: 16 }}>
          <div className="xt-row xt-gap-2" style={{ marginBottom: 8 }}>
            <Dot c={T.accentInk} />
            <span style={{ fontSize: 11, color: T.text3, letterSpacing: 0.12, textTransform: 'uppercase' }}>
              我读到的是
            </span>
          </div>
          <div style={{ fontFamily: T.serif, fontSize: 15, lineHeight: 1.75, color: T.text }}>
            {bank.summary}
          </div>
          <div style={{ fontSize: 11, color: T.text3, marginTop: 12, lineHeight: 1.7, borderTop: `1px solid ${T.hairline}`, paddingTop: 10 }}>
            表达目标 · {bank.intent}
          </div>
        </div>
      </div>

      {/* 3 expression cards — staggered fade-in */}
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {[
          { key: 'restrained', fitsFor: '想说，但不想给对方压力' },
          { key: 'gentle',     fitsFor: '想让对方感觉到温度' },
          { key: 'sincere',    fitsFor: '想认真表达，不绕弯' },
        ].map(({ key, fitsFor }, i) => (
          <div key={key} style={{ animation: `spaCardIn .42s ${0.2 + i * 0.13}s both` }}>
            <ExpressionCard
              style={STYLE_LABELS[key]}
              fitsFor={fitsFor}
              length={`${bank[key].length}字`}
              text={bank[key]}
              active={picked === key}
              onSelect={() => choose(key)}
            />
          </div>
        ))}
      </div>
      <style>{`@keyframes spaCardIn { from { opacity: 0; transform: translateY(10px) } to { opacity: 1; transform: translateY(0) } }`}</style>

      {/* Risk reminder — appears only when raw input contains a flagged phrase */}
      {risk && (
        <div style={{ padding: '4px 16px 0', animation: 'spaCardIn .42s .6s both' }}>
          <div style={{
            background: T.warmSoft, border: `1px solid rgba(224,168,123,0.28)`,
            borderRadius: 14, padding: '12px 14px',
            display: 'flex', gap: 10, alignItems: 'flex-start',
          }}>
            <span style={{ color: T.warm, marginTop: 1 }}>{I.warning}</span>
            <div>
              <div style={{ fontSize: 12, color: T.warm, fontWeight: 500, marginBottom: 4 }}>
                {risk.title}
              </div>
              <div style={{ fontSize: 12, color: T.text2, lineHeight: 1.65 }}>
                {risk.body}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CTA fixed-feeling bottom */}
      <div style={{
        position: 'sticky', bottom: 0,
        padding: '14px 16px 22px',
        background: `linear-gradient(to top, ${T.bg} 60%, transparent)`,
        marginTop: 16,
      }}>
        <button onClick={() => ctx?.nav('voice')} className="xt-btn primary full" style={{ height: 52 }}>
          用这条 · 生成语音
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 4 — TTS Generation
// ─────────────────────────────────────────────────────────────
function VoiceScreen({ state = 'idle', ctx }) {
  const rec = RECIPIENT_LABELS[ctx?.flow?.recipient] || '恋人';
  const sc  = SCENE_LABELS[ctx?.flow?.scene] || '想念';
  const picked = ctx?.flow?.style || 'gentle';
  const bank = EXPRESSION_BANK[ctx?.flow?.scene] || EXPRESSION_BANK.miss;
  const finalText = bank[picked] || bank.gentle;

  // Demo states surface designed error screens.
  if (ctx?.demo === 'generating')  return <StateGenerating ctx={ctx} />;
  if (ctx?.demo === 'failed')      return <StateFailed ctx={ctx} />;
  if (ctx?.demo === 'quota')       return <StateQuota ctx={ctx} />;
  if (ctx?.demo === 'no-provider') return <StateNoProvider ctx={ctx} />;

  return (
    <div className="xt-screen" style={{ paddingBottom: 28 }}>
      <AppBar title="给这段话，配一个声音" subtitle={`${sc} · ${STYLE_LABELS[picked] || '温柔版'}`} onLeft={() => ctx?.nav('back')} />
      <StepDots active={2} total={3} labels={['整理想法', '挑选表达', '生成语音']} />

      {/* Final text preview */}
      <div style={{ padding: '18px 16px 4px' }}>
        <div className="xt-card" style={{ padding: 16, position: 'relative' }}>
          <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 11, color: T.text3, letterSpacing: 0.12 }}>给{rec} · {sc} · {STYLE_LABELS[picked]}</span>
            <button style={{
              background: 'transparent', border: `1px solid ${T.hairline}`,
              color: T.text2, fontSize: 11, padding: '2px 10px',
              borderRadius: 999, cursor: 'pointer',
            }}>编辑文字</button>
          </div>
          <div className="xt-letter" style={{ fontSize: 14, lineHeight: 1.8 }}>
            {finalText}
          </div>
        </div>
      </div>

      {/* Voice picker */}
      <div className="xt-section-h">声音</div>
      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[
          { id: 'female-gentle', name: '温柔女声', desc: '清晰、靠近、稍慢' },
          { id: 'male-gentle',   name: '温柔男声', desc: '低、安静、像夜里的电话' },
          { id: 'female-bright', name: '清亮女声', desc: '年轻，适合朋友、自己' },
          { id: 'male-mature',   name: '成熟男声', desc: '稳，适合父母' },
        ].map((v, i) => {
          const sel = (ctx?.flow?.voice || 'female-gentle') === v.id;
          return (
            <div key={i} onClick={() => ctx?.setFlow(s => ({ ...s, voice: v.id }))} className="xt-row" style={{
              padding: '12px 14px', borderRadius: 14, cursor: 'pointer',
              background: sel ? T.accentSoft : T.surface,
              border: `1px solid ${sel ? T.accentDeep : T.hairline}`,
              gap: 12, transition: 'all .15s',
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: T.surface3, display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 2, padding: '0 6px',
              }}>
                {[0.4, 0.8, 0.5, 1, 0.6].map((h, k) => (
                  <div key={k} style={{
                    width: 2, height: `${h*60}%`,
                    background: sel ? T.accent : T.text3, borderRadius: 1,
                  }} />
                ))}
              </div>
              <div className="xt-grow">
                <div style={{ fontSize: 14, color: sel ? T.accentInk : T.text, fontWeight: 500 }}>{v.name}</div>
                <div style={{ fontSize: 11, color: T.text3, marginTop: 2 }}>{v.desc}</div>
              </div>
              <div style={{
                width: 22, height: 22, borderRadius: 999,
                border: `1.5px solid ${sel ? T.accent : T.hairline2}`,
                background: sel ? T.accent : 'transparent',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {sel && <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 5l2 2 4-4" stroke="white" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>}
              </div>
            </div>
          );
        })}
      </div>

      {/* Tone chips */}
      <div className="xt-section-h">语气</div>
      <div style={{ padding: '0 16px', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {[
          { id: 'restrained', l: '克制' },
          { id: 'gentle',     l: '温柔' },
          { id: 'sincere',    l: '真诚' },
          { id: 'whisper',    l: '轻声' },
          { id: 'bedtime',    l: '睡前' },
        ].map((c, i) => {
          const sel = (ctx?.flow?.tone || 'gentle') === c.id;
          return (
            <span key={i} onClick={() => ctx?.setFlow(s => ({ ...s, tone: c.id }))} className={`xt-pill ${sel ? 'active' : ''}`} style={{ padding: '8px 14px', fontSize: 13, cursor: 'pointer' }}>
              {c.l}
            </span>
          );
        })}
      </div>

      {/* Estimated duration — from chars */}
      <div style={{ padding: '18px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: T.text3 }}>预计时长</span>
        <span style={{ fontFamily: T.mono, fontSize: 13, color: T.text2 }}>
          ≈ {(() => {
            const secs = Math.max(3, Math.round(finalText.length * 0.28 + 1.5));
            const m = Math.floor(secs / 60), s = secs % 60;
            return `${m}:${String(s).padStart(2, '0')}`;
          })()}
        </span>
      </div>

      {/* CTA */}
      <div style={{ padding: '6px 16px 14px' }}>
        <button onClick={() => ctx?.nav('letter')} className="xt-btn primary full" style={{ height: 54, fontSize: 16 }}>
          生成语音
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Helpers — clipboard, download, image render
// ─────────────────────────────────────────────────────────────
async function _copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Legacy fallback
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); document.body.removeChild(ta); return true; }
    catch { document.body.removeChild(ta); return false; }
  }
}

function _triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

// Generate a silent WAV blob of N seconds — placeholder for real TTS output.
function _silentWav(seconds = 5) {
  const sampleRate = 22050;
  const n = Math.max(1, Math.floor(sampleRate * seconds));
  const buf = new ArrayBuffer(44 + n * 2);
  const v = new DataView(buf);
  const ws = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  ws(0, 'RIFF');  v.setUint32(4, 36 + n * 2, true);
  ws(8, 'WAVE');  ws(12, 'fmt '); v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, sampleRate, true); v.setUint32(28, sampleRate * 2, true);
  v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  ws(36, 'data'); v.setUint32(40, n * 2, true);
  return new Blob([buf], { type: 'audio/wav' });
}

// Render a letter to a portrait PNG suitable for sharing — pure canvas.
function _renderLetterImage(letter) {
  const W = 1080, H = 1620;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const g = c.getContext('2d');

  // bg + soft glow
  g.fillStyle = '#0A080E';
  g.fillRect(0, 0, W, H);
  const grad = g.createRadialGradient(W * 0.3, H * 0.0, 0, W * 0.3, H * 0.0, W);
  const accent = getComputedStyle(document.documentElement).getPropertyValue('--xt-accent').trim() || '#9B4DCA';
  grad.addColorStop(0, accent + '38');
  grad.addColorStop(1, 'transparent');
  g.fillStyle = grad; g.fillRect(0, 0, W, H);

  // Letter card
  const pad = 72;
  const cardX = pad, cardY = pad * 2.6, cardW = W - pad * 2, cardH = H - pad * 4.4;
  g.fillStyle = '#1A1521';
  g.strokeStyle = 'rgba(255,255,255,0.10)';
  g.lineWidth = 2;
  const r = 40;
  g.beginPath();
  g.moveTo(cardX + r, cardY);
  g.arcTo(cardX + cardW, cardY, cardX + cardW, cardY + cardH, r);
  g.arcTo(cardX + cardW, cardY + cardH, cardX, cardY + cardH, r);
  g.arcTo(cardX, cardY + cardH, cardX, cardY, r);
  g.arcTo(cardX, cardY, cardX + cardW, cardY, r);
  g.closePath();
  g.fill(); g.stroke();

  // Brand mark above card
  g.fillStyle = '#ECE6F0';
  g.font = '500 28px "Noto Serif SC", serif';
  g.textBaseline = 'top';
  g.fillText('想他了', pad, pad);

  // Pills row
  const recLabel = RECIPIENT_LABELS[letter.recipient] || '';
  const scLabel  = SCENE_LABELS[letter.scene] || '';
  const styleLabel = STYLE_LABELS[letter.style] || '';
  const labels = [`给${recLabel}`, scLabel, styleLabel].filter(Boolean);
  let px = cardX + 56;
  const py = cardY + 56;
  g.font = '500 24px "Noto Sans SC", sans-serif';
  labels.forEach((l, i) => {
    const tw = g.measureText(l).width;
    const pw = tw + 36, ph = 44;
    g.fillStyle = i === 0 ? accent + '2D' : 'rgba(255,255,255,0.05)';
    g.beginPath();
    const pr = ph / 2;
    g.moveTo(px + pr, py); g.arcTo(px + pw, py, px + pw, py + ph, pr);
    g.arcTo(px + pw, py + ph, px, py + ph, pr);
    g.arcTo(px, py + ph, px, py, pr);
    g.arcTo(px, py, px + pw, py, pr);
    g.closePath(); g.fill();
    g.fillStyle = i === 0 ? '#E8C9F4' : 'rgba(244,239,230,0.62)';
    g.fillText(l, px + 18, py + 9);
    px += pw + 12;
  });

  // Date marker
  g.fillStyle = 'rgba(244,239,230,0.38)';
  g.font = '400 22px "JetBrains Mono", monospace';
  const d = new Date(letter.createdAt || Date.now());
  const dateStr = `${d.getFullYear()} · ${String(d.getMonth()+1).padStart(2,'0')} · ${String(d.getDate()).padStart(2,'0')}  ·  ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  g.fillText(dateStr, cardX + 56, py + 90);

  // Body — wrap text, auto-shrink font if it doesn't fit the card.
  const body = letter.finalText || '';
  const textX = cardX + 56;
  const startY = py + 180;
  const maxW = cardW - 112;
  const bottomLimit = cardY + cardH - 140;

  // Pick a font size that fits: start at 38px, shrink to 26px in steps.
  // Wraps CJK char-by-char.
  let fontSize = 38, lineH = 64;
  const wrap = (size) => {
    g.font = `400 ${size}px "Noto Serif SC", serif`;
    const ls = [];
    let line = '';
    for (let i = 0; i < body.length; i++) {
      const ch = body[i];
      if (ch === '\n') { ls.push(line); line = ''; continue; }
      const test = line + ch;
      if (g.measureText(test).width > maxW) { ls.push(line); line = ch; }
      else line = test;
    }
    if (line) ls.push(line);
    return ls;
  };
  let lines = wrap(fontSize);
  while (fontSize > 26 && (startY + lines.length * lineH) > bottomLimit) {
    fontSize -= 2; lineH = Math.round(fontSize * 1.7);
    lines = wrap(fontSize);
  }

  g.fillStyle = '#F4EFE6';
  g.font = `400 ${fontSize}px "Noto Serif SC", serif`;
  let textY = startY;
  for (const line of lines) {
    if (textY > bottomLimit) break;
    g.fillText(line, textX, textY);
    textY += lineH;
  }

  // Signature
  g.fillStyle = 'rgba(244,239,230,0.62)';
  g.font = '400 24px "Noto Serif SC", serif';
  const sig = '—— 想他了 · 写于' + (d.getHours() >= 18 || d.getHours() < 5 ? '今晚' : '今天');
  const sigW = g.measureText(sig).width;
  g.fillText(sig, cardX + cardW - sigW - 56, cardY + cardH - 84);

  // Footer note
  g.fillStyle = 'rgba(244,239,230,0.22)';
  g.font = '400 22px "Noto Sans SC", sans-serif';
  const note = '由本人于 想他了 写下，未替任何人发送';
  const nw = g.measureText(note).width;
  g.fillText(note, (W - nw) / 2, H - pad);

  return c;
}

window._copyToClipboard = _copyToClipboard;
window._triggerDownload = _triggerDownload;
window._silentWav = _silentWav;
window._renderLetterImage = _renderLetterImage;

// ─────────────────────────────────────────────────────────────
// Toast — light-weight; used by letter actions
// ─────────────────────────────────────────────────────────────
function Toast({ text, tone = 'ok', onDone, ms = 1800 }) {
  React.useEffect(() => { const id = setTimeout(onDone, ms); return () => clearTimeout(id); }, []);
  if (!text) return null;
  const colors = {
    ok:   { c: T.ok,     b: T.okSoft },
    warm: { c: T.warm,   b: T.warmSoft },
  }[tone] || { c: T.text, b: T.surface2 };
  return (
    <div style={{
      position: 'absolute', left: 16, right: 16, bottom: 28, zIndex: 90,
      padding: '12px 16px', borderRadius: 14,
      background: 'rgba(26,21,33,0.96)',
      backdropFilter: 'blur(20px)',
      border: `1px solid ${colors.b}`,
      color: colors.c,
      display: 'flex', alignItems: 'center', gap: 10,
      fontSize: 13, lineHeight: 1.5,
      animation: 'spaSlideInR .22s cubic-bezier(.2,.8,.3,1) both',
    }}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M3 8l4 4 6-8" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <span style={{ color: T.text }}>{text}</span>
    </div>
  );
}
window.Toast = Toast;

// ─────────────────────────────────────────────────────────────
// Screen 5 — Result / Letter detail
// ─────────────────────────────────────────────────────────────
function LetterScreen({ ctx }) {
  // Source of truth: either a saved letter (flow.letterId) or the transient draft (flow.*)
  const all = useLetters();
  const saved = ctx?.flow?.letterId ? all.find(l => l.id === ctx.flow.letterId) : null;

  const recipient = saved?.recipient || ctx?.flow?.recipient || 'lover';
  const scene     = saved?.scene     || ctx?.flow?.scene     || 'miss';
  const picked    = saved?.style     || ctx?.flow?.style     || 'gentle';
  const voiceId   = saved?.voice     || ctx?.flow?.voice     || 'female-gentle';
  const toneId    = saved?.tone      || ctx?.flow?.tone      || 'gentle';

  const rec = RECIPIENT_LABELS[recipient] || '恋人';
  const sc  = SCENE_LABELS[scene] || '想念';
  const styleLabel = STYLE_LABELS[picked] || '温柔版';
  const voiceLabel = ({ 'female-gentle': '温柔女声', 'male-gentle': '温柔男声', 'female-bright': '清亮女声', 'male-mature': '成熟男声' })[voiceId] || '温柔女声';
  const toneLabel  = ({ restrained: '克制', gentle: '温柔', sincere: '真诚', whisper: '轻声', bedtime: '睡前' })[toneId] || '温柔';

  const bank = EXPRESSION_BANK[scene] || EXPRESSION_BANK.miss;
  const finalText = saved?.finalText || bank[picked] || bank.gentle;
  const lines = finalText.replace(/([。，！？])/g, '$1\n').split('\n').filter(Boolean);

  // Open-count tracking for saved letters
  React.useEffect(() => { if (saved?.id) Letters.touch(saved.id); }, [saved?.id]);

  const [menu, setMenu] = React.useState(false);
  const [toast, setToast] = React.useState(null);
  const [showSeal, setShowSeal] = React.useState(false);

  // Date / signature based on saved time or now
  const createdAt = saved?.createdAt || Date.now();
  const d = new Date(createdAt);
  const dateStr = `${d.getFullYear()} · ${String(d.getMonth()+1).padStart(2,'0')} · ${String(d.getDate()).padStart(2,'0')}  ·  ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;

  // Persist: turn transient into saved letter
  const save = () => {
    if (saved?.id) {
      Letters.update(saved.id, { favorited: !saved.favorited });
      setToast({ text: saved.favorited ? '已取消收藏' : '已收藏到信笺夹' });
      return;
    }
    const letter = Letters.add({
      recipient, scene, style: picked, voice: voiceId, tone: toneId,
      finalText, favorited: true,
    });
    ctx.setFlow(s => ({ ...s, letterId: letter.id }));
    setShowSeal(true);
    setTimeout(() => {
      setShowSeal(false);
      ctx.nav('history');
    }, 1300);
  };

  const downloadAudio = () => {
    const secs = Math.max(3, Math.round(finalText.length * 0.28 + 1.5));
    _triggerDownload(_silentWav(secs), `xiang-ta-le-placeholder-${createdAt}.wav`);
    setToast({ text: '音频已下载（演示用静音占位）', tone: 'warm' });
  };

  const [copyState, setCopyState] = React.useState('idle'); // idle | done
  const copy = async () => {
    const ok = await _copyToClipboard(finalText);
    if (ok) {
      setCopyState('done');
      setToast({ text: '文字已复制 · 可以粘贴去任何地方' });
      setTimeout(() => setCopyState('idle'), 1400);
    }
  };

  const saveImage = () => {
    setMenu(false);
    const c = _renderLetterImage({ recipient, scene, style: picked, finalText, createdAt });
    c.toBlob(blob => {
      if (!blob) { setToast({ text: '渲染失败，再试一次？', tone: 'warm' }); return; }
      _triggerDownload(blob, `xiang-ta-le-${createdAt}.png`);
      setToast({ text: '已保存为图片' });
    }, 'image/png', 0.95);
  };

  const renameTitle = () => {
    setMenu(false);
    if (!saved?.id) { setToast({ text: '先收藏到信笺夹，再编辑标题', tone: 'warm' }); return; }
    const next = prompt('给这封信起一个标题', saved.title || letterTitle(saved));
    if (next != null) {
      Letters.update(saved.id, { title: next.trim() || undefined });
      setToast({ text: '标题已更新' });
    }
  };

  const removeLetter = () => {
    setMenu(false);
    if (!saved?.id) { setToast({ text: '这封信还没保存', tone: 'warm' }); return; }
    if (!confirm('删除这封信？')) return;
    Letters.remove(saved.id);
    ctx.setFlow(s => ({ ...s, letterId: null }));
    ctx.nav('back');
  };

  const editAgain = () => {
    // Replace top entry so back doesn't return to letter
    ctx.setFlow(s => ({ ...s, style: null, letterId: null }));
    ctx.nav('input', { replace: true });
  };

  const changeTone = () => {
    ctx.setFlow(s => ({ ...s, letterId: null }));
    ctx.nav('voice', { replace: true });
  };

  // Web Speech API demo: speak the letter aloud right in the browser.
  // Falls back silently if not supported (Firefox without polyfill, etc.)
  const speakDemo = () => {
    if (!('speechSynthesis' in window)) {
      setToast({ text: '浏览器不支持试听，先下载音频试试', tone: 'warm' });
      return;
    }
    try { speechSynthesis.cancel(); } catch {}
    const u = new SpeechSynthesisUtterance(finalText);
    u.lang = 'zh-CN';
    u.rate = toneId === 'whisper' || toneId === 'bedtime' ? 0.78 : 0.88;
    u.pitch = voiceId.startsWith('male') ? 0.7 : 1.05;
    speechSynthesis.speak(u);
    setToast({ text: '使用浏览器内置语音试听 · 真实生成稍后接入' });
  };

  // Native share — combines copy / save / download into one OS-level affordance.
  const share = async () => {
    setMenu(false);
    const body = `${finalText}\n\n— 由 想他了 写下`;
    if (navigator.share) {
      try {
        await navigator.share({ title: saved?.title || '一封信笺', text: body });
        return;
      } catch (e) {
        if (e?.name === 'AbortError') return;
      }
    }
    await _copyToClipboard(body);
    setToast({ text: '系统不支持原生分享，已复制全文' });
  };

  return (
    <div className="xt-screen" style={{
      paddingBottom: 36, position: 'relative',
      backgroundImage: `radial-gradient(140% 50% at 50% -10%, var(--xt-accent-soft), transparent 70%)`,
    }}>
      <AppBar
        title={saved?.title || '今晚的信笺'}
        rightAction="more" transparent
        onLeft={() => ctx?.nav('back')}
        onRight={() => setMenu(m => !m)}
      />

      {/* Floating more-menu */}
      {menu && (
        <>
          <div onClick={() => setMenu(false)} style={{
            position: 'fixed', inset: 0, zIndex: 30, background: 'transparent',
          }} />
          <div style={{
            position: 'absolute', top: 92, right: 16, zIndex: 35,
            background: T.surface2, border: `1px solid ${T.hairline2}`,
            borderRadius: 14, padding: 6, minWidth: 168,
            boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
            animation: 'spaFadeOverlay .15s ease',
          }}>
            {[
              { l: '试听 · 浏览器朗读', fn: () => { setMenu(false); speakDemo(); } },
              { l: '系统分享 / 复制全文', fn: share },
              { l: '重命名标题', fn: renameTitle },
              { l: '保存为图片', fn: saveImage },
              { l: '换个语气',   fn: changeTone },
              { l: '重新编辑',   fn: editAgain },
              { l: saved?.favorited ? '取消收藏' : '收藏', fn: () => { setMenu(false); save(); } },
              { l: '删除',       fn: removeLetter, danger: true },
            ].map((it, i) => (
              <button key={i} onClick={it.fn} style={{
                display: 'block', width: '100%', textAlign: 'left',
                background: 'transparent', border: 0, padding: '10px 12px',
                fontFamily: T.sans, fontSize: 13,
                color: it.danger ? T.danger : T.text,
                cursor: 'pointer', borderRadius: 8,
              }}>{it.l}</button>
            ))}
          </div>
        </>
      )}

      {/* meta strip */}
      <div style={{ padding: '8px 20px 0' }}>
        <div className="xt-row xt-gap-2" style={{ flexWrap: 'wrap', marginBottom: 16 }}>
          <span className="xt-pill" style={{ background: T.accentSoft, color: T.accentInk, borderColor: T.accentDeep }}>给{rec}</span>
          <span className="xt-pill">{sc}</span>
          <span className="xt-pill">{styleLabel}</span>
          {saved?.favorited && <span className="xt-pill" style={{ color: T.accentInk }}>{I.star} 收藏</span>}
        </div>
      </div>

      {/* Letter paper */}
      <div style={{ padding: '0 16px 18px' }}>
        <div style={{
          background: `linear-gradient(${T.surface2} 0%, ${T.surface} 100%)`,
          border: `1px solid ${T.hairline2}`,
          borderRadius: 22, padding: '24px 26px 26px',
          position: 'relative', overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', inset: '60px 26px 70px 26px',
            backgroundImage: `repeating-linear-gradient(to bottom, transparent 0, transparent 33px, ${T.hairline} 33px, ${T.hairline} 34px)`,
            pointerEvents: 'none', opacity: 0.6,
          }} />
          <div style={{ position: 'absolute', top: 14, right: 16, opacity: 0.45 }}>
            <LetterSeal size={18} color={T.text3} />
          </div>
          <div style={{
            fontSize: 11, color: T.text3, letterSpacing: 0.16,
            marginBottom: 18, fontFamily: T.mono,
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span style={{ width: 12, height: 1, background: T.text4 }} />
            {dateStr}
          </div>
          <div className="xt-letter" style={{ fontSize: 17, lineHeight: '34px', fontWeight: 400, position: 'relative' }}>
            {lines.map((ln, i) => <React.Fragment key={i}>{ln}<br/></React.Fragment>)}
          </div>
          <div style={{
            marginTop: 26, textAlign: 'right',
            fontFamily: T.serif, fontSize: 13, color: T.text2,
            letterSpacing: 0.16, position: 'relative',
          }}>
            —— 写于{d.getHours() >= 18 || d.getHours() < 5 ? '今晚' : '今天'}
          </div>
        </div>
      </div>

      {/* full audio player */}
      <FullPlayer
        voice={voiceLabel} tone={toneLabel}
        totalSecs={Math.max(3, Math.round(finalText.length * 0.28 + 1.5))}
        letterId={saved?.id || `draft-${createdAt}`}
        onDownload={downloadAudio}
      />

      {/* actions */}
      <div style={{ padding: '18px 16px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <button onClick={copy} className="xt-btn ghost" style={copyState === 'done' ? { borderColor: T.ok, color: T.ok } : null}>
          {copyState === 'done'
            ? <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8l4 4 6-8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            : I.copy}
          <span>{copyState === 'done' ? '已复制' : '复制文字'}</span>
        </button>
        <button onClick={share} className="xt-btn ghost">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 2v8m0-8L5 5m3-3l3 3M4 8H3a1 1 0 00-1 1v4a1 1 0 001 1h10a1 1 0 001-1V9a1 1 0 00-1-1h-1" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>分享</span>
        </button>
        <button onClick={editAgain} className="xt-btn ghost">{I.edit}<span>重新编辑</span></button>
        <button onClick={changeTone} className="xt-btn ghost">{I.refresh}<span>换个语气</span></button>
      </div>

      <div style={{ padding: '14px 16px 0' }}>
        <button onClick={save} className="xt-btn full" style={{
          background: saved?.favorited ? T.accentSoft : T.accent,
          color: saved?.favorited ? T.accentInk : 'white',
          border: `1px solid ${saved?.favorited ? T.accentDeep : 'transparent'}`,
        }}>
          {I.star}<span>{saved?.id ? (saved.favorited ? '★ 已收藏' : '☆ 加入收藏') : '保存到信笺夹'}</span>
        </button>
      </div>

      <div style={{ fontSize: 11, color: T.text3, textAlign: 'center', marginTop: 18, lineHeight: 1.7, padding: '0 32px' }}>
        发送给对方的动作，<br/>
        永远由你自己来按。
      </div>

      {/* Save ceremony — local seal */}
      {showSeal && (
        <div className="spa-seal-overlay" style={{ position: 'absolute' }} onClick={() => setShowSeal(false)}>
          <div className="spa-seal-stamp">
            <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
              <rect x="8" y="8" width="40" height="40" rx="3" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M16 20h24M16 28h24M16 36h16" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              <circle cx="28" cy="28" r="14" stroke="currentColor" strokeWidth="0.8" strokeDasharray="2 3" opacity="0.5"/>
            </svg>
          </div>
          <div className="spa-seal-label">已 · 收 · 好</div>
        </div>
      )}

      {toast && <Toast text={toast.text} tone={toast.tone} onDone={() => setToast(null)} />}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 6 — History (信笺夹)
// ─────────────────────────────────────────────────────────────
function HistoryScreen({ ctx }) {
  const allLetters = useLetters();
  const [filter, setFilter] = React.useState('all');
  const [openMenuId, setOpenMenuId] = React.useState(null);
  const [query, setQuery] = React.useState('');
  const [showSearch, setShowSearch] = React.useState(false);

  // Demo: empty state via Tweaks
  if (ctx?.demo === 'empty') {
    return (
      <div className="xt-screen" style={{ position: 'relative' }}>
        {ctx && (
          <button onClick={() => ctx.nav('back')} style={{
            position: 'absolute', top: 50, left: 16, zIndex: 20,
            width: 36, height: 36, borderRadius: 999,
            background: T.surface, border: `1px solid ${T.hairline}`,
            color: T.text2, cursor: 'pointer', padding: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>{I.back}</button>
        )}
        <div style={{ padding: '54px 20px 6px 60px' }}>
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
          <button onClick={() => ctx?.nav('home')} className="xt-btn primary" style={{ marginTop: 22, padding: '12px 28px' }}>
            写第一封
          </button>
        </div>
      </div>
    );
  }

  // Filtered + searched view
  const filtered = allLetters.filter(l => {
    if (filter !== 'all') {
      if (filter === 'fav' && !l.favorited) return false;
      if (filter !== 'fav' && l.recipient !== filter) return false;
    }
    if (query) {
      const q = query.toLowerCase();
      const hay = `${l.finalText || ''} ${l.title || ''} ${RECIPIENT_LABELS[l.recipient] || ''} ${SCENE_LABELS[l.scene] || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  // True empty (no letters at all)
  if (!allLetters.length) {
    return (
      <div className="xt-screen" style={{ position: 'relative' }}>
        <button onClick={() => ctx?.nav('back')} style={{
          position: 'absolute', top: 50, left: 16, zIndex: 20,
          width: 36, height: 36, borderRadius: 999,
          background: T.surface, border: `1px solid ${T.hairline}`,
          color: T.text2, cursor: 'pointer', padding: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>{I.back}</button>
        <div style={{ padding: '54px 20px 6px 60px' }}>
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
          <button onClick={() => ctx?.nav('home')} className="xt-btn primary" style={{ marginTop: 22, padding: '12px 28px' }}>
            写第一封
          </button>
        </div>
      </div>
    );
  }

  // Recipient counts for filter chips
  const counts = allLetters.reduce((acc, l) => {
    acc[l.recipient] = (acc[l.recipient] || 0) + 1;
    return acc;
  }, {});
  const favCount = allLetters.filter(l => l.favorited).length;

  const onItemClick = (id) => {
    ctx?.setFlow(s => ({ ...s, letterId: id }));
    ctx?.nav('letter');
  };

  const togglePin = (e, id) => {
    e.stopPropagation();
    const l = allLetters.find(x => x.id === id);
    if (l) Letters.update(id, { favorited: !l.favorited });
  };

  const handleDelete = (e, id) => {
    e.stopPropagation();
    setOpenMenuId(null);
    if (confirm('删除这封信？')) Letters.remove(id);
  };

  return (
    <div className="xt-screen">
      <button onClick={() => ctx?.nav('back')} style={{
        position: 'absolute', top: 50, left: 16, zIndex: 20,
        width: 36, height: 36, borderRadius: 999,
        background: T.surface, border: `1px solid ${T.hairline}`,
        color: T.text2, cursor: 'pointer', padding: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>{I.back}</button>

      <div style={{ padding: '54px 20px 6px 60px' }}>
        <div className="xt-row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontFamily: T.serif, fontSize: 26, fontWeight: 500 }}>信笺夹</div>
            <div style={{ fontSize: 12, color: T.text3, marginTop: 6 }}>
              {allLetters.length} 封 · 本地保存，不会上传
            </div>
          </div>
          <button
            onClick={() => { setShowSearch(s => !s); if (showSearch) setQuery(''); }}
            aria-label="搜索"
            style={{
              width: 32, height: 32, borderRadius: 999,
              background: 'transparent', border: `1px solid ${T.hairline}`,
              color: T.text2, cursor: 'pointer', padding: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><title>搜索</title>
              <circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1.4"/>
              <path d="m9 9 3.5 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      {showSearch && (
        <div style={{ padding: '8px 16px 0' }}>
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索信笺正文 / 标题 / 对象 / 场景"
            style={{
              width: '100%', padding: '10px 14px', borderRadius: 12,
              background: T.surface, border: `1px solid ${T.hairline2}`,
              color: T.text, fontFamily: T.sans, fontSize: 13,
              outline: 'none',
            }}
          />
        </div>
      )}

      {/* filter chips */}
      <div className="xt-row xt-gap-2" style={{ padding: '14px 16px 8px', overflowX: 'auto' }}>
        {[
          { id: 'all',    l: '全部', n: allLetters.length },
          { id: 'lover',  l: '恋人', n: counts.lover  || 0 },
          { id: 'family', l: '父母', n: counts.family || 0 },
          { id: 'friend', l: '朋友', n: counts.friend || 0 },
          { id: 'self',   l: '自己', n: counts.self   || 0 },
          { id: 'fav',    l: '收藏', n: favCount },
        ].filter(c => c.id === 'all' || c.n > 0).map(c => (
          <span
            key={c.id}
            onClick={() => setFilter(c.id)}
            className={`xt-pill ${filter === c.id ? 'active' : ''}`}
            style={{ cursor: 'pointer', flexShrink: 0 }}
          >
            {c.l}{c.n > 0 && filter !== c.id ? ` · ${c.n}` : ''}
          </span>
        ))}
      </div>

      {/* list */}
      <div key={filter + ':' + query} style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 10, animation: 'spaCardIn .26s both' }}>
        {filtered.length === 0 ? (
          <div style={{
            padding: '40px 22px', textAlign: 'center',
            color: T.text3, fontSize: 13, lineHeight: 1.8,
          }}>
            这个筛选下还没有信笺。
          </div>
        ) : filtered.map((it) => {
          const rec = RECIPIENT_LABELS[it.recipient] || '';
          const sc  = SCENE_LABELS[it.scene] || '';
          const open = openMenuId === it.id;
          return (
            <div
              key={it.id}
              onClick={() => onItemClick(it.id)}
              className="xt-card"
              style={{ padding: 14, display: 'flex', gap: 12, cursor: 'pointer', position: 'relative' }}
            >
              <div style={{
                width: 40, height: 40, borderRadius: 12, flexShrink: 0,
                background: T.accentSoft,
                color: T.accentInk,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>{I.play}</div>
              <div className="xt-grow" style={{ minWidth: 0 }}>
                <div style={{
                  fontFamily: T.serif, fontSize: 14, color: T.text, fontWeight: 500,
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                }}>{letterTitle(it)}</div>
                <div className="xt-row" style={{ marginTop: 4, gap: 6, fontSize: 11, color: T.text3 }}>
                  <span>{rec}</span>
                  <span style={{ color: T.text4 }}>·</span>
                  <span>{sc}</span>
                  <span style={{ color: T.text4 }}>·</span>
                  <span>{letterTime(it.createdAt)}</span>
                </div>
              </div>
              <div className="xt-col" style={{ alignItems: 'flex-end', gap: 6 }}>
                <span style={{ fontFamily: T.mono, fontSize: 10, color: T.text3 }}>
                  {letterDuration(it.finalText)}
                </span>
                <span
                  onClick={(e) => { e.stopPropagation(); setOpenMenuId(open ? null : it.id); }}
                  style={{ color: it.favorited ? T.accent : T.text3, cursor: 'pointer', padding: 4 }}
                >
                  {it.favorited ? I.star : I.more}
                </span>
              </div>

              {open && (
                <>
                  <div onClick={(e) => { e.stopPropagation(); setOpenMenuId(null); }} style={{
                    position: 'fixed', inset: 0, zIndex: 30,
                  }} />
                  <div style={{
                    position: 'absolute', top: 50, right: 14, zIndex: 35,
                    background: T.surface2, border: `1px solid ${T.hairline2}`,
                    borderRadius: 12, padding: 4, minWidth: 140,
                    boxShadow: '0 16px 30px rgba(0,0,0,0.45)',
                  }}>
                    {[
                      { l: it.favorited ? '取消收藏' : '收藏', fn: (e) => { togglePin(e, it.id); setOpenMenuId(null); } },
                      { l: '删除', fn: (e) => handleDelete(e, it.id), danger: true },
                    ].map((m, k) => (
                      <button key={k} onClick={m.fn} style={{
                        display: 'block', width: '100%', textAlign: 'left',
                        background: 'transparent', border: 0,
                        padding: '8px 10px', fontFamily: T.sans, fontSize: 13,
                        color: m.danger ? T.danger : T.text,
                        cursor: 'pointer', borderRadius: 6,
                      }}>{m.l}</button>
                    ))}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ height: 90 }} />
      {/* docked mini player — when at least one letter exists */}
      {allLetters[0] && (
        <div style={{
          position: 'sticky', bottom: 0, left: 0, right: 0,
          paddingBottom: 'env(safe-area-inset-bottom)',
          marginTop: -90,
        }}>
          <div onClick={() => onItemClick(allLetters[0].id)} style={{ cursor: 'pointer' }}>
            <MiniPlayer
              title={letterTitle(allLetters[0])}
              recipient={RECIPIENT_LABELS[allLetters[0].recipient] || ''}
              scene={SCENE_LABELS[allLetters[0].scene] || ''}
              letterId={allLetters[0].id}
              totalSecs={Math.max(3, Math.round((allLetters[0].finalText || '').length * 0.28 + 1.5))}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Screen 7 — Settings / Status
// ─────────────────────────────────────────────────────────────
function SettingsScreen({ ctx }) {
  const letters = useLetters();
  const provider = useProvider();
  const [toast, setToast] = React.useState(null);

  const exportData = () => {
    const ts = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
    _triggerDownload(new Blob([Letters.exportJson()], { type: 'application/json' }), `xiang-ta-le-letters-${ts}.json`);
    setToast({ text: '已开始下载 JSON 备份' });
  };
  const clearAll = () => {
    if (!confirm(`真的要清除全部 ${letters.length} 封信笺？这个操作不可撤销。`)) return;
    Letters.clearAll();
    setToast({ text: '本地数据已清除' });
  };

  const providerTone = provider.kind === 'ok' ? 'ok' : provider.kind === 'quota' ? 'warm' : 'danger';
  const providerLabel = provider.kind === 'ok' ? '正常' : provider.kind === 'quota' ? '额度紧张' : '未连接';

  return (
    <div className="xt-screen" style={{ paddingBottom: 40, position: 'relative' }}>
      {ctx && (
        <button onClick={() => ctx.nav('back')} style={{
          position: 'absolute', top: 50, left: 16, zIndex: 20,
          width: 36, height: 36, borderRadius: 999,
          background: T.surface, border: `1px solid ${T.hairline}`,
          color: T.text2, cursor: 'pointer', padding: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>{I.back}</button>
      )}
      <div style={{ padding: '54px 20px 6px 60px' }}>
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
              <div style={{ fontSize: 11, color: T.text3, marginTop: 4 }}>{provider.detail}</div>
            </div>
            <StatusPill tone={providerTone} label={providerLabel} />
          </div>
          <div style={{ height: 1, background: T.hairline, margin: '14px 0' }} />
          <div className="xt-row" style={{ justifyContent: 'space-between' }}>
            <div style={{ fontSize: 12, color: T.text2 }}>本月剩余额度</div>
            <div style={{ fontSize: 12, color: T.text2, fontFamily: T.mono }}>
              {provider.kind === 'quota' ? '不足' : provider.kind === 'no_provider' ? '—' : `${Math.round((provider.quotaPct || 0) * 100)}%`}
            </div>
          </div>
          <div style={{
            height: 4, borderRadius: 999, marginTop: 8,
            background: T.hairline2, overflow: 'hidden', position: 'relative',
          }}>
            <div style={{
              position: 'absolute', inset: 0,
              width: `${(provider.quotaPct || 0) * 100}%`,
              background: providerTone === 'warm' ? T.warm : providerTone === 'danger' ? T.danger : 'var(--xt-accent)',
              borderRadius: 999,
            }}/>
          </div>
        </div>
      </div>

      <div className="xt-section-h">云同步 · 即将开放</div>
      <div style={{ padding: '0 16px' }}>
        <div style={{
          padding: 16, borderRadius: 16,
          border: `1px dashed ${T.hairline2}`,
          background: 'transparent',
          opacity: 0.7,
        }}>
          <div className="xt-row" style={{ justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 14, color: T.text, fontWeight: 500 }}>多设备同步</span>
            <span className="xt-pill" style={{ fontSize: 10 }}>之后开放</span>
          </div>
          <div style={{ fontSize: 12, color: T.text3, lineHeight: 1.7 }}>
            信笺会在你自己的设备之间安静地同步，不会被任何人读到。
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
          <div onClick={exportData} style={{ padding: '14px 16px', borderBottom: `1px solid ${T.hairline}`, display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}>
            <span style={{ fontSize: 14 }}>导出全部信笺 <span style={{ color: T.text3, fontSize: 12 }}>· {letters.length} 封</span></span>
            <span style={{ color: T.text3 }}>›</span>
          </div>
          <div onClick={clearAll} style={{ padding: '14px 16px', borderBottom: `1px solid ${T.hairline}`, display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}>
            <span style={{ fontSize: 14, color: T.danger }}>清除本地数据</span>
          </div>
          <div style={{ padding: '14px 16px', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 14, color: T.text3 }}>开发者面板</span>
            <span style={{ fontSize: 11, color: T.text4, fontFamily: T.mono }}>Debug</span>
          </div>
        </div>
      </div>

      <div style={{ fontSize: 10, color: T.text4, textAlign: 'center', marginTop: 22, fontFamily: T.mono, letterSpacing: 0.2 }}>
        想他了 · v0.1.0 · build 0517
      </div>

      {toast && <Toast text={toast.text} onDone={() => setToast(null)} />}
    </div>
  );
}

Object.assign(window, {
  HomeScreen, InputScreen, SuggestionsScreen, VoiceScreen,
  LetterScreen, HistoryScreen, SettingsScreen,
});
