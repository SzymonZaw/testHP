(() => {
  'use strict';
  const API = '/api/hand/photo-reconstruction';

  // Prepare the public spatial-reference catalog before the surface workflow
  // needs it. References remain provenance-only; they are never user data.
  if (!document.getElementById('spatial-reference-registry')) {
    const script = document.createElement('script');
    script.id = 'spatial-reference-registry';
    script.src = '/digital-twin/spatial-reference-registry.js?v=reference-catalog-1';
    document.head.appendChild(script);
  }

  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const response = await nativeFetch(...args);
    const input = args[0];
    const url = typeof input === 'string' ? input : input?.url || '';
    if (!url.includes(`${API}/prepare/`)) return response;
    try {
      const body = await response.clone().json();
      const preparedAsset = body?.prepared_asset;
      if (!body?.prepared_asset_id && preparedAsset?.prepared_asset_id) {
        return new Response(JSON.stringify({ ...body, prepared_asset_id: preparedAsset.prepared_asset_id, prepared_asset: preparedAsset }), {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers
        });
      }
    } catch {}
    return response;
  };

  const clean = value => String(value ?? '').replace(/[&<>\"']/g, '');
  async function sync() {
    const active = document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;
    const select = document.getElementById('hs-prep-source');
    if (active !== 'prepare' || !select?.value) return;
    const run = document.getElementById('hs-prep-run');
    const status = document.getElementById('hs-prep-status');
    const option = select.selectedOptions?.[0];
    const unassigned = /widok nieprzypisany|unassigned/i.test(option?.textContent || '');
    try {
      const r = await fetch(`${API}/state?subject_id=own_cohort&timepoint=T0`, {cache:'no-store'});
      if (!r.ok) return;
      const state = await r.json();
      const item = (state.inputs || state.evidence || []).find(x => x?.asset_id === select.value || x?.id === select.value || x?.sourceAssetId === select.value);
      if (item?.prepared && item.prepared_asset_id) {
        const result = document.getElementById('hs-prep-result');
        const preview = document.getElementById('hs-prep-preview');
        const save = document.getElementById('hs-prep-save');
        if (preview) preview.innerHTML = `<div class="hs-prep-pair"><figure><img src="${API}/file/source/${encodeURIComponent(select.value)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(item.prepared_asset_id)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div>`;
        if (result) result.innerHTML = `<span class="hs-prep-good">✓ Przygotowane</span><br>Identyfikator przygotowanego pliku: <code>${clean(item.prepared_asset_id)}</code>`;
        if (run) run.disabled = true;
        if (save) { save.disabled = false; save.dataset.id = item.prepared_asset_id; save.dataset.source = select.value; }
        if (status) { status.textContent = unassigned ? '✓ Zdjęcie jest już przygotowane. Przypisz widok przed rejestracją.' : '✓ Zdjęcie jest już przygotowane.'; status.className = 'hs-prep-status hs-prep-good'; }
        return;
      }
      if (unassigned && run) {
        run.disabled = false;
        if (status) { status.textContent = 'Widok nieprzypisany — można przygotować zdjęcie; widok przypisz przed rejestracją.'; status.className = 'hs-prep-status hs-prep-warn'; }
      }
    } catch {}
  }

  let unassignedPreparationBusy = false;
  const prepareUnassigned = async event => {
    const run = event.target?.closest?.('#hs-prep-run');
    if (!run || unassignedPreparationBusy) return;
    const select = document.getElementById('hs-prep-source');
    const option = select?.selectedOptions?.[0];
    const assetId = select?.value;
    const unassigned = !!assetId && /widok nieprzypisany|unassigned/i.test(option?.textContent || '');
    if (!unassigned) return;
    event.preventDefault(); event.stopImmediatePropagation(); unassignedPreparationBusy = true; run.disabled = true;
    const status = document.getElementById('hs-prep-status');
    const result = document.getElementById('hs-prep-result');
    if (status) { status.textContent = 'Przygotowywanie… (widok można przypisać później)'; status.className = 'hs-prep-status'; }
    try {
      const response = await fetch(`${API}/prepare/${encodeURIComponent(assetId)}`, {method:'POST'});
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
      const prepared = body.prepared_asset || body;
      const preparedId = body.prepared_asset_id || prepared.prepared_asset_id;
      if (!preparedId) throw new Error('Brak identyfikatora przygotowanego pliku.');
      const preview = document.getElementById('hs-prep-preview');
      const save = document.getElementById('hs-prep-save');
      if (preview) preview.innerHTML = `<div class="hs-prep-pair"><figure><img src="${API}/file/source/${encodeURIComponent(assetId)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(preparedId)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div>`;
      if (result) result.innerHTML = `<span class="hs-prep-good">✓ Przygotowane</span><br>${prepared.prepared_width || prepared.width || '?'} × ${prepared.prepared_height || prepared.height || '?'} px · widok nieprzypisany`;
      if (save) { save.disabled = false; save.dataset.id = preparedId; save.dataset.source = assetId; save.dataset.serverPrepared = '1'; }
      if (status) { status.textContent = '✓ Zdjęcie przygotowane. Przypisz widok przed rejestracją.'; status.className = 'hs-prep-status hs-prep-good'; }
      window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
    } catch (error) {
      if (status) { status.textContent = error?.message || 'Przygotowanie nie powiodło się.'; status.className = 'hs-prep-status hs-prep-warn'; }
      run.disabled = false;
    } finally { unassignedPreparationBusy = false; }
  };

  document.addEventListener('click', prepareUnassigned, true);
  let syncTimer = null;
  const schedule = () => { if (syncTimer !== null) return; syncTimer = setTimeout(() => { syncTimer = null; void sync(); }, 100); };
  document.addEventListener('change', e => { if (e.target?.id === 'hs-prep-source') schedule(); });
  window.addEventListener('testhp:evidence-updated', schedule);
  window.addEventListener('testhp:evidence-attached', schedule);
  const isPrepSourceNode = node => node instanceof Element && (node.id === 'hs-prep-source' || !!node.querySelector?.('#hs-prep-source'));
  new MutationObserver(mutations => { if (mutations.some(m => [...m.addedNodes, ...m.removedNodes].some(isPrepSourceNode))) schedule(); }).observe(document.body, {childList:true, subtree:true});
  const prepButtonObserver = new MutationObserver(() => {
    const select = document.getElementById('hs-prep-source'); const run = document.getElementById('hs-prep-run'); const option = select?.selectedOptions?.[0];
    if (!select?.value || !run || !/widok nieprzypisany|unassigned/i.test(option?.textContent || '')) return;
    if (run.disabled && !unassignedPreparationBusy) { run.disabled = false; const status = document.getElementById('hs-prep-status'); if (status && !/przygotowane|Przygotowywanie/i.test(status.textContent || '')) { status.textContent = 'Widok nieprzypisany — można przygotować zdjęcie; widok przypisz przed rejestracją.'; status.className = 'hs-prep-status hs-prep-warn'; } }
  });
  prepButtonObserver.observe(document.body, {attributes:true, attributeFilter:['disabled'], subtree:true});

  if (!document.getElementById('hand-surface-geometry-canonical-bridge')) {
    const script = document.createElement('script'); script.id = 'hand-surface-geometry-canonical-bridge'; script.src = '/digital-twin/hand-surface-geometry-canonical-bridge.js?v=canonical-geometry-2'; document.head.appendChild(script);
  }
  if (!document.getElementById('hand-geometry-mode-switch')) {
    const script = document.createElement('script'); script.id = 'hand-geometry-mode-switch'; script.src = '/digital-twin/hand-geometry-mode-switch.js?v=geometry-mode-1'; document.head.appendChild(script);
  }
})();
