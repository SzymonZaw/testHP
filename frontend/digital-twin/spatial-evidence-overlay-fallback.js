(() => {
  // Compatibility shim only.
  //
  // Projection ownership belongs to photo-surface-projection.js. This file
  // must not fetch the legacy spatial registry endpoint, wrap projection.sync(), or install
  // timers of its own: doing so creates a second projection pipeline and
  // produces repeated state/registry requests during bootstrap.
  //
  // Keep the public diagnostics hook so older debug tooling does not fail.
  const diagnostics = () => window.__testhpSpatialProjectionDiagnostics || null;

  window.testhpSpatialEvidenceOverlayFallback = {
    sync: async () => diagnostics(),
    getDiagnostics: diagnostics,
    disabled: true,
    reason: 'projection-owned-by-photo-surface-projection'
  };
})();
