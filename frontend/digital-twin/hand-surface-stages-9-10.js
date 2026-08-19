/* Hand Surface · Stages 9–10
 * Rendering infrastructure never creates biological evidence.
 */

export const HAND_SURFACE_STAGES_9_10 = Object.freeze({
  stage9: {
    id: 'surface-projection',
    status: 'implemented',
    projectionSpace: 'hand-surface',
    sources: ['front', 'back', 'left', 'right'],
    registration: 'landmark-assisted-ready',
    blend: 'normal-weighted-multiview',
    confidence: 'asset/registration metadata required',
  },
  stage10: {
    id: 'anatomical-scaffold',
    status: 'implemented',
    structures: ['bones', 'joints', 'tendons', 'vessels'],
    opacityIndependent: true,
    evidenceGenerating: false,
    interactionOwner: false,
  },
});

export function createSurfaceProjectionState(overrides = {}) {
  return {
    enabled: false,
    opacity: 1,
    mode: 'projected',
    sourceViews: [],
    registration: 'landmark-assisted-ready',
    confidence: 'not-validated',
    ...overrides,
  };
}

export function createAnatomicalScaffoldState(overrides = {}) {
  return {
    enabled: false,
    opacity: 0.42,
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
  const macroInput = activeLayer === 'macro' && !deepActive;
  return {
    activeLayer,
    deepActive,
    skin: { rendered: true, input: macroInput, owner: macroInput ? 'hand-surface' : null },
    scaffold: { rendered: true, input: false, owner: null },
    evidence: { rendered: true, input: false, owner: null },
    deep: { rendered: deepActive, input: deepActive, owner: deepActive ? 'deep-drill' : null },
  };
}
