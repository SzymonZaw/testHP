(() => {
  const root = document.querySelector('.app-shell');
  if (!root) return;
  const subjectId = 'own_cohort';
  const timepoint = 'T0';
  const slug = (value) => value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const childId = (parent, label) => {
    const key = label.toLowerCase().trim();
    const direct = { 'palm':'palm', 'thumb':'thumb', 'index':'index', 'middle':'middle', 'ring':'ring', 'little':'little', 'wrist':'wrist', 'thenar':'thenar', 'hypothenar':'hypothenar', 'central palm':'central-palm' };
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

  const attachPanel = document.createElement('section');
  attachPanel.className = 'panel';
  attachPanel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">EVIDENCE MANAGEMENT</span><strong>ATTACH TO SELECTED TARGET</strong></div><span class="research-badge">STAGE 2</span></div><div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:0 0 12px"><label>Modality<select id="stage24-modality"><option value="hand">Macro</option><option value="wsi">Tissue / WSI</option><option value="images">Cellular / microscopy</option><option value="rna">Molecular</option><option value="metadata">Structured metadata</option></select></label><label>Resolution<input id="stage24-resolution" placeholder="e.g. 2 µm/px"></label><label>Source<input id="stage24-source" placeholder="camera / lab / dataset"></label><label>Evidence file<input id="stage24-file" type="file"></label></div><label>Research signals (optional JSON)<textarea id="stage24-signals" rows="4" placeholder='{"macro_age": 41, "wrinkles": 32, "elasticity": 74}'></textarea><div style="display:flex;justify-content:space-between;gap:12px;align-items:center;margin-top:12px"><small id="stage24-target">Target: Hand · macro</small><button id="stage24-attach" class="primary" type="button">Attach evidence</button></div><p id="stage24-message" class="muted" style="margin-top:10px">Evidence is linked to the selected spatial node. Missing signals remain explicitly unestablished.</p>`;
  root.querySelector('.timeline')?.before(attachPanel);

  const hierarchyPanel = document.createElement('section');
  hierarchyPanel.className = 'panel';
  hierarchyPanel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">HIERARCHICAL SUMMARY</span><strong>MACRO → TISSUE → CELLULAR → CELL</strong></div><span class="research-badge">STAGE 4</span></div><div id="stage24-hierarchy" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px"></div><p class="muted" style="margin-top:12px">Parent summaries aggregate only explicitly attached descendant evidence. They never create evidence where none exists.</p>`;
  root.querySelector('.state-panel')?.after(hierarchyPanel);

  const message = (text, error = false) => { const el = document.getElementById('stage24-message'); if (el) { el.textContent = text; el.dataset.error = error ? 'true' : 'false'; } };

  async function refreshState() {
    const nodeId = nodeIdFromBreadcrumb();
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
    const target = document.getElementById('stage24-target');
    if (target) target.textContent = `Target: ${nodeId} · ${currentLevel()}`;
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

  document.getElementById('stage24-attach')?.addEventListener('click', async () => {
    const file = document.getElementById('stage24-file')?.files?.[0];
    if (!file) return message('Select an evidence file first.', true);
    let signals = {};
    const raw = document.getElementById('stage24-signals')?.value?.trim();
    if (raw) { try { signals = JSON.parse(raw); } catch { return message('Signals must be valid JSON.', true); } }
    const fd = new FormData();
    const level = currentLevel();
    fd.append('file', file); fd.append('subject_id', subjectId); fd.append('timepoint', timepoint); fd.append('spatial_node_id', nodeIdFromBreadcrumb());
    fd.append('spatial_level', level === 'macro' ? 'macro' : level === 'tissue' ? 'tissue' : level === 'cellular' ? 'cellular' : 'cell');
    fd.append('modality', document.getElementById('stage24-modality').value); fd.append('resolution', document.getElementById('stage24-resolution').value); fd.append('source', document.getElementById('stage24-source').value); fd.append('signals_json', JSON.stringify(signals));
    message('Attaching evidence…');
    try {
      const response = await fetch('/api/spatial/attach', {method: 'POST', body: fd});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Attachment failed');
      message(`Attached ${payload.evidence.filename} to ${payload.evidence.spatial_node_id}.`);
      document.getElementById('stage24-file').value = '';
      await refreshState();
      window.dispatchEvent(new CustomEvent('testhp:evidence-attached', {detail: payload}));
    } catch (error) { message(error.message, true); }
  });

  const observer = new MutationObserver(() => refreshState().catch(() => {}));
  const breadcrumb = document.getElementById('spatial-breadcrumb');
  if (breadcrumb) observer.observe(breadcrumb, {childList: true, subtree: true});
  refreshState().catch(() => {});
})();
