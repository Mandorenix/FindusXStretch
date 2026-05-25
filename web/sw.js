const CACHE_NAME = 'findus-light-v1';
const ASSETS = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './worker.js',
  './web_wrapper.py',
  './dsp.py',
  './manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

// Fetch event: Network-first, fallback to cache
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        // If network request succeeds, update the cache with the fresh response
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        // If network fails (offline), return from cache
        return caches.match(event.request);
      })
  );
});
