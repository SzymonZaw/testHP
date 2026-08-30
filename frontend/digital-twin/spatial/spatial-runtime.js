import { SpatialDataAdapter } from "./spatial-data-adapter.js";
import { createSpatialAsset, createSpatialSource, createCoordinateSystem } from "./spatial-types.js";

(() => {
  "use strict";
  if (window.TestHPSpatial) return;

  let referenceState = null;
  let referenceLoaded = false;
  let originalCanonicalState = null;

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

  function publishSpatialState() {
    const state = currentState();
    const adapter = buildAdapter(state);
    window.TestHPSpatial = {
      version: 2,
      adapter,
      state,
      reference: referenceState,
      validation: adapter?.validate() || { valid: false, reason: "No backend or reference spatial asset supplied." },
      getRegion: (regionId) => adapter?.getRegion(regionId) || null,
      getEvidence: (regionId) => adapter?.getEvidence(regionId) || [],
    };
    window.dispatchEvent(new CustomEvent("testhp:spatial-layer-changed", {
      detail: window.TestHPSpatial,
    }));
  }

  function installReferenceState(catalog) {
    const hand = Array.isArray(catalog?.datasets)
      ? catalog.datasets.find((dataset) => dataset?.id === "nih-hand-template-3dpx-017237")
      : null;
    if (!hand?.asset?.url) return false;

    referenceState = {
      id: hand.id,
      status: "reference-only",
      source: hand.provider,
      accession: hand.accession,
      provenance: hand.provenance || {},
      limitations: hand.limitations || [],
      asset: {
        id: hand.id,
        modality: "hand_3d",
        type: "glb",
        format: hand.asset.format || "glb",
        url: hand.asset.url,
        status: "ready",
        sourceType: "public_reference",
        sourceLabel: hand.title,
        version: hand.asset.processedVersion || "2",
        accession: hand.accession,
        coordinateSystem: { id: "source-defined", label: hand.coordinateSystem || "source-defined" },
        provenance: hand.provenance || {},
        metadata: { referenceOnly: true, limitations: hand.limitations || [] },
      },
    };

    if (window.TestHPCanonicalState && !window.__testhpReferenceCanonicalPatched) {
      originalCanonicalState = window.TestHPCanonicalState;
      const originalGet = originalCanonicalState.get;
      const mergedGet = () => {
        const state = originalGet();
        const assets = Array.isArray(state?.assets) ? state.assets : [];
        const hasRealHandAsset = assets.some((asset) => {
          const modality = String(asset?.modality ?? asset?.type ?? "").toLowerCase();
          const url = asset?.url || asset?.uri || asset?.assetUrl || asset?.asset_url;
          return ["hand_3d", "3d", "mesh", "gltf", "glb"].includes(modality) && url;
        });
        if (hasRealHandAsset) return { ...state, spatialReference: referenceState };
        return {
          ...state,
          assets: [...assets, referenceState.asset],
          spatialReference: referenceState,
        };
      };
      window.TestHPCanonicalState = Object.freeze({ ...originalCanonicalState, get: mergedGet });
      window.__testhpReferenceCanonicalPatched = true;
    }
    referenceLoaded = true;
    return true;
  }

  async function loadReferenceCatalog() {
    try {
      const response = await fetch("/digital-twin/reference-dataset-catalog-v1.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`Reference catalog HTTP ${response.status}`);
      const catalog = await response.json();
      installReferenceState(catalog);
    } catch (error) {
      window.dispatchEvent(new CustomEvent("testhp:reference-catalog-error", {
        detail: { message: error?.message || String(error) },
      }));
    } finally {
      publishSpatialState();
    }
  }

  function sync() {
    publishSpatialState();
  }

  window.TestHPSpatialRuntime = {
    sync,
    buildAdapter,
    getReference: () => referenceState,
    isReferenceLoaded: () => referenceLoaded,
  };
  window.addEventListener("testhp:canonical-state-changed", sync);
  sync();
  loadReferenceCatalog();
})();
