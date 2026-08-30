(() => {
'use strict';
const KEY='TestHPDigitalTwinSelfTest';
if(window[KEY]) return;
const checks=[];
const check=(name,ok,detail='')=>checks.push({name,ok:Boolean(ok),detail});
async function run(){
  checks.length=0;
  const root=document.getElementById('testhp-end-user-layer');
  check('main screen exists',!!root&&!!root.querySelector('.dt'));
  check('canonical state exists',!!window.TestHPCanonicalState);
  const canonical=window.TestHPCanonicalState?.get?.();
  check('canonical selection has subject/timepoint/region',!!canonical?.selection?.subject&&!!canonical?.selection?.timepoint&&!!canonical?.selection?.region);
  check('canonical selection contains tissue/cell/molecular layer',Object.prototype.hasOwnProperty.call(canonical?.selection||{},'tissue')&&Object.prototype.hasOwnProperty.call(canonical?.selection||{},'cell')&&Object.prototype.hasOwnProperty.call(canonical?.selection||{},'molecularLayer'));
  check('evidence panel exists',!!root?.querySelector('.coverage')&&root?.querySelectorAll('.evrow').length===8);
  check('biological age panel exists',!!root?.querySelector('.feature-panel')&&/BIOLOGICAL AGE/i.test(root?.querySelector('.feature-panel')?.textContent||''));
  check('trajectory panel exists',/TRAJECTORY/i.test(root?.textContent||''));
  check('what-if is explicitly hypothetical',/HYPOTHETICAL/i.test(root?.textContent||'')||/WHAT-IF/i.test(root?.textContent||''));
  check('intervention is bounded',/NOT ESTABLISHED/i.test(root?.textContent||''));
  check('governance panel exists',/GOVERNANCE/i.test(root?.textContent||''));
  check('no clinical-ready claim',!(/clinical ready(?!ness)/i.test(root?.textContent||'')));
  try{const health=await fetch('/api/health',{cache:'no-store'});check('backend health endpoint',health.ok,`HTTP ${health.status}`)}catch(e){check('backend health endpoint',false,String(e))}
  try{const analysis=await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(canonical?.selection?.subject||'own_cohort')}&timepoint=${encodeURIComponent(canonical?.selection?.timepoint||'T0')}`,{cache:'no-store'});check('analysis endpoint',analysis.ok,`HTTP ${analysis.status}`)}catch(e){check('analysis endpoint',false,String(e))}
  try{const status=await fetch(`/api/hand/digital-twin-status?subject_id=${encodeURIComponent(canonical?.selection?.subject||'own_cohort')}&hand_id=hand-001&timepoint_id=${encodeURIComponent(canonical?.selection?.timepoint||'T0')}`,{cache:'no-store'});check('digital-twin status endpoint',status.ok,`HTTP ${status.status}`)}catch(e){check('digital-twin status endpoint',false,String(e))}
  const result={ok:checks.every(x=>x.ok),checks,at:new Date().toISOString()};
  console.groupCollapsed(`[TestHP Digital Twin] ${result.ok?'PASS':'FAIL'}`);console.table(checks);console.groupEnd();
  window.dispatchEvent(new CustomEvent('testhp:digital-twin-self-test',{detail:result}));
  return result;
}
window[KEY]={run};
window.TestHPDigitalTwinSelfTest=Object.freeze({run});
})();
