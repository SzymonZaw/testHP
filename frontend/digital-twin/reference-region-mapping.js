(() => {
  'use strict';
  if (window.__testhpReferenceRegionMappingInstalled) return;
  window.__testhpReferenceRegionMappingInstalled = true;

  const MAPPING_URL = './reference-region-mapping-v1.json';
  let promise;

  async function loadReferenceRegionMapping(url = MAPPING_URL) {
    if (!promise) {
      promise = fetch(url, { credentials: 'same-origin' }).then(response => {
        if (!response.ok) throw new Error(`Reference region mapping unavailable (${response.status})`);
        return response.json();
      }).then(mapping => {
        if (!mapping || typeof mapping !== 'object' || !mapping.assetMappings) {
          throw new Error('Invalid reference region mapping');
        }
        return Object.freeze(mapping);
      });
    }
    return promise;
  }

  function getAssetMapping(mapping, assetId) {
    return mapping?.assetMappings?.[assetId] || null;
  }

  window.testhpReferenceRegionMapping = Object.freeze({
    MAPPING_URL,
    loadReferenceRegionMapping,
    getAssetMapping
  });
})();
