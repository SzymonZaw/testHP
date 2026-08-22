(() => {
  const SURFACE_KEY = 'digitalTwinHandSurface.v1';
  const EVIDENCE_KEY = 'digitalTwinEvidenceUX.v2';
  const PLAN_KEY = 'digitalTwinSurfaceProjection.v2';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  const readJson = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; }
    catch { return fallback; }
  };
  const surface = () => readJson(SURFACE_KEY, { geometry: {}, prepared: null, mappings: [], selectedView: 'front' });
  const evidence = () => {
    const value = readJson(EVIDENCE_KEY, { evidence: [] });
    return Array.isArray(value.evidence) ? value.evidence.filter(x => !x.archived) : [];
  };
  const currentTarget = () => window.spatialEvidenceTarget || window.selectedSpatialNode?.spatial_id || document.body.dataset.spatialTarget || 'hand';
  const targetOf = value => value?.spatial_id || value?.spatialId || value?.targetSpatialId || value?.target || value?.spatialTarget || null;
  const belongsToTarget = (value, target) => !targetOf(value) || targetOf(value) === target;
  const targetEvidence = target => evidence().filter(x => belongsToTarget(x, target));
  const targetMappings = target => (Array.isArray(surface().mappings) ? surface().mappings : []).filter(x => belongsToTarget(x, target));
  const evidenceFor = (view, target) => targetEvidence(target).find(x => String(x.view || '').toLowerCase() === view || (String(x.modality || '').toLowerCase() === 'skin_image' && String(x.preparedAsset?.view || '').toLowerCase() === view)) || null;
  const mappingFor = (view, target) => targetMappings(target).find(x => x.view === view) || null;

  function installCss() {
    if ($('hand-surface-20-22-css')) return;
    const style = document.createElement('style');
    style.id = 'hand-surface-20-22-css';
    style.textContent = `
      #hand-surface-stages-20-22{margin-top:16px}.hss22-card{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:16px;background:var(--panel,#fff)}
      .hss22-head,.hss22-actions{display:flex;align-items:center;gap:10px}.hss22-head{justify-content:space-between}.hss22-actions{flex-wrap:wrap}.hss22-secondary{font-size:12px;color:#667085;margin-top:8px}.hss22-badge{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#667085}.hss22-good{color:#1f6b45}.hss22-warn{color:#9a6700}.hss22-status{padding:12px;border-radius:9px;background:rgba(79,111,143,.08);font-size:13px}.hss22-ready{margin:10px 0;padding:10px;border-radius:9px;background:rgba(31,107,69,.08)}.hss22-missing{display:flex;flex-wrap:wrap;gap:6px;margin:9px 0}.hss22-chip{border:1px solid var(--border,#d8dee8);border-radius:999px;padding:5px 9px;font-size:12px}.hss22-progress{height:8px;background:#e8edf3;border-radius:999px;overflow:hidden;margin:9px 0}.hss22-progress i{display:block;height:100%;background:#4f6f8f}
    `;
    document.head.appendChild(style);
  }

  function ensurePanel() {
    if ($('hand-surface-stages-20-22')) return;
    const panel = document.createElement('section');
    panel.id = 'hand-surface-stages-20-22';
    panel.className = 'panel';
    panel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">HAND SURFACE</span><strong>Rejestracja powierzchni</strong></div><span class="muted">następny krok dla aktualnego celu</span></div><div id="hss22-content"></div>`;
    const studio = $('hand-surface-studio');
    if (studio) studio.after(panel); else document.querySelector('.timeline')?.before(panel);
    render();
  }

  function render() {
    const c = $('hss22-content');
    if (!c) return;
    const target = currentTarget();
    const ev = targetEvidence(target);
    const prepared = ev.filter(x => x.prepared || x.preparedAssetId || x.sourceType === 'prepared-image').length;
    const registered = VIEWS.filter(v => Number(mappingFor(v, target)?.quality || 0) > 0).length;
    const available = VIEWS.filter(v => !!evidenceFor(v, target));
    const missing = VIEWS.filter(v => !evidenceFor(v, target));
    const ready = registered === VIEWS.length;
    const preparationReady = prepared > 0;
    const progress = Math.round(registered / VIEWS.length * 100);
    const title = window.selectedSpatialNode?.label || document.querySelector('#spatial-node strong')?.textContent?.trim() || 'Aktualny cel';
    const next = !ev.length ? 'Dodaj materiał źródłowy dla tego celu.' : !preparationReady ? 'Przygotuj materiał, aby rozpocząć rejestrację.' : ready ? 'Wszystkie widoki są gotowe. Możesz utworzyć plan projekcji.' : 'Dodaj brakujące widoki, aby rozpocząć rejestrację.';

    c.innerHTML = `<div class="hss22-card">
      <div class="hss22-head"><strong>${esc(title)}</strong><span class="hss22-badge ${ready ? 'hss22-good' : 'hss22-warn'}">${ready ? 'GOTOWE' : 'WYMAGA DANYCH'}</span></div>
      <div class="hss22-secondary">Cel: <b>${esc(target)}</b></div>
      <div class="hss22-ready"><b>${preparationReady ? '✓ Przygotowanie gotowe' : '○ Przygotowanie niegotowe'}</b><br><span>${prepared} przygotowany${prepared === 1 ? ' materiał' : 'chowanych materiałów'} dla tego celu</span></div>
      <div class="hss22-head"><strong>Rejestracja widoków</strong><span>${registered}/5</span></div>
      <div class="hss22-progress"><i style="width:${progress}%"></i></div>
      ${ready ? `<div class="hss22-status hss22-good"><b>Wszystkie 5 widoków jest gotowych.</b><br>Możesz przejść do planu projekcji.</div>` : `<div class="hss22-status"><b>Brakuje ${missing.length} ${missing.length === 1 ? 'widoku' : 'widoków'}.</b><div class="hss22-missing">${missing.map(v => `<span class="hss22-chip">${esc(v.replaceAll('_',' '))}</span>`).join('')}</div>${available.length ? `<div class="hss22-secondary">Dostępne: ${available.map(v => esc(v.replaceAll('_',' '))).join(' · ')}</div>` : ''}</div>`}
      <div class="hss22-actions" style="margin-top:12px"><button id="hss22-next" class="primary">${ready ? 'Przejdź do planu projekcji' : 'Dodaj brakujące widoki'}</button><button id="hss22-refresh">Sprawdź ponownie</button></div>
      <div class="hss22-secondary">${esc(next)} Brakujące dane nie są zastępowane sztucznymi danymi.</div>
    </div>`;

    $('hss22-refresh').onclick = render;
    $('hss22-next').onclick = () => {
      if (ready) {
        const mappings = targetMappings(target);
        const plan = {schema:'surface-projection-v2',mode:'weighted-multiview-plan',target,views:{},confidence:0,savedAt:new Date().toISOString()};
        let total = 0;
        VIEWS.forEach(view => { const q = Math.max(0, Math.min(1, Number(mappings.find(x => x.view === view)?.quality || 0))); const hasPrepared = !!evidenceFor(view, target); const weight = Number((q * .75 + (hasPrepared ? .25 : 0)).toFixed(3)); plan.views[view] = {quality:q,prepared:hasPrepared,weight}; total += weight; });
        plan.confidence = Number(Math.min(1, total / VIEWS.length).toFixed(3));
        localStorage.setItem(PLAN_KEY, JSON.stringify(plan));
        window.dispatchEvent(new CustomEvent('testhp:surface-projection-plan-changed',{detail:plan}));
      } else {
        document.querySelector('.hss-tabs [data-tab="mapping"]')?.click();
        document.querySelector('.hss-tabs [data-tab="data"]')?.click();
      }
    };
  }

  function boot() {
    installCss();
    ensurePanel();
    const refresh = () => render();
    window.addEventListener('testhp:hand-surface-ready', refresh);
    window.addEventListener('testhp:evidence-attached', refresh);
    window.addEventListener('testhp:surface-projection-plan-changed', refresh);
    window.addEventListener('testhp:spatial-layer-changed', refresh);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true}); else boot();
})();
