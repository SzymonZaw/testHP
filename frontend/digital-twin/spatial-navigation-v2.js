const viewport=document.getElementById('twin-viewport');
const badge=document.getElementById('spatial-level-badge');
const node=document.getElementById('spatial-node');
const children=document.getElementById('spatial-children');
const breadcrumb=document.getElementById('spatial-breadcrumb');

if(viewport&&badge&&node&&children&&breadcrumb){
  const view=document.createElement('section');
  view.id='spatial-layer-view';
  view.className='spatial-layer-view';
  viewport.appendChild(view);

  const labels={
    'TISSUE FIELD':['Tissue section','Tissue navigation plane'],
    'CELLULAR FIELD':['Cellular field','Microscopy-field navigation plane'],
    'SINGLE CELL':['Single cell','Single-cell target view']
  };

  function level(){return String(badge.textContent||'MACRO').trim().toUpperCase();}
  function parent(){return [...breadcrumb.querySelectorAll('button')].slice(-2,-1)[0]||null;}

  function syncInspectorBoundary(){
    const macroRow=document.querySelector('.inspector .macro-row');
    if(!macroRow)return;
    const deep=level()!=='MACRO';
    macroRow.hidden=deep;
    macroRow.setAttribute('aria-hidden',deep?'true':'false');
  }

  function render(){
    const current=level();
    view.hidden=current==='MACRO';
    syncInspectorBoundary();
    if(current==='MACRO')return;
    view.replaceChildren();

    const header=document.createElement('div');
    header.className='layer-view-header';
    const titleWrap=document.createElement('div');
    const eyebrow=document.createElement('span'); eyebrow.textContent=labels[current]?.[0]||current;
    const title=document.createElement('strong'); title.textContent=node.querySelector('strong')?.textContent||'Spatial target';
    const subtitle=document.createElement('small'); subtitle.textContent=labels[current]?.[1]||'Spatial navigation view';
    titleWrap.append(eyebrow,title,subtitle);
    const back=document.createElement('button'); back.type='button'; back.className='layer-parent'; back.textContent='← Parent layer';
    back.disabled=!parent(); back.onclick=()=>parent()?.click();
    header.append(titleWrap,back); view.appendChild(header);

    const field=document.createElement('div');
    field.className=`layer-field layer-${current.toLowerCase().replaceAll(' ','-')}`;
    const targets=[...children.querySelectorAll('.spatial-target')];
    targets.forEach((target,i)=>{
      const item=document.createElement('button'); item.type='button'; item.className='layer-target';
      item.innerHTML=`<strong>${target.querySelector('strong')?.textContent||`Target ${i+1}`}</strong><span>${target.querySelector('span')?.textContent||'Navigation target'}</span>`;
      item.onclick=()=>target.click(); field.appendChild(item);
    });
    if(!targets.length){
      const terminal=document.createElement('div'); terminal.className='layer-terminal';
      terminal.innerHTML='<span>FINEST SPATIAL TARGET</span><strong>No deeper target</strong><small>Navigation only · no linked evidence</small>';
      field.appendChild(terminal);
    }
    view.appendChild(field);

    const note=document.createElement('p'); note.className='layer-view-note';
    note.textContent='Navigation view only. This visualization does not represent real tissue, microscopy, or cellular findings unless evidence is explicitly linked to this target.';
    view.appendChild(note);
  }

  const observer=new MutationObserver(render);
  observer.observe(badge,{childList:true,characterData:true,subtree:true});
  observer.observe(node,{childList:true,characterData:true,subtree:true});
  observer.observe(children,{childList:true,characterData:true,subtree:true});
  observer.observe(breadcrumb,{childList:true,subtree:true});
  render();
}