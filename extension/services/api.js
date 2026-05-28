import { CAREER_OS_API_URL, getSettings } from "../utils/storage.js";

function apiBase() {
  return CAREER_OS_API_URL.replace(/\/$/, "");
}

function parseError(body, status) {
  if (status === 404) {
    return "That pairing code expired or wasn't found. Generate a fresh code in Career OS and try again.";
  }
  if (status === 401 || status === 403) {
    return "Your Career OS login may have changed. Generate a new pairing code and connect again.";
  }
  if (status === 426) {
    return "Please update Career Lens to the latest beta version, then try again.";
  }
  const raw = body?.detail?.message || body?.detail || body?.message || "";
  const text = String(raw).toLowerCase();
  if (text.includes("timeout") || text.includes("timed out")) {
    return "Career OS is taking longer than expected. Check your connection and try again.";
  }
  if (text) return String(raw);
  return "Something went wrong. Try again in a moment.";
}

export async function syncLinkedInSessionWithCode({ cookies, pairingCode }) {
  const base = apiBase();
  if (!Array.isArray(cookies) || cookies.length === 0) {
    throw new Error("No LinkedIn session cookies found.");
  }
  if (!/^\d{6}$/.test(String(pairingCode || "").trim())) {
    throw new Error("Pairing code must be 6 digits.");
  }

  const response = await fetch(`${base}/automation/linkedin/connect-with-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      pairingCode: String(pairingCode).trim(),
      cookies,
      userAgent: navigator.userAgent,
      extensionVersion: chrome?.runtime?.getManifest?.()?.version || "unknown",
    }),
  });

  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }

  if (!response.ok) {
    throw new Error(parseError(body, response.status));
  }

  return body;
}

export async function resyncLinkedInSession({ cookies, syncToken }) {
  const settings = await getSettings();
  const base = apiBase();
  const token = (syncToken || settings.syncToken || "").trim();
  if (!token) throw new Error("No sync token. Reconnect with a pairing code.");
  if (!Array.isArray(cookies) || cookies.length === 0) {
    throw new Error("No LinkedIn cookies to sync.");
  }

  const response = await fetch(`${base}/automation/linkedin/resync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      syncToken: token,
      cookies,
      userAgent: navigator.userAgent,
      extensionVersion: chrome?.runtime?.getManifest?.()?.version || "unknown",
    }),
  });

  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }

  if (!response.ok) {
    throw new Error(parseError(body, response.status));
  }

  return body;
}
