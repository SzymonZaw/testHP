const state = { datasets: [], run: null, filter: 'all' };
const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty = v => String(v ?? '').replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
const statusClass = s => ['ok','ready','completed'].includes(s) ? 'ok' : ['warning','review','limited','insufficient_data'].includes(s) ? 'warning' : 'neutral';
const statusLabel = s => s === 'ok' ? 'Completed' : pretty(s || 'Pending');

async function getJSON(url, options){ const r=await fetch(url,options); if(!r.ok) throw new Error(`${r.status} ${r.statusText}`); return r.json(); }

function makeRunId(){
  const d=new Date();
  const stamp=d.toISOString().replace(/[-:TZ.]/g,'').slice(0,14);
  const suffix=(crypto.randomUUID ? crypto.randomUUID().slice(0,8) : Math.random().toString(16).slice(2,10));
  return `RUN-${stamp}-${suffix}`;
}
function runRecord(run){
  return {run_id:run.run_id, executed_at:run.executed_at, status:run.status, selected:run.selected||[], summary:run.summary||{}, datasets:(run.datasets||[]).map(d=>({name:d.name,modality:d.modality,task:d.task,files:d.files,supported_files:d.supported_files,available:d.available,warnings:d.warnings||[],analysis:d.analysis||{}})), findings:run.results?.findings||[], limitations:run.warnings||[], evidence_boundary:run.results?.biological_inference||'', biological_results:run.results?.biological_results||[]};
}
function saveHistory(run){
  const key='hpp.research.runs';
  const history=JSON.parse(localStorage.getItem(key)||'[]');
  history.unshift(runRecord(run));
  localStorage.setItem(key,JSON.stringify(history.slice(0,10)));
}
function csvCell(v){ const s=String(v??''); return `"${s.replaceAll('"','""')}"`; }
function download(name, content, type){ const blob=new Blob([content],{type}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000); }
function exportJSON(){ if(!state.run) return; download(`${state.run.run_id}.json`,JSON.stringify(runRecord(state.run),null,2),'application/json'); }
function exportCSV(){
  if(!state.run) return;
  const rows=[['run_id','dataset','modality','type','observation']];
  for(const f of state.run.results?.findings||[]) rows.push([state.run.run_id,f.dataset,f.modality,f.type,f.text]);
  download(`${state.run.run_id}-observations.csv`,rows.map(r=>r.map(csvCell).join(',')).join('\n'),'text/csv;charset=utf-8');
}
function renderMetrics(s={}){ $('metric-datasets').textContent=s.datasets??0; $('metric-files').textContent=s.files??0; $('metric-modalities').textContent=(s.modalities||[]).length; $('metric-links').textContent=s.linked_subjects??0; }
function renderRunStatus(run){ const s=run?.status||'warning'; $('run-status').textContent=s==='ready'||s==='completed'?'Run complete':s==='warning'?'Run complete with warnings':pretty(s); $('run-status').className=`badge ${statusClass(s)}`; }
function renderPipeline(run){
  const steps=run.steps||[];
  $('pipeline').innerHTML=steps.map((x,i)=>`<button class="stage ${statusClass(x.status)}" data-stage="${i}"><span class="num">${i+1}</span><span class="stage-copy"><strong>${esc(x.name||x.id)}</strong><span>${esc(statusLabel(x.status))}</span><p>${esc(x.purpose||'Pipeline stage.')}</p></span></button>`).join('');
  document.querySelectorAll('[data-stage]').forEach(b=>b.onclick=()=>renderStageDetail(steps[Number(b.dataset.stage)]));
}
function renderStageDetail(stage){
  const d=$('stage-detail'); if(!stage){d.className='stage-detail empty';d.textContent='Run the pipeline, then select a stage above to inspect what happened.';return;}
  const ds=state.run?.datasets||[]; const supported=ds.reduce((n,x)=>n+(x.supported_files||0),0); const warnings=ds.reduce((n,x)=>n+(x.warnings||[]).length,0); const usable=ds.filter(x=>x.available&&x.supported_files>0).length;
  const id=String(stage.id||stage.name); let stats=[],note='';
  if(id==='input') stats=[['Datasets selected',state.run.selected?.length||0],['Run ID',state.run.run_id]];
  else if(id==='ingestion') stats=[['Supported files',supported],['Usable datasets',usable]];
  else if(id==='validation') stats=[['Datasets checked',ds.length],['Validation warnings',warnings],['Without usable input',ds.filter(x=>!x.available).length]];
  else if(id==='normalization') stats=[['Supported files',supported],['Measured observations',state.run.results?.findings?.length||0]];
  else if(id==='fusion') stats=[['Modalities',state.run.summary?.modalities?.length||0],['Subject links',state.run.summary?.linked_subjects||0],['Datasets contributing',usable]];
  else if(id==='results') stats=[['Measured observations',state.run.results?.findings?.length||0],['Biological results',state.run.results?.biological_results?.length||0]];
  else stats=[['Run status',pretty(stage.status)]];
  note=id==='validation'&&warnings?'Warnings remain explicit limitations and are never converted into findings.':id==='fusion'?'No subject-level relationship is created without an explicit shared identifier.':'This panel reports processing evidence only; it does not create biological conclusions.';
  d.className='stage-detail'; d.innerHTML=`<div class="detail-heading"><div><span class="eyebrow">PIPELINE STAGE</span><h3>${esc(stage.name||stage.id)}</h3><p>${esc(stage.purpose||'Pipeline stage.')}</p></div><span class="status ${statusClass(stage.status)}">${esc(statusLabel(stage.status))}</span></div><div class="detail-stats">${stats.map(x=>`<div><span>${esc(x[0])}</span><strong>${esc(x[1])}</strong></div>`).join('')}</div><div class="detail-note"><strong>What this means</strong><p>${esc(note)}</p></div>`;
}
function measurementCards(a){
  const out=[],r=a?.raster_statistics,d=a?.image_dimensions,n=a?.numeric_summary,j=a?.annotations,w=a?.dicom_metadata;
  if(d) out.push(`<div class="measurement-metrics"><div><span>Files measured</span><strong>${esc(d.measured)}</strong></div><div><span>Width</span><strong>${esc(d.min_width)}–${esc(d.max_width)}</strong><small>px</small></div><div><span>Height</span><strong>${esc(d.min_height)}–${esc(d.max_height)}</strong><small>px</small></div></div>`);
  if(r) out.push(`<div class="measurement-metrics"><div><span>Mean brightness</span><strong>${esc(r.mean_brightness)}</strong><small>/255</small></div><div><span>Mean R</span><strong>${esc(r.mean_rgb?.[0])}</strong></div><div><span>Mean G</span><strong>${esc(r.mean_rgb?.[1])}</strong></div><div><span>Mean B</span><strong>${esc(r.mean_rgb?.[2])}</strong></div></div>`);
  if(n) out.push(`<div class="measurement-metrics"><div><span>Numeric values</span><strong>${esc(a.numeric_values)}</strong></div><div><span>Minimum</span><strong>${esc(n.observed_min)}</strong></div><div><span>Maximum</span><strong>${esc(n.observed_max)}</strong></div><div><span>Files with numeric data</span><strong>${esc(n.files_with_numeric_data)}</strong></div></div>`);
  if(j?.nodes) out.push(`<div class="measurement-metrics"><div><span>Valid JSON files</span><strong>${esc(j.valid_json)}</strong></div><div><span>Structured nodes</span><strong>${esc(j.nodes)}</strong></div></div>`);
  if(w?.length) out.push(`<div class="measurement-metrics"><div><span>DICOM files read</span><strong>${esc(w.length)}</strong></div>${w[0].rows&&w[0].columns?`<div><span>Matrix</span><strong>${esc(w[0].columns)} × ${esc(w[0].rows)}</strong></div>`:''}</div>`);
  return out.join('');
}
function groupedFindings(findings,ds){ const m=new Map(); for(const f of findings){const k=`${f.modality}::${f.dataset}`;if(!m.has(k))m.set(k,{dataset:f.dataset,modality:f.modality,texts:[],analysis:ds.find(x=>x.name===f.dataset)?.analysis||{}});const g=m.get(k);if(!g.texts.includes(f.text))g.texts.push(f.text);}return [...m.values()]; }
function renderMeasurements(findings,ds){
  const groups=groupedFindings(findings,ds),el=$('measurement-results');
  if(!findings.length){el.innerHTML='<div class="output-empty"><strong>No measured observations were produced.</strong><p>The available input is not currently covered by a descriptive measurement routine.</p></div>';return;}
  el.innerHTML=`<div class="measurement-head"><div><span class="eyebrow">MEASURED OBSERVATIONS</span><h3>What was actually measured</h3><p>Each dataset appears once. Values are grouped from the actual run response.</p></div><span class="badge ok">${findings.length} observations · ${groups.length} datasets</span></div><div class="measurement-list">${groups.map(g=>`<article class="measurement"><div class="measurement-meta"><span class="modality-icon">${esc((g.modality||'').slice(0,3).toUpperCase())}</span><div><strong>${esc(g.dataset)}</strong><span>${g.texts.length} computed observation${g.texts.length===1?'':'s'}</span></div></div>${g.texts.map(t=>`<p>${esc(t)}</p>`).join('')}${measurementCards(g.analysis)}</article>`).join('')}</div>`;
}
function renderModalityCards(ds){
  const groups={}; ds.forEach(d=>{const m=d.modality||'unknown';groups[m] ||= {datasets:0,files:0,supported:0,unavailable:0};const g=groups[m];g.datasets++;g.files+=d.files||0;g.supported+=d.supported_files||0;if(!d.available)g.unavailable++;});
  $('modality-results').innerHTML=Object.entries(groups).map(([m,g])=>{const p=g.files?Math.round(g.supported/g.files*100):0;return `<article class="result-card"><div class="result-card-head"><span class="modality-icon">${esc(m.slice(0,3).toUpperCase())}</span><div><strong>${esc(m)}</strong><span>${g.datasets} dataset${g.datasets===1?'':'s'}</span></div><span class="status ${g.supported?'ok':'unavailable'}">${g.supported?'Input available':'No usable input'}</span></div><div class="result-stat"><strong>${g.supported}</strong><span>supported files</span></div><div class="mini-progress"><i style="width:${p}%"></i></div><p>This is input coverage, not a research finding.${g.unavailable?` ${g.unavailable} dataset${g.unavailable===1?'':'s'} has no usable local input.`:''}</p></article>`}).join('');
}
function renderOutput(run){
  const findings=run.results?.findings||[],groups=groupedFindings(findings,run.datasets||[]),bio=run.results?.biological_results||[];
  $('output-level').textContent=findings.length?'Measured observations only':'No computed research result'; $('output-level').className=`badge ${findings.length?'ok':'warning'}`;
  $('output-summary').innerHTML=`<div class="output-hero"><div class="output-check">${findings.length?'✓':'!'}</div><div><strong>${findings.length?'Real measurements were computed from the files available in this run.':'No research result can currently be computed from the available files.'}</strong><p>Nothing here is generated from dataset names, placeholders, assumptions or missing data.</p></div></div><div class="output-kpis"><div><strong>${findings.length}</strong><span>real measured observations</span></div><div><strong>${groups.length}</strong><span>datasets with measurements</span></div><div><strong>${bio.length}</strong><span>biological results claimed</span></div><div><strong>${run.summary?.linked_subjects||0}</strong><span>subject links</span></div></div><div class="next-step"><span>Research result boundary</span><strong>${esc(run.results?.biological_inference||'Measured input characteristics are available; biological conclusions are not inferred.')}</strong><small>${esc(run.results?.next_action||'Add a validated modality-specific analysis before reporting a biological result.')}</small></div>`;
  renderMeasurements(findings,run.datasets||[]); $('research-findings').innerHTML=`<div class="finding"><div><span>Biological result</span><strong>Not available</strong></div><p>No biological conclusion is produced by the current routines.</p></div><div class="finding"><div><span>Subject-level result</span><strong>Not established</strong></div><p>No subject relationship is inferred without an explicit shared identifier.</p></div>`; renderModalityCards(run.datasets||[]); renderLimitations(run); renderVisuals(run); renderProvenance(run);
}
function renderLimitations(run){const w=[...(run.warnings||[]),'Biological conclusions are not inferred unless a validated analysis routine computes them.','Subject-level relationships are not inferred without an explicit shared identifier.'];$('limitations').innerHTML=[...new Set(w)].filter(Boolean).map(x=>`<div class="limitation"><span>!</span><p>${esc(x)}</p></div>`).join('');}
function renderInput(ds){const totals={};ds.filter(d=>d.available).forEach(d=>totals[d.modality]=(totals[d.modality]||0)+(d.supported_files||0));const max=Math.max(1,...Object.values(totals));$('modality-chart').innerHTML=Object.entries(totals).map(([m,v])=>`<div class="bar-row"><strong>${esc(m)}</strong><div class="bar"><i style="width:${Math.round(v/max*100)}%"></i></div><span>${v}</span></div>`).join('')||'<p class="muted">No usable inputs.</p>';$('dataset-list').innerHTML=ds.filter(d=>d.available).map(d=>`<span class="tag">${esc(d.name)}</span>`).join('')||'<span class="muted">No datasets contributed usable local input.</span>';}
function renderTable(ds){const vis=state.filter==='all'?ds:ds.filter(d=>d.modality===state.filter);$('dataset-table').innerHTML=vis.map(d=>{const t=d.files||0,s=d.supported_files||0,p=t?Math.round(s/t*100):0,st=d.available?(d.warnings?.length?'warning':'ok'):'unavailable';return `<tr><td><strong>${esc(d.name)}</strong></td><td>${esc(d.modality)}</td><td>${esc(d.task)}</td><td>${s} / ${t}</td><td class="coverage"><div class="coverage-bar"><i style="width:${p}%"></i></div></td><td><span class="status ${st}">${d.available?(d.warnings?.length?'Review':'Available'):'Unavailable'}</span></td></tr>`}).join('');}
function renderFilters(ds){const mods=['all',...new Set(ds.map(d=>d.modality))];$('filter-buttons').innerHTML=mods.map(m=>`<button class="${state.filter===m?'active':''}" data-filter="${esc(m)}">${m==='all'?'All':esc(m)}</button>`).join('');document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{state.filter=b.dataset.filter;renderFilters(ds);renderTable(ds);});}
function renderVisuals(run){
  const findings=run.results?.findings||[],groups=groupedFindings(findings,run.datasets||[]);
  const brightness=groups.map(g=>({name:g.dataset,value:g.analysis?.raster_statistics?.mean_brightness})).filter(x=>x.value!=null);
  const numeric=groups.map(g=>({name:g.dataset,value:g.analysis?.numeric_summary?.observed_max})).filter(x=>x.value!=null);
  const data=brightness.length?brightness:numeric;
  const title=brightness.length?'Mean image brightness by dataset':'Observed numeric maximum by dataset';
  if(!data.length){$('visuals').innerHTML='<div class="output-empty"><strong>No plottable measured values are available.</strong><p>The chart is intentionally empty rather than using placeholder data.</p></div>';return;}
  const rows=data.map(x=>{const max=Math.max(...data.map(y=>Number(y.value)||0),1);const pct=Math.max(2,Math.round(Number(x.value)/max*100));return '<div class="chart-row"><span title="'+esc(x.name)+'">'+esc(x.name)+'</span><div><i style="width:'+pct+'%"></i></div><strong>'+esc(x.value)+'</strong></div>';}).join('');
  $('visuals').innerHTML='<div class="visual-head"><div><span class="eyebrow">REAL-DATA VISUALIZATION</span><h3>'+esc(title)+'</h3><p>Only values returned by the current descriptive analysis are plotted.</p></div><span class="badge ok">'+data.length+' measured datasets</span></div><div class="chart">'+rows+'</div>';
}
function renderProvenance(run){
  $('provenance').innerHTML=`<div class="provenance-grid"><div><span>Run ID</span><strong>${esc(run.run_id)}</strong></div><div><span>Executed</span><strong>${esc(new Date(run.executed_at).toLocaleString())}</strong></div><div><span>Status</span><strong>${esc(pretty(run.status))}</strong></div><div><span>Datasets selected</span><strong>${esc((run.selected||[]).length)}</strong></div></div><p class="provenance-note">Every displayed measurement is traceable to a dataset and to the analysis object returned by this run. Large raw files are not copied into the repository.</p><div class="export-actions"><button id="export-json">Export run JSON</button><button id="export-csv">Export measured observations CSV</button></div>`;
  $('export-json').onclick=exportJSON;$('export-csv').onclick=exportCSV;
}
async function runPipeline(){
  $('run-button').disabled=true;$('run-button').textContent='Running…';
  try{const run=await getJSON('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets:[]})});run.run_id=makeRunId();run.executed_at=new Date().toISOString();state.run=run;saveHistory(run);state.datasets=run.datasets||[];renderMetrics(run.summary||{});renderRunStatus(run);renderPipeline(run);renderStageDetail();renderOutput(run);renderInput(state.datasets);renderFilters(state.datasets);renderTable(state.datasets);document.querySelector('.output-card').scrollIntoView({behavior:'smooth',block:'start'});}catch(e){$('run-status').textContent='Run failed';$('run-status').className='badge warning';$('stage-detail').className='stage-detail';$('stage-detail').innerHTML=`<div class="detail-note"><strong>Could not complete the run</strong><p>${esc(e.message)}</p></div>`;}finally{$('run-button').disabled=false;$('run-button').textContent='Run research pipeline';}}
async function init(){try{const[s,d]=await Promise.all([getJSON('/api/status'),getJSON('/api/datasets')]);$('system-status').textContent=s.status==='ready'?'System ready':pretty(s.status);state.datasets=d.datasets||[];renderInput(state.datasets);renderFilters(state.datasets);renderTable(state.datasets);renderMetrics({datasets:state.datasets.length,files:state.datasets.reduce((n,x)=>n+(x.supported_files||0),0),modalities:[...new Set(state.datasets.map(x=>x.modality))],linked_subjects:0});}catch(e){$('system-status').textContent='System unavailable';}$('run-button').onclick=runPipeline;}
init();