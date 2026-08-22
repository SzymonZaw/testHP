(() => {
  const $ = id => document.getElementById(id);
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function getTarget() {
    const node = window.selectedSpatialNode || window.spatialEvidenceTarget;
    if (node && typeof node === 'object') return { id: node.id || '', spatial_id: node.spatial_id || node.spatialId || node.id || 'hand', label: node.label || node.path?.join(' > ') || node.spatial_id || node.id || 'Bieżący cel' };
    const value = window.spatialEvidenceTarget || document.body.dataset.spatialTarget || 'hand';
    return { id: '', spatial_id: String(value), label: String(value) };
  }
  function installCss() {
    if ($('hand-surface-unified-ui-css')) return;
    const style = document.createElement('style'); style.id = 'hand-surface-unified-ui-css';
    style.textContent = `
      #hand-surface-unified{margin:16px 0;border:1px solid var(--border,#d8dee8);border-radius:14px;background:var(--panel,#fff);overflow:hidden}
      #hand-surface-unified .hsu-head{padding:16px 18px;border-bottom:1px solid var(--border,#d8dee8);display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap}
      #hand-surface-unified .hsu-kicker{display:block;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted,#667085);margin-bottom:3px}
      #hand-surface-unified .hsu-title{font-size:18px;font-weight:800}
      #hand-surface-unified .hsu-target{font-size:13px;color:var(--muted,#667085);text-align:right}.hsu-target span{display:block;font-size:11px;font-weight:800;letter-spacing:.06em}.hsu-target strong{display:block;color:inherit;font-size:14px}.hsu-target code{font-size:11px}
      #hand-surface-unified .hsu-nav{display:flex;gap:6px;padding:10px 14px;border-bottom:1px solid var(--border,#d8dee8);background:rgba(79,111,143,.04);align-items:center}
      #hand-surface-unified .hsu-nav button,#hand-surface-unified .hsu-subnav button{border:0;background:transparent;border-radius:9px;padding:8px 12px;cursor:pointer;font-weight:700;color:inherit}
      #hand-surface-unified .hsu-nav button.active,#hand-surface-unified .hsu-subnav button.active{background:#172033;color:#fff}
      #hand-surface-unified .hsu-progress{margin-left:auto;font-size:12px;color:var(--muted,#667085)}
      #hand-surface-unified .hsu-body{padding:0 14px 14px}.hsu-section[hidden]{display:none!important}
      #hand-surface-unified .hsu-subnav{display:flex;gap:6px;flex-wrap:wrap;padding:12px 0 8px;border-bottom:1px solid var(--border,#d8dee8);margin-bottom:8px}
      #hand-surface-unified .hsu-subnav button{font-size:13px;font-weight:650}
      #hand-surface-unified .hsu-subnav button .num{font-size:10px;opacity:.65;margin-right:4px}
      #hand-surface-unified .panel-title,#hand-surface-unified .hss-tabs,#hand-surface-unified .hss22-tabs{display:none!important}
      #hand-surface-unified .panel{margin:0;border:0;box-shadow:none}
      @media(max-width:700px){#hand-surface-unified .hsu-progress{width:100%;margin-left:0}.hsu-target{text-align:left}}
    `;
    document.head.appendChild(style);
  }
  function createShell() {
    if ($('hand-surface-unified')) return $('hand-surface-unified');
    const studio = $('hand-surface-studio'); if (!studio?.parentElement) return null;
    const shell = document.createElement('section'); shell.id='hand-surface-unified'; shell.className='panel';
    shell.innerHTML = `<div class="hsu-head"><div><span class="hsu-kicker">HAND SURFACE</span><div class="hsu-title">Materiał → geometria → rejestracja</div></div><div class="hsu-target" id="hand-surface-unified-target"></div></div><div class="hsu-nav"><button class="active" data-hsu-tab="material">Materiał</button><button data-hsu-tab="registration">Rejestracja</button><span class="hsu-progress" id="hand-surface-unified-progress">Jedna ścieżka pracy dla wybranego celu</span></div><div class="hsu-body"><div class="hsu-section" data-hsu-section="material"></div><div class="hsu-section" data-hsu-section="registration" hidden></div></div>`;
    studio.parentElement.insertBefore(shell, studio); return shell;
  }
  function movePanels(shell) {
    const studio=$('hand-surface-studio'), registration=$('hand-surface-stages-20-22'); if(!studio||!registration||!shell)return false;
    const material=shell.querySelector('[data-hsu-section="material"]'), reg=shell.querySelector('[data-hsu-section="registration"]');
    if(studio.parentElement!==material) material.appendChild(studio); if(registration.parentElement!==reg) reg.appendChild(registration); return true;
  }
  function makeSubnav(shell, section, items) {
    if(section.querySelector('.hsu-subnav')) return;
    const nav=document.createElement('div'); nav.className='hsu-subnav';
    nav.innerHTML=items.map((x,i)=>`<button class="${i===0?'active':''}" data-hsu-under="${x.tab}"><span class="num">${x.num}</span>${x.label}</button>`).join('');
    section.insertBefore(nav,section.firstChild);
    nav.querySelectorAll('[data-hsu-under]').forEach(btn=>btn.addEventListener('click',()=>{
      nav.querySelectorAll('[data-hsu-under]').forEach(b=>b.classList.toggle('active',b===btn));
      const panel=section.querySelector('.panel'); panel?.querySelector(`[data-tab="${btn.dataset.hsuUnder}"]`)?.click();
    }));
  }
  function selectTab(kind) {
    const shell=$('hand-surface-unified'); if(!shell)return;
    shell.querySelectorAll('[data-hsu-tab]').forEach(b=>b.classList.toggle('active',b.dataset.hsuTab===kind));
    shell.querySelectorAll('[data-hsu-section]').forEach(s=>s.hidden=s.dataset.hsuSection!==kind);
    const section=shell.querySelector(`[data-hsu-section="${kind}"]`);
    if(kind==='material') section?.querySelector('[data-hsu-under="evidence"]')?.click();
    else section?.querySelector('[data-hsu-under="registration"]')?.click();
  }
  function updateTarget(){const shell=$('hand-surface-unified');if(!shell)return;const t=getTarget();const el=$('hand-surface-unified-target');if(el)el.innerHTML=`<span>AKTUALNY CEL</span><strong>${escapeHtml(t.label)}</strong><code>${escapeHtml(t.spatial_id)}</code>`;const p=$('hand-surface-unified-progress');if(p)p.textContent=`Wszystko poniżej dotyczy: ${t.spatial_id}`;}
  function boot(){
    installCss(); const shell=createShell(); if(!shell)return; movePanels(shell);
    const material=shell.querySelector('[data-hsu-section="material"]'), reg=shell.querySelector('[data-hsu-section="registration"]');
    makeSubnav(shell,material,[{num:'',tab:'evidence',label:'Źródła'},{num:'',tab:'prepare',label:'Przygotowanie'},{num:'',tab:'geometry',label:'Geometria'}]);
    makeSubnav(shell,reg,[{num:'',tab:'registration',label:'Kontrola jakości'},{num:'',tab:'projection',label:'Plan projekcji'},{num:'',tab:'package',label:'Pakiet bliźniaka'}]);
    shell.querySelectorAll('[data-hsu-tab]').forEach(btn=>{if(btn.dataset.hsuBound==='1')return;btn.dataset.hsuBound='1';btn.addEventListener('click',()=>selectTab(btn.dataset.hsuTab));});
    updateTarget(); selectTab('material');
  }
  let scheduled=false; const scheduleBoot=()=>{if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;boot();});};
  window.addEventListener('testhp:spatial-layer-changed',()=>{updateTarget();scheduleBoot();});window.addEventListener('testhp:evidence-attached',scheduleBoot);window.addEventListener('testhp:hand-surface-ready',scheduleBoot);window.addEventListener('testhp:surface-projection-plan-changed',scheduleBoot);
  new MutationObserver(scheduleBoot).observe(document.body,{childList:true,subtree:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
