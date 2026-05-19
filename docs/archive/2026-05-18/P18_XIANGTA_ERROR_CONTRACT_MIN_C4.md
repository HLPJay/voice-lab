# P18-XIANGTA-ERROR-CONTRACT-MIN-C4

## 实现内容

### 新增 `src/xiangta/api/error_contract.py`
- `error_body(error_kind, message, retryable)` → 返回 flat dict
- `error_response(status_code, error_kind, message, retryable)` → 返回 JSONResponse

### Admin gate 改为 flat JSONResponse
- 移除 `HTTPException` + `detail` wrapper 模式
- 新增 `admin_guard_response(token)` → `JSONResponse | None`
- 所有 `/admin/*` 路由改为 `Header(x_xiangta_admin_token)` + 显式 guard 调用
- 不再使用 `dependencies=[Depends(require_admin)]`

### 统一错误返回
- `_write_error_response()` 复用 `error_response()`
- `suggestions()` ValueError 路径复用 `error_response()`
- `tts()` XiangTaError 路径复用 `error_response()`

### 错误响应形状
```json
{"ok": false, "errorKind": "...", "message": "...", "retryable": false}
```

## 测试覆盖

`tests/xiangta/test_error_contract.py` (12 tests):
1. `error_body()` 返回 ok=false
2. `error_body()` 返回 errorKind
3. `error_body()` 返回 message
4. `error_body()` retryable 默认为 false
5. `error_body()` retryable 可设置为 true
6. `error_response()` 返回指定 status_code
7. `error_response()` body 为 flat shape，无 detail
8. Admin disabled 返回 403
9. Admin disabled 响应为 flat shape，无 detail
10. Admin wrong token 返回 403，响应不含真实 token
11. Suggestions ValueError 返回 flat shape，无 detail
12. TTS disabled preset 返回 flat shape，无 detail

## 未实现项

- 完整 C6 nested error schema
- requestId / taskId / traceId
- 全局 exception handler / middleware
- H5 normalizeError
- Storage / TTS task / LLM

## 下一步

P18-XIANGTA-H5-DEV-FORMAL-MODE-C5