(() => {
  'use strict';
  if (window.__testhpExplorationFirstInstalled) return;
  window.__testhpExplorationFirstInstalled = true;
  const root = () => document.getElementById('testhp-end-user-layer');

  function ensureReferenceRegionGeometry() {
    if (!window.__testhpReferenceHandState?.active) return;
    if (window.testhpReferenceRegionGeometry) return;
    if (document.getElementById('testhp-reference-region-geometry-script')) return;
    const script = document.createElement('script');
    script.id = 'testhp-reference-region-geometry-script';
    script.src = '/digital-twin/reference-region-geometry.js?v=reference-region-safe-1';
    script.async = true;
    script.addEventListener('error', () => { window.__testhpReferenceRegionGeometryLoadError = true; }, { once: true });
    document.head.appendChild(script);
  }

  function ensureReferenceTissueRegistry() {
    if (!window.__testhpReferenceHandState?.active) return;
    if (window.testhpReferenceTissueRegistry) return;
    if (document.getElementById('testhp-reference-tissue-registry-script')) return;
    const script = document.createElement('script');
    script.id = 'testhp-reference-tissue-registry-script';
    script.src = '/digital-twin/reference-tissue-registry.js?v=reference-tissue-safe-1';
    script.async = true;
    script.addEventListener('error', () => { window.__testhpReferenceTissueRegistryLoadError = true; }, { once: true });
    document.head.appendChild(script);
  }

  function render() {
    const host = root();
    if (!host || !host.querySelector('.dt-phase9')) return;
    host.classList.add('dt-exploration-first');

    if (window.__testhpReferenceHandState?.active && window.testhpReferenceHand3D?.activate) {
      window.testhpReferenceHand3D.activate();
      ensureReferenceRegionGeometry();
      ensureReferenceTissueRegistry();
    }

    const workspace = host.querySelector('.workspace');
    if (!workspace || workspace.dataset.explorationFirst === '1') return;
    workspace.dataset.explorationFirst = '1';
    const center = workspace.querySelector('.center');
    if (center) {
      const head = center.querySelector('.viewer-head');
      if (head && !head.querySelector('.dt-explore-context')) {
        const context = document.createElement('div');
        context.className = 'dt-explore-context';
        context.innerHTML = '<strong>REFERENCE HAND</strong><span>NIH 3D · reference geometry</span><em>Reference data · not user health data</em>';
        head.prepend(context);
      }
      const viewport = center.querySelector('.viewport');
      if (viewport && !viewport.querySelector('.dt-explore-hint')) {
        const hint = document.createElement('div');
        hint.className = 'dt-explore-hint';
        hint.innerHTML = '<b>Explore the hand</b><span>Select a region to continue</span>';
        viewport.appendChild(hint);
      }
    }
    const right = workspace.querySelector('.right');
    if (right && !right.querySelector('.dt-next-step')) {
      const next = document.createElement('section');
      next.className = 'card dt-next-step';
      next.innerHTML = '<div class="eyebrow">NEXT STEP</div><strong>Select a hand region</strong><span>Start with Palm, then explore deeper evidence when supplied.</span>';
      right.prepend(next);
    }
  }

  function activateReference(event) {
    const detail = event?.detail ?? {};
    window.__testhpReferenceHandState = Object.freeze({
      active: true,
      sourceId: detail.sourceId || 'nih-hand-template-3DPX-017237',
      regionId: detail.regionId || 'palm',
      provenance: 'public_reference'
    });
    window.dispatchEvent(new CustomEvent('testhp:reference-hand-activated', { detail: window.__testhpReferenceHandState }));
    ensureReferenceRegionGeometry();
    ensureReferenceTissueRegistry();
    render();
  }

  window.addEventListener('testhp:reference-hand-requested', activateReference);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render, { once: true });
  else render();
  new MutationObserver(render).observe(document.documentElement, { childList: true, subtree: true });
})();
