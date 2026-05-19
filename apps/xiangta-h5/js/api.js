"use strict";

async function apiFetch(path, options, requestOptions) {
  const extra = requestOptions || {};
  const timeoutMs = Number(extra.timeoutMs || 0);
  const controller = timeoutMs > 0 && typeof AbortController !== "undefined"
    ? new AbortController()
    : null;
  let timer = null;

  apiFetch.lastErrorKind = null;
  apiFetch.lastErrorMessage = "";
  setStatus("正在请求...", "loading");

  try {
    if (controller && typeof window !== "undefined" && window.setTimeout) {
      timer = window.setTimeout(() => controller.abort(), timeoutMs);
    }

    const response = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
      signal: controller ? controller.signal : undefined,
    });

    if (timer && typeof window !== "undefined" && window.clearTimeout) {
      window.clearTimeout(timer);
      timer = null;
    }

    const body = await response.json();
    if (!response.ok || body.ok === false) {
      const message = body.message || body.errorKind || body.detail || ("HTTP " + response.status);
      apiFetch.lastErrorKind = "http";
      apiFetch.lastErrorMessage = message;
      setStatus("请求失败: " + message, "error");
      showToast(message);
      return null;
    }

    setStatus("已更新", "ok");
    return body;
  } catch (error) {
    if (timer && typeof window !== "undefined" && window.clearTimeout) {
      window.clearTimeout(timer);
      timer = null;
    }

    if (error && error.name === "AbortError") {
      const timeoutMessage = extra.timeoutMessage || "请求超时，请稍后再试";
      apiFetch.lastErrorKind = "timeout";
      apiFetch.lastErrorMessage = timeoutMessage;
      setStatus(timeoutMessage, "warn");
      showToast(timeoutMessage);
      return null;
    }

    apiFetch.lastErrorKind = "network";
    apiFetch.lastErrorMessage = (error && error.message) || "";
    setStatus("网络错误: " + ((error && error.message) || "unknown"), "error");
    showToast("网络错误，请稍后再试");
    return null;
  }
}
