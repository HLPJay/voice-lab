# P18-XIANGTA-STORAGE-FOUNDATION-C6-FIX2

## 修复内容

- 测试文件语法错误（无，实际已在上次 rewrite 中修正）
- 测试数量从 11 减至 10：合并 `test_default_path_creates_data_dir_and_file` 和 `test_cross_instance_persistence` 为 `test_default_path_and_cross_instance`
- `TestResolveSqlitePath` 合并为单参数化测试（3 cases: None, "", ":memory:"）
- 更新 docstring 覆盖项

## 未修改

- 未修改 API / storage / runtime_config / H5 / Core

## 下一步

P18-XIANGTA-TTS-TASK-MVP-C7
