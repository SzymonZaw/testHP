(() => {
  const state = { evidence: [], archived: new Set(), timepoint: 'all', modal: null };
  const $ = (id) => document.getElementById(id);
  const target = () => window.spatialEvidenceTarget || window.selectedSpatialNode || document.body.dataset.spatialTarget || 'hand';

  function ensurePanel() {
    if ($('evidence-workspace')) return;
    const host = document.querySelector('.right-column, .inspector, aside, main') || document.body;
    const panel = document.createElement('section');
    panel.id = 'evidence-workspace'; panel.className = 'panel evidence-workspace';
    panel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">EVIDENCE MANAGEMENT</span><strong>Evidence</strong></div><button id="evidence-add" class="primary" type="button">＋ Add Evidence</button></div><div class="evidence-toolbar"><button data-time="all" class="evidence-filter active">All</button><button data-time="T0" class="evidence-filter">T0</button><button data-time="T1" class="evidence-filter">T1</button><button data-time="T2" class="evidence-filter">T2</button><button data-time="archived" class="evidence-filter">Archived</button></div><div id="evidence-cards" class="evidence-cards"></div>`;
    host.appendChild(panel);
    $('evidence-add').onclick = openWizard;
    panel.querySelectorAll('.evidence-filter').forEach(b => b.onclick = () => { state.timepoint = b.dataset.time; panel.querySelectorAll('.evidence-filter').forEach(x=>x.classList.toggle('active',x===b)); render(); });
    render();
  }

  function openWizard(existing) {
    if ($('evidence-dialog')) $('evidence-dialog').remove();
    const e = existing || {};
    const d = document.createElement('dialog'); d.id='evidence-dialog'; d.innerHTML = `<form method="dialog" class="dialog-card evidence-wizard"><button class="close" value="cancel">×</button><span class="eyebrow">${existing?'EDIT':'ADD'} EVIDENCE</span><h2>${existing?'Edit evidence':'Add evidence'}</h2><div class="wizard-grid"><label>Type<select name="type"><option ${e.type==='Macro'?'selected':''}>Macro</option><option ${e.type==='Tissue'?'selected':''}>Tissue</option><option ${e.type==='Cellular'?'selected':''}>Cellular</option><option ${e.type==='Molecular'?'selected':''}>Molecular</option></select></label><label>Timepoint<select name="timepoint"><option>T0</option><option>T1</option><option>T2</option><option>T3</option></select></label><label>Modality<input name="modality" value="${e.modality||''}" placeholder="Microscopy"></label><label>Source<input name="source" value="${e.source||''}" placeholder="Laboratory / instrument"></label><label>Resolution<input name="resolution" value="${e.resolution||''}" placeholder="e.g. 0.5 µm/pixel"></label><label>Subject<input name="subject" value="${e.subject||'own_cohort'}"></label></div><label>File<input name="file" type="file" ${existing?'':'required'}></label><label>Research signals <textarea name="signals" placeholder="health_score=0.82\nstress_score=0.21\nsenescence_score=0.33">${e.signalText||''}</textarea></label><div class="dropzone">Drop a file here or use the file picker above</div><button id="evidence-save" class="primary" value="default">${existing?'Save changes':'Save evidence'}</button></form>`;
    document.body.appendChild(d); d.showModal();
    d.querySelector('form').onsubmit = async (ev) => { ev.preventDefault(); const f=new FormData(ev.target); const file=f.get('file'); const item={id:e.id||crypto.randomUUID(),type:f.get('type'),timepoint:f.get('timepoint'),modality:f.get('modality'),source:f.get('source'),resolution:f.get('resolution'),subject:f.get('subject'),signalText:f.get('signals'),filename:file&&file.name?file.name:(e.filename||'manual-entry'),target:target(),archived:false}; state.evidence=state.evidence.filter(x=>x.id!==item.id); state.evidence.unshift(item); persist(); d.close(); d.remove(); render(); try { await attachBackend(item,file); } catch(err) { console.warn('Evidence backend sync failed',err); } };
  }

  async function attachBackend(item,file) {
    if (!file) return;
    const fd=new FormData(); fd.append('file',file); fd.append('target_id',item.target); fd.append('spatial_level',item.type.toLowerCase()); fd.append('subject_id',item.subject); fd.append('timepoint',item.timepoint); fd.append('modality',item.modality); fd.append('resolution',item.resolution); fd.append('source',item.source); if(item.signalText) fd.append('signals_json', JSON.stringify(parseSignals(item.signalText)));
    const r=await fetch('/api/spatial/attach',{method:'POST',body:fd}); if(!r.ok) throw new Error(`HTTP ${r.status}`);
  }
  function parseSignals(s){const out={}; String(s||'').split(/\n|,/).forEach(x=>{const [k,v]=x.split('=').map(y=>y.trim()); if(k&&v!==undefined) out[k]=Number.isNaN(Number(v))?v:Number(v);}); return out;}
  function persist(){localStorage.setItem('digitalTwinEvidenceUX',JSON.stringify({evidence:state.evidence,archived:[...state.archived]}));}
  function load(){try{const x=JSON.parse(localStorage.getItem('digitalTwinEvidenceUX')||'{}');state.evidence=x.evidence||[];state.archived=new Set(x.archived||[]);}catch{}}
  function render(){const box=$('evidence-cards');if(!box)return; const list=state.evidence.filter(e=>e.target===target()||!e.target); const visible=list.filter(e=>state.timepoint==='all'?true:state.timepoint==='archived'?e.archived:e.timepoint===state.timepoint&&!e.archived); box.innerHTML=visible.length?visible.map(e=>`<article class="evidence-card"><div class="evidence-card-head"><span class="evidence-badge">${e.type}</span><span>${e.timepoint}</span></div><strong>${e.filename}</strong><small>${e.modality||'—'} · ${e.source||'source not set'}</small><small>${e.target}</small><div class="evidence-actions"><button data-edit="${e.id}">Edit</button><button data-archive="${e.id}">${e.archived?'Restore':'Archive'}</button><button data-view="${e.id}">Details</button></div></article>`).join(''):`<div class="empty-state">No evidence for this target and filter.<br><button class="secondary" id="empty-add">＋ Add Evidence</button></div>`;
    box.querySelector('#empty-add')?.addEventListener('click',openWizard); box.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>openWizard(state.evidence.find(e=>e.id===b.dataset.edit))); box.querySelectorAll('[data-archive]').forEach(b=>b.onclick=()=>{const e=state.evidence.find(x=>x.id===b.dataset.archive);e.archived=!e.archived;persist();render();}); box.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>detail(state.evidence.find(e=>e.id===b.dataset.view)));
  }
  function detail(e){const d=document.createElement('dialog');d.className='evidence-detail';d.innerHTML=`<div class="dialog-card"><button class="close">×</button><span class="eyebrow">EVIDENCE DETAIL</span><h2>${e.filename}</h2><dl><dt>Type</dt><dd>${e.type}</dd><dt>Target</dt><dd>${e.target}</dd><dt>Timepoint</dt><dd>${e.timepoint}</dd><dt>Modality</dt><dd>${e.modality||'—'}</dd><dt>Source</dt><dd>${e.source||'—'}</dd><dt>Resolution</dt><dd>${e.resolution||'—'}</dd></dl><h3>Research signals</h3><pre>${e.signalText||'No signals supplied.'}</pre><button class="primary" id="detail-edit">Edit</button></div>`;document.body.appendChild(d);d.showModal();d.querySelector('.close').onclick=()=>{d.close();d.remove()};d.querySelector('#detail-edit').onclick=()=>{d.close();d.remove();openWizard(e)};}
  window.addEventListener('digital-twin:target-changed',e=>{window.spatialEvidenceTarget=e.detail?.id||e.detail;render();});
  load(); document.addEventListener('DOMContentLoaded',ensurePanel); if(document.readyState!=='loading') ensurePanel();
})();
