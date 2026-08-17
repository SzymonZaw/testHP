const dialog = document.getElementById('observation-dialog');
const addObservation = document.getElementById('add-observation');
const zoneLabel = document.getElementById('zone-label');
const form = document.querySelector('#observation-dialog form');
const fileInput = form.querySelector('input[type="file"]');
const selects = form.querySelectorAll('select');
const subjectId = 'own_cohort';
let selectedZone = '05';

async function refreshTwin() {
  try {
    const response = await fetch('/api/hand/analysis?subject_id=' + encodeURIComponent(subjectId) + '&timepoint=T0');
    if (!response.ok) return;
    const result = await response.json();
    const coverage = result.coverage || {};
    document.querySelector('.coverage b:nth-of-type(1)').textContent = `Macro ${coverage.macro ?? 0}%`;
    document.querySelector('.coverage b:nth-of-type(2)').textContent = `Micro ${coverage.micro ?? 0}%`;
    document.querySelector('.coverage b:nth-of-type(3)').textContent = `Molecular ${coverage.molecular ?? 0}%`;
  } catch (_) {
    // Keep the research view usable when the API is unavailable.
  }
}

addObservation.addEventListener('click', () => dialog.showModal());

document.querySelectorAll('.zone').forEach((zone) => {
  zone.addEventListener('click', () => {
    document.querySelectorAll('.zone').forEach((item) => item.classList.remove('selected'));
    zone.classList.add('selected');
    selectedZone = zone.textContent.trim();
    zoneLabel.textContent = `Zone ${selectedZone}`;
    selects[1].value = selectedZone;
  });
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) {
    alert('Select at least one file.');
    return;
  }
  const modality = selects[2].value;
  const endpoint = modality === 'Photo' ? 'hand' : modality === 'Video' ? 'video' : modality === 'Microscopy' ? 'wsi' : modality === 'Molecular data' ? 'rna' : 'metadata';
  const body = new FormData();
  body.append('file', file);
  body.append('subject_id', subjectId);
  body.append('timepoint', 'T0');
  body.append('view', `zone-${selectedZone}`);
  const button = form.querySelector('.primary');
  button.disabled = true;
  button.textContent = 'Analyzing…';
  try {
    const response = await fetch(`/api/upload/${endpoint}`, { method: 'POST', body });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Upload failed');
    dialog.close();
    button.textContent = 'Register observation';
    const level = result.analysis?.analysis_level || 'ingestion_quality';
    alert(`Observation registered: ${result.asset.asset_id}\nAnalysis: ${level}\nBiological inference: not established`);
    await refreshTwin();
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = 'Register observation';
  }
});

document.querySelector('.close').addEventListener('click', () => dialog.close());
refreshTwin();
