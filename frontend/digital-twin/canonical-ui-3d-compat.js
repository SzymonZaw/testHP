(() => {
  'use strict';
  if (window.__testhpCanonical3DCompat) return;
  window.__testhpCanonical3DCompat = true;

  const sync = () => {
    document.querySelectorAll('.dt-region[data-region]').forEach((node) => node.classList.add('tree-region'));
    document.querySelectorAll('.dt-tissue[data-tissue]').forEach((node) => node.classList.add('tree-leaf'));
    document.querySelectorAll('.dt-cell[data-cell]').forEach((node) => node.classList.add('tree-leaf'));
  };
  const observer = new MutationObserver(sync);
  if (document.body) observer.observe(document.body, { childList: true, subtree: true });
  sync();
})();
