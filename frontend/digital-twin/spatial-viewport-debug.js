(() => {
  const boot = () => {
    const viewport = document.getElementById('twin-viewport');
    const canvas = document.getElementById('twin-canvas');
    if (!viewport || !canvas) return;

    const expected = [
      ['palm', 'Śródręcze'], ['little', 'Mały palec'], ['ring', 'Palec serdeczny'],
      ['middle', 'Palec środkowy'], ['index', 'Palec wskazujący'], ['thumb', 'Kciuk'], ['wrist', 'Nadgarstek']
    ];
    const lines = [];
    let started = Date.now();
    let lastProgress = 'debug initialized';
    let lastMutation = null;
    let lastWriter = null;
    let lastInteraction = null;
    let minimized = true;
    const originalMethods = [];

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) { host = document.createElement('section'); host.id = 'twin-viewport-debug-host'; document.body.appendChild(host); }
    host.setAttribute('aria-label', 'Twin Viewport debug');
    Object.assign(host.style, {position:'fixed',right:'16px',bottom:'16px',zIndex:'2147483647',width:'min(900px,calc(100vw - 32px))',maxWidth:'min(900px,calc(100vw - 32px))',pointerEvents:'auto'});

    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) { toggle=document.createElement('button'); toggle.id='twin-debug-toggle'; toggle.type='button'; host.appendChild(toggle); }
    Object.assign(toggle.style,{display:'block',padding:'8px 12px',borderRadius:'8px',border:'1px solid #4b746b',background:'#0b1514',color:'#9bd8c4',font:'800 11px ui-monospace,SFMono-Regular,Consolas,monospace',cursor:'pointer'});

    let panel = document.getElementById('twin-debug-panel');
    if (!panel) {
      panel=document.createElement('div'); panel.id='twin-debug-panel';
      panel.innerHTML='<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap"><strong>TWIN VIEWPORT · DEBUG</strong><div><button id="twin-debug-refresh" type="button">REFRESH</button><button id="twin-debug-clear" type="button">CLEAR</button><button id="twin-debug-close" type="button">MINIMIZE</button></div></div><pre id="twin-debug-runtime"></pre><pre id="twin-debug-state"></pre><pre id="twin-debug-navigation"></pre><pre id="twin-debug-source"></pre><pre id="twin-debug-renderer"></pre><pre id="twin-debug-interaction"></pre><pre id="twin-debug-log"></pre>';
      host.appendChild(panel);
    }
    Object.assign(panel.style,{display:'none',marginTop:'6px',width:'100%',maxHeight:'760px',overflow:'auto',padding:'12px',boxSizing:'border-box',borderRadius:'10px',background:'rgba(5,12,13,.98)',border:'1px solid #4b746b',boxShadow:'0 12px 35px rgba(0,0,0,.55)',color:'#dcece6',font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace'});

    const runtime=document.getElementById('twin-debug-runtime');
    const state=document.getElementById('twin-debug-state');
    const navigation=document.getElementById('twin-debug-navigation');
    const source=document.getElementById('twin-debug-source');
    const renderer=document.getElementById('twin-debug-renderer');
    const interaction=document.getElementById('twin-debug-interaction');
    const log=document.getElementById('twin-debug-log');
    if (!runtime || !state || !navigation || !source || !renderer || !interaction || !log) return;

    const now=()=>new Date().toLocaleTimeString();
    const writeLog=(message,stack)=>{
      lines.push(`[${now()}] ${message}${stack?`\n  stack: ${String(stack).replace(/\n/g,'\n         ')}`:''}`);
      while(lines.length>220) lines.shift();
      log.textContent=lines.join('\n'); log.scrollTop=log.scrollHeight;
    };
    const event=(message,stack)=>{lastProgress=message;writeLog(message,stack);if(!minimized)render();};
    const childrenNode=()=>document.getElementById('spatial-children');
    const childElements=()=>[...document.querySelectorAll('#spatial-children .spatial-target')];
    const childNames=()=>childElements().map(x=>x.querySelector('strong')?.textContent?.trim()||x.textContent.trim().replace(/\s+/g,' '));
    const spatial=()=>{
      const manager=window.spatialViewportManager;
      const node=document.getElementById('spatial-node');
      const badge=document.getElementById('spatial-level-badge');
      const crumbs=[...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean);
      const children=childNames();
      const target=node?.querySelector('strong')?.textContent?.trim()||'?';
      const id=window.spatialEvidenceTarget||manager?.activeKey||'?';
      return {manager:!!manager,target,id,level:badge?.textContent?.trim()||'?',path:crumbs.join(' > ')||'(root)',children,nodeText:node?.textContent?.trim().replace(/\s+/g,' ')||'(none)',active:manager?.active?.constructor?.name||'none',activeKey:manager?.activeKey||'none'};
    };
    const isHandRoot=s=>{const t=String(s.target||'').toLowerCase(),id=String(s.id||'').toLowerCase();return (t==='dłoń'||t==='hand'||id==='hand')&&s.path.split(' > ').length===1;};
    const clickable=()=>{
      const list=window.spatialViewportManager?.active?.clickable;
      return Array.isArray(list)?list.map(x=>({name:x?.name||'',spatialTarget:x?.userData?.spatialTarget||'',type:x?.type||''})):[];
    };
    const handFallback=s=>isHandRoot(s)&&s.children.length===1&&/regional field/i.test(s.children[0]);
    const stack=()=>{try{throw new Error('diagnostic stack');}catch(e){return e.stack?.split('\n').slice(2,8).join('\n')||'';}};

    const patchWriter=(proto,name)=>{
      const original=proto[name]; if(typeof original!=='function') return;
      const wrapped=function(...args){
        const target=this;
        if(target===childrenNode() || target?.closest?.('#spatial-children')) {
          const before=childNames().join(' | ')||'(none)';
          lastWriter={method:name,before,stack:stack(),time:now()};
          event(`DOM WRITE | spatial-children | method=${name} | before=${before}`,lastWriter.stack);
        }
        return original.apply(this,args);
      };
      try{proto[name]=wrapped;originalMethods.push(()=>{proto[name]=original;});}catch(e){event(`DEBUG PATCH FAILED | ${name} | ${e.message}`);}
    };
    patchWriter(Node.prototype,'appendChild');
    patchWriter(Node.prototype,'replaceChild');
    patchWriter(Node.prototype,'removeChild');
    patchWriter(Element.prototype,'insertAdjacentHTML');
    patchWriter(Element.prototype,'replaceChildren');

    const originalInner=Object.getOwnPropertyDescriptor(Element.prototype,'innerHTML');
    if(originalInner?.set){
      try{
        Object.defineProperty(Element.prototype,'innerHTML',{...originalInner,set(value){
          if(this===childrenNode() || this?.closest?.('#spatial-children')){
            const before=childNames().join(' | ')||'(none)';
            lastWriter={method:'innerHTML',before,value:String(value).slice(0,1000),stack:stack(),time:now()};
            event(`DOM WRITE | spatial-children | method=innerHTML | before=${before} | value=${String(value).slice(0,160)}`,lastWriter.stack);
          }
          return originalInner.set.call(this,value);
        }});
        originalMethods.push(()=>Object.defineProperty(Element.prototype,'innerHTML',originalInner));
      }catch(e){event(`DEBUG PATCH FAILED | innerHTML | ${e.message}`);}
    }

    const render=()=>{
      const s=spatial(), list=clickable(), names=list.map(x=>x.name||x.spatialTarget||'(unnamed)');
      const root=childrenNode();
      const rootHTML=root?.innerHTML?.slice(0,1800)||'(missing)';
      const regionIds=childElements().map(x=>({label:x.querySelector('strong')?.textContent?.trim()||'',dataset:{...x.dataset},html:x.outerHTML.slice(0,500)}));
      const expectedLabels=expected.map(x=>x[1]);
      const managerState=window.spatialViewportManager?.active;
      const macroClickable=list.filter(x=>expected.some(e=>e[0]===x.name||e[1]===x.name||e[0]===x.spatialTarget||e[1]===x.spatialTarget));
      runtime.textContent=['RUNTIME',`status:       ${window.__testhpTwinReady?'READY':Date.now()-started>10000?'INIT TIMEOUT':'INITIALIZING'}`,`init age:     ${Date.now()-started} ms`,`manager:      ${window.spatialViewportManager?'present':'MISSING'}`,`ready flag:   ${window.__testhpTwinReady?'YES':'NO'}`,`last progress:${lastProgress}`].join('\n');
      state.textContent=['','SPATIAL STATE',`level:        ${s.level}`,`target:       ${s.target}`,`spatial_id:   ${s.id}`,`path:         ${s.path}`,`children:     ${s.children.join(' | ')||'(none)'}`,`active view:  ${s.active}`,`active key:   ${s.activeKey}`,`node:         ${s.nodeText}`,`children DOM: ${!!root}`,`children HTML:${rootHTML}`].join('\n');
      navigation.textContent=['','NAVIGATION DIAGNOSTICS',`root is Hand:       ${isHandRoot(s)?'YES':'NO'}`,`root fallback:     ${handFallback(s)?'YES — Regional field is present at macro root':'NO'}`,`expected count:     7`,`actual count:       ${s.children.length}`,`expected children:  ${expectedLabels.join(' | ')}`,`actual children:    ${s.children.join(' | ')||'(none)'}`,`order correct:      ${s.children.join('|')===expectedLabels.join('|')?'YES':'NO'}`,`macro targets found: ${macroClickable.length}/7`,`manager active key: ${managerState?.activeKey||s.activeKey||'none'}`,`manager target id:   ${managerState?.target?.id||managerState?.spatialId||'unknown'}`].join('\n');
      source.textContent=['','SOURCE / WRITER DIAGNOSTICS',`last DOM writer:    ${lastWriter?.method||'(none captured)'}`,`writer time:        ${lastWriter?.time||'(none)'}`,`writer before:      ${lastWriter?.before||'(none)'}`,`writer stack:       ${lastWriter?.stack||'(none captured yet)'}`,`writer value:       ${lastWriter?.value||'(not innerHTML)'}`,`child metadata:     ${JSON.stringify(regionIds)}`].join('\n');
      renderer.textContent=['','RENDERER / 3D DIAGNOSTICS',`renderer:      ${s.active}`,`active key:    ${s.activeKey}`,`clickable:     ${list.length}`,`clickable names:${names.join(' | ')||'(none)'}`,`hand macro 3D: ${macroClickable.length}/7`,`Regional field 3D: ${list.some(x=>/regional field/i.test(x.name)||/regional field/i.test(x.spatialTarget))?'YES':'NO'}`,`scene:         ${managerState?.scene?.children?.length??'unknown'}`,`camera:        ${managerState?.camera?'present':'missing'}`].join('\n');
      interaction.textContent=['','LAST INTERACTION',lastInteraction?JSON.stringify(lastInteraction,null,2):'No navigation interaction captured yet.'].join('\n');
    };

    const observer=new MutationObserver(records=>{
      const relevant=records.some(r=>r.target===childrenNode()||r.target?.closest?.('#spatial-children'));
      if(relevant){
        const after=childNames();
        lastMutation={time:now(),type:records.map(r=>r.type).join(','),children:after};
        event(`DOM MUTATION | spatial-children | children=${after.join(' | ')||'(none)'}`);
        if(handFallback(spatial())) event('ROOT FALLBACK DETECTED | Regional field came back after a DOM mutation');
      }
      if(!minimized)render();
    });
    observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class','data-spatial-target','data-spatial-id']});

    const capture=(type,e)=>event(`${type} | ${JSON.stringify(e.detail||{})}`);
    window.addEventListener('error',e=>event(`WINDOW ERROR | ${e.message||'unknown'} | ${e.filename||''}:${e.lineno||''}`));
    window.addEventListener('unhandledrejection',e=>event(`UNHANDLED PROMISE | ${e.reason?.stack||e.reason||'unknown'}`));
    window.addEventListener('testhp:twin-ready',e=>{window.__testhpTwinReady=true;capture('TWIN READY',e);});
    window.addEventListener('testhp:twin-error',e=>capture('TWIN ERROR',e));
    window.addEventListener('testhp:twin-progress',e=>capture('INIT',e));
    window.addEventListener('testhp:viewport-rendered',e=>capture('VIEW RENDERED',e));
    window.addEventListener('testhp:spatial-layer-changed',e=>capture('SPATIAL LAYER',e));
    canvas.addEventListener('click',e=>{lastInteraction={type:'canvas click',x:e.clientX,y:e.clientY,time:now(),target:spatial().target};event(`CANVAS CLICK | x=${Math.round(e.clientX)} y=${Math.round(e.clientY)} | target=${spatial().target}`);},{passive:true});

    const setMinimized=v=>{minimized=v;panel.style.display=minimized?'none':'block';toggle.textContent=minimized?'TWIN VIEWPORT DEBUG · ROZWIŃ':'TWIN VIEWPORT DEBUG · ZWIŃ';if(!minimized)render();};
    toggle.onclick=()=>setMinimized(!minimized);
    document.getElementById('twin-debug-close')?.addEventListener('click',()=>setMinimized(true));
    document.getElementById('twin-debug-refresh')?.addEventListener('click',()=>{event('manual refresh');render();});
    document.getElementById('twin-debug-clear')?.addEventListener('click',()=>{lines.length=0;event('log cleared');});
    setInterval(()=>{if(!minimized)render();},500);
    event('DEBUG READY | writer hooks + mutation observer active');
    render();
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();