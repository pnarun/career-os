const CACHE = "career-os-shell-v5"
const SHELL = [
  "/",
  "/index.html",
  "/career-os-logo-symbol.png",
  "/career-os-logo-full.png",
  "/career-os-logo-black.png",
  "/manifest.webmanifest",
]

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  )
})

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  )
})

function isNavigation(request) {
  return request.mode === "navigate" || request.headers.get("accept")?.includes("text/html")
}

function isAsset(url) {
  return url.pathname.startsWith("/assets/") || url.pathname.endsWith(".js") || url.pathname.endsWith(".css")
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return
  const url = new URL(event.request.url)
  if (url.origin !== self.location.origin) return

  if (isNavigation(event.request) || isAsset(url)) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && response.type === "basic" && isNavigation(event.request)) {
            const clone = response.clone()
            caches.open(CACHE).then((cache) => cache.put("/index.html", clone))
          }
          return response
        })
        .catch(() => caches.match("/index.html"))
    )
    return
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached
      return fetch(event.request)
    })
  )
})
