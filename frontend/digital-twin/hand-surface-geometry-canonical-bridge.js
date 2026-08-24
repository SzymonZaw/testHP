(() => {
  const DEFAULT = Object.freeze({palmLength:1,palmWidth:1,fingerSpread:1,thumbAngle:1,taper:1,thickness:1});
  const STORAGE = 'digitalTwinHandSurface.v1';
  let base = new Map();
  let lastSignature = '';
  let installed = false;

  const manager = () => window.spatialViewportManager;
  const active = () => manager()?.active;
  const root = () => active()?.root || active()?.scene?.getObjectByName?.('macro-hand-root') || null;
  const mesh = id => root()?.getObjectByName?.(id) || active()?.scene?.getObjectByName?.(id) || null;

  function captureBase() {
    const ids = ['palm','index','middle','ring','little','thumb'];
    let count = 0;
    for (const id of ids) {
      const m = mesh(id);
      if (!m) continue;
      if (!base.has(m)) base.set(m, {
        position: {x:m.position.x,y:m.position.y,z:m.position.z},
        scale: {x:m.scale.x,y:m.scale.y,z:m.scale.z},
        rotation: {x:m.rotation.x,y:m.rotation.y,z:m.rotation.z}
      });
      count++;
    }
    return count;
  }

  function readState() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      return {...DEFAULT,...(raw.geometry || {})};
    } catch { return {...DEFAULT}; }
  }

  function saveState(geometry) {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      raw.geometry = {...DEFAULT,...geometry};
      raw.geometryCanonicalApplied = true;
      raw.geometryCanonicalAppliedAt = new Date().toISOString();
      localStorage.setItem(STORAGE, JSON.stringify(raw));
    } catch {}
  }

  function apply(geometry = readState(), reason = 'api') {
    const g = {...DEFAULT,...geometry};
    const count = captureBase();
    if (!count) return {ok:false,reason:'canonical meshes unavailable'};

    const applyMesh = (id, fn) => {
      const m = mesh(id), b = m && base.get(m);
      if (m && b) fn(m,b);
    };

    applyMesh('palm',(m,b)=>{
      m.position.set(b.position.x,b.position.y,b.position.z);
      m.scale.set(g.palmWidth*b.scale.x,g.palmLength*b.scale.y,g.thickness*b.scale.z);
    });

    ['index','middle','ring','little'].forEach(id => applyMesh(id,(m,b)=>{
      m.position.set(b.position.x*g.fingerSpread,b.position.y,b.position.z);
      m.scale.set(g.thickness*b.scale.x,b.scale.y,g.taper*b.scale.z);
      m.rotation.set(b.rotation.x,b.rotation.y,b.rotation.z);
    }));

    applyMesh('thumb',(m,b)=>{
      m.position.set(b.position.x,b.position.y,b.position.z);
      m.scale.set(g.thickness*b.scale.x,b.scale.y,b.scale.z);
      m.rotation.set(b.rotation.x,b.rotation.y,-.82*g.thumbAngle);
    });

    const render = active()?.renderer;
    const scene = active()?.scene;
    const camera = active()?.camera;
    if (render && scene && camera) render.render(scene,camera);
    lastSignature = JSON.stringify(g);
    window.dispatchEvent(new CustomEvent('testhp:geometry-canonical-applied',{detail:{geometry:g,reason,meshCount:count}}));
    return {ok:true,meshCount:count,geometry:g};
  }

  function reset() {
    const result = apply(DEFAULT,'reset');
    saveState(DEFAULT);
    return result;
  }

  window.digitalTwinGeometry = {
    version:'canonical-geometry-1',
    getState:readState,
    setParameter(name,value){ const next={...readState(),[name]:Number(value)}; saveState(next); return apply(next,'set-parameter'); },
    setState(next){ const merged={...DEFAULT,...next}; saveState(merged); return apply(merged,'set-state'); },
    reset,
    apply,
    inspect(){
      const result={};
      ['palm','index','middle','ring','little','thumb'].forEach(id=>{const m=mesh(id);if(m)result[id]={position:m.position.toArray(),scale:m.scale.toArray(),rotation:[m.rotation.x,m.rotation.y,m.rotation.z]};});
      return result;
    }
  };

  function ensureLayout() {
    const studio = document.getElementById('hand-surface-studio');
    const twin = document.querySelector('.twin-panel');
    if (!studio || !twin || studio.parentElement === twin) return;
    twin.appendChild(studio);
    studio.classList.add('hss-canonical-geometry-panel');
    if (!document.getElementById('hss-canonical-geometry-css')) {
      const style=document.createElement('style');
      style.id='hss-canonical-geometry-css';
      style.textContent=`
        .twin-panel{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,390px);gap:16px;align-items:start}
        .twin-panel>.twin-viewport{grid-column:1;grid-row:1}
        .twin-panel>.spatial-navigator{grid-column:1;grid-row:2}
        .twin-panel>.hss-canonical-geometry-panel{grid-column:2;grid-row:1 / span 2;margin:0;min-width:0}
        .hss-canonical-geometry-panel .hss-grid{display:block}
        .hss-canonical-geometry-panel .hss-card{margin-bottom:12px}
        .hss-canonical-geometry-panel .hss-preview{min-height:180px}
        .hss-canonical-geometry-panel .hss-geometry-apply-note{color:#53616c}
        @media(max-width:1050px){.twin-panel{display:block}.twin-panel>.hss-canonical-geometry-panel{margin-top:16px}}
      `;
      document.head.appendChild(style);
    }
  }

  function wireControls() {
    const studio=document.getElementById('hand-surface-studio');
    if(!studio || studio.dataset.canonicalGeometryWired==='1') return false;
    studio.dataset.canonicalGeometryWired='1';
    studio.addEventListener('input', event => {
      const input=event.target?.closest?.('[data-g]');
      if(!input) return;
      const value=Number(input.value);
      window.digitalTwinGeometry.setParameter(input.dataset.g,value);
      input.parentElement?.nextElementSibling && (input.parentElement.nextElementSibling.value=value);
      const label=studio.querySelector('.hss-geometry-value[data-value-for="'+input.dataset.g+'"]');
      if(label) label.textContent=value.toFixed(2)+'×';
    }, true);
    studio.addEventListener('click', event => {
      const button=event.target?.closest?.('#hss-apply-geometry');
      if(button){event.preventDefault();event.stopImmediatePropagation();window.digitalTwinGeometry.apply(readState(),'explicit-apply');return;}
      const reset=event.target?.closest?.('#hss-reset-geometry');
      if(reset){event.preventDefault();event.stopImmediatePropagation();window.digitalTwinGeometry.reset();return;}
    }, true);
    return true;
  }

  function sync() {
    ensureLayout();
    const wired=wireControls();
    if (active() && base.size===0) captureBase();
    const state=readState();
    if (active() && JSON.stringify(state)!==lastSignature) apply(state,'sync');
    return wired;
  }

  function boot() {
    if(installed)return;
    installed=true;
    const observer=new MutationObserver(sync);
    observer.observe(document.body,{childList:true,subtree:true});
    window.addEventListener('testhp:deep-3d-active',()=>setTimeout(sync,0));
    window.addEventListener('testhp:viewport-manager-ready',()=>setTimeout(sync,0));
    window.addEventListener('testhp:spatial-layer-changed',()=>setTimeout(sync,0));
    [0,100,300,800,1500,3000].forEach(ms=>setTimeout(sync,ms));
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
