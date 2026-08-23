(() => {
  const PANEL_ID = 'twin-debug-panel';
  const OUT_ID = 'twin-debug-hand-surface-integration';
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const text = el => el?.textContent?.trim() || '';
  const normalize = v => String(v ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
  const target = () => window.testhpSpatialContract?.getTarget?.() || window.selectedSpatialNode || null;
  const targetId = t => normalize(t?.spatial_id || t?.spatialId || t?.id || t || '');
  const status = (ok, yes='SPÓJNE', no='NIESPÓJNE') => ok ? yes : no;

  function readEvidence(t) {
    try {
      const raw = JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2') || '{}');
      const items = Array.isArray(raw.evidence) ? raw.evidence : [];
      return items.filter(x => normalize(x.spatial_id || x.spatialId || x.target) === targetId(t) && !x.archived);
    } catch { return []; }
  }

  function readJson(key) {
    try { return JSON.parse(localStorage.getItem(key) || 'null'); } catch { return null; }
  }

  function viewOf(x) {
    const explicit = normalize(x?.view || x?.preparedAsset?.view);
    if (['front','back','side_left','side_right','thumb'].includes(explicit)) return explicit;
    const name = normalize(x?.filename || x?.name || x?.preparedAsset?.name).replace(/[- ]/g, '_');
    return ['front','back','side_left','side_right','thumb'].find(v => name.includes(v)) || null;
  }

  function photoConsistency(t) {
    const id = targetId(t);
    const evidence = readEvidence(t);
    const views = ['front','back','side_left','side_right','thumb'];
    const byView = Object.fromEntries(views.map(v => [v, []]));
    evidence.forEach(x => { const v = viewOf(x); if (v) byView[v].push(x); });

    const prepared = views.filter(v => byView[v].some(x => x.prepared === true || x.preparedAssetId || x.prepared_asset_id));
    const assigned = views.filter(v => byView[v].length > 0);

    const surface = readJson('digitalTwinHandSurface.v1') || {};
    const mappings = Array.isArray(surface.mappings) ? surface.mappings : [];
    const targetMappings = mappings.filter(x => normalize(x.spatialTarget || x.target || x.spatial_id || x.spatialId) === id);
    const registered = views.filter(v => targetMappings.some(x => normalize(x.view) === v && Number(x.quality ?? 0) > 0));

    const plan = readJson('digitalTwinSurfaceProjection.v2');
    const planTarget = normalize(plan?.target || plan?.spatialTarget || plan?.spatial_id || plan?.spatialId);
    const planViews = Array.isArray(plan?.views) ? plan.views : [];
    const planReady = !!plan && planTarget === id && planViews.length > 0;

    const packageState = surface.twinPackage || surface.package || null;
    const reconstruction = window.__testhpPhotoReconstructionState || window.__testhpPhotoReconstruction || null;
    const reconstructionKnown = !!reconstruction;
    const reconstructionReady = reconstructionKnown ? !!(reconstruction.ready || reconstruction.status === 'ready' || reconstruction.reconstructed) : null;
    const applied = !!(surface.appliedToModel || surface.applied || surface.surfaceAssetId || surface.surface_asset_id);

    const canonical = window.__testhpTwinRegistryDiagnostics || {};
    const decisions = Array.isArray(canonical.matchDebug?.decisions) ? canonical.matchDebug.decisions : [];
    const canonicalAccepted = decisions.filter(x => x.matched).length;
    const canonicalRejected = decisions.filter(x => !x.matched).length;
    const canonicalExpected = normalize(canonical.requestedTarget);
    const canonicalTargetConsistent = !canonicalExpected || canonicalExpected === id;

    const duplicateViews = views.filter(v => byView[v].length > 1);
    const viewSetConsistent = assigned.length === prepared.length || prepared.length === 0;
    const registrationConsistent = registered.every(v => prepared.includes(v));

    return {
      id, evidence, assigned, prepared, registered, duplicateViews,
      targetMappings, planReady, planTarget, planViews,
      packageState, reconstructionKnown, reconstructionReady, applied,
      canonicalAccepted, canonicalRejected, canonicalExpected, canonicalTargetConsistent,
      viewSetConsistent, registrationConsistent,
      verdict: canonicalTargetConsistent && viewSetConsistent && registrationConsistent && duplicateViews.length === 0
    };
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
        if (String(previous) !== String(value)) push({type:'body.setAttribute', attribute:name, previous, next:String(value), targetId:targetId(target()), stack:(new Error()).stack || null});
      }
      return originalSetAttribute.apply(this, arguments);
    };
    const originalRemoveAttribute = Element.prototype.removeAttribute;
    Element.prototype.removeAttribute = function(name) {
      if (this === document.body && String(name).toLowerCase() === 'data-spatial-target') {
        const previous = this.getAttribute(name);
        if (previous != null) push({type:'body.removeAttribute', attribute:name, previous, next:null, targetId:targetId(target()), stack:(new Error()).stack || null});
      }
      return originalRemoveAttribute.apply(this, arguments);
    };
    const observer = new MutationObserver(mutations => mutations.forEach(m => {
      if (m.type === 'attributes' && m.target === document.body && m.attributeName === 'data-spatial-target') {
        push({type:'body.dataset mutation', attribute:m.attributeName, previous:m.oldValue, next:document.body.dataset.spatialTarget || null, targetId:targetId(target())});
      }
    }));
    observer.observe(document.body, {attributes:true, attributeFilter:['data-spatial-target'], attributeOldValue:true});
    push({type:'writer-trace-installed', initial:document.body.dataset.spatialTarget || null});
  }

  function inspect() {
    installDatasetWriterTrace();
    const t = target();
    const spatialId = targetId(t);
    const manager = window.spatialViewportManager;
    const unified = document.getElementById('hand-surface-unified');
    const nav = document.getElementById('spatial-children');
    const inspector = document.getElementById('region-title');
    const inspectorZone = document.getElementById('zone-label');
    const evidence = readEvidence(t);
    const navigationTarget = window.__testhpSpatialNavDiagnostic;
    const children = [...(nav?.querySelectorAll(':scope > .spatial-target') || [])];
    const childRouting = children.map(b => ({label:text(b.querySelector(':scope > strong')) || text(b), spatialId:b.dataset.spatialId || null, targetId:b.dataset.targetId || null}));
    const photo = photoConsistency(t);
    const checks = {
      'MODEL PRZESTRZENNY': !!manager && !!spatialId,
      'INSPEKTOR CELU PRZESTRZENNEGO': !!spatialId && (text(inspector) === (t?.label || '') || text(inspectorZone) === spatialId),
      'NAWIGACJA PRZESTRZENNA': !!spatialId && !!navigationTarget && navigationTarget.rootTarget === 'Dłoń',
      'HAND SURFACE': !!unified && !!spatialId && unified.querySelector('#hand-surface-unified-target code')?.textContent?.trim().toLowerCase() === spatialId,
      'INTERPRETACJA BADAWCZA': !!spatialId && evidence.length >= 0,
      'PHOTO 3D · TARGET': photo.canonicalTargetConsistent,
      'PHOTO 3D · VIEWS': photo.viewSetConsistent && photo.duplicateViews.length === 0,
      'PHOTO 3D · REGISTRATION': photo.registrationConsistent
    };
    const relation = Object.values(checks).every(Boolean);
    const rows = Object.entries(checks).map(([name,ok]) => `<div class="hsid-row"><strong>${esc(name)}</strong><span class="hsid-badge ${ok?'ok':'bad'}">${ok?'✓ SPÓJNE':'✕ NIESPÓJNE'}</span></div>`).join('');
    const trace = window.__testhpSpatialWriterTrace || {events:[]};
    const dataset = document.body?.dataset?.spatialTarget || null;
    const selected = spatialId || null;
    const datasetMismatch = !!dataset && !!selected && normalize(dataset) !== normalize(selected);
    const writerLines = (trace.events || []).slice(-12).map((e,i) => `[${i+1}] ${e.type} previous=${e.previous ?? 'NULL'} next=${e.next ?? e.initial ?? 'NULL'} target=${e.targetId ?? 'NULL'}${e.stack ? `\n    ${String(e.stack).split('\n').slice(1,4).join('\n    ')}` : ''}`).join('\n');

    let out = document.getElementById(OUT_ID);
    if (!out) {
      const panel = document.getElementById(PANEL_ID);
      if (!panel) return false;
      out = document.createElement('section'); out.id=OUT_ID; out.style.cssText='margin:12px 0;padding:12px;border:1px solid #506070;border-radius:10px;background:#10161c;color:#dce7ef;font:12px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;'; panel.appendChild(out);
    }

    const viewLines = ['front','back','side_left','side_right','thumb'].map(v => {
      const a = photo.assigned.includes(v), p = photo.prepared.includes(v), r = photo.registered.includes(v);
      return `${v.padEnd(11)} assigned=${a?'YES':'NO '} prepared=${p?'YES':'NO '} registered=${r?'YES':'NO '}`;
    }).join('\n');
    const reconStatus = photo.reconstructionKnown ? (photo.reconstructionReady ? 'READY' : 'NOT READY') : 'UNKNOWN · brak publicznego stanu rekonstrukcji';
    const overall = photo.verdict && !datasetMismatch ? 'SPÓJNE' : 'NIESPÓJNE';

    out.innerHTML = `<div style="font-weight:800;font-size:13px;margin-bottom:8px">HAND SURFACE · INTEGRATION DEBUG</div><div style="margin-bottom:10px">TARGET: <strong>${esc(t?.label || 'BRAK')}</strong> · <code>${esc(spatialId || 'BRAK')}</code> · level=${esc(t?.level || 'BRAK')}</div>${rows}<pre style="margin:10px 0 0;white-space:pre-wrap">MODEL PRZESTRZENNY → ${esc(spatialId || 'BRAK')}\nBODY data-spatial-target → ${esc(dataset || 'NULL')}\nTARGET CHAIN → ${datasetMismatch ? 'DRIFT' : 'OK'}\n\nPHOTO 3D RECONSTRUCTION · CONSISTENCY\nassigned views: ${photo.assigned.length}/5\nprepared views: ${photo.prepared.length}/5\nregistered views: ${photo.registered.length}/5\nduplicate view assignments: ${photo.duplicateViews.length ? photo.duplicateViews.join(', ') : 'none'}\ncanonical accepted: ${photo.canonicalAccepted} | rejected: ${photo.canonicalRejected}\ncanonical requested target: ${photo.canonicalExpected || 'NULL'}\ncanonical target match: ${photo.canonicalTargetConsistent ? 'YES' : 'NO'}\n\nVIEW PIPELINE\n${esc(viewLines)}\n\nPLAN / RECONSTRUCTION\nprojection plan: ${photo.planReady ? 'READY' : 'NOT READY'}\nplan target: ${photo.planTarget || 'NULL'}\nplan views: ${photo.planViews.length}\nreconstruction state: ${reconStatus}\nsurface package: ${photo.packageState ? 'PRESENT' : 'NOT PRESENT'}\napplied to spatial model: ${photo.applied ? 'YES' : 'NO / UNKNOWN'}\n\nTARGET WRITER / DATASET TRACE · latest 12\n${esc(writerLines || 'brak zmian data-spatial-target')}</pre><div style="margin-top:10px"><strong>WYNIK SPÓJNOŚCI</strong>: ${overall}</div>`;
    return true;
  }

  const boot=()=>{if(!inspect()) setTimeout(inspect,250);};
  ['testhp:spatial-contract-changed','testhp:spatial-layer-changed','testhp:viewport-rendered','testhp:inspector-scope-updated','testhp:evidence-attached','testhp:hand-surface-ready','testhp:spatial-writer-trace','testhp:surface-projection-plan-changed','testhp:evidence-registry-debug','testhp:evidence-registry-synced'].forEach(e=>window.addEventListener(e,boot));
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
