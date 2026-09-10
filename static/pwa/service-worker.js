const CACHE_NAME = "corefix-v2";

const STATIC_ASSETS = [
    "/",
    "/offline",
    "/static/css/style.css",
    "/static/js/script.js",
    "/static/assets/corefix-icon-192.png",
    "/static/assets/corefix-icon-512.png",
    "/static/pwa/manifest.json"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_ASSETS);
        })
    );

    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        })
    );

    self.clients.claim();
});

self.addEventListener("fetch", event => {

    if (event.request.method !== "GET") {
        return;
    }

    // Page navigation requests
    if (event.request.mode === "navigate") {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return caches.match("/offline");
                })
        );

        return;
    }

    // Static files
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {

                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(event.request)
                    .then(networkResponse => {

                        const responseClone =
                            networkResponse.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(
                                    event.request,
                                    responseClone
                                );
                            });

                        return networkResponse;
                    });
            })
    );
});