(() => {
  'use strict';
  if (window.__testhpRegionRootSemanticsInstalled) return;
  window.__testhpRegionRootSemanticsInstalled = true;

  const normalize = () => {
    const host = document.getElementById('testhp-end-user-layer');
    if (!host) return;
    host.querySelectorAll('button.dt-tree-root').forEach(button => {
      if (button.dataset.region !== 'hand') button.dataset.region = 'hand';
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', normalize, { once: true });
  } else {
    normalize();
  }

  const observer = new MutationObserver(normalize);
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
