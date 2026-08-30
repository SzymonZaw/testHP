export const SPATIAL_STATE_VERSION = 1;

export function createSpatialCanonicalState(overrides = {}) {
  return {
    version: SPATIAL_STATE_VERSION,
    subject: overrides.subject ?? null,
    timepoint: overrides.timepoint ?? null,
    region: overrides.region ?? null,
    tissue: overrides.tissue ?? null,
    cell: overrides.cell ?? null,
    molecularLayer: overrides.molecularLayer ?? null,
    evidence: overrides.evidence ?? null,
    biologicalState: overrides.biologicalState ?? null,
  };
}

export function applySpatialSelection(state, selection = {}) {
  return {
    ...state,
    region: selection.regionId ?? state.region,
    tissue: selection.tissueId ?? null,
    cell: selection.cellId ?? null,
  };
}

export function selectionFromCanonicalState(state) {
  return {
    regionId: state?.region ?? null,
    tissueId: state?.tissue ?? null,
    cellId: state?.cell ?? null,
  };
}

export function serializeSpatialState(state) {
  return JSON.stringify(createSpatialCanonicalState(state));
}

export function restoreSpatialState(serialized) {
  if (!serialized) return createSpatialCanonicalState();
  try {
    const parsed = JSON.parse(serialized);
    return createSpatialCanonicalState(parsed);
  } catch {
    return createSpatialCanonicalState();
  }
}

export function bindSpatialState({ getState, setState, storage, storageKey = "digital-twin:spatial-state" } = {}) {
  if (!getState || !setState) throw new Error("getState and setState are required.");
  const read = () => restoreSpatialState(storage?.getItem?.(storageKey));
  const write = () => storage?.setItem?.(storageKey, serializeSpatialState(getState()));
  return { read, write };
}
