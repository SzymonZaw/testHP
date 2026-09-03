(() => {
  'use strict';

  const install = () => {
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

    if (reveal()) return;

    const mutationObserver = new MutationObserver(() => {
      if (reveal()) mutationObserver.disconnect();
    });
    mutationObserver.observe(document.documentElement || document, { childList: true, subtree: true });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install, { once: true });
  } else {
    install();
  }
})();
