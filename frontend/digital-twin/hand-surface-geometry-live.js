(() => {
  const PARAMS = Object.freeze({
    palmLength: 1,
    palmWidth: 1,
    thickness: 1,
    fingerSpread: 1,
    taper: 1,
    thumbAngle: 1,
  });
  const FINGERS = ['index', 'middle', 'ring', 'little'];
  const clamp = (v, min, max) => Math.min(max, Math.max(min, Number(v) || 1));
  const readState = () => {
    try {
      const raw = JSON.parse(localStorage.getItem('digitalTwinHandGeometry.live.v1') || 'null');
      return { ...PARAMS, ...(raw?.parameters || raw || {}) };
    } catch { return { ...PARAMS }; }
  };
  let state = readState();
  let preview = null;
  let previewMeshes = new Map();
  let previewCamera = null;
  let previewRenderer = null;
  let previewScene = null;
  let previewControls = null;
  let resizeObserver = null;

  const getMainMeshes = () => {
    const manager = window.spatialViewportManager;
    const scene = manager?.active?.scene;
    const roots = [manager?.active?.root, scene].filter(Boolean);
    const found = new Map();
    const visit = obj => {
      if (!obj || found.size >= 6) return;
      const name = String(obj.name || '').replace(/^skin:/, '');
      if (['palm', ...FINGERS, 'thumb'].includes(name) && obj.isMesh) found.set(name, obj);
      obj.children?.forEach(visit);
    };
    roots.forEach(visit);
    return found;
  };

  const baselines = new WeakMap();
  const baseline = mesh => {
    if (!mesh) return null;
    let b = baselines.get(mesh);
    if (!b) {
      b = { position: mesh.position.clone(), scale: mesh.scale.clone(), rotationZ: mesh.rotation.z };
      baselines.set(mesh, b);
    }
    return b;
  };

  function applyToMain() {
    const meshes = getMainMeshes();
    if (!meshes.has('palm')) return meshes;
    const palm = meshes.get('palm');
    const pb = baseline(palm);
    palm.scale.set(pb.scale.x * state.palmWidth, pb.scale.y * state.palmLength, pb.scale.z * state.thickness);

    FINGERS.forEach((name, index) => {
      const mesh = meshes.get(name);
      if (!mesh) return;
      const b = baseline(mesh);
      const center = (FINGERS.length - 1) / 2;
      const spreadOffset = (index - center) * 0.20 * (state.fingerSpread - 1);
      mesh.position.x = b.position.x + spreadOffset;
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
  }

  function save() {
    localStorage.setItem('digitalTwinHandGeometry.live.v1', JSON.stringify({ schema: 'hand-surface-geometry-live-v1', parameters: state, updatedAt: new Date().toISOString() }));
  }

  function api() {
    const existing = window.digitalTwinGeometry;
    if (existing?.__liveBridgeInstalled) return existing;
    const bridge = existing || {};
    bridge.version = 'canonical-geometry-1';
    bridge.__liveBridgeInstalled = true;
    bridge.getState = () => ({ ...state });
    bridge.inspect = () => Object.fromEntries([...getMainMeshes()].map(([id, mesh]) => [id, {
      position: mesh.position.toArray(), scale: mesh.scale.toArray(), rotation: [mesh.rotation.x, mesh.rotation.y, mesh.rotation.z]
    }]));
    bridge.setParameter = (name, value) => {
      if (!(name in PARAMS)) return { ok: false, error: `Unknown geometry parameter: ${name}` };
      const ranges = { palmLength: [0.75, 1.25], palmWidth: [0.75, 1.25], thickness: [0.75, 1.25], fingerSpread: [0.7, 1.3], taper: [0.7, 1.3], thumbAngle: [0.7, 1.3] };
      const [min, max] = ranges[name];
      state = { ...state, [name]: clamp(value, min, max) };
      save();
      const meshes = applyToMain();
      updatePreview();
      updateUi();
      return { ok: true, meshCount: meshes.size, geometry: { ...state } };
    };
    bridge.setState = next => {
      Object.keys(PARAMS).forEach(k => { if (next?.[k] != null) bridge.setParameter(k, next[k]); });
      return { ok: true, geometry: { ...state } };
    };
    bridge.reset = () => bridge.setState(PARAMS);
    window.digitalTwinGeometry = bridge;
    return bridge;
  }

  async function makePreview() {
    if (previewRenderer || !preview) return;
    try {
      const THREE = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js');
      const { OrbitControls } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js');
      const canvas = preview.querySelector('canvas');
      previewRenderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      previewRenderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
      previewRenderer.outputColorSpace = THREE.SRGBColorSpace;
      previewScene = new THREE.Scene();
      previewCamera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
      previewCamera.position.set(0, 0.5, 8.6);
      previewControls = new OrbitControls(previewCamera, canvas);
      previewControls.enableDamping = true;
      previewControls.minDistance = 5;
      previewControls.maxDistance = 13;
      previewControls.target.set(0, 0.3, 0);
      previewScene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 2.1));
      const light = new THREE.DirectionalLight(0xffffff, 2.4); light.position.set(4, 6, 8); previewScene.add(light);
      const root = new THREE.Group(); root.rotation.x = -0.14; previewScene.add(root);
      const material = new THREE.MeshStandardMaterial({ color: 0xc68b72, roughness: 0.74 });
      const add = (id, p, r, l, rot = [0, 0, 0]) => {
        const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(r, l, 8, 18), material.clone());
        mesh.name = id; mesh.position.set(...p); mesh.rotation.set(...rot); root.add(mesh); previewMeshes.set(id, mesh);
      };
      add('wrist', [0, -2.15, 0], .72, 1.25);
      add('palm', [0, -.35, 0], 1.55, 2.25);
      add('thumb', [-1.45, 0, .02], .48, 1.45, [0, 0, -.82]);
      add('index', [-1.05, 1.95, 0], .43, 2.15);
      add('middle', [-.35, 2.25, 0], .46, 2.55);
      add('ring', [.42, 2.12, 0], .45, 2.32);
      add('little', [1.12, 1.86, 0], .40, 1.95, [0, 0, .08]);
      resizeObserver = new ResizeObserver(() => resizePreview());
      resizeObserver.observe(preview);
      const loop = () => { resizePreview(); previewControls?.update(); previewRenderer?.render(previewScene, previewCamera); requestAnimationFrame(loop); };
      loop();
      updatePreview();
    } catch (error) {
      const status = preview.querySelector('[data-geometry-preview-status]');
      if (status) status.textContent = `Podgląd niedostępny: ${error.message}`;
    }
  }

  function resizePreview() {
    if (!previewRenderer || !previewCamera || !preview) return;
    const rect = preview.getBoundingClientRect();
    const w = Math.max(1, rect.width), h = Math.max(1, rect.height);
    previewRenderer.setSize(w, h, false);
    previewCamera.aspect = w / h;
    previewCamera.updateProjectionMatrix();
  }

  function updatePreview() {
    if (!previewMeshes.size) return;
    const setScale = (id, x, y, z) => { const m = previewMeshes.get(id); if (m) m.scale.set(x, y, z); };
    const palm = previewMeshes.get('palm'); if (palm) palm.scale.set(state.palmWidth, state.palmLength, state.thickness);
    FINGERS.forEach((name, index) => {
      const m = previewMeshes.get(name); if (!m) return;
      const center = (FINGERS.length - 1) / 2;
      m.position.x = [-1.05, -.35, .42, 1.12][index] + (index - center) * 0.20 * (state.fingerSpread - 1);
      const width = 1 - 0.22 * (state.taper - 1);
      m.scale.set(width, 1, state.thickness);
    });
    const thumb = previewMeshes.get('thumb');
    if (thumb) { thumb.rotation.z = -.82 - 0.42 * (state.thumbAngle - 1); thumb.scale.set(1 - 0.10 * (state.taper - 1), 1, state.thickness); }
    const status = preview.querySelector('[data-geometry-preview-status]');
    if (status) status.textContent = `Live · ${Object.values(state).every(v => Number(v) === 1) ? 'wartości domyślne' : 'zmieniona geometria'}`;
  }

  function installUi() {
    if (document.getElementById('hand-geometry-live-preview')) return true;
    const geometrySection = document.querySelector('#hand-surface-unified [data-hsu-section="material"] [data-tab="geometry"], #hand-surface-unified [data-hsu-section="material"] .hand-geometry, #hand-surface-studio [data-tab="geometry"]');
    const candidates = [...document.querySelectorAll('[data-tab="geometry"]')];
    const tabButton = candidates.find(x => /geometr/i.test(x.textContent || ''));
    const section = geometrySection?.closest('[data-hsu-section]') || document.querySelector('#hand-surface-unified [data-hsu-section="material"]');
    if (!section || !tabButton) return false;
    const host = document.createElement('section');
    host.id = 'hand-geometry-live-preview';
    host.style.cssText = 'margin:0 0 14px;border:1px solid var(--border,#d8dee8);border-radius:12px;overflow:hidden;background:var(--panel,#fff)';
    host.innerHTML = `<div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;padding:13px 14px;border-bottom:1px solid var(--border,#d8dee8)"><div><strong style="display:block;font-size:14px">Podgląd na żywo</strong><span style="display:block;margin-top:3px;font-size:12px;color:#667085">Ten sam zestaw parametrów wpływa na model główny i na podgląd poniżej.</span></div><span data-geometry-preview-status style="font-size:11px;font-weight:800;color:#027a48">Live</span></div><div data-geometry-preview-canvas style="height:360px;background:#0d1117;position:relative"><canvas aria-label="Podgląd geometrii dłoni" style="width:100%;height:100%;display:block"></canvas><div style="position:absolute;left:12px;bottom:10px;color:#c9d1d9;font-size:11px;background:rgba(13,17,23,.72);padding:6px 8px;border-radius:7px">Przeciągnij · kółko myszy = zoom</div></div><div data-geometry-main-status style="padding:9px 12px;font-size:11px;color:#667085;border-top:1px solid var(--border,#d8dee8)"></div>`;
    const target = section.querySelector('[data-tab="geometry"]')?.parentElement || section.querySelector('.hsu-subnav')?.nextElementSibling || section.firstElementChild;
    section.insertBefore(host, target || null);
    preview = host.querySelector('[data-geometry-preview-canvas]');
    const mainStatus = host.querySelector('[data-geometry-main-status]');
    const refreshMainStatus = () => {
      const count = getMainMeshes().size;
      if (mainStatus) mainStatus.textContent = count >= 6 ? `Połączono z modelem głównym · ${count} elementów geometrii` : 'Model główny nie jest jeszcze gotowy — podgląd lokalny działa niezależnie.';
    };
    const bindSliders = () => {
      const root = section;
      const inputs = [...root.querySelectorAll('input[type="range"]')];
      const map = [
        ['palmLength', /długość dłoni/i], ['palmWidth', /szerokość dłoni/i], ['thickness', /grubość powierzchni/i],
        ['fingerSpread', /rozstaw palców/i], ['taper', /zwężenie palców/i], ['thumbAngle', /ustawienie kciuka/i]
      ];
      inputs.forEach(input => {
        if (input.dataset.geometryLiveBound === '1') return;
        const text = input.closest('label,div')?.textContent || '';
        const item = map.find(([, re]) => re.test(text));
        if (!item) return;
        input.dataset.geometryLiveBound = '1';
        input.addEventListener('input', () => window.digitalTwinGeometry.setParameter(item[0], input.value));
      });
      refreshMainStatus();
    };
    const syncInputs = () => {
      [...section.querySelectorAll('input[type="range"]')].forEach(input => {
        const text = input.closest('label,div')?.textContent || '';
        const map = [['palmLength',/długość dłoni/i],['palmWidth',/szerokość dłoni/i],['thickness',/grubość powierzchni/i],['fingerSpread',/rozstaw palców/i],['taper',/zwężenie palców/i],['thumbAngle',/ustawienie kciuka/i]];
        const item = map.find(([,re]) => re.test(text));
        if (item) input.value = state[item[0]];
      });
    };
    bindSliders();
    syncInputs();
    new MutationObserver(() => { bindSliders(); refreshMainStatus(); }).observe(section, { childList: true, subtree: true });
    window.addEventListener('testhp:hand-surface-geometry-changed', refreshMainStatus);
    makePreview();
    return true;
  }

  function updateUi() {
    const host = document.getElementById('hand-geometry-live-preview');
    if (!host) return;
    const status = host.querySelector('[data-geometry-preview-status]');
    if (status) status.textContent = `Live · ${Object.values(state).every(v => Number(v) === 1) ? 'wartości domyślne' : 'zmieniona geometria'}`;
  }

  function boot() {
    api();
    if (installUi()) return;
    const observer = new MutationObserver(() => { if (installUi()) observer.disconnect(); });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => { observer.disconnect(); installUi(); }, 15000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();
