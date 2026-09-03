(() => {
  'use strict';

  const install = () => {
    const reveal = () => {
      const model = document.querySelector('.dt-reference-3d-model');
      if (!model) return false;

      const revealModel = () => {
        try {
          model.dismissPoster?.();
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
