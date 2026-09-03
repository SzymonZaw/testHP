(() => {
  'use strict';

  // Canonical geometry is the single owner of window.digitalTwinGeometry.
  // Other geometry scripts must not claim ownership; they may only consume
  // this API or provide compatibility UI around it.
  if (window.digitalTwinGeometry?.__canonicalBridgeInstalled) return;

  const DEFAULT = Object.freeze({ palmLength: 1, palmWidth: 1, fingerSpread: 1, thumbAngle: 1, taper: 1, thickness: 1 });
  const STORAGE = 'digitalTwinHandSurface.v1';
  const PARTS = ['palm', 'index', 'middle', 'ring', 'little', 'thumb'];
  let base = new Map();
  let lastSignature = '';
  let installed = false;
  let proceduralBuildPromise = null;

  const manager = () => window.spatialViewportManager;
  const active = () => manager()?.active;
  const root = () => active()?.root || active()?.scene?.getObjectByName?.('macro-hand-root') || null;
  const mesh = id => root()?.getObjectByName?.(id) || active()?.scene?.getObjectByName?.(id) || null;
  const clone = value => Object.fromEntries(Object.keys(DEFAULT).map(key => [key, Number(value?.[key] ?? DEFAULT[key])]));

  function captureBase() {
    const ids = PARTS;
    let count = 0;
    for (const id of ids) {
      const m = mesh(id);
      if (!m) continue;
      if (!base.has(m)) {
        base.set(m, {
          position: { x: m.position.x, y: m.position.y, z: m.position.z },
          scale: { x: m.scale.x, y: m.scale.y, z: m.scale.z },
          rotation: { x: m.rotation.x, y: m.rotation.y, z: m.rotation.z }
        });
      }
      count++;
    }
    return count;
  }

  async function ensureProceduralHand() {
    if (captureBase() === PARTS.length) return true;
    if (proceduralBuildPromise) return proceduralBuildPromise;

    proceduralBuildPromise = (async () => {
      const current = active();
      const scene = current?.scene;
      if (!scene) return false;

      // The macro hand is deliberately defined as code, not as a downloadable
      // GLB/OBJ asset. This keeps the highest layer deterministic and makes the
      // geometry available even when no external hand model asset is present.
      let THREE;
      try {
        THREE = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js');
      } catch {
        return false;
      }

      if (captureBase() === PARTS.length) return true;

      let handRoot = scene.getObjectByName?.('macro-hand-root');
      if (!handRoot) {
        handRoot = new THREE.Group();
        handRoot.name = 'macro-hand-root';
        scene.add(handRoot);
      }

      const existing = id => handRoot.getObjectByName?.(id);
      const material = () => new THREE.MeshStandardMaterial({ color: 0xc68b72, roughness: 0.72, metalness: 0.02 });
      const addCapsule = (id, radius, length, position, rotation = [0, 0, 0], segments = 18) => {
        if (existing(id)) return existing(id);
        const m = new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 8, segments), material());
        m.name = id;
        m.position.set(...position);
        m.rotation.set(...rotation);
        handRoot.add(m);
        return m;
      };

      addCapsule('palm', 1.55, 2.35, [0, -0.32, 0], [0, 0, 0], 24);
      addCapsule('index', 0.43, 2.18, [-1.05, 1.96, 0]);
      addCapsule('middle', 0.46, 2.58, [-0.35, 2.27, 0]);
      addCapsule('ring', 0.45, 2.34, [0.42, 2.14, 0]);
      addCapsule('little', 0.40, 1.98, [1.12, 1.88, 0], [0, 0, 0.08]);
      addCapsule('thumb', 0.48, 1.48, [-1.42, 0.02, 0.02], [0, 0, -0.82]);

      captureBase();
      const renderer = current?.renderer;
      const camera = current?.camera;
      if (renderer && camera) renderer.render(scene, camera);
      window.dispatchEvent(new CustomEvent('testhp:macro-hand-procedural-ready', {
        detail: { meshCount: captureBase(), source: 'embedded-procedural-v1' }
      }));
      return captureBase() === PARTS.length;
    })().finally(() => { proceduralBuildPromise = null; });

    return proceduralBuildPromise;
  }

  function readState() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      return clone(raw.geometry || DEFAULT);
    } catch {
      return clone(DEFAULT);
    }
  }

  function saveState(geometry) {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      raw.geometry = clone(geometry);
      raw.geometryCanonicalApplied = true;
      raw.geometryCanonicalAppliedAt = new Date().toISOString();
      localStorage.setItem(STORAGE, JSON.stringify(raw));
    } catch {}
  }

  function apply(geometry = readState(), reason = 'api') {
    const g = clone(geometry);
    const count = captureBase();
    if (!count) {
      void ensureProceduralHand().then(ok => { if (ok) apply(g, 'procedural-ready'); });
      return { ok: false, reason: 'canonical meshes unavailable', pending: true };
    }

    const applyMesh = (id, fn) => {
      const m = mesh(id);
      const b = m && base.get(m);
      if (m && b) fn(m, b);
    };

    applyMesh('palm', (m, b) => {
      m.position.set(b.position.x, b.position.y, b.position.z);
      m.scale.set(g.palmWidth * b.scale.x, g.palmLength * b.scale.y, g.thickness * b.scale.z);
    });

    ['index', 'middle', 'ring', 'little'].forEach(id => applyMesh(id, (m, b) => {
      m.position.set(b.position.x * g.fingerSpread, b.position.y, b.position.z);
      m.scale.set(g.thickness * b.scale.x, b.scale.y, g.taper * b.scale.z);
      m.rotation.set(b.rotation.x, b.rotation.y, b.rotation.z);
    }));

    applyMesh('thumb', (m, b) => {
      m.position.set(b.position.x, b.position.y, b.position.z);
      m.scale.set(g.thickness * b.scale.x, b.scale.y, b.scale.z);
      m.rotation.set(b.rotation.x, b.rotation.y, -0.82 * g.thumbAngle);
    });

    const renderer = active()?.renderer;
    const scene = active()?.scene;
    const camera = active()?.camera;
    if (renderer && scene && camera) renderer.render(scene, camera);

    lastSignature = JSON.stringify(g);
    window.dispatchEvent(new CustomEvent('testhp:geometry-canonical-applied', {
      detail: { geometry: g, reason, meshCount: count, source: 'embedded-procedural-v1' }
    }));
    return { ok: true, meshCount: count, geometry: g, source: 'embedded-procedural-v1' };
  }

  function reset() {
    const result = apply(DEFAULT, 'reset');
    saveState(DEFAULT);
    return result;
  }

  window.digitalTwinGeometry = {
    version: 'canonical-geometry-4',
    __canonicalBridgeInstalled: true,
    getState: readState,
    setParameter(name, value) {
      if (!(name in DEFAULT)) return { ok: false, error: `Unknown geometry parameter: ${name}` };
      const next = { ...readState(), [name]: Number(value) };
      saveState(next);
      return apply(next, 'set-parameter');
    },
    setState(next) {
      const merged = { ...readState(), ...next };
      saveState(merged);
      return apply(merged, 'set-state');
    },
    reset,
    apply,
    ensureProceduralHand,
    inspect() {
      const result = {};
      PARTS.forEach(id => {
        const m = mesh(id);
        if (m) result[id] = {
          position: m.position.toArray(),
          scale: m.scale.toArray(),
          rotation: [m.rotation.x, m.rotation.y, m.rotation.z]
        };
      });
      return result;
    }
  };

  function installCss() {
    if (document.getElementById('hss-canonical-geometry-css')) return;
    const style = document.createElement('style');
    style.id = 'hss-canonical-geometry-css';
    style.textContent = '.hss-canonical-geometry-panel .hss-grid{display:block}.hss-canonical-geometry-panel .hss-card{margin-bottom:12px}.hss-canonical-geometry-panel .hss-geometry-apply-note{color:#53616c}.hss-geometry-preview-card{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px;border:1px solid var(--border,#d8dee8);border-radius:10px;background:rgba(79,111,143,.05);margin-bottom:12px}.hss-geometry-preview-card strong{display:block;font-size:13px}.hss-geometry-preview-card span{display:block;font-size:12px;color:#667085;margin-top:3px}.hss-geometry-preview-card button{white-space:nowrap}@media(max-width:700px){.hss-geometry-preview-card{display:block}.hss-geometry-preview-card button{margin-top:8px}}';
    document.head.appendChild(style);
  }

  function ensureLayout() {
    const studio = document.getElementById('hand-surface-studio');
    if (!studio) return;
    studio.classList.add('hss-canonical-geometry-panel');
    installCss();
  }

  function ensurePreviewLink() {
    const studio = document.getElementById('hand-surface-studio');
    const content = document.getElementById('hss-content');
    if (!studio || !content) return;
    const tab = studio.querySelector('.hss-tabs button[data-tab="geometry"]');
    if (!tab?.classList.contains('active') || content.querySelector('.hss-geometry-preview-card')) return;
    const card = document.createElement('div');
    card.className = 'hss-geometry-preview-card';
    card.innerHTML = '<div><strong>Podgląd modelu 3D</strong><span>Suwaki zmieniają model natychmiast. Model jest w górnej części strony.</span></div><button type="button" class="secondary">Pokaż model 3D</button>';
    card.querySelector('button').onclick = () => document.querySelector('.twin-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    content.prepend(card);
  }

  function wireControls() {
    const studio = document.getElementById('hand-surface-studio');
    if (!studio || studio.dataset.canonicalGeometryWired === '1') return false;
    studio.dataset.canonicalGeometryWired = '1';
    studio.addEventListener('input', event => {
      const input = event.target?.closest?.('[data-g]');
      if (!input || !(input.dataset.g in DEFAULT)) return;
      window.digitalTwinGeometry.setParameter(input.dataset.g, Number(input.value));
      const label = studio.querySelector('.hss-geometry-value[data-value-for="' + input.dataset.g + '"]');
      if (label) label.textContent = Number(input.value).toFixed(2) + '×';
    }, true);
    return true;
  }

  function sync() {
    ensureLayout();
    const wired = wireControls();
    ensurePreviewLink();
    if (active() && captureBase() === 0) void ensureProceduralHand();
    const state = readState();
    if (active() && JSON.stringify(state) !== lastSignature) apply(state, 'sync');
    return wired;
  }

  function boot() {
    if (installed) return;
    installed = true;
    const observer = new MutationObserver(sync);
    observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener('testhp:deep-3d-active', () => setTimeout(sync, 0));
    window.addEventListener('testhp:viewport-manager-ready', () => setTimeout(sync, 0));
    window.addEventListener('testhp:spatial-layer-changed', () => setTimeout(sync, 0));
    window.addEventListener('testhp:macro-hand-procedural-ready', () => setTimeout(sync, 0));
    [0, 100, 300, 800, 1500, 3000].forEach(ms => setTimeout(sync, ms));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();