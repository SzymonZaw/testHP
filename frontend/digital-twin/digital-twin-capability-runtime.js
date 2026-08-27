(() => {
  'use strict';

  // This registry is a verification surface, not a claim that every stage is
  // clinically validated or fully operational. `contract` means the project
  // has an explicit data/domain contract; `runtime` means a usable endpoint or
  // browser module exists; `ready` is reserved for data actually available at
  // runtime.
  const definitions = [
    [1, 'Data Dictionary', 'contract', 'frontend/digital-twin/hand-data-contract.js'],
    [2, 'Subject / Hand / Timepoint', 'contract', 'backend/data_foundation.py'],
    [3, 'Provenance', 'contract', 'backend/provenance.py'],
    [4, 'Quality / confidence', 'contract', 'backend/data_foundation.py'],
    [5, 'Spatial coordinate system', 'runtime', 'frontend/digital-twin/spatial-contract.js'],
    [6, 'Photo acquisition', 'runtime', 'backend/hand_surface_photo.py'],
    [7, 'Photo calibration', 'runtime', 'backend/hand_camera_calibration.py'],
    [8, 'Anatomical landmarks', 'contract', 'backend/anatomy_foundation.py'],
    [9, 'Segmentation', 'runtime', 'backend/hand_segmentation.py'],
    [10, '3D reconstruction', 'runtime', 'backend/multiview_reconstruction.py'],
    [11, 'MRI / US / other imaging', 'runtime', 'backend/imaging_ingestion.py'],
    [12, 'Anatomical structures', 'contract', 'backend/anatomy_foundation.py'],
    [13, 'Multimodal registration', 'runtime', 'backend/spatial_registration.py'],
    [14, 'Histology', 'runtime', 'backend/tissue_histology.py'],
    [15, 'Tissue segmentation', 'contract', 'backend/anatomy_segmentation.py'],
    [16, 'Tissue pathology', 'contract', 'backend/phase_cd.py'],
    [17, 'Cell segmentation', 'runtime', 'segmentation/cell_segmentation.py'],
    [18, 'Cell identity', 'contract', 'backend/phase_ef.py'],
    [19, 'Cell morphology', 'contract', 'backend/phase_ef.py'],
    [20, 'Cell state', 'contract', 'backend/phase_ef.py'],
    [21, 'scRNA-seq', 'contract', 'backend/phase_ef.py'],
    [22, 'Spatial transcriptomics', 'contract', 'backend/phase_ef.py'],
    [23, 'Proteomics', 'contract', 'backend/phase_ef.py'],
    [24, 'Epigenetics', 'contract', 'backend/phase_ef.py'],
    [25, 'Multi-omics integration', 'contract', 'backend/phase_ef.py'],
    [26, 'Longitudinal comparison', 'runtime', 'backend/longitudinal.py'],
    [27, 'Biological age', 'contract', 'backend/phase_ghi.py'],
    [28, 'Aging trajectory', 'contract', 'backend/phase_ghi.py'],
    [29, 'Disease trajectory', 'contract', 'backend/phase_ghi.py'],
    [30, 'Unified spatial model', 'contract', 'backend/phase_ghi.py'],
    [31, 'Cross-scale navigation', 'contract', 'backend/phase_ghi.py'],
    [32, 'State estimation', 'contract', 'backend/phase_ghi.py'],
    [33, 'Uncertainty', 'contract', 'backend/data_foundation.py'],
    [34, 'What-if simulation', 'contract', 'backend/phase_ghi.py'],
    [35, 'Risk assessment', 'contract', 'backend/phase_ghi.py'],
    [36, 'Intervention support', 'contract', 'backend/phase_ghi.py'],
    [37, 'Validation', 'runtime', 'validation/framework.py'],
    [38, 'Clinical / regulatory', 'contract', 'backend/phase_ghi.py']
  ];

  const state = {
    version: 'capability-registry-v1',
    loadedAt: new Date().toISOString(),
    stages: Object.fromEntries(definitions.map(([id, name, basis, source]) => [
      id,
      { id, name, basis, source, sourceChecked: false, sourceAvailable: null, runtimeReady: false, dataReady: false, notes: [] }
    ])),
    api: { status: false, twin: false, validateHand: false },
    warnings: []
  };

  const stage = id => state.stages[id];
  const setRuntime = (id, ready, note) => {
    const item = stage(id);
    if (!item) return;
    item.runtimeReady = !!ready;
    if (note && !item.notes.includes(note)) item.notes.push(note);
  };

  // Browser-visible modules are checked directly. Backend sources are checked
  // through their corresponding API availability when possible; source files
  // are never executed or treated as proof of biological functionality.
  const browserModules = new Set([
    'frontend/digital-twin/hand-data-contract.js',
    'frontend/digital-twin/spatial-contract.js'
  ]);
  definitions.forEach(([id, , , source]) => {
    if (browserModules.has(source)) {
      stage(id).sourceChecked = true;
      stage(id).sourceAvailable = true;
    }
  });

  const runtime = {
    version: state.version,
    getState() {
      return JSON.parse(JSON.stringify(state));
    },
    validate() {
      const errors = [];
      if (!state.stages[1].sourceAvailable) errors.push('Data Dictionary browser contract is not loaded');
      if (!state.stages[5].sourceAvailable) errors.push('Spatial contract browser module is not loaded');
      return {
        valid: errors.length === 0,
        errors,
        warnings: [...state.warnings],
        api: { ...state.api },
        stageCount: definitions.length
      };
    },
    getStage(id) {
      return stage(id) ? JSON.parse(JSON.stringify(stage(id))) : null;
    },
    list() {
      return definitions.map(([id]) => JSON.parse(JSON.stringify(stage(id))));
    },
    refresh: async () => {
      const checks = [
        ['/api/status', 'status'],
        ['/api/hand/twin?subject_id=own_cohort', 'twin'],
        ['/api/hand/validate', 'validateHand']
      ];
      await Promise.all(checks.map(async ([url, key]) => {
        try {
          const response = await fetch(url, { cache: 'no-store' });
          state.api[key] = response.ok;
        } catch (_) {
          state.api[key] = false;
        }
      }));

      setRuntime(2, state.api.status, 'subject/hand/timepoint API reachable');
      setRuntime(5, !!window.testhpSpatialContract, 'browser spatial contract loaded');
      setRuntime(6, state.api.validateHand, 'hand validation endpoint reachable');
      setRuntime(10, !!window.PhotoReconstruction3D, 'photo reconstruction browser module loaded');
      setRuntime(26, state.api.twin, 'twin endpoint reachable');
      state.stages[1].runtimeReady = !!window.testhpHandDataContract;
      state.stages[1].dataReady = !!window.testhpHandDataContract;
      state.stages[5].dataReady = !!window.testhpSpatialContract;
      state.loadedAt = new Date().toISOString();
      window.dispatchEvent(new CustomEvent('testhp:capabilities-refreshed', { detail: runtime.getState() }));
      return runtime.getState();
    }
  };

  // Compatibility aliases make the old console probe useful without claiming
  // that the object itself means the stage is implemented end-to-end.
  const aliases = {
    1: '__testhpDataDictionary', 2: '__testhpSubject', 3: '__testhpProvenance',
    4: '__testhpQuality', 5: '__testhpSpatialCoordinateSystem', 6: '__testhpPhotoAcquisition',
    7: '__testhpPhotoCalibration', 8: '__testhpLandmarks', 9: '__testhpSegmentation',
    10: '__testhpReconstruction', 11: '__testhpImaging', 12: '__testhpAnatomy',
    13: '__testhpMultimodalRegistration', 14: '__testhpHistology', 15: '__testhpTissueSegmentation',
    16: '__testhpTissuePathology', 17: '__testhpCellSegmentation', 18: '__testhpCellIdentity',
    19: '__testhpCellMorphology', 20: '__testhpCellState', 21: '__testhpScRNA',
    22: '__testhpSpatialTranscriptomics', 23: '__testhpProteomics', 24: '__testhpEpigenetics',
    25: '__testhpMultiOmics', 26: '__testhpLongitudinal', 27: '__testhpBiologicalAge',
    28: '__testhpAgingTrajectory', 29: '__testhpDiseaseTrajectory', 30: '__testhpUnifiedSpatialModel',
    31: '__testhpCrossScaleNavigation', 32: '__testhpStateEstimation', 33: '__testhpUncertainty',
    34: '__testhpWhatIf', 35: '__testhpRiskAssessment', 36: '__testhpInterventionSupport',
    37: '__testhpValidation', 38: '__testhpClinicalRegulatory'
  };

  Object.entries(aliases).forEach(([id, name]) => {
    window[name] = stage(Number(id));
  });
  window.__testhpDigitalTwinCapabilities = runtime;
  window.__testhpHandDataRuntime = runtime;
  window.__testhpHandDataContract = window.__testhpDataDictionary;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => runtime.refresh(), { once: true });
  } else {
    runtime.refresh();
  }
})();
