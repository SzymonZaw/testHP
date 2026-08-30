(() => {
  const runSpatialReferenceChecks = () => {
    const registry = window.testhpSpatialReferenceRegistry;
    const createAdapter = window.testhpCreateSpatialDataAdapter;
    if (!registry || !createAdapter) return { ok: false, skipped: true, reason: 'spatial reference modules not loaded' };

    const nih = registry.get('nih-hand-template-3dpx-017237');
    const adapter = createAdapter({ manifest: nih, regionMappings: [] });
    const checks = [
      ['NIH reference exists', !!nih],
      ['reference is not user data', nih?.kind === 'hand_geometry'],
      ['no invented region mappings', adapter.regionValidation.mappings.length === 0],
      ['palm is a supported canonical region id', adapter.regionIds.includes('palm')],
      ['missing region mapping remains unresolved', adapter.geometryToRegion('unknown-geometry') === null],
      ['invalid cell is rejected', !adapter.validateCell({ cellId: 'A17' }).valid]
    ];
    return { ok: checks.every(([, ok]) => ok), checks };
  };

  window.testhpRunSpatialReferenceChecks = runSpatialReferenceChecks;
})();
