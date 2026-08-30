import { SpatialDataAdapter } from "./spatial-data-adapter.js";
import { createSpatialAsset, createSpatialSource, createCoordinateSystem } from "./spatial-types.js";

(() => {
  "use strict";
  if (window.TestHPSpatial) return;

  function currentState() {
    try { return window.TestHPCanonicalState?.get?.() || null; } catch { return null; }
  }

  function assetFromState(state) {
    const candidate = (Array.isArray(state?.assets) ? state.assets : []).find((item) => {
      const modality = String(item?.modality ?? item?.type ?? "").toLowerCase();
      return ["hand_3d", "3d", "mesh", "gltf", "glb"].includes(modality) && (item?.url || item?.uri || item?.assetUrl || item?.asset_url);
    });
    if (!candidate) return null;
    const sourceId = candidate.sourceId || candidate.source_id || state?.provenance?.input_id || "backend-spatial-source";
    const coordinateSystem = createCoordinateSystem(candidate.coordinateSystem || candidate.coordinate_system || {});
    const regions = (state?.anatomy?.regions || []).map((region) => ({
      id: String(region?.region_id ?? region?.regionId ?? region?.id ?? "").toLowerCase(),
      label: region?.label || region?.name,
      geometryId: region?.geometryId ?? region?.geometry_id ?? region?.meshId ?? region?.mesh_id,
      evidenceIds: Array.isArray(region?.evidenceIds) ? region.evidenceIds : [],
      tissueIds: Array.isArray(region?.tissueIds) ? region.tissueIds : [],
    })).filter((region) => region.id && region.geometryId);
    return {
      source: createSpatialSource({
        id: sourceId,
        type: candidate.sourceType || candidate.source_type || "own_dataset",
        label: candidate.sourceLabel || candidate.source_label || "Backend spatial source",
        uri: candidate.source || candidate.uri,
        version: candidate.version || "",
        license: candidate.license || "",
        provenance: candidate.provenance || state?.provenance || {},
      }),
      coordinateSystem,
      asset: createSpatialAsset({
        id: candidate.id || candidate.assetId || candidate.asset_id || `asset:${sourceId}`,
        version: candidate.version || "1.0.0",
        format: candidate.format || (String(candidate.url || candidate.uri || "").toLowerCase().endsWith(".glb") ? "glb" : "gltf"),
        sourceId,
        assetUrl: candidate.url || candidate.uri || candidate.assetUrl || candidate.asset_url,
        coordinateSystemId: coordinateSystem.id,
        regions,
        metadata: candidate.metadata || {},
      }),
    };
  }

  function buildAdapter(state) {
    const sourceAsset = assetFromState(state);
    if (!sourceAsset) return null;
    return new SpatialDataAdapter({
      source: sourceAsset.source,
      coordinateSystem: sourceAsset.coordinateSystem,
      asset: sourceAsset.asset,
      evidence: state?.evidence?.items || [],
    });
  }

  function sync() {
    const state = currentState();
    const adapter = buildAdapter(state);
    window.TestHPSpatial = {
      version: 1,
      adapter,
      state,
      validation: adapter?.validate() || { valid: false, reason: "No backend spatial asset supplied." },
      getRegion: (regionId) => adapter?.getRegion(regionId) || null,
      getEvidence: (regionId) => adapter?.getEvidence(regionId) || [],
    };
    window.dispatchEvent(new CustomEvent("testhp:spatial-layer-changed", {
      detail: window.TestHPSpatial,
    }));
  }

  window.TestHPSpatialRuntime = { sync, buildAdapter };
  window.addEventListener("testhp:canonical-state-changed", sync);
  sync();
})();
