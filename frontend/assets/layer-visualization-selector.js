(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const wrap = document.createElement('section');
  wrap.id = 'independent-layer-visualization';
  Object.assign(wrap.style, {position:'absolute', inset:'0', zIndex:'100', pointerEvents:'none', fontFamily:'system-ui,sans-serif'});

  const switcher = document.createElement('div');
  Object.assign(switcher.style, {position:'absolute',left:'16px',right:'16px',bottom:'16px',zIndex:'110',display:'flex',flexWrap:'wrap',gap:'7px',alignItems:'center',padding:'8px',borderRadius:'14px',background:'#0d1918e8',border:'1px solid #36544e',backdropFilter:'blur(8px)',pointerEvents:'auto'});
  const title=document.createElement('span'); title.textContent='VISUALIZATION LAYER';
  Object.assign(title.style,{fontSize:'10px',fontWeight:'800',letterSpacing:'.12em',opacity:'.7',marginRight:'3px'}); switcher.appendChild(title);

  const stage=document.createElement('div');
  Object.assign(stage.style,{position:'absolute',inset:'0',display:'none',pointerEvents:'auto',overflow:'hidden',background:'radial-gradient(circle at 50% 45%,#18342f 0,#0b1518 62%)'});
  wrap.append(stage,switcher); viewport.appendChild(wrap);

  const keys=['macro','tissue','cellular','cell'];
  const names=['Macro anatomy','Tissue field','Cellular field','Single cell'];
  let selected='macro';

  function target(){return document.querySelector('#spatial-node strong')?.textContent?.trim()||'Selected target'}
  function targets(){return [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(e=>e.textContent.trim()).filter(Boolean)}
  function buttons(){[...switcher.querySelectorAll('button')].forEach(b=>b.remove());keys.forEach((k,i)=>{const b=document.createElement('button');b.type='button';b.textContent=names[i];const active=k===selected;Object.assign(b.style,{padding:'8px 11px',borderRadius:'9px',border:'1px solid #36544e',background:active?'#23463e':'#101b1a',color:'#dcece6',font:'600 11px system-ui,sans-serif',cursor:'pointer'});b.onclick=()=>{selected=k;render()};switcher.appendChild(b)})}
  function text(s,style){const e=document.createElement('div');e.textContent=s;Object.assign(e.style,style);stage.appendChild(e)}
  function render(){stage.replaceChildren();buttons();const base=document.getElementById('twin-canvas');const controls=document.querySelector('.viewer-controls');const hint=document.querySelector('.viewer-hint');const loading=document.getElementById('viewer-loading');const internal=document.getElementById('spatial-layer-canvas');if(selected==='macro'){stage.style.display='none';if(base){base.style.display='block';base.style.visibility='visible'}if(controls)controls.style.visibility='visible';if(hint)hint.style.visibility='visible';if(loading)loading.style.visibility='visible';if(internal)internal.style.display='none';return}stage.style.display='block';if(base){base.style.display='none';base.style.visibility='hidden'}if(controls)controls.style.visibility='hidden';if(hint)hint.style.visibility='hidden';if(loading)loading.style.visibility='hidden';if(internal)internal.style.display='none';
    if(selected==='tissue'){text('TISSUE SECTION',{position:'absolute',left:'18px',top:'18px',fontSize:'11px',fontWeight:'800',letterSpacing:'.12em',color:'#9bd8c4'});const p=document.createElement('div');Object.assign(p.style,{position:'absolute',left:'12%',right:'12%',top:'19%',bottom:'22%',border:'1px solid #78bca866',borderRadius:'16px',background:'linear-gradient(145deg,#294d45,#132824)',transform:'perspective(700px) rotateX(9deg) rotateY(-8deg)',boxShadow:'0 25px 60px #0008'});stage.appendChild(p);(targets().slice(0,3).length?targets().slice(0,3):['Tissue field A','Tissue field B','Tissue field C']).forEach((n,i)=>text(n,{position:'absolute',left:`${18+i*28}%`,top:`${43+(i%2)*17}%`,padding:'9px 12px',borderRadius:'10px',background:'#10221ee8',border:'1px solid #78bca866',color:'#dcece6',fontSize:'12px',fontWeight:'700'}))}
    if(selected==='cellular'){text('CELLULAR FIELD',{position:'absolute',left:'18px',top:'18px',fontSize:'11px',fontWeight:'800',letterSpacing:'.12em',color:'#9bd8c4'});const grid=document.createElement('div');Object.assign(grid.style,{position:'absolute',inset:'18% 10% 22%',background:'radial-gradient(circle,#244b43 1px,transparent 1px)',backgroundSize:'24px 24px',border:'1px solid #36544e',borderRadius:'14px'});stage.appendChild(grid);for(let i=0;i<16;i++){const c=document.createElement('div');Object.assign(c.style,{position:'absolute',left:`${8+(i*37)%84}%`,top:`${8+(i*61)%78}%`,width:'40px',height:'40px',borderRadius:'50%',background:'radial-gradient(circle at 35% 30%,#8bc7b0,#2f6759 65%,#102a24)',border:'1px solid #9bd8c488'});grid.appendChild(c)}}
    if(selected==='cell'){text('SINGLE CELL',{position:'absolute',left:'18px',top:'18px',fontSize:'11px',fontWeight:'800',letterSpacing:'.12em',color:'#9bd8c4'});text(target(),{position:'absolute',left:'50%',top:'86%',transform:'translateX(-50%)',fontSize:'12px',fontWeight:'700',color:'#dcece6'});const c=document.createElement('div');Object.assign(c.style,{position:'absolute',left:'50%',top:'48%',width:'190px',height:'190px',transform:'translate(-50%,-50%) rotateX(8deg) rotateY(-12deg)',borderRadius:'50%',background:'radial-gradient(circle at 35% 28%,#b8e4d4,#69ad99 35%,#315f53 70%,#122a24)',border:'2px solid #9bd8c4aa',boxShadow:'0 0 45px #5fae9855'});stage.appendChild(c);const n=document.createElement('div');Object.assign(n.style,{position:'absolute',left:'50%',top:'50%',width:'65px',height:'65px',transform:'translate(-50%,-50%)',borderRadius:'50%',background:'#315e51',border:'2px solid #9bd8c477'});c.appendChild(n)}}
  render();
  const obs=new MutationObserver(render);['spatial-node','spatial-children','spatial-level-badge'].forEach(id=>{const e=document.getElementById(id);if(e)obs.observe(e,{childList:true,subtree:true,characterData:true})});
})();
