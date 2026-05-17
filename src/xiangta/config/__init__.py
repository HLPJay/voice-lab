"""XiangTa 配置层 — 负责产品配置模型与配置读取。"""

from src.xiangta.config.product_config_models import (
    ProductLimits,
    ProductVoiceMapping,
    PublicVoicePreset,
    TonePreset,
)
from src.xiangta.config.product_config_repository import ProductConfigRepository

__all__ = [
    "ProductConfigRepository",
    "ProductVoiceMapping",
    "PublicVoicePreset",
    "TonePreset",
    "ProductLimits",
]
