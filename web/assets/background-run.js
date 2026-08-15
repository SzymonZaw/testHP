(() => {
  const button = document.getElementById('run-button');
  if (!button) return;
  const replacement = button.cloneNode(true);
  button.replaceWith(replacement);
  const stageNames = { input:'Input', ingestion:'Ingestion', validation:'Validation', normalization:'Normalization', fusion:'Multimodal fusion', results:'Research view' };
  const stageOrder = ['input','ingestion','validation','normalization','fusion','results'];
  let timer = null;
  function renderRunning(job) {
    const current = stageOrder.indexOf(job.current_stage);
    const purposes = {
      input:'Identify selected research datasets', ingestion:'Read available files from data/raw', validation:'Check files, formats and empty inputs', normalization:'Convert sources into common observations', fusion:'Aggregate dataset-level evidence without inventing subject links', results:'Present measured evidence, coverage and limitations'
    };
    const steps = stageOrder.map((id,index)=>({id,name:stageNames[id],purpose:purposes[id],status:index<current?'completed':index===current?'running':'pending'}));
    if (typeof renderPipeline === 'function') renderPipeline({steps});
    const status=document.getElementById('run-status');
    if(status){status.textContent=`${stageNames[job.current_stage]||'Processing'} · ${job.progress||0}%`;status.className='badge neutral';}
    replacement.disabled=true; replacement.textContent=`Processing… ${job.progress||0}%`;
  }
  async function poll(jobId){
    try{
      const r=await fetch(`/api/run/background/${encodeURIComponent(jobId)}`); if(!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      const job=await r.json();
      if(job.status==='running'){renderRunning(job);timer=setTimeout(()=>poll(jobId),500);return;}
      if(job.status==='completed'){
        clearTimeout(timer); state.run=job.result;
        if(typeof renderMetrics==='function') renderMetrics(state.run.summary);
        if(typeof renderRunStatus==='function') renderRunStatus(state.run);
        if(typeof renderPipeline==='function') renderPipeline(state.run);
        if(typeof renderOutput==='function') renderOutput(state.run);
        if(typeof renderInput==='function') renderInput(state.run.datasets||[]);
        if(typeof renderFilters==='function') renderFilters(state.run.datasets||[]);
        if(typeof renderTable==='function') renderTable(state.run.datasets||[]);
        if(typeof saveHistory==='function') saveHistory(state.run);
        replacement.disabled=false; replacement.textContent='Run research pipeline'; return;
      }
      throw new Error(job.error||`Pipeline status: ${job.status}`);
    }catch(error){
      clearTimeout(timer); replacement.disabled=false; replacement.textContent='Run research pipeline';
      const status=document.getElementById('run-status'); if(status){status.textContent='Run failed';status.className='badge warning';}
      const detail=document.getElementById('stage-detail'); if(detail){detail.className='stage-detail';detail.innerHTML=`<div class="detail-note"><strong>Pipeline error</strong><p>${String(error.message||error)}</p></div>`;}
    }
  }
  replacement.addEventListener('click',async()=>{
    replacement.disabled=true;replacement.textContent='Starting…';
    try{
      const r=await fetch('/api/run/background',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({datasets:[]})});
      if(!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      const job=await r.json(); renderRunning(job); poll(job.job_id);
    }catch(error){
      replacement.disabled=false;replacement.textContent='Run research pipeline';
      const status=document.getElementById('run-status'); if(status){status.textContent='Run failed';status.className='badge warning';}
      const detail=document.getElementById('stage-detail'); if(detail){detail.className='stage-detail';detail.innerHTML=`<div class="detail-note"><strong>Could not start run</strong><p>${String(error.message||error)}</p></div>`;}
    }
  });
})();
