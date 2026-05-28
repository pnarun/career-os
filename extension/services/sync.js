import { resyncLinkedInSession } from "./api.js";
import { checkLinkedInLogin, cookiesFingerprint } from "./linkedin.js";
import {
  getSettings,
  markSilentSync,
  setConnectionState,
} from "../utils/storage.js";

const SILENT_SYNC_INTERVAL_MINUTES = 300; // 5 hours
const MIN_SILENT_SYNC_GAP_MS = SILENT_SYNC_INTERVAL_MINUTES * 60 * 1000;

export async function runSilentSyncIfNeeded() {
  const settings = await getSettings();
  if (!settings.linkedinConnected || !settings.syncToken) {
    return { skipped: true, reason: "not_connected" };
  }

  const probe = await checkLinkedInLogin();
  if (!probe.authenticated) {
    await setConnectionState({
      linkedinConnected: false,
      lastError: "LinkedIn login required. Open linkedin.com and sign in.",
    });
    return { skipped: true, reason: "not_logged_in" };
  }

  const lastSilent = settings.lastSilentSyncAt
    ? new Date(settings.lastSilentSyncAt).getTime()
    : 0;
  const stale = !lastSilent || Date.now() - lastSilent >= MIN_SILENT_SYNC_GAP_MS;
  const cookiesChanged = probe.fingerprint !== settings.cookieFingerprint;

  if (!stale && !cookiesChanged) {
    return { skipped: true, reason: "fresh" };
  }

  await resyncLinkedInSession({
    cookies: probe.cookies,
    syncToken: settings.syncToken,
  });

  const syncedAt = new Date().toISOString();
  await setConnectionState({
    linkedinConnected: true,
    lastSyncedAt: syncedAt,
    lastError: "",
    syncToken: settings.syncToken,
    cookieFingerprint: probe.fingerprint,
  });
  await markSilentSync(syncedAt);

  return { skipped: false, syncedAt };
}

export { SILENT_SYNC_INTERVAL_MINUTES };
