const viewport = document.getElementById('twin-viewport');
if (!viewport) return;

const old = document.getElementById('independent-layer-visualization');
if (old) old.remove();

const wrap = document.createElement('section');
wrap.id = 'independent-layer-visualization';
Object.assign(wrap.style, {
  position: 'absolute', inset: '0', zIndex: '100', pointerEvents: 'none',
  fontFamily: 'system-ui, sans-serif'
});

const switcher = document.createElement('div');
switcher.setAttribute('aria-label', 'Visualization layer');
Object.assign(switcher.style, {
  position: 'absolute', left: '16px', right: '16px', bottom: '16px', zIndex: '110',
  display: 'flex', flexWrap: 'wrap', gap: '7px', alignItems: 'center',
  padding: '8px', borderRadius: '14px', background: '#0d1918e8',
  border: '1px solid #36544e', backdropFilter: 'blur(8px)', pointerEvents: 'auto'
});

const title = document.createElement('span');
title.textContent = 'VISUALIZATION LAYER';
Object.assign(title.style, {
  fontSize: '10px', fontWeight: '800', letterSpacing: '.12em', opacity: '.7', marginRight: '3px'
});
switcher.appendChild(title);

const stage = document.createElement('div');
Object.assign(stage.style, {
  position: 'absolute', inset: '0', display: 'none', pointerEvents: 'auto',
  overflow: 'hidden', background: 'radial-gradient(circle at 50% 45%, #18342f 0, #0b1518 62%)'
});
wrap.appendChild(stage);
wrap.appendChild(switcher);
viewport.appendChild(wrap);

const labels = ['Macro anatomy', 'Tissue field', 'Cellular field', 'Single cell'];
const keys = ['macro', 'tissue', 'cellular', 'cell'];
let selected = 'macro';

function clearStage() { stage.replaceChildren(); }
function addText(text, css = {}) {
  const e = document.createElement('div'); e.textContent = text; Object.assign(e.style, css); stage.appendChild(e); return e;
}
function targets() {
  return [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(e => e.textContent.trim()).filter(Boolean);
}
function currentTarget() {
  return document.querySelector('#spatial-node strong')?.textContent?.trim() || 'Selected target';
}
function makeButton(key, label) {
  const b = document.createElement('button'); b.type = 'button'; b.textContent = label;
  Object.assign(b.style, {
    padding: '8px 11px', borderRadius: '9px', border: '1px solid #36544e',
    background: key === selected ? '#23463e' : '#101b1a', color: '#dcece6',
    font: '600 11px system-ui,sans-serif', cursor: 'pointer'
  });
  b.onclick = () => { selected = key; render(); renderButtons(); };
  return b;
}
function renderButtons() {
  [...switcher.querySelectorAll('button')].forEach(b => b.remove());
  keys.forEach((k, i) => switcher.appendChild(makeButton(k, labels[i])));
}
function renderTissue() {
  const names = targets().slice(0, 3);
  addText('TISSUE SECTION', {position:'absolute',left:'18px',top:'18px',fontSize:'11px',fontWeight:'800',letterSpacing:'.12em',color:'#9bd8c4'});
  const plane = document.createElement('div');
  Object.assign(plane.style, {position:'absolute',left:'13%',right:'13%',top:'20%',bottom:'23%',border:'1px solid #78bca866',background:'linear-gradient(145deg,#294d45,#132824)',transform:'perspective(700px) rotateX(9deg) rotateY(-8deg)',boxShadow:'0 25px 60px #0008',borderRadius:'16px'});
  stage.appendChild(plane);
  (names.length ? names : ['Tissue region A','Tissue region B','Tissue region C']).forEach((n,i)=>{
    const p=document.createElement('div'); p.textContent=n;
    Object.assign(p.style,{position:'absolute',left:`${18+i*28}%`,top:`${42+(i%2)*17}%`,padding:'9px 12px',borderRadius:'10px',background:'#10221ee8',border:'1px solid #78bca866',color:'#dcece6',fontSize:'12px',fontWeight:'700'});stage.appendChild(p);
  });
}
function renderCellular() {
  addText('CELLULAR FIELD', {position:'absolute',left:'18px',top:'18px',fontSize:'11px',fontWeight:'800',letterSpacing:'.12em',color:'#9bd8c4'});
  const grid=document.createElement('div'); Object.assign(grid.style,{position:'absolute',inset:'18% 10% 22%',background:'radial-gradient(circle,#244b43 1px,transparent 1px)',backgroundSize:'24px 24px',border:'1px solid #36544e',borderRadius:'14px'});stage.appendChild(grid);
  for(let i=0;i<14;i++){const c=document.createElement('div');const x=12+(i*37)%76,y=18+(i*61)%66;Object.assign(c.style,{position:'absolute',left:`${x}%`,top:`${y}%`,width:'38px',height:'38px',borderRadius:'50%',background:'radial-gradient(circle at 35% 30%,#8bc7b0,#2f6759 65%,#102a24)',border:'1px solid #9bd8c488',boxShadow:'0 0 18px #5fae9844'});grid.appendChild(c)}
}
function renderCell() {
  addText('SINGLE CELL', {position:'absolute',left:'18px',top:'18px',fontSize:'11px',fontWeight:'800',letterSpacing:'.12em',color:'#9bd8c4'});
  addText(currentTarget(), {position:'absolute',left:'50%',top:'86%',transform:'translateX(-50%)',fontSize:'12px',fontWeight:'700',color:'#dcece6'});
  const cell=document.createElement('div'); Object.assign(cell.style,{position:'absolute',left:'50%',top:'48%',width:'190px',height:'190px',transform:'translate(-50%,-50%) rotateX(8deg) rotateY(-12deg)',borderRadius:'50%',background:'radial-gradient(circle at 35% 28%,#b8e4d4 0,#69ad99 35%,#315f53 70%,#122a24 100%)',border:'2px solid #9bd8c4aa',boxShadow:'0 0 45px #5fae9855, inset -20px -15px 35px #0b1714'});stage.appendChild(cell);
  const nucleus=document.createElement('div');Object.assign(nucleus.style,{position:'absolute',left:'50%',top:'50%',width:'65px',height:'65px',transform:'translate(-50%,-50%)',borderRadius:'50%',background:'#315e51',border:'2px solid #9bd8c477',boxShadow:'inset 0 0 18px #10251f'});cell.appendChild(nucleus);
}
function render() {
  clearStage();
  const base=document.getElementById('twin-canvas');
  const controls=document.querySelector('.viewer-controls');
  const hint=document.querySelector('.viewer-hint');
  const loading=document.getElementById('viewer-loading');
  const internal=document.getElementById('spatial-layer-canvas');
  const internalLabels=document.querySelector('#twin-viewport > div[style*="z-index: 21"]');
  if (selected === 'macro') {
    stage.style.display='none';
    if(base) { base.style.display='block'; base.style.visibility='visible'; }
    if(controls) controls.style.visibility='visible'; if(hint) hint.style.visibility='visible'; if(loading) loading.style.visibility='visible';
    if(internal) internal.style.display='none'; if(internalLabels) internalLabels.style.display='none';
    return;
  }
  stage.style.display='block';
  if(base) { base.style.display='none'; base.style.visibility='hidden'; }
  if(controls) controls.style.visibility='hidden'; if(hint) hint.style.visibility='hidden'; if(loading) loading.style.visibility='hidden';
  if(internal) internal.style.display='none'; if(internalLabels) internalLabels.style.display='none';
  if(selected==='tissue') renderTissue(); else if(selected==='cellular') renderCellular(); else renderCell();
}

renderButtons(); render();
const observer = new MutationObserver(() => { if(selected !== 'macro') render(); });
const children=document.getElementById('spatial-children'); const node=document.getElementById('spatial-node');
if(children) observer.observe(children,{childList:true,subtree:true,characterData:true});
if(node) observer.observe(node,{childList:true,subtree:true,characterData:true});