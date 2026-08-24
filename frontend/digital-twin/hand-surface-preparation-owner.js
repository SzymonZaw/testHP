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
    script.src = `${PREP_SRC}?v=prep-clean-owner-4-${Date.now()}`;
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

  const defaultFilename = e => {
    const source = String(e?.filename || 'prepared-image').trim();
    const base = source.replace(/\.[^.]+$/, '') || 'prepared-image';
    return `${base}_prepared.png`;
  };

  const ensureFilenameField = () => {
    if (!canonicalPresent()) return;
    const save = document.getElementById('hs-prep-save');
    if (!save || document.getElementById('hs-prep-filename')) return;
    const wrap = document.createElement('label');
    wrap.id = 'hs-prep-filename-wrap';
    wrap.style.cssText = 'display:block;margin-top:12px;font-size:12px;color:#667085;line-height:1.5';
    wrap.innerHTML = 'Nazwa zapisywanego pliku <input id="hs-prep-filename" type="text" maxlength="180" autocomplete="off" style="display:block;width:100%;max-width:360px;margin-top:6px;padding:8px;border:1px solid var(--border,#d8dee8);border-radius:8px;background:var(--panel,#fff);color:inherit;box-sizing:border-box">';
    save.parentElement?.insertBefore(wrap, save);
  };

  const selectedFilename = () => {
    const input = document.getElementById('hs-prep-filename');
    const value = input?.value?.trim();
    if (!value) return null;
    const normalized = value.replace(/[\\/:*?"<>|]+/g, '_').replace(/\s+/g, ' ').trim();
    if (!normalized) return null;
    return /\.[A-Za-z0-9]{1,8}$/.test(normalized) ? normalized : `${normalized}.png`;
  };

  const syncFilenameDefault = e => {
    const input = document.getElementById('hs-prep-filename');
    if (!input || input.dataset.userEdited === '1') return;
    input.value = defaultFilename(e);
  };

  function renderServerPrepared(e) {
    if (!e?.prepared || !e.prepared_asset_id) return false;
    ensureFilenameField();
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
    syncFilenameDefault(e);
    if (status) {
      status.textContent = '✓ Zdjęcie jest już przygotowane.';
      status.className = 'hs-prep-status hs-prep-good';
    }
    return true;
  }

  async function reconcileSelection() {
    if (!isPrepare() || !canonicalPresent()) return;
    ensureFilenameField();
    const select = document.getElementById('hs-prep-source');
    const assetId = select?.value;
    if (!assetId) return;
    const e = await serverPrepared(assetId);
    if (e?.prepared && e.prepared_asset_id) renderServerPrepared(e);
    else {
      const input = document.getElementById('hs-prep-filename');
      const selected = select.selectedOptions?.[0]?.textContent?.split(' · ')[0];
      if (input && input.dataset.userEdited !== '1' && selected) input.value = defaultFilename({filename:selected});
    }
  }

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

  document.addEventListener('change', event => {
    if (event.target?.id !== 'hs-prep-source') return;
    const input = document.getElementById('hs-prep-filename');
    if (input) delete input.dataset.userEdited;
    setTimeout(reconcileSelection, 0);
  }, true);

  document.addEventListener('input', event => {
    if (event.target?.id === 'hs-prep-filename') event.target.dataset.userEdited = '1';
  }, true);

  document.addEventListener('click', event => {
    const save = event.target?.closest?.('#hs-prep-save');
    if (!save) return;
    const filename = selectedFilename();
    if (!filename) return;
    const assetId = save.dataset.source;
    const preparedId = save.dataset.id;
    if (save.dataset.serverPrepared === '1') {
      event.preventDefault();
      event.stopImmediatePropagation();
      const item = document.getElementById('hs-prep-source')?.selectedOptions?.[0]?.textContent || assetId;
      try {
        const raw = JSON.parse(localStorage.getItem(EVIDENCE) || '{}');
        const evidence = Array.isArray(raw.evidence) ? raw.evidence : [];
        const existing = evidence.find(x => x.sourceAssetId === assetId && x.preparedAssetId === preparedId);
        if (existing) existing.filename = filename;
        else {
          const view = (JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.views.v1') || '{}'))[assetId] || null;
          evidence.unshift({id:`prepared-${preparedId}`,type:'Macro',sourceType:'prepared-image',target:'hand/palm',spatial_id:'hand/palm',timepoint:'T0',view,filename,sourceAssetId:assetId,preparedAssetId:preparedId,prepared:true,provenance:{sourceAssetId:assetId,preparation:'photo-reconstruction/prepare',originalUnchanged:true},archived:false,history:[{at:new Date().toISOString(),action:'prepared image saved'}]});
        }
        localStorage.setItem(EVIDENCE, JSON.stringify({...raw,evidence,target:'hand/palm'}));
      } catch {}
      window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
      return;
    }

    // The canonical controller owns ordinary saves. Rename the evidence it
    // creates immediately after its handler has persisted it.
    setTimeout(() => {
      try {
        const raw = JSON.parse(localStorage.getItem(EVIDENCE) || '{}');
        const evidence = Array.isArray(raw.evidence) ? raw.evidence : [];
        const match = [...evidence].reverse().find(x =>
          (preparedId && (x.preparedAssetId === preparedId || x.prepared_asset_id === preparedId)) ||
          (assetId && (x.sourceAssetId === assetId || x.asset_id === assetId))
        );
        if (match) {
          match.filename = filename;
          localStorage.setItem(EVIDENCE, JSON.stringify({...raw,evidence}));
          window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
        }
      } catch {}
    }, 0);
  }, true);

  const schedule = () => setTimeout(() => { ensureFilenameField(); restore(); }, 0);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:spatial-contract-changed', schedule);
  window.addEventListener('testhp:spatial-target-changed', schedule);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule, {once:true});
  else schedule();

  new MutationObserver(() => {
    if (isPrepare() && legacyPresent() && !canonicalPresent()) schedule();
    if (isPrepare() && canonicalPresent()) { ensureFilenameField(); reconcileSelection(); }
  }).observe(document.body, {childList:true, subtree:true});
})();