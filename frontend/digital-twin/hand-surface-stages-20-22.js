(() => {
  const SURFACE_KEY = 'digitalTwinHandSurface.v1';
  const EVIDENCE_KEY = 'digitalTwinEvidenceUX.v2';
  const PLAN_KEY = 'digitalTwinSurfaceProjection.v2';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const readJson = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; } catch { return fallback; } };
  const surface = () => readJson(SURFACE_KEY, {geometry:{}, prepared:null, mappings:[], selectedView:'front'});
  const evidence = () => { const value = readJson(EVIDENCE_KEY, {evidence:[]}); return Array.isArray(value.evidence) ? value.evidence.filter(x => !x.archived) : []; };

  // HAND SURFACE is a surface-level workflow. Deep navigation may continue below it,
  // but surface registration remains attached to the nearest hand/palm surface target.
  const rawTarget = () => window.spatialEvidenceTarget || window.selectedSpatialNode?.spatial_id || document.body.dataset.spatialTarget || 'hand';
  const surfaceTarget = () => {
    const raw = String(rawTarget() || 'hand');
    if (raw === 'hand/palm' || raw.startsWith('hand/palm/')) return 'hand/palm';
    return raw;
  };
  const surfaceTitle = () => surfaceTarget() === 'hand/palm' ? 'Śródręcze' : (window.selectedSpatialNode?.label || 'Aktualny cel');
  const targetOf = value => value?.spatial_id || value?.spatialId || value?.targetSpatialId || value?.target || value?.spatialTarget || null;
  const belongs = (value, target) => !targetOf(value) || targetOf(value) === target;
  const targetEvidence = target => evidence().filter(x => belongs(x, target));
  const targetMappings = target => (Array.isArray(surface().mappings) ? surface().mappings : []).filter(x => belongs(x, target));
  const evidenceFor = (view, target) => targetEvidence(target).find(x => String(x.view || '').toLowerCase() === view || (String(x.modality || '').toLowerCase() === 'skin_image' && String(x.preparedAsset?.view || '').toLowerCase() === view)) || null;
  const mappingFor = (view, target) => targetMappings(target).find(x => x.view === view) || null;

  function installCss() {
    if ($('hand-surface-20-22-css')) return;
    const style = document.createElement('style');
    style.id = 'hand-surface-20-22-css';
    style.textContent = `
      #hand-surface-stages-20-22{margin-top:14px}.hss22-card{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)}
      .hss22-head,.hss22-actions{display:flex;align-items:center;gap:10px}.hss22-head{justify-content:space-between}.hss22-actions{flex-wrap:wrap}.hss22-secondary{font-size:12px;color:#667085;margin-top:7px}.hss22-badge{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#667085}.hss22-good{color:#1f6b45}.hss22-warn{color:#9a6700}.hss22-status{padding:10px;border-radius:9px;background:rgba(79,111,143,.08);font-size:13px}.hss22-ready{margin:9px 0;padding:9px;border-radius:9px;background:rgba(31,107,69,.08)}.hss22-missing{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.hss22-chip{border:1px solid var(--border,#d8dee8);border-radius:999px;padding:4px 8px;font-size:12px}.hss22-progress{height:7px;background:#e8edf3;border-radius:999px;overflow:hidden;margin:8px 0}.hss22-progress i{display:block;height:100%;background:#4f6f8f}.hss22-inline-title{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#667085;margin-bottom:8px}
    `;
    document.head.appendChild(style);
  }

  function withSurfaceContext(fn) {
    const previousTarget = window.spatialEvidenceTarget;
    const previousNode = window.selectedSpatialNode;
    window.spatialEvidenceTarget = surfaceTarget();
    if (surfaceTarget() === 'hand/palm') window.selectedSpatialNode = {label:'Śródręcze', spatial_id:'hand/palm', id:'palm', path:['Hand','Palm']};
    try { return fn(); } finally { window.spatialEvidenceTarget = previousTarget; window.selectedSpatialNode = previousNode; }
  }

  function patchStudioTargeting() {
    const api = window.handSurfaceStages11to15;
    if (!api || api.__surfaceTargetPatched) return !!api;
    const originalRender = api.render;
    api.render = () => withSurfaceContext(() => originalRender());
    api.__surfaceTargetPatched = true;
    return true;
  }

  function ensureInlinePanel() {
    if ($('hand-surface-stages-20-22')) return;
    const studio = $('hand-surface-studio');
    if (!studio) return;
    const panel = document.createElement('div');
    panel.id = 'hand-surface-stages-20-22';
    panel.innerHTML = `<div class="hss22-inline-title">Dalszy etap powierzchni</div><div id="hss22-content"></div>`;
    studio.appendChild(panel);
    render();
  }

  function render() {
    const c = $('hss22-content');
    if (!c) return;
    const target = surfaceTarget();
    const ev = targetEvidence(target);
    const prepared = ev.filter(x => x.prepared || x.preparedAssetId || x.sourceType === 'prepared-image').length;
    const registered = VIEWS.filter(v => Number(mappingFor(v, target)?.quality || 0) > 0).length;
    const missing = VIEWS.filter(v => !evidenceFor(v, target));
    const ready = registered === VIEWS.length;
    const plan = readJson(PLAN_KEY, null);
    const planReady = plan?.target === target && plan?.schema === 'surface-projection-v2';
    const next = !ev.length ? 'Najpierw dodaj materiał dla śródręcza.' : !prepared ? 'Przygotuj materiał źródłowy.' : !ready ? 'Uzupełnij pięć widoków i jakość rejestracji.' : !planReady ? 'Utwórz plan projekcji.' : 'Pakiet bliźniaka jest gotowy do eksportu.';
    const progress = Math.round(registered / VIEWS.length * 100);
    c.innerHTML = `<div class="hss22-card">
      <div class="hss22-head"><strong>Rejestracja → projekcja → pakiet</strong><span class="hss22-badge ${ready ? 'hss22-good' : 'hss22-warn'}">${ready ? 'GOTOWE' : 'W TOKU'}</span></div>
      <div class="hss22-secondary">Cel powierzchni: <b>${esc(surfaceTitle())}</b> · <code>${esc(target)}</code></div>
      <div class="hss22-ready"><b>${prepared ? '✓' : '○'} Przygotowanie</b> · ${prepared} przygotowany materiał</div>
      <div class="hss22-head"><strong>Widoki rejestracyjne</strong><span>${registered}/5</span></div>
      <div class="hss22-progress"><i style="width:${progress}%"></i></div>
      ${ready ? `<div class="hss22-status hss22-good"><b>5/5 widoków zarejestrowanych.</b> ${planReady ? 'Plan projekcji istnieje.' : 'Możesz utworzyć plan projekcji.'}</div>` : `<div class="hss22-status"><b>Brakuje ${missing.length} ${missing.length === 1 ? 'widoku' : 'widoków'}.</b><div class="hss22-missing">${missing.map(v => `<span class="hss22-chip">${esc(v.replaceAll('_',' '))}</span>`).join('')}</div></div>`}
      <div class="hss22-actions" style="margin-top:10px"><button id="hss22-next" class="primary">${ready && !planReady ? 'Utwórz plan projekcji' : ready && planReady ? 'Odśwież stan pakietu' : 'Otwórz rejestrację'}</button><button id="hss22-refresh">Sprawdź ponownie</button></div>
      <div class="hss22-secondary">${esc(next)} Brakujące dane pozostają brakujące — nie tworzymy sztucznych widoków.</div>
    </div>`;

    $('hss22-refresh').onclick = () => { patchStudioTargeting(); withSurfaceContext(() => window.handSurfaceStages11to15?.render?.()); render(); };
    $('hss22-next').onclick = () => {
      if (!ready) { document.querySelector('.hss-tabs [data-tab="mapping"]')?.click(); return; }
      withSurfaceContext(() => {
        const mappings = targetMappings(target);
        const out = {schema:'surface-projection-v2',mode:'weighted-multiview-plan',target,views:{},confidence:0,savedAt:new Date().toISOString()};
        let total = 0;
        VIEWS.forEach(view => { const q = Math.max(0, Math.min(1, Number(mappings.find(x => x.view === view)?.quality || 0))); const hasPrepared = !!evidenceFor(view, target); const weight = Number((q * .75 + (hasPrepared ? .25 : 0)).toFixed(3)); out.views[view] = {quality:q,prepared:hasPrepared,weight}; total += weight; });
        out.confidence = Number(Math.min(1, total / VIEWS.length).toFixed(3));
        localStorage.setItem(PLAN_KEY, JSON.stringify(out));
        window.dispatchEvent(new CustomEvent('testhp:surface-projection-plan-changed',{detail:out}));
        render();
      });
    };
  }

  function boot() {
    installCss();
    const tryAttach = () => { patchStudioTargeting(); ensureInlinePanel(); render(); };
    tryAttach();
    window.addEventListener('testhp:spatial-target-changed', tryAttach);
    window.addEventListener('testhp:spatial-layer-changed', tryAttach);
    window.addEventListener('testhp:evidence-attached', tryAttach);
    window.addEventListener('testhp:hand-surface-ready', tryAttach);
    window.addEventListener('testhp:surface-projection-plan-changed', render);

    // Hand Surface actions must always write to the surface target, even when the
    // user is currently drilling into tissue/cellular navigation.
    document.addEventListener('click', event => {
      if (!event.target.closest('#hand-surface-studio')) return;
      const previousTarget = window.spatialEvidenceTarget;
      const previousNode = window.selectedSpatialNode;
      window.spatialEvidenceTarget = surfaceTarget();
      if (surfaceTarget() === 'hand/palm') window.selectedSpatialNode = {label:'Śródręcze', spatial_id:'hand/palm', id:'palm', path:['Hand','Palm']};
      setTimeout(() => { window.spatialEvidenceTarget = previousTarget; window.selectedSpatialNode = previousNode; }, 0);
    }, true);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true}); else boot();
})();
