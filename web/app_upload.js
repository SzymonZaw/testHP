// Upload helper for the research dashboard.
async function uploadAsset(event) {
  event.preventDefault();
  const form = event.target;
  const button = form.querySelector('button[type="submit"]');
  const file = document.getElementById('upload-file').files[0];
  if (!file) return;
  button.disabled = true;
  try {
    const modality = document.getElementById('upload-modality').value;
    const body = new FormData();
    body.append('file', file);
    body.append('subject_id', document.getElementById('upload-subject').value);
    body.append('timepoint', document.getElementById('upload-timepoint').value);
    body.append('subtype', document.getElementById('upload-subtype').value);
    body.append('view', document.getElementById('upload-view').value);
    const response = await fetch(`/api/upload/${encodeURIComponent(modality)}`, { method: 'POST', body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `${response.status} ${response.statusText}`);
    document.getElementById('upload-status').textContent = 'Uploaded';
    document.getElementById('upload-status').className = 'badge ok';
    document.getElementById('upload-result').textContent = `Stored ${data.asset.filename} as ${data.asset.path}`;
    document.getElementById('upload-file').value = '';
  } catch (error) {
    document.getElementById('upload-status').textContent = 'Upload failed';
    document.getElementById('upload-status').className = 'badge warning';
    document.getElementById('upload-result').textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

document.getElementById('upload-form').onsubmit = uploadAsset;
