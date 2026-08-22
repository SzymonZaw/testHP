// Canonical spatial target writer. The backend and evidence registry use the
// stable contract id; display aliases must not leak into manager state.
(() => {
  const ALIASES = new Map([
    ['hypothenar-eminence', 'hypothenar'],
    ['thenar-eminence', 'thenar'],
    ['central-palm-region', 'central-palm'],
  ]);

  const canonicalId = value => {
    const raw = value == null ? '' : String(value).trim().replace(/^\/+|\/+$/g, '');
    if (!raw) return 'hand';
    const parts = raw.split('/').filter(Boolean).map(part => ALIASES.get(part) || part);
    if (parts[0] !== 'hand') parts.unshift('hand');
    return parts.join('/');
  };

  const canonicalTarget = target => {
    if (!target || typeof target !== 'object') return target;
    const copy = { ...target };
    const raw = copy.spatial_id ?? copy.spatialId ?? copy.id;
    const spatialId = canonicalId(raw);
    copy.spatial_id = spatialId;
    copy.spatialId = spatialId;
    // Keep the semantic child id stable when the target is an ontology alias.
    if (copy.id && ALIASES.has(String(copy.id))) copy.id = ALIASES.get(String(copy.id));
    return copy;
  };

  const install = () => {
    const manager = window.spatialViewportManager;
    if (!manager || typeof manager.setSpatialTarget !== 'function') return false;
    if (manager.__testhpCanonicalSetSpatialTarget) return true;
    const original = manager.setSpatialTarget;
    manager.setSpatialTarget = function (target, ...rest) {
      const canonical = canonicalTarget(target);
      window.__testhpLastCanonicalSpatialTarget = canonical;
      return original.call(this, canonical, ...rest);
    };
    manager.__testhpCanonicalSetSpatialTarget = true;
    window.__testhpSpatialCanonicalizerInstalled = true;
    window.__testhpCanonicalSpatialId = canonicalId;
    window.__testhpCanonicalSpatialTarget = canonicalTarget;
    return true;
  };

  window.__testhpCanonicalSpatialId = canonicalId;
  window.__testhpCanonicalSpatialTarget = canonicalTarget;
  window.addEventListener('testhp:viewport-manager-ready', install);
  if (!install()) {
    const timer = setInterval(() => { if (install()) clearInterval(timer); }, 25);
    setTimeout(() => clearInterval(timer), 10000);
  }
})();
