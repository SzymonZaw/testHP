(() => {
  const KEY = 'testhp-evidence-seed-reload-v1';
  window.addEventListener('testhp:evidence-registry-synced', (event) => {
    const count = Number(event?.detail?.count || 0);
    if (!count || sessionStorage.getItem(KEY) === '1') return;
    sessionStorage.setItem(KEY, '1');
    setTimeout(() => location.reload(), 0);
  }, { once: true });
  window.addEventListener('load', () => sessionStorage.removeItem(KEY));
})();
