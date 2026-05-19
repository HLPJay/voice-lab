# P18-XIANGTA-COPYWRITING-LLM-MVP-C8-FIX1

## 修复内容

- 去掉 CopywritingService 内的模板双源，模板统一由 TemplateCopywritingGateway 提供，CopywritingService 只做 orchestration（validation / gateway call / fallback / to_dict）
- /suggestions 增加 XiangTaError flat error contract（LlmFailedError / 其他 XiangTaError → 400 flat error）
- test_copywriting_gateway.py 压缩到 7 个测试函数（12 个参数化 case），<=10 上限
- 保持不接真实 LLM provider

## 未修改

- 未修改 runtime_config.py / product_service.py / schemas.py
- 未修改 Core / H5 / storage / TTS
- 未实现真实 MiniMax/OpenAI/DeepSeek provider

## 下一步

P18-XIANGTA-H5-PRODUCT-FLOW-C9
