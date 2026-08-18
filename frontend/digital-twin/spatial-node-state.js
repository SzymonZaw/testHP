// Canonical spatial navigation state contract for the Digital Twin viewport.
// Renderers consume this normalized state rather than rebuilding navigation context.

export function createSpatialNodeState(node = {}) {
  const children = Array.isArray(node.children) ? node.children : [];
  const evidence = Array.isArray(node.evidence) ? node.evidence : [];
  return Object.freeze({
    resolution: node.resolution || 'macro',
    target: node.target || node.label || 'Hand',
    path: Array.isArray(node.path) ? [...node.path] : [],
    parent: node.parent ? { ...node.parent } : null,
    children: children.map(child => ({ ...child })),
    evidence: evidence.map(item => ({ ...item })),
  });
}

export function spatialNodeKey(state) {
  return [state.resolution, state.path.join('>'), state.target,
    state.children.map(child => child.label || child.target || '').join('|')].join('|');
}

export function hasEvidenceForResolution(state) {
  if (state.resolution === 'macro') return true;
  return state.evidence.some(item =>
    (item.resolution || item.spatial_resolution || item.level) === state.resolution
  );
}
