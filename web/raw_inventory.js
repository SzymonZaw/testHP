// Complete data/raw inventory: includes manually placed files and frontend uploads.
const rawInventoryEsc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function refreshRawInventory() {
  const response = await fetch('/api/ingestion/assets');
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const data = await response.json();
  const assets = data.assets || [];
  const summary = document.getElementById('asset-summary');
  const table = document.getElementById('asset-table');
  const empty = document.getElementById('asset-empty');
  if (!summary || !table || !empty) return;

  summary.innerHTML = `
    <div><strong>${data.raw_count || 0}</strong><span>raw files</span></div>
    <div><strong>${data.raw_available || 0}</strong><span>available</span></div>
    <div><strong>${data.unavailable || 0}</strong><span>unavailable / empty</span></div>
    <div><strong>${data.uploaded_count || 0}</strong><span>frontend uploads</span></div>
  `;

  if (!assets.length) {
    table.innerHTML = '';
    empty.hidden = false;
    empty.textContent = 'No files are currently present in data/raw.';
    return;
  }

  empty.hidden = true;
  table.innerHTML = assets.map(asset => `
    <tr>
      <td><strong>${rawInventoryEsc(asset.subject_id)}</strong></td>
      <td>${rawInventoryEsc(asset.timepoint)}</td>
      <td>${rawInventoryEsc(asset.modality)}</td>
      <td>${rawInventoryEsc(asset.subtype || '—')}</td>
      <td>${rawInventoryEsc(asset.view || '—')}</td>
      <td><strong>${rawInventoryEsc(asset.filename)}</strong><small class="asset-path">${rawInventoryEsc(asset.path)}</small></td>
      <td>${formatUploadBytes(asset.size_bytes)}</td>
      <td><span class="status ${asset.status === 'available' ? 'ok' : 'unavailable'}">${asset.status === 'available' ? 'Available' : 'Unavailable'}</span><small class="asset-source">${asset.source === 'upload' ? 'Frontend upload' : 'Existing raw input'}</small></td>
    </tr>
  `).join('');
}

const rawInventoryRefresh = document.getElementById('refresh-assets');
if (rawInventoryRefresh) rawInventoryRefresh.onclick = () => refreshRawInventory().catch(error => {
  const empty = document.getElementById('asset-empty');
  empty.hidden = false;
  empty.textContent = `Could not load raw inventory: ${error.message}`;
});

window.refreshRawInventory = refreshRawInventory;
refreshRawInventory().catch(() => {});
