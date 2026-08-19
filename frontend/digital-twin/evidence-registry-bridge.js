// Evidence registry is persisted directly by stages-2-4.js.
// Do not reload the page after registry synchronization: a reload here can
// race the bootstrap sequence and create an endless refresh loop.
(() => {
  window.addEventListener('testhp:evidence-registry-synced', (event) => {
    window.dispatchEvent(new CustomEvent('testhp:evidence-ux-refresh', {
      detail: event.detail || {}
    }));
  });
})();
