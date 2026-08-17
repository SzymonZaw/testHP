const dmEsc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dmPretty = (value) => String(value ?? '').replaceAll('_', ' ');

async function loadManagedDatasets() {
  const response = await fetch('/api/datasets');
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const data = await response.json();
  const datasets = data.registry || [];
  const list = document.getElementById('managed-datasets');
  const select = document.getElementById('upload-dataset');
  const current = select.value;
  select.innerHTML = '<option value="">Select a managed dataset…</option>' + datasets.map(d => `<option value="${dmEsc(d.dataset_id)}">${dmEsc(d.name)} · ${dmEsc(d.modality)} · ${dmEsc(d.dataset_id)}</option>`).join('');
  if (datasets.some(d => d.dataset_id === current)) select.value = current;
  list.innerHTML = datasets.map(d => `<article class="managed-dataset"><div><strong>${dmEsc(d.name)}</strong><span>${dmEsc(d.dataset_id)} · v${dmEsc(d.version)} · ${dmEsc(d.modality)}</span></div><div class="managed-dataset-meta"><span>${d.available_files || 0} available</span><span>${d.empty_files || 0} empty</span><span>${dmEsc(d.status)}</span></div><small>${dmEsc(d.root_path)}</small><p>${dmEsc(d.description || 'No description provided.')}</p></article>`).join('') || '<div class="asset-empty">No managed datasets yet. Create the first dataset above.</div>';
  const status = document.getElementById('dataset-manager-status');
  status.textContent = `${datasets.length} managed dataset${datasets.length === 1 ? '' : 's'}`;
  status.className = 'badge ok';
}

async function createManagedDataset(event) {
  event.preventDefault();
  const button = event.target.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const tags = document.getElementById('dataset-tags').value.split(',').map(x => x.trim()).filter(Boolean);
    const payload = {
      name: document.getElementById('dataset-name').value,
      modality: document.getElementById('dataset-modality').value,
      version: document.getElementById('dataset-version').value || '1.0',
      source: document.getElementById('dataset-source').value,
      description: document.getElementById('dataset-description').value,
      tags,
    };
    const response = await fetch('/api/datasets', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `${response.status} ${response.statusText}`);
    document.getElementById('dataset-create-result').innerHTML = `<div class="upload-success"><strong>Dataset created</strong><span>${dmEsc(data.dataset.dataset_id)} · ${dmEsc(data.dataset.name)}</span><small>Its manifest is ready. Add files through the dataset upload form below.</small></div>`;
    event.target.reset();
    document.getElementById('dataset-version').value = '1.0';
    await loadManagedDatasets();
    document.getElementById('upload-dataset').value = data.dataset.dataset_id;
    if (typeof window.refreshDashboard === 'function') await window.refreshDashboard();
  } catch (error) {
    document.getElementById('dataset-create-result').textContent = error.message;
    document.getElementById('dataset-manager-status').textContent = 'Create failed';
    document.getElementById('dataset-manager-status').className = 'badge warning';
  } finally { button.disabled = false; }
}

document.getElementById('dataset-form').onsubmit = createManagedDataset;
loadManagedDatasets().catch(error => { document.getElementById('dataset-manager-status').textContent = `Unavailable: ${error.message}`; document.getElementById('dataset-manager-status').className = 'badge warning'; });
window.refreshManagedDatasets = loadManagedDatasets;
