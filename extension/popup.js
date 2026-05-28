import { CAREER_OS_PRIVACY_URL } from "./config.js";
import {
  resyncLinkedInSession,
  syncLinkedInSessionWithCode,
} from "./services/api.js";
import { copyDiagnosticsToClipboard } from "./services/diagnostics.js";
import {
  checkBackendHealth,
  getExtensionVersion,
  isExtensionOutdated,
} from "./services/health.js";
import { checkLinkedInLogin, openLinkedInLogin } from "./services/linkedin.js";
import {
  clearConnectionState,
  clearLastError,
  getSettings,
  setConnectionState,
} from "./utils/storage.js";

const views = {
  checking: document.getElementById("viewChecking"),
  notLoggedIn: document.getElementById("viewNotLoggedIn"),
  pairing: document.getElementById("viewPairing"),
  connecting: document.getElementById("viewConnecting"),
  connected: document.getElementById("viewConnected"),
};

const pairingCodeInput = document.getElementById("pairingCode");
const errorMessage = document.getElementById("errorMessage");
const successMessage = document.getElementById("successMessage");
const connectedSynced = document.getElementById("connectedSynced");
const healthBanner = document.getElementById("healthBanner");
const extensionVersionEl = document.getElementById("extensionVersion");
const privacyLink = document.getElementById("privacyLink");

let currentView = "checking";

if (extensionVersionEl) {
  extensionVersionEl.textContent = `v${getExtensionVersion()}`;
}
if (privacyLink) {
  privacyLink.href = CAREER_OS_PRIVACY_URL;
}

function showView(name) {
  currentView = name;
  for (const [key, el] of Object.entries(views)) {
    el.classList.toggle("hidden", key !== name);
  }
}

function showError(message) {
  errorMessage.textContent = message || "";
  errorMessage.classList.toggle("hidden", !message);
  if (message) successMessage.classList.add("hidden");
}

function showSuccess(message) {
  successMessage.textContent = message || "";
  successMessage.classList.toggle("hidden", !message);
  if (message) errorMessage.classList.add("hidden");
}

function clearMessages() {
  showError("");
  showSuccess("");
}

function setHealthBanner(message, level = "info") {
  if (!healthBanner) return;
  if (!message) {
    healthBanner.classList.add("hidden");
    healthBanner.textContent = "";
    healthBanner.classList.remove("warn", "err");
    return;
  }
  healthBanner.textContent = message;
  healthBanner.classList.remove("hidden", "warn", "err");
  if (level === "warn") healthBanner.classList.add("warn");
  if (level === "err") healthBanner.classList.add("err");
}

function formatWhen(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function resolveView(settings, probe) {
  if (!probe.authenticated) return "notLoggedIn";
  if (settings.linkedinConnected && settings.syncToken) return "connected";
  if (currentView === "connecting") return "connecting";
  return "pairing";
}

async function runHealthChecks(settings) {
  const health = await checkBackendHealth();
  if (!health.ok) {
    setHealthBanner(
      "Career OS backend is unreachable. Check your connection and try again.",
      "err"
    );
    return;
  }
  if (isExtensionOutdated(health.extensionMinVersion)) {
    setHealthBanner(
      `Update Career Lens to v${health.extensionMinVersion} or newer (you have v${getExtensionVersion()}).`,
      "warn"
    );
    return;
  }
  if (settings.lastError) {
    setHealthBanner(`Last sync issue: ${settings.lastError}`, "warn");
    return;
  }
  if (!settings.linkedinConnected && health.ok) {
    setHealthBanner("LinkedIn not connected to Career OS yet.", "info");
    return;
  }
  setHealthBanner("");
}

async function refreshUi() {
  showView("checking");
  clearMessages();
  const settings = await getSettings();
  const probe = await checkLinkedInLogin();
  const view = resolveView(settings, probe);
  showView(view);
  await runHealthChecks(settings);

  if (view === "connected") {
    connectedSynced.textContent = `Last synced ${formatWhen(settings.lastSyncedAt)}`;
    if (settings.lastError) {
      await clearLastError();
    }
  } else if (view === "pairing") {
    pairingCodeInput.focus();
    if (settings.lastError) {
      await clearLastError();
    }
  }

  if (settings.lastError && view === "notLoggedIn") {
    showError(settings.lastError);
  }
}

async function handleConnectWithCode() {
  const code = String(pairingCodeInput.value || "").replace(/\D/g, "");
  if (!/^\d{6}$/.test(code)) {
    showError("Enter the 6-digit code from Career OS.");
    return;
  }

  showView("connecting");
  clearMessages();
  try {
    const probe = await checkLinkedInLogin();
    if (!probe.authenticated) {
      throw new Error("Please log into LinkedIn in this browser first.");
    }
    const result = await syncLinkedInSessionWithCode({
      cookies: probe.cookies,
      pairingCode: code,
    });
    const syncedAt = result.syncedAt || new Date().toISOString();
    await setConnectionState({
      linkedinConnected: true,
      lastSyncedAt: syncedAt,
      lastError: "",
      syncToken: result.syncToken || "",
      cookieFingerprint: probe.fingerprint,
    });
    pairingCodeInput.value = "";
    showSuccess("LinkedIn session saved successfully.");
    showView("connected");
    const settings = await getSettings();
    connectedSynced.textContent = `Last synced ${formatWhen(settings.lastSyncedAt)}`;
    setHealthBanner("");
  } catch (err) {
    showView("pairing");
    showError(err?.message || "Connection failed. Check your code and try again.");
  }
}

async function handleResync() {
  clearMessages();
  showView("connecting");
  try {
    const probe = await checkLinkedInLogin();
    if (!probe.authenticated) {
      throw new Error("Log into LinkedIn first.");
    }
    const settings = await getSettings();
    const result = await resyncLinkedInSession({
      cookies: probe.cookies,
      syncToken: settings.syncToken,
    });
    const syncedAt = result.syncedAt || new Date().toISOString();
    await setConnectionState({
      linkedinConnected: true,
      lastSyncedAt: syncedAt,
      lastError: "",
      syncToken: settings.syncToken,
      cookieFingerprint: probe.fingerprint,
    });
    showSuccess("Session refreshed.");
    showView("connected");
    connectedSynced.textContent = `Last synced ${formatWhen(syncedAt)}`;
    setHealthBanner("");
  } catch (err) {
    showView("connected");
    showError(err?.message || "Resync failed.");
    setHealthBanner(err?.message || "Resync failed.", "warn");
  }
}

async function handleDisconnect() {
  const ok = window.confirm(
    "Disconnect LinkedIn from Career OS? Generate a new pairing code in Career OS to reconnect."
  );
  if (!ok) return;
  await clearConnectionState();
  pairingCodeInput.value = "";
  clearMessages();
  showView("pairing");
  pairingCodeInput.focus();
}

document.getElementById("connectBtn").addEventListener("click", handleConnectWithCode);
document.getElementById("resyncBtn").addEventListener("click", handleResync);
document.getElementById("disconnectBtn").addEventListener("click", handleDisconnect);
document.getElementById("openLinkedInBtn").addEventListener("click", () => {
  void openLinkedInLogin();
});
document.getElementById("copyDiagnosticsBtn")?.addEventListener("click", async () => {
  try {
    await copyDiagnosticsToClipboard();
    showSuccess("Diagnostics copied to clipboard.");
  } catch {
    showError("Could not copy diagnostics.");
  }
});

pairingCodeInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") void handleConnectWithCode();
});
pairingCodeInput.addEventListener("input", () => {
  if (!errorMessage.classList.contains("hidden")) {
    showError("");
  }
});

void refreshUi();
