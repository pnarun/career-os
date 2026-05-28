const LINKEDIN_URL = "https://www.linkedin.com/feed/";

const LINKEDIN_COOKIE_URLS = [
  "https://www.linkedin.com/",
  "https://www.linkedin.com/feed/",
  "https://linkedin.com/",
];

const LINKEDIN_COOKIE_DOMAINS = [
  ".linkedin.com",
  "linkedin.com",
  "www.linkedin.com",
  ".www.linkedin.com",
];

function cookieKey(cookie) {
  return `${cookie.name}|${cookie.domain}|${cookie.path}`;
}

function isLinkedInDomain(domain) {
  if (!domain) return false;
  const d = domain.toLowerCase().replace(/^\./, "");
  return d === "linkedin.com" || d.endsWith(".linkedin.com");
}

export async function getLinkedInCookies() {
  const seen = new Map();

  const addBatch = (batch) => {
    if (!Array.isArray(batch)) return;
    for (const cookie of batch) {
      if (!cookie?.name || !isLinkedInDomain(cookie.domain)) continue;
      const key = cookieKey(cookie);
      if (!seen.has(key)) seen.set(key, cookie);
    }
  };

  for (const url of LINKEDIN_COOKIE_URLS) {
    try {
      addBatch(await chrome.cookies.getAll({ url }));
    } catch {
      /* ignore per-origin failures */
    }
  }

  for (const domain of LINKEDIN_COOKIE_DOMAINS) {
    try {
      addBatch(await chrome.cookies.getAll({ domain }));
    } catch {
      /* ignore per-domain failures */
    }
  }

  return Array.from(seen.values()).map((cookie) => ({
    name: cookie.name,
    value: cookie.value,
    domain: cookie.domain,
    path: cookie.path,
    expires: cookie.expirationDate ?? -1,
    httpOnly: Boolean(cookie.httpOnly),
    secure: Boolean(cookie.secure),
    sameSite: cookie.sameSite || "unspecified",
  }));
}

function findCookieByName(cookies, name) {
  const target = name.toLowerCase();
  return cookies.find((c) => (c.name || "").toLowerCase() === target);
}

function hasNonEmptyValue(cookie) {
  return Boolean(cookie?.value && String(cookie.value).length > 0);
}

export function evaluateLinkedInAuth(cookies) {
  const liAt = findCookieByName(cookies, "li_at");
  return {
    authenticated: hasNonEmptyValue(liAt),
  };
}

/** Stable fingerprint for change detection (no cookie values). */
export function cookiesFingerprint(cookies) {
  const parts = cookies
    .map((c) => `${c.name}:${c.domain}:${c.expires}`)
    .sort();
  return parts.join("|");
}

export async function checkLinkedInLogin() {
  const cookies = await getLinkedInCookies();
  const auth = evaluateLinkedInAuth(cookies);
  return {
    loggedIn: auth.authenticated,
    authenticated: auth.authenticated,
    cookies,
    fingerprint: cookiesFingerprint(cookies),
  };
}

export async function openLinkedInLogin() {
  await chrome.tabs.create({ url: LINKEDIN_URL });
}
