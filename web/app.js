const state = { datasets: [], filter: 'all', lastRun: null, selectedStage: null };

const $ = (id) => document.getElementById(id);

const stageInfo = {
  ingestion_validation: ['Input & validation', 'Read the selected sources and check what is actually available.'],
  ingestion: ['Input & ingestion', 'Read available files from the local data source.'],
  normalization_preprocessing: ['Normalization', 'Convert source files into common observations.'],
  normalization: ['Normalization', 'Convert heterogeneous sources into a common observation contract.'],
  multimodal_fusion: ['Multimodal fusion', 'Aggregate dataset-level evidence without inventing subject links.'],
  quality_uncertainty: ['Quality & uncertainty', 'Check observation quality and propagate evidence limitations.'],
  hierarchical_biological_state: ['Biological state', 'Organize observations into the supported biological hierarchy.'],
  digital_biological_twin: ['Digital twin snapshot', 'Create a provenance-preserving computational state snapshot.'],
  anomaly_longitudinal_analysis: ['Anomaly & longitudinal analysis', 'Look for signals while refusing unsupported trajectory claims.'],
  pipeline_evaluation: ['Research evaluation', 'Summarize evidence coverage and data readiness.'],
  decision_support: ['Research decision support', 'Return a conservative research-level outcome.'],
  audit_and_provenance: ['Audit & provenance', 'Record what happened, when, and with which limitations.'],
};

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function pretty(value) {
  return String(value ?? '').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function statusClass(status) {
  if (['ok', 'completed', 'ready'].includes(status)) return 'ok';
  if (['warning', 'limited', 'review', 'insufficient_data'].includes(status)) return 'warning';
  return 'neutral';
}

function normalizeSteps(data) {
  if (Array.isArray(data.stages) && data.stages.length) {
    return data.stages.map((stage, index) => ({
      stage: stage.stage ?? index + 1,
      name: stage.name,
      status: stage.status || 'review',
      purpose: stageInfo[stage.name]?.[1] || 'Research pipeline stage.',
      ...stage,
    }));
  }
  return (data.steps || []).map((step, index) => ({ stage: index + 1, ...step }));
}

function renderMetrics(summary = {}) {
  const datasets = summary.datasets ?? state.lastRun?.selected?.length ?? 0;
  const files = summary.files ?? state.lastRun?.datasets?.reduce((n, x) => n + (x.files || 0), 0) ?? 0;
  const modalities = summary.modalities || state.lastRun?.fusion?.modalities || [];
  $('metric-datasets').textContent = datasets;
  $('metric-files').textContent = files;
  $('metric-modalities').textContent = modalities.length;
  $('metric-links').textContent = summary.linked_subjects ?? state.lastRun?.fusion?.linked_subjects ?? 0;
}

function stageSummary(stage) {
  const parts = [];
  if (stage.summary && typeof stage.summary === 'object') {
    Object.entries(stage.summary).forEach(([key, value]) => {
      if (value === null || value === undefined || typeof value === 'object') return;
      parts.push(`<div><span>${esc(pretty(key))}</span><strong>${esc(value)}</strong></div>`);
    });
  }
  return parts.join('');
}

function renderPipeline(steps = []) {
  const normalized = steps.length ? steps : [
    {stage: 1, name: 'ingestion_validation', status: 'pending'},
    {stage: 2, name: 'normalization_preprocessing', status: 'pending'},
    {stage: 3, name: 'multimodal_fusion', status: 'pending'},
    {stage: 4, name: 'quality_uncertainty', status: 'pending'},
    {stage: 5, name: 'hierarchical_biological_state', status: 'pending'},
    {stage: 6, name: 'digital_biological_twin', status: 'pending'},
    {stage: 7, name: 'anomaly_longitudinal_analysis', status: 'pending'},
    {stage: 8, name: 'pipeline_evaluation', status: 'pending'},
    {stage: 9, name: 'decision_support', status: 'pending'},
    {stage: 10, name: 'audit_and_provenance', status: 'pending'},
  ];

  $('pipeline').innerHTML = normalized.map((stage, index) => {
    const [title, description] = stageInfo[stage.name] || [pretty(stage.name), stage.purpose || 'Research pipeline stage.'];
    const selected = state.selectedStage === (stage.stage ?? index + 1) ? 'selected' : '';
    return `<button class="stage ${esc(statusClass(stage.status))} ${selected}" data-stage="${stage.stage ?? index + 1}">
      <span class="num">${stage.stage ?? index + 1}</span>
      <span class="stage-copy"><strong>${esc(title)}</strong><span>${esc(stage.status === 'ok' ? 'Completed' : pretty(stage.status || 'Pending'))}</span><p>${esc(description)}</p></span>
    </button>`;
  }).join('');

  document.querySelectorAll('[data-stage]').forEach(button => {
    button.onclick = () => {
      state.selectedStage = Number(button.dataset.stage);
      renderPipeline(normalized);
      renderStageDetail(normalized.find(item => Number(item.stage) === state.selectedStage));
    };
  });
}

function renderStageDetail(stage) {
  const detail = $('stage-detail');
  if (!stage) {
    detail.className = 'stage-detail empty';
    detail.innerHTML = 'Select a pipeline stage to inspect its result.';
    return;
  }
  const [title, description] = stageInfo[stage.name] || [pretty(stage.name), stage.purpose || 'Research pipeline stage.'];
  const reason = stage.reason || stage.note || stage.longitudinal?.note || stage.anomaly?.note || '';
  const nested = stage.longitudinal || stage.anomaly || stage.evaluation || stage.decision;
  detail.className = 'stage-detail';
  detail.innerHTML = `<div class="detail-heading"><div><span class="eyebrow">STAGE ${esc(stage.stage)}</span><h3>${esc(title)}</h3><p>${esc(description)}</p></div><span class="status ${statusClass(stage.status)}">${esc(pretty(stage.status))}</span></div>
    ${stageSummary(stage) ? `<div class="detail-stats">${stageSummary(stage)}</div>` : ''}
    ${nested ? `<pre class="detail-json">${esc(JSON.stringify(nested, null, 2))}</pre>` : ''}
    ${reason ? `<div class="detail-note"><strong>What this means</strong><p>${esc(reason)}</p></div>` : ''}`;
}

function modalityTotals(items) {
  const totals = {};
  items.filter(x => x.valid && x.available).forEach(x => totals[x.modality] = (totals[x.modality] || 0) + (x.supported_files ?? x.files ?? 0));
  return totals;
}

function renderModalities(items) {
  const totals = modalityTotals(items);
  const max = Math.max(1, ...Object.values(totals));
  $('modality-chart').innerHTML = Object.entries(totals).map(([name, value]) => `<div class="bar-row"><strong>${esc(name)}</strong><div class="bar"><i style="width:${Math.round(value/max*100)}%"></i></div><span>${value}</span></div>`).join('') || '<p class="muted">No usable inputs.</p>';
  $('dataset-list').innerHTML = items.filter(x => x.valid && x.available).map(x => `<span class="tag">${esc(x.name)}</span>`).join('') || '<span class="muted">No datasets contributed usable local input.</span>';
}

function renderFilters(items) {
  const modalities = ['all', ...new Set(items.map(x => x.modality))];
  $('filter-buttons').innerHTML = modalities.map(m => `<button class="${state.filter === m ? 'active' : ''}" data-filter="${esc(m)}">${m === 'all' ? 'All' : esc(m)}</button>`).join('');
  document.querySelectorAll('[data-filter]').forEach(btn => btn.onclick = () => {
    state.filter = btn.dataset.filter;
    renderFilters(items);
    renderTable(items);
  });
}

function renderTable(items) {
  const visible = state.filter === 'all' ? items : items.filter(x => x.modality === state.filter);
  $('dataset-table').innerHTML = visible.map(x => {
    const total = x.files || 0;
    const supported = x.supported_files ?? x.files ?? 0;
    const ratio = total ? Math.round((supported / total) * 100) : 0;
    const status = x.valid && x.available ? 'ok' : (x.available ? 'warning' : 'unavailable');
    const label = x.valid && x.available ? 'Available' : (x.available ? 'Review' : 'Unavailable');
    return `<tr><td><strong>${esc(x.name)}</strong></td><td>${esc(x.modality)}</td><td>${esc(x.task)}</td><td>${supported} / ${total}</td><td class="coverage"><div class="coverage-bar"><i style="width:${ratio}%"></i></div></td><td><span class="status ${status}">${label}</span></td></tr>`;
  }).join('');
}

function modalityResultCards(items) {
  const groups = {};
  items.forEach(x => {
    const modality = x.modality || 'unknown';
    if (!groups[modality]) groups[modality] = {datasets: 0, files: 0, supported: 0, warnings: 0, unavailable: 0};
    const g = groups[modality];
    g.datasets += 1;
    g.files += x.files || 0;
    g.supported += x.supported_files ?? (x.status === 'ok' ? x.files || 0 : 0);
    g.warnings += (x.warnings || []).length;
    if (x.available === false || x.status === 'unavailable') g.unavailable += 1;
  });
  return Object.entries(groups).map(([modality, g]) => {
    const pct = g.files ? Math.round(g.supported / g.files * 100) : 0;
    const stateLabel = g.supported > 0 ? (g.warnings || g.unavailable ? 'Usable with limitations' : 'Usable input') : 'No usable input';
    return `<article class="result-card"><div class="result-card-head"><span class="modality-icon">${esc(modality.slice(0, 3).toUpperCase())}</span><div><strong>${esc(modality)}</strong><span>${g.datasets} dataset${g.datasets === 1 ? '' : 's'}</span></div><span class="status ${g.supported ? (g.warnings || g.unavailable ? 'warning' : 'ok') : 'unavailable'}">${stateLabel}</span></div><div class="result-stat"><strong>${g.supported}</strong><span>supported files</span></div><div class="mini-progress"><i style="width:${pct}%"></i></div><p>${pct}% of discovered files are supported. ${g.unavailable ? `${g.unavailable} dataset${g.unavailable === 1 ? '' : 's'} has no usable local input. ` : ''}${g.warnings ? `${g.warnings} validation warning${g.warnings === 1 ? '' : 's'}.` : 'No validation warnings.'}</p></article>`;
  }).join('');
}

function buildFindings(data) {
  const stages = normalizeSteps(data);
  const stage7 = stages.find(s => s.name === 'anomaly_longitudinal_analysis');
  const stage8 = stages.find(s => s.name === 'pipeline_evaluation');
  const stage9 = stages.find(s => s.name === 'decision_support');
  const findings = [];
  if (stage7?.longitudinal?.insufficient_evidence || stage7?.status === 'insufficient_data') findings.push(['Longitudinal inference', 'Not established', 'At least two independent timepoints are required before a trajectory is reported.']);
  if (stage7?.anomaly?.insufficient_evidence) findings.push(['Abnormality inference', 'Not established', stage7.anomaly.note || 'A baseline or reference is required before interpreting an abnormality signal.']);
  if (stage8?.summary?.readiness !== undefined) findings.push(['Pipeline readiness', `${Math.round(Number(stage8.summary.readiness) * 100)}%`, 'This is an engineering/data-readiness measure, not diagnostic accuracy.']);
  if (stage9?.summary?.decision) findings.push(['Research decision', pretty(stage9.summary.decision), (stage9.summary.reasons || []).join(' ') || 'Conservative research-level outcome.']);
  if (!findings.length && data.results) findings.push(['Evidence boundary', pretty(data.results.evidence_level || 'Dataset-level evidence'), data.results.biological_inference || 'No biological conclusion is claimed by this dashboard.']);
  return findings;
}

function renderOutput(data) {
  const datasets = data.datasets || [];
  const usable = datasets.filter(x => x.valid && x.available || x.status === 'ok');
  const limited = datasets.filter(x => (x.warnings || []).length || x.status === 'warning');
  const unavailable = datasets.filter(x => x.available === false || x.status === 'unavailable');
  const completed = data.status === 'completed' || data.status === 'ready';
  $('output-level').textContent = completed ? (unavailable.length || limited.length ? 'Evidence assembled with limitations' : 'Evidence assembled') : pretty(data.status || 'Review');
  $('output-level').className = `badge ${completed && !unavailable.length ? 'ok' : 'warning'}`;

  const inferenceBoundary = data.results?.biological_inference || 'Dataset-level research evidence only. Biological conclusions are not inferred by the ingestion dashboard.';
  const nextAction = data.results?.next_action || 'Review modality coverage and validation warnings before enabling downstream models.';
  const observationCount = data.snapshot?.observation_count ?? data.fusion?.observation_count ?? '—';
  const readiness = data.stages?.find(s => s.name === 'pipeline_evaluation')?.summary?.readiness;

  $('output-summary').innerHTML = `<div class="output-hero"><div class="output-check">✓</div><div><strong>${esc(inferenceBoundary)}</strong><p>${observationCount !== '—' ? `${esc(observationCount)} observation/state entries were produced by the run.` : 'The run reports coverage and processing evidence rather than a clinical conclusion.'}</p></div></div><div class="output-kpis"><div><strong>${usable.length}</strong><span>usable datasets</span></div><div><strong>${limited.length}</strong><span>with warnings</span></div><div><strong>${unavailable.length}</strong><span>without usable input</span></div><div><strong>${data.summary?.linked_subjects ?? data.fusion?.linked_subjects ?? 0}</strong><span>subject links</span></div></div><div class="next-step"><span>Recommended next step</span><strong>${esc(nextAction)}</strong>${readiness !== undefined ? `<small>Data/pipeline readiness: ${Math.round(Number(readiness) * 100)}%</small>` : ''}</div>`;

  $('modality-results').innerHTML = modalityResultCards(datasets);
  $('research-findings').innerHTML = buildFindings(data).map(([label, value, note]) => `<div class="finding"><div><span>${esc(label)}</span><strong>${esc(value)}</strong></div><p>${esc(note)}</p></div>`).join('');

  const warnings = [...(data.warnings || []), ...(data.limitations || []), ...(data.fusion?.warnings || [])];
  const unique = [...new Set([...warnings, 'Biological conclusions are not inferred by the ingestion dashboard.', 'Subject-level relationships are not inferred without an explicit shared identifier.'])];
  $('limitations').innerHTML = unique.filter(Boolean).map(w => `<div class="limitation"><span>!</span><p>${esc(w)}</p></div>`).join('');
}

function renderRunStatus(data) {
  const status = data.status || 'review';
  $('run-status').textContent = status === 'ready' || status === 'completed' ? 'Run complete' : pretty(status);
  $('run-status').className = `badge ${statusClass(status)}`;
}

async function getJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function refresh() {
  try {
    const [status, datasets] = await Promise.all([getJSON('/api/status'), getJSON('/api/datasets')]);
    $('system-status').textContent = status.raw_data ? 'System ready' : 'Input directory missing';
    state.datasets = datasets.datasets || datasets.registry || [];
    renderModalities(state.datasets);
    renderFilters(state.datasets);
    renderTable(state.datasets);
  } catch (error) {
    $('system-status').textContent = 'Backend unavailable';
    $('output-level').textContent = 'Unavailable';
    $('output-level').className = 'badge warning';
    $('output-summary').innerHTML = `<div class="output-empty"><strong>Dashboard cannot reach the processing service.</strong><p>${esc(error.message)}</p></div>`;
  }
}

async function run() {
  $('run-button').disabled = true;
  $('run-button').textContent = 'Running…';
  $('run-status').textContent = 'Processing';
  $('run-status').className = 'badge neutral';
  try {
    const data = await getJSON('/api/run', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({datasets: state.datasets.map(x => x.name)})});
    state.lastRun = data;
    state.selectedStage = null;
    renderMetrics(data.summary || {});
    const steps = normalizeSteps(data);
    renderPipeline(steps);
    renderStageDetail(null);
    renderRunStatus(data);
    renderOutput(data);
    if (data.datasets?.length) {
      state.datasets = data.datasets;
      renderModalities(state.datasets);
      renderFilters(state.datasets);
      renderTable(state.datasets);
    }
    document.querySelector('.output-card').scrollIntoView({behavior: 'smooth', block: 'start'});
  } catch (error) {
    $('run-status').textContent = 'Run failed';
    $('run-status').className = 'badge warning';
    $('output-level').textContent = 'Run failed';
    $('output-level').className = 'badge warning';
    $('output-summary').innerHTML = `<div class="output-empty"><strong>The research run could not be completed.</strong><p>${esc(error.message)}</p></div>`;
  } finally {
    $('run-button').disabled = false;
    $('run-button').textContent = 'Run research pipeline';
  }
}

$('run-button').onclick = run;
refresh();
