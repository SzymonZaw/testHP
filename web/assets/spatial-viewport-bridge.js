(() => {
  const viewport = document.getElementById('twin-viewport');
  const nav = document.querySelector('.spatial-navigator');
  if (!viewport || !nav) return;

  function sync() {
    const manager = window.spatialViewportManager;
    if (manager && typeof manager.render === 'function') manager.render();
  }

  nav.addEventListener('click', () => requestAnimationFrame(sync), true);

  const ids = ['spatial-level-badge', 'spatial-breadcrumb', 'spatial-node', 'spatial-children'];
  const observer = new MutationObserver(() => requestAnimationFrame(sync));
  ids.map(id => document.getElementById(id)).filter(Boolean).forEach(el => {
    observer.observe(el, { childList: true, subtree: true, characterData: true, attributes: true });
  });

  const timer = window.setInterval(sync, 250);
  window.addEventListener('beforeunload', () => window.clearInterval(timer), { once: true });
  window.setTimeout(sync, 0);
})();
