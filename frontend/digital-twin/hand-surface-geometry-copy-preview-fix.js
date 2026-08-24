(() => {
  const LEGACY_NOTE = 'Przesuwaj suwaki i obserwuj model. Nie musisz zatwierdzać każdej zmiany osobnym przyciskiem.';

  const removeLegacyPreview = () => {
    const candidates = [...document.querySelectorAll('.hss-grid > .hss-card')];
    let removed = false;

    candidates.forEach(card => {
      const text = (card.textContent || '').replace(/\s+/g, ' ').trim();
      const hasLegacyNote = text.includes(LEGACY_NOTE);
      const hasGeometryInfo = !!card.querySelector('.hss-geometry-info');
      const hasLegacyLastChange = !!card.querySelector('#hss-geometry-last');

      if (hasLegacyNote && hasGeometryInfo && hasLegacyLastChange) {
        card.remove();
        removed = true;
      }
    });

    return removed;
  };

  const boot = () => {
    removeLegacyPreview();

    if (!window.__testhpGeometryCopyPreviewFixObserver) {
      const observer = new MutationObserver(() => removeLegacyPreview());
      if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
        window.__testhpGeometryCopyPreviewFixObserver = observer;
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
