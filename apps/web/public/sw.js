// Minimal PWA service worker: cache-first for the app shell so an already-loaded
// wardrobe view degrades gracefully offline (docs/PRD.md §7 "Offline resilience").
// Deliberately not using a library (next-pwa etc.) for Phase 0 — this is the whole
// thing, kept small enough to read in one sitting; revisit if offline needs grow
// past "don't show a blank white screen."
const CACHE_NAME = "muse-shell-v1";
const SHELL_PATHS = ["/today", "/manifest.webmanifest"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_PATHS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  // Never cache API calls — wardrobe/outfit data must stay live, not stale.
  if (event.request.url.includes("/api/v1/")) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          return response;
        })
        .catch(() => cached);
    })
  );
});
