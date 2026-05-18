"""
XiangTa Runtime Configuration — 只读取运行时必需的 XiangTa 级别变量。
不读取任何真实 Provider API key。
不引入 Core 内部模块。
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class XiangTaRuntimeConfig:
    """只读运行时配置 — 不包含任何真实 Provider API key。"""
    core_base_url: str | None
    core_timeout_secs: float = 20.0


def load_runtime_config() -> XiangTaRuntimeConfig:
    """
    读取 XiangTa 运行时配置。
    只允许读取 XIANGTA_CORE_BASE_URL / XIANGTA_CORE_TIMEOUT_SECS。
    不读取任何真实 Provider API key。
    """
    core_base_url = os.environ.get("XIANGTA_CORE_BASE_URL") or None
    core_timeout_str = os.environ.get("XIANGTA_CORE_TIMEOUT_SECS", "")
    try:
        core_timeout_secs = float(core_timeout_str) if core_timeout_str else 20.0
    except ValueError:
        core_timeout_secs = 20.0

    return XiangTaRuntimeConfig(
        core_base_url=core_base_url,
        core_timeout_secs=core_timeout_secs,
    )