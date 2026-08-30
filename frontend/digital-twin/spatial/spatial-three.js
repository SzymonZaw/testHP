export function annotateSpatialObject(object3D, { geometryId, regionId, tissueId = null, cellId = null } = {}) {
  if (!object3D) return object3D;
  object3D.userData = {
    ...object3D.userData,
    spatial: { geometryId, regionId, tissueId, cellId },
  };
  return object3D;
}

export function findSpatialObject(root, predicate) {
  let match = null;
  root?.traverse?.((object) => {
    if (!match && predicate(object)) match = object;
  });
  return match;
}

export function findObjectByGeometryId(root, geometryId) {
  return findSpatialObject(root, (object) => object.userData?.spatial?.geometryId === geometryId);
}

export function getSpatialMetadataFromIntersection(intersection) {
  let object = intersection?.object;
  while (object) {
    if (object.userData?.spatial?.regionId) return object.userData.spatial;
    object = object.parent;
  }
  return null;
}

export function createSpatialPicker({ THREE, camera, domElement, root, onSelect }) {
  if (!THREE?.Raycaster || !THREE?.Vector2) throw new Error("Three.js Raycaster and Vector2 are required.");
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  function handlePointerDown(event) {
    const rect = domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const intersections = raycaster.intersectObject(root, true);
    for (const intersection of intersections) {
      const spatial = getSpatialMetadataFromIntersection(intersection);
      if (spatial) {
        onSelect?.(spatial, intersection);
        break;
      }
    }
  }

  domElement.addEventListener("pointerdown", handlePointerDown);
  return () => domElement.removeEventListener("pointerdown", handlePointerDown);
}

export function setSpatialHighlight(root, regionId, { active = true } = {}) {
  root?.traverse?.((object) => {
    const spatial = object.userData?.spatial;
    if (!spatial?.regionId) return;
    object.userData.spatialSelected = active && spatial.regionId === regionId;
    if (object.material && "emissiveIntensity" in object.material) {
      object.material.emissiveIntensity = object.userData.spatialSelected ? 0.7 : 0;
    }
  });
}
