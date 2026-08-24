(() => {
  const DEFAULT = Object.freeze({ palmLength: 1, palmWidth: 1, thickness: 1, fingerSpread: 1, taper: 1, thumbAngle: 1 });
  const RANGES = {
    palmLength: [.75, 1.25], palmWidth: [.75, 1.25], thickness: [.75, 1.25],
    fingerSpread: [.7, 1.3], taper: [.7, 1.3], thumbAngle: [.7, 1.3]
  };
  const KEY = 'digitalTwinHandGeometry.live.v1';
  const FINGERS = ['index', 'middle', 'ring', 'little'];
  const clamp = (v, [a, b]) => Math.min(b, Math.max(a, Number(v) || 1));
  const read = () => {
    try { return { ...DEFAULT, ...(JSON.parse(localStorage.getItem(KEY) || 'null')?.parameters || {}) }; }
    catch { return { ...DEFAULT }; }
  };
  const save = state => localStorage.setItem(KEY, JSON.stringify({ schema: 'hand-geometry-preview-v6', parameters: state, updatedAt: new Date().toISOString() }));

  let state = read();
  let three = null, renderer = null, scene = null, camera = null, controls = null, root = null;
  let host = null, canvas = null, resizeObserver = null, renderFrame = 0, started = false, destroyed = false;
  const meshes = new Map();

  const setStatus = text => document.querySelector('#hand-geometry-live-preview [data-geometry-preview-status]')?.replaceChildren(document.createTextNode(text));
  const setMainStatus = text => document.querySelector('#hand-geometry-live-preview [data-geometry-main-status]')?.replaceChildren(document.createTextNode(text));

  const findGeometryContainer = () => {
    const title = [...document.querySelectorAll('strong')].find(el => el.textContent?.trim() === 'Geometria dłoni');
    const intro = title?.closest('.hss-geometry-intro');
    return intro?.parentElement || null;
  };

  const ensureShell = () => {
    const existing = document.getElementById('hand-geometry-live-preview');
    if (existing?.isConnected) {
      host = existing.querySelector('[data-geometry-preview-canvas]');
      canvas = existing.querySelector('canvas');
      return !!(host && canvas);
    }
    const container = findGeometryContainer();
    if (!container) return false;
    const card = document.createElement('section');
    card.id = 'hand-geometry-live-preview';
    card.style.cssText = 'margin:14px 0 16px;border:1px solid var(--border,#d8dee8);border-radius:12px;overflow:hidden;background:var(--panel,#fff)';
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:12px;padding:13px 14px;border-bottom:1px solid var(--border,#d8dee8)">
        <div><strong style="display:block;font-size:14px">Podgląd 3D</strong><span style="display:block;margin-top:3px;font-size:12px;color:#667085">Niezależny model geometrii. Suwaki sterują wyłącznie tym podglądem.</span></div>
        <span data-geometry-preview-status style="font-size:11px;font-weight:800;color:#027a48">Uruchamianie…</span>
      </div>
      <div data-geometry-preview-canvas style="height:360px;background:#0b1220;position:relative">
        <canvas aria-label="Podgląd geometrii dłoni" style="width:100%;height:100%;display:block"></canvas>
        <div style="position:absolute;left:12px;bottom:10px;color:#c9d1d9;font-size:11px;background:rgba(13,17,23,.72);padding:6px 8px;border-radius:7px">Przeciągnij · kółko myszy = zoom</div>
      </div>
      <div data-geometry-main-status style="padding:9px 12px;font-size:11px;color:#667085;border-top:1px solid var(--border,#d8dee8)"></div>`;
    container.appendChild(card);
    host = card.querySelector('[data-geometry-preview-canvas]');
    canvas = card.querySelector('canvas');
    return true;
  };

  const material = () => new three.MeshStandardMaterial({ color: 0xc68b72, roughness: .68, metalness: 0 });
  const addMesh = (name, geometry, position, rotation = [0, 0, 0]) => {
    const mesh = new three.Mesh(geometry, material());
    mesh.name = name;
    mesh.position.set(...position);
    mesh.rotation.set(...rotation);
    root.add(mesh);
    meshes.set(name, mesh);
  };

  const buildModel = () => {
    meshes.clear();
    root = new three.Group();
    scene.add(root);
    addMesh('wrist', new three.CapsuleGeometry(.72, 1.35, 8, 20), [0, -2.18, 0]);
    addMesh('palm', new three.CapsuleGeometry(1.55, 2.35, 8, 24), [0, -.32, 0]);
    addMesh('thumb', new three.CapsuleGeometry(.48, 1.48, 8, 18), [-1.42, .02, .02], [0, 0, -.82]);
    addMesh('index', new three.CapsuleGeometry(.43, 2.18, 8, 18), [-1.05, 1.96, 0]);
    addMesh('middle', new three.CapsuleGeometry(.46, 2.58, 8, 18), [-.35, 2.27, 0]);
    addMesh('ring', new three.CapsuleGeometry(.45, 2.34, 8, 18), [.42, 2.14, 0]);
    addMesh('little', new three.CapsuleGeometry(.40, 1.98, 8, 18), [1.12, 1.88, 0], [0, 0, .08]);
  };

  const fitCamera = () => {
    if (!root || !camera) return;
    const box = new three.Box3().setFromObject(root);
    if (box.isEmpty()) return;
    const center = box.getCenter(new three.Vector3());
    const size = box.getSize(new three.Vector3());
    const max = Math.max(size.x, size.y, size.z);
    const distance = Math.max(7, (max / 2) / Math.tan(camera.fov * Math.PI / 360) * 1.25);
    camera.position.set(center.x, center.y + .15, center.z + distance);
    camera.near = Math.max(.01, distance / 100);
    camera.far = Math.max(100, distance * 8);
    camera.lookAt(center);
    camera.updateProjectionMatrix();
    controls.target.copy(center);
  };

  const resize = () => {
    if (!renderer || !camera || !host || destroyed) return;
    const rect = host.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setViewport(0, 0, width, height);
  };

  const applyGeometry = () => {
    if (!meshes.size) return;
    const palm = meshes.get('palm');
    palm.scale.set(state.palmWidth, state.palmLength, state.thickness);
    const x = [-1.05, -.35, .42, 1.12];
    FINGERS.forEach((name, i) => {
      const mesh = meshes.get(name);
      const fingerWidth = 1 - .22 * (state.taper - 1);
      mesh.position.x = x[i] + (i - 1.5) * .2 * (state.fingerSpread - 1);
      mesh.scale.set(fingerWidth, 1, state.thickness);
    });
    const thumb = meshes.get('thumb');
    thumb.rotation.z = -.82 - .42 * (state.thumbAngle - 1);
    thumb.scale.set(1 - .1 * (state.taper - 1), 1, state.thickness);
    fitCamera();
    controls.update();
    setStatus(Object.values(state).some(v => Number(v) !== 1) ? 'Live · zmieniona geometria' : 'Live · wartości domyślne');
    setMainStatus('Izolowany renderer · 7 elementów · brak połączenia z canonical rendererem.');
    renderOnce();
  };

  const renderOnce = () => {
    if (!renderer || !scene || !camera || destroyed) return;
    renderer.render(scene, camera);
  };

  const renderLoop = () => {
    if (destroyed || !renderer || !canvas?.isConnected) return;
    controls.update();
    renderer.render(scene, camera);
    renderFrame = requestAnimationFrame(renderLoop);
  };

  const bindSliders = () => {
    const container = findGeometryContainer();
    if (!container) return false;
    const mapping = [
      ['palmLength', /długość dłoni/i], ['palmWidth', /szerokość dłoni/i],
      ['thickness', /grubość powierzchni/i], ['fingerSpread', /rozstaw palców/i],
      ['taper', /zwężenie palców/i], ['thumbAngle', /ustawienie kciuka/i]
    ];
    container.querySelectorAll('input[type="range"]').forEach(input => {
      if (input.dataset.geometryPreviewBound === 'v2') return;
      const text = input.closest('label,div')?.textContent || '';
      const hit = mapping.find(([, re]) => re.test(text));
      if (!hit) return;
      input.dataset.geometryPreviewBound = 'v2';
      input.value = String(state[hit[0]]);
      input.addEventListener('input', () => {
        const key = hit[0];
        state[key] = clamp(input.value, RANGES[key]);
        save(state);
        applyGeometry();
        window.dispatchEvent(new CustomEvent('testhp:geometry-preview-changed', { detail: { ...state } }));
      });
    });
    return true;
  };

  const start = async () => {
    if (started || destroyed || !canvas?.isConnected) return;
    started = true;
    try {
      setStatus('Uruchamianie…');
      three = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js');
      const { OrbitControls } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js');
      if (destroyed || !canvas?.isConnected) return;

      renderer = new three.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setClearColor(0x0b1220, 1);
      renderer.outputColorSpace = three.SRGBColorSpace;
      renderer.toneMapping = three.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.05;

      scene = new three.Scene();
      scene.background = new three.Color(0x0b1220);
      camera = new three.PerspectiveCamera(30, 1, .01, 100);
      controls = new OrbitControls(camera, canvas);
      controls.enableDamping = true;
      controls.enablePan = true;
      controls.minDistance = 3;
      controls.maxDistance = 30;

      scene.add(new three.HemisphereLight(0xffffff, 0x334155, 2.5));
      const key = new three.DirectionalLight(0xffffff, 3);
      key.position.set(4, 7, 9);
      scene.add(key);
      const fill = new three.DirectionalLight(0xffd8c2, 1.25);
      fill.position.set(-5, 3, 5);
      scene.add(fill);
      const rim = new three.DirectionalLight(0xb9d8ff, 1);
      rim.position.set(1, 2, -6);
      scene.add(rim);

      buildModel();
      resizeObserver = new ResizeObserver(resize);
      resizeObserver.observe(host);
      resize();
      applyGeometry();
      renderLoop();

      canvas.addEventListener('webglcontextlost', event => {
        event.preventDefault();
        cancelAnimationFrame(renderFrame);
        setStatus('WebGL utracił kontekst — odśwież kartę, aby ponownie uruchomić podgląd.');
      }, { passive: false });
      setStatus('Gotowe');
    } catch (error) {
      started = false;
      console.error('[hand-geometry-live] preview failed', error);
      setStatus(`Podgląd niedostępny: ${error?.message || error}`);
      setMainStatus('Błąd dotyczy wyłącznie izolowanego podglądu. Canonical renderer nie jest używany.');
    }
  };

  const api = window.digitalTwinGeometry || {};
  api.version = 'isolated-preview-2';
  api.getState = () => ({ ...state });
  api.setParameter = (name, value) => {
    if (!(name in DEFAULT)) return { ok: false, error: `Unknown geometry parameter: ${name}` };
    state[name] = clamp(value, RANGES[name]);
    save(state);
    applyGeometry();
    return { ok: true, geometry: { ...state } };
  };
  api.setState = next => {
    Object.keys(DEFAULT).forEach(name => { state[name] = clamp(next?.[name] ?? state[name], RANGES[name]); });
    save(state);
    applyGeometry();
    return { ok: true, geometry: { ...state } };
  };
  api.reset = () => api.setState(DEFAULT);
  api.inspect = () => Object.fromEntries([...meshes].map(([name, mesh]) => [name, {
    position: mesh.position.toArray(), scale: mesh.scale.toArray(), rotation: [mesh.rotation.x, mesh.rotation.y, mesh.rotation.z]
  }]));
  window.digitalTwinGeometry = api;

  const boot = () => {
    if (destroyed) return;
    if (!ensureShell()) return;
    bindSliders();
    start();
  };

  const bootTimer = setInterval(() => {
    if (destroyed) return clearInterval(bootTimer);
    if (document.getElementById('hand-geometry-live-preview')) {
      bindSliders();
      if (started) clearInterval(bootTimer);
    } else {
      boot();
    }
  }, 250);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();

  window.addEventListener('beforeunload', () => {
    destroyed = true;
    clearInterval(bootTimer);
    cancelAnimationFrame(renderFrame);
    resizeObserver?.disconnect();
    controls?.dispose?.();
    renderer?.dispose?.();
    meshes.clear();
  }, { once: true });
})();
