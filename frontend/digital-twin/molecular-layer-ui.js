import { getDigitalTwinState, subscribeDigitalTwinState, updateSelection } from './canonical-ui-runtime.js';
import { MOLECULAR_LAYERS, suppliedMolecularLayers } from './digital-twin-phase1-8-governor.js';
const esc=v=>String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
function render(state){
  const host=document.getElementById('testhp-end-user-layer'); if(!host||!state.selection.cell)return;
  const right=host.querySelector('.dt-right'); if(!right||right.querySelector('.dt-molecular-card'))return;
  const available=new Set(suppliedMolecularLayers(state,state.selection.cell).map(x=>x.id));
  const card=document.createElement('section'); card.className='dt-card dt-molecular-card';
  card.innerHTML=`<div class="dt-card-title">MOLECULAR · CELL ${esc(state.selection.cell)}</div>${MOLECULAR_LAYERS.map(([id,label])=>`<button class="dt-mol ${available.has(id)?'available':'missing'} ${state.selection.molecularLayer===id?'active':''}" data-molecular="${id}">${esc(label)} <span>${available.has(id)?'Available':'Missing'}</span></button>`).join('')}`;
  right.insertBefore(card,right.firstChild);
  card.querySelectorAll('[data-molecular]').forEach(b=>b.onclick=()=>updateSelection({molecularLayer:available.has(b.dataset.molecular)?b.dataset.molecular:null}));
}
const style=document.createElement('style');style.textContent='.dt-molecular-card .dt-mol{display:flex;justify-content:space-between;width:100%;padding:7px 0;border:0;border-bottom:1px solid #19212b;background:transparent;color:#8fa0b2;text-align:left;cursor:pointer;font-size:11px}.dt-molecular-card .dt-mol span{color:#667487}.dt-molecular-card .dt-mol.available span{color:#79caa1}.dt-molecular-card .dt-mol.active{color:#69b8ff}';document.head.appendChild(style);
subscribeDigitalTwinState(render);
