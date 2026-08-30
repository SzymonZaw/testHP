import { getDigitalTwinState, subscribeDigitalTwinState, updateSelection } from './canonical-ui-runtime.js';

export const TIMEPOINTS = Object.freeze(['T0', 'T1', 'T2', 'T3']);
export const RESULT_STATUSES = Object.freeze(['Observed', 'Computed', 'Estimated', 'Predicted', 'Hypothetical', 'Not established']);
export const NOT_ESTABLISHED = 'Not established';

const hasValue = value => value !== null && value !== undefined && value !== '';

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
  if (state?.timepoint === timepoint && state?.status === 'ready') {
    return normalizeResultStatus(state?.biologicalState?.status);
  }
  return NOT_ESTABLISHED;
}

export function buildTimelineModel(state) {
  return TIMEPOINTS.map(timepoint => ({
    timepoint,
    selected: state?.selection?.timepoint === timepoint,
    status: trajectoryStatusForTimepoint(state, timepoint),
    established: trajectoryStatusForTimepoint(state, timepoint) !== NOT_ESTABLISHED,
  }));
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
  subscribeDigitalTwinState(mountTimeline);
}

if (typeof window !== 'undefined') {
  window.TestHPPhase10to18 = Object.freeze({ TIMEPOINTS, RESULT_STATUSES, NOT_ESTABLISHED, normalizeResultStatus, trajectoryStatusForTimepoint, buildTimelineModel });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
}
