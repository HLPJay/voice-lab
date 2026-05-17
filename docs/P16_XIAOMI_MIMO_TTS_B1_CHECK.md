# P16-XIAOMI-MIMO-TTS-B1-CHECK：验证 Xiaomi MiMo Chat TTS 最小实现

## 1. 阶段目标

验证 P16-XIAOMI-MIMO-TTS-B1 与 B1-CHECK-FIX1 的完整实现质量，确认 Xiaomi MiMo Chat TTS adapter 已形成配置化闭环。

## 2. 检查范围

- [x] env_resolver 支持 VOICE_LAB_ENV_FILE
- [x] xiaomi_mimo 默认 disabled 行为
- [x] 临时 enabled=true capability 暴露
- [x] plugin discovery 行为
- [x] runtime 配置读取行为（api_key / base_url / endpoint / model / timeout / static_voices）

## 3. env_resolver 修复情况

**问题**：原 env_resolver 只读取 os.environ + 项目根目录 .env，不支持临时 env 文件。

**修复**：更新 `resolve_env_value()` 解析顺序：

1. `os.environ[env_name]`（最高优先级）
2. `VOICE_LAB_ENV_FILE` 指向的 env 文件
3. 项目根目录 `.env` 文件
4. 找不到返回 `None`

**关键设计**：
- `VOICE_LAB_ENV_FILE` 只存放 env 文件路径，不是 key 值
- 如果 `VOICE_LAB_ENV_FILE` 指向不存在文件，跳过（不崩溃）
- `.env` 解析不打印内容、不打印 key、不记录 key 到日志
- 缓存结构按 env file path 分开缓存（`_cached_env_files: dict[str, dict[str, str]]`）
- `clear_env_cache()` 清理所有缓存，切换 VOICE_LAB_ENV_FILE 后可重新读取

**测试覆盖**（tests/test_env_resolver.py，13 tests）：
- os.environ 优先级最高
- VOICE_LAB_ENV_FILE 临时 env 文件读取
- 项目根目录 .env fallback
- VOICE_LAB_ENV_FILE 文件不存在时不崩溃
- clear_env_cache() 后可重新读取变化后的 env 文件
- 各种 .env 格式（simple、double-quoted、single-quoted、comments、empty lines）

## 4. xiaomi_mimo 默认 disabled 的预期行为

**验证结果**：

```yaml
# config/providers.yaml
- name: "xiaomi_mimo"
  enabled: false  # 默认 disabled
```

- `list_capabilities()` 默认**不包含** xiaomi_mimo（0 个 xiaomi_mimo capability）
- `get_provider("xiaomi_mimo")` 默认抛出 `UnsupportedProvider("Provider xiaomi_mimo is not enabled")`
- **前端 Provider 下拉框默认不显示 Xiaomi MiMo 是预期行为**，因为 `enabled=false`

**这是预期行为，不是 bug。**

## 5. 临时 enabled=true 的 capability 验证

**验证方法**：使用临时 ProviderConfig 和 AdapterConfig 注入 adapter。

**验证结果**：

当 xiaomi_mimo enabled=true 时，capability 暴露：

| Capability | 值 |
|---|---|
| tts.supported | `true` |
| tts.models | `["mimo-v2.5-tts"]` |
| tts.supports_streaming | `false` |
| voice_clone.supported | `false` |
| voice_design.supported | `false` |
| provider_voices.supported | `true` |
| metadata.adapter_type | `xiaomi_mimo_chat_tts` |
| metadata.real_cost | `true` |

## 6. runtime 配置读取验证

### 6.1 api_key 读取

**验证场景**：临时 ProviderConfig 设置 `api_key_env: "TEST_MIMO_KEY"`（不是 MIMO_API_KEY）

**验证步骤**：
1. 设置 `os.environ["TEST_MIMO_KEY"] = "test_key_from_custom_env"`
2. 不设置 `MIMO_API_KEY`
3. 创建 adapter 时注入临时 provider_config
4. 调用 `_get_api_key()`
5. 验证请求 header `api-key` 等于 `test_key_from_custom_env`

**验证结果**：`adapter._get_api_key()` 返回 `"test_key_from_custom_env"`，证明 adapter 没有硬编码 `MIMO_API_KEY`。

### 6.2 base_url / endpoint 读取

**验证场景**：临时 AdapterConfig 设置：
- `default_base_url: "https://custom.adapter.url"`
- `endpoints.tts: "/custom/endpoint"`

**验证步骤**：
1. 创建 adapter 时注入临时 adapter_config
2. 调用 `_get_base_url()` 和 `_get_endpoint()`
3. 使用 fake client 调用 `render_sync()`
4. 验证请求 URL 为 `https://custom.adapter.url/custom/endpoint`

**验证结果**：
- `_get_base_url()` 返回 `"https://custom.adapter.url"`
- `_get_endpoint()` 返回 `"/custom/endpoint"`
- 请求 URL 正确拼接

### 6.3 model 读取

**验证场景**：临时 ProviderConfig 设置 `default_model: "mimo-v2.5-tts"`

**验证结果**：
- `plan.model` 优先（如果设置）
- 空时使用 `ProviderConfig.default_model`
- 再为空时使用 `AdapterConfig.default_model`
- 最后是硬编码 fallback

### 6.4 timeout 读取

**验证场景**：临时 AdapterConfig 设置 `default_timeout_seconds: 60`

**验证结果**：`adapter._get_timeout()` 返回 `60`

### 6.5 static_voices 读取

**验证场景**：临时 AdapterConfig 设置 1 个测试音色

```python
provider_voices={
    'supported': True,
    'static_voices': [
        {'voice_id': 'test_voice', 'name': 'Test Voice', 'language': 'zh', 'gender': 'female'}
    ]
}
```

**验证步骤**：
1. 创建 adapter 时注入临时 adapter_config
2. 调用 `list_voices()`
3. 验证返回 1 个音色（不是硬编码的 9 个）

**验证结果**：`list_voices()` 返回 1 个音色，voice_id 为 `"test_voice"`

## 7. plugin discovery 验证

**验证结果**：
- `xiaomi_mimo_chat_tts` adapter 通过 `config/adapters/xiaomi_mimo_chat_tts.yaml` 的 `plugin.import_path` 加载
- 不修改 `app/providers/__init__.py` 做注册
- 不修改 `app/providers/adapter_type_registry.py` 做硬编码注册
- `clear_adapter_type_registry_for_tests()` 后仍可通过配置重新发现

## 8. fake client render_sync 验证

所有 render_sync 测试使用 fake httpx client，验证：
- 请求 URL 正确
- 请求 header 包含 `api-key`（不是 `Authorization: Bearer`）
- 请求 body 格式正确
- 响应解析正确（base64 decode、WAV 保存）
- 不调用真实小米 API

## 9. 测试结果

| 测试套件 | 结果 |
|---|---|
| test_env_resolver.py | 13 passed ✅ |
| test_xiaomi_mimo_chat_tts_adapter.py | 46 passed ✅ |
| test_adapter_plugin_discovery.py | 44 passed ✅ |
| test_adapter_config_loader.py | 51 passed ✅ |
| test_provider_config_dynamic.py | 47 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |
| **核心测试总计** | **277 passed** |
| 全量非 E2E 测试 | 1557 passed, 6 skipped ✅ |

## 10. 剩余风险

**无阻塞风险。**

**非阻塞观察项**：
- 真实 API 调用未测试（需要真实 MIMO_API_KEY）
- voice design / voice clone 语义映射待 P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 分析

## 11. 下一阶段建议

### 推荐：P16-XIAOMI-MIMO-TTS-REAL-PROBE-A0

**目标**：设计小米 MiMo 真实 API 最小探测方案

**内容**：
- 真实 API 探测前置条件（MIMO_API_KEY 获取方式）
- 最小探测路径（单次 render_sync 调用）
- 验证项（音频格式、音色名称、模型名称）
- 错误处理（API key 无效、quota 超限）

**注意**：必须用户明确授权后才能执行真实 API 探测。

## 12. 明确未做

- **未调用真实小米 API**
- **未把正式 config/providers.yaml 中 xiaomi_mimo 改成 enabled=true**
- **未修改 app/providers/__init__.py 做注册**
- **未修改 app/providers/adapter_type_registry.py 做注册**
- **未实现 design_voice**
- **未实现 clone_voice**
- **未实现 streaming**
- **未实现 async task**
- **未实现 delete_voice**
- **未做 UI**
- **未改 RenderPlan schema**
- **未改 VoiceBinding / ProviderVoice / VoiceProfile schema**
- **未改 resolve_binding**
- **未改真实业务默认 Provider**
- **未调用任何真实外部 API**

## 13. B1-CHECK 通过声明

**P16-XIAOMI-MIMO-TTS-B1-CHECK 通过。**

- [x] 配置化闭环已形成
- [x] env_resolver 支持 VOICE_LAB_ENV_FILE
- [x] xiaomi_mimo 默认 disabled 行为正确
- [x] plugin discovery 工作正常
- [x] runtime 配置读取通过测试验证
- [x] 未调用真实 API
- [x] 未修改注册表源码
- [x] 未实现 design_voice / clone_voice / streaming

**下一步**：进入 P16-XIAOMI-MIMO-TTS-REAL-PROBE-A0（真实 API 探测方案设计）
