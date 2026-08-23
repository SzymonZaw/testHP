(() => {
  'use strict';

  const API = '/api/hand/photo-reconstruction';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const LABELS = { front: 'Przód', back: 'Tył', side_left: 'Lewa strona', side_right: 'Prawa strona', thumb: 'Kciuk' };
  const target = () => String(window.testhpSpatialContract?.getTarget?.()?.spatial_id || window.testhpSpatialContract?.getTarget?.() || window.spatialEvidenceTarget || document.body?.dataset?.spatialTarget || 'hand');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
  let state = { inputs: [] };
  let observer;

  async function request(path, options) {
    const r = await fetch(`${API}${path}`, options);
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(body.detail || `Request failed (${r.status})`);
    return body;
  }

  async function load() {
    const s = await request('/state?subject_id=own_cohort&timepoint=T0');
    state.inputs = (s.inputs || []).filter(x => String(x.spatial_id || x.spatialId || x.target || target()) === target());
  }

  function ensureStyles() {
    if (document.getElementById('hs-prep-clean-css')) return;
    const s = document.createElement('style');
    s.id = 'hs-prep-clean-css';
    s.textContent = `.hs-prep-clean{display:grid;grid-template-columns:1.1fr .9fr;gap:14px}.hs-prep-box{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)}.hs-prep-select{width:100%;padding:8px;border:1px solid var(--border,#d8dee8);border-radius:8px;background:var(--panel,#fff);color:inherit}.hs-prep-preview{margin-top:10px;min-height:220px;border:1px dashed var(--border,#d8dee8);border-radius:10px;display:grid;place-items:center;overflow:hidden;background:#f7f8fa}.hs-prep-preview img{max-width:100%;max-height:320px;object-fit:contain}.hs-prep-pair{display:grid;grid-template-columns:1fr 1fr;gap:8px}.hs-prep-pair figure{margin:0}.hs-prep-pair img{width:100%;height:220px;object-fit:contain;background:#f7f8fa;border-radius:8px}.hs-prep-pair figcaption{font-size:11px;color:#667085;margin-top:4px}.hs-prep-meta{font-size:12px;color:#667085;line-height:1.5;margin:8px 0}.hs-prep-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.hs-prep-status{margin-top:10px;font-size:12px}.hs-prep-good{color:#1f6b45}.hs-prep-warn{color:#9a6700}.hs-prep-clean details{margin-top:12px}.hs-prep-clean details label{display:block;margin:8px 0;font-size:12px}.hs-prep-clean input{max-width:120px}`;
    document.head.appendChild(s);
  }

  function sourceOptions() {
    return state.inputs.filter(x => !x.archived).map(x => `<option value="${esc(x.asset_id)}">${esc(x.filename || x.asset_id)} · ${esc(LABELS[x.view] || x.view || 'widok nieprzypisany')}</option>`).join('');
  }

  function replacePrepare() {
    const content = document.getElementById('hss-content');
    const active = document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;
    if (!content || active !== 'prepare') return;
    if (content.dataset.cleanPreparation === '1') return;
    content.dataset.cleanPreparation = '1';
    content.innerHTML = `<div class="hs-prep-clean">
      <div class="hs-prep-box">
        <strong>Zdjęcie źródłowe</strong>
        <p class="hss-note">Wybierz zdjęcie zapisane wcześniej w „Zdjęcia / źródła”. Oryginał nie zostanie zmieniony.</p>
        <select id="hs-prep-source" class="hs-prep-select"><option value="">Wybierz zapisane zdjęcie…</option>${sourceOptions()}</select>
        <div id="hs-prep-meta" class="hs-prep-meta"></div>
        <div id="hs-prep-preview" class="hs-prep-preview"><span class="hss-note">Wybierz zdjęcie, aby rozpocząć.</span></div>
        <div class="hs-prep-actions"><button id="hs-prep-run" class="primary" disabled>Przygotuj zdjęcie</button></div>
      </div>
      <div class="hs-prep-box">
        <strong>Przygotowanie</strong>
        <p class="hss-note">System automatycznie usuwa tło, tworzy miękką maskę, przycina pusty obszar i zachowuje informacje potrzebne do późniejszej rejestracji.</p>
        <div id="hs-prep-result" class="hs-prep-meta">Brak przygotowanego wyniku.</div>
        <details><summary>Opcje zaawansowane</summary>
          <label>Tolerancja tła <input id="hs-prep-tol" type="number" min="4" max="80" value="28"></label>
          <label>Maksymalny wymiar <input id="hs-prep-max" type="number" min="1024" max="8192" value="4096"></label>
        </details>
        <div class="hs-prep-actions"><button id="hs-prep-save" disabled>Zapisz przygotowane zdjęcie</button></div>
        <div id="hs-prep-status" class="hs-prep-status" role="status"></div>
      </div>
    </div>`;

    const select = document.getElementById('hs-prep-source');
    const meta = document.getElementById('hs-prep-meta');
    const preview = document.getElementById('hs-prep-preview');
    const result = document.getElementById('hs-prep-result');
    const run = document.getElementById('hs-prep-run');
    const save = document.getElementById('hs-prep-save');
    let prepared = null;

    const selected = () => state.inputs.find(x => x.asset_id === select.value);
    const update = () => {
      const item = selected();
      run.disabled = !item;
      if (!item) { meta.textContent = ''; preview.innerHTML = '<span class="hss-note">Wybierz zdjęcie, aby rozpocząć.</span>'; return; }
      const spatial = item.spatial_id || item.spatialId || item.target || target();
      meta.innerHTML = `<strong>Cel:</strong> <code>${esc(spatial)}</code> · <strong>Widok:</strong> ${esc(LABELS[item.view] || item.view || 'nieprzypisany')} · <strong>Czas:</strong> ${esc(item.timepoint || 'T0')}`;
      if (item.prepared && item.prepared_asset_id) {
        result.innerHTML = '<span class="hs-prep-good">✓ To zdjęcie jest już przygotowane.</span>';
        preview.innerHTML = `<img src="${API}/file/prepared/${encodeURIComponent(item.prepared_asset_id)}" alt="Przygotowane zdjęcie">`;
      } else {
        result.textContent = 'Zdjęcie nie jest jeszcze przygotowane.';
        preview.innerHTML = '<span class="hss-note">Podgląd pojawi się po przygotowaniu.</span>';
      }
    };

    select.onchange = update;
    run.onclick = async () => {
      const item = selected();
      if (!item) return;
      const spatial = item.spatial_id || item.spatialId || item.target || target();
      const status = document.getElementById('hs-prep-status');
      if (spatial !== target()) { status.textContent = `Zdjęcie należy do innego celu: ${spatial}.`; status.className = 'hs-prep-status hs-prep-warn'; return; }
      run.disabled = true; status.textContent = 'Przygotowywanie…'; status.className = 'hs-prep-status';
      try {
        prepared = await request(`/prepare/${encodeURIComponent(item.asset_id)}`, { method:'POST' });
        const id = prepared.prepared_asset_id;
        if (!id) throw new Error('Brak identyfikatora przygotowanego pliku.');
        preview.innerHTML = `<div style="width:100%"><div class="hs-prep-pair"><figure><img src="${API}/file/source/${encodeURIComponent(item.asset_id)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(id)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div></div>`;
        result.innerHTML = `<span class="hs-prep-good">✓ Przygotowane</span><br>Rozmiar: ${prepared.prepared_width || '?'} × ${prepared.prepared_height || '?'} px<br>Crop: zachowany<br>Jakość: ${prepared.quality?.overall ?? '—'}`;
        save.disabled = false; save.dataset.id = id; save.dataset.source = item.asset_id;
        status.textContent = '✓ Gotowe. Oryginał pozostał niezmieniony.'; status.className = 'hs-prep-status hs-prep-good';
        item.prepared = true; item.prepared_asset_id = id; item.prepared_path = prepared.prepared_path; item.quality = prepared.quality; item.crop = prepared.crop;
      } catch (e) { status.textContent = e.message || 'Nie udało się przygotować zdjęcia.'; status.className = 'hs-prep-status hs-prep-warn'; run.disabled = false; }
    };

    save.onclick = () => {
      const item = selected();
      if (!item || !prepared) return;
      const evidenceKey = 'digitalTwinEvidenceUX.v2';
      try {
        const raw = JSON.parse(localStorage.getItem(evidenceKey) || '{}');
        const evidence = Array.isArray(raw.evidence) ? raw.evidence : [];
        const existing = evidence.find(x => x.sourceAssetId === item.asset_id && x.preparedAssetId === prepared.prepared_asset_id);
        if (!existing) evidence.unshift({ id:`prepared-${prepared.prepared_asset_id}`, type:'Macro', sourceType:'prepared-image', target:target(), spatial_id:target(), timepoint:item.timepoint || 'T0', view:item.view, filename:item.filename, sourceAssetId:item.asset_id, preparedAssetId:prepared.prepared_asset_id, prepared:true, quality:prepared.quality, crop:prepared.crop, provenance:{sourceAssetId:item.asset_id, preparation:'photo-reconstruction/prepare', originalUnchanged:true}, archived:false, history:[{at:new Date().toISOString(),action:'prepared image saved'}] });
        localStorage.setItem(evidenceKey, JSON.stringify({ ...raw, evidence, target:target() }));
      } catch {}
      document.getElementById('hs-prep-status').textContent = '✓ Przygotowane zdjęcie zapisane i gotowe do rejestracji.';
      document.getElementById('hs-prep-status').className = 'hs-prep-status hs-prep-good';
      window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
    };
    update();
  }

  async function boot() {
    ensureStyles();
    try { await load(); } catch { state.inputs = []; }
    replacePrepare();
  }

  function watch() {
    if (observer) return;
    observer = new MutationObserver(() => {
      const active = document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;
      const content = document.getElementById('hss-content');
      if (active === 'prepare' && content && content.dataset.cleanPreparation !== '1') boot();
      if (active !== 'prepare' && content) delete content.dataset.cleanPreparation;
    });
    observer.observe(document.body, { childList:true, subtree:true });
  }

  window.addEventListener('testhp:spatial-contract-changed', () => { const c=document.getElementById('hss-content'); if(c) delete c.dataset.cleanPreparation; boot(); });
  window.addEventListener('testhp:spatial-layer-changed', () => { const c=document.getElementById('hss-content'); if(c) delete c.dataset.cleanPreparation; boot(); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => { watch(); boot(); }, {once:true}); else { watch(); boot(); }
})();
