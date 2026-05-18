# XiangTa Testing Guide

## Scoped Regression

默认只跑 XiangTa scoped tests，不默认跑全量 `pytest`：

```bash
python -m pytest tests/xiangta -q --basetemp .pytest-tmp
```

## Single File Entry

```bash
python -m pytest tests/xiangta/test_admin_gate.py -q
python -m pytest tests/xiangta/test_admin_config_api.py -q
```

## Windows Temp Note

Windows 本机 Temp 目录权限异常时，统一追加：

```bash
--basetemp .pytest-tmp
```

## Naming Rule

- XiangTa 测试文件统一放在 `tests/xiangta/`
- 文件命名使用 `test_<feature>.py`

## Test Budget

- 小型 API / service 任务最多新增 1 个测试文件
- 通常不超过 6 到 10 个测试函数
- 优先使用 `pytest.mark.parametrize`
- 不要为每个字段单独写测试函数
- 优先复用现有 `tests/xiangta` 测试入口
