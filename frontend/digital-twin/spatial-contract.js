(() => {
  const SEGMENT_RE=/[^a-z0-9_-]+/gi; const LEVELS=new Set(['macro','tissue','cellular','molecular','cell']);
  const normalizeSegment=value=>String(value??'').trim().toLowerCase().replaceAll(' ','-').replace(SEGMENT_RE,'-');
  const normalizeId=value=>String(value??'').split('/').map(normalizeSegment).filter(Boolean).join('/');
  const buildSpatialId=path=>(Array.isArray(path)?path:[]).map(item=>typeof item==='string'?item:item?.id).map(normalizeSegment).filter(Boolean).join('/');
  const relation=(selectedId,candidateId)=>{const selected=normalizeId(selectedId),candidate=normalizeId(candidateId);if(!selected||!candidate)return'unknown';if(candidate===selected)return'direct';if(candidate.startsWith(`${selected}/`))return'descendant';if(selected.startsWith(`${candidate}/`))return'ancestor';const parent=selected.includes('/')?selected.slice(0,selected.lastIndexOf('/')):'';if(parent&&candidate.startsWith(`${parent}/`)&&candidate.split('/').length===selected.split('/').length)return'sibling';return'other'};
  const inScope=(selectedId,candidateId,includeDescendants=false)=>{const r=relation(selectedId,candidateId);return r==='direct'||(includeDescendants&&r==='descendant')};
  const scope=(selectedId,ids,includeDescendants=false)=>(Array.isArray(ids)?ids:[]).filter(id=>inScope(selectedId,id,includeDescendants));
  const normalizeTarget=detail=>{const source=detail||{},path=Array.isArray(source.path)?source.path.map(String):[],spatialId=normalizeId(source.spatial_id||buildSpatialId(path)||source.id||'hand'),segments=spatialId.split('/').filter(Boolean),rawLevel=String(source.level||'').toLowerCase(),level=LEVELS.has(rawLevel)?rawLevel:rawLevel==='single cell'?'cell':rawLevel||'macro';return Object.freeze({spatial_id:spatialId,id:normalizeSegment(source.id||segments.at(-1)||'hand'),label:source.target||source.label||path.at(-1)||segments.at(-1)||'Hand',level,path:path.length?path:segments,parent_spatial_id:segments.length>1?segments.slice(0,-1).join('/'):null,children:Array.isArray(source.children)?source.children:[]})};
  let current=normalizeTarget({spatial_id:'hand',id:'hand',target:'Hand',level:'macro',path:['Hand']});
  const publish=detail=>{current=normalizeTarget(detail);window.selectedSpatialNode=current;window.spatialEvidenceTarget=current;window.testhpSpatialTarget=current;window.dispatchEvent(new CustomEvent('testhp:spatial-contract-changed',{detail:current}));return current};
  window.testhpSpatialContract=Object.freeze({normalizeId,buildSpatialId,relation,inScope,scope,getTarget:()=>current,publish,LEVELS:[...LEVELS]});
  window.addEventListener('testhp:spatial-layer-changed',event=>publish(event.detail||{}));
  window.addEventListener('testhp:spatial-contract-request',event=>event?.detail?.callback?.(current));
  publish(current);
})();
