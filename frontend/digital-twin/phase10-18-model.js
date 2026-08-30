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
