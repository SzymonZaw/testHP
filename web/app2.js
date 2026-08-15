const state = { datasets: [], filter: 'all', run: null, stages: [] };
const $ = (id) => document.getElementById(id);

const stageInfo = {
  input: ['Input', 'Identify the research datasets selected for this run.'],
  ingestion: ['Ingestion', 'Read the files that are actually present under data/raw.'],
  validation: ['Validation', 'Check formats, empty files and whether each dataset has usable local input.'],
  normalization: ['Normalization', 'Represent supported sources in a common observation-oriented form.'],
  fusion: ['Multimodal fusion', 'Combine dataset-level evidence while keeping subject-level links explicit.'],
  results: ['Research view', 'Present coverage, evidence boundaries and limitations for this run.']
};

function esc(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function pretty(value) { return String(value ?? '').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase()); }
function statusClass(status) { return ['ok','ready','completed'].includes(status) ? 'ok' : ['warning','review','limited'].includes(status) ? 'warning' : 'neutral'; }
function statusLabel(status) { return status === 'ok' ? 'Completed' : pretty(status || 'Pending'); }

function renderRunStatus(run) {
  const status = run?.status || 'warning';
  const label = status === 'ready' || status === 'completed' ? 'Run complete' : status === 'warning' ? 'Run complete with warnings' : pretty(status);
  const badge = $('run-status');
  badge.textContent = label;
  badge.className = `badge ${statusClass(status)}`;
}

async function getJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function normalizeStages(run) {
  return (run.steps || []).map((step, index) => ({ ...step, stage: index + 1, name: String(step.id || step.name || '').toLowerCase() }));
}

function stageResult(stage) {
  const datasets = state.run?.datasets || [];
  const supported = datasets.reduce((n, d) => n + Number(d.supported_files || 0), 0);
  const total = datasets.reduce((n, d) => n + Number(d.files || 0), 0);
  const warnings = datasets.reduce((n, d) => n + (d.warnings || []).length, 0);
  const usable = datasets.filter(d => d.available && d.supported_files > 0).length;
  const unavailable = datasets.filter(d => !d.available).length;
  const modalityCount = new Set(datasets.filter(d => d.available).map(d => d.modality)).size;
  switch (stage.name) {
    case 'input': return { title: 'What entered the run', stats: [['Datasets selected', state.run?.selected?.length || 0], ['Modalities represented', modalityCount], ['Missing selections', state.run?.missing?.length || 0]], note: state.run?.missing?.length ? 'Some requested datasets were not found in the registry.' : 'The selected dataset registry was accepted for processing.' };
    case 'ingestion': return { title: 'What was read', stats: [['Files discovered', total], ['Supported files', supported], ['Datasets with usable input', usable]], note: supported ? 'Only files recognized by the configured modality formats are counted as usable input.' : 'No supported local input was available.' };
    case 'validation': return { title: 'What was checked', stats: [['Datasets checked', datasets.length], ['Validation warnings', warnings], ['Datasets without usable input', unavailable]], note: warnings ? 'Warnings are retained as limitations; they are not converted into positive findings.' : 'No validation warnings were produced for the selected datasets.' };
    case 'normalization': return { title: 'What was normalized', stats: [['Supported files entering normalization', supported], ['Datasets represented', usable]], note: supported ? 'Supported inputs are represented as common observations for downstream research processing.' : 'Normalization has no usable local input to process.' };
    case 'fusion': return { title: 'What was combined', stats: [['Modalities available', modalityCount], ['Subject links', 0], ['Datasets contributing usable input', usable]], note: 'Evidence is aggregated at dataset level. Subject relationships are not invented when a shared identifier is unavailable.' };
    case 'results': return { title: 'What can be reported', stats: [['Usable datasets', usable], ['Datasets with warnings', datasets.filter(d => (d.warnings || []).length).length], ['Datasets without usable input', unavailable]], note: 'This run reports data coverage and processing evidence. It does not claim a biological or clinical conclusion.' };
    default: return { title: 'Stage result', stats: [], note: 'No additional user-facing summary is available for this stage.' };
  }
}

function renderMetrics(summary = {}) {
  $('metric-datasets').textContent = summary.datasets ?? 0;
  $('metric-files').textContent = summary.files ?? 0;
  $('metric-modalities').textContent = (summary.modalities || []).length;
  $('metric-links').textContent = summary.linked_subjects ?? 0;
}

function renderPipeline(stages) {
  state.stages = stages;
  $('pipeline').innerHTML = stages.map(stage => {
    const info = stageInfo[stage.name] || [pretty(stage.name), stage.purpose || 'Research pipeline stage.'];
    return `<button class="stage ${statusClass(stage.status)}" data-stage="${stage.stage}"><span class="num">${stage.stage}</span><span class="stage-copy"><strong>${esc(info[0])}</strong><span>${esc(statusLabel(stage.status))}</span><p>${esc(info[1])}</p></span></button>`;
  }).join('');
  document.querySelectorAll('[data-stage]').forEach(button => button.onclick = () => renderStageDetail(stages.find(s => s.stage === Number(button.dataset.stage))));
}

function renderStageDetail(stage) {
  const detail = $('stage-detail');
  if (!stage) { detail.className = 'stage-detail empty'; detail.textContent = 'Run the pipeline, then select a stage above to inspect its result.'; return; }
  const info = stageInfo[stage.name] || [pretty(stage.name), stage.purpose || 'Research pipeline stage.'];
  const result = stageResult(stage);
  detail.className = 'stage-detail';
  detail.innerHTML = `<div class="detail-heading"><div><span class="eyebrow">STAGE ${stage.stage}</span><h3>${esc(result.title)}</h3><p>${esc(info[1])}</p></div><span class="status ${statusClass(stage.status)}">${esc(statusLabel(stage.status))}</span></div><div class="detail-stats">${result.stats.map(([label,value]) => `<div><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join('')}</div><div class="detail-note"><strong>What this means</strong><p>${esc(result.note)}</p></div>`;
}

function renderOutput(run) {
  const datasets = run.datasets || [];
  const usable = datasets.filter(d => d.available && d.supported_files > 0);
  const warningDatasets = datasets.filter(d => (d.warnings || []).length > 0);
  const unavailable = datasets.filter(d => !d.available);
  const completed = run.status === 'ready' || run.status === 'completed';
  $('output-level').textContent = completed ? (warningDatasets.length || unavailable.length ? 'Evidence assembled with limitations' : 'Evidence assembled') : pretty(run.status || 'Review');
  $('output-level').className = `badge ${completed && !unavailable.length ? 'ok' : 'warning'}`;
  const result = run.results || {};
  $('output-summary').innerHTML = `<div class="output-hero"><div class="output-check">✓</div><div><strong>${esc(result.biological_inference || 'Dataset-level research evidence only.')}</strong><p>The platform reports what was observed and processed in this run rather than silently converting missing data into a conclusion.</p></div></div><div class="output-kpis"><div><strong>${usable.length}</strong><span>usable datasets</span></div><div><strong>${warningDatasets.length}</strong><span>with warnings</span></div><div><strong>${unavailable.length}</strong><span>without usable input</span></div><div><strong>${run.summary?.linked_subjects ?? 0}</strong><span>subject links</span></div></div><div class="next-step"><span>Recommended next step</span><strong>${esc(result.next_action || 'Review modality coverage and validation warnings before enabling downstream models.')}</strong></div>`;
  $('research-findings').innerHTML = `<div class="finding"><div><span>Evidence boundary</span><strong>${esc(pretty(result.evidence_level || 'Dataset-level evidence'))}</strong></div><p>Biological conclusions are not inferred by the ingestion dashboard.</p></div><div class="finding"><div><span>Subject-level inference</span><strong>Not established</strong></div><p>No subject relationships are inferred without an explicit shared identifier.</p></div>`;
  renderModalityCards(datasets);
  renderLimitations(run);
}

function renderModalityCards(datasets) {
  const groups = {};
  datasets.forEach(d => { const m = d.modality || 'unknown'; groups[m] ||= {datasets:0,files:0,supported:0,warnings:0,unavailable:0}; const g=groups[m]; g.datasets++; g.files += d.files || 0; g.supported += d.supported_files || 0; g.warnings += (d.warnings||[]).length; if(!d.available) g.unavailable++; });
  $('modality-results').innerHTML = Object.entries(groups).map(([m,g]) => { const pct=g.files?Math.round(g.supported/g.files*100):0; const label=g.supported?(g.warnings||g.unavailable?'Usable with limitations':'Usable input'):'No usable input'; return `<article class="result-card"><div class="result-card-head"><span class="modality-icon">${esc(m.slice(0,3).toUpperCase())}</span><div><strong>${esc(m)}</strong><span>${g.datasets} dataset${g.datasets===1?'':'s'}</span></div><span class="status ${g.supported?(g.warnings||g.unavailable?'warning':'ok'):'unavailable'}">${label}</span></div><div class="result-stat"><strong>${g.supported}</strong><span>supported files</span></div><div class="mini-progress"><i style="width:${pct}%"></i></div><p>${pct}% of discovered files are supported.${g.unavailable?` ${g.unavailable} dataset${g.unavailable===1?'':'s'} has no usable local input.`:''}</p></article>`; }).join('');
}

function renderInput(datasets) {
  const totals = {}; datasets.filter(d => d.available).forEach(d => totals[d.modality]=(totals[d.modality]||0)+(d.supported_files||0));
  const max=Math.max(1,...Object.values(totals));
  $('modality-chart').innerHTML=Object.entries(totals).map(([m,v])=>`<div class="bar-row"><strong>${esc(m)}</strong><div class="bar"><i style="width:${Math.round(v/max*100)}%"></i></div><span>${v}</span></div>`).join('')||'<p class="muted">No usable inputs.</p>';
  $('dataset-list').innerHTML=datasets.filter(d=>d.available).map(d=>`<span class="tag">${esc(d.name)}</span>`).join('')||'<span class="muted">No datasets contributed usable local input.</span>';
}

function renderLimitations(run) {
  const warnings=[...(run.warnings||[])];
  if (!warnings.includes('Biological conclusions are not inferred by the ingestion dashboard.')) warnings.push('Biological conclusions are not inferred by the ingestion dashboard.');
  if (!warnings.includes('Subject-level relationships are not inferred without an explicit shared identifier.')) warnings.push('Subject-level relationships are not inferred without an explicit shared identifier.');
  $('limitations').innerHTML=[...new Set(warnings)].filter(Boolean).map(w=>`<div class="limitation"><span>!</span><p>${esc(w)}</p></div>`).join('');
}

function renderTable(datasets) {
  const visible=state.filter==='all'?datasets:datasets.filter(d=>d.modality===state.filter);
  $('dataset-table').innerHTML=visible.map(d=>{const total=d.files||0,s=d.supported_files||0,p=total?Math.round(s/total*100):0;const status=d.available?(d.warnings?.length?'warning':'ok'):'unavailable';const label=d.available?(d.warnings?.length?'Review':'Available'):'Unavailable';return `<tr><td><strong>${esc(d.name)}</strong></td><td>${esc(d.modality)}</td><td>${esc(d.task)}</td><td>${s} / ${total}</td><td class="coverage"><div class="coverage-bar"><i style="width:${p}%"></i></div></td><td><span class="status ${status}">${label}</span></td></tr>`}).join('');
}
function renderFilters(datasets) { const mods=['all',...new Set(datasets.map(d=>d.modality))]; $('filter-buttons').innerHTML=mods.map(m=>`<button class="${state.filter===m?'active':''}" data-filter="${esc(m)}">${m==='all'?'All':esc(m)}</button>`).join(''); document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{state.filter=b.dataset.filter;renderFilters(datasets);renderTable(datasets);}); }

async function runPipeline() {
  $('run-button').disabled=true; $('run-button').textContent='Running…';
  try {
    const run=await getJSON('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets:[]})});
    state.run=run; state.datasets=run.datasets||[]; renderMetrics(run.summary||{}); renderRunStatus(run); renderPipeline(normalizeStages(run)); renderStageDetail(); renderOutput(run); renderInput(state.datasets); renderFilters(state.datasets); renderTable(state.datasets);
  } catch(error) { $('run-status').textContent='Run failed'; $('run-status').className='badge warning'; $('stage-detail').className='stage-detail'; $('stage-detail').innerHTML=`<div class="detail-note"><strong>Could not complete the run</strong><p>${esc(error.message)}</p></div>`; }
  finally { $('run-button').disabled=false; $('run-button').textContent='Run research pipeline'; }
}

async function init() {
  try {
    const [status, datasets] = await Promise.all([getJSON('/api/status'), getJSON('/api/datasets')]);
    $('system-status').textContent = status.status === 'ready' ? 'System ready' : pretty(status.status);
    state.datasets = datasets.datasets || [];
    renderInput(state.datasets); renderFilters(state.datasets); renderTable(state.datasets);
    renderMetrics({datasets: state.datasets.length, files: state.datasets.reduce((n,d)=>n+(d.supported_files||0),0), modalities:[...new Set(state.datasets.map(d=>d.modality))], linked_subjects:0});
  } catch(error) { $('system-status').textContent='System unavailable'; }
  $('run-button').onclick=runPipeline;
}
init();