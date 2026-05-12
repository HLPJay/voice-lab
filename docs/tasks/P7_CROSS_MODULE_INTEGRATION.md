# P7：前端跨模块数据联动

## 问题总结

当前 6 个 Tab 之间数据孤立，用户操作完一个模块后需要手动刷新或跳转才能看到关联变化。具体问题：

### 问题 1：Provider 选择器散落且包含无用 Mock
- T2A Tab、音色管理、克隆、设计、绑定管理、删除音色 — 共 **6 处** Provider 下拉都硬编码了 `mock` 和 `minimax` 两个选项
- Mock 对真实用户无意义，增加误选风险
- Provider 列表应统一管理，方便未来扩展新 Provider

### 问题 2：克隆/设计完成后无后续引导
- 克隆成功后得到 `voice_id`，但用户不知道下一步该去绑定管理创建 binding
- 设计成功后同理，得到 `voice_id` 但和人设、绑定没有串联
- 应在成功后提供"一键绑定到人设"的快捷操作

### 问题 3：音色列表"绑定到人设"用 prompt 弹窗输入 profile_id
- `quickBindVoice()` 用 `prompt('输入要绑定的 profile_id')` — 用户需要手动输入 profile_id 字符串
- 应改为下拉选择已有人设

### 问题 4：绑定管理 Tab 创建绑定时 Voice ID 需手动输入
- 用户要从音色管理 Tab 记住 voice_id，再到绑定 Tab 手动粘贴
- Model 也是手动输入文本框（虽有默认值 `speech-2.8-hd`）
- 应支持从已查询的音色列表中选择

### 问题 5：批量生成剧本模式每添加一行都重新 fetch profiles
- `addScriptLine()` 每次都 `fetch('/api/voice/profiles')` — 添加 10 行台词就请求 10 次
- 应缓存 profile 列表，复用

### 问题 6：Tab 切换不刷新数据
- 在克隆 Tab 创建了新音色，切到音色管理 Tab 看不到（需手动点查询）
- 在绑定 Tab 创建了新绑定，切到 T2A Tab 人设下拉不更新
- 应在切换 Tab 时自动刷新关键数据

### 问题 7：删除音色后无联动
- 删除音色成功后，如果该 voice_id 已被绑定，binding 依然存在（指向已删除的 voice）
- 应提示用户或自动标记相关 binding 为不可用

### 问题 8：绑定创建表单无自动关联音色
- "创建绑定"表单中 `Provider Voice ID` 是纯文本输入框，用户不知道有哪些可选音色
- 应改为下拉选择，自动加载当前 provider 下的可用音色列表
- Model 也应从下拉选择或自动填充，不让用户手动输入

### 问题 9：各模块输入框缺少智能默认值
- 克隆 Tab 的 `model` 输入框是空的，应默认填 `speech-2.8-hd`
- 克隆 Tab 的 `preview_text` 应有默认示例文本
- 设计 Tab 的 `preview_text` 同理
- 批量生成的 `silence_between_ms` 等参数应有合理默认

### 问题 10：前端无创建人设入口
- 后端 `POST /api/voice/profiles` 已就绪，但前端没有创建人设的表单
- 绑定管理 Tab 只能查看/创建绑定，不能创建新的人设
- 导致系统中只有一个 seed 的"深夜程序员"，用户无法新增角色
- 应在绑定管理 Tab 顶部添加"创建人设"表单（id / name / description 为必要字段，其余可选）

### 问题 12：克隆/设计成功后无自定义试听入口
- 克隆成功后只能播放 API 返回的 demo 音频（如果传了 preview_text）
- 设计成功后同理，只有 `trial_audio_hex` 或 `trial_audio_url`
- 用户无法输入自定义文本用新创建的音色再试听一段
- 应在成功结果区提供"输入文本 → 试听"的快捷入口（调用同步 T2A，直接用 voice_id）

### 问题 13：音色列表不显示绑定状态
- 音色管理 Tab 查到的音色列表只显示 voice_id / 名称 / 类型 / 语言
- 用户看不出哪些音色已绑定到人设、哪些还是"孤立"的
- 克隆/设计出来的音色如果没绑定，等于无法在 T2A / 批量生成中使用
- 应在音色列表每行标注绑定状态：已绑定（显示绑定的人设名）/ 未绑定（高亮提示）

## 涉及文件

| 文件 | 操作 |
|------|------|
| `app/static/index.html` | 修改（前端逻辑重构） |

**不改后端**——所有 API 已就绪，只是前端没有串联。

## 实施方案（分 3 轮）

### Round A：全局数据缓存 + Provider 统一 + Tab 切换刷新 + 默认值填充

#### A1. 全局数据缓存

在 `<script>` 顶部新增缓存对象和统一加载函数：

```javascript
// 全局缓存
let _cachedProfiles = null;
let _cachedVoices = {};  // key: provider, value: voice list

async function loadProfiles(forceRefresh = false) {
  if (_cachedProfiles && !forceRefresh) return _cachedProfiles;
  const res = await fetch('/api/voice/profiles');
  _cachedProfiles = await res.json();
  return _cachedProfiles;
}

async function loadVoices(provider, forceRefresh = false) {
  if (_cachedVoices[provider] && !forceRefresh) return _cachedVoices[provider];
  const res = await fetch(`/api/voice/provider-voices?provider=${encodeURIComponent(provider)}`);
  const data = await res.json();
  _cachedVoices[provider] = data.voices || data || [];
  return _cachedVoices[provider];
}

function populateProfileSelect(selectEl, selectedId = '') {
  selectEl.innerHTML = '';
  if (!_cachedProfiles || _cachedProfiles.length === 0) {
    selectEl.innerHTML = '<option value="">无可用人设</option>';
    return;
  }
  _cachedProfiles.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.name;
    if (p.id === selectedId) opt.selected = true;
    selectEl.appendChild(opt);
  });
}

async function populateVoiceSelect(selectEl, provider, selectedVoiceId = '') {
  selectEl.innerHTML = '<option value="">加载音色中…</option>';
  try {
    const voices = await loadVoices(provider);
    selectEl.innerHTML = '<option value="">选择音色</option>';
    voices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.provider_voice_id;
      opt.textContent = `${v.name || v.provider_voice_id} (${v.voice_type || ''})`;
      if (v.provider_voice_id === selectedVoiceId) opt.selected = true;
      selectEl.appendChild(opt);
    });
  } catch (e) {
    selectEl.innerHTML = '<option value="">加载失败</option>';
  }
}
```

然后将现有的 3 处独立 `fetch('/api/voice/profiles')` 调用全部替换为使用缓存。

#### A2. Provider 统一

（1）隐藏 mock 选项：所有 Provider 下拉（`providerSelect`、`voiceProvider`、`deleteProvider`、`cloneProvider`、`designProvider`、`newBindingProvider`、`batchProvider`）移除 `<option value="mock">`。

开发模式在 URL 加 `?dev=1` 参数时才显示 mock：

```javascript
const showMock = new URLSearchParams(location.search).has('dev');
if (!showMock) {
  document.querySelectorAll('select option[value="mock"]').forEach(opt => opt.remove());
}
```

#### A3. Tab 切换自动刷新

修改 Tab 切换逻辑，添加切换回调：

```javascript
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    // ... 现有切换逻辑 ...

    const tab = btn.dataset.tab;
    if (tab === 'bindings') {
      loadProfiles(true).then(() => {
        populateProfileSelect(document.getElementById('bindingProfileSelect'));
        populateProfileSelect(document.getElementById('newBindingProfile'));
      });
      // 同时刷新绑定创建表单的音色下拉
      const provider = document.getElementById('newBindingProvider').value;
      if (provider) refreshBindingVoiceSelect(provider);
    }
    if (tab === 'tts') {
      loadProfiles(true).then(() => {
        populateProfileSelect(profileSelect);
      });
    }
    if (tab === 'batch') {
      loadProfiles(true).then(() => {
        populateProfileSelect(document.getElementById('batchProfile'));
      });
    }
  });
});
```

#### A4. 默认值填充

页面初始化时自动填入合理默认值：

```javascript
// 克隆 Tab 默认值
document.getElementById('cloneModel').value = 'speech-2.8-hd';
document.getElementById('clonePreviewText').value = '你好，这是一段声音克隆的试听文本，用于验证克隆效果。';

// 设计 Tab 默认值
document.getElementById('designPreviewText').value = '你好，这是一段声音设计的试听文本。';
```

HTML 层面也修改默认值属性：
- 克隆 Tab `cloneModel` 的 `placeholder` 改为 `value="speech-2.8-hd"`
- `clonePreviewText` 的 `placeholder` 改为预填文本

#### A5. 绑定管理 Tab 添加"创建人设"表单

在绑定管理 Tab（`tab-bindings`）的最顶部（"声音绑定列表" card 之前）新增一个 card：

```html
<div class="card">
  <div class="card-title">创建人设</div>
  <div class="config-grid">
    <div class="form-group">
      <label for="newProfileId">人设 ID（英文标识）</label>
      <input type="text" id="newProfileId" placeholder="如 narrator_female">
    </div>
    <div class="form-group">
      <label for="newProfileName">人设名称</label>
      <input type="text" id="newProfileName" placeholder="如 女性旁白">
    </div>
    <div class="form-group full-width">
      <label for="newProfileDesc">描述（可选）</label>
      <input type="text" id="newProfileDesc" placeholder="温柔知性的女性旁白音色">
    </div>
    <div class="form-group">
      <label for="newProfileGender">性别风格（可选）</label>
      <select id="newProfileGender">
        <option value="">不指定</option>
        <option value="male">male</option>
        <option value="female">female</option>
      </select>
    </div>
    <div class="form-group">
      <label for="newProfileAge">年龄风格（可选）</label>
      <select id="newProfileAge">
        <option value="">不指定</option>
        <option value="young">young</option>
        <option value="middle_aged">middle_aged</option>
        <option value="elderly">elderly</option>
      </select>
    </div>
  </div>
  <button class="btn-primary" onclick="handleCreateProfile()">创建人设</button>
  <div id="createProfileResult"></div>
</div>
```

JS 逻辑：

```javascript
async function handleCreateProfile() {
  const id = document.getElementById('newProfileId').value.trim();
  const name = document.getElementById('newProfileName').value.trim();
  const description = document.getElementById('newProfileDesc').value.trim();
  const genderStyle = document.getElementById('newProfileGender').value;
  const ageStyle = document.getElementById('newProfileAge').value;
  const resultDiv = document.getElementById('createProfileResult');

  if (!id || !name) {
    resultDiv.innerHTML = '<div class="error-msg">请填写人设 ID 和名称</div>';
    return;
  }

  try {
    const payload = { id, name };
    if (description) payload.description = description;
    if (genderStyle) payload.gender_style = genderStyle;
    if (ageStyle) payload.age_style = ageStyle;

    const resp = await fetch('/api/voice/profiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok) {
      resultDiv.innerHTML = `<div class="error-msg">创建失败: ${esc(data.detail || JSON.stringify(data))}</div>`;
      return;
    }
    resultDiv.innerHTML = `<div class="success-msg">创建成功: ${esc(data.name)} (${esc(data.id)})</div>`;

    // 刷新所有人设下拉
    await loadProfiles(true);
    populateProfileSelect(document.getElementById('bindingProfileSelect'));
    populateProfileSelect(document.getElementById('newBindingProfile'));

    // 清空输入
    document.getElementById('newProfileId').value = '';
    document.getElementById('newProfileName').value = '';
    document.getElementById('newProfileDesc').value = '';
  } catch (e) {
    resultDiv.innerHTML = `<div class="error-msg">网络错误: ${esc(e.message)}</div>`;
  }
}
```

创建成功后自动刷新全局人设缓存，所有人设下拉立即可见新人设。

### Round B：绑定创建表单音色联动 + 克隆/设计成功后一键绑定

#### B1. 绑定创建表单：Voice ID 改为下拉选择

将绑定管理 Tab 的"创建绑定"表单中的 `newBindingVoiceId` 从 `<input type="text">` 改为 `<select>`，根据选中的 Provider 动态加载可用音色：

HTML 修改：
```html
<!-- 原来 -->
<div class="form-group">
  <label for="newBindingVoiceId">Provider Voice ID</label>
  <input type="text" id="newBindingVoiceId" placeholder="如 Wise_Woman">
</div>

<!-- 改为 -->
<div class="form-group">
  <label for="newBindingVoiceId">Provider Voice ID</label>
  <select id="newBindingVoiceId" style="padding:8px;border:1px solid #e2e8f0;border-radius:6px">
    <option value="">请先选择 Provider</option>
  </select>
</div>
```

JS 逻辑：Provider 下拉变化时自动刷新音色列表：

```javascript
async function refreshBindingVoiceSelect(provider) {
  const voiceSel = document.getElementById('newBindingVoiceId');
  await populateVoiceSelect(voiceSel, provider);
}

document.getElementById('newBindingProvider').addEventListener('change', (e) => {
  refreshBindingVoiceSelect(e.target.value);
  // 清空或重设音色缓存
  delete _cachedVoices[e.target.value];
});

// 页面初始化时也触发一次
const initProvider = document.getElementById('newBindingProvider').value;
if (initProvider) refreshBindingVoiceSelect(initProvider);
```

#### B2. 绑定创建表单：Model 改为下拉选择

将 `newBindingModel` 从 `<input type="text">` 改为 `<select>`，列出常用模型：

```html
<div class="form-group">
  <label for="newBindingModel">Model</label>
  <select id="newBindingModel" style="padding:8px;border:1px solid #e2e8f0;border-radius:6px">
    <option value="speech-2.8-hd" selected>speech-2.8-hd（高清）</option>
    <option value="speech-2.8-turbo">speech-2.8-turbo（快速）</option>
    <option value="speech-2.6-hd">speech-2.6-hd（低延迟高清）</option>
    <option value="speech-2.6-turbo">speech-2.6-turbo（低延迟快速）</option>
    <option value="speech-02-hd">speech-02-hd（经典高清）</option>
    <option value="speech-02-turbo">speech-02-turbo（经典快速）</option>
  </select>
</div>
```

#### B3. 克隆成功后添加"一键绑定到人设"

在 `handleCloneVoice()` 成功分支的结果 HTML 中追加绑定面板：

```javascript
html += `<div style="margin-top:12px;padding:12px;background:#f7fafc;border-radius:8px">
  <div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速绑定到人设</div>
  <div style="display:flex;gap:8px;align-items:center">
    <select id="cloneBindProfile" style="flex:1;padding:6px;border:1px solid #e2e8f0;border-radius:6px"></select>
    <select id="cloneBindModel" style="width:160px;padding:6px;border:1px solid #e2e8f0;border-radius:6px">
      <option value="speech-2.8-hd" selected>speech-2.8-hd</option>
      <option value="speech-2.8-turbo">speech-2.8-turbo</option>
    </select>
    <button class="btn-primary" id="cloneBindBtn" style="margin:0;white-space:nowrap">绑定</button>
  </div>
  <div id="cloneBindResult" style="margin-top:6px"></div>
</div>`;

// 渲染后填充人设下拉 + 绑定事件
setTimeout(() => {
  const sel = document.getElementById('cloneBindProfile');
  if (sel) populateProfileSelect(sel);
  const btn = document.getElementById('cloneBindBtn');
  if (btn) {
    btn.onclick = async () => {
      const profileId = document.getElementById('cloneBindProfile').value;
      const model = document.getElementById('cloneBindModel').value;
      if (!profileId) { alert('请选择人设'); return; }
      try {
        await bindVoiceToProfile(voiceId, provider, profileId, model);
        document.getElementById('cloneBindResult').innerHTML =
          '<div class="success-msg" style="font-size:0.82rem">绑定成功!</div>';
      } catch (e) {
        document.getElementById('cloneBindResult').innerHTML =
          `<div class="error-msg" style="font-size:0.82rem">绑定失败: ${esc(e.message)}</div>`;
      }
    };
  }
}, 0);
```

#### B4. 设计成功后同样添加绑定面板

在 `handleDesignVoice()` 成功分支中做相同处理（voice_id 从返回的 `data.voice_id` 获取）。

#### B5. 音色列表"绑定到人设"改为下拉选择

将 `quickBindVoice()` 中的 `prompt()` 替换为内联面板：

```javascript
async function quickBindVoice(voiceId, voiceName, provider) {
  const existingPanel = document.getElementById('quickBindPanel');
  if (existingPanel) existingPanel.remove();

  const profiles = await loadProfiles();
  if (!profiles || profiles.length === 0) {
    alert('没有可用的人设，请先在绑定管理中创建人设');
    return;
  }

  const panel = document.createElement('div');
  panel.id = 'quickBindPanel';
  panel.style.cssText = 'padding:12px;background:#f7fafc;border-radius:8px;margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap';
  panel.innerHTML = `
    <span style="font-size:0.82rem">将 <code>${esc(voiceId)}</code> 绑定到：</span>
    <select id="quickBindProfileSel" style="padding:6px;border:1px solid #e2e8f0;border-radius:6px;min-width:140px"></select>
    <select id="quickBindModelSel" style="padding:6px;border:1px solid #e2e8f0;border-radius:6px;min-width:140px">
      <option value="speech-2.8-hd" selected>speech-2.8-hd</option>
      <option value="speech-2.8-turbo">speech-2.8-turbo</option>
      <option value="speech-2.6-hd">speech-2.6-hd</option>
      <option value="speech-2.6-turbo">speech-2.6-turbo</option>
    </select>
    <button class="btn-primary" id="quickBindConfirm" style="margin:0">确认绑定</button>
    <button class="btn-sm" onclick="document.getElementById('quickBindPanel').remove()">取消</button>
    <div id="quickBindMsg" style="width:100%;font-size:0.82rem"></div>
  `;

  document.getElementById('voiceListResults').appendChild(panel);
  populateProfileSelect(document.getElementById('quickBindProfileSel'));

  document.getElementById('quickBindConfirm').onclick = async () => {
    const profileId = document.getElementById('quickBindProfileSel').value;
    const model = document.getElementById('quickBindModelSel').value;
    if (!profileId) return;
    try {
      await bindVoiceToProfile(voiceId, provider, profileId, model);
      document.getElementById('quickBindMsg').innerHTML =
        `<span class="success-msg">绑定成功: ${esc(voiceName)} → ${esc(profileId)}</span>`;
    } catch (e) {
      document.getElementById('quickBindMsg').innerHTML =
        `<span class="error-msg">绑定失败: ${esc(e.message)}</span>`;
    }
  };
}
```

#### B6. 统一绑定函数

将多处绑定逻辑抽取为一个公共函数（接受 model 参数）：

```javascript
async function bindVoiceToProfile(voiceId, provider, profileId, model = 'speech-2.8-hd') {
  const resp = await fetch(`/api/voice/profiles/${profileId}/bindings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider: provider,
      model: model,
      provider_voice_id: voiceId,
      params: {},
      priority: 1,
    }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}
```

### Round C：剧本行 profile 缓存 + 删除联动 + T2A Tab 人设-音色联动提示

#### C1. 剧本行 profile 下拉使用缓存

修改 `addScriptLine()` 函数，不再每次 `fetch`，改用缓存 + `populateProfileSelect()`：

```javascript
function addScriptLine(role = '', text = '', profileId = '') {
  // ... 现有 DOM 创建逻辑 ...

  // 使用缓存填充，不再每行单独 fetch
  const sel = document.getElementById(`scriptProfile_${id}`);
  if (_cachedProfiles) {
    populateProfileSelect(sel, profileId);
  } else {
    loadProfiles().then(() => populateProfileSelect(sel, profileId));
  }
}
```

#### C2. 删除音色后提示绑定影响

在 `handleDeleteVoice()` 成功分支追加提示，并刷新音色缓存：

```javascript
// 清除该 provider 的音色缓存
delete _cachedVoices[provider];

resultsEl.innerHTML += `<div style="font-size:0.82rem;color:#ed8936;margin-top:8px">
  注意：如果该音色已绑定到人设，请到「绑定管理」Tab 检查并清理失效绑定。
</div>`;
```

#### C3. T2A Tab 人设选择后显示绑定状态

在 T2A Tab 的人设下拉变化时，查询该人设在当前 provider 下是否有 binding，给用户即时反馈：

```javascript
async function checkBindingStatus() {
  const profileId = profileSelect.value;
  const provider = providerSelect.value;
  const statusEl = document.getElementById('bindingStatus');
  if (!statusEl) return;

  if (!profileId || !provider) {
    statusEl.innerHTML = '';
    return;
  }

  try {
    const resp = await fetch(`/api/voice/profiles/${profileId}/bindings`);
    const bindings = await resp.json();
    const matched = bindings.filter(b => b.provider === provider && b.status === 'available');
    if (matched.length > 0) {
      const b = matched[0];
      statusEl.innerHTML = `<span style="font-size:0.78rem;color:#2f855a">
        ✓ 已绑定: ${esc(b.provider_voice_id)} (${esc(b.model)})
      </span>`;
    } else {
      statusEl.innerHTML = `<span style="font-size:0.78rem;color:#e53e3e">
        ✗ 该人设在 ${esc(provider)} 下无可用绑定，请到「绑定管理」创建
      </span>`;
    }
  } catch (e) {
    statusEl.innerHTML = '';
  }
}

profileSelect.addEventListener('change', checkBindingStatus);
providerSelect.addEventListener('change', checkBindingStatus);
```

HTML 中在人设下拉和 Provider 下拉下方添加状态显示区：

```html
<div id="bindingStatus" style="margin-top:4px;min-height:20px"></div>
```

这样用户在 T2A Tab 选择人设 + Provider 后，立即能看到是否有可用绑定，避免点了生成才报错。

#### C4. 克隆/设计成功后提供自定义试听入口

在克隆和设计成功结果区（一键绑定面板下方），追加一个"快速试听"区块：

```javascript
// 追加到克隆/设计成功的 html 中（绑定面板之后）
html += `<div style="margin-top:12px;padding:12px;background:#f0fff4;border-radius:8px">
  <div style="font-size:0.85rem;font-weight:600;margin-bottom:8px">快速试听</div>
  <div style="display:flex;gap:8px;align-items:center">
    <input type="text" id="quickPreviewText" placeholder="输入试听文本" value="你好，这是一段测试语音。"
      style="flex:1;padding:6px;border:1px solid #e2e8f0;border-radius:6px;font-size:0.85rem">
    <button class="btn-primary" id="quickPreviewBtn" style="margin:0;white-space:nowrap">试听</button>
  </div>
  <div id="quickPreviewResult" style="margin-top:8px"></div>
</div>`;
```

点击"试听"时，调用同步 T2A API，直接传 voice_id（无需绑定到人设即可试听）：

```javascript
document.getElementById('quickPreviewBtn').onclick = async () => {
  const text = document.getElementById('quickPreviewText').value.trim();
  if (!text) return;
  const resultDiv = document.getElementById('quickPreviewResult');
  resultDiv.innerHTML = '<span class="spinner"></span> 生成中…';
  try {
    // 需要一个已绑定的 profile 才能用 /api/voice/render
    // 这里用一种更直接的方式：直接调用 provider-voices 接口验证 voice 存在后
    // 提示用户先绑定，或者如果已经绑定了就用绑定的 profile 试听
    const cloneBindProfile = document.getElementById('cloneBindProfile') ||
                             document.getElementById('designBindProfile');
    const profileId = cloneBindProfile ? cloneBindProfile.value : '';
    if (!profileId) {
      resultDiv.innerHTML = '<span style="color:#ed8936;font-size:0.82rem">请先在上方绑定到人设后再试听</span>';
      return;
    }
    const resp = await fetch('/api/voice/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        profile_id: profileId,
        provider: provider,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      resultDiv.innerHTML = `<span style="color:#e53e3e;font-size:0.82rem">试听失败: ${esc(data.error?.message || JSON.stringify(data))}</span>`;
      return;
    }
    if (data.audio_asset && data.audio_asset.url) {
      resultDiv.innerHTML = `<audio class="audio-player" controls autoplay>
        <source src="${esc(data.audio_asset.url)}" type="audio/mpeg">
      </audio>`;
    } else {
      resultDiv.innerHTML = '<span style="color:#718096;font-size:0.82rem">未返回音频数据</span>';
    }
  } catch (e) {
    resultDiv.innerHTML = `<span style="color:#e53e3e;font-size:0.82rem">网络错误: ${esc(e.message)}</span>`;
  }
};
```

注意：试听依赖先完成绑定（因为 `/api/voice/render` 需要 profile_id + binding）。所以 UI 上的顺序是：成功 → 绑定到人设 → 试听。试听按钮在未绑定时提示"请先绑定"。

#### C5. 音色列表显示绑定状态

在 `renderVoiceTable()` 函数中，渲染音色表格时查询所有 binding，标注每个音色的绑定状态。

加载音色列表时同时获取所有 profile 的 bindings：

```javascript
async function loadAllBindings() {
  const profiles = await loadProfiles();
  if (!profiles || profiles.length === 0) return {};
  // 返回 { voice_id: [profile_name, ...] } 的映射
  const voiceBindMap = {};
  for (const p of profiles) {
    try {
      const resp = await fetch(`/api/voice/profiles/${p.id}/bindings`);
      const bindings = await resp.json();
      if (Array.isArray(bindings)) {
        bindings.forEach(b => {
          if (b.status === 'available') {
            if (!voiceBindMap[b.provider_voice_id]) voiceBindMap[b.provider_voice_id] = [];
            voiceBindMap[b.provider_voice_id].push(p.name);
          }
        });
      }
    } catch (e) {}
  }
  return voiceBindMap;
}
```

在 `handleListVoices()` 中调用并传给 `renderVoiceTable()`：

```javascript
async function handleListVoices() {
  // ... 现有查询逻辑 ...
  const voiceBindMap = await loadAllBindings();
  renderVoiceTable(voices, provider, total, voiceBindMap);
}
```

修改 `renderVoiceTable()` 表头增加"绑定状态"列：

```javascript
function renderVoiceTable(voices, provider, total, voiceBindMap = {}) {
  // 表头加一列
  // <th>绑定状态</th>

  voices.forEach(v => {
    const boundProfiles = voiceBindMap[v.provider_voice_id];
    const bindStatusHtml = boundProfiles && boundProfiles.length > 0
      ? `<span style="color:#2f855a;font-size:0.78rem">已绑定: ${esc(boundProfiles.join(', '))}</span>`
      : `<span style="color:#ed8936;font-size:0.78rem">未绑定</span>`;

    html += `<tr>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>${bindStatusHtml}</td>
      <td><button class="btn-sm bind-voice-btn" ...>绑定到人设</button></td>
    </tr>`;
  });
}
```

这样用户在音色列表中一眼能看到哪些音色是"孤立"的（未绑定到任何人设），需要去绑定才能用于 T2A 生成。

## 验收标准

1. `python -m pytest tests/ -x -q` 全部通过（本次不涉及后端改动，但确保不破坏现有测试）
2. **Provider 统一**：默认不显示 mock，加 `?dev=1` 时才显示
3. **Tab 切换刷新**：在绑定 Tab 创建新绑定后切到 T2A Tab，人设下拉能看到最新数据
4. **克隆/设计→绑定**：成功后出现人设下拉 + Model 下拉 + 绑定按钮，点击可直接创建 binding
5. **音色列表绑定**：点"绑定到人设"弹出内联面板（人设下拉 + Model 下拉），不再 prompt 输入
6. **创建绑定音色联动**：绑定管理 Tab "创建绑定"中 Provider 切换时自动加载可选音色下拉、Model 为下拉选择
7. **剧本行缓存**：添加 10 行剧本台词，Network 面板只看到 1 次 profiles 请求
8. **删除提示**：删除音色后看到绑定影响警告，音色缓存自动刷新
9. **T2A 绑定状态**：选人设 + Provider 后下方显示绑定状态（✓ 已绑定 / ✗ 无绑定）
10. **默认值**：克隆 Tab 的 model 默认 `speech-2.8-hd`、preview_text 有预填文本；设计 Tab 同理
11. **全部人设可选**：T2A / 绑定管理 / 批量生成 / 剧本行的人设下拉都能查到系统中所有人设
12. **创建人设**：在绑定管理 Tab 可以创建新人设（填 ID + 名称），创建后所有人设下拉立即刷新
13. **克隆/设计试听**：成功 → 绑定到人设 → 输入文本 → 试听，完整链路可用；未绑定时试听按钮提示"请先绑定"
14. **音色绑定状态**：音色列表每行显示"已绑定: xxx人设"或"未绑定"标签，未绑定的音色一眼可辨

## 不要做的事

1. **不要修改后端 Python 文件** — 所有 API 已就绪
2. **不要修改测试文件** — 纯前端改动
3. **不要修改 admin.html** — 管理面板不在本次范围
4. **不要新增 API 端点** — 复用现有接口
5. **不要引入前端框架** — 保持原生 JS
6. **不要修改现有 API 的请求/响应格式** — 只改前端调用方式
