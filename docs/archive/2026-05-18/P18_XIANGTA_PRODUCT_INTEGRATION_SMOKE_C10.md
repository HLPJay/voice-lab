# P18-XIANGTA-PRODUCT-INTEGRATION-SMOKE-C10

## 实现内容

- 新增 `tests/xiangta/test_product_integration_smoke.py`，30 个静态/集成 smoke 测试
- 覆盖 bootstrap → suggestions → tts/tasks → letters → history API 闭环
- 覆盖无 audioUrl 也可保存文字信笺（no-audio mock + real failed task）
- 覆盖 H5 screen-based mobile product flow contract
- 覆盖 H5 formal/dev mode separation
- 覆盖 mobile-first CSS contract
- 覆盖 forbidden fields 不泄露检查
- 更新 NEXT_TASKS.md：C10 ✅，进入 C11

## 测试覆盖

- TestProductApiFlow: 5 tests (bootstrap, suggestions, tts task with/without audio, letters save)
- TestNoForbiddenFields: 4 tests (bootstrap, suggestions, letters POST/GET)
- TestH5ScreenFlow: 4 tests (screens, viewport, showScreen, state.screen)
- TestH5TtsTaskFlow: 3 tests (generateTtsTask endpoint, pollTtsTask, tts only in dev)
- TestH5NoAudioSave: 4 tests (revealSaveLetterSection, renderTtsTask calls reveal, tts-hint, null audio)
- TestFormalDevMode: 4 tests (devPanel hidden, coreProfileSelect inside devPanel, getAppMode, loadCoreProfiles guard)
- TestMobileCss: 6 tests (screen system, hero, choice-chip, bottom-actions, toast, CSS vars)

## 未实现项

- 不做真实浏览器自动化
- 不做截图/视觉回归
- 不接真实 TTS Provider
- 不接真实 LLM Provider
- task API 当前仍是同步执行 + 内存状态

## Follow-up cleanup

- test_h5_product_flow.py 当前测试数量偏多，后续 cleanup 可压缩
- toast 重复触发自动隐藏计时可后续优化

## 下一步

P18-XIANGTA-MERGE-READINESS-C11
