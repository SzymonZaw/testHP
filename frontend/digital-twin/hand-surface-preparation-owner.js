(() => {
  'use strict';

  // Single-owner guard for Stage 12. The legacy stages-11-15 renderer still
  // knows how to render an older preparation form. It may run again when the
  // spatial target changes, so this small coordinator restores the canonical
  // preparation UI instead of allowing the two renderers to compete.
  const PREP_SRC = '/digital-twin/hand-surface-preparation-ui.js';
  const isPrepare = () => document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab === 'prepare';
  const canonicalPresent = () => !!document.querySelector('#hss-content .hs-prep-clean');
  const legacyPresent = () => {
    const c = document.getElementById('hss-content');
    if (!c) return false;
    return !!c.querySelector('#hss-file, #hss-run, #hss-saveprep') || /Waiting for an image|Choose a skin photo|Stage 12 · Image preparation/.test(c.textContent || '');
  };

  let restoring = false;
  function restore() {
    if (restoring || !isPrepare() || canonicalPresent() || !legacyPresent()) return;
    restoring = true;
    const content = document.getElementById('hss-content');
    if (content) {
      content.innerHTML = '';
      delete content.dataset.cleanPreparation;
    }

    // Re-execute the canonical preparation controller. It is intentionally
    // loaded only after the legacy DOM has been removed.
    const script = document.createElement('script');
    script.src = `${PREP_SRC}?v=prep-clean-owner-2-${Date.now()}`;
    script.dataset.prepOwnerReload = '1';
    script.onload = () => { restoring = false; };
    script.onerror = () => { restoring = false; };
    document.body.appendChild(script);
  }

  const schedule = () => setTimeout(restore, 0);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:spatial-contract-changed', schedule);
  window.addEventListener('testhp:spatial-target-changed', schedule);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule, {once:true});
  else schedule();

  new MutationObserver(() => {
    if (isPrepare() && legacyPresent() && !canonicalPresent()) schedule();
  }).observe(document.body, {childList:true, subtree:true});
})();
