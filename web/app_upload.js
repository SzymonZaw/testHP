// Upload helper for the research dashboard.
const uploadEsc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function formatUploadBytes(bytes = 0) { if (!bytes) return '0 B'; const units=['B','KB','MB','GB','TB']; let value=bytes,index=0; while(value>=1024&&index<units.length-1){value/=1024;index+=1;} return `${value.toFixed(index ? 1 : 0)} ${units[index]}`; }

async function loadUploadedAssets() {
  const response = await fetch('/api/ingestion/assets');
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const data = await response.json(); const assets=data.assets||[];
  const table=document.getElementById('asset-table'), empty=document.getElementById('asset-empty'), summary=document.getElementById('asset-summary');
  summary.innerHTML=`<div><strong>${data.count||0}</strong><span>raw assets</span></div><div><strong>${data.available||0}</strong><span>available</span></div><div><strong>${data.unavailable||0}</strong><span>unavailable / empty</span></div>`;
  if(!assets.length){table.innerHTML='';empty.hidden=false;return;}
  empty.hidden=true;
  table.innerHTML=assets.slice().reverse().map(asset=>`<tr><td><strong>${uploadEsc(asset.subject_id)}</strong></td><td>${uploadEsc(asset.timepoint)}</td><td>${uploadEsc(asset.modality)}</td><td>${uploadEsc(asset.subtype||'—')}</td><td>${uploadEsc(asset.view||'—')}</td><td><strong>${uploadEsc(asset.filename)}</strong><small class="asset-path">${uploadEsc(asset.path)}</small></td><td>${formatUploadBytes(asset.size_bytes)}</td><td><span class="status ${asset.status==='available'?'ok':'unavailable'}">${uploadEsc(asset.status)}</span></td></tr>`).join('');
}

async function uploadAsset(event) {
  event.preventDefault(); const form=event.target, button=form.querySelector('button[type="submit"]'), file=document.getElementById('upload-file').files[0]; if(!file) return; button.disabled=true;
  try {
    const modality=document.getElementById('upload-modality').value; const datasetId=document.getElementById('upload-dataset').value; let response;
    if(datasetId){
      const body=new FormData(); body.append('file',file); body.append('subject_id',document.getElementById('upload-subject').value); body.append('timepoint',document.getElementById('upload-timepoint').value); body.append('subtype',document.getElementById('upload-subtype').value); body.append('view',document.getElementById('upload-view').value);
      response=await fetch(`/api/datasets/${encodeURIComponent(datasetId)}/upload`,{method:'POST',body});
    } else {
      const body=new FormData(); body.append('file',file); body.append('subject_id',document.getElementById('upload-subject').value); body.append('timepoint',document.getElementById('upload-timepoint').value); body.append('subtype',document.getElementById('upload-subtype').value); body.append('view',document.getElementById('upload-view').value);
      response=await fetch(`/api/upload/${encodeURIComponent(modality)}`,{method:'POST',body});
    }
    const data=await response.json(); if(!response.ok) throw new Error(data.detail||`${response.status} ${response.statusText}`);
    const asset=data.asset||data.file; const path=asset.path;
    document.getElementById('upload-status').textContent=asset.status==='available'?'Added to dataset':'Added but unavailable'; document.getElementById('upload-status').className=`badge ${asset.status==='available'?'ok':'warning'}`;
    document.getElementById('upload-result').innerHTML=`<div class="upload-success"><strong>${datasetId?'Added to managed dataset':'Stored in raw data'}</strong><span>${uploadEsc(path)}</span><small>${datasetId?`Manifest ${uploadEsc(data.dataset.dataset_id)} has been refreshed.`:'The legacy upload path remains available for compatibility.'}</small></div>`;
    document.getElementById('upload-file').value=''; await loadUploadedAssets(); if(typeof window.refreshManagedDatasets==='function') await window.refreshManagedDatasets(); if(typeof window.refreshDashboard==='function') await window.refreshDashboard();
  } catch(error){ document.getElementById('upload-status').textContent='Upload failed'; document.getElementById('upload-status').className='badge warning'; document.getElementById('upload-result').textContent=error.message; }
  finally {button.disabled=false;}
}

document.getElementById('upload-form').onsubmit=uploadAsset;
document.getElementById('refresh-assets').onclick=async()=>{try{await loadUploadedAssets();}catch(error){document.getElementById('asset-empty').hidden=false;document.getElementById('asset-empty').textContent=`Could not load raw inventory: ${error.message}`;}};
loadUploadedAssets().catch(()=>{});
