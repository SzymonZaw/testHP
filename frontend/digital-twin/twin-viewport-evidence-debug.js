// TWIN VIEWPORT · DEBUG — evidence target diagnostics
// Diagnostic-only helper. Does not mutate production evidence records.
(function () {
  'use strict';

  function canonicalize(value) {
    if (value == null) return null;
    const raw = String(value).trim();
    if (!raw) return null;
    if (raw === 'hand/palm' || raw === 'Śródręcze' || raw === 'Palm' || raw === 'palm') return 'hand/palm';
    return raw;
  }

  function getValue(record, keys) {
    for (const key of keys) {
      if (record && record[key] != null && String(record[key]).trim() !== '') return record[key];
    }
    return null;
  }

  window.testhpEvidenceTargetDebug = function (records, currentTarget) {
    const list = Array.isArray(records) ? records : [];
    const current = canonicalize(currentTarget);
    const samples = list.slice(0, 10).map((record, index) => {
      const spatialId = getValue(record, ['spatial_id', 'spatialId']);
      const target = getValue(record, ['target']);
      const region = getValue(record, ['region', 'regionId', 'region_id']);
      const canonicalCandidates = [spatialId, target, region].map(canonicalize).filter(Boolean);
      const linked = current != null && canonicalCandidates.includes(current);
      return {
        index: index + 1,
        spatial_id: spatialId,
        spatialId,
        target,
        region,
        canonicalCandidates,
        linked
      };
    });

    const linkedCount = list.reduce((count, record) => {
      const values = ['spatial_id', 'spatialId', 'target', 'region', 'regionId', 'region_id']
        .map(key => record && record[key])
        .filter(v => v != null && String(v).trim() !== '')
        .map(canonicalize);
      return count + (current != null && values.includes(current) ? 1 : 0);
    }, 0);

    const output = {
      currentTarget: {
        raw: currentTarget,
        canonical: current
      },
      total: list.length,
      linkedCount,
      matchStrategy: 'canonical spatial_id / spatialId / target / region fields',
      samples
    };

    window.__testhpEvidenceTargetDebug = output;
    return output;
  };
})();
