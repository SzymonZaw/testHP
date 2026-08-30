/** Phase 16: integration guard for spatial, temporal and model-backed UI.
 *
 * This module is deliberately conservative: it never invents anatomy, cells,
 * molecular values, ages, trajectories or interventions. It only derives UI
 * state from the canonical state and backend result already loaded in memory.
 */
import { getDigitalTwinState, subscribeDigitalTwinState, updateSelection } from './canonical-ui-runtime.js';
import { suppliedCells, suppliedTissues, suppliedMolecularLayers, sanitizeSelection } from './digital-twin-phase1-8-governor.js';

const TIMEPOINTS = Object.freeze(['T0', 'T1', 'T2', 'T3']);
const NOT_ESTABLISHED = 'Not established';

function state() { return getDigitalTwinState?.() ?? null; }
function readyAsset(a) { return ['ready','available','verified','usable'].includes(String(a?.status ?? '').toLowerCase()); }
function modalityAvailable(s, modality) {
  const aliases = {
    hand_images:['hand_images','hand','image'], hand_video:['hand_video','video'], hand_3d:['hand_3d','3d','mesh'],
    tissue_wsi:['tissue_wsi','wsi'], single_cell_rna:['single_cell_rna','rna','scrna'], proteomics:['proteomics','protein'],
    epigenetics:['epigenetics','methylation','chromatin'], genomics:['genomics','genome','variant']
  }[modality] ?? [modality];
  return (s?.assets ?? []).some(a => readyAsset(a) && aliases.includes(String(a?.modality ?? '').toLowerCase()));
}

export function integrationSnapshot(s = state()) {
  const sel = s?.selection ?? {};
  const tissues = suppliedTissues(s, sel.region);
  const cells = suppliedCells(s, sel.region, sel.tissue);
  const molecular = suppliedMolecularLayers(s, sel.cell);
  return {
    timepoint: TIMEPOINTS.includes(sel.timepoint) ? sel.timepoint : 'T0',
    region: sel.region ?? 'palm',
    tissue: sel.tissue ?? null,
    cell: sel.cell ?? null,
    molecularLayer: sel.molecularLayer ?? null,
    supplied: { tissues: tissues.length, cells: cells.length, molecularLayers: molecular.length },
    evidence: {
      handImages: modalityAvailable(s,'hand_images'), handVideo: modalityAvailable(s,'hand_video'),
      hand3d: modalityAvailable(s,'hand_3d'), wsi: modalityAvailable(s,'tissue_wsi'),
      rna: modalityAvailable(s,'single_cell_rna'), proteomics: modalityAvailable(s,'proteomics'),
      epigenetics: modalityAvailable(s,'epigenetics'), genomics: modalityAvailable(s,'genomics')
    },
    modelBacked: {
      age: Boolean(s?.biologicalAge && typeof s.biologicalAge === 'object' && s.biologicalAge.status !== 'not_established'),
      agingTrajectory: Boolean(s?.trajectory), diseaseTrajectory: Boolean(s?.diseaseTrajectory),
      whatIf: Boolean(s?.whatIf), intervention: Boolean(s?.interventions)
    }
  };
}

function validateSelection(s) {
  if (!s?.selection) return;
  const safe = sanitizeSelection(s, s.selection);
  const a = s.selection, b = safe.selection;
  const changed = ['timepoint','region','tissue','cell','molecularLayer'].some(k => a[k] !== b[k]);
  if (changed) updateSelection(b);
}

function persistTimepoint(timepoint) {
  try { sessionStorage.setItem('testhp.digitalTwin.timepoint', timepoint); } catch { /* best effort */ }
}
function restoreTimepoint() {
  try {
    const t = sessionStorage.getItem('testhp.digitalTwin.timepoint');
    if (TIMEPOINTS.includes(t) && state()?.selection?.timepoint !== t) updateSelection({timepoint:t});
  } catch { /* best effort */ }
}

function install() {
  if (window.__testhpPhase16IntegrationGuard) return;
  window.__testhpPhase16IntegrationGuard = true;
  restoreTimepoint();
  subscribeDigitalTwinState?.((next) => {
    validateSelection(next);
    const t = next?.selection?.timepoint;
    if (TIMEPOINTS.includes(t)) persistTimepoint(t);
    window.dispatchEvent(new CustomEvent('testhp:integration-snapshot', { detail: integrationSnapshot(next) }));
  });
  window.addEventListener('testhp:canonical-state-changed', e => {
    validateSelection(e.detail);
    const t = e.detail?.selection?.timepoint;
    if (TIMEPOINTS.includes(t)) persistTimepoint(t);
  });
  window.TestHPIntegration = Object.freeze({ integrationSnapshot, modalityAvailable, NOT_ESTABLISHED, TIMEPOINTS });
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once:true });
else install();
