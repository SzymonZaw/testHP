(() => {
  'use strict';
  window.testhpHandSurfacePipeline = {
    version: '1.0.0',
    stages: [
      'upload',
      'source',
      'view',
      'preparation',
      'registration',
      'projection'
    ],
    create(assetId) {
      return {
        assetId,
        upload: null,
        source: null,
        view: null,
        preparation: null,
        registration: null,
        projection: null
      };
    }
  };
})();