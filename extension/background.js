import { SILENT_SYNC_INTERVAL_MINUTES, runSilentSyncIfNeeded } from "./services/sync.js";

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("career-lens-silent-sync", {
    periodInMinutes: SILENT_SYNC_INTERVAL_MINUTES,
  });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("career-lens-silent-sync", {
    periodInMinutes: SILENT_SYNC_INTERVAL_MINUTES,
  });
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== "career-lens-silent-sync") return;
  void runSilentSyncIfNeeded().catch(() => {});
});
