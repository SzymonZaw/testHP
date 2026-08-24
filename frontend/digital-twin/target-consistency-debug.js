(() => {
  const SCRIPT_ID = 'testhp-target-consistency-debug';
  if (window.__testhpTargetConsistencyDebugInstalled) return;
  window.__testhpTargetConsistencyDebugInstalled = true;

  const normalize = value => String(value ?? '').trim().replace(/^\/+|\/+$/g, '');
  const first = (obj, keys) => {
    for (const key of keys) if (obj && obj[key] != null && obj[key] !== '') return obj[key];
    return null;
  };
  const idFrom = value => {
    if (!value) return '';
    if (typeof value === 'object') return normalize(first(value, ['spatial_node_id','spatial_id','spatialId','targetSpatialId','id']) || '');
    const raw = normalize(value);
    return raw.includes('/') ? raw : '';
  };
  const managerTarget = () => {
    const manager = window.spatialViewportManager;
    const state = manager?.state || {};
    const active = manager?.active || {};
    const candidates = [
      state.spatial_id, state.spatialId, state.targetSpatialId,
      state.spatialTarget, state.target,
      active.spatial_node_id, active.spatial_id, active.spatialId, active.targetSpatialId,
      manager?.spatialTarget, manager?.target
    ];
    return candidates.map(idFrom).find(Boolean) || '';
  };
  const contractTarget = () => idFrom(window.testhpSpatialContract?.getTarget?.());
  const selectedTarget = () => idFrom(window.selectedSpatialNode);
  const evidenceTarget = () => idFrom(window.spatialEvidenceTarget);
  const currentNode = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || '';
  const currentPath = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const registry = () => window.__testhpTwinRegistryDiagnostics || {};
  const evidence = () => {
    try {
      const value = JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2') || '{}');
      return Array.isArray(value.evidence) ? value.evidence.filter(x => !x.archived) : [];
    } catch { return []; }
  };
  const recordTarget = record => idFrom(first(record, ['spatial_node_id','spatial_id','spatialId']) || first(record?.target || {}, ['spatial_node_id','spatial_id','spatialId']) || record?.target);
  const targetEvidence = id => evidence().filter(record => recordTarget(record) === id);

  function relation(expected, actual) {
    const e = normalize(expected), a = normalize(actual);
    if (!e || !a) return 'MISSING';
    if (e === a) return 'EXACT';
    if (e.startsWith(a + '/')) return 'EXPECTED_IS_DESCENDANT';
    if (a.startsWith(e + '/')) return 'ACTUAL_IS_DESCENDANT';
    return 'UNRELATED';
  }

  function diagnose() {
    const manager = managerTarget();
    const contract = contractTarget();
    const selected = selectedTarget();
    const evidenceGlobal = evidenceTarget();
    const id = manager || contract || selected || evidenceGlobal || '';
    const values = [manager, contract, selected, evidenceGlobal].filter(Boolean);
    const allExact = !!id && values.every(value => value === id);
    const targetDrift = !!id && values.some(value => value !== id);
    const d = registry();
    const linked = Array.isArray(d.targetRecords) ? d.targetRecords : [];
    const cacheLinked = targetEvidence(id);
    const targetLinked = Number(d.matchDebug?.exact_count ?? d.targetLinked ?? linked.length ?? 0);
    const prepared = Number(d.prepared ?? 0);
    const views = Number(d.viewsTargetScoped ?? d.matchDebug?.views_target_scoped ?? 0);

    let diagnosis = 'NO_TARGET';
    if (id && targetDrift) diagnosis = 'TARGET_DRIFT';
    else if (id && targetLinked === 0 && cacheLinked.length === 0) diagnosis = 'TARGET_DATA_MISSING';
    else if (id && targetLinked > 0 && prepared === 0) diagnosis = 'ASSET_PREPARATION_MISSING';
    else if (id && prepared > 0 && views === 0) diagnosis = 'TARGET_VIEWS_MISSING';
    else if (id) diagnosis = 'TARGET_CONSISTENT';

    return { id, manager, contract, selected, evidenceGlobal, allExact, targetDrift, diagnosis, targetLinked, prepared, views, cacheLinked: cacheLinked.length, currentNode: currentNode(), path: currentPath(), registry: d };
  }

  function installRegistryCacheMismatchCollapse() {
    if (window.__testhpRegistryCacheMismatchCollapseInstalled) return;
    window.__testhpRegistryCacheMismatchCollapseInstalled = true;

    const wanted = 'REGISTRY / CACHE MISMATCH DIAGNOSTICS';
    const normalizeHeading = value => String(value || '').replace(/\s+/g, ' ').trim().toUpperCase();

    const findHeading = () => {
      const candidates = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,strong,b,summary,div,section')];
      return candidates.find(el => normalizeHeading(el.textContent) === wanted) || null;
    };

    const collapse = () => {
      const heading = findHeading();
      if (!heading) return false;
      if (heading.closest('details[data-testhp-registry-cache-mismatch]')) return true;

      // Collapse the diagnostic block only. Other controls and panels remain unchanged.
      const boundary = heading.closest('section,article,fieldset,.tvd-section,.hss-section,.hss-card,.debug-panel') || heading.parentElement;
      if (!boundary || boundary.dataset.testhpRegistryCacheMismatchWrapped === '1') return true;

      const details = document.createElement('details');
      details.dataset.testhpRegistryCacheMismatch = '1';
      details.open = false;
      details.style.cssText = 'margin-top:10px;';

      const summary = document.createElement('summary');
      summary.textContent = wanted;
      summary.style.cssText = 'cursor:pointer;font-weight:800;';

      const body = document.createElement('div');
      body.dataset.testhpRegistryCacheMismatchBody = '1';
      while (boundary.firstChild) body.appendChild(boundary.firstChild);

      details.append(summary, body);
      boundary.dataset.testhpRegistryCacheMismatchWrapped = '1';
      boundary.appendChild(details);
      return true;
    };

    const run = () => collapse();
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once:true });
    else run();

    const observer = new MutationObserver(() => {
      if (!document.querySelector('details[data-testhp-registry-cache-mismatch]')) collapse();
    });
    if (document.body) observer.observe(document.body, { childList:true, subtree:true });
    window.addEventListener('testhp:evidence-registry-debug', run);
    window.addEventListener('testhp:evidence-registry-synced', run);
  }

  function render() {
    const panel = document.getElementById('hand-surface-debug-flow');
    if (!panel) return;
    const old = document.getElementById('hsd-target-consistency');
    if (old) old.remove();
    const result = diagnose();
    const box = document.createElement('details');
    box.id = 'hsd-target-consistency';
    box.open = true;
    box.style.cssText = 'margin-top:10px;padding:9px;border:1px solid #52647a;border-radius:8px;background:#0b1320;color:#dbe7f5;font:11px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;';
    const driftLabel = result.targetDrift ? 'DRIFT' : 'EXACT';
    const status = result.diagnosis === 'TARGET_DATA_MISSING' ? 'DATA MISSING' : result.diagnosis.replaceAll('_',' ');
    box.innerHTML = `<summary style="cursor:pointer;color:#9fc4e8;font-weight:800">TARGET CONSISTENCY · ${status}</summary><pre style="white-space:pre-wrap;margin:8px 0 0;color:#aebed0">` +
      `DIAGNOSIS\n` +
      `  routing       PASS\n` +
      `  target        ${driftLabel}\n` +
      `  data          ${result.targetLinked > 0 ? 'PRESENT' : 'MISSING'}\n` +
      `  registry      ${result.targetLinked > 0 ? 'LINKED' : 'UNLINKED'}\n` +
      `  prepared      ${result.prepared}\n` +
      `  views         ${result.views}\n\n` +
      `TARGET SOURCES\n` +
      `  manager       ${result.manager || 'NULL'}  [${relation(result.id,result.manager)}]\n` +
      `  contract      ${result.contract || 'NULL'}  [${relation(result.id,result.contract)}]\n` +
      `  selected      ${result.selected || 'NULL'}  [${relation(result.id,result.selected)}]\n` +
      `  evidence      ${result.evidenceGlobal || 'NULL'}  [${relation(result.id,result.evidenceGlobal)}]\n` +
      `  resolved      ${result.id || 'NULL'}\n\n` +
      `REGISTRY\n` +
      `  raw           ${result.registry.rawCount ?? result.registry.raw_count ?? result.registry.total ?? 'NULL'}\n` +
      `  scoped        ${result.registry.matchDebug?.scoped_count ?? 'NULL'}\n` +
      `  exact         ${result.registry.matchDebug?.exact_count ?? result.registry.targetLinked ?? 'NULL'}\n` +
      `  rejected      ${result.registry.matchDebug?.rejected_count ?? 'NULL'}\n` +
      `  prepared      ${result.registry.prepared ?? 'NULL'}\n` +
      `  endpoint      ${result.registry.endpoint || 'NULL'}\n\n` +
      `PROVENANCE\n` +
      `  path          ${result.path.join(' > ') || 'NULL'}\n` +
      `  node          ${result.currentNode || 'NULL'}\n` +
      `  cache-linked  ${result.cacheLinked}\n` +
      `  fingerprint  ${fingerprint(result.id)}\n\n` +
      (result.diagnosis === 'TARGET_DATA_MISSING'
        ? 'CONCLUSION\n  Target routing is consistent. No target-linked registry/evidence record exists.\n'
        : result.diagnosis === 'TARGET_DRIFT'
          ? 'CONCLUSION\n  Target IDs disagree. Display labels are ignored; compare only ID-bearing sources.\n'
          : 'CONCLUSION\n  All available ID-bearing target sources agree. Continue downstream inspection.\n') +
      '</pre>`;
    panel.appendChild(box);
    installRegistryCacheMismatchCollapse();
  }

  function fingerprint(value) {
    const s = String(value || ''); let h = 2166136261;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return ('00000000' + (h >>> 0).toString(16)).slice(-8);
  }

  function schedule() {
    let tries = 0;
    const timer = setInterval(() => { render(); if (++tries >= 80) clearInterval(timer); }, 250);
    window.addEventListener('testhp:spatial-layer-changed', render);
    window.addEventListener('testhp:spatial-contract-changed', render);
    window.addEventListener('testhp:evidence-registry-updated', render);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule, {once:true});
  else schedule();
})();
