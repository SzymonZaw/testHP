(() => {
  'use strict';

  const KEY = '__testhpEvidencePipelineV2';
  if (window[KEY]) return;

  const contract = () => window.__testhpDigitalTwinDataContractV2;
  const VALID_MODES = ['macro', 'tissue', 'cellular', 'molecular'];

  function register(input = {}) {
    if (!contract()) throw new Error('Digital twin data contract v2 is not loaded');
    const item = contract().evidence(input);
    return item;
  }

  function forTarget(records = [], spatialId) {
    return records.filter(item => item?.target?.spatialId === spatialId);
  }

  function availability(records = [], spatialId, modality = null) {
    const items = forTarget(records, spatialId).filter(item => !modality || item.modality === modality);
    return {
      count: items.length,
      available: items.some(item => ['available', 'verified'].includes(item.status)),
      verified: items.some(item => item.status === 'verified'),
      real: items.some(item => item.source === 'real'),
      items
    };
  }

  function summarize(records = [], spatialId) {
    const items = forTarget(records, spatialId);
    return VALID_MODES.reduce((result, modality) => {
      const modeItems = items.filter(item => item.modality === modality);
      result[modality] = {
        count: modeItems.length,
        available: modeItems.some(item => ['available', 'verified'].includes(item.status)),
        real: modeItems.some(item => item.source === 'real')
      };
      return result;
    }, {});
  }

  function resolve(records = [], spatialId) {
    return records.filter(item => item?.target?.spatialId === spatialId).sort((a, b) => {
      const score = item => (item.source === 'real' ? 4 : item.source === 'computed' ? 3 : item.source === 'simulated' ? 2 : 1) + (item.status === 'verified' ? 2 : item.status === 'available' ? 1 : 0);
      return score(b) - score(a);
    });
  }

  const api = Object.freeze({ register, forTarget, availability, summarize, resolve });
  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:evidence-pipeline-v2-ready'));
})();
