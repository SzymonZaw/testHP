/* Biological age hierarchy UI v2. Values are displayed only when established by upstream evidence. */
(function(){
  'use strict';
  const LEVELS=['hand','region','tissue','cell_type'];
  function normalize(n){return n && typeof n==='object'?n:null;}
  function formatAge(node){
    const n=normalize(node);
    if(!n || n.status==='not_established' || n.age==null) return 'Nieustalone naukowo';
    const age=Number(n.age); if(!Number.isFinite(age)) return 'Nieustalone naukowo';
    const unit=n.unit||'years';
    const uncertainty=n.uncertainty;
    return uncertainty!=null?`${age.toFixed(1)} ${unit} ± ${Number(uncertainty).toFixed(1)}`:`${age.toFixed(1)} ${unit}`;
  }
  function render(container, hierarchy){
    if(!container)return;
    container.replaceChildren();
    const walk=(node,depth)=>{
      if(!node || !LEVELS.includes(node.level))return;
      const row=document.createElement('div'); row.className=`age-node level-${node.level}`; row.style.paddingLeft=`${depth*20}px`;
      const label=document.createElement('span'); label.className='age-label'; label.textContent=node.label||node.id||node.level;
      const value=document.createElement('span'); value.className='age-value'; value.textContent=formatAge(node); row.append(label,value); container.appendChild(row);
      (node.children||[]).forEach(child=>walk(child,depth+1));
    };
    walk(hierarchy,0);
  }
  let canonicalAge=null;
  function setCanonicalAge(view){
    canonicalAge=view||null;
    window.dispatchEvent(new CustomEvent('testhp:biological-age-canonical-changed',{detail:canonicalAge}));
  }
  window.TestHPBiologicalAgeHierarchy={render,formatAge,getCanonical:()=>canonicalAge};
  window.addEventListener('testhp:canonical-biological-age-changed',e=>setCanonicalAge(e.detail));
})();
