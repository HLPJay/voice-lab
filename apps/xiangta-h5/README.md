# apps/xiangta-h5 — 想Ta了 H5 静态前端

## 定位

想Ta了产品主流程最小 H5 静态页面（B7-1 MVP），无需构建步骤，无外部依赖。

## 主流程

```
1. 打开页面 → 自动加载 bootstrap 配置（recipient / scene / voicePreset / tone）
2. 选择参数，填写原始心情（rawText）
3. 点击"生成文案建议" → POST /api/xiangta/suggestions → 展示 3 条建议
4. 点击选择一条建议 → 自动填入最终文案
5. 点击"生成语音" → POST /api/xiangta/tts → 展示 taskId / status / contract
6. 点击"保存信笺" → POST /api/xiangta/letters
7. 点击"刷新历史" → GET /api/xiangta/letters → 展示最近历史
```

## 本地预览

```bash
cd apps/xiangta-h5
python -m http.server 5173
# 浏览器打开 http://localhost:5173
```

> 注意：直接用静态服务器打开时，浏览器会遇到 CORS 限制。
> 需要后端在同一域名下，或通过反向代理将 `/api/xiangta/*` 转发到后端。
>
> 推荐方式：在项目根目录启动后端（FastAPI），并在 FastAPI 中挂载本目录
> 或使用 Nginx/Caddy 代理。

## 文件说明

| 文件         | 说明 |
|---|---|
| `index.html` | 单页 H5，包含所有 UI 区域 |
| `styles.css` | 移动端优先样式，无外部依赖 |
| `app.js`     | 纯 JS，调用 `/api/xiangta/*` 接口 |

## 约束

- 不含 npm / package.json / 构建工具
- 不含真实 API key / provider 参数
- 不含外部 CDN 引用
- TTS 当前为 dry-run 合约（不生成真实音频）
