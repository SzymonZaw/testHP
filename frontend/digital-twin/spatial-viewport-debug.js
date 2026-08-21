(() => {
  const boot = () => {
    const viewport = document.getElementById('twin-viewport');
    const canvas = document.getElementById('twin-canvas');
    if (!viewport || !canvas) return;

    const expectedHandChildren = [
      { id:'palm', label:'Śródręcze' },
      { id:'little', label:'Mały palec' },
      { id:'ring', label:'Palec serdeczny' },
      { id:'middle', label:'Palec środkowy' },
      { id:'index', label:'Palec wskazujący' },
      { id:'thumb', label:'Kciuk' },
      { id:'wrist', label:'Nadgarstek' }
    ];

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) host = document.createElement('section');
    host.id = 'twin-viewport-debug-host';
    host.setAttribute('aria-label', 'Twin Viewport debug');
    Object.assign(host.style, {position:'fixed',right:'16px',bottom:'16px',zIndex:'2147483647',width:'min(860px,calc(100vw - 32px))',maxWidth:'min(860px,calc(100vw - 32px))',pointerEvents:'auto',display:'block'});
    if (host.parentElement !== document.body) document.body.appendChild(host);

    let panel = document.getElementById('twin-debug-panel');
    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) { toggle=document.createElement('button'); toggle.id='twin-debug-toggle'; toggle.type='button'; toggle.textContent='TWIN VIEWPORT DEBUG · ROZWIŃ'; host.appendChild(toggle); }
    Object.assign(toggle.style,{display:'block',padding:'8px 12px',borderRadius:'8px',border:'1px solid #4b746b',background:'#0b1514',color:'#9bd8c4',font:'800 11px ui-monospace,SFMono-Regular,Consolas,monospace',cursor:'pointer',boxShadow:'0 8px 24px rgba(0,0,0,.45)'});

    if (!panel) {
      panel=document.createElement('div'); panel.id='twin-debug-panel';
      panel.innerHTML='<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap"><strong>TWIN VIEWPORT · DEBUG</strong><div><button id="twin-debug-refresh" type="button">REFRESH</button><button id="twin-debug-clear" type="button">CLEAR</button><button id="twin-debug-close" type="button">MINIMIZE</button></div></div><pre id="twin-debug-runtime"></pre><pre id="twin-debug-state"></pre><pre id="twin-debug-navigation"></pre><pre id="twin-debug-renderer"></pre><pre id="twin-debug-interaction"></pre><pre id="twin-debug-log"></pre>';
      host.appendChild(panel);
    }
    Object.assign(panel.style,{display:'none',marginTop:'6px',width:'100%',maxHeight:'680px',overflow:'auto',padding:'12px',boxSizing:'border-box',borderRadius:'10px',background:'rgba(5,12,13,.98)',border:'1px solid #4b746b',boxShadow:'0 12px 35px rgba(0,0,0,.55)',color:'#dcece6',font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace'});

    const refresh=document.getElementById('twin-debug-refresh');
    const clear=document.getElementById('twin-debug-clear');
    const close=document.getElementById('twin-debug-close');
    const runtime=document.getElementById('twin-debug-runtime');
    const state=document.getElementById('twin-debug-state');
    const navigation=document.getElementById('twin-debug-navigation');
    const renderer=document.getElementById('twin-debug-renderer');
    const interaction=document.getElementById('twin-debug-interaction');
    const log=document.getElementById('twin-debug-log');
    if (!runtime || !state || !navigation || !renderer || !interaction || !log) return;

    const lines=[];
    let initStarted=Date.now();
    let lastProgress='debug panel initialized';
    let minimized=true;
    let lastInteraction=null;
    let lastRepairSignature='';

    const now=()=>new Date().toLocaleTimeString();
    const writeLog=message=>{lines.push(`[${now()}] ${message}`);while(lines.length>300)lines.shift();log.textContent=lines.join('\n');log.scrollTop=log.scrollHeight;};
    const event=message=>{lastProgress=message;writeLog(message);if(!minimized)render();};

    const spatial=()=>{
      const manager=window.spatialViewportManager;
      const badge=document.getElementById('spatial-level-badge');
      const node=document.getElementById('spatial-node');
      const crumbs=[...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean);
      const children=[...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x=>x.textContent.trim()).filter(Boolean);
      const level=badge?.textContent?.trim()||'?';
      const target=node?.querySelector('strong')?.textContent?.trim()||'?';
      const targetId=window.spatialEvidenceTarget||manager?.activeKey||'?';
      return {manager:!!manager,level,target,targetId,path:crumbs.join(' > ')||'(root)',children,renderer:manager?.active?.constructor?.name||'none',key:manager?.activeKey||'none',nodeText:node?.textContent?.trim().replace(/\s+/g,' ')||'(none)'};
    };

    const clickableNames=()=>{
      const clickable=window.spatialViewportManager?.active?.clickable;
      return Array.isArray(clickable)?clickable.map(x=>x?.name||x?.userData?.spatialTarget||'(unnamed)'):[];
    };
    const isHandRoot=s=>{const target=String(s.target||'').toLowerCase();const id=String(s.targetId||'').toLowerCase();return(target==='dłoń'||target==='hand'||id==='hand')&&s.path.split(' > ').length===1;};
    const badRootFallback=s=>isHandRoot(s)&&s.children.length===1&&/regional field/i.test(s.children[0]);

    const projectMeshToCanvas=(mesh,camera)=>{
      if (!mesh?.position || !camera?.matrixWorldInverse?.elements || !camera?.projectionMatrix?.elements) return null;
      const root=mesh.parent;
      const local=mesh.position;
      const worldMatrix=root?.matrixWorld?.elements;
      let x=local.x,y=local.y,z=local.z;
      if (worldMatrix) {
        const e=worldMatrix;
        const w=e[3]*x+e[7]*y+e[11]*z+e[15];
        const nx=e[0]*x+e[4]*y+e[8]*z+e[12];
        const ny=e[1]*x+e[5]*y+e[9]*z+e[13];
        const nz=e[2]*x+e[6]*y+e[10]*z+e[14];
        x=w?nx/w:nx;y=w?ny/w:ny;z=w?nz/w:nz;
      }
      const view=camera.matrixWorldInverse.elements;
      const vx=view[0]*x+view[4]*y+view[8]*z+view[12];
      const vy=view[1]*x+view[5]*y+view[9]*z+view[13];
      const vz=view[2]*x+view[6]*y+view[10]*z+view[14];
      const vw=view[3]*x+view[7]*y+view[11]*z+view[15];
      const p=camera.projectionMatrix.elements;
      const cx=p[0]*vx+p[4]*vy+p[8]*vz+p[12]*vw;
      const cy=p[1]*vx+p[5]*vy+p[9]*vz+p[13]*vw;
      const cw=p[3]*vx+p[7]*vy+p[11]*vz+p[15]*vw;
      if (!cw) return null;
      const ndcX=cx/cw,ndcY=cy/cw;
      const rect=canvas.getBoundingClientRect();
      return {clientX:rect.left+((ndcX+1)/2)*rect.width,clientY:rect.top+((1-ndcY)/2)*rect.height};
    };

    const dispatchCanvasNavigation=item=>{
      const active=window.spatialViewportManager?.active;
      const mesh=Array.isArray(active?.clickable)?active.clickable.find(x=>x?.name===item.id):null;
      const camera=active?.camera;
      const point=projectMeshToCanvas(mesh,camera);
      if(!mesh||!camera||!point){event(`HAND NAV ERROR | ${item.label} | mesh=${!!mesh} camera=${!!camera} projection=${!!point}`);return false;}
      ['pointerdown','pointerup','click'].forEach(type=>canvas.dispatchEvent(new PointerEvent(type,{bubbles:true,cancelable:true,clientX:point.clientX,clientY:point.clientY,pointerId:1,pointerType:'mouse',buttons:0})));
      lastInteraction={type:'navigator button',source:'navigation repair bridge',time:now(),coordinates:`${Math.round(point.clientX)},${Math.round(point.clientY)}`,before:`${spatial().target} / ${spatial().targetId}`,after:'pending',hit:mesh.name,navigation:'synthetic canvas hit'};
      event(`HAND NAV | ${item.label} -> mesh=${mesh.name} | canvas=${Math.round(point.clientX)},${Math.round(point.clientY)}`);
      setTimeout(()=>{const after=spatial();if(lastInteraction)lastInteraction.after=`${after.target} / ${after.targetId}`;event(`HAND NAV RESULT | ${item.label} -> ${after.target} | id=${after.targetId}`);},150);
      return true;
    };

    const repairHandRoot=()=>{
      const s=spatial();
      if(!isHandRoot(s)) return false;
      const container=document.getElementById('spatial-children');
      if(!container) return false;
      const existing=[...container.querySelectorAll('.spatial-target strong')].map(x=>x.textContent.trim());
      const expected=expectedHandChildren.map(x=>x.label);
      const needsRepair=existing.length!==expected.length||existing.some(x=>/regional field/i.test(x))||existing.join('|')!==expected.join('|');
      const signature=`${s.target}|${existing.join('|')}`;
      if(!needsRepair||signature===lastRepairSignature) return false;
      lastRepairSignature=signature;
      writeLog(`NAVIGATION ROOT BUG | target=${s.target} | current=${existing.join(' | ')||'(none)'} | expected=7 hand macro regions`);
      container.replaceChildren();
      expectedHandChildren.forEach(item=>{
        const button=document.createElement('button');button.type='button';button.className='spatial-target';button.dataset.repairedRootTarget=item.id;
        const title=document.createElement('strong');title.textContent=item.label;
        const meta=document.createElement('span');meta.textContent='Anatomia makro';
        button.append(title,meta);button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();dispatchCanvasNavigation(item);});container.appendChild(button);
      });
      writeLog(`NAVIGATION ROOT REPAIRED | Dłoń -> ${expected.join(' | ')}`);
      return true;
    };

    const runtimeInfo=()=>{
      const rect=viewport.getBoundingClientRect(),cr=canvas.getBoundingClientRect();
      let graphics='MISSING';try{graphics=canvas.getContext('webgl2')?'WebGL2':canvas.getContext('webgl')?'WebGL':'NONE';}catch(e){graphics=`ERROR: ${e.message}`;}
      return {viewport:`${Math.round(rect.width)}×${Math.round(rect.height)}`,canvas:`${Math.round(cr.width)}×${Math.round(cr.height)} (${canvas.width}×${canvas.height})`,display:getComputedStyle(canvas).display,visibility:getComputedStyle(canvas).visibility,opacity:getComputedStyle(canvas).opacity,pointerEvents:getComputedStyle(canvas).pointerEvents,graphics,manager:window.spatialViewportManager?'present':'MISSING',ready:window.__testhpTwinReady?'YES':'NO',initAge:`${Date.now()-initStarted} ms`,lastProgress};
    };

    const render=()=>{
      repairHandRoot();
      const v=runtimeInfo(),s=spatial(),names=clickableNames(),rootFallback=badRootFallback(s);
      runtime.textContent=['RUNTIME',`status:       ${v.ready==='YES'?'READY':Date.now()-initStarted>10000?'INIT TIMEOUT':'INITIALIZING'}`,`viewport:     ${v.viewport}`,`canvas:       ${v.canvas}`,`display:      ${v.display}`,`visibility:   ${v.visibility}`,`opacity:      ${v.opacity}`,`pointerEvents:${v.pointerEvents}`,`graphics:     ${v.graphics}`,`manager:      ${v.manager}`,`init age:     ${v.initAge}`,`ready:        ${v.ready}`,`last progress:${v.lastProgress}`].join('\n');
      state.textContent=['','SPATIAL STATE',`level:        ${s.level}`,`target:       ${s.target}`,`spatial_id:   ${s.targetId}`,`path:         ${s.path}`,`children:     ${s.children.join(' | ')||'(none)'}`,`renderer:     ${s.renderer}`,`active_key:   ${s.key}`,`node:         ${s.nodeText}`,`layer chain:  ${s.path} > ${s.target}`,`next layer:   ${s.children.join(' | ')||'(none)'}`].join('\n');
      navigation.textContent=['','NAVIGATION DIAGNOSTICS',`root target:       ${isHandRoot(s)?'YES':'NO'}`,`expected children: ${expectedHandChildren.length}`,`actual children:   ${s.children.length}`,`fallback present:  ${rootFallback?'YES — Regional field is incorrectly generated for Hand':'NO'}`,`current children:  ${s.children.join(' | ')||'(none)'}`,`expected order:    ${expectedHandChildren.map(x=>x.label).join(' | ')}`,`repair bridge:     ${isHandRoot(s)?'ACTIVE':'idle'}`,`repair source:     DOM fallback correction`,`deeper hierarchy:  ${isHandRoot(s)?'preserved by canonical 3D navigation after selecting a macro region':'canonical navigator'}`].join('\n');
      renderer.textContent=['','RENDERER',`manager:      ${v.manager}`,`active:       ${s.renderer}`,`active key:   ${s.key}`,`clickable:    ${names.length}`,`clickable set:${names.join(' | ')||'(none)'}`,`canvas:       ${v.graphics}`,`canonical:    YES — no second renderer`].join('\n');
      interaction.textContent=['','LAST INTERACTION',lastInteraction?[`type:         ${lastInteraction.type}`,`source:       ${lastInteraction.source}`,`time:         ${lastInteraction.time}`,`coordinates:  ${lastInteraction.coordinates}`,`before:       ${lastInteraction.before}`,`after:        ${lastInteraction.after}`,`hit:           ${lastInteraction.hit}`,`navigation:   ${lastInteraction.navigation}`].join('\n'):'No navigation interaction captured yet.'].join('\n');
    };

    const setMinimized=value=>{minimized=value;panel.style.display=minimized?'none':'block';toggle.textContent=minimized?'TWIN VIEWPORT DEBUG · ROZWIŃ':'TWIN VIEWPORT DEBUG · ZWIŃ';if(!minimized)render();};
    toggle.onclick=()=>setMinimized(!minimized);if(close)close.onclick=()=>setMinimized(true);if(refresh)refresh.onclick=()=>{event('manual refresh');render();};if(clear)clear.onclick=()=>{lines.length=0;event('log cleared');};
    window.addEventListener('error',e=>event(`WINDOW ERROR | ${e.message||'unknown'} | ${e.filename||''}:${e.lineno||''}`));
    window.addEventListener('unhandledrejection',e=>event(`UNHANDLED PROMISE | ${e.reason?.stack||e.reason||'unknown'}`));
    window.addEventListener('testhp:twin-ready',e=>{window.__testhpTwinReady=true;event(`TWIN READY | ${JSON.stringify(e.detail||{})}`);});
    window.addEventListener('testhp:twin-error',e=>event(`TWIN ERROR | ${e.detail?.error?.stack||e.detail?.error||'unknown'}`));
    window.addEventListener('testhp:twin-progress',e=>event(`INIT | ${e.detail?.step||e.detail?.message||'progress'}`));
    window.addEventListener('testhp:viewport-rendered',e=>event(`VIEW RENDERED | ${JSON.stringify(e.detail||{})}`));
    window.addEventListener('testhp:spatial-layer-changed',e=>event(`SPATIAL LAYER | ${JSON.stringify(e.detail||{})}`));
    window.addEventListener('resize',()=>event('viewport/window resize observed'),{passive:true});

    const observer=new MutationObserver(()=>{repairHandRoot();if(!minimized)render();});
    ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true,characterData:true});});
    window.__testhpTwinDebug={refresh:render,log:writeLog,viewport,canvas,repairHandRoot};
    render();
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
