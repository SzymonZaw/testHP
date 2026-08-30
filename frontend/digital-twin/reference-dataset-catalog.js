(() => {
  const CATALOG_URL = './reference-dataset-catalog-v1.json';

  function normalizeDataset(dataset) {
    return Object.freeze({
      ...dataset,
      sourceUrl: dataset.url,
      referenceOnly: true
    });
  }

  async function loadReferenceDatasetCatalog(url = CATALOG_URL) {
    const response = await fetch(url, { credentials: 'same-origin' });
    if (!response.ok) {
      throw new Error(`Reference dataset catalog unavailable (${response.status})`);
    }

    const catalog = await response.json();
    if (!catalog || !Array.isArray(catalog.datasets)) {
      throw new Error('Invalid reference dataset catalog');
    }

    return Object.freeze({
      ...catalog,
      datasets: Object.freeze(catalog.datasets.map(normalizeDataset))
    });
  }

  window.testhpReferenceDatasetCatalog = Object.freeze({
    CATALOG_URL,
    loadReferenceDatasetCatalog
  });
})();
