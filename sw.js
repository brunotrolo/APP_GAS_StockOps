// Service Worker mínimo — só para habilitar instalação como PWA
// Sobe a versão do CACHE a cada mudança relevante no shell (index.html/sw.js):
// isso força o navegador a descartar o cache antigo em vez de servi-lo para sempre.
const CACHE = 'opcoes-launcher-v2';
const SHELL = ['./index.html', './manifest.json', './icon.svg'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Network-first para o shell: sempre tenta buscar a versão mais nova primeiro
// e só cai no cache se estiver offline. Evita ficar preso numa versão antiga
// do launcher depois de um deploy (era exatamente isso que travava a aba
// do dia a dia no redirecionamento automático antigo).
self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
