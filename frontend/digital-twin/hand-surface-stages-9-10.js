/* Hand Surface · Stages 9–10
 * Rendering-only infrastructure: projection/scaffold state never creates evidence.
 */

export const HAND_SURFACE_STAGES_9_10 = Object.freeze({
  stage9: {
    id: 'surface-projection',
    status: 'prototype',
    projectionSpace: 'hand-surface',
    sources: ['front', 'back', 'left', 'right'],
    registration: 'landmark-assisted',
    blend: 'weighted-multiview',
    confidence: 'not-validated',
  },
  stage10: {
    id: 'anatomical-scaffold',
    status: 'prototype',
    structures: ['bones', 'joints', 'tendons', 'vessels'],
    opacityIndependent: true,
    evidenceGenerating: false,
  },
});

export function createSurfaceProjectionState(overrides = {}) {
  return {
    enabled: false,
    opacity: 1,
    mode: 'projected',
    sourceViews: [],
    registration: 'landmark-assisted',
    confidence: 'not-validated',
    ...overrides,
  };
}

export function createAnatomicalScaffoldState(overrides = {}) {
  return {
    enabled: false,
    opacity: 1,
    visibleStructures: {
      bones: true,
      joints: true,
      tendons: false,
      vessels: false,
    },
    interactionOwner: false,
    ...overrides,
  };
}

export function getViewportLayerContract({ activeLayer = 'macro', deepActive = false } = {}) {
  return {
    activeLayer,
    deepActive,
    skin: { rendered: true, input: activeLayer === 'macro' && !deepActive },
    scaffold: { rendered: true, input: false },
    evidence: { rendered: true, input: false },
    deep: { rendered: deepActive, input: deepActive },
  };
}
