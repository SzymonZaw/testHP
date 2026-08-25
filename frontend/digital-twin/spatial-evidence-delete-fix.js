(() => {
  'use strict';

  if (window.__testhpSpatialEvidenceDeleteFix) return;
  window.__testhpSpatialEvidenceDeleteFix = true;

  const STORAGE = 'digitalTwinEvidenceUX.v2';

  const readStore = () => {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      return value && typeof value === 'object' ? value : {};
    } catch {
      return {};
    }
  };

  const evidenceIdOf = item => item?.backendEvidenceId || item?.backend_evidence_id || item?.evidence_id || null;
  const assetIdOf = item => item?.backendAssetId || item?.backend_asset_id || item?.asset_id || item?.sourceAssetId || null;

  const findItem = token => {
    const items = Array.isArray(readStore().evidence) ? readStore().evidence : [];
    return items.find(item => item?.id === token || evidenceIdOf(item) === token || assetIdOf(item) === token) || null;
  };

  const removeLocal = (item, token) => {
    try {
      const store = readStore();
      if (!Array.isArray(store.evidence)) return;
      const evidenceId = evidenceIdOf(item);
      const assetId = assetIdOf(item);
      const filtered = store.evidence.filter(x => {
        const sameToken = x?.id === token || evidenceIdOf(x) === token || assetIdOf(x) === token;
        const sameEvidence = evidenceId && evidenceIdOf(x) === evidenceId;
        const sameAsset = assetId && assetIdOf(x) === assetId;
        return !(sameToken || sameEvidence || sameAsset);
      });
      localStorage.setItem(STORAGE, JSON.stringify({ ...store, evidence: filtered }));
    } catch (error) {
      console.warn('[Twin] failed to update local evidence cache after delete', error);
    }
  };

  const deleteCanonical = async (token) => {
    const item = findItem(token);
    const evidenceId = evidenceIdOf(item) || (/^evidence[_-]/i.test(token) ? token : null);
    const assetId = assetIdOf(item) || (/^asset[_-]/i.test(token) ? token : null);

    if (!evidenceId && !assetId) {
      removeLocal(item, token);
      return;
    }

    const params = new URLSearchParams();
    if (evidenceId) params.set('evidence_id', evidenceId);
    if (assetId) params.set('asset_id', assetId);

    const response = await fetch(`/api/spatial/evidence?${params.toString()}`, {
      method: 'DELETE',
      cache: 'no-store',
      keepalive: true,
    });

    if (!response.ok && response.status !== 404) {
      const body = await response.text().catch(() => '');
      throw new Error(body || `HTTP ${response.status}`);
    }

    removeLocal(item, token);
    window.dispatchEvent(new CustomEvent('testhp:evidence-registry-deleted', {
      detail: { evidence_id: evidenceId, asset_id: assetId, source: 'delete-button' }
    }));
    window.dispatchEvent(new CustomEvent('testhp:evidence-ux-refresh', {
      detail: { source: 'canonical-delete-button', evidence_id: evidenceId, asset_id: assetId }
    }));
  };

  document.addEventListener('click', event => {
    const button = event.target?.closest?.('[data-archive]');
    if (!button) return;

    const token = button.getAttribute('data-archive');
    if (!token) return;

    event.preventDefault();
    event.stopImmediatePropagation();

    button.disabled = true;
    deleteCanonical(token)
      .then(() => button.closest('.hss-item')?.remove())
      .catch(error => {
        button.disabled = false;
        console.error('[Twin] spatial evidence delete failed', error);
      });
  }, true);
})();
