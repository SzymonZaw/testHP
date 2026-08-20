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
    'TISSUE FIELD':['Sekcja tkankowa','Płaszczyzna nawigacji tkankowej'],
    'CELLULAR FIELD':['Pole komórkowe','Płaszczyzna nawigacji mikroskopowej'],
    'SINGLE CELL':['Pojedyncza komórka','Widok celu pojedynczej komórki']
  };

  function level(){return String(badge.textContent||'MAKRO').trim().toUpperCase();}
  function parent(){return [...breadcrumb.querySelectorAll('button')].slice(-2,-1)[0]||null;}

  function syncInspectorBoundary(){
    const macroRow=document.querySelector('.inspector .macro-row');
    if(!macroRow)return;
    const deep=level()!=='MAKRO';
    macroRow.hidden=deep;
    macroRow.setAttribute('aria-hidden',deep?'true':'false');
  }

  function render(){
    const current=level();
    view.hidden=current==='MAKRO';
    syncInspectorBoundary();
    if(current==='MAKRO')return;
    view.replaceChildren();

    const header=document.createElement('div');
    header.className='layer-view-header';
    const titleWrap=document.createElement('div');
    const eyebrow=document.createElement('span'); eyebrow.textContent=labels[current]?.[0]||current;
    const title=document.createElement('strong'); title.textContent=node.querySelector('strong')?.textContent||'Cel przestrzenny';
    const subtitle=document.createElement('small'); subtitle.textContent=labels[current]?.[1]||'Widok nawigacji przestrzennej';
    titleWrap.append(eyebrow,title,subtitle);
    const back=document.createElement('button'); back.type='button'; back.className='layer-parent'; back.textContent='← Warstwa nadrzędna';
    back.disabled=!parent(); back.onclick=()=>parent()?.click();
    header.append(titleWrap,back); view.appendChild(header);

    const field=document.createElement('div');
    field.className=`layer-field layer-${current.toLowerCase().replaceAll(' ','-')}`;
    const targets=[...children.querySelectorAll('.spatial-target')];
    targets.forEach((target,i)=>{
      const item=document.createElement('button'); item.type='button'; item.className='layer-target';
      item.innerHTML=`<strong>${target.querySelector('strong')?.textContent||`Cel ${i+1}`}</strong><span>${target.querySelector('span')?.textContent||'Cel nawigacyjny'}</span>`;
      item.onclick=()=>target.click(); field.appendChild(item);
    });
    if(!targets.length){
      const terminal=document.createElement('div'); terminal.className='layer-terminal';
      terminal.innerHTML='<span>NAJDROBNIEJSZY CEL PRZESTRZENNY</span><strong>Brak głębszego celu</strong><small>Tylko nawigacja · brak powiązanych danych</small>';
      field.appendChild(terminal);
    }
    view.appendChild(field);

    const note=document.createElement('p'); note.className='layer-view-note';
    note.textContent='To jest wyłącznie widok nawigacji. Wizualizacja nie przedstawia rzeczywistych danych tkankowych, mikroskopowych ani komórkowych, chyba że dane są jawnie przypisane do tego celu.';
    view.appendChild(note);
  }

  const observer=new MutationObserver(render);
  observer.observe(badge,{childList:true,characterData:true,subtree:true});
  observer.observe(node,{childList:true,characterData:true,subtree:true});
  observer.observe(children,{childList:true,characterData:true,subtree:true});
  observer.observe(breadcrumb,{childList:true,subtree:true});
  render();
}