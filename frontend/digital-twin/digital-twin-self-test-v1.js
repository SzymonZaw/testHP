(() => {
'use strict';
const KEY='TestHPDigitalTwinSelfTest';
if(window[KEY]) return;
const checks=[];
const check=(name,ok,detail='')=>checks.push({name,ok:Boolean(ok),detail});
async function run(){
  checks.length=0;
  const root=document.getElementById('testhp-end-user-layer');
  const canonical=window.TestHPCanonicalState?.get?.();
  check('main screen exists',!!root&&!!root.querySelector('.dt-canonical'));
  check('canonical state exists',!!window.TestHPCanonicalState);
  check('canonical state version 4',canonical?.stateVersion==='4');
  check('canonical selection has subject/timepoint/region',!!canonical?.selection?.subject&&!!canonical?.selection?.timepoint&&!!canonical?.selection?.region);
  check('canonical selection contains tissue/cell/molecular layer',Object.prototype.hasOwnProperty.call(canonical?.selection||{},'tissue')&&Object.prototype.hasOwnProperty.call(canonical?.selection||{},'cell')&&Object.prototype.hasOwnProperty.call(canonical?.selection||{},'molecularLayer'));
  check('canonical evidence exists',!!canonical?.evidence&&Object.prototype.hasOwnProperty.call(canonical.evidence,'coverage'));
  check('canonical biological state exists',!!canonical?.biologicalState&&canonical.biologicalState.status==='Not established' || !!canonical?.biologicalState);
  check('evidence panel exists',!!root?.querySelector('.dt-card')&&root?.querySelectorAll('.dt-evidence-row').length===8);
  check('3D viewport host exists',!!root?.querySelector('#twin-viewport'));
  check('spatial region tree exists',root?.querySelectorAll('[data-region]').length===8);
  check('cell inspector is backend-bounded',/No cell is created by the frontend/i.test(root?.textContent||'')||!!root?.querySelector('[data-cell]'));
  check('governance is research-only',/RESEARCH ONLY/i.test(root?.textContent||'')&&/Clinical readiness is not established/i.test(root?.textContent||''));
  check('no clinical recommendation claim',!/clinical recommendation/i.test(root?.textContent||''));
  try{const health=await fetch('/api/health',{cache:'no-store'});check('backend health endpoint',health.ok,`HTTP ${health.status}`)}catch(e){check('backend health endpoint',false,String(e))}
  try{const analysis=await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(canonical?.selection?.subject||'own_cohort')}&timepoint=${encodeURIComponent(canonical?.selection?.timepoint||'T0')}`,{cache:'no-store'});check('analysis endpoint',analysis.ok,`HTTP ${analysis.status}`)}catch(e){check('analysis endpoint',false,String(e))}
  const result={ok:checks.every(x=>x.ok),checks,at:new Date().toISOString()};
  console.groupCollapsed(`[TestHP Digital Twin] ${result.ok?'PASS':'FAIL'}`);console.table(checks);console.groupEnd();
  window.dispatchEvent(new CustomEvent('testhp:digital-twin-self-test',{detail:result}));
  return result;
}
window[KEY]={run};
window.TestHPDigitalTwinSelfTest=Object.freeze({run});
})();
