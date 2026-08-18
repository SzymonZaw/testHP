import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  const viewport = document.getElementById('twin-viewport');
  const baseCanvas = document.getElementById('twin-canvas');
  const controls = document.querySelector('.viewer-controls');
  const hint = document.querySelector('.viewer-hint');
  const loading = document.getElementById('viewer-loading');
  const badge = document.getElementById('spatial-level-badge');
  const nodeEl = document.getElementById('spatial-node');
  const childrenEl = document.getElementById('spatial-children');
  const breadcrumbEl = document.getElementById('spatial-breadcrumb');
  if (!viewport || !baseCanvas || !badge || !nodeEl || !childrenEl) return;

  const COLORS = {
    background: 0x0b1518,
    panel: 0x132923,
    macro: 0xc68b72,
    tissue: 0x5d9d89,
    cellular: 0x5fae98,
    cell: 0x8bc7b0,
    accent: 0x9bd8c4,
    grid: 0x4f9b86,
    nucleus: 0x315e51,
    membrane: 0x7bc0aa,
    tissueDark: 0x244b40,
    tissueLight: 0x7bb9a5
  };

  class BaseRenderer {
    constructor(manager) { this.manager = manager; }
    mount() {}
    destroy() {}
    resize() {}
    rotate() {}
    zoom() {}
    reset() {}
  }

  class Hand3DRenderer extends BaseRenderer {
    mount() {
      this.manager.base(true);
      this.manager.deep(false);
    }
    reset() { document.getElementById('reset-view')?.click(); }
    rotate(d) { document.getElementById(d < 0 ? 'rotate-left' : 'rotate-right')?.click(); }
    zoom(f) { document.getElementById(f < 1 ? 'zoom-in' : 'zoom-out')?.click(); }
  }

  class SpatialSceneRenderer extends BaseRenderer {
    constructor(manager, title) {
      super(manager);
      this.title = title;
      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
      this.camera.position.set(0, 0, 8);
      this.root = new THREE.Group();
      this.scene.add(this.root);
      this.scene.add(new THREE.HemisphereLight(0xffffff, 0x10201d, 2.1));
      const light = new THREE.DirectionalLight(0xffffff, 2.4);
      light.position.set(4, 5, 7);
      this.scene.add(light);
      this.pointer = new THREE.Vector2();
      this.raycaster = new THREE.Raycaster();
      this.clickable = [];
      this.dragging = false;
      this.zoomLevel = 8;
    }

    mount() {
      this.canvas = this.manager.deepCanvas;
      this.renderer = this.manager.deepRenderer;
      this.manager.base(false);
      this.manager.deep(true, this.title);
      this.bindPointer();
      this.renderContent();
      this.resize();
    }

    bindPointer() {
      this.onDown = e => {
        this.dragging = true;
        this.lastX = e.clientX;
        this.lastY = e.clientY;
        this.canvas.style.cursor = 'grabbing';
      };
      this.onMove = e => {
        if (!this.dragging) return;
        this.root.rotation.y += (e.clientX - this.lastX) * 0.008;
        this.root.rotation.x += (e.clientY - this.lastY) * 0.006;
        this.lastX = e.clientX;
        this.lastY = e.clientY;
      };
      this.onUp = () => {
        this.dragging = false;
        this.canvas.style.cursor = 'grab';
      };
      this.onWheel = e => {
        e.preventDefault();
        this.zoom(e.deltaY > 0 ? 1.12 : 0.89);
      };
      this.onClick = e => {
        const r = this.canvas.getBoundingClientRect();
        this.pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1;
        this.pointer.y = -((e.clientY - r.top) / r.height) * 2 + 1;
        this.raycaster.setFromCamera(this.pointer, this.camera);
        const hit = this.raycaster.intersectObjects(this.clickable, false)[0];
        if (hit?.object?.userData?.target) hit.object.userData.target.click();
      };
      this.canvas.addEventListener('pointerdown', this.onDown);
      this.canvas.addEventListener('pointermove', this.onMove);
      this.canvas.addEventListener('pointerup', this.onUp);
      this.canvas.addEventListener('pointercancel', this.onUp);
      this.canvas.addEventListener('pointerleave', this.onUp);
      this.canvas.addEventListener('wheel', this.onWheel, { passive: false });
      this.canvas.addEventListener('click', this.onClick);
    }

    targets() {
      return [...childrenEl.querySelectorAll('.spatial-target')].filter(e => e.querySelector('strong'));
    }

    name(e) {
      return e.querySelector('strong')?.textContent?.trim() || 'Spatial target';
    }

    makeMesh(geometry, position, color, target = null, materialOptions = {}) {
      const material = new THREE.MeshStandardMaterial({
        color,
        roughness: 0.65,
        metalness: 0.03,
        emissive: 0x071c17,
        emissiveIntensity: 0.2,
        ...materialOptions
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(...position);
      if (target) {
        mesh.userData.target = target;
        this.clickable.push(mesh);
      }
      this.root.add(mesh);
      return mesh;
    }

    label(text, x, y, target) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = text;
      Object.assign(button.style, {
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        transform: 'translate(-50%,-50%)',
        pointerEvents: 'auto',
        padding: '9px 12px',
        borderRadius: '10px',
        border: '1px solid #78bca866',
        background: '#12221fe8',
        color: '#dcece6',
        font: '700 12px system-ui,sans-serif',
        cursor: 'pointer',
        backdropFilter: 'blur(6px)'
      });
      button.onclick = () => target?.click();
      this.manager.deepLabels.appendChild(button);
    }

    heading(text) {
      const element = document.createElement('div');
      element.textContent = text;
      Object.assign(element.style, {
        position: 'absolute',
        left: '50%',
        top: '12%',
        transform: 'translateX(-50%)',
        font: '800 11px system-ui,sans-serif',
        letterSpacing: '.16em',
        color: '#9bd8c4',
        whiteSpace: 'nowrap'
      });
      this.manager.deepLabels.appendChild(element);
    }

    empty(text) {
      const element = document.createElement('div');
      element.textContent = text;
      Object.assign(element.style, {
        position: 'absolute',
        left: '50%',
        bottom: '17%',
        transform: 'translateX(-50%)',
        color: '#9fb7b0',
        font: '600 12px system-ui,sans-serif',
        textAlign: 'center',
        whiteSpace: 'nowrap'
      });
      this.manager.deepLabels.appendChild(element);
    }

    resize() {
      const r = viewport.getBoundingClientRect();
      const w = Math.max(1, r.width);
      const h = Math.max(1, r.height);
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h, false);
    }

    rotate(d) { this.root.rotation.y += d; }

    zoom(f) {
      this.zoomLevel = Math.max(3.5, Math.min(18, this.zoomLevel * f));
      this.camera.position.setLength(this.zoomLevel);
    }

    reset() {
      this.root.rotation.set(0, 0, 0);
      this.zoomLevel = 8;
      this.camera.position.set(0, 0, 8);
    }

    destroy() {
      if (this.canvas) {
        this.canvas.removeEventListener('pointerdown', this.onDown);
        this.canvas.removeEventListener('pointermove', this.onMove);
        this.canvas.removeEventListener('pointerup', this.onUp);
        this.canvas.removeEventListener('pointercancel', this.onUp);
        this.canvas.removeEventListener('pointerleave', this.onUp);
        this.canvas.removeEventListener('wheel', this.onWheel);
        this.canvas.removeEventListener('click', this.onClick);
      }
      this.root.traverse(object => {
        object.geometry?.dispose?.();
        if (object.material) {
          if (Array.isArray(object.material)) object.material.forEach(m => m.dispose?.());
          else object.material.dispose?.();
        }
      });
      this.root.clear();
      this.clickable = [];
    }
  }

  class MacroRegionRenderer extends SpatialSceneRenderer {
    renderContent() {
      const name = this.title.toLowerCase();
      const finger = ['thumb', 'index finger', 'middle finger', 'ring finger', 'little finger'].includes(name);
      const wrist = name === 'wrist';

      if (finger) {
        const mesh = this.makeMesh(new THREE.CapsuleGeometry(0.78, 3.9, 10, 24), [0, 0, 0], COLORS.macro);
        mesh.rotation.z = name === 'thumb' ? 0.55 : name === 'little finger' ? 0.08 : 0;
      } else if (wrist) {
        const mesh = this.makeMesh(new THREE.CylinderGeometry(1.45, 1.7, 2.7, 32), [0, 0, 0], COLORS.macro);
        mesh.rotation.z = Math.PI / 2;
      } else {
        this.makeMesh(new THREE.BoxGeometry(5.2, 2.6, 0.55), [0, 0, 0], COLORS.macro);
      }

      this.heading(this.title.toUpperCase());
      const targets = this.targets().slice(0, 3);
      targets.forEach((target, i) => {
        const x = -1.8 + i * 1.8;
        const y = -1.3 + (i % 2) * 0.3;
        this.makeMesh(new THREE.SphereGeometry(0.14, 16, 12), [x, y, 0.4], COLORS.accent, target);
        this.label(this.name(target), 25 + i * 25, 57 - (i % 2) * 15, target);
      });
    }
  }

  class TissuePlaneRenderer extends SpatialSceneRenderer {
    renderContent() {
      this.heading('TISSUE PLANE');
      this.makeMesh(new THREE.BoxGeometry(7.2, 4.3, 0.12), [0, 0, -0.65], COLORS.panel);

      const border = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.BoxGeometry(6.9, 4.0, 0.16)),
        new THREE.LineBasicMaterial({ color: COLORS.tissueLight, transparent: true, opacity: 0.55 })
      );
      border.position.z = -0.45;
      this.root.add(border);

      const targets = this.targets().slice(0, 3);
      const positions = [[-2.2, 0.65, 0.2], [0, -0.15, 0.3], [2.2, 0.65, 0.2]];
      targets.forEach((target, i) => {
        const region = this.makeMesh(new THREE.BoxGeometry(1.9, 1.4, 0.28), positions[i], COLORS.tissue, target);
        region.rotation.z = (i - 1) * 0.05;
        const inner = this.makeMesh(new THREE.BoxGeometry(1.45, 0.95, 0.34), [positions[i][0], positions[i][1], 0.38], COLORS.tissueDark);
        inner.rotation.z = region.rotation.z;
        this.label(this.name(target), 23 + i * 27, 57 - (i % 2) * 17, target);
      });

      if (!targets.length) this.empty('No deeper tissue targets are defined.');
    }
  }

  class CellularFieldRenderer extends SpatialSceneRenderer {
    renderContent() {
      this.heading('CELLULAR FIELD');
      this.makeMesh(new THREE.BoxGeometry(7.2, 4.3, 0.14), [0, 0, -0.55], 0x101f20);

      const gridMaterial = new THREE.LineBasicMaterial({ color: COLORS.grid, transparent: true, opacity: 0.35 });
      for (let x = -3; x <= 3; x++) {
        const geometry = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(x, -2, -0.35),
          new THREE.Vector3(x, 2, -0.35)
        ]);
        this.root.add(new THREE.Line(geometry, gridMaterial));
      }
      for (let y = -2; y <= 2; y++) {
        const geometry = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(-3, y, -0.35),
          new THREE.Vector3(3, y, -0.35)
        ]);
        this.root.add(new THREE.Line(geometry, gridMaterial));
      }

      const targets = this.targets().slice(0, 3);
      const positions = [[-2, 0.75, 0.2], [0, -0.55, 0.3], [2, 0.8, 0.2]];
      targets.forEach((target, i) => {
        const cell = this.makeMesh(new THREE.SphereGeometry(0.62, 32, 20), positions[i], COLORS.cellular, target);
        cell.scale.set(1, 0.72, 0.35);
        const nucleus = this.makeMesh(new THREE.SphereGeometry(0.23, 20, 16), [positions[i][0], positions[i][1], 0.48], COLORS.nucleus);
        nucleus.scale.z = 0.35;
        this.label(this.name(target), 25 + i * 25, 54 - (i % 2) * 17, target);
      });

      if (!targets.length) this.empty('No deeper cellular targets are defined.');
    }
  }

  class SingleCellRenderer extends SpatialSceneRenderer {
    renderContent() {
      this.heading('SINGLE CELL');
      const membrane = this.makeMesh(
        new THREE.SphereGeometry(1.5, 48, 32),
        [0, 0, 0],
        COLORS.cell,
        null,
        { transparent: true, opacity: 0.42, side: THREE.DoubleSide }
      );
      membrane.material.emissive.setHex(0x0b3026);
      membrane.material.emissiveIntensity = 0.35;

      const cytoplasm = this.makeMesh(
        new THREE.SphereGeometry(1.28, 48, 32),
        [0, 0, 0],
        COLORS.tissueLight,
        null,
        { transparent: true, opacity: 0.24, side: THREE.DoubleSide }
      );

      const nucleus = this.makeMesh(new THREE.SphereGeometry(0.56, 40, 24), [-0.2, 0.1, 1.0], COLORS.nucleus);
      nucleus.material.emissive.setHex(0x183b31);
      nucleus.material.emissiveIntensity = 0.45;

      for (const [x, y, z, scale] of [[0.55, 0.4, 0.85, 0.16], [-0.65, -0.25, 0.82, 0.13], [0.55, -0.65, 0.72, 0.11]]) {
        const organelle = this.makeMesh(new THREE.SphereGeometry(scale, 18, 12), [x, y, z], COLORS.accent);
        organelle.material.emissive.setHex(0x1b4b3e);
        organelle.material.emissiveIntensity = 0.3;
      }

      this.label(this.title, 50, 82, null);
      this.empty('Navigation target only · no cellular evidence is implied.');
    }
  }

  class SpatialViewportManager {
    constructor() {
      this.active = null;
      this.activeKey = '';
      this.deepCanvas = document.createElement('canvas');
      this.deepCanvas.id = 'spatial-active-canvas';
      Object.assign(this.deepCanvas.style, {
        position: 'absolute', inset: '0', width: '100%', height: '100%',
        zIndex: '20', display: 'none', cursor: 'grab', background: '#0b1518'
      });
      viewport.appendChild(this.deepCanvas);

      this.deepLabels = document.createElement('div');
      Object.assign(this.deepLabels.style, {
        position: 'absolute', inset: '0', zIndex: '21', display: 'none', pointerEvents: 'none'
      });
      viewport.appendChild(this.deepLabels);

      this.deepTitle = document.createElement('div');
      Object.assign(this.deepTitle.style, {
        position: 'absolute', left: '18px', bottom: '18px', zIndex: '40', display: 'none',
        padding: '8px 11px', borderRadius: '10px', background: 'rgba(13,25,24,.92)',
        border: '1px solid rgba(155,216,196,.35)', color: '#dcece6',
        font: '800 11px system-ui,sans-serif', letterSpacing: '.1em'
      });
      viewport.appendChild(this.deepTitle);

      this.upButton = document.createElement('button');
      this.upButton.id = 'spatial-up';
      this.upButton.type = 'button';
      this.upButton.textContent = '↑ Higher layer';
      Object.assign(this.upButton.style, {
        position: 'absolute', left: '18px', top: '18px', zIndex: '45', display: 'none',
        padding: '9px 13px', borderRadius: '10px', border: '1px solid rgba(155,216,196,.45)',
        background: 'rgba(13,25,24,.94)', color: '#dcece6', font: '800 11px system-ui,sans-serif',
        letterSpacing: '.04em', cursor: 'pointer', boxShadow: '0 8px 24px rgba(0,0,0,.25)'
      });
      this.upButton.title = 'Go to the parent spatial layer';
      this.upButton.addEventListener('click', () => this.navigateUp());
      viewport.appendChild(this.upButton);

      this.deepRenderer = new THREE.WebGLRenderer({ canvas: this.deepCanvas, antialias: true, alpha: false });
      this.deepRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.deepRenderer.outputColorSpace = THREE.SRGBColorSpace;
      this.deepRenderer.setClearColor(COLORS.background, 1);

      this.originalControlHandlers = new Map();
      ['reset-view', 'rotate-left', 'rotate-right', 'zoom-in', 'zoom-out', 'zoom-region'].forEach(id => {
        const button = document.getElementById(id);
        if (button) this.originalControlHandlers.set(id, button.onclick);
      });

      const observer = new MutationObserver(() => this.render());
      [badge, nodeEl, childrenEl, breadcrumbEl].filter(Boolean).forEach(element => {
        observer.observe(element, { childList: true, subtree: true, characterData: true, attributes: true });
      });

      window.addEventListener('resize', () => this.resize());
      window.addEventListener('keydown', event => {
        if ((event.key === 'Escape' || event.key === 'Backspace') && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName) && !this.rootMacro()) {
          this.navigateUp();
        }
      });
    }

    path() {
      return [...(breadcrumbEl?.querySelectorAll('button') || [])].map(button => button.textContent.trim()).filter(Boolean);
    }

    title() {
      return nodeEl.querySelector('strong')?.textContent?.trim() || 'Spatial target';
    }

    level() {
      const text = String(badge.textContent || '').toUpperCase();
      if (text.includes('SINGLE')) return 'cell';
      if (text.includes('CELLULAR')) return 'cellular';
      if (text.includes('TISSUE')) return 'tissue';
      return 'macro';
    }

    rootMacro() {
      return this.level() === 'macro' && this.path().length <= 1 && this.title() === 'Hand';
    }

    key() {
      return `${this.level()}|${this.path().join('>')}|${this.title()}|${[...childrenEl.querySelectorAll('.spatial-target strong')].map(x => x.textContent.trim()).join('|')}`;
    }

    parentButton() {
      const buttons = [...(breadcrumbEl?.querySelectorAll('button') || [])];
      return buttons.slice(-2, -1)[0] || null;
    }

    navigateUp() {
      if (this.rootMacro()) return false;
      const parent = this.parentButton();
      if (parent) {
        parent.click();
        return true;
      }
      return false;
    }

    base(visible) {
      baseCanvas.style.display = visible ? 'block' : 'none';
      baseCanvas.style.visibility = visible ? 'visible' : 'hidden';
    }

    deep(visible, title = '') {
      this.deepCanvas.style.display = visible ? 'block' : 'none';
      this.deepLabels.style.display = visible ? 'block' : 'none';
      this.deepTitle.style.display = visible ? 'block' : 'none';
      this.upButton.style.display = visible && !this.rootMacro() ? 'block' : 'none';
      this.deepTitle.textContent = visible ? `${this.level().toUpperCase()} · ${title.toUpperCase()}` : '';
      if (hint) hint.style.visibility = visible ? 'hidden' : 'visible';
      if (loading) loading.style.visibility = 'hidden';
    }

    controls(deep) {
      const handlers = {
        'reset-view': () => this.active?.reset(),
        'rotate-left': () => this.active?.rotate(-Math.PI / 9),
        'rotate-right': () => this.active?.rotate(Math.PI / 9),
        'zoom-in': () => this.active?.zoom(0.86),
        'zoom-out': () => this.active?.zoom(1.16),
        'zoom-region': () => this.active?.zoom(0.84)
      };
      Object.entries(handlers).forEach(([id, handler]) => {
        const button = document.getElementById(id);
        if (button) button.onclick = deep ? handler : (this.originalControlHandlers.get(id) || null);
      });
      if (controls) controls.style.visibility = 'visible';
    }

    createDeepRenderer(level, title) {
      if (level === 'macro') return new MacroRegionRenderer(this, title);
      if (level === 'tissue') return new TissuePlaneRenderer(this, title);
      if (level === 'cellular') return new CellularFieldRenderer(this, title);
      return new SingleCellRenderer(this, title);
    }

    render() {
      const key = this.key();
      if (key === this.activeKey) {
        this.resize();
        this.upButton.style.display = !this.rootMacro() && this.deepCanvas.style.display !== 'none' ? 'block' : 'none';
        return;
      }

      this.activeKey = key;
      const root = this.rootMacro();
      if (this.active) {
        this.active.destroy();
        this.active = null;
      }
      this.deepLabels.replaceChildren();
      this.base(false);
      this.deep(false);

      if (root) {
        this.active = new Hand3DRenderer(this);
        this.active.mount();
        this.controls(false);
        return;
      }

      this.active = this.createDeepRenderer(this.level(), this.title());
      this.active.mount();
      this.controls(true);
      this.resize();
    }

    resize() { this.active?.resize(); }

    animate() {
      requestAnimationFrame(() => this.animate());
      if (this.active instanceof SpatialSceneRenderer) {
        this.deepRenderer.render(this.active.scene, this.active.camera);
      }
    }
  }

  const manager = new SpatialViewportManager();
  window.spatialViewportManager = manager;
  manager.render();
  manager.animate();
})();
