(() => {
  const esc = (v) => String(v ?? '').replace(/[&<>\"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;', "'":'&#39;' }[c]));
  const zones = [
    { id: 'wrist', label: 'Wrist', position: [0, -1.8, 0], size: [1.65, 1.5, 0.72], level: 'macro' },
    { id: 'palm', label: 'Palm', position: [0, 0, 0], size: [2.7, 3.2, 0.78], level: 'macro' },
    { id: 'thumb', label: 'Thumb', position: [-2.0, 0.2, 0], size: [1.15, 2.5, 0.72], level: 'macro', rotation: [0, 0, -0.55] },
    { id: 'index', label: 'Index finger', position: [-1.05, 3.0, 0], size: [0.72, 3.25, 0.64], level: 'macro' },
    { id: 'middle', label: 'Middle finger', position: [0, 3.25, 0], size: [0.76, 3.75, 0.66], level: 'macro' },
    { id: 'ring', label: 'Ring finger', position: [1.0, 3.05, 0], size: [0.74, 3.45, 0.65], level: 'macro' },
    { id: 'little', label: 'Little finger', position: [1.85, 2.55, 0], size: [0.66, 2.65, 0.60], level: 'macro' },
    { id: 'thenar', label: 'Thenar region', position: [-1.0, 0.2, 0.45], size: [1.15, 1.55, 0.35], level: 'macro' },
    { id: 'hypothenar', label: 'Hypothenar region', position: [1.0, -0.1, 0.45], size: [1.15, 1.45, 0.35], level: 'macro' },
  ];

  let selected = 'palm';
  let activeLayer = 'macro';
  let scene, camera, renderer, controls, raycaster, pointer;
  const meshes = new Map();

  function addSection() {
    if (document.getElementById('hand-digital-twin-v1')) return document.getElementById('hand-digital-twin-v1');
    const section = document.createElement('section');
    section.id = 'hand-digital-twin-v1';
    section.className = 'card hand-twin-v1';
    section.innerHTML = `
      <div class="section-head">
        <div><span class="eyebrow">HAND · DIGITAL TWIN V1</span><h2>Interactive 3D hand</h2><p class="section-note">Explore anatomical zones in three dimensions. The visualization is a spatial interface to evidence; it does not invent unavailable biological measurements.</p></div>
        <span id="twin-v1-status" class="badge neutral">Loading</span>
      </div>
      <div class="hand-twin-toolbar"><div class="hand-layer-tabs" id="hand-layer-tabs"></div><button id="hand-reset" type="button">Reset view</button></div>
      <div class="hand-twin-layout">
        <div class="hand-3d-panel"><div id="hand-3d-canvas" class="hand-3d-canvas"></div><div class="hand-3d-help">Drag: rotate · Wheel: zoom · Right drag: pan · Click a zone: inspect</div></div>
        <aside class="hand-zone-panel" id="hand-zone-panel"></aside>
      </div>
    `;
    const footer = document.querySelector('footer');
    document.querySelector('main.container').insertBefore(section, footer);
    document.getElementById('hand-reset').onclick = resetView;
    return section;
  }

  function renderTabs(run) {
    const availability = {
      macro: true,
      tissue: Boolean(run?.evidence?.tissue || run?.tissue_available),
      cellular: Boolean(run?.evidence?.cellular || run?.cellular_available),
      molecular: Boolean(run?.evidence?.molecular || run?.molecular_available),
    };
    document.getElementById('hand-layer-tabs').innerHTML = Object.entries(availability).map(([id, available]) => `<button type="button" class="hand-layer-tab ${id === activeLayer ? 'active' : ''}" data-layer="${id}">${id[0].toUpperCase()+id.slice(1)} <span>${available ? 'available' : 'unavailable'}</span></button>`).join('');
    document.querySelectorAll('.hand-layer-tab').forEach((button) => button.onclick = () => { activeLayer = button.dataset.layer; renderTabs(run); renderPanel(run); });
  }

  function makeMesh(THREE, zone, index) {
    const geometry = new THREE.BoxGeometry(...zone.size, 6, 8, 6);
    geometry.translate(0, 0, 0);
    const material = new THREE.MeshStandardMaterial({ color: 0x9aa6b2, roughness: 0.62, metalness: 0.02, transparent: true, opacity: 0.94 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(...zone.position);
    if (zone.rotation) mesh.rotation.set(...zone.rotation);
    mesh.userData.zoneId = zone.id;
    mesh.userData.index = index;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    meshes.set(zone.id, mesh);
    return mesh;
  }

  function buildScene(THREE, OrbitControls) {
    const host = document.getElementById('hand-3d-canvas');
    host.innerHTML = '';
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b1016);
    camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    camera.position.set(0, 2.2, 15);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.setSize(host.clientWidth || 640, host.clientHeight || 560);
    host.appendChild(renderer.domElement);
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.minDistance = 6;
    controls.maxDistance = 28;
    controls.target.set(0, 1, 0);
    raycaster = new THREE.Raycaster();
    pointer = new THREE.Vector2();
    scene.add(new THREE.HemisphereLight(0xdce8f2, 0x26313b, 2.1));
    const key = new THREE.DirectionalLight(0xffffff, 2.8); key.position.set(-5, 7, 10); key.castShadow = true; scene.add(key);
    const rim = new THREE.DirectionalLight(0x9fb5c8, 1.4); rim.position.set(7, 4, -7); scene.add(rim);
    const floor = new THREE.Mesh(new THREE.CircleGeometry(14, 64), new THREE.MeshStandardMaterial({ color: 0x111821, roughness: 0.95 }));
    floor.rotation.x = -Math.PI / 2; floor.position.y = -3.2; floor.receiveShadow = true; scene.add(floor);
    zones.forEach((zone, i) => scene.add(makeMesh(THREE, zone, i)));
    renderer.domElement.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('resize', resize);
    animate();
  }

  function onPointerDown(event) {
    if (!renderer || event.button !== 0) return;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects([...meshes.values()]);
    if (hits.length) { selected = hits[0].object.userData.zoneId; updateSelection(); }
  }

  function updateSelection() {
    meshes.forEach((mesh, id) => {
      const active = id === selected;
      mesh.material.color.setHex(active ? 0x78b7d8 : 0x9aa6b2);
      mesh.material.emissive.setHex(active ? 0x15394c : 0x000000);
      mesh.material.emissiveIntensity = active ? 0.8 : 0;
      mesh.scale.setScalar(active ? 1.035 : 1);
    });
  }

  function renderPanel(run) {
    const zone = zones.find((z) => z.id === selected) || zones[1];
    const layerInfo = {
      macro: ['Macro', 'Available from current hand imagery and geometric observations.', true],
      tissue: ['Tissue', 'Requires tissue-level imaging or WSI associated with this region.', false],
      cellular: ['Cellular', 'Requires microscopy / cellular observations associated with this region.', false],
      molecular: ['Molecular', 'Requires molecular or RNA observations linked to this region.', false],
    }[activeLayer];
    document.getElementById('hand-zone-panel').innerHTML = `
      <div class="zone-panel-head"><span class="eyebrow">SELECTED ZONE</span><h3>${esc(zone.label)}</h3><span class="status ok">${esc(zone.id)}</span></div>
      <div class="zone-summary"><div><span>Layer</span><strong>${layerInfo[0]}</strong></div><div><span>Evidence</span><strong>${layerInfo[2] ? 'Available' : 'Unavailable'}</strong></div></div>
      <div class="zone-metrics"><div><span>Structural state</span><strong>${activeLayer === 'macro' ? 'Observed' : '—'}</strong><small>${activeLayer === 'macro' ? 'from available imagery' : 'not measured'}</small></div><div><span>Biological age</span><strong>—</strong><small>no zone-linked estimate</small></div><div><span>Damage</span><strong>—</strong><small>not inferred</small></div><div><span>Pathology</span><strong>—</strong><small>not inferred</small></div></div>
      <div class="evidence-box ${layerInfo[2] ? 'available' : ''}"><strong>${layerInfo[2] ? 'Evidence available' : `${layerInfo[0]} analysis unavailable`}</strong><p>${esc(layerInfo[1])}</p></div>
      <button type="button" class="deep-analysis" data-deep="${zone.id}">Deep analysis</button>
      <p class="muted">Deep analysis should only unlock measurements supported by evidence linked to this anatomical region.</p>
    `;
    document.querySelector('.deep-analysis').onclick = () => {
      if (activeLayer === 'macro') {
        activeLayer = 'tissue'; renderTabs(run); renderPanel(run);
      }
    };
    updateSelection();
  }

  function resetView() { if (!camera || !controls) return; camera.position.set(0, 2.2, 15); controls.target.set(0, 1, 0); controls.update(); }
  function resize() { const host = document.getElementById('hand-3d-canvas'); if (!renderer || !host) return; const w = host.clientWidth || 640; const h = host.clientHeight || 560; camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h, false); }
  function animate() { requestAnimationFrame(animate); if (controls) controls.update(); if (renderer) renderer.render(scene, camera); }

  async function load() {
    addSection();
    const status = document.getElementById('twin-v1-status');
    try {
      const response = await fetch('/api/hand/analysis', { cache: 'no-store' });
      const run = response.ok ? await response.json() : null;
      renderTabs(run || {});
      renderPanel(run || {});
      const THREE = await import('https://unpkg.com/three@0.180.0/build/three.module.js');
      const controlsModule = await import('https://unpkg.com/three@0.180.0/examples/jsm/controls/OrbitControls.js');
      buildScene(THREE, controlsModule.OrbitControls);
      status.textContent = run?.status === 'ready' ? 'Ready · evidence linked' : 'Ready · review evidence';
      status.className = `badge ${run?.status === 'ready' ? 'ok' : 'warning'}`;
    } catch (error) {
      status.textContent = `3D unavailable: ${error.message}`;
      status.className = 'badge warning';
    }
  }

  document.addEventListener('DOMContentLoaded', load);
})();
