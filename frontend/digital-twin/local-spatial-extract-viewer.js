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
  function ensureStyles() { /* unchanged */ }
  function cardRoot(parent) { let card = parent.querySelector(`:scope > .${CARD_CLASS}`); if (card) return card; card = document.createElement('section'); card.className = CARD_CLASS; card.setAttribute('aria-label', 'Local MERFISH spatial extract'); card.innerHTML = `<div class="dt-local-spatial-head"><div><div class="dt-local-spatial-kicker">REAL LINKED DATA</div><div class="dt-local-spatial-title">MERFISH · LOCAL SPATIAL EXTRACT</div></div><div class="dt-local-spatial-meta">SAMPLE-LOCAL<br>Not registered to NIH hand geometry</div></div><div class="dt-local-spatial-note">Actual cells from the locally materialized H5AD extract. Coordinates are shown in their dataset/sample-local frame only.</div><canvas aria-label="MERFISH sample-local cell coordinates"></canvas><div class="dt-local-spatial-cell" aria-live="polite">No cell selected.</div><div class="dt-local-spatial-status">Loading local cell extract…</div>`; parent.appendChild(card); return card; }
  function pointData(cells){return cells.map(c=>{const x=Array.isArray(c?.spatial)?c.spatial[0]:c?.x;const y=Array.isArray(c?.spatial)?c.spatial[1]:c?.y;return Number.isFinite(Number(x))&&Number.isFinite(Number(y))?[Number(x),Number(y),c]:null;}).filter(Boolean).slice(0,MAX_POINTS);}
  function geometry(points,width,height){let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;for(const [x,y] of points){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}const pad=24,spanX=Math.max(1e-9,maxX-minX),spanY=Math.max(1e-9,maxY-minY),scale=Math.min((width-2*pad)/spanX,(height-2*pad)/spanY),plotW=spanX*scale,plotH=spanY*scale,ox=(width-plotW)/2,oy=(height-plotH)/2;return {minX,maxX,minY,maxY,scale,ox,oy,plotW,plotH};}
  function draw(canvas,cells){if(!canvas)return 0; const rect=canvas.getBoundingClientRect(),width=Math.max(320,Math.round(rect.width)),height=Math.max(240,Math.round(rect.height)),dpr=Math.max(1,Math.min(2,window.devicePixelRatio||1));canvas.width=width*dpr;canvas.height=height*dpr;const ctx=canvas.getContext('2d');if(!ctx)return 0;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);const points=pointData(cells);if(!points.length)return 0;const g=geometry(points,width,height);ctx.strokeStyle='rgba(155,216,196,.14)';ctx.strokeRect(g.ox,g.oy,g.plotW,g.plotH);ctx.fillStyle='#9bd8c4';for(const [x,y,cell] of points){const px=g.ox+(x-g.minX)*g.scale,py=g.oy+(g.maxY-y)*g.scale;ctx.beginPath();ctx.arc(px,py,cell?.cellId===selectedCellId?4:1.7,0,Math.PI*2);ctx.fill();}return points.length;}
  function renderSelection(card){const cell=activeCells.find(c=>c?.cellId===selectedCellId),el=card?.querySelector('.dt-local-spatial-cell');if(!el)return;if(!cell){el.textContent='No cell selected.';return;}el.textContent=`Selected cell · ${cell.cellId}`;}
  function selectCell(cell,card){if(!cell?.cellId)return;selectedCellId=cell.cellId;renderSelection(card);draw(card.querySelector('canvas'),activeCells);window.TestHPCanonicalState?.updateSelection?.({cell:cell.cellId});window.dispatchEvent(new CustomEvent('testhp:local-cell-selected',{detail:{sourceId:SOURCE_ID,region:activeRegion,cell}}));}
  function bindCanvas(){}
  async function load(region=currentRegion()){return true;}
  function onCanonicalStateChanged(){const state=window.TestHPCanonicalState?.get?.();const region=currentRegion();if(region!==activeRegion){loaded=false;load(region);return;}const canonicalCell=state?.selection?.cell||null;if(canonicalCell!==selectedCellId){selectedCellId=canonicalCell;const card=document.querySelector('.'+CARD_CLASS);if(card){renderSelection(card);draw(card.querySelector('canvas'),activeCells);}}}
  function boot(){let observer,attempts=0;const tryMount=()=>{attempts+=1;load();if(attempts>=240)return;window.requestAnimationFrame(tryMount);};observer=new MutationObserver(()=>{if(mountPoint()&&!document.querySelector('.'+CARD_CLASS))load();});observer.observe(document.documentElement||document,{childList:true,subtree:true});tryMount();window.addEventListener('testhp:reference-hand-activated',load);window.addEventListener('testhp:canonical-state-changed',onCanonicalStateChanged);}
  window.testhpLocalSpatialExtract=Object.freeze({version:'local-spatial-extract-safe-6',sourceId:SOURCE_ID,load,getState:()=>({installed:true,loaded,loading,region:activeRegion,selectedCellId,cardPresent:!!document.querySelector(`.${CARD_CLASS}`)})});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();