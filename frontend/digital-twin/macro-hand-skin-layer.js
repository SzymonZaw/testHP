import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  const viewport = document.getElementById('twin-viewport');
  const baseCanvas = document.getElementById('twin-canvas');
  const badge = document.getElementById('spatial-level-badge');
  const breadcrumb = document.getElementById('spatial-breadcrumb');
  if (!viewport || !baseCanvas || !badge || !breadcrumb) return;

  const canvas = document.createElement('canvas');
  canvas.id = 'macro-hand-skin-canvas';
  Object.assign(canvas.style, {
    position: 'absolute', inset: '0', width: '100%', height: '100%',
    zIndex: '18', display: 'none', pointerEvents: 'none',
    background: 'transparent'
  });
  viewport.appendChild(canvas);

  const hud = document.createElement('div');
  hud.id = 'macro-hand-skin-hud';
  Object.assign(hud.style, {
    position: 'absolute', left: '18px', bottom: '18px', zIndex: '24',
    display: 'none', pointerEvents: 'none', padding: '8px 11px', borderRadius: '10px',
    background: 'rgba(8,18,19,.78)', border: '1px solid rgba(155,216,196,.22)',
    color: '#dcece6', font: '800 10px system-ui,sans-serif', letterSpacing: '.08em',
    backdropFilter: 'blur(8px)'
  });
  viewport.appendChild(hud);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(28, 1, 0.1, 100);
  camera.position.set(0, 0.2, 10.5);
  const root = new THREE.Group();
  root.rotation.set(-0.06, 0.18, 0.02);
  scene.add(root);
  scene.add(new THREE.HemisphereLight(0xfff5ed, 0x243b35, 2.4));
  const key = new THREE.DirectionalLight(0xffeee4, 3.1);
  key.position.set(4, 6, 8);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x9bc9bb, 1.2);
  fill.position.set(-5, 2, 5);
  scene.add(fill);

  const skinGroup = new THREE.Group();
  const skeletonGroup = new THREE.Group();
  root.add(skinGroup, skeletonGroup);

  let texture = null;
  let textureSource = 'procedural skin';
  let active = false;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let zoom = 10.5;
  let loadedAssetId = '';

  function currentPath() {
    return [...breadcrumb.querySelectorAll('button')].map(x => x.textContent.trim()).filter(Boolean);
  }

  function isRootMacro() {
    const value = String(badge.textContent || '').toUpperCase();
    return value.includes('MACRO') && currentPath().length <= 1 && /\bhand\b/i.test(document.getElementById('spatial-node')?.textContent || '');
  }

  function makeSkinMaterial() {
    return new THREE.MeshPhysicalMaterial({
      color: 0xc98d78,
      roughness: 0.74,
      metalness: 0,
      clearcoat: 0.08,
      clearcoatRoughness: 0.8,
      map: texture || null,
      transparent: true,
      opacity: texture ? 0.96 : 0.93,
      side: THREE.FrontSide
    });
  }

  function roundedBox(w, h, d, radius) {
    const shape = new THREE.Shape();
    const x = -w / 2, y = -h / 2;
    shape.moveTo(x + radius, y);
    shape.lineTo(x + w - radius, y);
    shape.quadraticCurveTo(x + w, y, x + w, y + radius);
    shape.lineTo(x + w, y + h - radius);
    shape.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    shape.lineTo(x + radius, y + h);
    shape.quadraticCurveTo(x, y + h, x, y + h - radius);
    shape.lineTo(x, y + radius);
    shape.quadraticCurveTo(x, y, x + radius, y);
    const geometry = new THREE.ExtrudeGeometry(shape, { depth: d, bevelEnabled: true, bevelSegments: 5, bevelSize: radius * 0.55, bevelThickness: radius * 0.55, curveSegments: 8 });
    geometry.center();
    return geometry;
  }

  function addSkin(geometry, position, scale = [1, 1, 1], rotation = [0, 0, 0]) {
    const mesh = new THREE.Mesh(geometry, makeSkinMaterial());
    mesh.position.set(...position);
    mesh.rotation.set(...rotation);
    mesh.scale.set(...scale);
    skinGroup.add(mesh);
    return mesh;
  }

  function addBone(a, b, radius = 0.075) {
    const start = new THREE.Vector3(...a), end = new THREE.Vector3(...b);
    const delta = new THREE.Vector3().subVectors(end, start);
    const mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(radius, radius * 0.9, delta.length(), 10),
      new THREE.MeshStandardMaterial({ color: 0xe8d7bf, roughness: 0.72, transparent: true, opacity: 0.16, depthWrite: false })
    );
    mesh.position.copy(start).add(end).multiplyScalar(0.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
    skeletonGroup.add(mesh);
  }

  function buildSkeleton() {
    skeletonGroup.clear();
    // Wrist + palm metacarpal fan.
    addBone([0, -2.35, -0.02], [0, -0.75, -0.02], 0.11);
    const bases = [-1.55, -0.78, 0, 0.78, 1.48];
    bases.forEach((x, i) => {
      const lean = i === 0 ? -0.32 : i === 4 ? 0.2 : 0;
      addBone([x * 0.55, -0.7, 0], [x, 0.45, 0], 0.075);
      addBone([x, 0.45, 0], [x + lean, 1.35, 0], 0.062);
      addBone([x + lean, 1.35, 0], [x + lean * 1.15, 2.05, 0], 0.052);
    });
  }

  function buildHand() {
    skinGroup.clear();
    // Palm and wrist form a continuous soft silhouette rather than disconnected blocks.
    addSkin(roundedBox(4.25, 4.0, 0.95, 0.7), [0, -0.15, 0], [1, 1, 0.88]);
    addSkin(new THREE.CapsuleGeometry(1.05, 2.2, 12, 32), [0, -2.35, 0], [0.86, 1, 0.72], [0, 0, Math.PI / 2]);

    const fingers = [
      { x: -1.65, y: 2.15, len: 2.55, r: 0.43, tilt: -0.07 },
      { x: -0.82, y: 2.35, len: 3.05, r: 0.46, tilt: -0.025 },
      { x: 0.02, y: 2.45, len: 3.25, r: 0.47, tilt: 0 },
      { x: 0.87, y: 2.35, len: 3.0, r: 0.44, tilt: 0.025 },
      { x: 1.62, y: 2.1, len: 2.55, r: 0.40, tilt: 0.08 }
    ];
    fingers.forEach(f => {
      const finger = addSkin(new THREE.CapsuleGeometry(f.r, f.len, 12, 24), [f.x, f.y, 0.02], [1, 1, 0.78], [0, 0, f.tilt]);
      finger.material.clearcoat = 0.12;
    });

    // Thumb sweeps outward from the thenar area.
    const thumb = addSkin(new THREE.CapsuleGeometry(0.48, 2.35, 12, 24), [-2.05, 0.25, 0.04], [1, 1, 0.8], [0, 0, -0.85]);
    thumb.scale.y = 1.05;
    buildSkeleton();
  }

  function disposeTexture() {
    texture?.dispose?.();
    texture = null;
  }

  function applyTexture(next, source) {
    disposeTexture();
    texture = next;
    textureSource = source;
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = THREE.ClampToEdgeWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
    skinGroup.traverse(obj => {
      if (!obj.isMesh) return;
      obj.material.map = texture;
      obj.material.needsUpdate = true;
    });
    hud.textContent = `MACRO SKIN MAP · ${source}`;
  }

  async function loadRealSkin() {
    try {
      const response = await fetch('/api/hand/analysis?subject_id=own_cohort&timepoint=T0', { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const assets = (data.assets || []).filter(a => ['ready', 'available'].includes(String(a.status || '').toLowerCase()) && String(a.modality || '').toLowerCase() === 'hand');
      const asset = assets.find(a => ['front', 'dorsal', 'palm'].includes(String(a.view || '').toLowerCase())) || assets[0];
      if (!asset || !asset.asset_id || asset.asset_id === loadedAssetId) return;
      loadedAssetId = asset.asset_id;
      const image = new Image();
      image.crossOrigin = 'anonymous';
      image.onload = () => {
        const tex = new THREE.Texture(image);
        tex.needsUpdate = true;
        applyTexture(tex, asset.filename || asset.asset_id);
      };
      image.src = `/api/spatial/evidence/${encodeURIComponent(asset.asset_id)}`;
    } catch (_) {
      // Procedural skin remains the deterministic fallback when no macro photo is linked.
    }
  }

  function resize() {
    const rect = viewport.getBoundingClientRect();
    const w = Math.max(1, rect.width), h = Math.max(1, rect.height);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }

  function syncVisibility() {
    const next = isRootMacro();
    if (next === active) return;
    active = next;
    canvas.style.display = active ? 'block' : 'none';
    hud.style.display = active ? 'block' : 'none';
    if (active) {
      baseCanvas.style.opacity = '0';
      baseCanvas.style.pointerEvents = 'auto';
      resize();
      loadRealSkin();
    } else {
      baseCanvas.style.opacity = '';
      baseCanvas.style.pointerEvents = '';
    }
  }

  canvas.addEventListener('pointerdown', e => { dragging = true; lastX = e.clientX; lastY = e.clientY; });
  canvas.addEventListener('pointermove', e => {
    if (!dragging || !active) return;
    root.rotation.y += (e.clientX - lastX) * 0.006;
    root.rotation.x += (e.clientY - lastY) * 0.004;
    lastX = e.clientX; lastY = e.clientY;
  });
  window.addEventListener('pointerup', () => { dragging = false; });
  canvas.addEventListener('wheel', e => {
    if (!active) return;
    e.preventDefault();
    zoom = Math.max(7.5, Math.min(15, zoom * (e.deltaY > 0 ? 1.08 : 0.92)));
    camera.position.z = zoom;
  }, { passive: false });

  buildHand();
  hud.textContent = `MACRO SKIN MAP · ${textureSource}`;
  const observer = new MutationObserver(syncVisibility);
  [badge, breadcrumb, document.getElementById('spatial-node')].filter(Boolean).forEach(el => observer.observe(el, { childList: true, subtree: true, characterData: true, attributes: true }));
  window.addEventListener('resize', resize);
  setInterval(syncVisibility, 250);

  function animate() {
    requestAnimationFrame(animate);
    syncVisibility();
    if (active) renderer.render(scene, camera);
  }
  animate();
})();
