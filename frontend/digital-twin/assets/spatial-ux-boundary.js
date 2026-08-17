const badge=document.getElementById('spatial-level-badge');
const inspector=document.querySelector('.inspector');
const macroRow=document.querySelector('.inspector .macro-row');
const tissueState=document.getElementById('tissue-state');
const tissueDetail=document.getElementById('tissue-detail');
const tissueStatus=document.getElementById('tissue-status');
const cellularState=document.getElementById('cellular-state');
const cellularDetail=document.getElementById('cellular-detail');
const cellularStatus=document.getElementById('cellular-status');
const molecularState=document.getElementById('molecular-state');
const molecularDetail=document.getElementById('molecular-detail');
const molecularStatus=document.getElementById('molecular-status');
const macroState=document.getElementById('macro-state');
const macroDetail=document.getElementById('macro-detail');
const macroStatus=document.getElementById('macro-status');
const evidenceLevel=document.getElementById('evidence-level');
const confidence=document.getElementById('confidence-state');
const style=document.createElement('style');
style.textContent=`body.spatial-deep .inspector{display:none}body.spatial-deep .workspace{grid-template-columns:1fr}body.spatial-deep .twin-panel{width:100%}body.spatial-deep .spatial-navigator{background:#f8fafb}body.spatial-deep .spatial-navigator .spatial-note{max-width:760px}body.spatial-deep .state-panel{margin-top:16px}`;
document.head.appendChild(style);
function level(){return String(badge?.textContent||'MACRO').trim().toLowerCase()}
function set(el,text){if(el)el.textContent=text}
function sync(){
 const l=level();
 const deep=!l.includes('macro');
 document.body.classList.toggle('spatial-deep',deep);
 if(macroRow)macroRow.hidden=false;
 if(deep){
   set(macroState,'Not shown at this resolution');
   set(macroStatus,'PARENT');
   set(macroDetail,'Parent macro evidence exists, but is not displayed as evidence for this deeper spatial target.');
   set(tissueState,l.includes('tissue')?'No evidence at this resolution':'No tissue evidence at this spatial target');
   set(tissueStatus,'NONE');
   set(tissueDetail,l.includes('tissue')?'No tissue / WSI evidence is linked to this exact target. The target remains navigation-only.':'No tissue evidence is linked to this exact spatial target.');
   set(cellularState,l.includes('cellular')?'No evidence at this resolution':'No cellular evidence at this spatial target');
   set(cellularStatus,'NONE');
   set(cellularDetail,l.includes('cellular')?'No cellular evidence is linked to this exact microscopy field. The target remains navigation-only.':'No cellular evidence is linked to this exact spatial target.');
   set(molecularState,'No molecular evidence at this spatial target');
   set(molecularStatus,'NONE');
   set(molecularDetail,'No molecular measurements are explicitly linked to this spatial target.');
   set(confidence,'Navigation only');
   set(evidenceLevel,`No evidence at ${badge?.textContent||'this resolution'}`);
 } else {
   set(macroDetail,'Registered hand images are available only as macro-resolution evidence for the selected region.');
 }
}
if(badge){new MutationObserver(sync).observe(badge,{childList:true,characterData:true,subtree:true});sync();}
