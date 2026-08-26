(() => {
  'use strict';
  const API = '/api/hand/photo-reconstruction';

  // The prepare endpoint returns the identifier inside `prepared_asset`.
  // Normalize that response for the existing preparation UI, which consumes
  // the identifier at the top level. Keep the backend contract unchanged.
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
        const normalized = {
          ...body,
          prepared_asset_id: preparedAsset.prepared_asset_id,
          prepared_asset: preparedAsset
        };
        return new Response(JSON.stringify(normalized), {
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

      // Preparation itself does not require a view. View assignment is a
      // separate prerequisite for registration, so an unassigned source must
      // remain actionable instead of being left behind a disabled button.
      if (unassigned && run) {
        run.disabled = false;
        if (status) {
          status.textContent = 'Widok nieprzypisany — można przygotować zdjęcie; widok przypisz przed rejestracją.';
          status.className = 'hs-prep-status hs-prep-warn';
        }
      }
    } catch {}
  }

  // Allow preparation of an unassigned-view source. The backend preparation
  // contract explicitly permits this (it stores the result as `unassigned`),
  // while view assignment remains a separate step required before registration.
  // The canonical UI previously disabled the button and returned early, even
  // though POST /prepare/:asset_id could successfully create the prepared asset.
  let unassignedPreparationBusy = false;
  const prepareUnassigned = async event => {
    const run = event.target?.closest?.('#hs-prep-run');
    if (!run || unassignedPreparationBusy) return;
    const select = document.getElementById('hs-prep-source');
    const option = select?.selectedOptions?.[0];
    const assetId = select?.value;
    const label = option?.textContent || '';
    const unassigned = /widok nieprzypisany|unassigned/i.test(label);
    if (!assetId || !unassigned) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    unassignedPreparationBusy = true;
    run.disabled = true;

    const status = document.getElementById('hs-prep-status');
    const result = document.getElementById('hs-prep-result');
    if (status) {
      status.textContent = 'Przygotowywanie… (widok można przypisać później)';
      status.className = 'hs-prep-status';
    }

    try {
      const response = await fetch(`${API}/prepare/${encodeURIComponent(assetId)}`, {method:'POST'});
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
      const prepared = body.prepared_asset || body;
      const preparedId = body.prepared_asset_id || prepared.prepared_asset_id;
      if (!preparedId) throw new Error('Brak identyfikatora przygotowanego pliku.');

      const preview = document.getElementById('hs-prep-preview');
      const save = document.getElementById('hs-prep-save');
      if (preview) {
        preview.innerHTML = `<div class="hs-prep-pair"><figure><img src="${API}/file/source/${encodeURIComponent(assetId)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(preparedId)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div>`;
      }
      if (result) {
        result.innerHTML = `<span class="hs-prep-good">✓ Przygotowane</span><br>${prepared.prepared_width || prepared.width || '?'} × ${prepared.prepared_height || prepared.height || '?'} px · widok nieprzypisany`;
      }
      if (save) {
        save.disabled = false;
        save.dataset.id = preparedId;
        save.dataset.source = assetId;
        save.dataset.serverPrepared = '1';
      }
      if (status) {
        status.textContent = '✓ Zdjęcie przygotowane. Przypisz widok przed rejestracją.';
        status.className = 'hs-prep-status hs-prep-good';
      }
      window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
    } catch (error) {
      if (status) {
        status.textContent = error?.message || 'Przygotowanie nie powiodło się.';
        status.className = 'hs-prep-status hs-prep-warn';
      }
      run.disabled = false;
    } finally {
      unassignedPreparationBusy = false;
    }
  };

  // Capture phase prevents the canonical bubble handler from immediately
  // rejecting an unassigned source. Assigned-view sources keep the canonical
  // workflow unchanged.
  document.addEventListener('click', prepareUnassigned, true);

  // Do not schedule from every DOM mutation. The previous body-wide observer
  // created a new 100 ms timeout for essentially every render mutation,
  // including mutations caused by this bridge itself. That produced hundreds
  // of pending timers and a feedback loop in the preparation UI.
  let syncTimer = null;
  const schedule = () => {
    if (syncTimer !== null) return;
    syncTimer = setTimeout(() => {
      syncTimer = null;
      void sync();
    }, 100);
  };

  document.addEventListener('change', e => { if (e.target?.id === 'hs-prep-source') schedule(); });
  window.addEventListener('testhp:evidence-updated', schedule);
  window.addEventListener('testhp:evidence-attached', schedule);

  // Keep dynamic-page support without reacting to unrelated render mutations.
  // In particular, changes to #hs-prep-preview/result/status must not retrigger
  // sync after sync() updates those elements.
  const isPrepSourceNode = node => {
    if (!(node instanceof Element)) return false;
    return node.id === 'hs-prep-source' || !!node.querySelector?.('#hs-prep-source');
  };
  new MutationObserver(mutations => {
    if (mutations.some(m => [...m.addedNodes, ...m.removedNodes].some(isPrepSourceNode))) schedule();
  }).observe(document.body, {childList:true, subtree:true});

  // Geometry is a first-class part of the unified surface workflow. Load the
  // canonical bridge here because this source bridge is already injected by
  // the unified UI on every page load.
  if (!document.getElementById('hand-surface-geometry-canonical-bridge')) {
    const script = document.createElement('script');
    script.id = 'hand-surface-geometry-canonical-bridge';
    script.src = '/digital-twin/hand-surface-geometry-canonical-bridge.js?v=canonical-geometry-2';
    document.head.appendChild(script);
  }

  // The mode switch lives in the same digital-twin bundle. The file already
  // exists on this feature branch; explicitly load it from the public route
  // used by the frontend so the UI can actually expose the two geometry modes.
  if (!document.getElementById('hand-geometry-mode-switch')) {
    const script = document.createElement('script');
    script.id = 'hand-geometry-mode-switch';
    script.src = '/digital-twin/hand-geometry-mode-switch.js?v=geometry-mode-1';
    document.head.appendChild(script);
  }
})();