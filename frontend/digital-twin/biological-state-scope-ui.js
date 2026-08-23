(() => {
  function render(payload) {
    const state=payload?.state||{}; const summary=payload?.summary||{};
    const observationCount=Number(state.observation_count??summary.observation_count??0);
    const evidenceCount=Number(state.evidence_count??summary.evidence_count??0);
    const count=document.getElementById('evidence-count'); const availability=document.getElementById('evidence-level');
    if(count)count.textContent=`${observationCount} element${observationCount===1?'':'ów'}`;
    if(availability)availability.textContent=observationCount>0?(evidenceCount>0?'Dane obserwowane + evidence':'Dane obserwowane'):'Brak obserwacji';
    const target=window.testhpSpatialContract?.getTarget?.();
    if(target?.spatial_id){const context=document.getElementById('region-context');if(context)context.textContent=`${target.label||target.spatial_id} · T0`}
    const interpretations=state.interpretations||{};
    const map={biological_age:'age-state',structural_functional_state:'structure-state',damage:'damage-state',pathology:'pathology-state'};
    Object.entries(map).forEach(([key,id])=>{const el=document.getElementById(id);if(!el)return;const value=interpretations[key];el.textContent=value==null||String(value).trim()===''?(key==='biological_age'?'Nieustalony':key==='pathology'?'Nieustalona':'Nieustalone'):String(value)})
  }
  async function refresh(){const target=window.testhpSpatialContract?.getTarget?.();if(!target?.spatial_id)return;const params=new URLSearchParams({subject_id:'own_cohort',timepoint:'T0',spatial_id:target.spatial_id,include_descendants:'false'});try{const r=await fetch(`/api/biological-state?${params.toString()}`,{cache:'no-store'});if(r.ok)render(await r.json())}catch{}}
  window.addEventListener('testhp:biological-state-updated',e=>render(e.detail));
  window.addEventListener('testhp:spatial-contract-changed',refresh);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh,{once:true});else refresh();

  // Explicit target-source/registry diagnosis. This is intentionally loaded here so it
  // remains independent from the main hand-surface renderer and cannot change routing.
  const loadTargetConsistencyDebug = () => {
    if (window.__testhpTargetConsistencyDebugInstalled || document.getElementById('testhp-target-consistency-debug-script')) return;
    const script = document.createElement('script');
    script.id = 'testhp-target-consistency-debug-script';
    script.src = '/digital-twin/target-consistency-debug.js?v=target-consistency-1';
    script.async = true;
    script.onerror = () => window.dispatchEvent(new CustomEvent('testhp:target-consistency-debug-error'));
    document.head.appendChild(script);
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',loadTargetConsistencyDebug,{once:true});else loadTargetConsistencyDebug();
})();
