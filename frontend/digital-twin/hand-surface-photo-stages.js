(() => {
  const API = '/api/hand/photo-reconstruction';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const LABELS = { front: 'Przód', back: 'Tył', side_left: 'Lewa strona', side_right: 'Prawa strona', thumb: 'Kciuk' };
  const SCOPE = 'digitalTwinPhotoSpatialScope.v1';
  const VIEW_STORE = 'digitalTwinEvidenceUX.views.v1';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const canonical = value => {
    const raw = typeof value === 'string' ? value : value?.spatial_id || value?.spatialId || value?.target || value?.spatialTarget || null;
    if (!raw) return 'hand';
    const fn = window.testhpSpatialContract?.canonicalTargetId;
    return typeof fn === 'function' ? (fn(raw) || 'hand') : String(raw).replace(/^\/+|\/+$/g, '').toLowerCase();
  };
  const target = () => ({ subject_id: window.testhpPhotoReconstructionSubject || 'own_cohort', timepoint: window.testhpPhotoReconstructionTimepoint || 'T0', spatial_id: canonical(window.testhpSpatialContract?.getTarget?.() || window.spatialEvidenceTarget || window.selectedSpatialNode || document.body?.dataset?.spatialTarget || 'hand') });
  const readScope = () => { try { return JSON.parse(localStorage.getItem(SCOPE) || '{}'); } catch { return {}; } };
  const readViewStore = () => { try { const value = JSON.parse(localStorage.getItem(VIEW_STORE) || '{}'); return value && typeof value === 'object' && !Array.isArray(value) ? value : {}; } catch { return {}; } };
  const rememberTarget = (assetId, spatialId) => { if (!assetId) return; const scope = readScope(); scope[assetId] = canonical(spatialId); localStorage.setItem(SCOPE, JSON.stringify(scope)); };
  const savedViewFor = item => item?.asset_id ? readViewStore()[item.asset_id] || (item.id ? readViewStore()[item.id] : null) : (item?.id ? readViewStore()[item.id] : null);
  const withSavedViews = items => (Array.isArray(items) ? items : []).map(item => { const savedView = savedViewFor(item); return !item?.view && savedView ? { ...item, view: savedView } : item; });
  const scoped = (item, id) => canonical(item?.spatial_id || item?.spatialId || item?.target || readScope()[item?.asset_id] || 'hand') === id;
  let state = null;

  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, options);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
    return body;
  }

  function injectCss() {
    if ($('photo-stage-clean-css')) return;
    const style = document.createElement('style');
    style.id = 'photo-stage-clean-css';
    style.textContent = `.p3r-clean{margin-top:12px}.p3r-clean-upload{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0}.p3r-clean-upload input{display:none}.p3r-clean-upload label{display:inline-flex;align-items:center;cursor:pointer}.p3r-clean-note{margin:8px 0;padding:9px 11px;border-radius:9px;background:rgba(79,111,143,.06);font-size:12px;color:#667085;line-height:1.45}.p3r-clean-summary{display:flex;gap:7px;flex-wrap:wrap;margin:8px 0}.p3r-clean-chip{padding:5px 8px;border-radius:999px;background:#f2f4f7;font-size:11px}.p3r-clean-chip.good{color:#1f6b45;background:#ecfdf3}.p3r-clean-chip.warn{color:#9a6700;background:#fffaeb}.p3r-clean-list{display:grid;gap:7px}.p3r-clean-item{padding:9px 10px;border:1px solid var(--border,#d8dee8);border-radius:9px}.p3r-clean-head{display:flex;justify-content:space-between;gap:8px;align-items:center}.p3r-clean-meta{font-size:12px;color:#667085}.p3r-clean-select{width:100%;margin-top:6px;padding:6px 8px;border:1px solid var(--border,#d8dee8);border-radius:7px;background:var(--panel,#fff);color:inherit}.p3r-clean-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:7px}.p3r-clean-status{margin-top:9px;font-size:12px;color:#667085}.p3r-clean-status.bad{color:#b42318}.p3r-clean-unassigned{border-style:dashed;background:rgba(79,111,143,.025)}`;
    document.head.appendChild(style);
  }

  function host() {
    const panel = $('photo-3d-reconstruction');
    if (!panel) return null;
    if ($('p3r-clean-root')) return $('p3r-clean-root');
    const root = document.createElement('div');
    root.id = 'p3r-clean-root'; root.className = 'p3r-clean';
    root.innerHTML = `<div class="p3r-clean-upload"><label class="primary" for="p3r-clean-files">＋ Dodaj zdjęcia</label><input id="p3r-clean-files" type="file" accept="image/jpeg,image/png,image/webp,image/tiff" multiple><button id="p3r-clean-register" type="button">Zarejestruj przygotowane widoki</button></div><div id="p3r-clean-note" class="p3r-clean-note"></div><div id="p3r-clean-summary" class="p3r-clean-summary"></div><div id="p3r-clean-list" class="p3r-clean-list"></div><div id="p3r-clean-status" class="p3r-clean-status" aria-live="polite"></div>`;
    const note = panel.querySelector('.p3r-note');
    const card = note?.closest('.p3r-card') || panel.querySelector('.p3r-card') || panel;
    if (note) note.insertAdjacentElement('afterend', root); else card.prepend(root);
    $('p3r-clean-files').addEventListener('change', e => upload([...e.target.files]));
    $('p3r-clean-register').addEventListener('click', register);
    return root;
  }

  function status(text, bad = false) { const el = $('p3r-clean-status'); if (el) { el.textContent = text; el.classList.toggle('bad', bad); } }

  async function load() {
    const t = target();
    const raw = await request(`/state?subject_id=${encodeURIComponent(t.subject_id)}&timepoint=${encodeURIComponent(t.timepoint)}&spatial_id=${encodeURIComponent(t.spatial_id)}`);
    const inputs = withSavedViews(Array.isArray(raw.inputs) ? raw.inputs : []);
    state = { ...raw, spatial_id: t.spatial_id, inputs }; render();
  }

  async function upload(files) {
    if (!files.length) return;
    const t = target(); status(`Dodawanie ${files.length} ${files.length === 1 ? 'zdjęcia' : 'zdjęć'} dla ${t.spatial_id}…`);
    try {
      for (const file of files) {
        const form = new FormData(); form.append('file', file); form.append('subject_id', t.subject_id); form.append('timepoint', t.timepoint); form.append('spatial_node_id', t.spatial_id);
        const result = await request('/upload', { method: 'POST', body: form });
        rememberTarget(result.asset_id || result.photo?.asset_id, t.spatial_id);
      }
      status('Zdjęcia dodane. Przypisz widok i przygotuj każde zdjęcie.'); await load();
    } catch (error) { status(error.message || 'Nie udało się dodać zdjęć.', true); }
    finally { if ($('p3r-clean-files')) $('p3r-clean-files').value = ''; }
  }

  window.addEventListener('testhp:hand-photo-source-add-request', event => {
    const input = $('p3r-clean-files');
    if (input) { input.click(); return; }
    status('Formularz dodawania zdjęć nie jest jeszcze gotowy.', true);
  });

  async function assign(assetId, view) {
    const t = target();
    try {
      await request('/assign', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ asset_id: assetId, view, spatial_id: t.spatial_id, subject_id: t.subject_id, timepoint: t.timepoint }) });
      rememberTarget(assetId, t.spatial_id); status(`Przypisano widok: ${LABELS[view]}.`); await load();
    } catch (error) { status(error.message || 'Nie udało się przypisać widoku.', true); }
  }

  async function prepare(assetId) {
    const t = target();
    try {
      const item = state?.inputs?.find(x => x.asset_id === assetId);
      const savedView = savedViewFor(item) || item?.view;
      if (!savedView) { status('Najpierw wybierz widok zdjęcia.', true); return; }
      await request('/assign', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ asset_id: assetId, view: savedView, spatial_id: t.spatial_id, subject_id: t.subject_id, timepoint: t.timepoint }) });
      status('Przygotowywanie zdjęcia…');
      await request(`/prepare/${encodeURIComponent(assetId)}?spatial_id=${encodeURIComponent(t.spatial_id)}&subject_id=${encodeURIComponent(t.subject_id)}&timepoint=${encodeURIComponent(t.timepoint)}`, { method: 'POST' });
      rememberTarget(assetId, t.spatial_id); status('Zdjęcie jest przygotowane.'); await load();
    }
    catch (error) { status(error.message || 'Nie udało się przygotować zdjęcia.', true); }
  }

  async function register() {
    const t = target();
    const preparedViews = new Set((state?.inputs || []).filter(x => x.prepared && x.view).map(x => x.view));
    if (preparedViews.size < 2) { status('Przygotuj co najmniej 2 zdjęcia z różnych widoków.', true); return; }
    try {
      status('Rejestrujemy przygotowane widoki…');
      const result = await request('/register', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ subject_id: t.subject_id, timepoint: t.timepoint, spatial_id: t.spatial_id }) });
      status(result.ready_for_projection ? `${result.registered_count || 0} widoków zarejestrowano. Powierzchnia może przejść do kolejnego etapu.` : 'Rejestracja wymaga jeszcze uzupełnienia.');
      await load();
    }
    catch (error) { status(error.message || 'Nie udało się zarejestrować widoków.', true); }
  }

  function itemCard(item, view = null, unassigned = false) {
    const preparedFlag = !!item.prepared, ready = item.registration?.status === 'registered';
    const currentView = item.view || view || '';
    return `<div class="p3r-clean-item ${unassigned ? 'p3r-clean-unassigned' : ''}"><div class="p3r-clean-head"><strong>${esc(item.filename || 'Zdjęcie')}</strong><span class="p3r-clean-meta">${ready ? '✓ Zarejestrowane' : preparedFlag ? '✓ Przygotowane' : currentView ? 'Przypisane' : 'Dodane'}</span></div><div class="p3r-clean-meta">${currentView ? `Widok: ${esc(LABELS[currentView] || currentView)}` : 'Nie przypisano jeszcze widoku'}</div><select class="p3r-clean-select" data-asset="${esc(item.asset_id)}"><option value="">Wybierz widok…</option>${VIEWS.map(v => `<option value="${v}" ${v === currentView ? 'selected' : ''}>${LABELS[v]}</option>`).join('')}</select><div class="p3r-clean-actions">${!preparedFlag ? `<button type="button" data-prepare="${esc(item.asset_id)}">Przygotuj zdjęcie</button>` : '<span class="p3r-clean-meta">Zdjęcie gotowe do rejestracji</span>'}</div></div>`;
  }

  function render() {
    if (!state || !$('p3r-clean-list')) return;
    const assignedItems = state.inputs.filter(x => x.view && VIEWS.includes(x.view));
    const unassignedItems = state.inputs.filter(x => !x.view || !VIEWS.includes(x.view));
    const byView = {}; assignedItems.forEach(x => { byView[x.view] = x; });
    $('p3r-clean-note').innerHTML = `<strong>Zdjęcia dla:</strong> <code>${esc(state.spatial_id)}</code>. Dodaj co najmniej 2 zdjęcia z różnych stron dłoni, przypisz im różne widoki i przygotuj je.`;
    const assigned = assignedItems.length, prepared = new Set(state.inputs.filter(x => x.prepared && x.view && VIEWS.includes(x.view)).map(x => x.view)).size, registered = new Set(state.inputs.filter(x => x.registration?.status === 'registered' && x.view).map(x => x.view)).size;
    $('p3r-clean-summary').innerHTML = `<span class="p3r-clean-chip">${assigned} / 5 widoków przypisanych</span><span class="p3r-clean-chip ${prepared >= 2 ? 'good' : 'warn'}">${prepared} / 5 widoków przygotowanych</span><span class="p3r-clean-chip ${registered >= 2 ? 'good' : 'warn'}">${registered} / 5 widoków zarejestrowanych</span>`;
    const unassignedHtml = unassignedItems.length ? `<div class="p3r-clean-item p3r-clean-unassigned"><div class="p3r-clean-head"><strong>Zdjęcia bez widoku</strong><span class="p3r-clean-meta">${unassignedItems.length}</span></div><div class="p3r-clean-meta">Wybierz widok dla każdego zdjęcia, aby można było je przygotować.</div></div>${unassignedItems.map(item => itemCard(item, null, true)).join('')}` : '';
    const viewsHtml = VIEWS.map(view => { const item = byView[view]; return item ? itemCard(item, view) : `<div class="p3r-clean-item"><div class="p3r-clean-head"><strong>${LABELS[view]}</strong><span class="p3r-clean-meta">Brak zdjęcia</span></div><div class="p3r-clean-meta">Dodaj zdjęcie dla tego widoku.</div></div>`; }).join('');
    $('p3r-clean-list').innerHTML = unassignedHtml + viewsHtml;
    $('p3r-clean-list').querySelectorAll('select[data-asset]').forEach(el => el.addEventListener('change', () => { if (el.value) assign(el.dataset.asset, el.value); }));
    $('p3r-clean-list').querySelectorAll('[data-prepare]').forEach(el => el.addEventListener('click', () => prepare(el.dataset.prepare)));
  }

  function boot() { injectCss(); if (!host()) return false; load().catch(error => status(error.message || 'Nie można wczytać zdjęć.', true)); return true; }
  const schedule = () => setTimeout(boot, 0);
  window.addEventListener('testhp:spatial-layer-changed', schedule); window.addEventListener('testhp:spatial-contract-changed', schedule); window.addEventListener('testhp:evidence-attached', schedule);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
  const observer = new MutationObserver(() => { if (!$('p3r-clean-root')) boot(); }); if (document.body) observer.observe(document.body, { childList: true, subtree: true });
})();