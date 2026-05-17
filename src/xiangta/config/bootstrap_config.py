"""
Bootstrap 静态配置 — styles 与 limits。

styles 是固定的三种表达风格，不来自 JSON（产品定义稳定，无需外部配置）。
后续如需动态化，只需改本文件为从 styles.json 读取，调用方无需变动。

limits 是产品层的输入约束，同样固定，不依赖外部 Provider。
"""
from __future__ import annotations

STYLES: list[dict] = [
    {
        "id": "restrained",
        "label": "克制版",
        "desc": "少一点情绪外露，不给对方压力",
        "enabled": True,
    },
    {
        "id": "gentle",
        "label": "温柔版",
        "desc": "更柔和、更靠近一点",
        "enabled": True,
    },
    {
        "id": "sincere",
        "label": "真诚版",
        "desc": "认真表达，不绕弯",
        "enabled": True,
    },
]

LIMITS: dict = {
    "maxRawTextChars": 500,
    "maxTtsChars": 500,
    "maxSuggestions": 3,
}
