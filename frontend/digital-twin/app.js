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
    const response = await fetch('/api/hand/twin?subject_id=' + encodeURIComponent(subjectId));
    if (!response.ok) return;
    const twin = await response.json();
    document.querySelector('.coverage b:nth-of-type(1)').textContent = `Macro ${twin.coverage?.macro ?? 100}%`;
  } catch (_) {
    // The visual prototype remains usable when the API is unavailable.
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
  button.textContent = 'Registering…';
  try {
    const response = await fetch(`/api/upload/${endpoint}`, { method: 'POST', body });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Upload failed');
    dialog.close();
    button.textContent = 'Register observation';
    alert(`Observation registered: ${result.asset.asset_id}`);
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
