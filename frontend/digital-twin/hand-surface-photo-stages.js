(() => {
  const API = '/api/hand/photo-reconstruction';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const LABELS = { front: 'Front', back: 'Back', side_left: 'Lewa strona', side_right: 'Prawa strona', thumb: 'Kciuk' };
  const PHOTO_SCOPE = 'digitalTwinPhotoSpatialScope.v1';
  const $ = id => document.getElementById(id);
  const canonicalTarget = value => {
    const shared = window.testhpSpatialContract?.canonicalTargetId;
    const raw = typeof value === 'string' ? value : value?.spatial_id || value?.spatialId || value?.target || value?.spatialTarget || null;
    if (!raw) return 'hand';
    return typeof shared === 'function' ? (shared(raw) || 'hand') : String(raw).replace(/^\/+|\/+$/g, '').toLowerCase();
  };
  const target = () => ({
    subject_id: window.testhpPhotoReconstructionSubject || 'own_cohort',
    timepoint: window.testhpPhotoReconstructionTimepoint || 'T0',
    spatial_id: canonicalTarget(window.testhpSpatialContract?.getTarget?.() || window.spatialEvidenceTarget || window.selectedSpatialNode || document.body?.dataset?.spatialTarget || 'hand')
  });
  const readScope = () => {
    try { return JSON.parse(localStorage.getItem(PHOTO_SCOPE) || '{}'); } catch { return {}; }
  };
  const writeScope = value => localStorage.setItem(PHOTO_SCOPE, JSON.stringify(value));
  const rememberAssetTarget = (assetId, spatialId) => {
    if (!assetId) return;
    const scope = readScope();
    scope[assetId] = canonicalTarget(spatialId);
    writeScope(scope);
  };
  const assetTarget = item => canonicalTarget(item?.spatial_id || item?.spatialId || item?.target || readScope()[item?.asset_id] || item?.spatialTarget || 'hand');
  const filterScopedInputs = (inputs, spatialId) => {
    const scope = readScope();
    return (Array.isArray(inputs) ? inputs : []).filter(item => canonicalTarget(item?.spatial_id || item?.spatialId || scope[item?.asset_id] || 'hand') === spatialId);
  };
  let current = null;
  let syncing = false;

  function css() {
    if ($('photo-stage-1-5-css')) return;
    const style = document.createElement('style');
    style.id = 'photo-stage-1-5-css';
    style.textContent = `.p3r-upload{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0 12px}.p3r-upload input{display:none}.p3r-upload-label{display:inline-flex;align-items:center;gap:7px;cursor:pointer}.p3r-mini{font-size:12px;color:var(--muted,#667085)}.p3r-row{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center}.p3r-row-main{min-width:0}.p3r-file{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.p3r-select{width:100%;margin-top:6px;padding:6px 8px;border:1px solid var(--border,#d8dee8);border-radius:7px;background:var(--panel,#fff);color:inherit}.p3r-item-actions{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:7px}.p3r-preview{width:56px;height:56px;object-fit:cover;border-radius:7px;border:1px solid var(--border,#d8dee8);background:#f2f4f7}.p3r-stage-summary{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}.p3r-stage-chip{padding:5px 8px;border-radius:999px;background:rgba(79,111,143,.08);font-size:11px}.p3r-stage-chip.good{color:#1f6b45;background:rgba(31,107,69,.08)}.p3r-stage-chip.warn{color:#9a6700;background:rgba(154,103,0,.08)}.p3r-user-note{margin:8px 0;padding:9px 11px;border-radius:9px;background:rgba(79,111,143,.06);font-size:12px;color:#667085;line-height:1.45}.p3r-preview-label{margin:0 0 8px;font-size:12px;font-weight:800;color:#53616c;text-transform:uppercase;letter-spacing:.06em}@media(max-width:800px){.p3r-row{grid-template-columns:1fr}}`;
    document.head.appendChild(style);
  }

  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, options);
    let body = {};
    try { body = await response.json(); } catch { /* non-json response */ }
    if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
    return body;
  }

  function message(text, error = false) {
    const el = $('p3r-stage-message');
    if (el) { el.textContent = text; el.classList.toggle('p3r-bad', error); }
  }

  async function loadState() {
    const t = target();
    const state = await request(`/state?subject_id=${encodeURIComponent(t.subject_id)}&timepoint=${encodeURIComponent(t.timepoint)}`);
    current = { ...state, spatial_id: t.spatial_id, inputs: filterScopedInputs(state.inputs, t.spatial_id) };
    current.assigned_count = current.inputs.filter(x => x.view && x.view !== 'unknown').length;
    current.prepared_count = current.inputs.filter(x => x.prepared && x.view && x.view !== 'unknown').length;
    current.ready_views = [...new Set(current.inputs.filter(x => x.prepared && x.view).map(x => x.view))].sort();
    current.can_register = current.prepared_count >= 2;
    current.can_reconstruct = current.prepared_count >= 2;
    render();
    await syncLegacyEvidence();
  }

  function ensureControls() {
    if ($('p3r-stage-list')) return true;
    const panel = $('photo-3d-reconstruction');
    if (!panel) return false;
    const card = panel.querySelector('.p3r-grid > .p3r-card:nth-child(2)');
    if (!card) return false;
    const note = card.querySelector('.p3r-note');
    if (note) note.textContent = 'Zdjęcia są przypisane do aktywnego celu przestrzennego. Dodaj zdjęcia, przypisz widoki i przygotuj je przed rekonstrukcją. Co najmniej 2 przygotowane widoki są wymagane.';
    const controls = document.createElement('div');
    controls.innerHTML = `<div class="p3r-upload"><label class="primary p3r-upload-label" for="p3r-photo-files">Dodaj zdjęcia</label><input id="p3r-photo-files" type="file" accept="image/jpeg,image/png,image/webp,image/tiff" multiple><button id="p3r-register" type="button">Sprawdź przygotowane widoki</button></div><div id="p3r-user-note" class="p3r-user-note"><strong>Cel zdjęć:</strong> <code>${target().spatial_id}</code>. Zdjęcia dodane tutaj nie są dziedziczone przez inne cele.</div><div id="p3r-stage-summary" class="p3r-stage-summary"></div><div id="p3r-stage-list" class="p3r-list"></div><div id="p3r-stage-message" class="p3r-status" style="margin-top:10px">Ładowanie zdjęć…</div>`;
    note?.insertAdjacentElement('afterend', controls.firstElementChild);
    note?.insertAdjacentElement('afterend', controls.querySelector('#p3r-user-note'));
    const summary = controls.querySelector('#p3r-stage-summary');
    const list = controls.querySelector('#p3r-stage-list');
    const messageEl = controls.querySelector('#p3r-stage-message');
    card.querySelector('.p3r-meter')?.parentElement?.insertAdjacentElement('beforebegin', summary);
    card.querySelector('.p3r-meter')?.parentElement?.insertAdjacentElement('beforebegin', list);
    card.querySelector('#p3r-status')?.replaceWith(messageEl);
    card.querySelector('#p3r-meta')?.style.setProperty('display', 'none');
    const previewHost = panel.querySelector('#p3r-stage');
    if (previewHost && !panel.querySelector('.p3r-preview-label')) {
      const label = document.createElement('div');
      label.className = 'p3r-preview-label';
      label.textContent = 'Podgląd powierzchni 3D';
      previewHost.parentElement.insertBefore(label, previewHost);
    }
    $('p3r-photo-files')?.addEventListener('change', event => uploadFiles([...event.target.files]));
    $('p3r-register')?.addEventListener('click', registerViews);
    return true;
  }

  async function uploadFiles(files) {
    if (!files.length) return;
    const t = target();
    message(`Przesyłanie ${files.length} ${files.length === 1 ? 'zdjęcia' : 'zdjęć'} dla ${t.spatial_id}…`);
    try {
      for (const file of files) {
        const form = new FormData();
        form.append('file', file);
        form.append('subject_id', t.subject_id);
        form.append('timepoint', t.timepoint);
        form.append('spatial_node_id', t.spatial_id);
        const result = await request('/upload', { method: 'POST', body: form });
        rememberAssetTarget(result.asset_id || result.photo?.asset_id, t.spatial_id);
      }
      message('Zdjęcia dodane do aktywnego celu. Przypisz widoki i przygotuj każde zdjęcie.');
      await loadState();
    } catch (error) { message(error.message || 'Nie udało się dodać zdjęć.', true); }
    finally { const input = $('p3r-photo-files'); if (input) input.value = ''; }
  }

  async function assign(assetId, view) {
    try {
      await request('/assign', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({asset_id: assetId, view}) });
      rememberAssetTarget(assetId, target().spatial_id);
      message(`Przypisano widok: ${LABELS[view]}.`);
      await loadState();
    } catch (error) { message(error.message || 'Nie udało się przypisać widoku.', true); }
  }

  async function prepare(assetId) {
    try {
      rememberAssetTarget(assetId, target().spatial_id);
      message('Przygotowywanie zdjęcia…');
      await request(`/prepare/${encodeURIComponent(assetId)}`, { method: 'POST' });
      message('Zdjęcie jest gotowe do rekonstrukcji.');
      await loadState();
    } catch (error) { message(error.message || 'Nie udało się przygotować zdjęcia.', true); }
  }

  async function registerViews() {
    const t = target();
    if (!current || current.prepared_count < 2) { message('Przygotuj co najmniej 2 zdjęcia z różnych widoków.', true); return; }
    try {
      message('Sprawdzanie przygotowanych widoków…');
      const result = await request(`/register?subject_id=${encodeURIComponent(t.subject_id)}&timepoint=${encodeURIComponent(t.timepoint)}`, { method: 'POST' });
      message(result.ready_for_projection ? `${result.registered_count} widoków jest gotowych do kolejnego etapu dla ${t.spatial_id}.` : 'Rejestracja wymaga jeszcze sprawdzenia.');
      await loadState();
    } catch (error) { message(error.message || 'Nie udało się sprawdzić widoków.', true); }
  }

  function render() {
    if (!current) return;
    const list = $('p3r-stage-list');
    if (!list) return;
    const byView = Object.fromEntries(current.inputs.filter(x => x.view).map(x => [x.view, x]));
    list.innerHTML = VIEWS.map(view => {
      const item = byView[view];
      if (!item) return `<div class="p3r-item"><div class="p3r-head"><strong>${LABELS[view]}</strong><span class="p3r-badge p3r-bad">BRAK</span></div><small class="p3r-mini">Dodaj zdjęcie i przypisz je do tego widoku dla ${esc(current.spatial_id)}.</small></div>`;
      const prepared = !!item.prepared;
      const registered = item.registration?.status === 'registered';
      const image = prepared ? `${API}/file/prepared/${encodeURIComponent(item.prepared_asset_id)}` : `${API}/file/source/${encodeURIComponent(item.asset_id)}`;
      const warning = item.warnings?.length ? `<div class="p3r-mini p3r-warn">${esc(item.warnings.join(' '))}</div>` : '';
      return `<div class="p3r-item"><div class="p3r-row"><img class="p3r-preview" src="${image}" alt="${LABELS[view]}"><div class="p3r-row-main"><div class="p3r-head"><strong>${LABELS[view]}</strong><span class="p3r-badge ${registered ? 'p3r-good' : prepared ? 'p3r-good' : 'p3r-warn'}">${registered ? 'GOTOWE' : prepared ? 'PRZYGOTOWANE' : 'DODANE'}</span></div><span class="p3r-file p3r-mini">${esc(item.filename)}</span><select class="p3r-select" data-asset="${esc(item.asset_id)}"><option value="">Zmień widok…</option>${VIEWS.map(v => `<option value="${v}" ${v === view ? 'selected' : ''}>${LABELS[v]}</option>`).join('')}</select>${warning}</div></div><div class="p3r-item-actions">${!prepared ? `<button type="button" data-prepare="${esc(item.asset_id)}">Przygotuj zdjęcie</button>` : `<span class="p3r-mini">Jakość ${Math.round((item.quality?.overall || 0) * 100)}%</span>`}${registered ? '<span class="p3r-mini p3r-good">Widok gotowy</span>' : ''}</div></div>`;
    }).join('');

    list.querySelectorAll('[data-prepare]').forEach(button => button.addEventListener('click', () => prepare(button.dataset.prepare)));
    list.querySelectorAll('select[data-asset]').forEach(select => select.addEventListener('change', () => { if (select.value) assign(select.dataset.asset, select.value); }));

    const assigned = current.assigned_count;
    const prepared = current.prepared_count;
    const registered = current.inputs.filter(x => x.registration?.status === 'registered').length;
    const summary = $('p3r-stage-summary');
    if (summary) summary.innerHTML = `<span class="p3r-stage-chip">${assigned} / 5 przypisanych</span><span class="p3r-stage-chip ${prepared >= 2 ? 'good' : 'warn'}">${prepared} / 5 przygotowanych</span><span class="p3r-stage-chip ${registered >= 2 ? 'good' : 'warn'}">${registered} / 5 gotowych</span><span class="p3r-stage-chip">cel: ${esc(current.spatial_id)}</span>`;
    const build = $('p3r-build');
    if (build) {
      build.disabled = prepared < 2;
      build.textContent = 'Zbuduj powierzchnię 3D';
    }
    const score = $('p3r-score');
    if (score) score.textContent = `${prepared} / ${VIEWS.length}`;
    const meter = $('p3r-meter');
    if (meter) meter.style.width = `${Math.round(prepared / VIEWS.length * 100)}%`;
  }

  async function blobToDataUrl(blob) {
    return await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(blob); });
  }

  async function syncLegacyEvidence() {
    if (syncing || !current) return;
    syncing = true;
    try {
      const key = 'digitalTwinEvidenceUX.v2';
      let store = {};
      try { store = JSON.parse(localStorage.getItem(key) || '{}'); } catch { store = {}; }
      const other = Array.isArray(store.evidence) ? store.evidence.filter(x => x.sourceType !== 'prepared-image') : [];
      const prepared = [];
      const t = target();
      for (const item of current.inputs.filter(x => x.prepared && x.prepared_asset_id && x.view)) {
        const response = await fetch(`${API}/file/prepared/${encodeURIComponent(item.prepared_asset_id)}`);
        if (!response.ok) continue;
        const dataUrl = await blobToDataUrl(await response.blob());
        const spatialId = assetTarget(item) || t.spatial_id;
        prepared.push({ evidence_id: `photo-prepared-${item.prepared_asset_id}`, asset_id: item.asset_id, sourceType: 'prepared-image', prepared: true, filename: item.filename, view: item.view, preparedAsset: { name: item.filename, view: item.view, dataUrl, spatialTarget: spatialId }, subject_id: item.subject_id, timepoint: item.timepoint, target: spatialId, spatial_id: spatialId, spatialId, updated_at: item.updated_at });
      }
      localStorage.setItem(key, JSON.stringify({ ...store, evidence: [...other, ...prepared], target: t.spatial_id, spatial_id: t.spatial_id }));
    } catch { /* server manifest remains canonical */ }
    finally { syncing = false; }
  }

  function refreshScope() {
    if (!$('p3r-stage-list')) return;
    const note = $('p3r-user-note');
    if (note) note.innerHTML = `<strong>Cel zdjęć:</strong> <code>${target().spatial_id}</code>. Zdjęcia dodane tutaj nie są dziedziczone przez inne cele.`;
    loadState().catch(() => {});
  }

  function boot() {
    css();
    let attempts = 0;
    const start = async () => {
      if (!ensureControls()) { if (++attempts < 80) setTimeout(start, 100); return; }
      try { await loadState(); } catch (error) { message(error.message || 'Nie można wczytać stanu zdjęć.', true); }
    };
    start();
  }

  window.addEventListener('testhp:spatial-layer-changed', refreshScope);
  window.addEventListener('testhp:spatial-contract-changed', refreshScope);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
