import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const viewport = document.getElementById('twin-viewport');
const baseCanvas = document.getElementById('twin-canvas');
const controls = document.querySelector('.viewer-controls');
const hint = document.querySelector('.viewer-hint');
const loading = document.getElementById('viewer-loading');
const badge = document.getElementById('spatial-level-badge');
const node = document.getElementById('spatial-node');
const children = document.getElementById('spatial-children');

if (viewport && badge && node && children) {
  const layerCanvas = document.createElement('canvas');
  layerCanvas.id = 'spatial-layer-canvas';
  Object.assign(layerCanvas.style, {
    position: 'absolute', inset: '0', width: '100%', height: '100%',
    zIndex: '3', display: 'none', cursor: 'default'
  });
  viewport.appendChild(layerCanvas);

  const labels = document.createElement('div');
  labels.id = 'spatial-layer-labels';
  Object.assign(labels.style, {
    position: 'absolute', inset: '0', zIndex: '4', pointerEvents: 'none', display: 'none'
  });
  viewport.appendChild(labels);

  const renderer = new THREE.WebGLRenderer({canvas: layerCanvas, antialias: true, alpha: true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0b1518);
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  camera.position.set(0, 0, 8);
  const ambient = new THREE.HemisphereLight(0xffffff, 0x10201d, 2.2);
  scene.add(ambient);
  const key = new THREE.DirectionalLight(0xffffff, 2.4);
  key.position.set(4, 5, 7);
  scene.add(key);
  const layerRoot = new THREE.Group();
  scene.add(layerRoot);

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let clickable = [];
  let activeLevel = 'MACRO ANATOMY';
  let frame = 0;

  const COLORS = {
    tissue: 0x4f8f7d,
    cellular: 0x5fae98,
    cell: 0x8bc7b0,
    accent: 0x9bd8c4,
    grid: 0x4f9b86
  };

  function level() {
    return String(badge.textContent || 'MACRO').trim().toUpperCase();
  }

  function targetElements() {
    return [...children.querySelectorAll('.spatial-target')];
  }

  function targetText(el) {
    return el.querySelector('strong')?.textContent || 'Spatial target';
  }

  function clearScene() {
    while (layerRoot.children.length) {
      const obj = layerRoot.children.pop();
      obj.traverse?.(child => {
        child.geometry?.dispose?.();
        if (child.material) {
          if (Array.isArray(child.material)) child.material.forEach(m => m.dispose?.());
          else child.material.dispose?.();
        }
      });
    }
    clickable = [];
    labels.replaceChildren();
  }

  function addLabel(text, x, y, target) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = text;
    Object.assign(button.style, {
      position: 'absolute', left: `${x}%`, top: `${y}%`, transform: 'translate(-50%,-50%)',
      pointerEvents: 'auto', padding: '10px 13px', borderRadius: '12px',
      border: '1px solid #78bca866', background: '#12221fe6', color: '#dcece6',
      font: '700 12px system-ui,sans-serif', cursor: 'pointer', backdropFilter: 'blur(6px)'
    });
    button.addEventListener('click', () => target.click());
    labels.appendChild(button);
  }

  function makeTargetMesh(geometry, position, target, material = COLORS.tissue) {
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
      color: material, roughness: .62, metalness: .05, emissive: 0x071c17, emissiveIntensity: .22
    }));
    mesh.position.set(...position);
    mesh.userData.target = target;
    layerRoot.add(mesh);
    clickable.push(mesh);
    return mesh;
  }

  function renderTissue() {
    const targets = targetElements();
    const plate = new THREE.Mesh(
      new THREE.BoxGeometry(6.5, 3.8, .32),
      new THREE.MeshStandardMaterial({color: 0x18322d, roughness: .85, metalness: .02})
    );
    plate.position.z = -.35;
    layerRoot.add(plate);

    const positions = [[-2.05, .45, .25], [0, -.25, .45], [2.05, .5, .25]];
    targets.forEach((target, i) => {
      makeTargetMesh(new THREE.BoxGeometry(1.55, 1.25, .38), positions[i % positions.length], target, COLORS.tissue);
      addLabel(targetText(target), 24 + (i * 26), 58 - (i % 2) * 18, target);
    });
  }

  function renderCellular() {
    const targets = targetElements();
    const plate = new THREE.Mesh(
      new THREE.BoxGeometry(7, 4.2, .18),
      new THREE.MeshStandardMaterial({color: 0x101f20, roughness: .9})
    );
    plate.position.z = -.45;
    layerRoot.add(plate);

    for (let x = -3; x <= 3; x += 1) {
      for (let y = -2; y <= 2; y += 1) {
        const cell = new THREE.Mesh(
          new THREE.CircleGeometry(.13, 20),
          new THREE.MeshBasicMaterial({color: COLORS.grid, transparent: true, opacity: .5})
        );
        cell.position.set(x + (y % 2) * .35, y * .7, -.1);
        layerRoot.add(cell);
      }
    }

    const positions = [[-2.0, .75, .2], [0, -.55, .3], [2.0, .8, .2]];
    targets.forEach((target, i) => {
      const mesh = makeTargetMesh(new THREE.SphereGeometry(.62, 32, 20), positions[i % 3], target, COLORS.cellular);
      mesh.scale.set(1, .72, .35);
      addLabel(targetText(target), 25 + i * 25, 54 - (i % 2) * 17, target);
    });
  }

  function renderSingleCell() {
    const target = targetElements()[0];
    const outer = new THREE.Mesh(
      new THREE.SphereGeometry(1.45, 48, 32),
      new THREE.MeshStandardMaterial({color: COLORS.cell, roughness: .55, transparent: true, opacity: .82, emissive: 0x0b3026, emissiveIntensity: .35})
    );
    outer.position.z = .1;
    if (target) { outer.userData.target = target; clickable.push(outer); }
    layerRoot.add(outer);

    const nucleus = new THREE.Mesh(
      new THREE.SphereGeometry(.55, 40, 24),
      new THREE.MeshStandardMaterial({color: 0x315e51, roughness: .45, emissive: 0x183b31, emissiveIntensity: .45})
    );
    nucleus.position.set(-.2, .1, 1.05);
    layerRoot.add(nucleus);

    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(2.0, .025, 8, 96),
      new THREE.MeshBasicMaterial({color: COLORS.accent, transparent: true, opacity: .55})
    );
    layerRoot.add(ring);
    if (target) addLabel(targetText(target), 50, 82, target);
  }

  function render() {
    activeLevel = level();
    const deeper = activeLevel !== 'MACRO' && activeLevel !== 'MACRO ANATOMY';
    layerCanvas.style.display = deeper ? 'block' : 'none';
    labels.style.display = deeper ? 'block' : 'none';
    if (baseCanvas) baseCanvas.style.visibility = deeper ? 'hidden' : 'visible';
    if (controls) controls.style.visibility = deeper ? 'hidden' : 'visible';
    if (hint) hint.style.visibility = deeper ? 'hidden' : 'visible';
    if (loading) loading.style.visibility = deeper ? 'hidden' : 'visible';
    if (!deeper) return;

    clearScene();
    camera.position.set(0, 0, 8);
    camera.lookAt(0, 0, 0);
    if (activeLevel === 'TISSUE FIELD') renderTissue();
    else if (activeLevel === 'CELLULAR FIELD') renderCellular();
    else renderSingleCell();
    resize();
  }

  function resize() {
    const rect = viewport.getBoundingClientRect();
    const w = Math.max(1, rect.width);
    const h = Math.max(1, rect.height);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }

  function animate() {
    frame = requestAnimationFrame(animate);
    if (layerCanvas.style.display !== 'none') {
      layerRoot.rotation.y += .0025;
      renderer.render(scene, camera);
    }
  }

  layerCanvas.addEventListener('pointerdown', event => {
    const rect = layerCanvas.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(clickable, false)[0];
    if (hit?.object?.userData?.target) hit.object.userData.target.click();
  });

  const observer = new MutationObserver(() => render());
  observer.observe(badge, {childList: true, characterData: true, subtree: true});
  observer.observe(node, {childList: true, characterData: true, subtree: true});
  observer.observe(children, {childList: true, characterData: true, subtree: true});
  window.addEventListener('resize', resize);
  render();
  animate();
}