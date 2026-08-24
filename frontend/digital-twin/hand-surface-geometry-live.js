(() => {
  const PARAMS = { palmLength: 1, palmWidth: 1, thickness: 1, fingerSpread: 1, taper: 1, thumbAngle: 1 };
  const RANGES = {
    palmLength: [.75, 1.25], palmWidth: [.75, 1.25], thickness: [.75, 1.25],
    fingerSpread: [.7, 1.3], taper: [.7, 1.3], thumbAngle: [.7, 1.3]
  };
  const FINGERS = ['index', 'middle', 'ring', 'little'];
  const KEY = 'digitalTwinHandGeometry.live.v1';
  const clamp = (v, a, b) => Math.min(b, Math.max(a, Number(v) || 1));
  const read = () => {
    try {
      const x = JSON.parse(localStorage.getItem(KEY) || 'null');
      return { ...PARAMS, ...(x?.parameters || x || {}) };
    } catch { return { ...PARAMS }; }
  };

  let state = read();
  let host = null, canvas = null, renderer = null, scene = null, camera = null, controls = null;
  let previewRoot = null, meshes = new Map(), resizeObserver = null, frame = 0;
  let booted = false, previewReady = false;

  const getMain = () => {
    const active = window.spatialViewportManager?.active;
    const roots = [active?.root, active?.scene].filter(Boolean);
    const out = new Map();
    const visit = object => {
      if (!object || out.size >= 6) return;
      const name = String(object.name || '').replace(/^skin:/, '');
      if (['palm', ...FINGERS, 'thumb'].includes(name) && object.isMesh) out.set(name, object);
      object.children?.forEach(visit);
    };
    roots.forEach(visit);
    return out;
  };

  const bases = new WeakMap();
  const base = mesh => {
    let value = bases.get(mesh);
    if (!value) {
      value = { p: mesh.position.clone(), s: mesh.scale.clone(), rz: mesh.rotation.z };
      bases.set(mesh, value);
    }
    return value;
  };

  const save = () => localStorage.setItem(KEY, JSON.stringify({
    schema: 'hand-surface-geometry-live-v3',
    parameters: state,
    updatedAt: new Date().toISOString()
  }));

  const updateMain = () => {
    const meshesMain = getMain();
    const palm = meshesMain.get('palm');
    if (!palm) return meshesMain;

    const palmBase = base(palm);
    palm.scale.set(
      palmBase.s.x * state.palmWidth,
      palmBase.s.y * state.palmLength,
      palmBase.s.z * state.thickness
    );

    FINGERS.forEach((name, index) => {
      const mesh = meshesMain.get(name);
      if (!mesh) return;
      const b = base(mesh);
      mesh.position.x = b.p.x + (index - 1.5) * .2 * (state.fingerSpread - 1);
      const width = 1 - .22 * (state.taper - 1);
      mesh.scale.set(b.s.x * width, b.s.y, b.s.z * state.thickness);
    });

    const thumb = meshesMain.get('thumb');
    if (thumb) {
      const b = base(thumb);
      thumb.rotation.z = b.rz - .42 * (state.thumbAngle - 1);
      thumb.scale.set(b.s.x * (1 - .1 * (state.taper - 1)), b.s.y, b.s.z * state.thickness);
    }

    window.dispatchEvent(new CustomEvent('testhp:hand-surface-geometry-changed', {
      detail: { parameters: { ...state }, meshCount: meshesMain.size, source: 'digitalTwinGeometry' }
    }));
    return meshesMain;
  };

  const setStatus = text => {
    const element = document.querySelector('#hand-geometry-live-preview [data-geometry-preview-status]');
    if (element) element.textContent = text;
  };

  const updateUi = () => {
    const card = document.getElementById('hand-geometry-live-preview');
    if (!card) return;
    const status = card.querySelector('[data-geometry-preview-status]');
    if (status) {
      status.textContent = previewReady
        ? (Object.values(state).every(value => Number(value) === 1) ? 'Live · wartości domyślne' : 'Live · zmieniona geometria')
        : 'Uruchamianie…';
    }
    const mainStatus = card.querySelector('[data-geometry-main-status]');
    if (mainStatus) {
      const count = getMain().size;
      mainStatus.textContent = count >= 6
        ? `Połączono z modelem głównym · ${count} elementów geometrii`
        : 'Podgląd działa lokalnie. Model główny jest chwilowo niedostępny.';
    }
  };

  const updatePreview = () => {
    if (!meshes.size) return;
    const palm = meshes.get('palm');
    if (palm) palm.scale.set(state.palmWidth, state.palmLength, state.thickness);

    const xs = [-1.05, -.35, .42, 1.12];
    FINGERS.forEach((name, index) => {
      const mesh = meshes.get(name);
      if (!mesh) return;
      mesh.position.x = xs[index] + (index - 1.5) * .2 * (state.fingerSpread - 1);
      const width = 1 - .22 * (state.taper - 1);
      mesh.scale.set(width, 1, state.thickness);
    });

    const thumb = meshes.get('thumb');
    if (thumb) {
      thumb.rotation.z = -.82 - .42 * (state.thumbAngle - 1);
      thumb.scale.set(1 - .1 * (state.taper - 1), 1, state.thickness);
    }
    updateUi();
  };

  const resize = () => {
    if (!renderer || !camera || !host) return;
    const rect = host.getBoundingClientRect();
    const width = Math.max(1, Math.round(rect.width));
    const height = Math.max(1, Math.round(rect.height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };

  // Frame the entire procedural hand instead of relying on a fixed camera distance.
  // The previous fixed camera was too close for the full wrist-to-fingertip extent,
  // which could leave the preview apparently empty/black after boot.
  const framePreview = THREE => {
    if (!previewRoot || !camera) return;
    const box = new THREE.Box3().setFromObject(previewRoot);
    if (box.isEmpty()) return;

    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxSize = Math.max(size.x, size.y, size.z);
    const fov = camera.fov * Math.PI / 180;
    const distance = (maxSize / 2) / Math.tan(fov / 2) * 1.28;

    camera.position.set(center.x, center.y + .1, center.z + Math.max(7, distance));
    camera.near = Math.max(.01, distance / 100);
    camera.far = Math.max(100, distance * 8);
    camera.lookAt(center);
    camera.updateProjectionMatrix();
    if (controls) {
      controls.target.copy(center);
      controls.minDistance = Math.max(4, distance * .45);
      controls.maxDistance = Math.max(20, distance * 2.5);
      controls.update();
    }
  };

  const makePreview = async () => {
    if (previewReady || !canvas || !canvas.isConnected) return;

    try {
      setStatus('Uruchamianie…');

      // Use the exact same Three.js build as the canonical main viewer.
      // This avoids mixing the app's jsDelivr build with an esm.sh build.
      const THREE = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js');
      const { OrbitControls } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js');
      if (!canvas.isConnected) return;

      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setClearColor(0x0b1220, 1);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;

      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x0b1220);
      camera = new THREE.PerspectiveCamera(30, 1, .01, 100);
      controls = new OrbitControls(camera, canvas);
      controls.enableDamping = true;
      controls.enablePan = true;

      scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 2.8));
      const key = new THREE.DirectionalLight(0xffffff, 3.2);
      key.position.set(4, 7, 9);
      scene.add(key);
      const fill = new THREE.DirectionalLight(0xffd8c2, 1.5);
      fill.position.set(-5, 3, 5);
      scene.add(fill);

      previewRoot = new THREE.Group();
      previewRoot.name = 'hand-geometry-live-preview-root';
      previewRoot.rotation.x = -.14;
      scene.add(previewRoot);

      const add = (id, position, radius, length, rotation = [0, 0, 0]) => {
        const material = new THREE.MeshStandardMaterial({
          color: 0xc68b72,
          roughness: .64,
          metalness: 0,
          emissive: 0x24130d,
          emissiveIntensity: .035
        });
        const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 8, 18), material);
        mesh.name = id;
        mesh.position.set(...position);
        mesh.rotation.set(...rotation);
        previewRoot.add(mesh);
        meshes.set(id, mesh);
      };

      add('wrist', [0, -2.15, 0], .72, 1.25);
      add('palm', [0, -.35, 0], 1.55, 2.25);
      add('thumb', [-1.45, 0, .02], .48, 1.45, [0, 0, -.82]);
      add('index', [-1.05, 1.95, 0], .43, 2.15);
      add('middle', [-.35, 2.25, 0], .46, 2.55);
      add('ring', [.42, 2.12, 0], .45, 2.32);
      add('little', [1.12, 1.86, 0], .4, 1.95, [0, 0, .08]);

      resizeObserver = new ResizeObserver(() => resize());
      resizeObserver.observe(host);
      resize();
      updatePreview();
      framePreview(THREE);
      previewReady = true;
      updateUi();

      canvas.addEventListener('webglcontextlost', event => {
        event.preventDefault();
        previewReady = false;
        cancelAnimationFrame(frame);
        setStatus('Podgląd utracił kontekst WebGL');
      }, { passive: false });

      canvas.addEventListener('webglcontextrestored', () => {
        previewReady = true;
        setStatus('Live · wartości domyślne');
        updatePreview();
        framePreview(THREE);
      });

      const render = () => {
        if (!renderer || !canvas?.isConnected) return;
        resize();
        controls?.update();
        renderer.render(scene, camera);
        frame = requestAnimationFrame(render);
      };
      render();
    } catch (error) {
      previewReady = false;
      console.error('[hand-surface-geometry-live] preview boot failed', error);
      setStatus(`Podgląd niedostępny: ${error?.message || error}`);
    }
  };

  const geometryRoot = () => {
    const title = [...document.querySelectorAll('strong')].find(element => element.textContent?.trim() === 'Geometria dłoni');
    if (!title) return null;
    const intro = title.closest('.hss-geometry-intro');
    const container = intro?.parentElement;
    return intro && container ? { intro, container } : null;
  };

  const installUi = () => {
    const existing = document.getElementById('hand-geometry-live-preview');
    if (existing?.isConnected) {
      host = existing.querySelector('[data-geometry-preview-canvas]');
      canvas = existing.querySelector('canvas');
      if (host && canvas) makePreview();
      return true;
    }

    const root = geometryRoot();
    if (!root) return false;

    const card = document.createElement('section');
    card.id = 'hand-geometry-live-preview';
    card.style.cssText = 'margin:14px 0 16px;border:1px solid var(--border,#d8dee8);border-radius:12px;overflow:hidden;background:var(--panel,#fff)';
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:12px;padding:13px 14px;border-bottom:1px solid var(--border,#d8dee8)">
        <div>
          <strong style="display:block;font-size:14px">Podgląd 3D</strong>
          <span style="display:block;margin-top:3px;font-size:12px;color:#667085">Przesuwaj suwaki i obserwuj dokładnie ten sam efekt w podglądzie.</span>
        </div>
        <span data-geometry-preview-status style="font-size:11px;font-weight:800;color:#027a48">Uruchamianie…</span>
      </div>
      <div data-geometry-preview-canvas style="height:360px;background:#0b1220;position:relative">
        <canvas aria-label="Podgląd geometrii dłoni" style="width:100%;height:100%;display:block"></canvas>
        <div style="position:absolute;left:12px;bottom:10px;color:#c9d1d9;font-size:11px;background:rgba(13,17,23,.72);padding:6px 8px;border-radius:7px">Przeciągnij · kółko myszy = zoom</div>
      </div>
      <div data-geometry-main-status style="padding:9px 12px;font-size:11px;color:#667085;border-top:1px solid var(--border,#d8dee8)"></div>`;

    root.container.appendChild(card);
    host = card.querySelector('[data-geometry-preview-canvas]');
    canvas = card.querySelector('canvas');
    makePreview();
    return true;
  };

  const bind = () => {
    const root = geometryRoot()?.container;
    if (!root) return;
    const map = [
      ['palmLength', /długość dłoni/i], ['palmWidth', /szerokość dłoni/i],
      ['thickness', /grubość powierzchni/i], ['fingerSpread', /rozstaw palców/i],
      ['taper', /zwężenie palców/i], ['thumbAngle', /ustawienie kciuka/i]
    ];

    root.querySelectorAll('input[type="range"]').forEach(input => {
      if (input.dataset.geometryLiveBound) return;
      const text = input.closest('label,div')?.textContent || '';
      const hit = map.find(([, regexp]) => regexp.test(text));
      if (!hit) return;
      input.dataset.geometryLiveBound = '1';
      input.value = state[hit[0]];
      input.addEventListener('input', () => window.digitalTwinGeometry.setParameter(hit[0], input.value));
    });
  };

  const api = window.digitalTwinGeometry || {};
  api.version = 'canonical-geometry-3-live';
  api.__liveBridgeInstalled = true;
  api.getState = () => ({ ...state });
  api.inspect = () => Object.fromEntries([...getMain()].map(([id, mesh]) => [id, {
    position: mesh.position.toArray(),
    scale: mesh.scale.toArray(),
    rotation: [mesh.rotation.x, mesh.rotation.y, mesh.rotation.z]
  }]));
  api.setParameter = (name, value) => {
    if (!(name in PARAMS)) return { ok: false, error: `Unknown geometry parameter: ${name}` };
    const [min, max] = RANGES[name];
    state = { ...state, [name]: clamp(value, min, max) };
    save();
    const mainMeshes = updateMain();
    updatePreview();
    return { ok: true, meshCount: mainMeshes.size, geometry: { ...state } };
  };
  api.setState = next => {
    Object.keys(PARAMS).forEach(key => {
      if (next?.[key] != null) api.setParameter(key, next[key]);
    });
    return { ok: true, geometry: { ...state } };
  };
  api.reset = () => api.setState(PARAMS);
  window.digitalTwinGeometry = api;

  const ensure = () => {
    installUi();
    bind();
    updateMain();
    updatePreview();
  };

  const boot = () => {
    if (booted) return;
    booted = true;
    ensure();

    const observer = new MutationObserver(() => {
      if (!document.getElementById('hand-geometry-live-preview')) ensure();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    ['testhp:deep-3d-active', 'testhp:viewport-manager-ready', 'testhp:spatial-layer-changed']
      .forEach(eventName => window.addEventListener(eventName, () => setTimeout(ensure, 0)));
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
