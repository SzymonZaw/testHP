(() => {
  'use strict';

  if (window.__testhpReferenceHand3DViewerInstalled) return;
  window.__testhpReferenceHand3DViewerInstalled = true;

  const NIH_GLB_URL = 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811';
  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const VIEWER_VERSION = 'reference-3d-safe-2';
  const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
  const GLTF_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';

  let bootPromise = null;
  let sceneState = null;

  function state(patch = {}) {
    window.__testhpReferenceHand3DViewerState = Object.freeze({
      installed: true,
      version: VIEWER_VERSION,
      active: false,
      loading: false,
      loaded: false,
      sourceId: SOURCE_ID,
      assetUrl: NIH_GLB_URL,
      provenance: 'public_reference',
      regionId: window.__testhpReferenceHandState?.regionId || 'palm',
      error: null,
      ...patch,
    });
    return window.__testhpReferenceHand3DViewerState;
  }

  function addStyles() {
    if (document.getElementById('testhp-reference-hand-3d-style')) return;
    const style = document.createElement('style');
    style.id = 'testhp-reference-hand-3d-style';
    style.textContent = `
      .dt-reference-3d-card{position:relative;min-height:360px;width:100%;border:1px solid #263545;border-radius:16px;background:#0b1118;overflow:hidden;isolation:isolate}
      .dt-reference-3d-canvas{display:block;width:100%;height:100%;min-height:360px;touch-action:none;cursor:grab}
      .dt-reference-3d-canvas:active{cursor:grabbing}
      .dt-reference-3d-overlay{position:absolute;inset:0;pointer-events:none;z-index:2}
      .dt-reference-3d-title{position:absolute;left:16px;top:14px;padding:8px 10px;border:1px solid #344456;border-radius:10px;background:#0d151ee8;color:#dce7f2;font:700 11px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase}
      .dt-reference-3d-status{position:absolute;left:16px;bottom:14px;max-width:70%;padding:7px 9px;border-radius:9px;background:#0d151ee8;color:#9fb0c2;font:600 11px/1.35 system-ui,sans-serif}
      .dt-reference-3d-fallback{position:absolute;inset:0;display:grid;place-items:center;padding:32px;text-align:center;color:#9fb0c2;font:600 12px/1.5 system-ui,sans-serif;background:radial-gradient(circle at 50% 42%,#15242f 0,#0b1118 62%)}
      .dt-reference-3d-fallback strong{display:block;color:#dce7f2;margin-bottom:6px;font-size:13px}
      .dt-reference-3d-fallback a{color:#9bd8c4;pointer-events:auto}
    `;
    document.head.appendChild(style);
  }

  function findHost() {
    return document.getElementById('testhp-end-user-layer');
  }

  function ensureCard() {
    const host = findHost();
    if (!host) return null;
    let card = host.querySelector('.dt-reference-3d-card');
    if (card) return card;

    card = document.createElement('section');
    card.className = 'dt-reference-3d-card';
    card.setAttribute('aria-label', 'NIH 3D reference hand');
    card.innerHTML = `
      <canvas class="dt-reference-3d-canvas" aria-label="Interactive NIH 3D reference hand"></canvas>
      <div class="dt-reference-3d-overlay">
        <div class="dt-reference-3d-title">REFERENCE HAND · NIH 3D · 3DPX-017237</div>
        <div class="dt-reference-3d-status">Public reference geometry · not user health data</div>
      </div>
    `;

    const preferred = host.querySelector('.center .viewport, .viewport');
    if (preferred) {
      preferred.style.position = preferred.style.position || 'relative';
      preferred.style.minHeight = preferred.style.minHeight || '360px';
      preferred.appendChild(card);
    } else {
      const anchor = host.querySelector('.dt-reference-runtime-state, .workspace, .dt-phase9');
      if (anchor?.parentElement) anchor.parentElement.insertBefore(card, anchor.nextSibling);
      else host.appendChild(card);
    }
    return card;
  }

  function fallback(card, message) {
    if (!card) return;
    const existing = card.querySelector('.dt-reference-3d-fallback');
    if (existing) existing.querySelector('span').textContent = message;
    else {
      const box = document.createElement('div');
      box.className = 'dt-reference-3d-fallback';
      box.innerHTML = `<div><strong>Reference geometry unavailable in the local viewer</strong><span></span><br><a href="https://3d.nih.gov/entries/3DPX-017237" target="_blank" rel="noopener noreferrer">Open NIH 3D reference</a></div>`;
      box.querySelector('span').textContent = message;
      card.appendChild(box);
    }
  }

  function normalizeObject(object, THREE) {
    const box = new THREE.Box3().setFromObject(object);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxSize = Math.max(size.x, size.y, size.z) || 1;
    const scale = 4.8 / maxSize;
    object.scale.setScalar(scale);
    object.position.set(-center.x * scale, -center.y * scale, -center.z * scale);
  }

  function createScene(card, THREE, GLTFLoader) {
    const canvas = card.querySelector('.dt-reference-3d-canvas');
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.setClearColor(0x0b1118, 1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
    camera.position.set(0, 0.2, 7.5);

    scene.add(new THREE.HemisphereLight(0xe8f2ff, 0x10202b, 2.2));
    const key = new THREE.DirectionalLight(0xffffff, 3.0);
    key.position.set(4, 6, 8);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x9bd8c4, 1.1);
    fill.position.set(-5, 2, 3);
    scene.add(fill);

    const root = new THREE.Group();
    scene.add(root);
    const loader = new GLTFLoader();

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const width = Math.max(1, rect.width);
      const height = Math.max(1, rect.height);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    canvas.addEventListener('pointerdown', event => {
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      canvas.setPointerCapture?.(event.pointerId);
    });
    canvas.addEventListener('pointermove', event => {
      if (!dragging) return;
      root.rotation.y += (event.clientX - lastX) * 0.008;
      root.rotation.x += (event.clientY - lastY) * 0.006;
      lastX = event.clientX;
      lastY = event.clientY;
    });
    const stop = () => { dragging = false; };
    canvas.addEventListener('pointerup', stop);
    canvas.addEventListener('pointercancel', stop);
    canvas.addEventListener('wheel', event => {
      event.preventDefault();
      const factor = event.deltaY > 0 ? 1.12 : 0.89;
      camera.position.multiplyScalar(factor);
      camera.position.clampLength(3.2, 14);
    }, { passive: false });

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();
    sceneState = { renderer, scene, camera, root, observer };

    loader.load(
      NIH_GLB_URL,
      gltf => {
        normalizeObject(gltf.scene, THREE);
        root.add(gltf.scene);
        state({ active: true, loading: false, loaded: true, error: null });
        const status = card.querySelector('.dt-reference-3d-status');
        if (status) status.textContent = 'Loaded from NIH 3D · public reference geometry · not user health data';
      },
      undefined,
      error => {
        console.warn('[reference-hand-3d] NIH GLB could not be loaded; keeping UI responsive.', error);
        state({ active: true, loading: false, loaded: false, error: 'NIH reference GLB could not be loaded' });
        fallback(card, 'The NIH reference remains available as provenance; the 3D asset could not be loaded into this viewer.');
      }
    );

    const animate = () => {
      if (!sceneState || sceneState.renderer !== renderer) return;
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };
    animate();
  }

  async function boot() {
    if (bootPromise) return bootPromise;
    bootPromise = (async () => {
      addStyles();
      state({ active: true, loading: true, error: null });
      const card = ensureCard();
      if (!card) {
        state({ active: true, loading: false, error: 'Reference viewer host is not available' });
        return;
      }
      try {
        const [{ default: THREE }, { GLTFLoader }] = await Promise.all([
          import(THREE_URL),
          import(GLTF_URL),
        ]);
        createScene(card, THREE, GLTFLoader);
      } catch (error) {
        console.warn('[reference-hand-3d] viewer dependency failed; keeping UI responsive.', error);
        state({ active: true, loading: false, error: '3D viewer dependencies could not be loaded' });
        fallback(card, 'The 3D viewer dependency could not be loaded.');
      }
    })();
    return bootPromise;
  }

  function activate() {
    state({ active: true, regionId: window.__testhpReferenceHandState?.regionId || 'palm' });
    boot();
  }

  window.testhpReferenceHand3D = Object.freeze({
    version: VIEWER_VERSION,
    sourceId: SOURCE_ID,
    assetUrl: NIH_GLB_URL,
    activate,
    getState: () => window.__testhpReferenceHand3DViewerState,
  });

  state();
  window.addEventListener('testhp:reference-hand-activated', activate);
  if (window.__testhpReferenceHandState?.active) activate();
})();
