import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

/*
 * Hand Surface runtime · Stages 9–10 completion
 *
 * The macro viewport owns interaction. This layer is visual context only:
 * - real hand photographs are projected onto a curved 3D hand surface;
 * - front/back/left/right views are blended by surface normal;
 * - the anatomical scaffold is independent of evidence and never creates it;
 * - deep views can keep this surface rendered in the DOM, but they never receive input.
 */

(() => {
  const viewport = document.getElementById('twin-viewport');
  const baseCanvas = document.getElementById('twin-canvas');
  if (!viewport || !baseCanvas) return;

  const VIEWS = ['front', 'back', 'left', 'right'];
  const SKIN = 0xb87963;
  const BONE = 0xd8c8ad;
  const FALLBACK = new THREE.Color(SKIN);

  const makeFallbackTexture = () => {
    const data = new Uint8Array([184, 121, 99, 255]);
    const texture = new THREE.DataTexture(data, 1, 1, THREE.RGBAFormat);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.needsUpdate = true;
    return texture;
  };

  class HandSurfaceView {
    constructor() {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'hand-surface-canvas';
      Object.assign(this.canvas.style, {
        position: 'absolute', inset: '0', width: '100%', height: '100%',
        zIndex: '12', display: 'none', background: 'transparent', cursor: 'grab',
        touchAction: 'none', pointerEvents: 'auto'
      });
      viewport.appendChild(this.canvas);

      this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.05;

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
      this.camera.position.set(0, 0.15, 10.5);
      this.camera.lookAt(0, 0.35, 0);

      this.scene.add(new THREE.HemisphereLight(0xfff7f0, 0x263331, 2.1));
      const key = new THREE.DirectionalLight(0xffffff, 2.6); key.position.set(4, 6, 8); this.scene.add(key);
      const fill = new THREE.DirectionalLight(0xdcecff, 0.8); fill.position.set(-5, 2, -4); this.scene.add(fill);
      const rim = new THREE.DirectionalLight(0xffd6c4, 0.75); rim.position.set(2, -2, -6); this.scene.add(rim);

      this.root = new THREE.Group();
      this.root.rotation.x = -0.06;
      this.scene.add(this.root);
      this.handGroup = new THREE.Group();
      this.scaffoldGroup = new THREE.Group();
      this.root.add(this.handGroup, this.scaffoldGroup);

      this.fallbackTexture = makeFallbackTexture();
      this.textures = { front: this.fallbackTexture, back: this.fallbackTexture, left: this.fallbackTexture, right: this.fallbackTexture };
      this.assets = {};
      this.loadedViews = [];
      this.photoMode = true;
      this.scaffoldVisible = true;
      this.skinOpacity = 1;
      this.scaffoldOpacity = 0.42;
      this.visible = false;
      this.drag = false;
      this.zoomLevel = 10.5;
      this.materials = [];
      this.photoMaterials = [];
      this.buildHand();
      this.buildScaffold();
      this.buildControls();
      this.bind();
      this.loadEvidence();
      this.resize();
    }

    buildControls() {
      const bar = document.createElement('div');
      bar.id = 'hand-surface-controls';
      Object.assign(bar.style, {
        position: 'absolute', right: '14px', top: '14px', zIndex: '35', display: 'none',
        flexWrap: 'wrap', alignItems: 'center', gap: '5px', padding: '7px',
        borderRadius: '11px', background: 'rgba(10,20,20,.88)', backdropFilter: 'blur(10px)',
        border: '1px solid rgba(155,216,196,.28)'
      });
      const button = (label, title, fn) => {
        const b = document.createElement('button');
        b.type = 'button'; b.textContent = label; b.title = title; b.onclick = fn;
        Object.assign(b.style, { padding: '6px 9px', borderRadius: '8px', border: '1px solid rgba(155,216,196,.28)', background: 'rgba(20,35,34,.9)', color: '#dcece6', font: '800 10px system-ui', cursor: 'pointer' });
        bar.appendChild(b); return b;
      };
      button('PHOTO', 'Use registered hand photographs', () => { this.photoMode = true; this.updateMaterials(); });
      button('MODEL', 'Use anatomical skin material', () => { this.photoMode = false; this.updateMaterials(); });
      button('BONES', 'Toggle anatomical scaffold', () => { this.scaffoldVisible = !this.scaffoldVisible; this.scaffoldGroup.visible = this.scaffoldVisible; });
      button('RESET', 'Reset hand camera and rotation', () => this.reset());

      const label = document.createElement('span'); label.textContent = 'SKIN';
      Object.assign(label.style, { marginLeft: '3px', color: '#9db4ad', font: '800 9px system-ui' }); bar.appendChild(label);
      const skin = document.createElement('input'); skin.type = 'range'; skin.min = '0.15'; skin.max = '1'; skin.step = '0.01'; skin.value = '1'; skin.title = 'Skin opacity';
      skin.oninput = () => { this.skinOpacity = Number(skin.value); this.updateMaterials(); };
      Object.assign(skin.style, { width: '72px', accentColor: '#9bd8c4' }); bar.appendChild(skin);

      const status = document.createElement('span');
      status.id = 'hand-surface-status';
      Object.assign(status.style, { color: '#9db4ad', font: '700 9px system-ui', minWidth: '110px', textAlign: 'right' });
      bar.appendChild(status);
      viewport.appendChild(bar);
      this.controlBar = bar;
      this.statusEl = status;
    }

    buildHand() {
      this.handGroup.clear();
      this.materials = [];
      this.photoMaterials = [];
      const material = () => {
        const m = new THREE.MeshPhysicalMaterial({
          color: FALLBACK, roughness: 0.72, metalness: 0, clearcoat: 0.06,
          clearcoatRoughness: 0.7, transparent: true, depthWrite: true
        });
        this.materials.push(m); return m;
      };
      const add = (geometry, position, scale, rotation = [0, 0, 0]) => {
        const mesh = new THREE.Mesh(geometry, material());
        mesh.position.set(...position); mesh.scale.set(...scale); mesh.rotation.set(...rotation);
        mesh.castShadow = true; mesh.receiveShadow = true; this.handGroup.add(mesh); return mesh;
      };

      // Curved palm + wrist. Overlapping volumes are intentionally smooth and shallow,
      // producing a natural silhouette without pretending to be subject-specific anatomy.
      add(new THREE.SphereGeometry(1, 64, 40), [0, -0.25, 0], [2.28, 2.72, 0.82]);
      add(new THREE.SphereGeometry(0.98, 48, 32), [0, -1.18, -0.04], [2.18, 1.48, 0.78]);
      add(new THREE.CylinderGeometry(0.76, 0.95, 1.9, 48), [0, -2.25, -0.01], [1, 1, 0.9], [0, 0, 0]);

      const fingers = [
        ['index', -1.14, 2.05, 0.45, 1.72, -0.035],
        ['middle', -0.38, 2.30, 0.49, 2.05, -0.008],
        ['ring', 0.42, 2.20, 0.47, 1.94, 0.015],
        ['little', 1.13, 1.96, 0.41, 1.66, 0.065]
      ];
      for (const [, x, y, r, len, tilt] of fingers) {
        add(new THREE.CapsuleGeometry(r, len, 12, 28), [x, y, 0], [1, 1, 0.82], [0, 0, tilt]);
        add(new THREE.SphereGeometry(r * 0.98, 28, 20), [x, y - len * 0.30, 0.015], [1, 1, 0.82]);
        add(new THREE.SphereGeometry(r * 0.91, 28, 20), [x, y + len * 0.22, 0.01], [1, 1, 0.82]);
      }
      add(new THREE.CapsuleGeometry(0.52, 1.65, 12, 28), [-1.68, 0.35, 0.10], [1, 1, 0.9], [0, 0, -0.77]);
      add(new THREE.SphereGeometry(0.59, 32, 24), [-1.23, -0.02, 0.12], [1, 1, 0.82]);

      // Subtle palmar creases are geometry, not evidence.
      const crease = new THREE.MeshBasicMaterial({ color: 0x7d493e, transparent: true, opacity: 0.12, depthWrite: false });
      for (const [x, y, sx] of [[-0.05, 0.95, 1.65], [0.0, 0.55, 1.8], [-0.62, 0.15, 1.05]]) {
        const line = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.012, 6, 48, Math.PI * 0.95), crease);
        line.rotation.set(Math.PI / 2, 0, Math.PI / 2); line.position.set(x, y, 0.68); line.scale.x = sx; this.handGroup.add(line);
      }
      this.updateMaterials();
    }

    buildScaffold() {
      this.scaffoldGroup.clear();
      const boneMaterial = new THREE.MeshStandardMaterial({ color: BONE, roughness: 0.52, metalness: 0, transparent: true, opacity: this.scaffoldOpacity, depthWrite: false });
      const addBone = (a, b, radius = 0.13) => {
        const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b), d = vb.clone().sub(va);
        const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 1.08, d.length(), 12), boneMaterial.clone());
        mesh.material.opacity = this.scaffoldOpacity;
        mesh.position.copy(va.clone().add(vb).multiplyScalar(0.5));
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
        this.scaffoldGroup.add(mesh);
      };
      const joint = (p, r = 0.17) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 12), boneMaterial.clone()); m.material.opacity = this.scaffoldOpacity; m.position.set(...p); this.scaffoldGroup.add(m); };

      addBone([0, -1.75, 0.02], [0, -0.85, 0.03], 0.20);
      addBone([0, -0.85, 0.03], [-0.72, 0.05, 0.03], 0.16); addBone([0, -0.85, 0.03], [0.0, 0.10, 0.03], 0.16); addBone([0, -0.85, 0.03], [0.72, 0.04, 0.03], 0.16);
      for (const x of [-1.14, -0.38, 0.42, 1.13]) {
        const tipY = x === -0.38 ? 3.15 : x === -1.14 ? 2.82 : x === 0.42 ? 3.02 : 2.72;
        addBone([x, 0.05, 0.03], [x, 1.15, 0.03], 0.105); addBone([x, 1.15, 0.03], [x, tipY, 0.03], 0.085);
        joint([x, 0.05, 0.03], 0.13); joint([x, 1.15, 0.03], 0.12);
      }
      addBone([-0.96, 0.02, 0.06], [-1.62, 0.48, 0.06], 0.12); addBone([-1.62, 0.48, 0.06], [-2.20, 1.18, 0.06], 0.09); joint([-1.62, 0.48, 0.06], 0.14);
      this.scaffoldGroup.visible = this.scaffoldVisible;
    }

    bind() {
      this.onDown = e => { this.drag = false; this.pointerStartX = e.clientX; this.pointerStartY = e.clientY; this.lastX = e.clientX; this.lastY = e.clientY; this.canvas.setPointerCapture?.(e.pointerId); this.canvas.style.cursor = 'grabbing'; };
      this.onMove = e => {
        if (Math.hypot(e.clientX - this.pointerStartX, e.clientY - this.pointerStartY) > 4) this.drag = true;
        if (!this.drag) return;
        this.root.rotation.y += (e.clientX - this.lastX) * 0.0075;
        this.root.rotation.x += (e.clientY - this.lastY) * 0.0055;
        this.root.rotation.x = THREE.MathUtils.clamp(this.root.rotation.x, -1.0, 1.0);
        this.lastX = e.clientX; this.lastY = e.clientY;
      };
      this.onUp = e => { this.canvas.releasePointerCapture?.(e.pointerId); this.canvas.style.cursor = 'grab'; };
      this.onWheel = e => { e.preventDefault(); e.stopPropagation(); this.zoom(e.deltaY > 0 ? 1.08 : 0.92); };
      this.onClick = e => {
        if (this.drag) { this.drag = false; return; }
        // The surface is a visual replacement for the macro canvas. Forward one synthetic
        // macro click only; never forward pointerdown/up, so deep layers cannot be triggered twice.
        const wasVisible = this.visible;
        this.canvas.style.display = 'none';
        baseCanvas.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: e.clientX, clientY: e.clientY, view: window }));
        this.canvas.style.display = wasVisible ? 'block' : 'none';
      };
      this.canvas.addEventListener('pointerdown', this.onDown);
      this.canvas.addEventListener('pointermove', this.onMove);
      this.canvas.addEventListener('pointerup', this.onUp);
      this.canvas.addEventListener('pointercancel', this.onUp);
      this.canvas.addEventListener('wheel', this.onWheel, { passive: false });
      this.canvas.addEventListener('click', this.onClick);
      window.addEventListener('resize', () => this.resize());
    }

    async loadEvidence() {
      try {
        const response = await fetch('/api/hand/analysis?subject_id=own_cohort&timepoint=T0', { cache: 'no-store' });
        if (!response.ok) throw new Error(`analysis ${response.status}`);
        const data = await response.json();
        const candidates = (data.assets || []).filter(a => a.modality === 'hand' && ['available', 'ready'].includes(String(a.status || '').toLowerCase()));
        for (const view of VIEWS) {
          const asset = candidates.find(a => String(a.view || '').toLowerCase() === view);
          if (!asset?.asset_id) continue;
          this.assets[view] = asset;
          const image = new Image(); image.crossOrigin = 'anonymous';
          image.onload = () => {
            const texture = new THREE.Texture(image);
            texture.colorSpace = THREE.SRGBColorSpace; texture.anisotropy = this.renderer.capabilities.getMaxAnisotropy(); texture.needsUpdate = true;
            this.textures[view] = texture;
            if (!this.loadedViews.includes(view)) this.loadedViews.push(view);
            this.updateMaterials(); this.updateStatus();
          };
          image.onerror = () => this.updateStatus();
          image.src = `/api/hand/evidence/${encodeURIComponent(asset.asset_id)}`;
        }
        this.updateStatus();
      } catch (error) {
        console.warn('Hand surface evidence unavailable', error);
        this.updateStatus();
      }
    }

    updateStatus() {
      if (!this.statusEl) return;
      this.statusEl.textContent = this.loadedViews.length ? `PHOTO ${this.loadedViews.join(' · ')}` : 'MODEL · no photos';
    }

    updateMaterials() {
      const uniforms = {
        handFront: { value: this.textures.front || this.fallbackTexture },
        handBack: { value: this.textures.back || this.fallbackTexture },
        handLeft: { value: this.textures.left || this.fallbackTexture },
        handRight: { value: this.textures.right || this.fallbackTexture },
        photoEnabled: { value: this.photoMode ? 1 : 0 }
      };
      this.handGroup.traverse(o => {
        if (!o.isMesh || !o.material?.isMeshPhysicalMaterial) return;
        o.material.color.setHex(SKIN); o.material.opacity = this.skinOpacity; o.material.transparent = true;
        o.material.map = null;
        o.material.onBeforeCompile = shader => {
          Object.assign(shader.uniforms, uniforms);
          shader.vertexShader = shader.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 hsWorldPosition; varying vec3 hsWorldNormal;');
          shader.vertexShader = shader.vertexShader.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nhsWorldPosition = worldPosition.xyz;\nhsWorldNormal = normalize(mat3(modelMatrix) * objectNormal);');
          shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\nuniform sampler2D handFront; uniform sampler2D handBack; uniform sampler2D handLeft; uniform sampler2D handRight; uniform float photoEnabled; varying vec3 hsWorldPosition; varying vec3 hsWorldNormal;');
          shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', `
            vec3 n = normalize(hsWorldNormal);
            float wf = max(n.z, 0.0); float wb = max(-n.z, 0.0); float wl = max(-n.x, 0.0); float wr = max(n.x, 0.0);
            float sumW = wf + wb + wl + wr + 0.0001;
            wf /= sumW; wb /= sumW; wl /= sumW; wr /= sumW;
            vec2 uvFront = vec2(hsWorldPosition.x / 4.65 + 0.5, 1.0 - (hsWorldPosition.y / 6.15 + 0.5));
            vec2 uvBack  = vec2(1.0 - (hsWorldPosition.x / 4.65 + 0.5), 1.0 - (hsWorldPosition.y / 6.15 + 0.5));
            vec2 uvLeft  = vec2(hsWorldPosition.z / 1.75 + 0.5, 1.0 - (hsWorldPosition.y / 6.15 + 0.5));
            vec2 uvRight = vec2(1.0 - (hsWorldPosition.z / 1.75 + 0.5), 1.0 - (hsWorldPosition.y / 6.15 + 0.5));
            vec3 projected = texture2D(handFront, clamp(uvFront, 0.001, 0.999)).rgb * wf;
            projected += texture2D(handBack, clamp(uvBack, 0.001, 0.999)).rgb * wb;
            projected += texture2D(handLeft, clamp(uvLeft, 0.001, 0.999)).rgb * wl;
            projected += texture2D(handRight, clamp(uvRight, 0.001, 0.999)).rgb * wr;
            diffuseColor.rgb = mix(diffuseColor.rgb, projected, photoEnabled * 0.96);
          `);
        };
        o.material.needsUpdate = true;
      });
    }

    show(visible, deepActive = false) {
      this.visible = Boolean(visible);
      const ownsInput = this.visible && !deepActive;
      this.canvas.style.display = this.visible ? 'block' : 'none';
      this.canvas.style.pointerEvents = ownsInput ? 'auto' : 'none';
      this.controlBar.style.display = ownsInput ? 'flex' : 'none';
      this.updateStatus(); this.resize();
    }

    resize() {
      const r = viewport.getBoundingClientRect();
      const w = Math.max(1, r.width), h = Math.max(1, r.height);
      this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h, false);
    }
    rotate(delta) { this.root.rotation.y += delta; }
    zoom(factor) { this.zoomLevel = THREE.MathUtils.clamp(this.zoomLevel * factor, 6.2, 16); this.camera.position.setLength(this.zoomLevel); }
    reset() { this.root.rotation.set(-0.06, 0, 0); this.camera.position.set(0, 0.15, 10.5); this.camera.lookAt(0, 0.35, 0); this.zoomLevel = 10.5; }
    render() { if (this.visible) this.renderer.render(this.scene, this.camera); }
  }

  const view = new HandSurfaceView();
  window.handSurfaceView = view;

  const manager = window.spatialViewportManager;
  if (!manager) return;
  const oldRender = manager.render.bind(manager);
  manager.render = () => {
    oldRender();
    const deepActive = Boolean(document.querySelector('.deep-drill-visualization, [data-deep-active="true"]'));
    view.show(Boolean(manager.rootMacro?.()), deepActive);
  };
  const oldResize = manager.resize.bind(manager);
  manager.resize = () => { oldResize(); view.resize(); };
  manager.render();
  const loop = () => { requestAnimationFrame(loop); view.render(); };
  loop();
})();
