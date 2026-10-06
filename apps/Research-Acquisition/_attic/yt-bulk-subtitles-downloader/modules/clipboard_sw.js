// POF 2828 clipboard service worker — minimal, safe.
// Caches the app shell so it opens even offline; always goes to the network
// for /api (never serve stale clips). If the network fails, falls back to cache.
const CACHE = 'pof-clip-v2';
const SHELL = ['/clipboard3', '/manifest.webmanifest', '/clip-icon.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;            // never cache writes
  if (url.pathname.startsWith('/api')) return;        // clips are always live from the network
  // App shell: cache-first, refresh in the background.
  e.respondWith(
    caches.match(e.request).then((hit) => {
      const net = fetch(e.request).then((res) => {
        if (res && res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
