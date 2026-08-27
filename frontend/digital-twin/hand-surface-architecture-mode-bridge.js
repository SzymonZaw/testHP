(() => {
  'use strict';

  // Legacy URL compatibility only. Architecture mode remains owned by the
  // canonical geometry/data modules. This bridge only exposes verification
  // metadata and bootstraps the canonical capability registry once.
  window.testhpHandSurfaceArchitectureModeBridge = window.testhpHandSurfaceArchitectureModeBridge || {};
  if (window.__testhpDigitalTwinCapabilities) return;

  const src = '/digital-twin/digital-twin-capability-runtime.js?v=capabilities-1';
  if ([...document.scripts].some(script => script.src && script.src.includes('/digital-twin-capability-runtime.js'))) return;
  const script = document.createElement('script');
  script.src = src;
  script.async = false;
  script.onerror = () => {
    window.testhpHandSurfaceArchitectureModeBridge.capabilityRuntimeError = `Nie udało się załadować ${src}`;
  };
  document.head.appendChild(script);
})();
