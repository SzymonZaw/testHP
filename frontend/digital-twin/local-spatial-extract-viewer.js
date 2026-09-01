(()=>{
  'use strict';
  if (window.__testhpLocalSpatialExtractViewerInstalled) return;
  window.__testhpLocalSpatialExtractViewerInstalled = true;

  const SOURCE_ID = 'human-skin-spatial-census';
  const ENDPOINT = `/api/reference/tissue/${SOURCE_ID}/cells/preview`;
  const CARD_CLASS = 'dt-reference-spatial-extract';
  const MAX_POINTS = 1000;
  let loading = false;
  let loaded = false;
  let activeRegion = null;
  let activeCells = [];
  let selectedCellId = null;
  let abortController = null;

  function host() { return document.getElementById('testhp-end-user-layer'); }
  function mountPoint() {
    const h = host();
    if (!h) return null;
    return h.querySelector('#twin-viewport') || h.querySelector('.dt-viewport') || null;
  }
  function currentRegion() { return window.TestHPCanonicalState?.get?.()?.selection?.region || 'palm'; }
  function ensureStyles() {
    if (document.getElementById('testhp-local-spatial-extract-style')) return;
    const style = document.createElement('style'); style.id = 'testhp-local-spatial-extract-style';
    style.textContent = `.${CARD_CLASS}{margin-top:16px;border:1px solid rgba(155,216,196,.22);border-radius:16px;background:#0b1118;overflow:hidden}.${CARD_CLASS} .dt-local-spatial-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;padding:14px 16px;border-bottom:1px solid rgba(155,216,196,.12)}.${CARD_CLASS} .dt-local-spatial-kicker{font-size:9px;letter-spacing:.14em;color:#9bd8c4;font-weight:800;text-transform:uppercase}.${CARD_CLASS} .dt-local-spatial-title{font-size:14px;font-weight:800;color:#dce7f2;margin-top:3px}.${CARD_CLASS} .dt-local-spatial-meta{font-size:10px;color:#9fb0c2;text-align:right;line-height:1.45}.${CARD_CLASS} .dt-local-spatial-note{padding:10px 16px;font-size:10px;color:#9fb0c2;border-bottom:1px solid rgba(155,216,196,.08)}.${CARD_CLASS} canvas{display:block;width:100%;height:320px;background:#081015;cursor:crosshair}.${CARD_CLASS} .dt-local-spatial-cell{padding:10px 16px;font-size:10px;color:#dce7f2;border-top:1px solid rgba(155,216,196,.08);min-height:18px}.${CARD_CLASS} .dt-local-spatial-status{padding:9px 16px;font-size:10px;color:#9fb0c2;border-top:1px solid rgba(155,216,196,.08)}`;
    document.head.appendChild(style);
  }
  function cardRoot(parent) {
    let card = parent.querySelector(`:scope > .${CARD_CLASS}`); if (card) return card;
    card = document.createElement('section'); card.className = CARD_CLASS; card.setAttribute('aria-label', 'Local MERFISH spatial extract');
    card.innerHTML = `<div class="dt-local-spatial-head"><div><div class="dt-local-spatial-kicker">REAL LINKED DATA</div><div class="dt-local-spatial-title">MERFISH · LOCAL SPATIAL EXTRACT</div></div><div class="dt-local-spatial-meta">SAMPLE-LOCAL<br>Not registered to NIH hand geometry</div></div><div class="dt-local-spatial-note">Actual cells from the locally materialized H5AD extract. Coordinates are shown in their dataset/sample-local frame only.</div><canvas aria-label="MERFISH sample-local cell coordinates"></canvas><div class="dt-local-spatial-cell" aria-live="polite">No cell selected.</div><div class="dt-local-spatial-status">Loading local cell extract…</div>`;
    parent.appendChild(card); return card;
  }
  function pointData(cells) { return cells.map(c => { const x = Array.isArray(c?.spatial) ? c.spatial[0] : c?.x; const y = Array.isArray(c?.spatial) ? c.spatial[1] : c?.y; return Number.isFinite(Number(x)) && Number.isFinite(Number(y)) ? [Number(x), Number(y), c] : null; }).filter(Boolean).slice(0, MAX_POINTS); }
  function geometry(points, width, height) {
    let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity; for (const [x,y] of points) { minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y); }
    const pad=24,spanX=Math.max(1e-9,maxX-minX),spanY=Math.max(1e-9,maxY-minY),scale=Math.min((width-2*pad)/spanX,(height-2*pad)/spanY),plotW=spanX*scale,plotH=spanY*scale,ox=(width-plotW)/2,oy=(height-plotH)/2; return {minX,maxX,minY,maxY,scale,ox,oy,plotW,plotH};
  }
  function draw(canvas, cells) {
    if (!canvas) return 0;
    const rect=canvas.getBoundingClientRect(),width=Math.max(320,Math.round(rect.width)),height=Math.max(240,Math.round(rect.height)),dpr=Math.max(1,Math.min(2,window.devicePixelRatio||1));
    canvas.width=width*dpr;canvas.height=height*dpr;const ctx=canvas.getContext('2d');if(!ctx)return 0;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);
    const points=pointData(cells);if(!points.length)return 0;const g=geometry(points,width,height);ctx.strokeStyle='rgba(155,216,196,.14)';ctx.strokeRect(g.ox,g.oy,g.plotW,g.plotH);ctx.fillStyle='#9bd8c4';
    for(const [x,y,cell] of points){const px=g.ox+(x-g.minX)*g.scale,py=g.oy+(g.maxY-y)*g.scale;ctx.beginPath();ctx.arc(px,py,cell?.cellId===selectedCellId?4:1.7,0,Math.PI*2);ctx.fill();}
    ctx.fillStyle='#9fb0c2';ctx.font='10px system-ui, sans-serif';ctx.fillText(`n=${points.length}`,10,height-10);return points.length;
  }
  function renderSelection(card) { const cell=activeCells.find(c=>c?.cellId===selectedCellId),el=card?.querySelector('.dt-local-spatial-cell');if(!el)return;if(!cell){el.textContent='No cell selected.';return;}el.textContent=`Selected cell · ${cell.cellId} · ${cell.anatomicSite||'unknown site'} · ${cell.regionName||'unknown region'} · x=${Number(cell.x).toFixed(2)} · y=${Number(cell.y).toFixed(2)}`; }
  function selectCell(cell,card){if(!cell?.cellId)return;selectedCellId=cell.cellId;renderSelection(card);draw(card.querySelector('canvas'),activeCells);window.TestHPCanonicalState?.updateSelection?.({cell:cell.cellId});window.dispatchEvent(new CustomEvent('testhp:local-cell-selected',{detail:{sourceId:SOURCE_ID,region:activeRegion,cell}}));}
  function bindCanvas(canvas,card){if(!canvas||canvas.dataset.cellSelectionBound==='true')return;canvas.dataset.cellSelectionBound='true';canvas.addEventListener('click',event=>{if(!activeCells.length)return;const rect=canvas.getBoundingClientRect(),width=Math.max(320,Math.round(rect.width)),height=Math.max(240,Math.round(rect.height)),points=pointData(activeCells);if(!points.length)return;const g=geometry(points,width,height),px=event.clientX-rect.left,py=event.clientY-rect.top;let nearest=null,nearestDistance=Infinity;for(const [x,y,cell] of points){const cx=g.ox+(x-g.minX)*g.scale,cy=g.oy+(g.maxY-y)*g.scale,distance=Math.hypot(cx-px,cy-py);if(distance<nearestDistance){nearestDistance=distance;nearest=cell;}}if(nearest&&nearestDistance<=14)selectCell(nearest,card);});}
  async function load(region=currentRegion()) {
    const parent=mountPoint();if(!parent)return false;ensureStyles();const card=cardRoot(parent);bindCanvas(card.querySelector('canvas'),card);const normalizedRegion=String(region||'palm').trim().toLowerCase()||'palm';if(loading&&activeRegion===normalizedRegion)return true;if(loaded&&activeRegion===normalizedRegion){draw(card.querySelector('canvas'),activeCells);renderSelection(card);return true;}
    abortController?.abort();abortController=new AbortController();loading=true;activeRegion=normalizedRegion;activeCells=[];selectedCellId=null;renderSelection(card);const status=card.querySelector('.dt-local-spatial-status'),meta=card.querySelector('.dt-local-spatial-meta');if(status)status.textContent=`Loading local cell extract · ${normalizedRegion}…`;if(meta)meta.innerHTML=`${normalizedRegion.toUpperCase()} · SAMPLE-LOCAL<br>Not registered to NIH hand geometry`;
    try{const params=new URLSearchParams({region:normalizedRegion,limit:String(MAX_POINTS)}),response=await fetch(`${ENDPOINT}?${params.toString()}`,{cache:'no-store',credentials:'same-origin',signal:abortController.signal}),payload=await response.json();if(!response.ok)throw new Error(payload?.detail||`local extract endpoint returned ${response.status}`);if(activeRegion!==normalizedRegion)return true;activeCells=Array.isArray(payload?.cells)?payload.cells:[];const count=draw(card.querySelector('canvas'),activeCells),site=payload?.anatomicSite||payload?.region||activeCells[0]?.anatomicSite||'unknown site';if(status)status.textContent=`${count} plotted real cells · ${site} · sample-local coordinates`;loaded=true;}catch(error){if(error?.name==='AbortError')return true;if(status)status.textContent=`Local spatial extract unavailable: ${error?.message||error}`;loaded=false;}finally{if(activeRegion===normalizedRegion)loading=false;}return true;
  }
  function onCanonicalStateChanged(){const state=window.TestHPCanonicalState?.get?.();const region=currentRegion();if(region!==activeRegion){loaded=false;load(region);return;}const canonicalCell=state?.selection?.cell||null;if(canonicalCell!==selectedCellId){selectedCellId=canonicalCell;const card=document.querySelector('.'+CARD_CLASS);if(card){renderSelection(card);draw(card.querySelector('canvas'),activeCells);}}}
  function boot(){let observer,attempts=0;const tryMount=()=>{attempts+=1;load();if(attempts>=240)return;window.requestAnimationFrame(tryMount);};observer=new MutationObserver(()=>{if(mountPoint()&&!document.querySelector('.'+CARD_CLASS))load();});observer.observe(document.documentElement||document,{childList:true,subtree:true});tryMount();window.addEventListener('testhp:reference-hand-activated',load);window.addEventListener('testhp:canonical-state-changed',onCanonicalStateChanged);}
  window.testhpLocalSpatialExtract=Object.freeze({version:'local-spatial-extract-safe-7',sourceId:SOURCE_ID,load,getState:()=>({installed:true,loaded,loading,region:activeRegion,selectedCellId,cardPresent:!!document.querySelector(`.${CARD_CLASS}`)})});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
