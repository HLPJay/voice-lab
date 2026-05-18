# P18-XIANGTA-ADMIN-GATE-C3

## 实现内容

- 为 XiangTa Admin API 增加最小 token gate。
- 支持 `XIANGTA_ADMIN_ENABLED` 和 `XIANGTA_ADMIN_TOKEN`。
- 非 Admin API 不受影响。

## 测试覆盖

- 新增 `tests/xiangta/test_admin_gate.py`。
- 更新 `tests/xiangta/test_admin_config_api.py`，显式带 Admin env 和 header。
- 记录 XiangTa scoped regression 入口到 `docs/agent/TESTING_GUIDE.md`。

## 未实现项

- 未实现用户系统、JWT、RBAC、Admin UI。
- 未修改 Core、H5、真实配置 JSON、Provider 配置。

## 下一步

`P18-XIANGTA-ERROR-CONTRACT-MIN-C4`
