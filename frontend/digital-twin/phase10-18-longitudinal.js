import { getDigitalTwinState, subscribeDigitalTwinState, updateSelection } from './canonical-ui-runtime.js';

export const TIMEPOINTS = Object.freeze(['T0', 'T1', 'T2', 'T3']);
export const RESULT_STATUSES = Object.freeze(['Observed', 'Computed', 'Estimated', 'Predicted', 'Hypothetical', 'Not established']);
export const NOT_ESTABLISHED = 'Not established';

export function normalizeResultStatus(value) {
  const raw = String(value?.status ?? value?.kind ?? value ?? '').trim().toLowerCase().replaceAll('_', ' ');
  const found = RESULT_STATUSES.find(item => item.toLowerCase() === raw);
  return found ?? NOT_ESTABLISHED;
}

export function trajectoryStatusForTimepoint(state, timepoint) {
  const candidates = [state?.trajectory, state?.diseaseTrajectory];
  for (const data of candidates) {
    const points = Array.isArray(data) ? data : Array.isArray(data?.points) ? data.points : Array.isArray(data?.series) ? data.series : [];
    const point = points.find(item => String(item?.timepoint ?? item?.time ?? item?.label ?? '') === timepoint);
    if (point) return normalizeResultStatus(point);
  }
  if (state?.timepoint === timepoint && state?.status === 'ready') return normalizeResultStatus(state?.biologicalState?.status);
  return NOT_ESTABLISHED;
}

export function buildTimelineModel(state) {
  return TIMEPOINTS.map(timepoint => {
    const status = trajectoryStatusForTimepoint(state, timepoint);
    return { timepoint, selected: state?.selection?.timepoint === timepoint, status, established: status !== NOT_ESTABLISHED };
  });
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[char]));
}

function renderTimeline(state) {
  const model = buildTimelineModel(state);
  return `<section class="dt-longitudinal-timeline" aria-label="Longitudinal timepoint timeline">
    <div class="dt-longitudinal-head"><span>TIME</span><small>Observed · Predicted · Not established</small></div>
    <div class="dt-longitudinal-track">
      ${model.map((item, index) => `<div class="dt-longitudinal-node ${item.selected ? 'selected' : ''} ${item.established ? 'established' : 'unknown'}">
        <button type="button" data-longitudinal-timepoint="${item.timepoint}" aria-pressed="${item.selected}">${item.timepoint}</button>
        <span>${escapeHtml(item.status)}</span>
      </div>${index < model.length - 1 ? '<div class="dt-longitudinal-line" aria-hidden="true"></div>' : ''}`).join('')}
    </div>
  </section>`;
}

function installStyle() {
  if (typeof document === 'undefined') return;
  const style = document.createElement('style');
  style.textContent = `
.dt-longitudinal-timeline{margin:0 28px;padding:10px 0 12px;border-bottom:1px solid #171f28;color:#8290a1}.dt-longitudinal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:10px;font-weight:800;letter-spacing:.12em}.dt-longitudinal-head small{font-size:9px;font-weight:500;letter-spacing:0;color:#667587}.dt-longitudinal-track{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;align-items:start}.dt-longitudinal-node{position:relative;text-align:center}.dt-longitudinal-node button{position:relative;z-index:2;border:1px solid #26313d;border-radius:999px;background:#0d1219;color:#788799;padding:4px 10px;cursor:pointer;font-size:10px}.dt-longitudinal-node.selected button{border-color:#69b8ff;color:#dbeeff;box-shadow:0 0 0 2px #69b8ff22}.dt-longitudinal-node span{display:block;margin-top:4px;color:#586778;font-size:9px}.dt-longitudinal-node.established span{color:#7da98f}.dt-longitudinal-node.unknown span{color:#667487}.dt-longitudinal-line{height:1px;background:#27323e;transform:translateY(12px)}@media(max-width:700px){.dt-longitudinal-timeline{margin:0 14px}.dt-longitudinal-track{overflow-x:auto;grid-template-columns:repeat(4,minmax(78px,1fr))}}
`;
  document.head.appendChild(style);
}

function mountTimeline(state) {
  const anchor = document.querySelector('.dt-breadcrumb-top');
  if (!anchor) return;
  document.querySelectorAll('.dt-longitudinal-timeline').forEach(node => node.remove());
  anchor.insertAdjacentHTML('afterend', renderTimeline(state));
  document.querySelectorAll('[data-longitudinal-timepoint]').forEach(button => {
    button.addEventListener('click', () => updateSelection({ timepoint: button.dataset.longitudinalTimepoint, tissue: null, cell: null, molecularLayer: null }));
  });
}

function install() {
  if (window.__testhpPhase10to18Loaded) return;
  window.__testhpPhase10to18Loaded = true;
  installStyle();
  subscribeDigitalTwinState(mountTimeline);
}

if (typeof window !== 'undefined') {
  window.TestHPPhase10to18 = Object.freeze({ TIMEPOINTS, RESULT_STATUSES, NOT_ESTABLISHED, normalizeResultStatus, trajectoryStatusForTimepoint, buildTimelineModel });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
}
