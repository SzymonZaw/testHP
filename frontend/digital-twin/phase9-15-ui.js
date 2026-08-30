import { getDigitalTwinState, subscribeDigitalTwinState, updateSelection, ingestAnalysisResult, setAnalysisError } from './canonical-ui-runtime.js';
import { SPATIAL_REGIONS, suppliedCellId, suppliedTissueId, suppliedTissues, suppliedCells, displayNotEstablished } from './digital-twin-phase1-8-governor.js';

const MODALITIES = [
  ['hand_images', 'Hand Images'], ['hand_video', 'Hand Video'], ['hand_3d', '3D Scan'], ['tissue_wsi', 'WSI'],
  ['single_cell_rna', 'RNA'], ['proteomics', 'Proteomics'], ['epigenetics', 'Epigenetics'], ['genomics', 'Genomics'],
];
const TIMEPOINTS = ['T0', 'T1', 'T2', 'T3'];
const TABS = ['age', 'trajectory', 'what-if', 'intervention', 'governance'];
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
const hasValue = v => v !== null && v !== undefined && v !== '';
const value = v => hasValue(v) ? esc(v) : '<span class="dt-ne">NOT ESTABLISHED</span>';
const number = v => Number.isFinite(Number(v)) ? Number(v) : null;
const status = v => v?.status ?? v?.state ?? null;
const confidence = v => v?.confidence ?? null;
const uncertainty = v => v?.uncertainty ?? null;
const statusLabel = v => String(status(v) || 'Not established').replaceAll('_', ' ');

function readyAsset(asset) { return ['ready','available','verified','usable'].includes(String(asset?.status ?? '').toLowerCase()); }
function backendHasModality(state, id) {
  const aliases = {
    hand_images:['hand_images','hand','image'], hand_video:['hand_video','video'], hand_3d:['hand_3d','3d','mesh'], tissue_wsi:['tissue_wsi','wsi'],
    single_cell_rna:['single_cell_rna','rna','scrna'], proteomics:['proteomics','protein'], epigenetics:['epigenetics','methylation','chromatin'], genomics:['genomics','genome','variant']
  }[id] || [id];
  return (Array.isArray(state.assets) ? state.assets : []).some(a => readyAsset(a) && aliases.includes(String(a.modality ?? '').toLowerCase()));
}
function selectedCell(state) {
  const cells = suppliedCells(state, state.selection.region, state.selection.tissue);
  return cells.find(c => suppliedCellId(c) === String(state.selection.cell)) || null;
}
function ageObject(state) { return state.biologicalAge && typeof state.biologicalAge === 'object' ? state.biologicalAge : {}; }
function ageField(obj, ...keys) { for (const key of keys) if (hasValue(obj?.[key])) return obj[key]; return null; }
function ageRows(state) {
  const a = ageObject(state);
  return [
    ['Chronological age', ageField(a,'chronological_age','chronologicalAge')],
    ['Hand biological age', ageField(a,'hand_biological_age','handBiologicalAge') ?? (state.selection.region === 'palm' && !state.selection.tissue && !state.selection.cell ? ageField(a,'biological_age','biologicalAge') : null)],
    ['Tissue biological age', ageField(a,'tissue_biological_age','tissueBiologicalAge')],
    ['Cell population age', ageField(a,'cell_population_age','cellPopulationAge','cellular_age')],
    ['Molecular age', ageField(a,'molecular_age','molecularAge')],
  ];
}
function ageMeta(state) {
  const a = ageObject(state), p = state.provenance || {};
  return {
    model: a.model ?? a.model_id ?? p.model_id ?? null,
    version: a.version ?? a.model_version ?? p.model_version ?? null,
    source: a.source ?? p.source ?? null,
    validation: a.validation_status ?? state.validation?.validation_status ?? 'not_validated'
  };
}
function trajectoryPoints(data) {
  if (!data) return [];
  const raw = Array.isArray(data) ? data : (Array.isArray(data.points) ? data.points : Array.isArray(data.series) ? data.series : []);
  return raw.map((p,i) => ({
    x: p?.timepoint ?? p?.time ?? p?.label ?? `T${i}`,
    y: number(p?.value ?? p?.biological_age ?? p?.age ?? p?.score),
    status: String(p?.status ?? p?.kind ?? '').toLowerCase(),
    uncertainty: number(p?.uncertainty ?? p?.std ?? p?.error),
    lower: number(p?.lower ?? p?.min), upper: number(p?.upper ?? p?.max)
  })).filter(p => p.y !== null);
}
function drawChart(data) {
  const pts = trajectoryPoints(data);
  if (pts.length < 2) return '<div class="dt-empty-block"><b>NOT ESTABLISHED</b><span>No validated longitudinal trajectory is supplied by the backend for this state.</span></div>';
  const W=720,H=220,P=38, ys=pts.map(p=>p.y), min=Math.min(...ys), max=Math.max(...ys), span=(max-min)||1;
  const px=i=>P+i*(W-2*P)/Math.max(1,pts.length-1), py=y=>H-P-(y-min)/span*(H-2*P);
  const line=pts.map((p,i)=>`${px(i)},${py(p.y)}`).join(' ');
  const bands=pts.every(p=>p.lower!==null&&p.upper!==null) ? `<polygon class="dt-band" points="${pts.map((p,i)=>`${px(i)},${py(p.upper)}`).join(' ')} ${pts.slice().reverse().map((p,i)=>`${px(pts.length-1-i)},${py(p.lower)}`).join(' ')}"/>` : '';
  const dots=pts.map((p,i)=>`<circle cx="${px(i)}" cy="${py(p.y)}" r="4"><title>${esc(p.x)}: ${p.y}</title></circle>`).join('');
  const labels=pts.map((p,i)=>`<text x="${px(i)}" y="${H-10}" text-anchor="middle">${esc(p.x)}</text>`).join('');
  return `<svg class="dt-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Longitudinal trajectory">${bands}<polyline points="${line}" fill="none" stroke="currentColor" stroke-width="2"/>${dots}${labels}</svg>`;
}
function trajectoryPanel(state) {
  const data = state.trajectory;
  const disease = state.diseaseTrajectory;
  return `<section class="dt-card dt-wide-card"><div class="dt-card-title">TRAJECTORY</div>
    <div class="dt-traj-tabs"><span class="active">overview</span><span>aging</span><span>disease</span></div>
    <div class="dt-traj-grid"><div><h3>Aging trajectory</h3>${drawChart(data)}<small>Observed = source/model says observed · Predicted = source/model says predicted · uncertainty only when supplied.</small></div><div><h3>Disease trajectory</h3>${drawChart(disease)}</div></div>
    <div class="dt-trajectory-scope"><button data-scope="hand">Hand</button><span>→</span><button data-scope="palm">Palm</button><span>→</span><button data-scope="tissue">Tissue</button><span>→</span><button data-scope="cell">Cell population</button></div>
  </section>`;
}
function evidencePanel(state) {
  const cov=number(state.evidence?.coverage); const pct=cov===null?'—':`${Math.round(cov<=1?cov*100:cov)}%`;
  const qc=Array.isArray(state.qc)?state.qc:[];
  return `<section class="dt-card"><div class="dt-card-title">EVIDENCE</div><div class="dt-coverage"><span>Evidence coverage</span><b>${pct}</b></div>${MODALITIES.map(([id,label])=>`<div class="dt-evidence-row"><span>${label}</span><b class="${backendHasModality(state,id)?'yes':'no'}">${backendHasModality(state,id)?'Available':'Missing'}</b></div>`).join('')}<div class="dt-qc"><b>Quality</b>${qc.length?qc.map(q=>`<span>${esc(q.modality)} · ${esc(q.status)}</span>`).join(''):'No QC result supplied'}</div><p class="dt-note">Evidence ≠ Health · Coverage ≠ Clinical confidence · Missing ≠ Disease.</p></section>`;
}
function governancePanel(state) {
  const p=state.provenance||{}, v=state.validation||{};
  const evidenceUsed=Array.isArray(state.evidence?.items)?state.evidence.items:[];
  return `<section class="dt-card"><div class="dt-card-title">GOVERNANCE</div><div class="dt-governance-status">RESEARCH ONLY</div><div class="dt-governance-grid">
    <span>Result status</span><b>${esc(state.biologicalState?.status || 'Not established')}</b>
    <span>Model</span><b>${value(p.model_id)}</b><span>Model version</span><b>${value(p.model_version)}</b>
    <span>Dataset version</span><b>${value(p.dataset_version)}</b><span>Pipeline version</span><b>${value(p.pipeline_version)}</b>
    <span>Source</span><b>${value(p.source)}</b><span>Analysis ID</span><b>${value(p.analysis_id)}</b>
    <span>Validation</span><b>${value(v.validation_status)}</b><span>Evidence used</span><b>${evidenceUsed.length || 'NOT ESTABLISHED'}</b>
    <span>Confidence</span><b>${value(state.biologicalState?.confidence)}</b><span>Uncertainty</span><b>${value(state.biologicalState?.uncertainty)}</b>
  </div><small>Observed · Computed · Estimated · Predicted · Hypothetical · Not established</small></section>`;
}
function renderAge(state) {
  const meta=ageMeta(state), rows=ageRows(state), a=ageObject(state);
  return `<section class="dt-card dt-wide-card"><div class="dt-card-title">BIOLOGICAL AGE</div><div class="dt-age-grid">${rows.map(([label,val])=>`<div class="dt-age-card"><span>${label}</span><strong>${value(val)}</strong>${hasValue(val)?'<small>Backend/model supplied</small>':'<small>No validated/model-supplied estimate</small>'}</div>`).join('')}</div><div class="dt-governance-grid dt-age-meta"><span>Confidence</span><b>${value(a.confidence)}</b><span>Uncertainty</span><b>${value(a.uncertainty)}</b><span>Model</span><b>${value(meta.model)}</b><span>Version</span><b>${value(meta.version)}</b><span>Source</span><b>${value(meta.source)}</b><span>Validation status</span><b>${value(meta.validation)}</b></div><p class="dt-note">Brak modelu lub danych oznacza <b>Not established</b>; nie jest to zero ani brak starzenia.</p></section>`;
}
function renderWhatIf(state) {
  const wf=state.whatIf;
  const has=wf && typeof wf==='object' && (Array.isArray(wf.scenarios)||wf.current_state||wf.no_intervention);
  return `<section class="dt-card dt-wide-card"><div class="dt-card-title">WHAT-IF SIMULATION <span class="dt-pill">HYPOTHETICAL</span></div>${has?`<div class="dt-scenario-grid">${[['Current state',wf.current_state],['No intervention',wf.no_intervention],['Scenario A',wf.scenario_a],['Scenario B',wf.scenario_b]].map(([l,x])=>`<div class="dt-scenario"><b>${l}</b><span>${value(x?.status ?? x?.value ?? x)}</span></div>`).join('')}</div>`:'<div class="dt-empty-block"><b>NOT ESTABLISHED</b><span>No validated what-if model/result is supplied by the backend.</span></div>'}<p class="dt-note">Simulation only. Hypothetical outputs are never presented as observed clinical facts.</p></section>`;
}
function renderIntervention(state) {
  const i=state.interventions;
  const established=i && typeof i==='object' && i.status && String(i.status).toLowerCase()!=='not_established';
  return `<section class="dt-card dt-wide-card"><div class="dt-card-title">INTERVENTION SUPPORT</div>${established?`<div class="dt-intervention-grid"><span>Area requiring attention</span><b>${value(i.area ?? i.priority ?? i.finding)}</b><span>Evidence supporting finding</span><b>${value(i.evidence)}</b><span>Confidence</span><b>${value(i.confidence)}</b><span>Uncertainty</span><b>${value(i.uncertainty)}</b><span>Validation</span><b>${value(i.validation_status ?? i.clinical_validation)}</b></div>`:'<div class="dt-empty-block"><b>NOT ESTABLISHED</b><span>Insufficient validated evidence for intervention recommendation.</span></div>'}<p class="dt-note"><b>No automatic treatment recommendations.</b> Decision support remains research-only.</p></section>`;
}
function cellInspector(state) {
  const cell=selectedCell(state); if(!cell) return `<section class="dt-card"><div class="dt-card-title">CELL INSPECTOR</div><div class="dt-empty-inspector"><b>Select a supplied cell</b><span>No cell is created by the frontend.</span></div></section>`;
  return `<section class="dt-card"><div class="dt-card-title">CELL INSPECTOR</div><div class="dt-cell-title">CELL ${esc(suppliedCellId(cell))}</div>${[['Type',cell.type??cell.cell_type],['Location',`${state.selection.region}${state.selection.tissue?` / ${state.selection.tissue}`:''}`],['Morphology',cell.morphology??cell.morphology_status],['Cell State',cell.state??cell.cell_state],['Health',cell.health],['Biological Age',cell.biological_age??cell.age],['Confidence',confidence(cell)],['Uncertainty',uncertainty(cell)]].map(([l,v])=>`<div class="dt-detail"><span>${l}</span><b>${l==='Location'?esc(v):value(v)}</b></div>`).join('')}</section>`;
}
function tree(state) {
  const sel=state.selection, tissues=suppliedTissues(state,sel.region), cells=suppliedCells(state,sel.region,sel.tissue);
  return `<aside class="dt-left"><div class="dt-section-label">WHERE AM I?</div><div class="dt-breadcrumb">Hand / ${esc(sel.region)}${sel.tissue?` / ${esc(sel.tissue)}`:''}${sel.cell?` / Cell ${esc(sel.cell)}`:''}</div><div class="dt-tree"><button class="dt-tree-root" data-region="palm">HAND</button>${SPATIAL_REGIONS.map(([id,label])=>`<div class="dt-tree-group"><button class="dt-region ${id===sel.region?'active':''}" data-region="${id}">${id===sel.region?'▾':'▸'} ${label}</button>${id===sel.region?`<div class="dt-tree-children">${tissues.length?tissues.map(t=>{const tid=suppliedTissueId(t);return `<button class="dt-tissue ${tid===sel.tissue?'active':''}" data-tissue="${esc(tid)}">${esc(t.name??t.label??tid)}</button>`}).join(''):'<span class="dt-empty">No tissue data supplied</span>'}${sel.tissue?`<div class="dt-cell-heading">CELLS</div>${cells.length?cells.map(c=>{const cid=suppliedCellId(c);return `<button class="dt-cell ${cid===sel.cell?'active':''}" data-cell="${esc(cid)}">● ${esc(cid)}</button>`}).join(''):'<span class="dt-empty">No cell data supplied</span>'}`:''}</div>`:''}</div>`).join('')}</div><div class="dt-scale"><div class="dt-section-label">SCALE</div><div>Hand → Region → Tissue → Cell → Molecular</div></div></aside>`;
}
function bind(host) {
  host.querySelectorAll('[data-region]').forEach(b=>b.onclick=()=>updateSelection({region:b.dataset.region,tissue:null,cell:null,molecularLayer:null}));
  host.querySelectorAll('[data-tissue]').forEach(b=>b.onclick=()=>updateSelection({tissue:b.dataset.tissue,cell:null,molecularLayer:null}));
  host.querySelectorAll('[data-cell]').forEach(b=>b.onclick=()=>updateSelection({cell:b.dataset.cell,molecularLayer:null}));
  host.querySelectorAll('[data-timepoint]').forEach(b=>b.onclick=()=>loadTimepoint(b.dataset.timepoint));
  host.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{const u=new URL(location.href);u.searchParams.set('view',b.dataset.tab);history.replaceState(null,'',u);render(getDigitalTwinState());});
  host.querySelectorAll('[data-scope]').forEach(b=>b.onclick=()=>{const scope=b.dataset.scope; if(scope==='cell') return; if(scope==='hand'||scope==='palm') updateSelection({region:'palm',tissue:null,cell:null});});
}
async function loadTimepoint(timepoint) {
  const s=getDigitalTwinState(); updateSelection({timepoint,tissue:null,cell:null,molecularLayer:null});
  try { const r=await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(s.selection.subject)}&timepoint=${encodeURIComponent(timepoint)}`,{cache:'no-store',headers:{Accept:'application/json'}}); if(!r.ok) throw new Error(`Analysis HTTP ${r.status}`); ingestAnalysisResult(await r.json()); }
  catch(e){ setAnalysisError(e); }
}
function render(state) {
  const host=document.getElementById('testhp-end-user-layer') || document.body.appendChild(Object.assign(document.createElement('main'),{id:'testhp-end-user-layer'}));
  const view=new URL(location.href).searchParams.get('view')||'age', sel=state.selection;
  const main=view==='age'?renderAge(state):view==='trajectory'?trajectoryPanel(state):view==='what-if'?renderWhatIf(state):view==='intervention'?renderIntervention(state):governancePanel(state);
  host.innerHTML=`<div class="dt-canonical dt-phase9"><header class="dt-topbar"><div><div class="dt-kicker">HUMAN DIGITAL TWIN</div><div class="dt-subtitle">Spatial · cellular · molecular · longitudinal</div></div><div class="dt-context"><span>Subject <b>${esc(sel.subject)}</b></span><span>Timepoint ${TIMEPOINTS.map(t=>`<button class="dt-time-btn ${t===sel.timepoint?'active':''}" data-timepoint="${t}">${t}</button>`).join('')}</span><span>Region <b>${esc(sel.region)}</b></span></div></header><div class="dt-breadcrumb-top">Hand / ${esc(sel.region)}${sel.tissue?` / ${esc(sel.tissue)}`:''}${sel.cell?` / Cell ${esc(sel.cell)}`:''}</div><div class="dt-grid">${tree(state)}<section class="dt-center"><div class="dt-viewport-head"><span><span class="dt-kicker">DIGITAL TWIN</span> · ${esc(sel.region)}</span><span>${sel.cell?'CELL '+esc(sel.cell):sel.tissue?'TISSUE':'REGION'}</span></div><div id="twin-viewport" class="dt-viewport"></div><div class="dt-viewport-note">Drag to rotate · wheel to zoom · click a supplied spatial target</div>${main}</section><aside class="dt-right">${cellInspector(state)}${evidencePanel(state)}<section class="dt-card"><div class="dt-card-title">NAVIGATION</div>${TABS.map(t=>`<button class="dt-tab ${view===t?'active':''}" data-tab="${t}">${t==='what-if'?'What-if':t[0].toUpperCase()+t.slice(1)}</button>`).join('')}</section><section class="dt-card dt-governance"><div class="dt-card-title">GOVERNANCE</div><b>RESEARCH ONLY</b><span>Clinical readiness is not established.</span></section></aside></div><footer class="dt-footer"><span>Backend result is authoritative.</span><span>State v${esc(state.stateVersion)}</span><span>Data status: ${esc(state.status)}</span></footer></div>`;
  bind(host);
}

const style=document.createElement('style'); style.textContent=`
.dt-phase9{min-height:100vh;background:#0b0f14;color:#e7edf4;font:14px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.dt-phase9 *{box-sizing:border-box}.dt-topbar{display:flex;justify-content:space-between;gap:24px;padding:20px 28px;border-bottom:1px solid #202833}.dt-kicker,.dt-section-label,.dt-card-title{font-size:11px;font-weight:800;letter-spacing:.12em;color:#91a0b2}.dt-subtitle{color:#6f7d8e;font-size:12px}.dt-context{display:flex;align-items:center;gap:14px;color:#758395;font-size:12px}.dt-context b{color:#dbe4ee}.dt-time-btn,.dt-region,.dt-tree-root,.dt-tissue,.dt-cell,.dt-tab{border:0;background:transparent;color:#9eacbc;cursor:pointer}.dt-time-btn{padding:4px 7px}.dt-time-btn.active,.dt-region.active,.dt-tissue.active,.dt-cell.active,.dt-tab.active{color:#69b8ff}.dt-breadcrumb-top{padding:10px 28px;color:#718093;font-size:12px;border-bottom:1px solid #171f28}.dt-grid{display:grid;grid-template-columns:245px minmax(500px,1fr) 345px;min-height:calc(100vh - 126px)}.dt-left,.dt-right{padding:18px;border-right:1px solid #202833}.dt-right{border-right:0;border-left:1px solid #202833}.dt-section-label{margin-bottom:9px}.dt-breadcrumb{color:#758395;font-size:11px;margin-bottom:13px}.dt-tree-group{margin:2px 0}.dt-region{width:100%;padding:8px;border-radius:7px;text-align:left}.dt-region.active{background:#111b26}.dt-tree-children{padding:5px 0 8px 14px;border-left:1px solid #283444}.dt-tissue,.dt-cell{display:block;width:100%;padding:6px 8px;text-align:left;font-size:12px}.dt-cell-heading{margin:11px 8px 4px;font-size:10px;color:#647487;letter-spacing:.1em}.dt-empty,.dt-empty-inspector,.dt-empty-block{display:block;color:#687789;padding:8px;font-size:12px}.dt-empty-block{border:1px dashed #293544;border-radius:10px;margin-top:8px}.dt-empty-block b{display:block;color:#b3bfcb;font-size:11px;letter-spacing:.08em}.dt-empty-block span{display:block;margin-top:5px}.dt-scale{margin-top:25px;padding-top:16px;border-top:1px solid #202833;color:#788799;font-size:11px}.dt-center{padding:12px;min-width:0}.dt-viewport-head{display:flex;justify-content:space-between;padding:5px 4px 9px;color:#8290a1}.dt-viewport{height:520px;min-height:420px;border:1px solid #202833;border-radius:14px;overflow:hidden;background:#0d1219}.dt-viewport-note{color:#667587;font-size:10px;padding:7px}.dt-right .dt-card{border-bottom:1px solid #202833;padding-bottom:15px;margin-bottom:16px}.dt-card-title{margin-bottom:11px}.dt-metric,.dt-detail,.dt-evidence-row,.dt-coverage,.dt-governance-grid{display:grid;grid-template-columns:1fr auto;gap:9px;padding:6px 0}.dt-detail span,.dt-evidence-row span,.dt-coverage span,.dt-governance-grid span{color:#738296}.dt-detail b,.dt-governance-grid b{text-align:right;max-width:180px}.dt-ne{color:#a5afba;font-weight:700;letter-spacing:.03em}.dt-evidence-row b{font-size:11px}.dt-evidence-row .yes{color:#79caa1}.dt-evidence-row .no{color:#667487}.dt-note{color:#687789;font-size:10px}.dt-qc{display:flex;flex-direction:column;gap:3px;margin-top:8px;color:#738296;font-size:10px}.dt-cell-title{font-weight:800;font-size:15px;margin-bottom:8px}.dt-tab{display:inline-block;padding:6px 8px;margin:0 4px 4px 0;border:1px solid #222d39;border-radius:7px;font-size:11px}.dt-governance b,.dt-governance-status{display:block;color:#d6a64f;font-size:10px;letter-spacing:.08em}.dt-governance span{display:block;color:#6c7a8b;margin-top:4px;font-size:10px}.dt-wide-card{margin-top:15px;padding-top:15px;border-top:1px solid #202833}.dt-age-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.dt-age-card{padding:12px;border:1px solid #222d39;border-radius:10px;background:#0e141b}.dt-age-card span{display:block;color:#77879a;font-size:10px}.dt-age-card strong{display:block;margin-top:9px;font-size:13px}.dt-age-card small{display:block;margin-top:5px;color:#5f6e7f;font-size:9px}.dt-age-meta{margin-top:10px;border-top:1px solid #1c2630;padding-top:9px}.dt-chart{display:block;width:100%;height:220px;color:#70b6e8}.dt-chart text{fill:#718093;font-size:11px}.dt-chart .dt-band{fill:currentColor;opacity:.12;stroke:none}.dt-traj-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.dt-traj-grid h3{font-size:13px;margin:3px 0;color:#cfd8e2}.dt-traj-grid small{color:#687789;font-size:10px}.dt-traj-tabs{display:flex;gap:15px;margin-bottom:8px;color:#667487;font-size:10px;text-transform:uppercase;letter-spacing:.08em}.dt-traj-tabs .active{color:#69b8ff}.dt-trajectory-scope{display:flex;gap:7px;align-items:center;margin-top:10px;color:#617083;font-size:10px}.dt-trajectory-scope button{border:0;background:transparent;color:#87a5bf;cursor:pointer}.dt-pill{display:inline-block;margin-left:7px;border:1px solid #5d5137;border-radius:999px;padding:2px 6px;color:#d6a64f;font-size:9px}.dt-scenario-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.dt-scenario{border:1px solid #222d39;border-radius:10px;padding:12px}.dt-scenario b,.dt-scenario span{display:block}.dt-scenario span{margin-top:7px}.dt-intervention-grid{display:grid;grid-template-columns:1fr 1.4fr;gap:0 14px}.dt-footer{display:flex;justify-content:space-between;padding:9px 18px;color:#5f6d7e;border-top:1px solid #202833;font-size:9px}@media(max-width:1050px){.dt-grid{grid-template-columns:210px minmax(380px,1fr)}.dt-right{grid-column:1/-1;border-left:0;border-top:1px solid #202833}.dt-age-grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:700px){.dt-grid{display:block}.dt-topbar{display:block}.dt-context{margin-top:12px;flex-wrap:wrap}.dt-left,.dt-right{border:0;border-bottom:1px solid #202833}.dt-viewport{height:420px}.dt-age-grid,.dt-traj-grid,.dt-scenario-grid{grid-template-columns:1fr}.dt-footer{display:block}.dt-footer span{display:block;margin:2px 0}}
`; document.head.appendChild(style);

subscribeDigitalTwinState(render);
if (!window.__testhpPhase9Loaded) {
  window.__testhpPhase9Loaded = true;
  const s=getDigitalTwinState();
  if (s.status==='idle' && !s.error) loadTimepoint(s.selection.timepoint);
}
