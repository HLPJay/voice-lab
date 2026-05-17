# tests/xiangta — 想Ta了产品层测试

## 测试策略

- **单元测试**：preset_mapper、error_translator、letter_service（纯逻辑，无外部依赖）
- **集成测试（Mock）**：copywriting_service、tts_orchestrator（mock voice_lab_gateway）
- **E2E（Mock API）**：路由层 + 前端，不调用真实 MiniMax

## 命名规范

```
tests/xiangta/
├── unit/
│   ├── test_preset_mapper.py
│   ├── test_error_translator.py
│   └── test_letter_service.py
├── integration/
│   ├── test_copywriting_service.py   — mock gateway
│   └── test_tts_orchestrator.py      — mock gateway
└── e2e/
    └── test_xiangta_routes.py        — mock API E2E
```

## 运行命令（待实现后使用）

```bash
# 单元测试
python -m pytest tests/xiangta/unit/ -q

# 集成测试（mock）
python -m pytest tests/xiangta/integration/ -q

# E2E（mock，不调用真实 MiniMax）
python -m pytest tests/xiangta/e2e/ -q
```

## P17-A0 状态

本阶段只建目录和 README，不新增测试文件。
测试随各功能阶段（A1/A2/A3）同步编写。
