(() => {
  const root = document.querySelector('.app-shell');
  if (!root) return;

  const subjectId = 'own_cohort';
  const timepoint = 'T0';
  const STORAGE = 'digitalTwinEvidenceUX.v2';
  const $ = (id) => document.getElementById(id);
  const timeoutFetch = (url, options = {}, ms = 8000) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), ms);
    return fetch(url, {...options, signal: controller.signal}).finally(() => clearTimeout(timer));
  };

  const slug = (value) => String(value || '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const childId = (parent, label) => {
    const key = String(label || '').toLowerCase().trim();
    const direct = {palm:'palm',thumb:'thumb',index:'index',middle:'middle',ring:'ring',little:'little',wrist:'wrist',thenar:'thenar',hypothenar:'hypothenar','central palm':'central-palm'};
    if (direct[key]) return direct[key];
    if (key === 'proximal segment') return `${parent}-proximal`;
    if (key === 'middle segment') return `${parent}-middle`;
    if (key === 'distal segment') return `${parent}-distal`;
    const field = key.match(/microscopy field\s*([abc])/i);
    if (field) return `${parent}-field-${field[1].toLowerCase()}`;
    const cell = key.match(/cell target\s*(\d+)/i);
    if (cell) return `${parent}-cell-${cell[1]}`;
    return slug(label);
  };

  const breadcrumbLabels = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(b => b.textContent.trim()).filter(Boolean);
  const nodeIdFromBreadcrumb = () => {
    const labels = breadcrumbLabels();
    if (!labels.length) return 'hand';
    const ids = ['hand'];
    labels.slice(1).forEach(label => ids.push(childId(ids[ids.length - 1], label)));
    return ids.join('/');
  };

  const syncCanonicalTarget = () => {
    const labels = breadcrumbLabels();
    const nodeId = nodeIdFromBreadcrumb();
    const label = labels.length ? labels.join(' > ') : 'Hand';
    window.spatialEvidenceTarget = nodeId;
    window.selectedSpatialNode = nodeId;
    document.body.dataset.spatialTarget = nodeId;
    const targetLabel = $('evidence-target-label');
    if (targetLabel) targetLabel.textContent = ` · ${label}`;
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-changed', {detail:{spatial_target_id:nodeId,label}}));
    return nodeId;
  };

  const ensureInitialSpatialTarget = () => {
    const breadcrumb = $('spatial-breadcrumb');
    if (!breadcrumb) return false;
    const labels = breadcrumbLabels();
    if (!labels.length) return false;
    if (labels.length === 1 && labels[0].toLowerCase() === 'hand') {
      const palm = [...document.querySelectorAll('#spatial-children button')].find(b => b.textContent.trim().toLowerCase().startsWith('palm'));
      if (palm) {
        palm.click();
        return true;
      }
      return false;
    }
    syncCanonicalTarget();
    return true;
  };

  const hideDeveloperDebug = () => {
    document.querySelectorAll('*').forEach(el => {
      if (el.children.length > 8) return;
      const text = (el.textContent || '').trim();
      if (/^TWIN-VIEWPORT DEBUG/i.test(text) || /^TWIN-VIEWPORT DEBUGCLEAR/i.test(text) || /^DEBUG$/i.test(text)) {
        el.style.display = 'none';
        el.setAttribute('aria-hidden', 'true');
      }
    });
  };

  const cleanLegacyActions = () => {
    document.querySelectorAll('#evidence-workspace button').forEach(button => {
      if (/^\s*[＋+]\s*Add observation\s*$/i.test(button.textContent || '')) button.textContent = '＋ Add biological observation';
    });
    document.querySelectorAll('button').forEach(button => {
      if (button.closest('#evidence-workspace')) return;
      if (/^\s*[＋+]\s*Add observation\s*$/i.test((button.textContent || '').trim())) button.remove();
    });
  };

  const seedEvidenceFromBackend = async () => {
    try {
      const response = await timeoutFetch(`/api/hand/analysis?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}`);
      if (!response.ok) return 0;
      const analysis = await response.json();
      const assets = (analysis.assets || []).filter(x => ['ready','available'].includes(String(x.status || '').toLowerCase()));
      const handAssets = assets.filter(x => String(x.modality || '').toLowerCase() === 'hand');
      let stored = {};
      try { stored = JSON.parse(localStorage.getItem(STORAGE) || '{}'); } catch {}
      const evidence = Array.isArray(stored.evidence) ? stored.evidence : [];
      const existingIds = new Set(evidence.map(x => x.backendAssetId || x.id));
      handAssets.forEach(asset => {
        if (existingIds.has(asset.asset_id)) return;
        evidence.push({
          id:`backend-${asset.asset_id}`, backendAssetId:asset.asset_id, type:'Macro', sourceType:'upload',
          target:'hand/palm', timepoint:asset.timepoint || timepoint, date:asset.date || new Date().toISOString().slice(0,10),
          modality:'Hand image', resolution:asset.resolution || '', subject:asset.subject_id || subjectId, operator:asset.operator || '',
          filename:asset.filename || asset.view || `hand-${asset.asset_id}`, fileData:'', signals:[], annotations:'',
          comments:'Imported from registered hand evidence.', history:[{at:new Date().toISOString(),action:'imported from registry'}], archived:false
        });
      });
      localStorage.setItem(STORAGE, JSON.stringify({evidence,target:nodeIdFromBreadcrumb()}));
      window.dispatchEvent(new CustomEvent('testhp:evidence-registry-synced',{detail:{count:handAssets.length}}));
      return handAssets.length;
    } catch (error) {
      console.warn('Evidence registry seed failed', error);
      return 0;
    }
  };

  const renderHierarchy = (nodes) => {
    const container = $('stage24-hierarchy');
    if (!container) return;
    container.replaceChildren();
    nodes.forEach(node => {
      const card = document.createElement('div');
      card.className = 'state-card';
      const age = node.biological_age?.overall;
      card.innerHTML = `<span>${node.node_id}</span><strong>${age == null ? 'Not established' : `${age} · proxy`}</strong><small>${node.status === 'observed' ? 'Observed' : 'Insufficient evidence'} · ${node.evidence_count || 0} evidence item(s)</small>`;
      container.appendChild(card);
    });
    if (!nodes.length) container.innerHTML = '<div class="state-card"><span>Hierarchy</span><strong>Not established</strong><small>Attach evidence to begin aggregation.</small></div>';
  };

  const refreshState = async () => {
    const nodeId = syncCanonicalTarget();
    try {
      const [stateResponse, summaryResponse] = await Promise.all([
        timeoutFetch(`/api/spatial/state?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}&spatial_node_id=${encodeURIComponent(nodeId)}`),
        timeoutFetch('/api/spatial/summary',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subject_id:subjectId,timepoint,root_node_id:nodeId})})
      ]);
      if (!stateResponse.ok || !summaryResponse.ok) return;
      const state = await stateResponse.json();
      const summary = await summaryResponse.json();
      const age = state.biological_age?.overall;
      if ($('age-state')) $('age-state').textContent = age == null ? 'Not established' : `${age} · research proxy`;
      const signals = state.signals || {};
      const set = (id,value) => { const el=$(id); if(el) el.textContent=value == null ? 'Not established' : `${value} · observed signal`; };
      set('structure-state',signals.elasticity?.value ?? signals.collagen_structure?.value ?? signals.health_score?.value);
      set('damage-state',signals.stress_score?.value ?? signals.fibrosis?.value);
      set('pathology-state',signals.inflammation?.value);
      if ($('confidence-state')) $('confidence-state').textContent = state.evidence_count ? `${state.evidence_count} evidence item(s)` : 'Insufficient evidence';
      if ($('evidence-level')) $('evidence-level').textContent = state.evidence_count ? 'Explicitly attached research evidence' : 'Insufficient evidence';
      renderHierarchy(summary.nodes || []);
      window.dispatchEvent(new CustomEvent('testhp:spatial-state',{detail:{nodeId,state,summary}}));
    } catch (error) {
      console.warn('Stage 2–4 refresh failed', error);
    }
  };

  const installHierarchyPanel = () => {
    if ($('stage24-hierarchy')) return;
    const hierarchyPanel = document.createElement('section');
    hierarchyPanel.className = 'panel';
    hierarchyPanel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">HIERARCHICAL SUMMARY</span><strong>MACRO → TISSUE → CELLULAR → CELL</strong></div><span class="research-badge">STAGE 4</span></div><div id="stage24-hierarchy" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px"></div><p class="muted" style="margin-top:12px">Parent summaries aggregate only explicitly attached descendant evidence. They never create evidence where none exists.</p>`;
    $('state-panel')?.after(hierarchyPanel);
  };

  const boot = async () => {
    installHierarchyPanel();
    hideDeveloperDebug();
    let ready = false;
    for (let i = 0; i < 30 && !ready; i++) {
      ready = ensureInitialSpatialTarget();
      if (!ready) await new Promise(resolve => setTimeout(resolve, 100));
    }
    if (!ready) syncCanonicalTarget();
    const count = await seedEvidenceFromBackend();
    cleanLegacyActions();
    await refreshState();
    const status = $('twin-status');
    if (status) status.textContent = count ? `${count} macro observations loaded` : 'Digital Twin ready';
    hideDeveloperDebug();
    cleanLegacyActions();
  };

  const breadcrumb = $('spatial-breadcrumb');
  if (breadcrumb) new MutationObserver(() => { hideDeveloperDebug(); cleanLegacyActions(); }).observe(breadcrumb,{childList:true,subtree:true});
  new MutationObserver(() => { hideDeveloperDebug(); cleanLegacyActions(); }).observe(root,{childList:true,subtree:true});
  window.addEventListener('testhp:evidence-attached',refreshState);
  window.addEventListener('testhp:spatial-target-changed',() => { cleanLegacyActions(); refreshState(); });
  window.addEventListener('testhp:evidence-registry-synced',cleanLegacyActions);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',boot,{once:true}); else boot();
})();