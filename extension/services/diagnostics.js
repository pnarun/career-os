import { CAREER_OS_API_URL, getSettings } from "../utils/storage.js";
import { checkBackendHealth, getExtensionVersion } from "./health.js";

/** Non-sensitive diagnostics for support (no cookies, tokens, or emails). */
export async function buildDiagnosticsExport() {
  const settings = await getSettings();
  const health = await checkBackendHealth();
  return {
    extensionVersion: getExtensionVersion(),
    backendUrl: CAREER_OS_API_URL,
    backendStatus: health.status,
    linkedinConnected: settings.linkedinConnected,
    lastSyncedAt: settings.lastSyncedAt || null,
    lastError: settings.lastError ? "[present]" : null,
    lastSilentSyncAt: settings.lastSilentSyncAt || null,
    exportedAt: new Date().toISOString(),
  };
}

export async function copyDiagnosticsToClipboard() {
  const payload = await buildDiagnosticsExport();
  const text = JSON.stringify(payload, null, 2);
  await navigator.clipboard.writeText(text);
  return text;
}
