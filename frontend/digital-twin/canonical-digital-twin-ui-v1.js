import { getDigitalTwinState, ingestAnalysisResult, updateSelection, subscribeDigitalTwinState } from './canonical-ui-runtime.js';
import { SPATIAL_REGIONS, MOLECULAR_LAYERS, suppliedCellId, suppliedTissueId, suppliedTissues, suppliedCells, suppliedMolecularLayers, displayNotEstablished } from './digital-twin-phase1-8-governor.js';

const MODALITIES = [
  ['hand_images', 'Hand Images'], ['hand_video', 'Hand Video'], ['hand_3d', '3D Scan'], ['tissue_wsi', 'WSI'],
  ['single_cell_rna', 'RNA'], ['proteomics', 'Proteomics'], ['epigenetics', 'Epigenetics'], ['genomics', 'Genomics'],
];
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
const finite = (value) => Number.isFinite(Number(value)) ? Number(value) : null;
const ready = (value) => ['ready','available','verified','usable'].includes(String(value?.status ?? '').toLowerCase());

function backendHasModality(state, id) {
  const aliases = {
    hand_images: ['hand_images','hand','image'], hand_video: ['hand_video','video'], hand_3d: ['hand_3d','3d','mesh'],
    tissue_wsi: ['tissue_wsi','wsi'], single_cell_rna: ['single_cell_rna','rna','scrna'], proteomics: ['proteomics','protein'],
    epigenetics: ['epigenetics','methylation','chromatin'], genomics: ['genomics','genome','variant'],
  }[id] ?? [id];
  const assets = Array.isArray(state.assets) ? state.assets : [];
  return assets.some((asset) => ready(asset) && aliases.includes(String(asset.modality ?? '').toLowerCase()));
}

function valueOrNE(value) { return esc(displayNotEstablished(value)); }
function statusOf(value) { return value?.status ?? value?.state ?? null; }
function confidenceOf(value) { return value?.confidence ?? null; }
function uncertaintyOf(value) { return value?.uncertainty ?? null; }

function ensureHost() {
  let host = document.getElementById('testhp-end-user-layer');
  if (!host) { host = document.createElement('main'); host.id = 'testhp-end-user-layer'; document.body.appendChild(host); }
  return host;
}

function render(state) {
  const host = ensureHost();
  const sel = state.selection;
  const tissues = suppliedTissues(state, sel.region);
  const cells = suppliedCells(state, sel.region, sel.tissue);
  const selectedCell = cells.find((cell) => suppliedCellId(cell) === String(sel.cell)) ?? null;
  const molecular = suppliedMolecularLayers(state, sel.cell);
  const available = MODALITIES.filter(([id]) => backendHasModality(state, id)).length;
  const coverage = finite(state.evidence?.coverage);
  const coveragePct = coverage === null ? '—' : `${Math.round(coverage <= 1 ? coverage * 100 : coverage)}%`;

  host.innerHTML = `
    <div class="dt-canonical">
      <header class="dt-topbar">
        <div><div class="dt-kicker">HUMAN DIGITAL TWIN</div><div class="dt-subtitle">Spatial · cellular · molecular · longitudinal</div></div>
        <div class="dt-context"><span>Subject <b>${esc(sel.subject)}</b></span><span>Timepoint <div class="dt-time">${['T0','T1','T2','T3'].map((t)=>`<button class="dt-time-btn ${t===sel.timepoint?'active':''}" data-timepoint="${t}">${t}</button>`).join('')}</div></span><span>Region <b>${esc(sel.region)}</b></span></div>
      </header>
      <div class="dt-grid">
        <aside class="dt-left">
          <div class="dt-section-label">WHERE AM I?</div>
          <div class="dt-breadcrumb">Hand / ${esc(sel.region)}${sel.tissue ? ` / ${esc(sel.tissue)}` : ''}${sel.cell ? ` / Cell ${esc(sel.cell)}` : ''}</div>
          <div class="dt-tree"><button class="dt-tree-root" data-region="hand">HAND</button>${SPATIAL_REGIONS.map(([id,label]) => `
            <div class="dt-tree-group"><button class="dt-region ${id===sel.region?'active':''}" data-region="${id}">${id===sel.region?'▾':'▸'} ${label}</button>${id===sel.region ? `<div class="dt-tree-children">${tissues.length ? tissues.map((t)=>{const tid=suppliedTissueId(t);return `<button class="dt-tissue ${tid===sel.tissue?'active':''}" data-tissue="${esc(tid)}">${esc(t.name ?? t.label ?? tid)}</button>`}).join('') : '<span class="dt-empty">No tissue data supplied</span>'}${sel.tissue ? `<div class="dt-cell-heading">CELLS</div>${cells.length ? cells.map((c)=>{const cid=suppliedCellId(c);return `<button class="dt-cell ${cid===sel.cell?'active':''}" data-cell="${esc(cid)}">● ${esc(cid)}</button>`}).join('') : '<span class="dt-empty">No cell data supplied</span>'}` : ''}</div>` : ''}</div>`).join('')}</div>
          <div class="dt-scale"><div class="dt-section-label">SCALE</div><div>Hand → Region → Tissue → Cell → Molecular</div></div>
        </aside>
        <section class="dt-center">
          <div class="dt-viewport-head"><div><span class="dt-kicker">DIGITAL TWIN</span><b> · ${esc(sel.region)}</b></div><span class="dt-nav-state">${sel.cell ? `CELL ${esc(sel.cell)}` : sel.tissue ? 'TISSUE' : 'REGION'}</span></div>
          <div id="twin-viewport" class="dt-viewport"></div>
          <div class="dt-viewport-note">Drag to rotate · wheel to zoom · click a supplied spatial target</div>
        </section>
        <aside class="dt-right">
          <section class="dt-card"><div class="dt-card-title">BIOLOGICAL STATE</div><div class="dt-metric"><span>Health</span><b>${valueOrNE(state.biologicalState?.health?.state ?? state.health?.state)}</b></div><div class="dt-metric"><span>Biological age</span><b>${valueOrNE(state.biologicalState?.biologicalAge?.biological_age ?? state.biologicalAge?.biological_age)}</b></div><div class="dt-metric"><span>Confidence</span><b>${valueOrNE(state.biologicalState?.confidence ?? confidenceOf(state.health))}</b></div><div class="dt-metric"><span>Uncertainty</span><b>${valueOrNE(state.biologicalState?.uncertainty ?? state.uncertainty)}</b></div><p class="dt-note">Wynik jest wyświetlany tylko, jeśli został dostarczony przez backend/model.</p></section>
          <section class="dt-card"><div class="dt-card-title">EVIDENCE</div><div class="dt-coverage"><span>Evidence coverage</span><b>${coveragePct}</b></div>${MODALITIES.map(([id,label])=>`<div class="dt-evidence-row"><span>${label}</span><b class="${backendHasModality(state,id)?'yes':'no'}">${backendHasModality(state,id)?'Available':'Missing'}</b></div>`).join('')}<p class="dt-note">Evidence ≠ Health · Coverage ≠ Clinical confidence · Missing ≠ Disease.</p><div class="dt-missing">${esc(MODALITIES.filter(([id])=>!backendHasModality(state,id)).map(([,label])=>label).join(', ') || 'None')}</div></section>
          <section class="dt-card"><div class="dt-card-title">CELL INSPECTOR</div>${selectedCell ? `<div class="dt-cell-title">CELL ${esc(suppliedCellId(selectedCell))}</div><div class="dt-detail"><span>Type</span><b>${valueOrNE(selectedCell.type ?? selectedCell.cell_type)}</b></div><div class="dt-detail"><span>Location</span><b>${esc(sel.region)}${sel.tissue?` / ${esc(sel.tissue)}`:''}</b></div><div class="dt-detail"><span>Morphology</span><b>${valueOrNE(selectedCell.morphology ?? selectedCell.morphology_status)}</b></div><div class="dt-detail"><span>Cell State</span><b>${valueOrNE(selectedCell.state ?? selectedCell.cell_state)}</b></div><div class="dt-detail"><span>Health</span><b>${valueOrNE(selectedCell.health)}</b></div><div class="dt-detail"><span>Biological Age</span><b>${valueOrNE(selectedCell.biological_age ?? selectedCell.age)}</b></div><div class="dt-detail"><span>Confidence</span><b>${valueOrNE(confidenceOf(selectedCell))}</b></div><div class="dt-detail"><span>Uncertainty</span><b>${valueOrNE(uncertaintyOf(selectedCell))}</b></div><div class="dt-molecular"><div class="dt-card-title">MOLECULAR</div>${MOLECULAR_LAYERS.map(([id,label])=>`<button class="dt-mol ${molecular.some((x)=>x.id===id)?'available':'missing'} ${sel.molecularLayer===id?'active':''}" data-molecular="${id}">${label} <span>${molecular.some((x)=>x.id===id)?'Available':'Missing'}</span></button>`).join('')}</div>` : '<div class="dt-empty-inspector"><b>Select a supplied cell</b><span>Choose a cell from the spatial tree. No cell is created by the frontend.</span></div>'}</section>
          <section class="dt-card dt-governance"><div class="dt-card-title">GOVERNANCE</div><b>RESEARCH ONLY</b><span>Clinical readiness is not established.</span><small>Backend result is authoritative. Frontend does not invent biological values.</small></section>
        </aside>
      </div>
      <footer class="dt-footer"><span>${available}/${MODALITIES.length} evidence modalities available</span><span>State v${esc(state.stateVersion)}</span><span>Data status: ${esc(state.status)}</span></footer>
    </div>`;

  host.querySelectorAll('[data-region]').forEach((button) => button.addEventListener('click', () => {
    const region = button.dataset.region;
    if (region === 'hand') updateSelection({ region: 'palm' }); else updateSelection({ region });
  }));
  host.querySelectorAll('[data-tissue]').forEach((button) => button.addEventListener('click', () => updateSelection({ tissue: button.dataset.tissue })));
  host.querySelectorAll('[data-cell]').forEach((button) => button.addEventListener('click', () => updateSelection({ cell: button.dataset.cell })));
  host.querySelectorAll('[data-molecular]').forEach((button) => button.addEventListener('click', () => updateSelection({ molecularLayer: button.dataset.molecular })));
  host.querySelectorAll('[data-timepoint]').forEach((button) => button.addEventListener('click', () => loadTimepoint(button.dataset.timepoint)));
}

async function loadTimepoint(timepoint) {
  const state = getDigitalTwinState();
  updateSelection({ timepoint, tissue: null, cell: null, molecularLayer: null });
  try {
    const response = await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(state.selection.subject)}&timepoint=${encodeURIComponent(timepoint)}`, { cache: 'no-store', headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`Analysis HTTP ${response.status}`);
    ingestAnalysisResult(await response.json());
  } catch (error) {
    window.TestHPCanonicalState?.setAnalysisError?.(error);
  }
}

async function loadInitial() {
  const state = getDigitalTwinState();
  try {
    const response = await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(state.selection.subject)}&timepoint=${encodeURIComponent(state.selection.timepoint)}`, { cache: 'no-store', headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`Analysis HTTP ${response.status}`);
    ingestAnalysisResult(await response.json());
  } catch (error) {
    window.TestHPCanonicalState?.setAnalysisError?.(error);
  }
}

const style = document.createElement('style');
style.textContent = `
.dt-canonical{min-height:100vh;background:#0b0f14;color:#e7edf4;font:14px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.dt-topbar{display:flex;justify-content:space-between;gap:24px;padding:22px 28px;border-bottom:1px solid #202833}.dt-kicker,.dt-section-label,.dt-card-title{font-size:11px;font-weight:800;letter-spacing:.12em;color:#91a0b2}.dt-subtitle{color:#6f7d8e;font-size:12px}.dt-context{display:flex;align-items:center;gap:18px;color:#758395;font-size:12px}.dt-context b{color:#dbe4ee}.dt-time{display:inline-flex;margin-left:6px}.dt-time-btn,.dt-region,.dt-tree-root,.dt-tissue,.dt-cell,.dt-mol{border:0;background:transparent;color:#9eacbc;text-align:left;cursor:pointer}.dt-time-btn{padding:4px 7px}.dt-time-btn.active,.dt-region.active,.dt-tissue.active,.dt-cell.active,.dt-mol.active{color:#69b8ff}.dt-grid{display:grid;grid-template-columns:250px minmax(420px,1fr) 330px;min-height:calc(100vh - 82px)}.dt-left,.dt-right{padding:20px;border-right:1px solid #202833}.dt-right{border-right:0;border-left:1px solid #202833}.dt-section-label{margin-bottom:9px}.dt-breadcrumb{color:#758395;font-size:12px;margin-bottom:14px}.dt-tree-group{margin:2px 0}.dt-region{width:100%;padding:8px;border-radius:7px}.dt-region.active{background:#111b26}.dt-tree-children{padding:5px 0 8px 15px;border-left:1px solid #283444}.dt-tissue,.dt-cell{display:block;width:100%;padding:6px 8px;font-size:13px}.dt-cell-heading{margin:12px 8px 4px;font-size:10px;color:#647487;letter-spacing:.1em}.dt-empty,.dt-empty-inspector{display:block;color:#687789;padding:8px;font-size:12px}.dt-scale{margin-top:28px;padding-top:18px;border-top:1px solid #202833;color:#788799;font-size:12px}.dt-center{padding:14px;min-width:0}.dt-viewport-head{display:flex;justify-content:space-between;padding:7px 5px 10px;color:#8290a1}.dt-nav-state{font-size:11px;color:#69b8ff}.dt-viewport{min-height:560px;height:calc(100vh - 150px);border:1px solid #202833;border-radius:14px;overflow:hidden;background:#0d1219}.dt-viewport-note{color:#667587;font-size:11px;padding:8px}.dt-card{border-bottom:1px solid #202833;padding:0 0 17px;margin-bottom:18px}.dt-card-title{margin-bottom:12px}.dt-metric,.dt-detail,.dt-evidence-row,.dt-coverage{display:flex;justify-content:space-between;gap:12px;padding:7px 0}.dt-metric span,.dt-detail span,.dt-evidence-row span,.dt-coverage span{color:#738296}.dt-metric b,.dt-detail b{font-weight:700;text-align:right}.dt-note{color:#687789;font-size:11px}.dt-evidence-row b{font-size:11px}.dt-evidence-row .yes{color:#79caa1}.dt-evidence-row .no{color:#667487}.dt-missing{color:#657486;font-size:10px;margin-top:8px}.dt-cell-title{font-weight:800;font-size:16px;margin-bottom:10px}.dt-molecular{margin-top:15px}.dt-mol{display:flex;justify-content:space-between;width:100%;padding:7px 0;border-bottom:1px solid #19212b;font-size:12px}.dt-mol span{color:#667487}.dt-mol.available span{color:#79caa1}.dt-governance b{display:block;color:#d6a64f;font-size:11px;letter-spacing:.08em}.dt-governance span,.dt-governance small{display:block;color:#6c7a8b;margin-top:5px;font-size:11px}.dt-footer{display:flex;justify-content:space-between;padding:10px 20px;color:#5f6d7e;border-top:1px solid #202833;font-size:10px}@media(max-width:1100px){.dt-grid{grid-template-columns:210px minmax(360px,1fr)}.dt-right{grid-column:1/-1;border-left:0;border-top:1px solid #202833;display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.dt-viewport{height:520px}}@media(max-width:760px){.dt-topbar,.dt-context{flex-direction:column;align-items:flex-start}.dt-grid{display:block}.dt-left,.dt-right{border:0;border-bottom:1px solid #202833}.dt-right{display:block}.dt-viewport{height:440px;min-height:440px}}
`;
document.head.appendChild(style);
subscribeDigitalTwinState(render);
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', loadInitial, { once: true }); else loadInitial();
