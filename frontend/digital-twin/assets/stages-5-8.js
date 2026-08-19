(() => {
  const panel=document.createElement('section');
  panel.className='panel';
  panel.id='stages-5-8-panel';
  panel.innerHTML=`<div class="panel-title"><div><span class="section-kicker">DIGITAL TWIN ENGINE</span><strong>STAGES 5–8</strong></div><span class="research-badge">RESEARCH ONLY</span></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;padding:16px"><article class="state-card"><span>Evidence layer</span><strong id="s58-evidence">Evidence layer</strong><small>Stage 5 · spatially attached observations</small></article><article class="state-card"><span>Anatomy</span><strong id="s58-anatomy">Anatomical structure</strong><small>Stage 6 · depth context</small></article><article class="state-card"><span>Progressive resolution</span><strong id="s58-resolution">Progressive biological resolution</strong><small>Stage 7 · context preserved</small></article><article class="state-card"><span>Longitudinal</span><strong id="s58-longitudinal">Longitudinal twin</strong><small>Stage 8 · time-aware twin</small></article></div><div id="s58-findings" style="padding:0 16px 16px"></div>`;

  const mount=()=>{
    const anchor=document.querySelector('.timeline');
    if(anchor && !document.getElementById('stages-5-8-panel')) anchor.after(panel);
    const findings=document.getElementById('s58-findings');
    if(findings) findings.textContent='Stages 5–8 registered. Evidence is explicit research data; navigation targets do not imply biological findings.';
  };

  // Keep the critical boot path independent of the hand-surface engine.
  // hand-surface-engine.js owns its own renderer, OrbitControls dependency and
  // async evidence loading. Importing it here can block startup on a CDN/module
  // request, so it must not be part of stages 5–8 bootstrap.
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();
