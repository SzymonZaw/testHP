import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

const subjectId = 'own_cohort';
const timepoint = 'T0';
const viewport = document.getElementById('twin-viewport');
const canvas = document.getElementById('twin-canvas');
const loading = document.getElementById('viewer-loading');
const dialog = document.getElementById('observation-dialog');
let analysis = null;
let selectedRegion = 'palm';
const regionMeshes = new Map();

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(viewport.clientWidth, viewport.clientHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);
const camera = new THREE.PerspectiveCamera(32, viewport.clientWidth / viewport.clientHeight, 0.1, 100);
camera.position.set(0, 1.5, 8.5);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enablePan = true;
controls.minDistance = 4;
controls.maxDistance = 15;
controls.target.set(0, 0.4, 0);

scene.add(new THREE.HemisphereLight(0xffffff, 0x172033, 2.2));
const key = new THREE.DirectionalLight(0xffffff, 2.8);
key.position.set(4, 6, 7);
scene.add(key);
const fill = new THREE.DirectionalLight(0x8bb8ff, 1.0);
fill.position.set(-5, 2, -4);
scene.add(fill);

const root = new THREE.Group();
root.rotation.x = -0.18;
scene.add(root);

const normalMaterial = new THREE.MeshStandardMaterial({ color: 0xc68b72, roughness: 0.72, metalness: 0.02 });
const selectedMaterial = new THREE.MeshStandardMaterial({ color: 0x66b3ff, roughness: 0.58, metalness: 0.02, emissive: 0x0b2745, emissiveIntensity: 0.35 });
const reviewMaterial = new THREE.MeshStandardMaterial({ color: 0xd6a64f, roughness: 0.68 });
const unavailableMaterial = new THREE.MeshStandardMaterial({ color: 0x586174, roughness: 0.9 });

function capsule(name, position, radius, length, rotation = [0, 0, 0]) {
  const geometry = new THREE.CapsuleGeometry(radius, length, 8, 16);
  const mesh = new THREE.Mesh(geometry, normalMaterial.clone());
  mesh.name = name;
  mesh.position.set(...position);
  mesh.rotation.set(...rotation);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  root.add(mesh);
  regionMeshes.set(name, mesh);
  return mesh;
}

// Anatomical zones are spatial components, not diagnostic segmentation.
capsule('wrist', [0, -2.15, 0], 0.72, 1.25);
capsule('palm', [0, -0.35, 0], 1.55, 2.25);
capsule('thumb', [-1.45, 0.0, 0.02], 0.48, 1.45, [0, 0, -0.82]);
capsule('index', [-1.05, 1.95, 0], 0.43, 2.15);
capsule('middle', [-0.35, 2.25, 0], 0.46, 2.55);
capsule('ring', [0.42, 2.12, 0], 0.45, 2.32);
capsule('little', [1.12, 1.86, 0], 0.40, 1.95, [0, 0, 0.08]);

const jointMaterial = new THREE.MeshStandardMaterial({ color: 0xb87962, roughness: 0.75 });
for (const [region, points] of Object.entries({ index: [-1.05, 2.45], middle: [-0.35, 2.85], ring: [0.42, 2.68], little: [1.12, 2.32] })) {
  for (const y of [points[1] - 0.55, points[1] - 1.12]) {
    const joint = new THREE.Mesh(new THREE.SphereGeometry(region === 'little' ? 0.40 : 0.43, 16, 12), jointMaterial.clone());
    joint.position.set(points[0], y, 0);
    joint.name = `${region}-joint`;
    root.add(joint);
  }
}

function evidenceStatus(region) {
  const assets = analysis?.assets || [];
  const macro = assets.some(a => a.modality === 'hand' && a.status === 'available' && (a.view === region || region === 'palm'));
  const tissue = assets.some(a => ['wsi', 'images'].includes(a.modality) && a.status === 'available');
  const molecular = assets.some(a => ['rna', 'metadata'].includes(a.modality) && a.status === 'available');
  return { macro, tissue, cellular: tissue && false, molecular };
}

function materialFor(region) {
  const status = evidenceStatus(region);
  if (!status.macro && !status.tissue && !status.molecular) return unavailableMaterial.clone();
  if (!status.macro || (!status.tissue && status.molecular)) return reviewMaterial.clone();
  return normalMaterial.clone();
}

function refreshMaterials() {
  for (const [region, mesh] of regionMeshes) mesh.material = materialFor(region);
  selectRegion(selectedRegion, false);
}

function selectRegion(region, focus = true) {
  if (!regionMeshes.has(region)) return;
  selectedRegion = region;
  for (const [id, mesh] of regionMeshes) {
    mesh.material = materialFor(id);
    if (id === region) mesh.material = selectedMaterial.clone();
  }
  document.getElementById('zone-label').textContent = region;
  document.getElementById('form-region').value = region;
  const status = evidenceStatus(region);
  document.getElementById('macro-state').textContent = status.macro ? 'Available' : 'Unavailable';
  document.getElementById('macro-detail').textContent = status.macro ? 'Registered hand image evidence is available for this region.' : 'No region-linked hand image is currently available.';
  document.getElementById('tissue-state').textContent = status.tissue ? 'Available / review' : 'Unavailable';
  document.getElementById('tissue-detail').textContent = status.tissue ? 'Tissue-level artifacts exist in the project; region linkage is not assumed without explicit metadata.' : 'No tissue / WSI evidence registered for this region.';
  document.getElementById('cellular-state').textContent = 'Unavailable';
  document.getElementById('cellular-detail').textContent = 'Cellular conclusions require microscopy / cellular data explicitly linked to this region.';
  document.getElementById('molecular-state').textContent = status.molecular ? 'Available / unlinked' : 'Unavailable';
  document.getElementById('molecular-detail').textContent = status.molecular ? 'Molecular files exist, but no subject/region link is inferred automatically.' : 'No molecular measurements are linked to this region.';
  document.getElementById('confidence-state').textContent = status.macro ? 'Observed input' : 'No evidence';
  document.getElementById('evidence-level').textContent = status.macro ? 'Macro / observed data' : 'Availability only';
  if (focus) {
    controls.target.set(0, region === 'wrist' ? -1.2 : region === 'palm' ? -0.35 : 1.3, 0);
    controls.update();
  }
}

async function refreshAnalysis() {
  try {
    const response = await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    analysis = await response.json();
    const c = analysis.coverage || {};
    document.getElementById('coverage-macro').textContent = `Macro ${c.macro ?? 0}%`;
    document.getElementById('coverage-tissue').textContent = `Tissue ${c.micro ?? 0}%`;
    document.getElementById('coverage-cellular').textContent = `Cellular ${c.micro ?? 0}%`;
    document.getElementById('coverage-molecular').textContent = `Molecular ${c.molecular ?? 0}%`;
    document.getElementById('twin-status').textContent = 'Evidence loaded';
    refreshMaterials();
  } catch (error) {
    document.getElementById('twin-status').textContent = 'Evidence unavailable';
  } finally {
    loading.remove();
  }
}

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
canvas.addEventListener('click', event => {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects([...regionMeshes.values()], false);
  if (hits.length) selectRegion(hits[0].object.name);
});

function resetView() {
  camera.position.set(0, 1.5, 8.5);
  controls.target.set(0, 0.4, 0);
  controls.update();
}
document.getElementById('reset-view').onclick = resetView;
document.getElementById('rotate-left').onclick = () => { root.rotation.y -= Math.PI / 9; };
document.getElementById('rotate-right').onclick = () => { root.rotation.y += Math.PI / 9; };
document.getElementById('zoom-in').onclick = () => { camera.position.multiplyScalar(0.86); controls.update(); };
document.getElementById('zoom-out').onclick = () => { camera.position.multiplyScalar(1.16); controls.update(); };
document.getElementById('zoom-region').onclick = () => { camera.position.multiplyScalar(0.84); controls.update(); };
document.getElementById('deep-analysis').onclick = () => {
  const status = evidenceStatus(selectedRegion);
  const message = status.tissue ? `Deep analysis for ${selectedRegion}: tissue-level evidence exists, but cellular interpretation is not enabled without explicit microscopy linkage.` : `Deep analysis for ${selectedRegion}: no tissue/cellular evidence is currently available. The system will not invent it.`;
  alert(message);
};
document.getElementById('add-observation').onclick = () => dialog.showModal();
document.querySelector('.close').onclick = () => dialog.close();

document.getElementById('register-observation').onclick = async event => {
  event.preventDefault();
  const file = document.getElementById('observation-file').files[0];
  if (!file) return;
  const modality = document.getElementById('form-modality').value;
  const endpoint = { Photo: 'hand', Video: 'video', Microscopy: 'wsi', Measurements: 'metadata', 'Molecular data': 'rna' }[modality];
  const body = new FormData();
  body.append('file', file); body.append('subject_id', subjectId); body.append('timepoint', timepoint); body.append('view', selectedRegion);
  const button = document.getElementById('register-observation');
  button.disabled = true; button.textContent = 'Registering…';
  try {
    const response = await fetch(`/api/upload/${endpoint}`, { method: 'POST', body });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Upload failed');
    dialog.close();
    await refreshAnalysis();
    alert(`Observation registered for ${selectedRegion}. Biological inference is not established automatically.`);
  } catch (error) { alert(error.message); } finally { button.disabled = false; button.textContent = 'Register observation'; }
};

function resize() {
  const w = viewport.clientWidth, h = viewport.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);
function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }
resize(); animate(); selectRegion('palm', false); refreshAnalysis();
