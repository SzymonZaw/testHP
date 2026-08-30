(() => {
  "use strict";
  if (window.TestHPReferenceLayerRuntime) return;

  let active = Object.freeze({ mode: "reference", tissue: [], cell: [], molecular: [], datasetIds: [], limitations: [] });

  function publish(next) {
    active = Object.freeze({
      mode: "reference",
      tissue: Object.freeze([...(next?.referenceLayers?.tissue || [])]),
      cell: Object.freeze([...(next?.referenceLayers?.cell || [])]),
      molecular: Object.freeze([...(next?.referenceLayers?.molecular || [])]),
      datasetIds: Object.freeze([...(next?.referenceDatasetIds || [])]),
      limitations: Object.freeze([...(next?.referenceLimitations || [])]),
    });
    window.TestHPReferenceLayers = active;
    window.dispatchEvent(new CustomEvent("testhp:reference-layers-changed", { detail: active }));
    if (window.TestHPSpatialRuntime?.sync) window.TestHPSpatialRuntime.sync();
    return active;
  }

  function activate(projection) {
    return publish(projection || {});
  }

  function clear() {
    return publish({ referenceLayers: { tissue: [], cell: [], molecular: [] }, referenceDatasetIds: [], referenceLimitations: [] });
  }

  window.TestHPReferenceLayerRuntime = { activate, clear, get: () => active };
  window.addEventListener("testhp:reference-layer-projection", (event) => activate(event.detail));
  window.addEventListener("testhp:spatial-layer-changed", () => {
    window.TestHPSpatial?.reference && publish({
      referenceLayers: {
        tissue: window.TestHPSpatial.reference.tissue || [],
        cell: window.TestHPSpatial.reference.cell || [],
        molecular: window.TestHPSpatial.reference.molecular || [],
      },
      referenceDatasetIds: window.TestHPSpatial.reference.datasetIds || [],
      referenceLimitations: window.TestHPSpatial.reference.limitations || [],
    });
  });
})();
