import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  const viewport = document.getElementById('twin-viewport');
  const baseCanvas = document.getElementById('twin-canvas');
  if (!viewport || !baseCanvas) return;

  const COLORS = { skin: 0xb87963, skinDark: 0x8f5546 };

  class HandSurfaceView {
    constructor() {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'hand-surface-canvas';
      Object.assign(this.canvas.style, { position: 'absolute', inset: '0', width: '100%', height: '100%', zIndex: '12', display: 'none', background: 'transparent', cursor: 'grab' });
      viewport.appendChild(this.canvas);
      this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
      this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100);
      this.camera.position.set(0, 0.25, 9.2);
      this.camera.lookAt(0, 0.35, 0);
      this.scene.add(new THREE.HemisphereLight(0xfff5ed, 0x24312f, 2.2));
      const key = new THREE.DirectionalLight(0xffffff, 2.5); key.position.set(4, 6, 8); this.scene.add(key);
      const fill = new THREE.DirectionalLight(0xd9ecff, 0.9); fill.position.set(-5, 2, -4); this.scene.add(fill);
      this.root = new THREE.Group();
      this.root.rotation.x = -0.08;
      this.scene.add(this.root);
      this.drag = false;
      this.zoomLevel = 9.2;
      this.photoMode = true;
      this.texture = null;
      this.handShell = null;
      this.asset = null;
      this.visible = false;
      this.bind();
      this.addControls();
      this.buildHand();
      this.loadEvidence();
      this.resize();
    }

    addControls() {
      const bar = document.createElement('div');
      bar.id = 'hand-surface-controls';
      Object.assign(bar.style, { position: 'absolute', right: '18px', top: '18px', zIndex: '35', display: 'none', gap: '6px' });
      const make = (text, title, fn) => {
        const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.title = title;
        Object.assign(b.style, { padding: '7px 10px', borderRadius: '9px', border: '1px solid rgba(155,216,196,.35)', background: 'rgba(13,25,24,.9)', color: '#dcece6', font: '800 11px system-ui', cursor: 'pointer' });
        b.onclick = fn; bar.appendChild(b); return b;
      };
      make('PHOTO', 'Show the registered macro photograph projected onto the 3D hand', () => { this.photoMode = true; this.updateMaterial(); });
      make('MODEL', 'Show the anatomical surface without photo', () => { this.photoMode = false; this.updateMaterial(); });
      make('RESET', 'Reset hand view', () => this.reset());
      viewport.appendChild(bar); this.controlBar = bar;
    }

    bind() {
      this.onDown = e => { this.drag = true; this.lastX = e.clientX; this.lastY = e.clientY; this.canvas.style.cursor = 'grabbing'; };
      this.onMove = e => { if (!this.drag) return; this.root.rotation.y += (e.clientX - this.lastX) * 0.008; this.root.rotation.x += (e.clientY - this.lastY) * 0.006; this.root.rotation.x = Math.max(-1.15, Math.min(1.15, this.root.rotation.x)); this.lastX = e.clientX; this.lastY = e.clientY; };
      this.onUp = () => { this.drag = false; this.canvas.style.cursor = 'grab'; };
      this.onWheel = e => { e.preventDefault(); this.zoom(e.deltaY > 0 ? 1.08 : 0.92); };
      this.onClick = e => {
        if (this.drag) return;
        const wasVisible = this.visible;
        this.canvas.style.display = 'none';
        const target = document.elementFromPoint(e.clientX, e.clientY);
        if (target === this.canvas || target === viewport) baseCanvas.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: e.clientX, clientY: e.clientY, view: window }));
        else target?.dispatchEvent?.(new MouseEvent('click', { bubbles: true, clientX: e.clientX, clientY: e.clientY, view: window }));
        this.canvas.style.display = wasVisible ? 'block' : 'none';
      };
      this.canvas.addEventListener('pointerdown', this.onDown); this.canvas.addEventListener('pointermove', this.onMove); this.canvas.addEventListener('pointerup', this.onUp); this.canvas.addEventListener('pointercancel', this.onUp); this.canvas.addEventListener('pointerleave', this.onUp); this.canvas.addEventListener('wheel', this.onWheel, { passive: false }); this.canvas.addEventListener('click', this.onClick);
    }

    async loadEvidence() {
      try {
        const response = await fetch('/api/hand/analysis?subject_id=own_cohort&timepoint=T0');
        const data = await response.json();
        const asset = (data.assets || []).find(a => a.modality === 'hand' && ['front', 'back'].includes(String(a.view || '').toLowerCase()) && ['ready', 'available'].includes(String(a.status || '').toLowerCase()));
        if (!asset?.asset_id) return;
        this.asset = asset;
        const image = new Image(); image.crossOrigin = 'anonymous';
        image.onload = () => { this.texture = new THREE.Texture(image); this.texture.colorSpace = THREE.SRGBColorSpace; this.texture.needsUpdate = true; this.updateMaterial(); };
        image.src = `/api/hand/evidence/${encodeURIComponent(asset.asset_id)}`;
      } catch (error) { console.warn('Hand surface evidence unavailable', error); }
    }

    buildHand() {
      this.root.clear();
      const skin = new THREE.MeshStandardMaterial({ color: COLORS.skin, roughness: 0.78, metalness: 0 });
      const group = new THREE.Group();
      const palm = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32), skin.clone()); palm.scale.set(2.15, 2.65, 0.72); palm.position.set(0, -0.2, 0); group.add(palm);
      const wrist = new THREE.Mesh(new THREE.CylinderGeometry(0.78, 0.95, 1.75, 32), skin.clone()); wrist.rotation.z = Math.PI / 2; wrist.scale.z = 0.82; wrist.position.set(0, -2.05, 0); group.add(wrist);
      const fingers = [['index', -1.12, 2.05, 0.47, 2.0, -0.05], ['middle', -0.38, 2.35, 0.50, 2.45, -0.02], ['ring', 0.42, 2.22, 0.49, 2.25, 0.01], ['little', 1.12, 1.98, 0.43, 1.85, 0.08]];
      for (const [, x, y, r, len, tilt] of fingers) {
        const f = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 10, 24), skin.clone()); f.position.set(x, y, 0); f.rotation.z = tilt; group.add(f);
        const joint = new THREE.Mesh(new THREE.SphereGeometry(r * 1.02, 24, 16), skin.clone()); joint.scale.z = 0.82; joint.position.set(x, y - len * 0.28, 0.02); group.add(joint);
      }
      const thumb = new THREE.Mesh(new THREE.CapsuleGeometry(0.55, 1.65, 10, 24), skin.clone()); thumb.position.set(-1.65, 0.45, 0.12); thumb.rotation.z = -0.78; thumb.scale.z = 0.92; group.add(thumb);
      const thumbJoint = new THREE.Mesh(new THREE.SphereGeometry(0.58, 24, 16), skin.clone()); thumbJoint.position.set(-1.2, 0.1, 0.16); thumbJoint.scale.z = 0.8; group.add(thumbJoint);
      const creaseMaterial = new THREE.MeshBasicMaterial({ color: COLORS.skinDark, transparent: true, opacity: 0.18 });
      for (const y of [1.15, 1.55, 2.15]) { const line = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.012, 6, 32, Math.PI), creaseMaterial); line.rotation.x = Math.PI / 2; line.rotation.z = Math.PI / 2; line.position.set(0, y, 0.55); line.scale.x = 1.8; group.add(line); }
      this.root.add(group); this.handShell = group; this.updateMaterial();
    }

    updateMaterial() {
      if (!this.handShell) return;
      this.handShell.traverse(o => {
        if (!o.isMesh || !o.material?.isMeshStandardMaterial) return;
        o.material.color.setHex(COLORS.skin); o.material.map = null; o.material.needsUpdate = true;
      });
      if (this.photoMode && this.texture) this.applyProjectionMaterial();
    }

    applyProjectionMaterial() {
      this.handShell.traverse(o => {
        if (!o.isMesh || !o.material?.isMeshStandardMaterial) return;
        const base = o.material;
        base.onBeforeCompile = shader => {
          shader.uniforms.handPhoto = { value: this.texture };
          shader.vertexShader = shader.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 handWorldPosition; varying vec3 handWorldNormal;');
          shader.vertexShader = shader.vertexShader.replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nhandWorldPosition = (modelMatrix * vec4(transformed, 1.0)).xyz;\nhandWorldNormal = normalize(mat3(modelMatrix) * objectNormal);');
          shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\nuniform sampler2D handPhoto; varying vec3 handWorldPosition; varying vec3 handWorldNormal;');
          shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', 'float frontness = smoothstep(0.18, 0.72, abs(handWorldNormal.z)); vec2 photoUv = vec2(handWorldPosition.x / 4.4 + 0.5, handWorldPosition.y / 5.7 + 0.5); photoUv.y = 1.0 - photoUv.y; vec4 handPhotoColor = texture2D(handPhoto, clamp(photoUv, 0.001, 0.999)); diffuseColor.rgb = mix(diffuseColor.rgb, handPhotoColor.rgb, frontness * 0.92);');
        };
        base.needsUpdate = true;
      });
    }

    show(visible) { this.visible = visible; this.canvas.style.display = visible ? 'block' : 'none'; this.controlBar.style.display = visible ? 'flex' : 'none'; this.resize(); }
    resize() { const r = viewport.getBoundingClientRect(); const w = Math.max(1, r.width); const h = Math.max(1, r.height); this.camera.aspect = w / h; this.camera.updateProjectionMatrix(); this.renderer.setSize(w, h, false); }
    rotate(d) { this.root.rotation.y += d; }
    zoom(f) { this.zoomLevel = Math.max(5.5, Math.min(15, this.zoomLevel * f)); this.camera.position.setLength(this.zoomLevel); }
    reset() { this.root.rotation.set(0, 0, 0); this.camera.position.set(0, 0.25, 9.2); this.camera.lookAt(0, 0.35, 0); this.zoomLevel = 9.2; }
    render() { if (this.visible) this.renderer.render(this.scene, this.camera); }
  }

  const view = new HandSurfaceView();
  window.handSurfaceView = view;
  const manager = window.spatialViewportManager;
  if (!manager) return;
  const oldRender = manager.render.bind(manager);
  manager.render = () => { oldRender(); view.show(manager.rootMacro()); };
  const oldResize = manager.resize.bind(manager);
  manager.resize = () => { oldResize(); view.resize(); };
  manager.render();
  const loop = () => { requestAnimationFrame(loop); view.render(); };
  loop();
})();
