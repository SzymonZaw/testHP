import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

(() => {
  'use strict';
  const ROOT_ID = 'persistent-3d-preview';
  if (document.getElementById(ROOT_ID)) return;

  const style = document.createElement('style');
  style.textContent = `
    #${ROOT_ID}{margin:18px 0;border:1px solid var(--border,#d8dee8);border-radius:14px;background:var(--panel,#fff);overflow:hidden}
    #${ROOT_ID} .p3d-head{padding:15px 18px;border-bottom:1px solid var(--border,#d8dee8);display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}
    #${ROOT_ID} .p3d-kicker{display:block;font-size:10px;font-weight:800;letter-spacing:.09em;color:#667085;text-transform:uppercase}
    #${ROOT_ID} h2{margin:3px 0 0;font-size:18px}
    #${ROOT_ID} .p3d-sub{margin:4px 0 0;color:#667085;font-size:12px}
    #${ROOT_ID} .p3d-live{font-size:11px;font-weight:800;color:#1f6b45;padding:5px 8px;border-radius:999px;background:#ecfdf3}
    #${ROOT_ID} .p3d-body{display:grid;grid-template-columns:minmax(0,1fr) 270px;min-height:390px}
    #${ROOT_ID} .p3d-stage{position:relative;min-height:390px;background:#0b1220}
    #${ROOT_ID} canvas{display:block;width:100%;height:100%;min-height:390px;touch-action:none}
    #${ROOT_ID} .p3d-hint{position:absolute;left:12px;bottom:10px;color:#d8dee8;background:rgba(11,18,32,.72);padding:6px 9px;border-radius:8px;font-size:11px;pointer-events:none}
    #${ROOT_ID} .p3d-controls{padding:16px;border-left:1px solid var(--border,#d8dee8);display:grid;gap:13px;align-content:start}
    #${ROOT_ID} .p3d-control{display:grid;gap:5px}
    #${ROOT_ID} .p3d-control label{font-size:12px;font-weight:700;display:flex;justify-content:space-between;gap:8px}
    #${ROOT_ID} input[type=range]{width:100%}
    #${ROOT_ID} .p3d-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:4px}
    #${ROOT_ID} button{border:1px solid var(--border,#d8dee8);border-radius:8px;padding:8px 10px;background:#fff;cursor:pointer;font-weight:700}
    #${ROOT_ID} .p3d-note{font-size:11px;line-height:1.45;color:#667085;padding-top:4px}
    @media(max-width:800px){#${ROOT_ID} .p3d-body{grid-template-columns:1fr}#${ROOT_ID} .p3d-controls{border-left:0;border-top:1px solid var(--border,#d8dee8)}}
  `;
  document.head.appendChild(style);

  const panel = document.createElement('section');
  panel.id = ROOT_ID;
  panel.innerHTML = `
    <header class="p3d-head">
      <div><span class="p3d-kicker">STAŁY MODUŁ · NIEZALEŻNY OD GEOMETRII</span><h2>Podgląd 3D</h2><p class="p3d-sub">Przesuwaj suwaki i obserwuj dokładnie ten sam efekt w podglądzie.</p></div>
      <span class="p3d-live">Live · wartości domyślne</span>
    </header>
    <div class="p3d-body">
      <div class="p3d-stage"><canvas aria-label="Niezależny podgląd 3D dłoni"></canvas><div class="p3d-hint">Przeciągnij · kółko myszy = zoom</div></div>
      <aside class="p3d-controls">
        <div class="p3d-control"><label><span>Szerokość dłoni</span><output data-out="width">100%</output></label><input data-param="width" type="range" min="70" max="140" value="100"></div>
        <div class="p3d-control"><label><span>Długość dłoni</span><output data-out="length">100%</output></label><input data-param="length" type="range" min="70" max="140" value="100"></div>
        <div class="p3d-control"><label><span>Grubość</span><output data-out="thickness">100%</output></label><input data-param="thickness" type="range" min="60" max="150" value="100"></div>
        <div class="p3d-control"><label><span>Kciuk</span><output data-out="thumb">100%</output></label><input data-param="thumb" type="range" min="70" max="140" value="100"></div>
        <div class="p3d-actions"><button type="button" data-action="reset">Reset</button><button type="button" data-action="rotate">Obróć 90°</button></div>
        <div class="p3d-note">Ten moduł posiada własny canvas, renderer, kamerę i scenę. Nie korzysta z <code>#twin-canvas</code>, <code>spatialViewportManager</code> ani lifecycle repairera.</div>
      </aside>
    </div>`;

  const appShell = document.querySelector('.app-shell');
  if (appShell) appShell.appendChild(panel);
  else document.body.appendChild(panel);

  const canvas = panel.querySelector('canvas');
  const stage = panel.querySelector('.p3d-stage');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x0b1220, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0b1220);
  const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100);
  camera.position.set(0, 0.6, 8.5);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.enablePan = true;
  controls.minDistance = 4;
  controls.maxDistance = 14;
  controls.target.set(0, 0.3, 0);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x172033, 2.1));
  const key = new THREE.DirectionalLight(0xffffff, 2.8); key.position.set(4, 6, 7); scene.add(key);
  const fill = new THREE.DirectionalLight(0x8bb8ff, 1.2); fill.position.set(-5, 2, -4); scene.add(fill);

  const root = new THREE.Group();
  root.rotation.x = -0.15;
  scene.add(root);

  const material = new THREE.MeshStandardMaterial({ color: 0xc68b72, roughness: 0.72, metalness: 0.02 });
  const meshes = new Map();
  const capsule = (name, position, radius, length, rotation = [0,0,0]) => {
    const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 8, 18), material.clone());
    mesh.name = name;
    mesh.position.set(...position);
    mesh.rotation.set(...rotation);
    root.add(mesh);
    meshes.set(name, mesh);
    return mesh;
  };

  capsule('wrist', [0,-2.15,0], .72, 1.25);
  capsule('palm', [0,-.35,0], 1.55, 2.25);
  capsule('thumb', [-1.45,0.0,.02], .48, 1.45, [0,0,-.82]);
  capsule('index', [-1.05,1.95,0], .43, 2.15);
  capsule('middle', [-.35,2.25,0], .46, 2.55);
  capsule('ring', [.42,2.12,0], .45, 2.32);
  capsule('little', [1.12,1.86,0], .40, 1.95, [0,0,.08]);

  const params = { width: 1, length: 1, thickness: 1, thumb: 1 };
  const update = () => {
    const width = params.width, length = params.length, thickness = params.thickness;
    const palm = meshes.get('palm');
    palm.scale.set(width * thickness, length * thickness, thickness);
    meshes.get('wrist').scale.set(width * thickness, thickness, thickness);
    const fingers = ['index','middle','ring','little'];
    fingers.forEach(name => {
      const mesh = meshes.get(name);
      mesh.scale.set(width * thickness, length, thickness);
    });
    const thumb = meshes.get('thumb');
    thumb.scale.set(params.thumb * thickness, params.thumb * length, params.thumb * thickness);
    panel.querySelectorAll('[data-out]').forEach(out => {
      const key = out.dataset.out;
      out.value = `${Math.round(params[key] * 100)}%`;
      out.textContent = `${Math.round(params[key] * 100)}%`;
    });
  };

  panel.querySelectorAll('[data-param]').forEach(input => input.addEventListener('input', () => {
    params[input.dataset.param] = Number(input.value) / 100;
    update();
  }));
  panel.querySelector('[data-action="reset"]').addEventListener('click', () => {
    Object.keys(params).forEach(key => params[key] = 1);
    panel.querySelectorAll('[data-param]').forEach(input => input.value = 100);
    root.rotation.set(-0.15, 0, 0);
    camera.position.set(0, 0.6, 8.5);
    controls.target.set(0, 0.3, 0);
    controls.update();
    update();
  });
  panel.querySelector('[data-action="rotate"]').addEventListener('click', () => { root.rotation.y += Math.PI / 2; });

  const resize = () => {
    const rect = stage.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };
  new ResizeObserver(resize).observe(stage);
  resize();
  update();

  const render = () => { controls.update(); renderer.render(scene, camera); requestAnimationFrame(render); };
  render();
})();
