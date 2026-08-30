(() => {
  'use strict';
  if (window.__testhpSpatialActiveAssetBridgeInstalled) return;
  window.__testhpSpatialActiveAssetBridgeInstalled = true;

  function sync(asset) {
    const state = window.TestHPCanonicalState?.get?.();
    if (!state) return;
    state.assets = asset ? [{
      id: asset.id,
      url: asset.url,
      status: asset.status || 'available',
      modality: 'hand_3d',
      source_id: asset.sourceId || asset.source_id || 'user-upload',
      provenance: asset.metadata?.provenance || { sourceType: asset.ownership === 'user' ? 'user_upload' : 'public_reference' },
      spatial_manifest: asset.metadata || null,
      geometry_mapping: asset.mapping || null
    }] : [];
    if (asset?.metadata?.regions) {
      state.anatomy = state.anatomy || {};
      state.anatomy.regions = asset.metadata.regions;
    }
    window.dispatchEvent(new CustomEvent('testhp:canonical-state-changed',{detail:{source:'spatial-active-asset-bridge',asset}}));
  }

  window.addEventListener('testhp:spatial-asset-selected', event => sync(event.detail?.asset || null));
  window.addEventListener('testhp:spatial-asset-cleared', () => sync(null));
})();
