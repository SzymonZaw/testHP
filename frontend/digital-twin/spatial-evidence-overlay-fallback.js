(() => {
  const REGISTRY = '/api/spatial/registry';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const normalize = v => String(v ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
  const target = () => normalize(
    window.testhpSpatialContract?.getTarget?.()?.spatial_id ||
    window.selectedSpatialNode?.spatial_id ||
    window.spatialEvidenceTarget ||
    'hand'
  );

  const inferView = item => {
    const explicit = normalize(item?.view || item?.camera_view || item?.projection_view);
    if (VIEWS.includes(explicit)) return explicit;
    const name = normalize(item?.filename || '').replace(/[^a-z0-9]+/g, '_');
    for (const view of VIEWS) {
      if (new RegExp(`(?:^|_)${view}(?:_|$)`, 'i').test(name)) return view;
    }
    if (/(?:^|_)left(?:_|$)/i.test(name)) return 'side_left';
    if (/(?:^|_)right(?:_|$)/i.test(name)) return 'side_right';
    if (/(?:^|_)kciuk(?:_|$)/i.test(name)) return 'thumb';
    return null;
  };

  async function fetchRegistry() {
    const t = target();
    const url = `${REGISTRY}?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encodeURIComponent(t)}&debug=true`;
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error(`registry HTTP ${response.status}`);
    const payload = await response.json();
    const items = Array.isArray(payload.items) ? payload.items : [];
    // A registry-root asset is evidence inventory, not visual localization.
    // Only explicitly/localized evidence may be projected onto the 3D surface.
    const localizedItems = items.filter(item => item?.spatially_localized === true);
    return {
      target: t,
      items: localizedItems,
      registryCount: items.length,
      localizedCount: localizedItems.length,
      skippedNonLocalizedCount: items.length - localizedItems.length,
    };
  }

  function findTargetMesh(root, spatialTarget) {
    const leaf = normalize(spatialTarget).split('/').filter(Boolean).pop() || 'hand';
    const aliases = new Set([leaf, `skin:${leaf}`, `skin_${leaf}`, `${leaf}_mesh`, `${leaf}-mesh`]);
    let exact = null;
    let fuzzy = null;
    root.traverse?.(object => {
      if (!object?.isMesh) return;
      const name = normalize(object.name);
      if (aliases.has(name)) exact = exact || object;
      else if (!fuzzy && (name.includes(leaf) || name.includes(`skin:${leaf}`))) fuzzy = object;
    });
    return exact || fuzzy || (leaf === 'hand' ? root.getObjectByName('hand') : null);
  }

  function placement(view, bounds, THREE) {
    const { box, center, size } = bounds;
    const depth = Math.max(size.x, size.y, size.z) * 0.12;
    const width = Math.max(size.x, size.y) * 0.92;
    const height = Math.max(size.x, size.y) * 0.72;
    const placements = {
      front: { position: new THREE.Vector3(center.x, center.y, box.max.z + depth), rotation: new THREE.Euler(0, 0, 0) },
      back: { position: new THREE.Vector3(center.x, center.y, box.min.z - depth), rotation: new THREE.Euler(0, Math.PI, 0) },
      side_left: { position: new THREE.Vector3(box.min.x - depth, center.y, center.z), rotation: new THREE.Euler(0, -Math.PI / 2, 0) },
      side_right: { position: new THREE.Vector3(box.max.x + depth, center.y, center.z), rotation: new THREE.Euler(0, Math.PI / 2, 0) },
      thumb: { position: new THREE.Vector3(center.x - size.x * 0.32, center.y + size.y * 0.08, center.z + size.z * 0.08), rotation: new THREE.Euler(0, -0.65, 0) }
    };
    const p = placements[view] || placements.front;
    return {
      ...p,
      scale: new THREE.Vector3(
        view === 'thumb' ? width * 0.45 : width,
        view === 'thumb' ? height * 0.55 : height,
        Math.max(depth * 8, 0.2)
      )
    };
  }

  function resolveView(item, index, usedViews) {
    const inferred = inferView(item);
    if (inferred && !usedViews.has(inferred)) return { view: inferred, method: 'metadata-or-filename' };
    const fallback = VIEWS.find(view => !usedViews.has(view));
    return fallback ? { view: fallback, method: 'registry-order-fallback' } : null;
  }

  async function applyRegistryOverlay(ctx) {
    const manager = window.spatialViewportManager;
    if (!manager?.active?.scene || !ctx.items.length) return { applied: false, reason: 'no-localized-registry-evidence', registryCount: ctx.registryCount, localizedCount: ctx.localizedCount, skippedNonLocalizedCount: ctx.skippedNonLocalizedCount };
    const THREE = await import('three');
    const { DecalGeometry } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/geometries/DecalGeometry.js');
    const root = manager.active.scene;
    const mesh = findTargetMesh(root, ctx.target);
    if (!mesh?.isMesh) return { applied: false, reason: 'target-mesh-not-found', registryCount: ctx.registryCount, localizedCount: ctx.localizedCount, skippedNonLocalizedCount: ctx.skippedNonLocalizedCount };

    root.getObjectByName('__spatial_registry_evidence_projection__')?.removeFromParent();
    const group = new THREE.Group();
    group.name = '__spatial_registry_evidence_projection__';
    const box = new THREE.Box3().setFromObject(mesh);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    const bounds = { box, size, center };
    const usedViews = new Set();
    const applied = [];

    for (let index = 0; index < ctx.items.length; index += 1) {
      const item = ctx.items[index];
      const resolved = resolveView(item, index, usedViews);
      if (!resolved) continue;
      const { view, method } = resolved;
      const assetId = item?.asset_id;
      if (!assetId) continue;
      const imageUrl = `/api/spatial/preview/${encodeURIComponent(assetId)}?max_width=1400&max_height=1000`;
      try {
        const texture = await new THREE.TextureLoader().loadAsync(imageUrl);
        texture.colorSpace = THREE.SRGBColorSpace;
        const material = new THREE.MeshBasicMaterial({
          map: texture,
          transparent: true,
          opacity: 0.62,
          depthWrite: false,
          polygonOffset: true,
          polygonOffsetFactor: -1
        });
        const p = placement(view, bounds, THREE);
        const decal = new THREE.Mesh(new DecalGeometry(mesh, p.position, p.rotation, p.scale), material);
        decal.name = `registry-evidence-projection:${view}:${assetId}`;
        group.add(decal);
        usedViews.add(view);
        applied.push({ view, method, assetId, evidenceId: item.evidence_id || null, filename: item.filename || null });
      } catch (error) {
        console.warn('[spatial-evidence-overlay]', item?.filename || assetId, error);
      }
    }

    if (!group.children.length) return { applied: false, reason: 'registry-images-not-loadable', registryCount: ctx.registryCount, localizedCount: ctx.localizedCount, skippedNonLocalizedCount: ctx.skippedNonLocalizedCount };
    root.add(group);
    try { manager.render?.(); } catch {}
    return { applied: true, reason: 'direct-registry-evidence', target: ctx.target, registryCount: ctx.registryCount, localizedCount: ctx.localizedCount, skippedNonLocalizedCount: ctx.skippedNonLocalizedCount, applied };
  }

  async function sync() {
    try {
      const ctx = await fetchRegistry();
      const result = await applyRegistryOverlay(ctx);
      window.__testhpSpatialProjectionDiagnostics = {
        ...(window.__testhpSpatialProjectionDiagnostics || {}),
        target: ctx.target,
        directRegistryEvidence: true,
        registryCount: ctx.registryCount,
        localizedCount: ctx.localizedCount,
        skippedNonLocalizedCount: ctx.skippedNonLocalizedCount,
        ...result
      };
      window.dispatchEvent(new CustomEvent('testhp:spatial-evidence-overlay-applied', { detail: result }));
      return result;
    } catch (error) {
      const result = { applied: false, reason: 'registry-overlay-error', message: error?.message || String(error) };
      window.__testhpSpatialProjectionDiagnostics = { ...(window.__testhpSpatialProjectionDiagnostics || {}), target: target(), directRegistryEvidence: true, ...result };
      console.warn('[spatial-evidence-overlay]', error);
      return result;
    }
  }

  const original = window.testhpPhotoSurfaceProjection?.sync;
  const wrappedSync = async () => {
    if (typeof original === 'function') {
      try { await original(); } catch {}
    }
    const result = await sync();
    if (result.applied) {
      const existing = window.testhpPhotoSurfaceProjection;
      if (existing) existing.getDiagnostics = () => window.__testhpSpatialProjectionDiagnostics || null;
    }
    return result;
  };

  window.testhpSpatialEvidenceOverlayFallback = { sync, getDiagnostics: () => window.__testhpSpatialProjectionDiagnostics || null };
  if (window.testhpPhotoSurfaceProjection) window.testhpPhotoSurfaceProjection.sync = wrappedSync;
  window.addEventListener('testhp:spatial-target-changed', () => setTimeout(sync, 250));
  window.addEventListener('testhp:evidence-registry-synced', () => setTimeout(sync, 250));
  window.addEventListener('testhp:viewport-manager-ready', () => setTimeout(sync, 400));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(sync, 900), { once: true });
  else setTimeout(sync, 900);
})();
