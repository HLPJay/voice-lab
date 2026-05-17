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


class InvalidInputError(XiangTaError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_input", message, retryable=False)


class TextTooLongError(XiangTaError):
    def __init__(self, max_chars: int) -> None:
        super().__init__(
            "text_too_long",
            f"文案超过 {max_chars} 字，请缩短后再试。",
            retryable=False,
        )


class PresetNotFoundError(XiangTaError):
    def __init__(self, detail: str = "") -> None:
        super().__init__("preset_not_found", detail or "声线或语气配置不存在。", retryable=False)


class TtsFailedError(XiangTaError):
    def __init__(self, detail: str = "") -> None:
        super().__init__("tts_failed", f"生成声音时遇到了问题，可以再试一次。{detail}", retryable=True)


class LlmFailedError(XiangTaError):
    def __init__(self) -> None:
        super().__init__("llm_failed", "整理表达时出了点问题，可以再试一次。", retryable=True)


def translate(exc: Exception) -> XiangTaError:
    """将 Core 抛出的技术异常映射为 XiangTaError。"""
    from src.xiangta.services.preset_mapper import PresetMappingError  # local import to avoid cycle

    if isinstance(exc, XiangTaError):
        return exc
    if isinstance(exc, PresetMappingError):
        return PresetNotFoundError(str(exc))
    return XiangTaError("unknown", "出了点小问题，可以再试一次。", retryable=True)
