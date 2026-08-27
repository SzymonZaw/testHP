(() => {
  'use strict';

  // Compatibility entry point only.
  // Geometry ownership belongs exclusively to hand-surface-geometry-canonical-bridge.js.
  // This file intentionally does not create a second Three.js scene, renderer,
  // animation loop, or window.digitalTwinGeometry implementation.
  const removeLegacyPreview = () => {
    document.getElementById('hand-geometry-live-preview')?.remove();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', removeLegacyPreview, { once: true });
  } else {
    removeLegacyPreview();
  }
})();
