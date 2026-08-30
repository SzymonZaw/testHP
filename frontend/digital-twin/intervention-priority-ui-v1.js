(() => {
  'use strict';
  const KEY='__testhpInterventionPriorityUIV1';
  if(window[KEY]) return;
  function mount(analysis){
    let host=document.getElementById('testhp-intervention-layer');
    if(!host){host=document.createElement('section');host.id='testhp-intervention-layer';document.body.appendChild(host);}
    const assessments=Array.isArray(analysis?.assessments)?analysis.assessments:[];
    const items=assessments.map(a=>({
      region:String(a.region_id||a.regionId||'Unknown'),
      problem:String(a.problem||a.intervention_reason||a.label||'No intervention reason established'),
      priority:String(a.priority||'UNKNOWN').toUpperCase(),
      confidence:Number.isFinite(Number(a.confidence))?Math.round(Number(a.confidence)*100):null,
      evidence:Array.isArray(a.evidence)?a.evidence.length:0
    })).filter(a=>a.priority!=='UNKNOWN'||a.problem!=='No intervention reason established');
    host.innerHTML=`<div class="testhp-ip-card"><div class="testhp-ip-head"><div><span class="testhp-ip-kicker">Intervention Priority</span><h2>Where should attention be focused?</h2></div><span class="testhp-ip-note">Decision support only</span></div>${items.length?items.map(item=>`<article class="testhp-ip-item"><div><strong>${escapeHtml(item.region)}</strong><span>${escapeHtml(item.problem)}</span></div><b>${escapeHtml(item.priority)}</b><div class="testhp-ip-meta"><span>Confidence: ${item.confidence==null?'—':item.confidence+'%'}</span><span>Evidence: ${item.evidence}</span></div></article>`).join(''):`<div class="testhp-ip-empty"><strong>No intervention priority established</strong><span>The system has no explicit, validated intervention assessment for the supplied data. Missing evidence is not treated as a reason to recommend treatment or rejuvenation.</span></div>`}</div>`;
  }
  function escapeHtml(v){return String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));}
  function init(){if(!document.getElementById('testhp-intervention-layer-style')){const s=document.createElement('style');s.id='testhp-intervention-layer-style';s.textContent=`#testhp-intervention-layer{max-width:1180px;margin:16px auto;padding:0 18px;font-family:Inter,system-ui,sans-serif;color:#e8edf5}.testhp-ip-card{background:#111722;border:1px solid #293345;border-radius:18px;padding:20px}.testhp-ip-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.testhp-ip-kicker{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#8190a8}.testhp-ip-head h2{margin:6px 0 0;font-size:22px}.testhp-ip-note{font-size:12px;color:#94a0b5;border:1px solid #344056;border-radius:999px;padding:7px 10px}.testhp-ip-item{display:grid;grid-template-columns:1fr auto;gap:7px 18px;margin-top:12px;padding:15px;border:1px solid #2a3548;border-radius:13px;background:#171f2d}.testhp-ip-item>div:first-child{display:flex;flex-direction:column;gap:4px}.testhp-ip-item>div:first-child span,.testhp-ip-meta{color:#94a0b5;font-size:13px}.testhp-ip-item>b{align-self:center;letter-spacing:.06em}.testhp-ip-meta{grid-column:1/-1;display:flex;gap:18px}.testhp-ip-empty{display:flex;flex-direction:column;gap:8px;margin-top:14px;padding:18px;border:1px dashed #344056;border-radius:12px;color:#94a0b5;line-height:1.5}.testhp-ip-empty strong{color:#e8edf5}@media(max-width:700px){.testhp-ip-head{flex-direction:column}.testhp-ip-meta{flex-direction:column;gap:4px}}`;document.head.appendChild(s)}
    const listener=e=>mount(e.detail?.analysis||e.detail||null);window.addEventListener('testhp:analysis-ready',listener);window.addEventListener('testhp:digital-twin-analysis-ready',listener);mount(window.__testhpLastAnalysis||null);
  }
  window[KEY]=Object.freeze({mount});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
