# P5 任务：前端产品功能增强

## 目标

补齐前端测试面板的功能缺口，让音色管理 → 绑定配置 → 语音生成 → 历史查看形成完整闭环。

## 分轮实施

| 轮次 | 编号 | 内容 | 改动范围 |
|------|------|------|----------|
| 1 | A | T2A 参数调节 + 流式模式 UI 修正 | `schemas.py`, `voice_render.py`, `index.html` |
| 2 | B | Binding 管理 Tab | `index.html` |
| 3 | C | 音色列表增强（搜索 + 试听 + 一键绑定） | `index.html` |
| 4 | D | 历史记录 + Job 列表 | 后端新增 API + `index.html` |

---

## P5-A：T2A 参数调节 + 流式模式 UI 修正

### 需要修改的文件

| 文件 | 操作 |
|------|------|
| `app/domain/schemas.py` | 修改（VoiceRenderRequest 新增可选参数） |
| `app/api/voice_render.py` | 修改（传递 voice_overrides） |
| `app/static/index.html` | 修改 |

### 1. 后端：暴露语音参数

当前 `VoiceRenderService.render_voice()` 已支持 `voice_overrides` 参数，但 API 层和 Schema 没有暴露。

**`app/domain/schemas.py`** — `VoiceRenderRequest` 新增可选字段：

```python
class VoiceRenderRequest(BaseModel):
    text: str = Field(min_length=1)
    profile_id: str = "deep_night_programmer"
    provider: str | None = None
    need_subtitle: bool = True
    output_format: str = "hex"
    # 新增：语音参数覆盖（可选）
    speed: float | None = Field(None, ge=0.5, le=2.0, description="语速 0.5-2.0")
    vol: float | None = Field(None, ge=0.1, le=10.0, description="音量 0.1-10.0")
    pitch: int | None = Field(None, ge=-12, le=12, description="音调 -12 到 12")
    emotion: str | None = Field(None, description="情绪：happy/sad/angry/fearful/disgusted/surprised/neutral")
```

**`app/api/voice_render.py`** — 构造 voice_overrides 传给 service：

```python
@router.post("/render", response_model=VoiceRenderResponse)
async def render_voice(
    request: VoiceRenderRequest,
    session: Session = Depends(get_session),
):
    voice_overrides = {}
    if request.speed is not None:
        voice_overrides["speed"] = request.speed
    if request.vol is not None:
        voice_overrides["vol"] = request.vol
    if request.pitch is not None:
        voice_overrides["pitch"] = request.pitch
    if request.emotion is not None:
        voice_overrides["emotion"] = request.emotion
    return await service.render_voice(session, request, voice_overrides=voice_overrides or None)
```

同样修改 `StreamRenderRequest` 和 `stream_render_service.py`，使流式模式也支持语音参数。

### 2. 前端：T2A 配置区新增参数控件

在"配置"卡片的 config-grid 中，"生成模式"之前，新增一行"语音参数"：

```html
<div class="form-group full-width">
    <label>语音参数（可选，不填使用绑定默认值）</label>
    <div class="param-row">
        <div class="param-item">
            <label for="paramSpeed">语速</label>
            <input type="number" id="paramSpeed" step="0.05" min="0.5" max="2.0" placeholder="0.5-2.0">
        </div>
        <div class="param-item">
            <label for="paramVol">音量</label>
            <input type="number" id="paramVol" step="0.1" min="0.1" max="10.0" placeholder="0.1-10.0">
        </div>
        <div class="param-item">
            <label for="paramPitch">音调</label>
            <input type="number" id="paramPitch" step="1" min="-12" max="12" placeholder="-12~12">
        </div>
        <div class="param-item">
            <label for="paramEmotion">情绪</label>
            <select id="paramEmotion">
                <option value="">默认</option>
                <option value="happy">happy</option>
                <option value="sad">sad</option>
                <option value="angry">angry</option>
                <option value="fearful">fearful</option>
                <option value="disgusted">disgusted</option>
                <option value="surprised">surprised</option>
                <option value="neutral">neutral</option>
            </select>
        </div>
    </div>
</div>
```

CSS `.param-row` 样式：

```css
.param-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}
.param-item {
    flex: 1;
    min-width: 100px;
}
.param-item label {
    display: block;
    font-size: 0.78rem;
    color: #718096;
    margin-bottom: 4px;
}
.param-item input, .param-item select {
    width: 100%;
    padding: 6px 8px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 0.85rem;
}
```

### 3. 前端：handleGenerate() 传递参数

在构造 payload 时读取参数值并加入请求体：

```javascript
const speed = document.getElementById('paramSpeed').value;
const vol = document.getElementById('paramVol').value;
const pitch = document.getElementById('paramPitch').value;
const emotion = document.getElementById('paramEmotion').value;

const payload = {
    text,
    profile_id: profileId,
    provider,
    need_subtitle: subtitle,
    ...(speed ? { speed: parseFloat(speed) } : {}),
    ...(vol ? { vol: parseFloat(vol) } : {}),
    ...(pitch ? { pitch: parseInt(pitch) } : {}),
    ...(emotion ? { emotion } : {}),
    // ... 原有逻辑
};
```

流式模式的 `startStreamGenerate()` 同样需要传递这些参数到 WebSocket start 消息中。

### 4. 前端：流式模式 UI 修正

- 当选择"流式生成"时，隐藏"生成字幕"复选框（流式模式不支持字幕）
- 切换回其他模式时恢复显示

```javascript
genModes.forEach(r => r.addEventListener('change', () => {
    const mode = document.querySelector('input[name="genMode"]:checked').value;
    variantCountRow.classList.toggle('visible', mode === 'variants');
    // 流式模式隐藏字幕选项
    document.getElementById('subtitleRow').style.display = mode === 'stream' ? 'none' : '';
}));
```

需要给字幕复选框的外层 div 加 `id="subtitleRow"`。

### 5. 前端：音频格式选择

在配置区新增格式选择下拉框：

```html
<div class="form-group">
    <label for="outputFormat">音频格式</label>
    <select id="outputFormat">
        <option value="mp3">MP3</option>
        <option value="wav">WAV</option>
        <option value="flac">FLAC</option>
        <option value="pcm">PCM</option>
    </select>
</div>
```

生成请求中 `output_format` 从该下拉框取值，替代当前硬编码的 "hex"。

### 验收标准

1. `python -m pytest tests/ -x -q` 全部通过
2. T2A Tab 显示语速/音量/音调/情绪四个参数控件
3. 不填参数时行为与之前一致（使用绑定默认值）
4. 填入参数后，单条/异步/流式三种模式都能正确传递
5. 选择"流式生成"时字幕复选框自动隐藏
6. 音频格式下拉框可选，生成请求中正确传递 output_format

### 不要做的事

- 不要修改 `voice_render_service.py`（已支持 voice_overrides）
- 不要修改 Provider 层
- 不要新增测试文件（本轮为前端 + 薄后端改动）

---

## P5-B：Binding 管理 Tab

### 需要修改的文件

| 文件 | 操作 |
|------|------|
| `app/static/index.html` | 修改（新增第 5 个 Tab） |

### Tab 设计

在 Tab 导航栏末尾新增：

```html
<button class="tab-btn" data-tab="bindings">绑定管理</button>
```

新增 Tab 内容区 `id="tab-bindings"`，包含两个卡片：

#### 卡片 1：查看绑定列表

```html
<div class="card">
    <div class="card-title">声音绑定列表</div>
    <div class="config-grid">
        <div class="form-group">
            <label for="bindingProfileSelect">声音人设</label>
            <select id="bindingProfileSelect">
                <!-- 页面加载时从 /api/voice/profiles 填充 -->
            </select>
        </div>
    </div>
    <button class="btn-primary" onclick="handleListBindings()">查询</button>
    <div id="bindingListResults"></div>
</div>
```

列表展示为表格：

| 列 | 字段 |
|------|------|
| ID | binding.id |
| Provider | binding.provider |
| Model | binding.model |
| Voice ID | binding.provider_voice_id |
| Voice Name | binding.provider_voice_name |
| 参数 | binding.params（JSON 展示） |
| 优先级 | binding.priority |
| 状态 | binding.status |
| 操作 | [删除] 按钮 |

删除按钮调用 `DELETE /api/voice/bindings/{binding_id}`，成功后刷新列表。

#### 卡片 2：创建绑定

```html
<div class="card">
    <div class="card-title">创建绑定</div>
    <div class="config-grid">
        <div class="form-group">
            <label for="newBindingProfile">声音人设</label>
            <select id="newBindingProfile">
                <!-- 从 /api/voice/profiles 填充 -->
            </select>
        </div>
        <div class="form-group">
            <label for="newBindingProvider">Provider</label>
            <select id="newBindingProvider">
                <option value="mock">mock</option>
                <option value="minimax">minimax</option>
            </select>
        </div>
        <div class="form-group">
            <label for="newBindingModel">Model</label>
            <input type="text" id="newBindingModel" value="speech-2.8-hd" placeholder="speech-2.8-hd">
        </div>
        <div class="form-group">
            <label for="newBindingVoiceId">Provider Voice ID</label>
            <input type="text" id="newBindingVoiceId" placeholder="如 Wise_Woman">
        </div>
        <div class="form-group">
            <label for="newBindingPriority">优先级</label>
            <input type="number" id="newBindingPriority" value="1" min="1" max="99">
        </div>
        <div class="form-group full-width">
            <label for="newBindingParams">参数（JSON，可选）</label>
            <input type="text" id="newBindingParams" placeholder='{"speed": 0.9}'>
        </div>
    </div>
    <button class="btn-primary" onclick="handleCreateBinding()">创建</button>
    <div id="createBindingResult"></div>
</div>
```

创建调用 `POST /api/voice/profiles/{profile_id}/bindings`。

### JS 函数

```javascript
async function handleListBindings() {
    const profileId = document.getElementById('bindingProfileSelect').value;
    const resp = await fetch(`/api/voice/profiles/${profileId}/bindings`);
    const data = await resp.json();
    // 渲染为表格，每行有删除按钮
}

async function handleCreateBinding() {
    const profileId = document.getElementById('newBindingProfile').value;
    const payload = {
        provider: ...,
        model: ...,
        provider_voice_id: ...,
        priority: ...,
        params: JSON.parse(paramsStr || '{}'),
    };
    const resp = await fetch(`/api/voice/profiles/${profileId}/bindings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
    });
    // 显示结果
}

async function handleDeleteBinding(bindingId) {
    if (!confirm('确定删除？')) return;
    await fetch(`/api/voice/bindings/${bindingId}`, { method: 'DELETE' });
    // 刷新列表
}
```

### 验收标准

1. `python -m pytest tests/ -x -q` 全部通过
2. 第 5 个 Tab"绑定管理"可正常切换
3. 选择 profile 后查询到该 profile 的所有绑定
4. 可以创建新绑定，创建后列表自动刷新
5. 可以删除（软删除）绑定，删除后列表自动刷新
6. 参数 JSON 填写错误时给出友好提示

### 不要做的事

- 不要修改后端任何文件
- 不要修改其他 Tab 的功能

---

## P5-C：音色列表增强

### 需要修改的文件

| 文件 | 操作 |
|------|------|
| `app/static/index.html` | 修改（音色管理 Tab 增强） |

### 功能增强

#### 1. 搜索框

在音色列表卡片中新增搜索输入框，实时过滤已加载的音色列表：

```html
<div class="form-group full-width">
    <label for="voiceSearch">搜索（name / voice_id / description）</label>
    <input type="text" id="voiceSearch" placeholder="输入关键词过滤…" oninput="filterVoiceList()">
</div>
```

`filterVoiceList()` 在前端内存中过滤已加载的音色数据（不发新请求），匹配 name / provider_voice_id / description 字段。

#### 2. 试听按钮

每个音色项旁边显示"试听"按钮。点击后：
1. 弹出一个小输入框让用户输入试听文本（默认值："你好，欢迎使用声音实验室"）
2. 调用 `POST /api/voice/render` 传入 `provider_voice_id`... 

等等 — 当前 render API 只接受 `profile_id`，不能直接传 `provider_voice_id`。试听需要先有 binding。

**替代方案**：试听按钮改为"用此音色创建绑定"，跳转到绑定管理 Tab 并自动填入 provider + voice_id + model。

#### 3. 一键绑定

每个音色项显示"绑定到人设"按钮：
- 点击后弹出选择人设的下拉框（从 /api/voice/profiles 获取）
- 用户选择人设后，自动调用 `POST /api/voice/profiles/{profile_id}/bindings`
- 成功后显示"绑定成功"提示

```javascript
async function quickBindVoice(providerVoiceId, provider, voiceName) {
    // 弹出 profile 选择
    const profileId = prompt('输入要绑定的 profile_id', 'deep_night_programmer');
    if (!profileId) return;
    
    const resp = await fetch(`/api/voice/profiles/${profileId}/bindings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            provider: provider,
            model: 'speech-2.8-hd',
            provider_voice_id: providerVoiceId,
            params: {},
            priority: 1,
        }),
    });
    // 显示结果
}
```

#### 4. 分页 / 加载更多

如果音色数量 > 50，只显示前 50 条，底部显示"加载更多"按钮。或者使用虚拟滚动（实现复杂，不推荐）。

简单方案：默认显示前 50 条 + 搜索过滤，不做后端分页。

### 验收标准

1. `python -m pytest tests/ -x -q` 全部通过
2. 搜索框输入后实时过滤音色列表
3. 每个音色项有"绑定到人设"按钮，可一键创建绑定
4. 音色数量多时不会导致页面卡顿（前端过滤 + 截断显示）

### 不要做的事

- 不要修改后端 API
- 不要实现真正的试听功能（需要 render API 改动，留到后续）

---

## P5-D：历史记录 + Job 列表

### 需要修改的文件

| 文件 | 操作 |
|------|------|
| `app/api/voice_jobs.py` | 修改（新增列表查询 API） |
| `app/repositories/voice_job_repo.py` | 修改（新增列表查询方法） |
| `app/static/index.html` | 修改（T2A Tab 新增历史区域） |
| `tests/test_job_list_api.py` | **新建** |

### 1. 后端：Job 列表 API

当前只有 `GET /api/voice/jobs/{job_id}` 单条查询，需要新增列表查询。

**`app/repositories/voice_job_repo.py`** 新增：

```python
def list_jobs(
    session: Session,
    *,
    job_type: str | None = None,
    status: str | None = None,
    profile_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[VoiceJob], int]:
    """返回 (jobs, total_count)"""
```

**`app/api/voice_jobs.py`** 新增：

```python
@router.get("/jobs")
async def list_jobs(
    job_type: str | None = None,
    status: str | None = None,
    profile_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    jobs, total = voice_job_repo.list_jobs(
        session, job_type=job_type, status=status,
        profile_id=profile_id, limit=min(limit, 100), offset=offset,
    )
    return {
        "jobs": [VoiceJobRead(...) for job in jobs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
```

### 2. 前端：T2A Tab 历史记录

在 T2A Tab 的"生成"按钮和结果区之间（或结果区下方），新增"历史记录"折叠区域：

```html
<div class="card" style="margin-top:16px">
    <div class="card-title" style="cursor:pointer" onclick="toggleHistory()">
        历史记录 ▾
    </div>
    <div id="historyArea" style="display:none">
        <div id="historyList"></div>
        <button class="btn-sm" id="loadMoreHistory" onclick="loadMoreHistory()" style="display:none">加载更多</button>
    </div>
</div>
```

页面加载和每次生成完成后自动刷新历史列表。

列表每项显示：
- 时间（created_at）
- 类型（job_type 中文）
- 状态（status badge）
- 文本摘要（input_text 前 30 字 + "..."）
- Provider / Model
- 操作：如果有 audio_asset，显示播放按钮

```javascript
async function loadHistory(offset = 0) {
    const resp = await fetch(`/api/voice/jobs?limit=10&offset=${offset}`);
    const data = await resp.json();
    // 渲染历史列表
}
```

### 3. 测试

**`tests/test_job_list_api.py`** 新建：

```python
def test_list_jobs_empty(test_app):
    """空数据库返回空列表"""

def test_list_jobs_returns_jobs(test_app, seed_profile):
    """生成后可查到 job"""

def test_list_jobs_filter_by_type(test_app, seed_profile):
    """按 job_type 过滤"""

def test_list_jobs_pagination(test_app, seed_profile):
    """分页参数生效"""
```

### 验收标准

1. `python -m pytest tests/ -x -q` 全部通过（含新增 4 个测试）
2. `GET /api/voice/jobs` 返回 Job 列表，支持过滤和分页
3. T2A Tab 底部显示历史记录（可折叠）
4. 历史项显示时间、类型、状态、文本摘要
5. 支持"加载更多"分页

### 不要做的事

- 不要修改现有的 `GET /api/voice/jobs/{job_id}` 端点
- 不要修改其他 Tab 的功能
- 不要在历史列表中显示音频 base64 数据

---

## 总体验收

P5 全部完成后：
- T2A Tab：参数调节 + 格式选择 + 流式字幕隐藏 + 历史记录
- 音色管理 Tab：搜索过滤 + 一键绑定
- 绑定管理 Tab：查看/创建/删除绑定
- 前端 → 后端完整闭环：音色浏览 → 绑定到人设 → 选参数生成 → 查看历史
