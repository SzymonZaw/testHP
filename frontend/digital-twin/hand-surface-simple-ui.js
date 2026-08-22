(() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function target(){
    const t=window.testhpSpatialContract?.getTarget?.()||window.selectedSpatialNode||window.spatialEvidenceTarget;
    if(t&&typeof t==='object')return{label:t.label||t.path?.join(' > ')||t.spatial_id||t.id||'Bieżący cel',spatial_id:t.spatial_id||t.spatialId||t.id||'hand'};
    return{label:String(t||'Dłoń'),spatial_id:String(t||'hand')};
  }
  function installCss(){
    if($('hand-surface-unified-css-v3'))return;
    const style=document.createElement('style');style.id='hand-surface-unified-css-v3';style.textContent=`
      #hand-surface-unified{margin:16px 0;border:1px solid var(--border,#d8dee8);border-radius:14px;background:var(--panel,#fff);overflow:hidden}
      #hand-surface-unified .hsu-head{padding:16px 18px;border-bottom:1px solid var(--border,#d8dee8);display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap}
      #hand-surface-unified .hsu-kicker{display:block;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#667085}.hsu-title{font-size:18px;font-weight:800;margin-top:3px}
      #hand-surface-unified .hsu-target{font-size:12px;color:#667085;text-align:right}.hsu-target span{display:block;font-size:11px;font-weight:800;letter-spacing:.06em}.hsu-target strong{display:block;color:inherit;font-size:14px}.hsu-target code{font-size:11px}
      #hand-surface-unified .hsu-nav{display:flex;gap:6px;padding:10px 14px;border-bottom:1px solid var(--border,#d8dee8);background:rgba(79,111,143,.04);align-items:center;flex-wrap:wrap}
      #hand-surface-unified .hsu-nav button,#hand-surface-unified .hsu-subnav button{border:0;background:transparent;border-radius:9px;padding:8px 12px;cursor:pointer;font-weight:700;color:inherit}.hsu-nav button.active,.hsu-subnav button.active{background:#172033!important;color:#fff!important}
      #hand-surface-unified .hsu-progress{margin-left:auto;font-size:12px;color:#667085}.hsu-body{padding:0 14px 14px}.hsu-section[hidden]{display:none!important}
      #hand-surface-unified .hsu-subnav{display:flex;gap:6px;flex-wrap:wrap;padding:12px 0 8px;border-bottom:1px solid var(--border,#d8dee8);margin-bottom:8px}
      #hand-surface-unified .panel-title,#hand-surface-unified .hss-tabs,#hand-surface-unified .hss22-tabs{display:none!important}
      #hand-surface-unified .panel{margin:0;border:0;box-shadow:none}#hand-surface-unified .hss22-grid{grid-template-columns:1fr!important}
      /* The original panels stay mounted for their data/actions, but cannot appear as separate modules. */
      #hand-surface-unified ~ #hand-surface-studio,#hand-surface-unified ~ #hand-surface-stages-20-22{display:none!important}
      body > #hand-surface-studio,body > #hand-surface-stages-20-22{display:none!important}
      @media(max-width:700px){#hand-surface-unified .hsu-progress{width:100%;margin-left:0}.hsu-target{text-align:left}}
    `;document.head.appendChild(style);
  }
  function createShell(){
    let shell=$('hand-surface-unified');if(shell)return shell;
    const studio=$('hand-surface-studio');if(!studio?.parentElement)return null;
    const shellEl=document.createElement('section');shellEl.id='hand-surface-unified';shellEl.className='panel';
    shellEl.innerHTML=`<div class="hsu-head"><div><span class="hsu-kicker">HAND SURFACE</span><div class="hsu-title">Materiał → geometria → rejestracja</div></div><div class="hsu-target" id="hand-surface-unified-target"></div></div><div class="hsu-nav" role="tablist"><button class="active" data-hsu-tab="material">Materiał</button><button data-hsu-tab="registration">Rejestracja</button><span class="hsu-progress" id="hand-surface-unified-progress"></span></div><div class="hsu-body"><div class="hsu-section" data-hsu-section="material"></div><div class="hsu-section" data-hsu-section="registration" hidden></div></div>`;
    studio.parentElement.insertBefore(shellEl,studio);return shellEl;
  }
  function movePanels(shell){
    const studio=$('hand-surface-studio'),registration=$('hand-surface-stages-20-22'),material=shell?.querySelector('[data-hsu-section="material"]'),reg=shell?.querySelector('[data-hsu-section="registration"]');
    if(studio&&material&&studio.parentElement!==material)material.appendChild(studio);if(registration&&reg&&registration.parentElement!==reg)reg.appendChild(registration);
  }
  function makeSubnav(section,items){
    if(!section||section.querySelector('.hsu-subnav'))return;const nav=document.createElement('div');nav.className='hsu-subnav';nav.innerHTML=items.map(x=>`<button data-hsu-under="${x.tab}">${x.label}</button>`).join('');section.insertBefore(nav,section.firstChild);
    nav.querySelectorAll('[data-hsu-under]').forEach(btn=>btn.addEventListener('click',()=>{nav.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b===btn));section.querySelector(`[data-tab="${btn.dataset.hsuUnder}"]`)?.click();}));
  }
  function selectTab(kind){const shell=$('hand-surface-unified');if(!shell)return;shell.querySelectorAll('[data-hsu-tab]').forEach(b=>b.classList.toggle('active',b.dataset.hsuTab===kind));shell.querySelectorAll('[data-hsu-section]').forEach(s=>s.hidden=s.dataset.hsuSection!==kind);const section=shell.querySelector(`[data-hsu-section="${kind}"]`);section?.querySelector('.hsu-subnav button')?.click();}
  function updateTarget(){const shell=$('hand-surface-unified');if(!shell)return;const t=target();const el=$('hand-surface-unified-target');if(el)el.innerHTML=`<span>AKTUALNY CEL</span><strong>${esc(t.label)}</strong><code>${esc(t.spatial_id)}</code>`;const p=$('hand-surface-unified-progress');if(p)p.textContent=`Wszystko poniżej dotyczy: ${t.spatial_id}`;}
  function boot(){installCss();const shell=createShell();if(!shell)return;movePanels(shell);const material=shell.querySelector('[data-hsu-section="material"]'),reg=shell.querySelector('[data-hsu-section="registration"]');makeSubnav(material,[{tab:'evidence',label:'Źródła'},{tab:'prepare',label:'Przygotowanie'},{tab:'geometry',label:'Geometria'}]);makeSubnav(reg,[{tab:'registration',label:'Kontrola jakości'},{tab:'projection',label:'Plan projekcji'},{tab:'package',label:'Pakiet bliźniaka'}]);shell.querySelectorAll('[data-hsu-tab]').forEach(b=>{if(b.dataset.bound==='1')return;b.dataset.bound='1';b.addEventListener('click',()=>selectTab(b.dataset.hsuTab));});updateTarget();selectTab('material');}
  let scheduled=false;const schedule=()=>{if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;boot();});};
  window.addEventListener('testhp:spatial-layer-changed',()=>{updateTarget();schedule();});window.addEventListener('testhp:spatial-contract-changed',()=>{updateTarget();schedule();});window.addEventListener('testhp:evidence-attached',schedule);window.addEventListener('testhp:hand-surface-ready',schedule);window.addEventListener('testhp:surface-projection-plan-changed',schedule);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
