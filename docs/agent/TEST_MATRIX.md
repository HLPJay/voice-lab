# Frontend E2E Test Matrix

**25 个 E2E**（tests/e2e/test_frontend_capabilities.py）

## 模块加载

| 测试 | 覆盖 |
|---|---|
| `test_voice_clone_module_is_loaded_and_exports_available` | voice_clone.js 加载 + 4 个 window 函数 |
| `test_voice_import_module_is_loaded_and_exports_available` | voice_import.js 加载 + window.handleImportRemoteVoice |
| `test_batch_longtext_module_is_loaded_and_submit_validation_works` | batch_longtext.js 加载 + handleBatchLongtextSubmit |
| `test_batch_script_module_is_loaded_and_submit_validation_still_works` | batch_script.js 加载 + handleBatchScriptSubmit |

## Voice Clone

| 测试 | 覆盖 |
|---|---|
| `test_voice_clone_error_insufficient_balance` | clone 余额不足错误展示 |
| `test_voice_clone_mock_submit_success` | clone mock 提交成功 + audio player + quick bind/preview 面板 |

## Voice Design

| 测试 | 覆盖 |
|---|---|
| `test_voice_design_mock_success` | design mock 提交成功 |

## Voice Import

| 测试 | 覆盖 |
|---|---|
| `test_voice_import_clone_mock_success` | clone import 成功 + audio + quick bind 面板 |

## Batch Longtext

| 测试 | 覆盖 |
|---|---|
| `test_batch_longtext_mock_submit_success_starts_progress` | longtext 批量提交 + 进度面板 + 按钮恢复 |

## Batch Script

| 测试 | 覆盖 |
|---|---|
| `test_batch_script_mock_submit_success_starts_progress` | 剧本批量提交 + 进度面板 + 按钮恢复 |

## Audition Records

| 测试 | 覆盖 |
|---|---|
| `test_audition_records_render` | audition records 渲染 |
| `test_audition_records_delete` | audition records 删除 |

## History

| 测试 | 覆盖 |
|---|---|
| `test_history_tab_loads` | history tab 加载 |
| `test_history_delete_job` | history 任务删除 |

## Provider Capability

| 测试 | 覆盖 |
|---|---|
| `test_provider_capability_loaded` | Provider capability 加载 / 切换 / 失败降级 |

## Admin

| 测试 | 覆盖 |
|---|---|
| `test_admin_page_matrix` | Admin 页面和矩阵 |

## 覆盖链路汇总

```
Provider capability 加载/切换/降级
History Tab 加载/刷新/删除
Audition Records 渲染/删除
Batch Longtext mock 提交/进度/按钮恢复
Batch Script mock 提交/进度/按钮恢复
Voice Clone module + 4 exports
Voice Clone insufficient balance error
Voice Clone mock success + audio + quick bind/preview
Voice Design mock success
Voice Import module + handleImportRemoteVoice
Voice Import clone mock success + audio + quick bind
Admin page matrix
```

## targeted E2E 命令

```bash
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "clone"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "import"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "design"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "script"
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "batch_longtext"
```
