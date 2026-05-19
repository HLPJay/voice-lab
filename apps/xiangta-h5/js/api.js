"use strict";

async function apiFetch(path, options) {
  setStatus("正在请求...", "loading");
  try {
    const response = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const body = await response.json();
    if (!response.ok || body.ok === false) {
      const message = body.message || body.errorKind || body.detail || ("HTTP " + response.status);
      setStatus("请求失败：" + message, "error");
      showToast(message);
      return null;
    }
    setStatus("已更新", "ok");
    return body;
  } catch (error) {
    setStatus("网络错误：" + error.message, "error");
    showToast("网络错误，请稍后再试");
    return null;
  }
}
