(() => {
  'use strict';

  const reveal = () => {
    const model = document.querySelector('.dt-reference-3d-model');
    if (!model) return false;

    const revealModel = () => {
      try {
        // Use model-viewer's native reveal path. The viewer previously used
        // reveal="manual", which left its internal WebGL canvas at display:none
        // even after dismissPoster(). Switching to auto lets model-viewer manage
        // the canvas visibility together with its viewport/render lifecycle.
        if (model.getAttribute('reveal') !== 'auto') {
          model.setAttribute('reveal', 'auto');
        }
        model.updateFraming?.();
        model.requestUpdate?.();
      } catch (_) {}
    };

    revealModel();

    if (model.__testhpViewportRevealObserver) return true;

    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        revealModel();
        observer.disconnect();
        model.__testhpViewportRevealObserver = null;
        break;
      }
    }, { root: null, rootMargin: '200px 0px', threshold: 0.00001 });

    model.__testhpViewportRevealObserver = observer;
    observer.observe(model);
    return true;
  };

  const syncAfterCanonicalRegionChange = () => {
    const hand = window.__testhpReferenceHandState;
    if (!hand?.active) return;

    const viewerState = window.__testhpReferenceHand3DViewerState;
    if (viewerState) {
      window.__testhpReferenceHand3DViewerState = Object.freeze({
        ...viewerState,
        regionId: hand.regionId || viewerState.regionId || 'palm'
      });
    }

    if (!document.querySelector('.dt-reference-3d-model')) {
      // The canonical region tree rebuild can detach the existing model-viewer.
      // Mark the stale loaded state as needing a remount, then use the viewer's
      // public activation hook. The reference viewer can reattach its existing
      // loaded card instead of downloading the GLB again.
      if (viewerState?.loaded) {
        window.__testhpReferenceHand3DViewerState = Object.freeze({
          ...window.__testhpReferenceHand3DViewerState,
          active: true,
          loading: false,
          loaded: false,
          regionId: hand.regionId || 'palm'
        });
      }
      window.testhpReferenceHand3D?.activate?.();
    }

    reveal();
  };

  const install = () => {
    reveal();

    const mutationObserver = new MutationObserver(() => {
      reveal();
    });
    mutationObserver.observe(document.documentElement || document, { childList: true, subtree: true });

    window.addEventListener('testhp-canonical-state-changed', syncAfterCanonicalRegionChange);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install, { once: true });
  } else {
    install();
  }
})();
