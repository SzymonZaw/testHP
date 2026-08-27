(() => {
  'use strict';

  // Canonical geometry owner is implemented by hand-geometry-permanent-module.js.
  // This entrypoint contains no second owner or synchronization logic; it only
  // exposes the canonical API under the expected name.
  const expose = () => {
    const owner = window.__testhpPermanentGeometry;
    if (!owner) return false;
    window.testhpHandGeometryCanonicalOwner = owner;
    return true;
  };

  if (expose()) return;
  let tries = 0;
  const timer = setInterval(() => {
    if (expose() || ++tries > 40) clearInterval(timer);
  }, 100);
})();
