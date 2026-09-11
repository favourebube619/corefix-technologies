const CACHE_NAME = "corefix-v3";

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

    const url = new URL(event.request.url);

    // Do not cache/intercept admin, API or authenticated pages
    if (
        url.pathname.startsWith("/api/") ||
        url.pathname.startsWith("/admin") ||
        url.pathname.startsWith("/dashboard") ||
        url.pathname.startsWith("/login") ||
        url.pathname.startsWith("/logout") ||
        url.pathname.startsWith("/signup") ||
        url.pathname.startsWith("/profile/")
    ) {
        return;
    }

    // Normal page navigation
    if (event.request.mode === "navigate") {

        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match("/offline"))
        );

        return;
    }

    // Static assets
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {

                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(event.request)
                    .then(networkResponse => {

                        if (
                            !networkResponse ||
                            networkResponse.status !== 200
                        ) {
                            return networkResponse;
                        }

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
                    })
                    .catch(() => {
                        return new Response(
                            "",
                            {
                                status: 503,
                                statusText: "Offline"
                            }
                        );
                    });
            })
    );
});


// =====================================================
// PUSH NOTIFICATIONS
// =====================================================

self.addEventListener("push", event => {

    let data = {
        title: "CoreFix Technologies",
        body: "You have a new update.",
        icon: "/static/assets/corefix-icon-192.png",
        badge: "/static/assets/corefix-icon-192.png",
        url: "/dashboard"
    };

    if (event.data) {
        try {
            data = event.data.json();
        } catch (error) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: data.icon || "/static/assets/corefix-icon-192.png",
        badge: data.badge || "/static/assets/corefix-icon-192.png",
        data: {
            url: data.url || "/dashboard"
        }
    };

    event.waitUntil(
        self.registration.showNotification(
            data.title || "CoreFix Technologies",
            options
        )
    );
});


self.addEventListener("notificationclick", event => {

    event.notification.close();

    const targetUrl =
        event.notification.data?.url || "/dashboard";

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        }).then(windowClients => {

            for (const client of windowClients) {
                if ("focus" in client) {
                    client.navigate(targetUrl);
                    return client.focus();
                }
            }

            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});