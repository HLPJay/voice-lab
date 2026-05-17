"""
想Ta了 (XiangTa) — 情绪表达产品服务层

架构：XiangTa Mobile → XiangTa Product Server → Voice Lab Core（via voice_lab_gateway）

本包不直接导入 src.voice_lab.*，所有 Core 调用通过 services.voice_lab_gateway 代理。
"""
