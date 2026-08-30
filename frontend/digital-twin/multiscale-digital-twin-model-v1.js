/* Canonical end-user model: one hand, multiple scales, explicit uncertainty. */
(function(){
  'use strict';
  const SCALES=['hand','region','tissue','cell','molecular'];
  function create(input={}){
    return {schema_version:'digital_twin_v1',subject_id:input.subject_id||null,timepoint:input.timepoint||null,scales:{hand:input.hand||null,region:input.regions||[],tissue:input.tissues||[],cell:input.cells||[],molecular:input.molecular||{}},evidence:input.evidence||{},uncertainty:input.uncertainty||{},interventions:input.interventions||[]};
  }
  function availability(model){const m=model||{};return SCALES.reduce((out,k)=>{const v=m.scales?.[k];out[k]=Array.isArray(v)?v.length>0:!!v&&Object.keys(v).length>0;return out;},{});}
  window.TestHPDigitalTwinModel={SCALES,create,availability};
})();
