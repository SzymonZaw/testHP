(() => {
  'use strict';
  if (window.__testhpSpatialImportSelfTestInstalled) return;
  window.__testhpSpatialImportSelfTestInstalled = true;

  const api = window.TestHPSpatialData;
  const results = [];
  const check = (name, pass, detail='') => results.push({name, pass:Boolean(pass), detail});

  if (!api) {
    window.__testhpSpatialImportSelfTest = { ok:false, results:[{name:'Spatial data adapter available',pass:false,detail:'TestHPSpatialData is not loaded'}] };
    return;
  }

  const manifest = {
    schemaVersion:'1.0',
    assetId:'self-test-hand',
    sourceId:'self-test',
    assetUrl:'blob:self-test',
    coordinateSystem:{id:'self-test',units:'mm',axisOrder:'XYZ',orientation:'right-handed'},
    regions:[
      {regionId:'palm',geometryId:'Palm'},
      {regionId:'thumb',geometryId:'Thumb'},
      {regionId:'index',geometryId:'Index'},
      {regionId:'middle',geometryId:'Middle'},
      {regionId:'ring',geometryId:'Ring'},
      {regionId:'little',geometryId:'Little'},
      {regionId:'wrist',geometryId:'Wrist'}
    ]
  };

  const validation = api.validateSpatialManifest(manifest);
  check('Manifest validates', validation.valid, validation.errors?.join('; '));
  const mapping = api.mapGeometryToRegions(manifest);
  check('geometryId → regionId mapping', mapping.valid && mapping.geometryToRegion.Palm === 'palm', mapping.errors?.join('; '));
  const normalized = api.normalizeImportMetadata(manifest, manifest.assetUrl);
  check('Import metadata normalization', normalized.assetId === manifest.assetId);
  check('Required region set', api.REGION_IDS.every(id => normalized.regions.some(r => r.regionId === id)));

  const duplicate = api.validateSpatialManifest({...manifest, regions:[...manifest.regions,{regionId:'palm',geometryId:'Palm2'}]});
  check('Duplicate region rejected', !duplicate.valid && duplicate.errors.some(e => e.includes('duplicate regionId')));

  const invalidCoordinates = api.validateSpatialManifest({...manifest, coordinateSystem:{id:'bad'}});
  check('Incomplete coordinate system rejected', !invalidCoordinates.valid);

  window.__testhpSpatialImportSelfTest = Object.freeze({
    ok: results.every(r => r.pass),
    results: Object.freeze(results)
  });
  window.dispatchEvent(new CustomEvent('testhp:spatial-import-self-test',{detail:window.__testhpSpatialImportSelfTest}));
})();
