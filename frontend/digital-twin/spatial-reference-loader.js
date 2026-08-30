(() => {
  // Loads metadata for public reference datasets without treating them as user/patient data.
  // Binary assets remain external; this layer records provenance and validates capabilities.
  const registry = () => window.testhpSpatialReferenceRegistry;

  const REQUIRED = ['id', 'kind', 'title', 'sourceUrl', 'provides', 'doesNotProvide', 'provenance', 'status'];

  function validateReference(reference) {
    const errors = REQUIRED.filter(key => reference == null || reference[key] == null || reference[key] === '')
      .map(key => `missing:${key}`);
    if (reference && !Array.isArray(reference.provides)) errors.push('invalid:provides');
    if (reference && !Array.isArray(reference.doesNotProvide)) errors.push('invalid:doesNotProvide');
    return Object.freeze({ valid: errors.length === 0, errors });
  }

  function load(id) {
    const source = registry()?.get(id);
    if (!source) return Object.freeze({ ok: false, error: 'reference_not_found' });
    const validation = validateReference(source);
    if (!validation.valid) return Object.freeze({ ok: false, error: 'invalid_reference', validation });
    return Object.freeze({
      ok: true,
      source,
      asset: Object.freeze({
        sourceId: source.id,
        sourceUrl: source.sourceUrl,
        downloadUrl: source.downloadUrl || null,
        coordinateSystem: source.coordinateSystem || 'source-defined',
        provides: [...source.provides],
        doesNotProvide: [...source.doesNotProvide],
        provenance: source.provenance,
        status: source.status
      })
    });
  }

  function capabilities(id) {
    const result = load(id);
    if (!result.ok) return result;
    return Object.freeze({
      ok: true,
      canProvide: result.asset.provides,
      cannotProvide: result.asset.doesNotProvide
    });
  }

  window.testhpSpatialReferenceLoader = Object.freeze({ validateReference, load, capabilities });
})();
