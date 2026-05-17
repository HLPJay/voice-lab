"""
Error Translator — Core 技术异常 → 产品友好文案。

前端只接收 errorKind + message，不感知技术细节。
"""
from __future__ import annotations


class XiangTaError(Exception):
    def __init__(self, kind: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.retryable = retryable

    def to_dict(self) -> dict:
        return {"ok": False, "errorKind": self.kind, "message": self.message, "retryable": self.retryable}


# ── 已知错误类型 ──────────────────────────────────────────────────────────────

class QuotaExhaustedError(XiangTaError):
    def __init__(self) -> None:
        super().__init__("quota", "今天的声音已用完，明天再来试试。", retryable=False)


class NoProviderError(XiangTaError):
    def __init__(self) -> None:
        super().__init__("no_provider", "声音服务暂时连接不上，请稍后再试。", retryable=True)


class TtsFailedError(XiangTaError):
    def __init__(self, detail: str = "") -> None:
        super().__init__("tts_failed", f"生成声音时遇到了问题，可以再试一次。{detail}", retryable=True)


class LlmFailedError(XiangTaError):
    def __init__(self) -> None:
        super().__init__("llm_failed", "整理表达时出了点问题，可以再试一次。", retryable=True)


def translate(exc: Exception) -> XiangTaError:
    """
    将 Core 抛出的技术异常映射为 XiangTaError。

    TODO(P17-A2/A3): 随着 Core 错误类型的引入，逐步完善映射规则。
    """
    if isinstance(exc, XiangTaError):
        return exc
    # 兜底：未知异常统一提示
    return XiangTaError("unknown", "出了点小问题，可以再试一次。", retryable=True)
