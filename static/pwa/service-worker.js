const CACHE_NAME = "corefix-v1";

const STATIC_ASSETS = [
    "/",
    "/static/css/style.css",
    "/static/js/script.js",
    "/static/assets/corefix-icon-192.png",
    "/static/pwa/manifest.json"
];


/* =====================================================
   INSTALL
===================================================== */

self.addEventListener("install", event => {

    event.waitUntil(
        caches
            .open(CACHE_NAME)
            .then(cache => {

                return cache.addAll(STATIC_ASSETS);

            })
    );

    self.skipWaiting();

});


/* =====================================================
   ACTIVATE
===================================================== */

self.addEventListener("activate", event => {

    event.waitUntil(
        caches
            .keys()
            .then(cacheNames => {

                return Promise.all(
                    cacheNames
                        .filter(name => name !== CACHE_NAME)
                        .map(name => caches.delete(name))
                );

            })
    );

    self.clients.claim();

});


/* =====================================================
   FETCH
===================================================== */

self.addEventListener("fetch", event => {

    if (event.request.method !== "GET") {
        return;
    }

    event.respondWith(
        caches
            .match(event.request)
            .then(cachedResponse => {

                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(event.request)
                    .then(networkResponse => {

                        const responseClone =
                            networkResponse.clone();

                        caches
                            .open(CACHE_NAME)
                            .then(cache => {

                                cache.put(
                                    event.request,
                                    responseClone
                                );

                            });

                        return networkResponse;

                    })
                    .catch(() => {

                        if (
                            event.request.mode === "navigate"
                        ) {
                            return caches.match("/");
                        }

                    });

            })
    );

});