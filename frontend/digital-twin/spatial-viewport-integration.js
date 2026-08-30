/*
 * Thin integration layer between Three.js picking, SpatialAsset and the
 * existing canonical spatial state/event contract.
 * It does not fabricate anatomy or biological results.
 */
(() => {
  const emit = detail => {
    window.__testhpSpatialState = {
      ...(window.__testhpSpatialState || {}),
      ...detail
    };
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-changed', { detail }));
    window.dispatchEvent(new CustomEvent('testhp:spatial-layer-changed', { detail }));
  };

  function selectRegion(regionId, extra = {}) {
    if (!regionId) return false;
    emit({
      spatial_id: `hand/${regionId}`,
      spatial_node_id: `hand/${regionId}`,
      region: regionId,
      tissue: null,
      cell: null,
      molecularLayer: null,
      ...extra
    });
    return true;
  }

  function selectTissue(regionId, tissueId, extra = {}) {
    if (!regionId || !tissueId) return false;
    emit({
      spatial_id: `hand/${regionId}/${tissueId}`,
      spatial_node_id: `hand/${regionId}/${tissueId}`,
      region: regionId,
      tissue: tissueId,
      cell: null,
      molecularLayer: null,
      ...extra
    });
    return true;
  }

  function selectCell(regionId, tissueId, cellId, extra = {}) {
    if (!regionId || !tissueId || !cellId) return false;
    emit({
      spatial_id: `hand/${regionId}/${tissueId}/${cellId}`,
      spatial_node_id: `hand/${regionId}/${tissueId}/${cellId}`,
      region: regionId,
      tissue: tissueId,
      cell: cellId,
      molecularLayer: null,
      ...extra
    });
    return true;
  }

  function bindThreePicking({ renderer, camera, scene, asset, THREE } = {}) {
    if (!renderer || !camera || !scene || !asset || !THREE) throw new Error('renderer, camera, scene, THREE and asset are required');
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const canvas = renderer.domElement;

    const onPointerDown = event => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(scene.children, true);
      for (const hit of hits) {
        const result = window.testhpSpatialAssetAdapter?.regionForObject(hit.object, asset);
        if (!result) continue;
        selectRegion(result.regionId, {
          geometryId: result.geometryId,
          sourceAssetId: asset.id,
          selectionOrigin: '3d'
        });
        return;
      }
    };

    canvas.addEventListener('pointerdown', onPointerDown);
    return () => canvas.removeEventListener('pointerdown', onPointerDown);
  }

  window.testhpSpatialViewportIntegration = Object.freeze({
    selectRegion,
    selectTissue,
    selectCell,
    bindThreePicking
  });
})();
