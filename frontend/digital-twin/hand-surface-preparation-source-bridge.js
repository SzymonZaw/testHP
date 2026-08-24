(() => {
  'use strict';
  const API = '/api/hand/photo-reconstruction';
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
})();
