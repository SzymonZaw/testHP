(() => {
  'use strict';
  const BOOT_KEY = '__testhpHandSurfaceArchitectureModeBridgeBooted';
  if (window[BOOT_KEY]) return;
  window[BOOT_KEY] = true;

  const API = '/api/hand/photo-reconstruction';
  const architecture = () => window.testhpHandSurfaceArchitecture;

  async function loadArchitecture() {
    if (architecture()) return architecture();
    if (window.__testhpHandSurfaceArchitectureLoad) return window.__testhpHandSurfaceArchitectureLoad;
    return new Promise(resolve => {
      const script = document.getElementById('hand-surface-architecture-v1');
      if (!script) { resolve(null); return; }
      const done = () => resolve(architecture() || null);
      if (architecture()) done(); else script.addEventListener('load', done, {once:true});
    });
  }

  async function syncState() {
    const api = await loadArchitecture();
    if (!api) return null;
    try {
      const response = await fetch(`${API}/state?subject_id=own_cohort&timepoint=T0&spatial_id=hand`, {cache:'no-store'});
      if (!response.ok) return null;
      const state = await response.json();
      const evidence = Array.isArray(state.evidence) ? state.evidence : [];
      const sources = api.summarizeEvidence(evidence).sources;
      api.registerLayer('macro', {
        spatial_id: 'hand',
        geometry: {kind:'classic-geometry', layer:'macro', status:'available', provenance:'canonical-macro-model'},
        sources
      });
      return api.setEvidenceSnapshot({evidence, analysis:null});
    } catch (error) {
      console.warn('[hand-surface-architecture]', error);
      return null;
    }
  }

  window.addEventListener('testhp:hand-geometry-mode-changed', event => {
    const mode = event.detail?.mode;
    if (mode === 'classic' || mode === 'real') architecture()?.setMode(mode);
  });
  window.addEventListener('testhp:evidence-updated', () => void syncState());
  window.addEventListener('testhp:evidence-attached', () => void syncState());
  window.addEventListener('testhp:viewport-manager-ready', () => void syncState());
  window.addEventListener('testhp:spatial-layer-changed', () => void syncState());

  void syncState();
  window.testhpHandSurfaceArchitectureModeBridge = {version:'1.0.0', syncState};
})();
