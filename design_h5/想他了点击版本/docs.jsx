// Documentation artboards — product overview, IA, domain model, API facade, handoff
// These render as wider text-heavy cards on the canvas (not inside iOS frames).

function DocCard({ width = 560, title, kicker, children, height }) {
  return (
    <div style={{
      width, minHeight: height || 'auto',
      background: T.bg, color: T.text,
      border: `1px solid ${T.hairline2}`, borderRadius: 24,
      padding: '28px 30px 30px', fontFamily: T.sans,
      display: 'flex', flexDirection: 'column', gap: 16,
    }}>
      {kicker && <div style={{ fontSize: 11, color: T.text3, letterSpacing: 0.2, textTransform: 'uppercase' }}>{kicker}</div>}
      <div style={{ fontFamily: T.serif, fontSize: 24, fontWeight: 500, letterSpacing: 0.02, lineHeight: 1.35 }}>{title}</div>
      <div style={{ height: 1, background: T.hairline }} />
      <div style={{ fontSize: 14, lineHeight: 1.85, color: T.text2 }}>{children}</div>
    </div>
  );
}

function K({ children }) {
  return <span style={{
    fontFamily: T.mono, fontSize: 12, padding: '1px 6px', borderRadius: 4,
    background: T.surface2, color: T.accentInk, border: `1px solid ${T.hairline}`,
  }}>{children}</span>;
}

function DL({ items }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {items.map(([k, v], i) => (
        <div key={i}>
          <div style={{ fontSize: 12, color: T.text3, letterSpacing: 0.08, marginBottom: 4 }}>{k}</div>
          <div style={{ fontSize: 14, color: T.text, lineHeight: 1.75 }}>{v}</div>
        </div>
      ))}
    </div>
  );
}

function Ul({ items, accent }) {
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map((t, i) => (
        <li key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <span style={{
            color: accent || T.text3, fontFamily: T.mono, fontSize: 11,
            paddingTop: 4, flexShrink: 0, width: 18,
          }}>{String(i + 1).padStart(2, '0')}</span>
          <span style={{ flex: 1, color: T.text2, fontSize: 13.5, lineHeight: 1.8 }}>{t}</span>
        </li>
      ))}
    </ul>
  );
}

// ─────────────────────────────────────────────────────────────
// Product overview
// ─────────────────────────────────────────────────────────────
function DocProduct() {
  return (
    <DocCard kicker="第一部分 · 产品整理" title="想Ta了 — 把想说的话，变成更合适的文字和语音">
      <DL items={[
        ['产品定位', '以情绪为入口、面向不同关系对象的情绪表达与语音生成工具。不是聊天软件、不是 AI 扮演恋人 / 男友 / 女友、不是自动代聊。'],
        ['目标用户', '需要在深夜、独处、关系紧张、想念、内疚、感谢等时刻好好把话说出来的成年用户。情绪表达能力暂时不稳定的人。'],
        ['核心使用场景', '想念、道歉、感谢、安慰、晚安，五个高频情绪入口。每次使用约 60–120 秒完成一次完整闭环。'],
        ['核心价值', '把粗糙的真心，整理成对方更容易接住的文字 + 有情绪的语音。降低"开口"的门槛。'],
        ['MVP 范围', <>4 个对象身份、5 个情绪场景、3 种表达风格、文案 + TTS 全链路、本地历史、Provider 状态提示。<br/>覆盖 17 个核心状态。</>],
        ['非 MVP 范围', '账号系统 / 云同步 / 社交分享 / 分组聊天 / 自动发送 / 声音克隆 / 对方聊天记录分析 / 心理诊断。'],
      ]} />
      <div style={{ height: 1, background: T.hairline, margin: '14px 0 4px' }} />
      <DL items={[
        ['和普通 TTS 工具的差异', '不让用户面对 voice_id / model_id / 采样率。入口是情绪而非参数。同一段文字会推荐不同语气和声音组合。'],
        ['和普通 AI 聊天工具的差异', '没有持续会话；没有 AI 角色；生成的是给"具体的人"看 / 听的一封信笺，需要用户确认后再用。'],
        ['产品边界（坚决不做）', <>不扮演恋人 / 朋友；不代聊；不分析对方记录；不克隆对方声音；不诱导冷暴力、试探、操控；不替用户发送。</>],
      ]} />
    </DocCard>
  );
}

// ─────────────────────────────────────────────────────────────
// IA — page graph
// ─────────────────────────────────────────────────────────────
function DocIA() {
  // very simple SVG flow
  const box = (x, y, w, h, label, sub, fill) => (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="14"
            fill={fill || T.surface} stroke={T.hairline2} strokeWidth="1"/>
      <text x={x + w/2} y={y + 26} textAnchor="middle"
            fontFamily={T.serif} fontSize="14" fill={T.text} fontWeight="500">{label}</text>
      {sub && <text x={x + w/2} y={y + 46} textAnchor="middle"
            fontFamily={T.sans} fontSize="10" fill={T.text3}>{sub}</text>}
    </g>
  );
  const arrow = (x1, y1, x2, y2) => (
    <line x1={x1} y1={y1} x2={x2} y2={y2}
          stroke={T.accentDeep} strokeWidth="1.4"
          markerEnd="url(#arrh)" />
  );
  return (
    <DocCard width={760} kicker="第二部分 · 信息架构" title="页面结构 · 主路径 · 错误恢复路径">
      <svg viewBox="0 0 720 380" style={{ width: '100%', height: 380 }}>
        <defs>
          <marker id="arrh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0 0 L10 5 L0 10 z" fill={T.accentDeep} />
          </marker>
        </defs>
        {box(20,  20,  140, 64, '首页', '情绪入口', T.accentSoft)}
        {box(200, 20,  140, 64, '输入页', '真实想法')}
        {box(380, 20,  140, 64, '建议页', '3 个版本')}
        {box(560, 20,  140, 64, '语音页', 'TTS 配置')}
        {box(380, 140, 140, 64, '结果页', '信笺详情', T.accentSoft)}
        {box(20,  140, 140, 64, '信笺夹', '历史')}
        {box(200, 140, 140, 64, '设置页', '本机状态')}

        {arrow(160, 52, 200, 52)}
        {arrow(340, 52, 380, 52)}
        {arrow(520, 52, 560, 52)}
        {arrow(630, 84, 480, 140)}
        {arrow(450, 204, 230, 204)}
        {arrow(160, 172, 200, 172)}
        {arrow(90, 84, 90, 140)}

        {/* error loop */}
        <path d="M 630 110 Q 720 110 720 200 Q 720 280 630 280 L 520 280 Q 460 280 460 220"
              fill="none" stroke={T.warm} strokeWidth="1.2" strokeDasharray="4 4" markerEnd="url(#arrh-w)" />
        <defs>
          <marker id="arrh-w" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0 0 L10 5 L0 10 z" fill={T.warm} />
          </marker>
        </defs>
        {box(540, 260, 180, 64, '错误恢复', '保留文字 · 可重试', '#1A1521')}
        <text x="240" y="320" fontFamily={T.mono} fontSize="11" fill={T.text3}>
          失败 / 额度 / 配置缺失 → 保留文字 → 重试 / 改文字 / 改服务
        </text>
      </svg>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
        <div>
          <div style={{ fontSize: 12, color: T.text3, marginBottom: 6, letterSpacing: 0.1 }}>主要路径</div>
          <Ul items={[
            <>首页 → 输入 → 建议 → 语音 → 结果 → 信笺夹</>,
            <>建议页 编辑 / 切换风格 → 再次回到建议页</>,
            <>语音页 切换声音 / 语气 → 重新生成</>,
          ]} />
        </div>
        <div>
          <div style={{ fontSize: 12, color: T.text3, marginBottom: 6, letterSpacing: 0.1 }}>次要 / 恢复路径</div>
          <Ul items={[
            <>语音生成失败 → 保留文字 → 重试 / 改文字 / 改设置</>,
            <>额度不足 → 仅保存文字 → 明天再来生成语音</>,
            <>Provider 未配置 → 设置页 → 回到语音页继续</>,
            <>历史加载失败 → 显示离线信笺 + 重试入口</>,
          ]} />
        </div>
      </div>
    </DocCard>
  );
}

// ─────────────────────────────────────────────────────────────
// Domain model
// ─────────────────────────────────────────────────────────────
function DocDomain() {
  const models = [
    { n: 'RecipientType', d: '对象身份。id, label, hintCopy, defaultVoiceHint, defaultToneHint, extensible'  },
    { n: 'EmotionScene',  d: '情绪场景。id, label, mood, defaultStyle, riskHints[]' },
    { n: 'ExpressionDraft', d: '一次表达草稿。rawInput, recipientId, sceneId, prompts[], updatedAt' },
    { n: 'EmotionLetter', d: '一封情绪信笺（核心聚合）。id, draftId, recipientId, sceneId, styleId, finalText, audio?, createdAt, favorited' },
    { n: 'VoiceConfig',   d: '面向用户的语音配置。voicePresetId, tonePresetId, speedHint。绝不暴露底层 voice_id / model_id。' },
    { n: 'AudioAsset',    d: '本地音频资产。letterId, url(blob), duration, format, sizeBytes, createdAt' },
    { n: 'GenerationTask', d: '一次后台任务。kind: "expression"|"tts", status: idle|running|done|failed|quota|noProvider, progress?, error?' },
    { n: 'ProviderStatus', d: '服务可用性快照。connected, missingFields[], quotaState, lastError, lastCheckedAt' },
    { n: 'PlaybackState', d: '全局播放状态。letterId?, isPlaying, positionMs, durationMs, source: result|history|input' },
  ];
  return (
    <DocCard width={620} kicker="第五部分 · 领域模型" title="9 个核心实体，写给前端 / 写给 Claude Code">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {models.map((m, i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '180px 1fr', gap: 16,
            paddingBottom: 10, borderBottom: i === models.length - 1 ? 'none' : `1px solid ${T.hairline}`,
          }}>
            <K>{m.n}</K>
            <div style={{ fontSize: 13, color: T.text2, lineHeight: 1.7 }}>{m.d}</div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: 12, color: T.text3, marginTop: 6, lineHeight: 1.8 }}>
        约束：所有底层 MiniMax 参数（voice_id, model_id, sample_rate, websocket endpoint…）
        必须封装在 Mobile API Facade 内部，前端永远只见 <K>VoiceConfig.voicePresetId</K> 之类的语义键。
      </div>
    </DocCard>
  );
}

// ─────────────────────────────────────────────────────────────
// API Facade
// ─────────────────────────────────────────────────────────────
function DocAPI() {
  const rows = [
    ['GET',  '/m/bootstrap',                'recipients[], scenes[], styles[], voices[], tones[], providerStatus'],
    ['GET',  '/m/recipients',               '对象身份配置，可扩展'],
    ['GET',  '/m/scenes',                   '情绪场景配置 + risk hints'],
    ['POST', '/m/drafts',                   'create ExpressionDraft (rawInput, recipientId, sceneId)'],
    ['POST', '/m/drafts/:id/suggest',       '触发文案生成任务 → 返回 taskId'],
    ['GET',  '/m/tasks/:id',                '查询任务状态（文案 / TTS 通用）'],
    ['POST', '/m/letters',                  '保存最终信笺（finalText, styleId, voiceConfig?）'],
    ['POST', '/m/letters/:id/tts',          '触发 TTS 任务 → 返回 taskId'],
    ['GET',  '/m/letters/:id',              '取信笺详情 + audioUrl(blob/local)'],
    ['GET',  '/m/letters?filter=…',         '查询信笺夹（按 recipient / scene / favorited）'],
    ['GET',  '/m/provider/status',          'connected, missingFields, quotaState'],
  ];
  return (
    <DocCard width={780} kicker="第六部分 · Mobile API Facade" title="前端只看到语义化端点，不需要懂 MiniMax">
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {rows.map(([m, p, d], i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '60px 260px 1fr', gap: 14,
            padding: '10px 0', borderBottom: i === rows.length - 1 ? 'none' : `1px solid ${T.hairline}`,
            alignItems: 'baseline',
          }}>
            <span style={{
              fontFamily: T.mono, fontSize: 11,
              color: m === 'GET' ? T.ok : T.accentInk,
              border: `1px solid ${m === 'GET' ? T.okSoft : T.accentSoft}`,
              padding: '2px 8px', borderRadius: 4, textAlign: 'center',
              background: m === 'GET' ? T.okSoft : T.accentSoft,
            }}>{m}</span>
            <K>{p}</K>
            <span style={{ fontSize: 13, color: T.text2, lineHeight: 1.7 }}>{d}</span>
          </div>
        ))}
      </div>
      <div style={{
        background: T.surface2, border: `1px solid ${T.hairline}`,
        borderRadius: 12, padding: 14, marginTop: 8,
      }}>
        <div style={{ fontSize: 12, color: T.text3, marginBottom: 6, letterSpacing: 0.1, textTransform: 'uppercase' }}>设计原则</div>
        <Ul items={[
          <>所有任务（文案 / TTS）都用统一 <K>GET /m/tasks/:id</K> 轮询或 SSE 订阅。前端不区分同步 / 异步 / WebSocket，由 Facade 内部按场景路由。</>,
          <>错误响应统一形态：<K>{`{ kind: 'no_provider' | 'no_key' | 'quota' | 'network' | 'tts_failed' | 'llm_failed' | 'storage_failed', userMessage }`}</K>。</>,
          <>音频以本地 blob URL 返回；下载是浏览器侧动作，不走后台。</>,
        ]} />
      </div>
    </DocCard>
  );
}

// ─────────────────────────────────────────────────────────────
// Claude Code handoff
// ─────────────────────────────────────────────────────────────
function DocHandoff() {
  return (
    <DocCard width={820} kicker="第七部分 · Claude Code Handoff" title="可直接交给 Claude Code 的实现包">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <div style={{ fontSize: 12, color: T.text3, marginBottom: 8, letterSpacing: 0.1, textTransform: 'uppercase' }}>推荐目录结构</div>
          <pre style={{
            fontFamily: T.mono, fontSize: 11.5, color: T.text2,
            background: T.surface, border: `1px solid ${T.hairline}`, borderRadius: 10,
            padding: 14, margin: 0, lineHeight: 1.7, whiteSpace: 'pre-wrap',
          }}>{`apps/mobile/
├── routes/
│   ├── home.tsx
│   ├── input.tsx
│   ├── suggestions.tsx
│   ├── voice.tsx
│   ├── letter.[id].tsx
│   ├── history.tsx
│   └── settings.tsx
├── ui/
│   ├── RecipientCard.tsx
│   ├── SceneChip.tsx
│   ├── ExpressionCard.tsx
│   ├── MiniPlayer.tsx
│   ├── FullPlayer.tsx
│   ├── StateSheet.tsx
│   └── tokens.css
├── state/
│   ├── flowStore.ts        # current draft / selection
│   ├── lettersStore.ts     # local persistence
│   ├── playbackStore.ts
│   └── providerStore.ts
├── api/
│   ├── mobileFacade.ts     # only entrypoint — NO MiniMax imports here
│   └── types.ts
└── app.tsx`}</pre>
        </div>

        <div>
          <div style={{ fontSize: 12, color: T.text3, marginBottom: 8, letterSpacing: 0.1, textTransform: 'uppercase' }}>路由 / 状态 / API</div>
          <Ul items={[
            <>路由：<K>/m/home /m/input /m/suggest /m/voice /m/letter/:id /m/history /m/settings</K></>,
            <>状态管理：Zustand 三个 store（flow / letters / playback）。Provider 状态独立轮询。</>,
            <>API 封装：单一 <K>mobileFacade.ts</K>，内部委托现有 voice_lab 能力。前端禁止 import voice_lab 子模块。</>,
            <>音频播放：单例 <K>HTMLAudioElement</K> + Zustand playbackStore，跨页持续。</>,
            <>本地持久化：IndexedDB 存 EmotionLetter + AudioAsset blob；不上传服务器。</>,
          ]} />

          <div style={{ fontSize: 12, color: T.text3, marginTop: 18, marginBottom: 8, letterSpacing: 0.1, textTransform: 'uppercase' }}>允许 / 不允许修改</div>
          <Ul accent={T.ok} items={[
            <><K>apps/mobile/**</K> — 可自由新增、修改</>,
            <><K>packages/voice-lab-facade/**</K> — 只允许添加适配方法</>,
            <><K>tokens.css</K> — 设计 token，按需扩展</>,
          ]} />
          <div style={{ height: 6 }} />
          <Ul accent={T.danger} items={[
            <><K>packages/voice-lab/**</K> 现有能力 — 不允许修改</>,
            <>所有 MiniMax 直连模块 — 不允许在 apps/mobile 中 import</>,
            <>历史的脚本面板 / 后台 — 不在本项目改动范围</>,
          ]} />
        </div>
      </div>

      <div style={{ height: 1, background: T.hairline, margin: '4px 0 0' }} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <div style={{ fontSize: 12, color: T.text3, marginBottom: 8, letterSpacing: 0.1, textTransform: 'uppercase' }}>分阶段实现计划</div>
          <Ul items={[
            <><K>FE0</K> 只读审查：列出当前 voice_lab 能力是否够，缺什么写到 ADR</>,
            <><K>FE1</K> 路由 + 设计 tokens + 空骨架页</>,
            <><K>FE2</K> Home / Input / Recipient / Scene 选择</>,
            <><K>FE3</K> Suggestions + ExpressionCard + 风险提醒</>,
            <><K>FE4</K> Voice 配置 + TTS 任务 + 全局播放器</>,
            <><K>FE5</K> History + Letter 详情 + 收藏 / 筛选</>,
            <><K>FE6</K> 17 个状态全覆盖 + Provider 状态 + 验收</>,
          ]} />
        </div>
        <div>
          <div style={{ fontSize: 12, color: T.text3, marginBottom: 8, letterSpacing: 0.1, textTransform: 'uppercase' }}>第一阶段验收标准</div>
          <Ul items={[
            <>能从首页一路走到结果页，不依赖刷新；移动端 375 / 414 / 393 三档 viewport 都不破版</>,
            <>3 种表达版本可见、可切换、可编辑、可复制</>,
            <>语音生成中 / 成功 / 失败 / 额度不足 / Provider 缺失，五状态均有专属 UI 与恢复路径</>,
            <>不出现底层参数命名（voice_id, model_id, sample_rate）</>,
            <>不出现"AI 正在思考"或聊天气泡形态</>,
            <>历史信笺可筛选 / 收藏 / 快速播放；空状态友好</>,
            <>错误文案以"先安抚 → 给一条出路"为格式，覆盖 7 种错误形态</>,
            <>所有发送 / 分享按钮只复制到剪贴板，不替用户发送</>,
          ]} accent={T.accent} />
        </div>
      </div>

      <div style={{
        marginTop: 6, padding: 16,
        background: T.accentSoft, border: `1px solid ${T.accentDeep}`,
        borderRadius: 14, color: T.accentInk, fontSize: 13, lineHeight: 1.8,
      }}>
        交付给 Claude Code 时，将本设计文件作为"产品说明书 + 视觉规范"附上。
        Claude Code 实现时禁止：扮演恋人 / 自动发送 / 克隆对方声音 / 分析对方记录 / 引入操控话术。
        每一阶段以"完成 + 录屏 30 秒走一遍主路径"作为通过标准。
      </div>
    </DocCard>
  );
}

// ─────────────────────────────────────────────────────────────
// State coverage matrix (17 states summary)
// ─────────────────────────────────────────────────────────────
function DocStateMatrix() {
  const states = [
    ['01', '首次进入',           '欢迎引导 + 默认选中"恋人 · 想念"', 'accent'],
    ['02', '未选对象身份',       'CTA 禁用 + 微抖提示',                'mute'],
    ['03', '未选情绪场景',       'CTA 禁用 + 微抖提示',                'mute'],
    ['04', '输入为空',           '按钮禁用 + 占位例句循环淡入',         'mute'],
    ['05', 'AI 文案生成中',      '陪伴式动画 + "慢慢想…" 文案',         'accent'],
    ['06', '文案生成成功',       '三张版本卡片浮入',                    'ok'],
    ['07', '文案生成失败',       '保留原始输入 + 一键重试',              'warm'],
    ['08', '用户编辑文案',       '行内编辑 + 字数 + 撤销',              'accent'],
    ['09', 'TTS 生成中',         '波形预占位 + 大约时长',                'accent'],
    ['10', 'TTS 生成成功',       '波形点亮 + 自动试听一次',              'ok'],
    ['11', 'TTS 生成失败',       'StateSheet · 再试一次',                'warm'],
    ['12', '额度不足',           'StateSheet · 只保存文字',              'warm'],
    ['13', 'Provider 配置缺失',  'StateSheet · 去填配置',                'danger'],
    ['14', '音频试听中',         '全局播放器 active + 波形跑动',          'accent'],
    ['15', '保存成功',           '半屏 Toast · 已收好',                  'ok'],
    ['16', '历史为空',           '虚线信笺占位 + 写第一封',              'mute'],
    ['17', '历史加载失败',       '离线缓存条目 + 顶部重试条',             'warm'],
  ];
  const toneC = { accent: T.accent, ok: T.ok, warm: T.warm, danger: T.danger, mute: T.text3 };
  return (
    <DocCard width={620} kicker="第三部分 · 状态覆盖" title="17 个状态 · 每一个都有专属 UI">
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {states.map(([n, name, desc, tone], i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '40px 130px 1fr 20px', gap: 12,
            padding: '10px 0', borderBottom: i === states.length - 1 ? 'none' : `1px solid ${T.hairline}`,
            alignItems: 'baseline',
          }}>
            <span style={{ fontFamily: T.mono, fontSize: 11, color: T.text3 }}>{n}</span>
            <span style={{ fontSize: 14, color: T.text, fontFamily: T.serif }}>{name}</span>
            <span style={{ fontSize: 12.5, color: T.text2, lineHeight: 1.7 }}>{desc}</span>
            <Dot c={toneC[tone]} size={7} />
          </div>
        ))}
      </div>
    </DocCard>
  );
}

Object.assign(window, {
  DocProduct, DocIA, DocDomain, DocAPI, DocHandoff, DocStateMatrix,
});
