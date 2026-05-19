# P18-XIANGTA-H5-PRODUCT-FLOW-C9-FIX1

## 修复内容

- 修复无 audioUrl 时无法保存信笺的问题
- failed / no audio task 也允许保存文字信笺
- 保留 audioUrl 存在时的 audio player
- 保存信笺允许 audioUrl/durationSecs 为 null
- `revealSaveLetterSection()` 函数提取，failed 分支不再阻断保存入口
- 添加 `.tts-hint` 样式提示"语音暂未生成，可先保存文字信笺"

## 未修改

- 未修改 src/**
- 未修改 Core / runtime / backend API
- 未接真实 TTS Provider

## 下一步

P18-XIANGTA-PRODUCT-INTEGRATION-SMOKE-C10
