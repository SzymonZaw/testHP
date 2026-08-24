(() => {
  'use strict';

  const PREP_SRC = '/digital-twin/hand-surface-preparation-ui.js';
  const API = '/api/hand/photo-reconstruction';
  const EVIDENCE = 'digitalTwinEvidenceUX.v2';
  const isPrepare = () => document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab === 'prepare';
  const canonicalPresent = () => !!document.querySelector('#hss-content .hs-prep-clean');
  const legacyPresent = () => {
    const c = document.getElementById('hss-content');
    if (!c) return false;
    return !!c.querySelector('#hss-file, #hss-run, #hss-saveprep') || /Waiting for an image|Choose a skin photo|Stage 12 · Image preparation/.test(c.textContent || '');
  };

  let restoring = false;
  function restore() {
    if (restoring || !isPrepare() || canonicalPresent() || !legacyPresent()) return;
    restoring = true;
    const content = document.getElementById('hss-content');
    if (content) {
      content.innerHTML = '';
      delete content.dataset.cleanPreparation;
    }
    const script = document.createElement('script');
    script.src = `${PREP_SRC}?v=prep-clean-owner-3-${Date.now()}`;
    script.dataset.prepOwnerReload = '1';
    script.onload = () => { restoring = false; };
    script.onerror = () => { restoring = false; };
    document.body.appendChild(script);
  }

  async function serverPrepared(assetId) {
    if (!assetId) return null;
    try {
      const r = await fetch(`${API}/state?subject_id=own_cohort&timepoint=T0`, {cache:'no-store'});
      if (!r.ok) return null;
      const body = await r.json();
      return (body.inputs || body.evidence || []).find(e => e.asset_id === assetId) || null;
    } catch { return null; }
  }

  function renderServerPrepared(e) {
    if (!e?.prepared || !e.prepared_asset_id) return false;
    const result = document.getElementById('hs-prep-result');
    const preview = document.getElementById('hs-prep-preview');
    const run = document.getElementById('hs-prep-run');
    const save = document.getElementById('hs-prep-save');
    const status = document.getElementById('hs-prep-status');
    if (!result || !run) return false;
    const id = e.prepared_asset_id;
    if (preview) preview.innerHTML = `<div class="hs-prep-pair"><figure><img src="${API}/file/source/${encodeURIComponent(e.asset_id)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(id)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div>`;
    const p = e.prepared_asset || {};
    result.innerHTML = `<span class="hs-prep-good">✓ Przygotowane</span><br>${p.prepared_width || p.width || '?'} × ${p.prepared_height || p.height || '?'} px · wynik zapisany po stronie serwera`;
    run.disabled = true;
    run.dataset.serverPrepared = '1';
    if (save) {
      save.disabled = false;
      save.dataset.id = id;
      save.dataset.source = e.asset_id;
      save.dataset.serverPrepared = '1';
    }
    if (status) {
      status.textContent = '✓ Zdjęcie jest już przygotowane.';
      status.className = 'hs-prep-status hs-prep-good';
    }
    return true;
  }

  async function reconcileSelection() {
    if (!isPrepare() || !canonicalPresent()) return;
    const select = document.getElementById('hs-prep-source');
    const assetId = select?.value;
    if (!assetId) return;
    const e = await serverPrepared(assetId);
    if (e?.prepared && e.prepared_asset_id) renderServerPrepared(e);
  }

  // The canonical controller can be reloaded more than once. Before its
  // preparation click handler runs, always consult the persisted server state.
  // If the asset is already prepared, never issue another prepare request.
  document.addEventListener('click', async event => {
    if (!isPrepare()) return;
    const run = event.target?.closest?.('#hs-prep-run');
    if (!run || run.dataset.serverPrepared === '1') return;
    const select = document.getElementById('hs-prep-source');
    const assetId = select?.value;
    if (!assetId) return;
    const e = await serverPrepared(assetId);
    if (e?.prepared && e.prepared_asset_id) {
      event.preventDefault();
      event.stopImmediatePropagation();
      renderServerPrepared(e);
    }
  }, true);

  // Keep the persisted prepared state visible after selecting a source.
  document.addEventListener('change', event => {
    if (event.target?.id !== 'hs-prep-source') return;
    setTimeout(reconcileSelection, 0);
  }, true);

  // Save a server-prepared result even when the canonical controller instance
  // that rendered the button does not own the refreshed preparation object.
  document.addEventListener('click', event => {
    const save = event.target?.closest?.('#hs-prep-save[data-server-prepared="1"]');
    if (!save) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const select = document.getElementById('hs-prep-source');
    const assetId = save.dataset.source;
    const preparedId = save.dataset.id;
    const item = select?.selectedOptions?.[0]?.textContent || assetId;
    try {
      const raw = JSON.parse(localStorage.getItem(EVIDENCE) || '{}');
      const evidence = Array.isArray(raw.evidence) ? raw.evidence : [];
      if (!evidence.some(x => x.sourceAssetId === assetId && x.preparedAssetId === preparedId)) {
        const view = (JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.views.v1') || '{}'))[assetId] || null;
        evidence.unshift({id:`prepared-${preparedId}`,type:'Macro',sourceType:'prepared-image',target:'hand/palm',spatial_id:'hand/palm',timepoint:'T0',view,filename:item.split(' · ')[0],sourceAssetId:assetId,preparedAssetId:preparedId,prepared:true,provenance:{sourceAssetId:assetId,preparation:'photo-reconstruction/prepare',originalUnchanged:true},archived:false,history:[{at:new Date().toISOString(),action:'prepared image saved'}]});
        localStorage.setItem(EVIDENCE, JSON.stringify({...raw,evidence,target:'hand/palm'}));
      }
    } catch {}
    window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
  }, true);

  const schedule = () => setTimeout(restore, 0);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:spatial-contract-changed', schedule);
  window.addEventListener('testhp:spatial-target-changed', schedule);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule, {once:true});
  else schedule();

  new MutationObserver(() => {
    if (isPrepare() && legacyPresent() && !canonicalPresent()) schedule();
    if (isPrepare() && canonicalPresent()) reconcileSelection();
  }).observe(document.body, {childList:true, subtree:true});
})();