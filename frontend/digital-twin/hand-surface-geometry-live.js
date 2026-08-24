(() => {
  const PARAMS = Object.freeze({
    palmLength: 1,
    palmWidth: 1,
    thickness: 1,
    fingerSpread: 1,
    taper: 1,
    thumbAngle: 1,
  });
  const RANGES = {
    palmLength: [0.75, 1.25], palmWidth: [0.75, 1.25], thickness: [0.75, 1.25],
    fingerSpread: [0.7, 1.3], taper: [0.7, 1.3], thumbAngle: [0.7, 1.3],
  };
  const FINGERS = ['index', 'middle', 'ring', 'little'];
  const KEY = 'digitalTwinHandGeometry.live.v1';
  const clamp = (value, min, max) => Math.min(max, Math.max(min, Number(value) || 1));
  const readState = () => {
    try { const raw = JSON.parse(localStorage.getItem(KEY) || 'null'); return { ...PARAMS, ...(raw?.parameters || raw || {}) }; }
    catch { return { ...PARAMS }; }
  };

  let state = readState();
  let previewHost = null, previewCanvas = null, previewMeshes = new Map();
  let previewRenderer = null, previewScene = null, previewCamera = null, previewControls = null;
  let previewResizeObserver = null, bootObserver = null, hostObserver = null;
  let renderFrame = 0;

  const getMainMeshes = () => {
    const manager = window.spatialViewportManager;
    const scene = manager?.active?.scene;
    const roots = [manager?.active?.root, scene].filter(Boolean);
    const found = new Map();
    const visit = object => {
      if (!object || found.size >= 6) return;
      const name = String(object.name || '').replace(/^skin:/, '');
      if (['palm', ...FINGERS, 'thumb'].includes(name) && object.isMesh) found.set(name, object);
      object.children?.forEach(visit);
    };
    roots.forEach(visit);
    return found;
  };

  const baselines = new WeakMap();
  const baseline = mesh => {
    let value = baselines.get(mesh);
    if (!value) { value = { position: mesh.position.clone(), scale: mesh.scale.clone(), rotationZ: mesh.rotation.z }; baselines.set(mesh, value); }
    return value;
  };

  const applyToMain = () => {
    const meshes = getMainMeshes();
    const palm = meshes.get('palm');
    if (!palm) return meshes;
    const pb = baseline(palm);
    palm.scale.set(pb.scale.x * state.palmWidth, pb.scale.y * state.palmLength, pb.scale.z * state.thickness);
    FINGERS.forEach((name, index) => {
      const mesh = meshes.get(name); if (!mesh) return;
      const b = baseline(mesh), center = (FINGERS.length - 1) / 2;
      mesh.position.x = b.position.x + (index - center) * 0.20 * (state.fingerSpread - 1);
      const width = 1 - 0.22 * (state.taper - 1);
      mesh.scale.set(b.scale.x * width, b.scale.y, b.scale.z * state.thickness);
    });
    const thumb = meshes.get('thumb');
    if (thumb) {
      const b = baseline(thumb);
      thumb.rotation.z = b.rotationZ - 0.42 * (state.thumbAngle - 1);
      thumb.scale.set(b.scale.x * (1 - 0.10 * (state.taper - 1)), b.scale.y, b.scale.z * state.thickness);
    }
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-geometry-changed', { detail: { parameters: { ...state }, meshCount: meshes.size, source: 'digitalTwinGeometry' } }));
    return meshes;
  };

  const save = () => localStorage.setItem(KEY, JSON.stringify({ schema: 'hand-surface-geometry-live-v1', parameters: state, updatedAt: new Date().toISOString() }));

  const geometryApi = () => {
    const existing = window.digitalTwinGeometry;
    if (existing?.__liveBridgeInstalled) return existing;
    const bridge = existing || {};
    bridge.version = 'canonical-geometry-1';
    bridge.__liveBridgeInstalled = true;
    bridge.getState = () => ({ ...state });
    bridge.inspect = () => Object.fromEntries([...getMainMeshes()].map(([id, mesh]) => [id, { position: mesh.position.toArray(), scale: mesh.scale.toArray(), rotation: [mesh.rotation.x, mesh.rotation.y, mesh.rotation.z] }]));
    bridge.setParameter = (name, value) => {
      if (!(name in PARAMS)) return { ok: false, error: `Unknown geometry parameter: ${name}` };
      const [min, max] = RANGES[name]; state = { ...state, [name]: clamp(value, min, max) }; save();
      const meshes = applyToMain(); updatePreview(); updateUi();
      return { ok: true, meshCount: meshes.size, geometry: { ...state } };
    };
    bridge.setState = next => { Object.keys(PARAMS).forEach(name => { if (next?.[name] != null) bridge.setParameter(name, next[name]); }); return { ok: true, geometry: { ...state } }; };
    bridge.reset = () => bridge.setState(PARAMS);
    window.digitalTwinGeometry = bridge;
    return bridge;
  };

  const geometryRoot = () => {
    const title = [...document.querySelectorAll('strong')].find(el => el.textContent?.trim() === 'Geometria dłoni');
    if (!title) return null;
    const intro = title.closest('.hss-geometry-intro'), container = intro?.parentElement;
    if (intro && container) return { title, intro, container };
    const parent = title.parentElement;
    return parent ? { title, intro: null, container: parent } : null;
  };

  const setStatus = text => { const status = previewHost?.querySelector('[data-geometry-preview-status]'); if (status) status.textContent = text; };
  const updateMainConnection = () => {
    const status = previewHost?.querySelector('[data-geometry-main-status]'); if (!status) return;
    const count = getMainMeshes().size;
    status.textContent = count >= 6 ? `Połączono z modelem głównym · ${count} elementów geometrii` : 'Podgląd działa lokalnie. Model główny jest chwilowo niedostępny.';
  };
  const resizePreview = () => {
    if (!previewRenderer || !previewCamera || !previewHost) return;
    const rect = previewHost.getBoundingClientRect(), width = Math.max(1, rect.width), height = Math.max(1, rect.height);
    previewRenderer.setSize(width, height, false); previewCamera.aspect = width / height; previewCamera.updateProjectionMatrix();
  };
  const updatePreview = () => {
    if (!previewMeshes.size) return;
    const palm = previewMeshes.get('palm'); if (palm) palm.scale.set(state.palmWidth, state.palmLength, state.thickness);
    const baseX = [-1.05, -0.35, 0.42, 1.12];
    FINGERS.forEach((name, index) => { const mesh = previewMeshes.get(name); if (!mesh) return; const center = 1.5; mesh.position.x = baseX[index] + (index - center) * 0.20 * (state.fingerSpread - 1); const width = 1 - 0.22 * (state.taper - 1); mesh.scale.set(width, 1, state.thickness); });
    const thumb = previewMeshes.get('thumb'); if (thumb) { thumb.rotation.z = -0.82 - 0.42 * (state.thumbAngle - 1); thumb.scale.set(1 - 0.10 * (state.taper - 1), 1, state.thickness); }
    setStatus(Object.values(state).every(value => Number(value) === 1) ? 'Live · wartości domyślne' : 'Live · zmieniona geometria');
  };

  const disposePreview = () => {
    if (renderFrame) cancelAnimationFrame(renderFrame);
    renderFrame = 0;
    previewResizeObserver?.disconnect(); previewResizeObserver = null;
    previewControls?.dispose?.(); previewControls = null;
    previewScene?.traverse?.(obj => { if (obj.geometry?.dispose) obj.geometry.dispose(); if (obj.material) { const materials = Array.isArray(obj.material) ? obj.material : [obj.material]; materials.forEach(m => m.dispose?.()); } });
    previewRenderer?.dispose?.();
    previewRenderer = null; previewScene = null; previewCamera = null; previewMeshes = new Map(); previewCanvas = null; previewHost = null;
  };

  const makePreview = async () => {
    if (!previewHost || previewRenderer || !previewCanvas) return;
    try {
      const THREE = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js');
      const { OrbitControls } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js');
      if (!previewCanvas?.isConnected) return;
      previewRenderer = new THREE.WebGLRenderer({ canvas: previewCanvas, antialias: true, alpha: true });
      previewRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); previewRenderer.outputColorSpace = THREE.SRGBColorSpace;
      previewScene = new THREE.Scene(); previewCamera = new THREE.PerspectiveCamera(30, 1, 0.1, 100); previewCamera.position.set(0, 0.5, 8.6);
      previewControls = new OrbitControls(previewCamera, previewCanvas); previewControls.enableDamping = true; previewControls.minDistance = 5; previewControls.maxDistance = 13; previewControls.target.set(0, 0.3, 0);
      previewScene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 2.1)); const light = new THREE.DirectionalLight(0xffffff, 2.4); light.position.set(4, 6, 8); previewScene.add(light);
      const root = new THREE.Group(); root.rotation.x = -0.14; previewScene.add(root);
      const material = new THREE.MeshStandardMaterial({ color: 0xc68b72, roughness: 0.74 });
      const add = (id, position, radius, length, rotation = [0, 0, 0]) => { const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 8, 18), material.clone()); mesh.name = id; mesh.position.set(...position); mesh.rotation.set(...rotation); root.add(mesh); previewMeshes.set(id, mesh); };
      add('wrist', [0, -2.15, 0], 0.72, 1.25); add('palm', [0, -0.35, 0], 1.55, 2.25); add('thumb', [-1.45, 0, 0.02], 0.48, 1.45, [0, 0, -0.82]); add('index', [-1.05, 1.95, 0], 0.43, 2.15); add('middle', [-0.35, 2.25, 0], 0.46, 2.55); add('ring', [0.42, 2.12, 0], 0.45, 2.32); add('little', [1.12, 1.86, 0], 0.40, 1.95, [0, 0, 0.08]);
      previewResizeObserver = new ResizeObserver(resizePreview); previewResizeObserver.observe(previewHost);
      const loop = () => { if (!previewRenderer || !previewCanvas?.isConnected) return; resizePreview(); previewControls?.update(); previewRenderer.render(previewScene, previewCamera); renderFrame = requestAnimationFrame(loop); }; loop(); updatePreview();
    } catch (error) { setStatus(`Podgląd niedostępny: ${error.message}`); }
  };

  const bindSliders = root => {
    if (!root) return;
    const inputs = [...root.querySelectorAll('input[type="range"]')];
    const map = [['palmLength', /długość dłoni/i], ['palmWidth', /szerokość dłoni/i], ['thickness', /grubość powierzchni/i], ['fingerSpread', /rozstaw palców/i], ['taper', /zwężenie palców/i], ['thumbAngle', /ustawienie kciuka/i]];
    inputs.forEach(input => { if (input.dataset.geometryLiveBound === '1') return; const text = input.closest('label,div')?.textContent || ''; const match = map.find(([, regex]) => regex.test(text)); if (!match) return; input.dataset.geometryLiveBound = '1'; input.addEventListener('input', () => window.digitalTwinGeometry.setParameter(match[0], input.value)); });
  };
  const syncSliders = root => {
    if (!root) return;
    const map = [['palmLength', /długość dłoni/i], ['palmWidth', /szerokość dłoni/i], ['thickness', /grubość powierzchni/i], ['fingerSpread', /rozstaw palców/i], ['taper', /zwężenie palców/i], ['thumbAngle', /ustawienie kciuka/i]];
    [...root.querySelectorAll('input[type="range"]')].forEach(input => { const text = input.closest('label,div')?.textContent || ''; const match = map.find(([, regex]) => regex.test(text)); if (match) input.value = state[match[0]]; });
  };

  const installUi = () => {
    const existingHost = document.getElementById('hand-geometry-live-preview');
    if (existingHost?.isConnected) return true;
    if (existingHost && !existingHost.isConnected) existingHost.remove();
    const root = geometryRoot(); if (!root) return false;
    const host = document.createElement('section'); host.id = 'hand-geometry-live-preview';
    host.style.cssText = 'margin:14px 0 16px;border:1px solid var(--border,#d8dee8);border-radius:12px;overflow:hidden;background:var(--panel,#fff)';
    host.innerHTML = `<div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;padding:13px 14px;border-bottom:1px solid var(--border,#d8dee8)"><div><strong style="display:block;font-size:14px">Podgląd 3D</strong><span style="display:block;margin-top:3px;font-size:12px;color:#667085">Przesuwaj suwaki i obserwuj dokładnie ten sam efekt w podglądzie.</span></div><span data-geometry-preview-status style="font-size:11px;font-weight:800;color:#027a48">Uruchamianie…</span></div><div data-geometry-preview-canvas style="height:360px;background:#0d1117;position:relative"><canvas aria-label="Podgląd geometrii dłoni" style="width:100%;height:100%;display:block"></canvas><div style="position:absolute;left:12px;bottom:10px;color:#c9d1d9;font-size:11px;background:rgba(13,17,23,.72);padding:6px 8px;border-radius:7px">Przeciągnij · kółko myszy = zoom</div></div><div data-geometry-main-status style="padding:9px 12px;font-size:11px;color:#667085;border-top:1px solid var(--border,#d8dee8)"></div>`;
    previewHost = host.querySelector('[data-geometry-preview-canvas]'); previewCanvas = host.querySelector('canvas');
    if (root.intro?.parentElement === root.container) root.container.insertBefore(host, root.intro.nextSibling); else root.container.appendChild(host);
    bindSliders(root.container); syncSliders(root.container); updateMainConnection(); makePreview();
    return true;
  };

  const updateUi = () => { const host = document.getElementById('hand-geometry-live-preview'); if (!host) return; const status = host.querySelector('[data-geometry-preview-status]'); if (status) status.textContent = Object.values(state).every(value => Number(value) === 1) ? 'Live · wartości domyślne' : 'Live · zmieniona geometria'; updateMainConnection(); };

  const ensureInstalled = () => {
    const host = document.getElementById('hand-geometry-live-preview');
    if (!host || !host.isConnected) { if (previewRenderer || previewHost) disposePreview(); installUi(); }
  };

  const boot = () => {
    geometryApi(); installUi();
    if (!bootObserver) {
      bootObserver = new MutationObserver(() => {
        ensureInstalled();
        const root = geometryRoot(); if (root) { bindSliders(root.container); syncSliders(root.container); updateMainConnection(); }
      });
      bootObserver.observe(document.body, { childList: true, subtree: true });
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();