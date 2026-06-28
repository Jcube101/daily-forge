/**
 * Daily Forge service worker — offline shell + notification support.
 */

const CACHE_NAME = "daily-forge-v0.2.2";
const PRECACHE_URLS = [
  "/",
  "/static/style.css",
  "/static/app.js",
  "/static/js/settings.js",
  "/static/js/heatmap.js",
  "/static/js/char-count.js",
  "/static/js/drafts.js",
  "/static/js/onboarding.js",
  "/static/js/recap.js",
  "/static/js/notifications.js",
  "/static/manifest.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  // API calls: network-first.
  if (request.url.includes("/api/")) {
    event.respondWith(
      fetch(request).catch(() => caches.match(request))
    );
    return;
  }

  // Static assets & pages: cache-first, fallback network.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (!response || response.status !== 200 || response.type !== "basic") {
          return response;
        }
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        return response;
      });
    })
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SHOW_REMINDER") {
    const { title, body } = event.data;
    self.registration.showNotification(title || "Daily Forge", {
      body: body || "Time to show up — what's one thing you'll share today?",
      icon: "/static/icons/icon-192.png",
      badge: "/static/icons/icon-192.png",
      tag: "daily-forge-reminder",
      renotify: true,
    });
  }
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      if (clients.length > 0) return clients[0].focus();
      return self.clients.openWindow("/");
    })
  );
});