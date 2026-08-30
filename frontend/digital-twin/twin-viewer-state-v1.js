/* 3D twin viewer state bridge. Rendering stays in the existing viewer; this owns semantic status. */
(function(){
  'use strict';
  const STATUS=['healthy','at_risk','diseased','unknown'];
  const palette={healthy:0x3fb950,at_risk:0xd29922,diseased:0xf85149,unknown:0x586174};
  function normalizeStatus(value){const s=String(value||'unknown').toLowerCase().replaceAll(' ','_');return STATUS.includes(s)?s:'unknown';}
  function colorFor(status){return palette[normalizeStatus(status)];}
  function regionSummary(region, analysis){
    const r=region||{}; const a=analysis||{};
    return {id:r.id||r.region_id||'unknown',label:r.label||r.name||r.id||'Unknown',status:normalizeStatus(r.status||r.health_state),age:r.biological_age??r.age??null,evidence:Array.isArray(r.evidence)?r.evidence:[],cells:r.cell_count??null};
  }
  window.TestHPTwinViewerState={normalizeStatus,colorFor,regionSummary};
})();
