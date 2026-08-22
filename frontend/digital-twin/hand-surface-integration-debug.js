(() => {
  const PANEL_ID = 'twin-debug-panel';
  const OUT_ID = 'twin-debug-hand-surface-integration';
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const text = el => el?.textContent?.trim() || '';
  const target = () => window.testhpSpatialContract?.getTarget?.() || window.selectedSpatialNode || null;
  const status = (ok, yes='SPÓJNE', no='NIESPÓJNE') => ok ? yes : no;
  function readEvidence(t) {
    try {
      const raw = JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2') || '{}');
      const items = Array.isArray(raw.evidence) ? raw.evidence : [];
      return items.filter(x => String(x.spatial_id || x.spatialId || x.target || '') === String(t?.spatial_id || ''));
    } catch { return []; }
  }
  function inspect() {
    const t = target();
    const spatialId = t?.spatial_id || t?.spatialId || t?.id || '';
    const manager = window.spatialViewportManager;
    const unified = document.getElementById('hand-surface-unified');
    const nav = document.getElementById('spatial-children');
    const inspector = document.getElementById('region-title');
    const inspectorZone = document.getElementById('zone-label');
    const evidence = readEvidence(t);
    const navigationTarget = window.__testhpSpatialNavDiagnostic;
    const children = [...(nav?.querySelectorAll(':scope > .spatial-target') || [])];
    const childRouting = children.map(b => ({label:text(b.querySelector(':scope > strong')) || text(b), spatialId:b.dataset.spatialId || null, targetId:b.dataset.targetId || null}));
    const checks = {
      'MODEL PRZESTRZENNY': !!manager && !!spatialId,
      'INSPEKTOR CELU PRZESTRZENNEGO': !!spatialId && (text(inspector) === (t?.label || '') || text(inspectorZone) === spatialId),
      'NAWIGACJA PRZESTRZENNA': !!spatialId && !!navigationTarget && navigationTarget.rootTarget === 'Dłoń',
      'HAND SURFACE': !!unified && !!spatialId && unified.querySelector('#hand-surface-unified-target code')?.textContent?.trim() === spatialId,
      'INTERPRETACJA BADAWCZA': !!spatialId && evidence.length >= 0
    };
    const relation = ['MODEL PRZESTRZENNY','INSPEKTOR CELU PRZESTRZENNEGO','NAWIGACJA PRZESTRZENNA','HAND SURFACE','INTERPRETACJA BADAWCZA'].every(k => checks[k]);
    const rows = Object.entries(checks).map(([name,ok]) => `<div class="hsid-row"><strong>${esc(name)}</strong><span class="hsid-badge ${ok?'ok':'bad'}">${ok?'✓ SPÓJNE':'✕ NIESPÓJNE'}</span></div>`).join('');
    const trace = [
      `MODEL PRZESTRZENNY  →  ${spatialId || 'BRAK CELU'}`,
      `                         ↓`,
      `INSPEKTOR             →  ${text(inspector) || 'BRAK'}`,
      `                         ↓`,
      `NAWIGACJA             →  ${children.length} celów potomnych`,
      `                         ↓`,
      `HAND SURFACE          →  ${unified ? 'aktywny' : 'BRAK'}`,
      `                         ↓`,
      `INTERPRETACJA         →  ${evidence.length} materiałów dla celu`,
    ].join('\n');
    let out = document.getElementById(OUT_ID);
    if (!out) {
      const panel = document.getElementById(PANEL_ID);
      if (!panel) return false;
      out = document.createElement('section'); out.id=OUT_ID; out.style.cssText='margin:12px 0;padding:12px;border:1px solid #506070;border-radius:10px;background:#10161c;color:#dce7ef;font:12px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;'; panel.appendChild(out);
    }
    out.innerHTML = `<div style="font-weight:800;font-size:13px;margin-bottom:8px">HAND SURFACE · INTEGRATION DEBUG</div><div style="margin-bottom:10px">TARGET: <strong>${esc(t?.label || 'BRAK')}</strong> · <code>${esc(spatialId || 'BRAK')}</code> · level=${esc(t?.level || 'BRAK')}</div>${rows}<pre style="margin:10px 0 0;white-space:pre-wrap">${esc(trace)}</pre><div style="margin-top:10px"><strong>NAWIGACJA DZIECI</strong><br>${esc(JSON.stringify(childRouting,null,2))}</div><div style="margin-top:10px"><strong>WYNIK</strong>: ${relation ? 'CAŁY KONTEKST JEST SPÓJNY' : 'WYKRYTO NIESPÓJNOŚĆ — sprawdź elementy oznaczone ✕'}</div>`;
    return true;
  }
  const boot=()=>{if(!inspect()) setTimeout(inspect,250);};
  ['testhp:spatial-contract-changed','testhp:spatial-layer-changed','testhp:viewport-rendered','testhp:inspector-scope-updated','testhp:evidence-attached','testhp:hand-surface-ready'].forEach(e=>window.addEventListener(e,boot));
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
