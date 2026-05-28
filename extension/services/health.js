import { CAREER_OS_API_URL } from "../utils/storage.js";

function apiBase() {
  return CAREER_OS_API_URL.replace(/\/$/, "");
}

export function getExtensionVersion() {
  try {
    return chrome.runtime.getManifest().version || "unknown";
  } catch {
    return "unknown";
  }
}

/** Ping Career OS API; returns { ok, status, detail }. */
export async function checkBackendHealth() {
  const base = apiBase();
  try {
    const response = await fetch(`${base}/health?detail=1`, {
      method: "GET",
      cache: "no-store",
    });
    if (!response.ok) {
      return { ok: false, status: "unreachable", httpStatus: response.status };
    }
    const body = await response.json();
    const degraded = body.status && body.status !== "ok";
    return {
      ok: !degraded,
      status: degraded ? "degraded" : "ok",
      extensionMinVersion: body.extension_min_version || "",
    };
  } catch {
    return { ok: false, status: "unreachable" };
  }
}

export function isExtensionOutdated(minVersion) {
  const min = String(minVersion || "").trim();
  if (!min) return false;
  const current = getExtensionVersion();
  if (!current || current === "unknown") return false;
  const parse = (v) =>
    String(v)
      .split(/[.-]/)
      .map((n) => parseInt(n, 10) || 0);
  const a = parse(current);
  const b = parse(min);
  const len = Math.max(a.length, b.length);
  for (let i = 0; i < len; i += 1) {
    const x = a[i] || 0;
    const y = b[i] || 0;
    if (x < y) return true;
    if (x > y) return false;
  }
  return false;
}
