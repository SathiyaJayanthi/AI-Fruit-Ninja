const CACHE_NAME = 'ai-fruit-ninja-cache-v1';
const PRECACHE_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/manifest.json',
  './assets/fruits/watermelon.png',
  './assets/fruits/apple.png',
  './assets/fruits/orange.png',
  './assets/fruits/banana.png',
  './assets/fruits/pineapple.png',
  './assets/fruits/strawberry.png',
  './assets/fruits/grapes.png',
  './assets/bombs/bomb.png',
  './assets/backgrounds/arcade_bg.png',
  './assets/sounds/swoosh.wav',
  './assets/sounds/slice.wav',
  './assets/sounds/splat.wav',
  './assets/sounds/combo.wav',
  './assets/sounds/explosion.wav',
  './assets/sounds/game_over.wav'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Pre-caching offline game assets');
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return networkResponse;
      }).catch(() => {
        // Fallback for offline mode
        return caches.match('./index.html');
      });
    })
  );
});
