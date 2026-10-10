"use strict";
// 셸은 stale-while-revalidate, data/*.json은 네트워크 우선(오프라인이면 마지막 캐시).
const CACHE = "seonhak-v5";
const SHELL = ["./", "index.html", "style.css", "app.js", "config.js", "manifest.json", "icon-192.png", "icon-512.png", "badge-96.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.includes("/data/") || url.pathname.includes("/demo/")) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }
  // stale-while-revalidate: 즉시 캐시로 띄우고 뒤에서 새 버전 받아두기 (다음 실행 때 반영)
  e.respondWith(
    caches.open(CACHE).then((c) =>
      c.match(e.request).then((hit) => {
        const fresh = fetch(e.request)
          .then((res) => { if (res.ok) c.put(e.request, res.clone()); return res; })
          .catch(() => hit);
        return hit || fresh;
      })
    )
  );
});

self.addEventListener("push", (e) => {
  let msg = { title: "선학역 행사 알림", body: "", url: "./" };
  try { msg = Object.assign(msg, e.data.json()); } catch (_) { /* 텍스트 페이로드 */ }
  e.waitUntil(
    self.registration.showNotification(msg.title, {
      body: msg.body,
      icon: "icon-192.png",
      badge: "badge-96.png",
      data: { url: msg.url },
    })
  );
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const target = new URL(e.notification.data.url || "./", self.registration.scope).href;
  e.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if (w.url.startsWith(self.registration.scope)) {
          w.navigate(target);
          return w.focus();
        }
      }
      return self.clients.openWindow(target);
    })
  );
});
