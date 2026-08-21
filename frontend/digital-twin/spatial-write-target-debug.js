(() => {
  'use strict';

  // Debug-only instrumentation. It does not change the write contract; it observes
  // the selected target, the region-data form, local persistence and observation API.
  let last = {
    navigation: null,
    inspector: null,
    form: null,
    persisted: null,
    request: null,
    result: null,
    at: null
  };
  let observerBound = false;
  let fetchBound = false;

  const normalize = value => typeof value === 'string'
    ? value.replace(/^\/+|\/+$/g, '')
    : '';

  const currentNavigation = () => {
    const node = window.selectedSpatialNode;
    const id = normalize(node?.spatial_id || node?.id || window.spatialEvidenceTarget || '');
    const path = [...document.querySelectorAll('#spatial-breadcrumb button')]
      .map(x => x.textContent.trim()).filter(Boolean).join(' > ');
    const label = document.querySelector('#spatial-node strong')?.textContent?.trim() || '?';
    return { spatial_id: id || '(none)', label, path: path || '(root)' };
  };

  const currentInspector = () => {
    const badge = document.getElementById('zone-label');
    const title = document.getElementById('region-title');
    const node = window.selectedSpatialNode;
    return {
      spatial_id: normalize(node?.spatial_id || node?.id || window.spatialEvidenceTarget || ''),
      label: title?.textContent?.trim() || badge?.textContent?.trim() || '?'
    };
  };

  const ensurePanel = () => {
    const panel = document.getElementById('twin-debug-panel');
    if (!panel) return null;
    let box = document.getElementById('twin-debug-write-target');
    if (!box) {
      box = document.createElement('pre');
      box.id = 'twin-debug-write-target';
      panel.appendChild(box);
    }
    box.style.margin = '10px 0 0';
    box.style.padding = '10px';
    box.style.border = '1px solid rgba(75,116,107,.8)';
    box.style.borderRadius = '8px';
    box.style.whiteSpace = 'pre-wrap';
    box.style.font = '11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace';
    box.style.color = '#dcece6';
    return box;
  };

  const render = () => {
    const box = ensurePanel();
    if (!box) return;
    const n = last.navigation || currentNavigation();
    const i = last.inspector || currentInspector();
    const f = last.form;
    const p = last.persisted;
    const r = last.request;
    const same = (a, b) => !!a && !!b && normalize(a) === normalize(b);
    const selected = normalize(n?.spatial_id || '');
    const formTarget = normalize(f?.spatial_id || '');
    const persistedTarget = normalize(p?.spatial_id || '');
    const requestTarget = normalize(r?.spatial_id || '');
    const targetChain = [selected, normalize(i?.spatial_id || ''), formTarget, persistedTarget, requestTarget].filter(Boolean);
    const chainPass = targetChain.length > 0 && targetChain.every(x => x === selected);
    const formPass = f ? same(selected, formTarget) : null;
    const persistencePass = p ? same(selected, persistedTarget) : null;
    const requestPass = r ? same(selected, requestTarget) : null;
    const overall = last.result || (chainPass ? 'PASS' : 'WAITING');

    box.textContent = [
      'WRITE TARGET CONTRACT',
      '────────────────────────────────────────',
      `navigation spatial_id: ${n?.spatial_id || '(none)'}`,
      `navigation label:      ${n?.label || '?'}`,
      `navigation path:       ${n?.path || '?'}`,
      `inspector spatial_id:   ${i?.spatial_id || '(none)'}`,
      `form spatial_id:        ${f?.spatial_id || '(not captured)'}`,
      `biological_level:       ${f?.biological_level || '(not captured)'}`,
      `persisted spatial_id:   ${p?.spatial_id || '(not captured)'}`,
      `request spatial_id:     ${r?.spatial_id || '(not captured)'}`,
      '',
      'TARGET EQUALITY',
      `  navigation = inspector: ${same(n?.spatial_id, i?.spatial_id) ? 'PASS' : 'FAIL'}`,
      `  navigation = form:      ${formPass === null ? 'WAITING' : formPass ? 'PASS' : 'FAIL'}`,
      `  navigation = persisted: ${persistencePass === null ? 'WAITING' : persistencePass ? 'PASS' : 'FAIL'}`,
      `  navigation = request:   ${requestPass === null ? 'WAITING' : requestPass ? 'PASS' : 'FAIL'}`,
      '',
      'WRITE RULE',
      '  add/edit data must target EXACTLY selected navigation spatial_id',
      '  parent target: BLOCKED',
      '  descendant target: BLOCKED',
      '  sibling target: BLOCKED',
      '  biological_level does not change spatial target',
      '',
      `CONTRACT RESULT: ${overall}`,
      last.at ? `last write diagnostic: ${last.at}` : 'last write diagnostic: waiting for Add/Edit data',
      r?.method ? `last observation API: ${r.method} ${r.url || ''} · spatial_id=${r.spatial_id || '(none)'}` : 'last observation API: not captured'
    ].join('\n');
  };

  const captureForm = () => {
    const form = document.getElementById('ri-data-form');
    if (!form || form.dataset.writeDebugBound) return;
    form.dataset.writeDebugBound = '1';
    form.addEventListener('submit', () => {
      const nav = currentNavigation();
      const inspector = currentInspector();
      last.navigation = nav;
      last.inspector = inspector;
      last.form = {
        spatial_id: normalize(window.selectedSpatialNode?.spatial_id || window.selectedSpatialNode?.id || window.spatialEvidenceTarget || ''),
        biological_level: document.getElementById('ri-data-type')?.value || '',
        name: document.getElementById('ri-data-name')?.value?.trim() || '',
        mode: document.getElementById('ri-data-id')?.value ? 'edit' : 'create'
      };
      last.result = normalize(last.form.spatial_id) === normalize(nav.spatial_id) ? 'PASS' : 'FAIL';
      last.at = new Date().toISOString();
      render();
    }, true);
  };

  const capturePersistence = () => {
    const raw = localStorage.getItem('digitalTwinRegionData.v1');
    if (!raw) return;
    try {
      const payload = JSON.parse(raw);
      const items = Array.isArray(payload?.items) ? payload.items : [];
      const nav = currentNavigation();
      const relevant = items.filter(x => x?.target && x.updatedAt).sort((a,b) => String(b.updatedAt).localeCompare(String(a.updatedAt)))[0];
      if (relevant) {
        last.persisted = {
          spatial_id: normalize(relevant.target),
          item_id: relevant.id || '',
          biological_level: relevant.type || '',
          name: relevant.name || ''
        };
        if (last.form && last.form.name === relevant.name) {
          last.navigation = nav;
          last.result = normalize(relevant.target) === normalize(nav.spatial_id) ? 'PASS' : 'FAIL';
          last.at = new Date().toISOString();
        }
      }
    } catch (_) {}
  };

  const bindFetch = () => {
    if (fetchBound || typeof window.fetch !== 'function') return;
    fetchBound = true;
    const original = window.fetch.bind(window);
    window.fetch = async (...args) => {
      const input = args[0];
      const init = args[1] || {};
      const url = typeof input === 'string' ? input : input?.url || '';
      const method = String(init.method || (typeof input !== 'string' && input?.method) || 'GET').toUpperCase();
      if (url.includes('/api/observations') && ['POST','PUT','PATCH'].includes(method)) {
        let body = init.body;
        try {
          if (typeof body === 'string') body = JSON.parse(body);
        } catch (_) {}
        const spatialId = normalize(body?.spatial_id || '');
        last.request = { method, url, spatial_id: spatialId, biological_level: body?.biological_level || '' };
        const nav = currentNavigation();
        last.result = spatialId && spatialId === normalize(nav.spatial_id) ? 'PASS' : 'FAIL';
        last.at = new Date().toISOString();
        render();
      }
      const response = await original(...args);
      setTimeout(() => { capturePersistence(); render(); }, 0);
      return response;
    };
  };

  const bind = () => {
    if (observerBound) return;
    observerBound = true;
    bindFetch();
    const observer = new MutationObserver(() => { captureForm(); capturePersistence(); render(); });
    observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener('testhp:spatial-layer-changed', () => { last.navigation = currentNavigation(); last.inspector = currentInspector(); render(); });
    window.addEventListener('testhp:region-data-changed', () => { capturePersistence(); render(); });
    window.addEventListener('testhp:evidence-ux-refresh', () => { capturePersistence(); render(); });
    captureForm();
    capturePersistence();
    render();
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind, { once: true });
  else bind();
})();
