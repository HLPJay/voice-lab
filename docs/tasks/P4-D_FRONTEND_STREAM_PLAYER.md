# P4-D 任务：前端 WebSocket 流式播放器

## 目标

在 `app/static/index.html` 的 T2A 生成 Tab 中新增"流式生成"模式。点击生成后通过 WebSocket 连接 `/api/voice/ws/render`，实时显示接收进度，完成后播放完整音频。

## 前置条件

- P4-C 已完成：WebSocket 端点 `ws://host/api/voice/ws/render` 可用
- 消息流：client 发 start → server 回 connected → started → audio_chunk × N → completed

## 需要修改的文件

| 文件 | 操作 |
|------|------|
| `app/static/index.html` | 修改 |

## 详细规范

### 1. 生成模式新增第四项

当前 radio 组（约第 555-558 行）：

```html
<label><input type="radio" name="genMode" value="single" checked> 单条生成</label>
<label><input type="radio" name="genMode" value="async"> 异步生成</label>
<label><input type="radio" name="genMode" value="variants"> 多版本试音</label>
```

修改为：

```html
<label><input type="radio" name="genMode" value="single" checked> 单条生成</label>
<label><input type="radio" name="genMode" value="async"> 异步生成</label>
<label><input type="radio" name="genMode" value="stream"> 流式生成</label>
<label><input type="radio" name="genMode" value="variants"> 多版本试音</label>
```

### 2. handleGenerate() 增加 stream 分支

在 `handleGenerate()` 函数中（约第 813 行），当 `mode === 'stream'` 时调用新的 `startStreamGenerate()` 函数，而非发 HTTP 请求。

```javascript
const mode = document.querySelector('input[name="genMode"]:checked').value;
const isVariant = mode === 'variants';
const isAsync = mode === 'async';
const isStream = mode === 'stream';

// ... 原有 loading 设置 ...

if (isStream) {
    startStreamGenerate(text, profileId, provider, subtitle);
    return;
}

// ... 原有 HTTP 逻辑 ...
```

### 3. 新增 startStreamGenerate() 函数

```javascript
function startStreamGenerate(text, profileId, provider, subtitle) {
    // 1. 构建 WebSocket URL
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${location.host}/api/voice/ws/render`;
    
    // 2. 初始化进度 UI
    resultsArea.innerHTML = `
        <div class="card" id="streamStatusCard">
            <div class="result-label">流式生成</div>
            <div class="stream-progress">
                <span class="spinner"></span>
                <span id="streamStatusText">连接中…</span>
            </div>
            <div class="stream-stats" id="streamStats" style="display:none">
                <span>已接收: <strong id="streamChunkCount">0</strong> 个片段</span>
                <span>已接收时长: <strong id="streamDuration">0</strong> ms</span>
            </div>
        </div>`;
    resultsArea.classList.add('visible');
    
    // 3. 建立 WebSocket 连接
    const ws = new WebSocket(wsUrl);
    const audioChunks = [];  // 收集 base64 chunks
    
    ws.onopen = () => {
        // 发送 start 消息
        ws.send(JSON.stringify({
            event: "start",
            text: text,
            profile_id: profileId,
            provider: provider,
            output_format: "mp3",
            need_subtitle: subtitle,
        }));
    };
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        
        switch (msg.event) {
            case "connected":
                document.getElementById('streamStatusText').textContent = 
                    `已连接 (${msg.request_id})`;
                break;
                
            case "started":
                document.getElementById('streamStatusText').textContent = 
                    `生成中… (${msg.provider} / ${msg.model})`;
                document.getElementById('streamStats').style.display = '';
                break;
                
            case "audio_chunk":
                audioChunks.push(msg.audio_base64);
                document.getElementById('streamChunkCount').textContent = 
                    audioChunks.length;
                if (msg.duration_ms) {
                    // 累加已接收时长
                    const el = document.getElementById('streamDuration');
                    el.textContent = parseInt(el.textContent || '0') + msg.duration_ms;
                }
                break;
                
            case "completed":
                renderStreamResult(msg, audioChunks);
                setLoading(false);
                ws.close();
                break;
                
            case "error":
                resultsArea.innerHTML = `<div class="error-msg">流式生成失败：[${esc(msg.code)}] ${esc(msg.message)}</div>`;
                setLoading(false);
                ws.close();
                break;
        }
    };
    
    ws.onerror = () => {
        resultsArea.innerHTML = `<div class="error-msg">WebSocket 连接失败</div>`;
        setLoading(false);
    };
    
    ws.onclose = (event) => {
        // 如果非正常关闭且没有收到 completed/error
        if (event.code !== 1000 && !resultsArea.querySelector('.result-section') && !resultsArea.querySelector('.error-msg')) {
            resultsArea.innerHTML = `<div class="error-msg">连接断开 (code: ${event.code})</div>`;
            setLoading(false);
        }
    };
}
```

### 4. 新增 renderStreamResult() 函数

将收集到的 base64 chunks 拼接为 Blob，创建 audio URL 播放。同时显示完整音频的下载链接（使用 completed 消息中的 audio_asset）。

```javascript
function renderStreamResult(completed, audioChunks) {
    // 1. 拼接所有 base64 chunk 为二进制
    const binaryParts = audioChunks.map(b64 => {
        const binary = atob(b64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes;
    });
    const blob = new Blob(binaryParts, { type: 'audio/mpeg' });
    const blobUrl = URL.createObjectURL(blob);
    
    // 2. 渲染结果
    const asset = completed.audio_asset;
    resultsArea.innerHTML = `
        <div class="result-section">
            <div class="result-label">流式生成结果</div>
            <span class="job-status status-success">已完成</span>
            <p style="font-size:0.82rem;color:#718096;margin-top:6px">
                任务ID：<code>${esc(completed.job_id)}</code>
                · 片段数: ${completed.total_chunks}
                · 总时长: ${completed.total_duration_ms} ms
                · 字符数: ${completed.total_characters}
            </p>
            <audio class="audio-player" controls preload="auto">
                <source src="${blobUrl}" type="audio/mpeg">
                您的浏览器不支持音频播放
            </audio>
            <div class="action-row">
                ${asset ? `<a class="btn-sm" href="/api/voice/assets/${asset.id}/download" download>下载(服务端)</a>` : ''}
                <a class="btn-sm" href="${blobUrl}" download="stream_audio.mp3">下载(本地缓存)</a>
            </div>
        </div>`;
    resultsArea.classList.add('visible');
}
```

### 5. CSS 补充

在 `<style>` 中新增流式进度样式：

```css
.stream-progress {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 12px 0;
    font-size: 0.9rem;
    color: #4a5568;
}

.stream-stats {
    display: flex;
    gap: 24px;
    font-size: 0.82rem;
    color: #718096;
    margin-top: 8px;
    padding: 8px 12px;
    background: #f7fafc;
    border-radius: 6px;
}
```

## 行为说明

1. **连接中** — 显示 spinner + "连接中…"
2. **收到 connected** — 更新文字为 "已连接 (request_id)"
3. **收到 started** — 更新文字为 "生成中… (provider / model)"，显示统计区域
4. **每收到 audio_chunk** — 更新片段计数和累计时长
5. **收到 completed** — 停止 loading，拼接音频并渲染播放器 + 下载链接
6. **收到 error** — 显示错误信息，停止 loading
7. **连接断开** — 如果没有正常完成，显示断开提示

## 验收标准

1. `python -m pytest tests/ -x -q` 全部通过（198 passed，本轮无新增测试）
2. 启动 `uvicorn app.main:app`，打开 `/static/index.html`
3. T2A Tab 生成模式显示四个选项：单条 / 异步 / 流式 / 多版本
4. 选择"流式生成"+ mock provider，点击生成：
   - 显示连接进度（连接中 → 已连接 → 生成中）
   - 片段计数实时更新
   - 完成后显示播放器，可播放音频
   - 下载链接可用
5. 选择 minimax provider（需 API Key），点击生成：
   - 流式接收真实 MiniMax 音频
   - 完成后可正常播放
6. 其他三种模式（单条/异步/多版本）功能不受影响

## 不要做的事

- 不要修改后端任何文件
- 不要修改 `admin.html`
- 不要新增测试文件（前端无自动化测试）
- 不要实现实时播放（边收边放），只需完成后一次性播放
