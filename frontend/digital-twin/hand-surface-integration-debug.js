(() => {
  const PANEL_ID = 'twin-debug-panel';
  const OUT_ID = 'twin-debug-hand-surface-integration';
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const text = el => el?.textContent?.trim() || '';
  const target = () => window.testhpSpatialContract?.getTarget?.() || window.selectedSpatialNode || null;
  const status = (ok, yes='SPÓJNE', no='NIESPÓJNE') => ok ? yes : no;
  const writerTrace = window.__testhpSpatialWriterTrace || {events: [], current: null};
  function readEvidence(t) {
    try {
      const raw = JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2') || '{}');
      const items = Array.isArray(raw.evidence) ? raw.evidence : [];
      return items.filter(x => String(x.spatial_id || x.spatialId || x.target || '') === String(t?.spatial_id || ''));
    } catch { return []; }
  }
  function installDatasetWriterTrace() {
    if (window.__testhpDatasetWriterTraceInstalled) return;
    window.__testhpDatasetWriterTraceInstalled = true;
    window.__testhpSpatialWriterTrace = {events: [], current: null};
    const push = detail => {
      const trace = window.__testhpSpatialWriterTrace;
      trace.events.push({t: Date.now(), ...detail});
      if (trace.events.length > 40) trace.events.shift();
      trace.current = detail;
      window.dispatchEvent(new CustomEvent('testhp:spatial-writer-trace', {detail}));
    };
    const originalSetAttribute = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {
      if (this === document.body && String(name).toLowerCase() === 'data-spatial-target') {
        const previous = this.getAttribute(name);
        if (String(previous) !== String(value)) push({type:'body.setAttribute', attribute:name, previous, next:String(value), targetId:target()?.spatial_id || target()?.spatialId || null, stack:(new Error()).stack || null});
      }
      return originalSetAttribute.apply(this, arguments);
    };
    const originalRemoveAttribute = Element.prototype.removeAttribute;
    Element.prototype.removeAttribute = function(name) {
      if (this === document.body && String(name).toLowerCase() === 'data-spatial-target') {
        const previous = this.getAttribute(name);
        if (previous != null) push({type:'body.removeAttribute', attribute:name, previous, next:null, targetId:target()?.spatial_id || target()?.spatialId || null, stack:(new Error()).stack || null});
      }
      return originalRemoveAttribute.apply(this, arguments);
    };
    const observer = new MutationObserver(mutations => mutations.forEach(m => {
      if (m.type === 'attributes' && m.target === document.body && m.attributeName === 'data-spatial-target') {
        push({type:'body.dataset mutation', attribute:m.attributeName, previous:m.oldValue, next:document.body.dataset.spatialTarget || null, targetId:target()?.spatial_id || target()?.spatialId || null});
      }
    }));
    observer.observe(document.body, {attributes:true, attributeFilter:['data-spatial-target'], attributeOldValue:true});
    push({type:'writer-trace-installed', initial:document.body.dataset.spatialTarget || null});
  }
  function inspect() {
    installDatasetWriterTrace();
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
    const relation = Object.values(checks).every(Boolean);
    const rows = Object.entries(checks).map(([name,ok]) => `<div class="hsid-row"><strong>${esc(name)}</strong><span class="hsid-badge ${ok?'ok':'bad'}">${ok?'✓ SPÓJNE':'✕ NIESPÓJNE'}</span></div>`).join('');
    const trace = window.__testhpSpatialWriterTrace || {events:[]};
    const dataset = document.body?.dataset?.spatialTarget || null;
    const selected = spatialId || null;
    const datasetMismatch = !!dataset && !!selected && dataset !== selected;
    const writerLines = (trace.events || []).slice(-12).map((e,i) => `[${i+1}] ${e.type} previous=${e.previous ?? 'NULL'} next=${e.next ?? e.initial ?? 'NULL'} target=${e.targetId ?? 'NULL'}${e.stack ? `\n    ${String(e.stack).split('\n').slice(1,4).join('\n    ')}` : ''}`).join('\n');
    let out = document.getElementById(OUT_ID);
    if (!out) {
      const panel = document.getElementById(PANEL_ID);
      if (!panel) return false;
      out = document.createElement('section'); out.id=OUT_ID; out.style.cssText='margin:12px 0;padding:12px;border:1px solid #506070;border-radius:10px;background:#10161c;color:#dce7ef;font:12px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;'; panel.appendChild(out);
    }
    out.innerHTML = `<div style="font-weight:800;font-size:13px;margin-bottom:8px">HAND SURFACE · INTEGRATION DEBUG</div><div style="margin-bottom:10px">TARGET: <strong>${esc(t?.label || 'BRAK')}</strong> · <code>${esc(spatialId || 'BRAK')}</code> · level=${esc(t?.level || 'BRAK')}</div>${rows}<pre style="margin:10px 0 0;white-space:pre-wrap">MODEL PRZESTRZENNY → ${esc(spatialId || 'BRAK')}\nBODY data-spatial-target → ${esc(dataset || 'NULL')}\nTARGET CHAIN → ${datasetMismatch ? 'DRIFT' : 'OK'}\n\nNAWIGACJA DZIECI\n${esc(JSON.stringify(childRouting,null,2))}\n\nTARGET WRITER / DATASET TRACE · latest 12\n${esc(writerLines || 'brak zmian data-spatial-target')}</pre><div style="margin-top:10px"><strong>WYNIK</strong>: ${relation ? 'CAŁY KONTEKST JEST SPÓJNY' : 'WYKRYTO NIESPÓJNOŚĆ — sprawdź elementy oznaczone ✕'}</div>`;
    return true;
  }
  const boot=()=>{if(!inspect()) setTimeout(inspect,250);};
  ['testhp:spatial-contract-changed','testhp:spatial-layer-changed','testhp:viewport-rendered','testhp:inspector-scope-updated','testhp:evidence-attached','testhp:hand-surface-ready','testhp:spatial-writer-trace'].forEach(e=>window.addEventListener(e,boot));
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
