import type { AppPage } from "@/components/layout/Sidebar"

const STORAGE_KEY = "career-os-active-page"

const VALID_PAGES: AppPage[] = [
  "dashboard",
  "resume-hub",
  "jobs-hub",
  "career-hub",
  "insights-hub",
  "operations-hub",
  "settings",
  "profile",
]

function isValidPage(value: string | null): value is AppPage {
  return value !== null && (VALID_PAGES as string[]).includes(value)
}

/** Last in-app page (survives refresh; URL stays unchanged). */
export function readSavedPage(): AppPage {
  if (typeof window === "undefined") return "dashboard"
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    return isValidPage(saved) ? saved : "dashboard"
  } catch {
    return "dashboard"
  }
}

export function saveActivePage(page: AppPage) {
  if (typeof window === "undefined") return
  try {
    sessionStorage.setItem(STORAGE_KEY, page)
  } catch {
    // private mode / quota — ignore
  }
}

export function clearSavedPage() {
  if (typeof window === "undefined") return
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}
