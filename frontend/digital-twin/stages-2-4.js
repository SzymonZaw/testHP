(() => {
  const root = document.querySelector('.app-shell');
  if (!root) return;
  const subjectId = 'own_cohort';
  const timepoint = 'T0';
  const slug = (value) => value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const childId = (parent, label) => {
    const key = label.toLowerCase().trim();
    const direct = { palm:'palm', thumb:'thumb', index:'index', middle:'middle', ring:'ring', little:'little', wrist:'wrist', thenar:'thenar', hypothenar:'hypothenar', 'central palm':'central-palm' };
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
  const nodeIdFromBreadcrumb = () => {
    const labels = [...document.querySelectorAll('#spatial-breadcrumb button')].map((b) => b.textContent.trim()).filter(Boolean);
    if (!labels.length) return 'hand';
    const ids = ['hand'];
    labels.slice(1).forEach((label) => ids.push(childId(ids[ids.length - 1], label)));
    return ids.join('/');
  };
  const currentLevel = () => (document.getElementById('spatial-level-badge')?.textContent || 'MACRO').toLowerCase().replace(' ', '');

  const hierarchyPanel = document.createElement('section');
  hierarchyPanel.className = 'panel';
  hierarchyPanel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">HIERARCHICAL SUMMARY</span><strong>MACRO → TISSUE → CELLULAR → CELL</strong></div><span class="research-badge">STAGE 4</span></div><div id="stage24-hierarchy" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px"></div><p class="muted" style="margin-top:12px">Parent summaries aggregate only explicitly attached descendant evidence. They never create evidence where none exists.</p>`;
  root.querySelector('.state-panel')?.after(hierarchyPanel);

  function syncCanonicalTarget() {
    const nodeId = nodeIdFromBreadcrumb();
    const label = [...document.querySelectorAll('#spatial-breadcrumb button')].map((b) => b.textContent.trim()).filter(Boolean).join(' > ') || 'Hand';
    window.spatialEvidenceTarget = nodeId;
    window.selectedSpatialNode = nodeId;
    document.body.dataset.spatialTarget = nodeId;
    const targetLabel = document.getElementById('evidence-target-label');
    if (targetLabel) targetLabel.textContent = label;
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-changed', { detail: { spatial_target_id: nodeId, label } }));
    return nodeId;
  }

  function ensureInitialSpatialTarget() {
    const breadcrumb = document.getElementById('spatial-breadcrumb');
    if (!breadcrumb) return;
    const buttons = [...breadcrumb.querySelectorAll('button')];
    if (buttons.length === 1 && buttons[0].textContent.trim().toLowerCase() === 'hand') {
      const palm = [...document.querySelectorAll('#spatial-children button')].find((b) => b.textContent.trim().toLowerCase().startsWith('palm'));
      if (palm) palm.click();
    }
    syncCanonicalTarget();
  }

  function cleanupLegacyEvidenceActions() {
    document.querySelectorAll('#evidence-workspace').forEach((panel) => {
      panel.querySelectorAll('button').forEach((button) => {
        if (/^\s*[＋+]\s*Add observation\s*$/i.test(button.textContent || '')) button.textContent = '＋ Add biological observation';
      });
    });
    document.querySelectorAll('button').forEach((button) => {
      if (button.closest('#evidence-workspace')) return;
      const text = (button.textContent || '').trim();
      if (/^\s*[＋+]\s*Add observation\s*$/i.test(text)) button.remove();
    });
  }

  async function refreshState() {
    const nodeId = syncCanonicalTarget();
    try {
      const [stateResponse, summaryResponse] = await Promise.all([
        fetch(`/api/spatial/state?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}&spatial_node_id=${encodeURIComponent(nodeId)}`),
        fetch('/api/spatial/summary', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({subject_id: subjectId, timepoint, root_node_id: nodeId}) })
      ]);
      if (!stateResponse.ok || !summaryResponse.ok) return;
      const state = await stateResponse.json();
      const summary = await summaryResponse.json();
      const age = state.biological_age?.overall;
      const ageEl = document.getElementById('age-state');
      if (ageEl) ageEl.textContent = age == null ? 'Not established' : `${age} · research proxy`;
      const signals = state.signals || {};
      const set = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value == null ? 'Not established' : `${value} · observed signal`; };
      set('structure-state', signals.elasticity?.value ?? signals.collagen_structure?.value ?? signals.health_score?.value);
      set('damage-state', signals.stress_score?.value ?? signals.fibrosis?.value);
      set('pathology-state', signals.inflammation?.value);
      const conf = document.getElementById('confidence-state');
      if (conf) conf.textContent = state.evidence_count ? `${state.evidence_count} evidence item(s)` : 'Insufficient evidence';
      const level = document.getElementById('evidence-level');
      if (level) level.textContent = state.evidence_count ? 'Explicitly attached research evidence' : 'Insufficient evidence';
      renderHierarchy(summary.nodes || []);
      window.dispatchEvent(new CustomEvent('testhp:spatial-state', { detail: { nodeId, state, summary } }));
    } catch (error) {
      console.warn('Stage 2–4 refresh failed', error);
    }
  }

  function renderHierarchy(nodes) {
    const container = document.getElementById('stage24-hierarchy');
    if (!container) return;
    container.replaceChildren();
    nodes.forEach((node) => {
      const card = document.createElement('div'); card.className = 'state-card';
      const age = node.biological_age?.overall;
      const status = node.status === 'observed' ? 'Observed' : 'Insufficient evidence';
      card.innerHTML = `<span>${node.node_id}</span><strong>${age == null ? 'Not established' : `${age} · proxy`}</strong><small>${status} · ${node.evidence_count} evidence item(s)</small>`;
      container.appendChild(card);
    });
    if (!nodes.length) container.innerHTML = '<div class="state-card"><span>Hierarchy</span><strong>Not established</strong><small>Attach evidence to begin aggregation.</small></div>';
  }

  const observer = new MutationObserver(() => { syncCanonicalTarget(); cleanupLegacyEvidenceActions(); });
  const breadcrumb = document.getElementById('spatial-breadcrumb');
  if (breadcrumb) observer.observe(breadcrumb, {childList: true, subtree: true});
  const shellObserver = new MutationObserver(() => cleanupLegacyEvidenceActions());
  shellObserver.observe(root, {childList: true, subtree: true});
  window.addEventListener('testhp:evidence-attached', () => refreshState());
  window.addEventListener('testhp:spatial-target-changed', () => { cleanupLegacyEvidenceActions(); refreshState(); });
  ensureInitialSpatialTarget();
  cleanupLegacyEvidenceActions();
  refreshState();
})();
