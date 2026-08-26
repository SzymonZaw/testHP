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
    try {
      const r = await fetch(`${API}/state?subject_id=own_cohort&timepoint=T0`, {cache:'no-store'});
      if (!r.ok) return;
      const state = await r.json();
      const item = (state.inputs || state.evidence || []).find(x => x?.asset_id === select.value || x?.id === select.value || x?.sourceAssetId === select.value);
      if (!item?.prepared || !item.prepared_asset_id) return;
      const result = document.getElementById('hs-prep-result');
      const preview = document.getElementById('hs-prep-preview');
      const run = document.getElementById('hs-prep-run');
      const save = document.getElementById('hs-prep-save');
      const status = document.getElementById('hs-prep-status');
      if (preview) preview.innerHTML = `<div class="hs-prep-pair"><figure><img src="${API}/file/source/${encodeURIComponent(select.value)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(item.prepared_asset_id)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div>`;
      if (result) result.innerHTML = `<span class="hs-prep-good">✓ Przygotowane</span><br>Identyfikator przygotowanego pliku: <code>${clean(item.prepared_asset_id)}</code>`;
      if (run) run.disabled = true;
      if (save) { save.disabled = false; save.dataset.id = item.prepared_asset_id; save.dataset.source = select.value; }
      if (status) { status.textContent = '✓ Zdjęcie jest już przygotowane.'; status.className = 'hs-prep-status hs-prep-good'; }
    } catch {}
  }
  const schedule = () => setTimeout(sync, 100);
  document.addEventListener('change', e => { if (e.target?.id === 'hs-prep-source') schedule(); });
  window.addEventListener('testhp:evidence-updated', schedule);
  window.addEventListener('testhp:evidence-attached', schedule);
  new MutationObserver(() => schedule()).observe(document.body, {childList:true, subtree:true});

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
