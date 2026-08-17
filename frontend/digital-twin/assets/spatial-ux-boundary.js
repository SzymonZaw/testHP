const badge=document.getElementById('spatial-level-badge');
const style=document.createElement('style');
style.textContent=`body.spatial-deep .inspector,body.spatial-deep .state-panel{display:none!important}body.spatial-deep .workspace{grid-template-columns:1fr!important}body.spatial-deep .twin-panel{width:100%!important}body.spatial-deep .spatial-navigator{background:#f8fafb}`;
document.head.appendChild(style);
function level(){return String(badge?.textContent||'MACRO').trim().toLowerCase()}
function set(el,text){if(el)el.textContent=text}
function sync(){
 const l=level();
 const deep=!l.includes('macro');
 document.body.classList.toggle('spatial-deep',deep);
 const inspector=document.querySelector('.inspector');
 const statePanel=document.querySelector('.state-panel');
 if(inspector)inspector.style.setProperty('display',deep?'none':'flex','important');
 if(statePanel)statePanel.style.setProperty('display',deep?'none':'block','important');
 if(!deep)return;
 set(document.getElementById('macro-state'),'Not shown at this resolution');
 set(document.getElementById('macro-status'),'PARENT');
 set(document.getElementById('macro-detail'),'Parent macro evidence exists, but is not displayed as evidence for this deeper spatial target.');
 set(document.getElementById('tissue-state'),l.includes('tissue')?'No evidence at this resolution':'No tissue evidence at this spatial target');
 set(document.getElementById('tissue-status'),'NONE');
 set(document.getElementById('tissue-detail'),l.includes('tissue')?'No tissue / WSI evidence is linked to this exact target. The target remains navigation-only.':'No tissue evidence is linked to this exact spatial target.');
 set(document.getElementById('cellular-state'),l.includes('cellular')?'No evidence at this resolution':'No cellular evidence at this spatial target');
 set(document.getElementById('cellular-status'),'NONE');
 set(document.getElementById('cellular-detail'),l.includes('cellular')?'No cellular evidence is linked to this exact microscopy field. The target remains navigation-only.':'No cellular evidence is linked to this exact spatial target.');
 set(document.getElementById('molecular-state'),'No molecular evidence at this spatial target');
 set(document.getElementById('molecular-status'),'NONE');
 set(document.getElementById('molecular-detail'),'No molecular measurements are explicitly linked to this spatial target.');
 set(document.getElementById('confidence-state'),'Navigation only');
 set(document.getElementById('evidence-level'),`No evidence at ${badge?.textContent||'this resolution'}`);
}
if(badge){new MutationObserver(sync).observe(badge,{childList:true,characterData:true,subtree:true});}
new MutationObserver(sync).observe(document.body,{childList:true,subtree:true});
sync();
setInterval(sync,250);