/** Production Career OS API — not shown in the extension UI. */
export const CAREER_OS_API_URL = "https://career-os-pd9g.onrender.com";

export async function getSettings() {
  const stored = await chrome.storage.local.get([
    "linkedinConnected",
    "lastSyncedAt",
    "lastError",
    "syncToken",
    "cookieFingerprint",
    "lastSilentSyncAt",
  ]);
  return {
    linkedinConnected: Boolean(stored.linkedinConnected),
    lastSyncedAt: stored.lastSyncedAt || "",
    lastError: stored.lastError || "",
    syncToken: stored.syncToken || "",
    cookieFingerprint: stored.cookieFingerprint || "",
    lastSilentSyncAt: stored.lastSilentSyncAt || "",
  };
}

export async function setConnectionState({
  linkedinConnected,
  lastSyncedAt = "",
  lastError = "",
  syncToken,
  cookieFingerprint,
}) {
  const payload = {
    linkedinConnected: Boolean(linkedinConnected),
    lastSyncedAt: lastSyncedAt || "",
    lastError: lastError || "",
  };
  if (typeof syncToken === "string") payload.syncToken = syncToken;
  if (typeof cookieFingerprint === "string") payload.cookieFingerprint = cookieFingerprint;
  await chrome.storage.local.set(payload);
}

export async function clearConnectionState() {
  await chrome.storage.local.set({
    linkedinConnected: false,
    lastSyncedAt: "",
    lastError: "",
    syncToken: "",
    cookieFingerprint: "",
    lastSilentSyncAt: "",
  });
}

export async function markSilentSync(iso) {
  await chrome.storage.local.set({
    lastSilentSyncAt: iso || new Date().toISOString(),
  });
}

export async function clearLastError() {
  await chrome.storage.local.set({ lastError: "" });
}
