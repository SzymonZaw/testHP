import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  const viewport = document.getElementById('twin-viewport');
  const canvas = document.getElementById('twin-canvas');
  if (!viewport || !canvas) return;

  const text = id => document.getElementById(id)?.textContent?.trim() || '';
  const level = () => {
    const value = text('spatial-level-badge').toLowerCase();
    if (value.includes('pojedyncz') || value.includes('single')) return 'cell';
    if (value.includes('komórkow') || value.includes('cellular')) return 'cellular';
    if (value.includes('tkank') || value.includes('tissue')) return 'tissue';
    return 'macro';
  };
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const path = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const childButtons = () => [...document.querySelectorAll('#spatial-children .spatial-target')];
  const children = () => childButtons().map(x => x.querySelector('strong')?.textContent?.trim()).filter(Boolean);

  let deepGroup = null;
  let attachedScene = null;
  let lastVisualState = '';
  let managerHooked = false;
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  function managerReady() {
    const manager = window.spatialViewportManager;
    return manager?.version === 'canonical-three-1' && manager.active?.scene && manager.active?.camera;
  }

  function clearGroup() {
    if (!deepGroup) return;
    [...deepGroup.children].forEach(object => {
      object.traverse(child => {
        if (!child.isMesh) return;
        child.geometry?.dispose?.();
        if (Array.isArray(child.material)) child.material.forEach(material => material.dispose?.());
        else child.material?.dispose?.();
      });
    });
    deepGroup.clear();
  }

  function ensureGroup(manager) {
    const scene = manager.active.scene;
    if (!deepGroup) {
      deepGroup = new THREE.Group();
      deepGroup.name = 'digital-twin-navigation-layer';
    }
    if (attachedScene !== scene) {
      if (deepGroup.parent) deepGroup.parent.remove(deepGroup);
      scene.add(deepGroup);
      attachedScene = scene;
    }
    return deepGroup;
  }

  function materialFor(kind, index, selected = false) {
    const colors = {
      tissue: [0x8bd3c7, 0x72b8df, 0xd6a64f],
      cellular: [0x7fc8ff, 0xb78cff, 0x7fe0b0],
      cell: [0x66b3ff, 0xd6a64f, 0xc58cff]
    };
    const color = colors[kind][index % 3];
    return new THREE.MeshStandardMaterial({
      color: selected ? 0x66b3ff : color,
      roughness: 0.55,
      metalness: 0.05,
      transparent: true,
      opacity: kind === 'cell' ? 0.9 : 0.72,
      emissive: selected ? 0x0b2745 : color,
      emissiveIntensity: selected ? 0.35 : 0.12
    });
  }

  function cameraFor(kind) {
    const manager = window.spatialViewportManager;
    if (!managerReady() || !manager.active.camera || !manager.active.controls) return;
    const camera = manager.active.camera;
    const controls = manager.active.controls;
    const next = kind === 'cell' ? 5.8 : kind === 'cellular' ? 7.2 : 8.0;
    camera.position.set(0, kind === 'cell' ? 0.55 : 0.8, next);
    controls.target.set(0, 0.2, 0);
    controls.update();
  }

  function addLeaf(kind, currentTarget) {
    if (kind !== 'cell') return;
    const geometry = new THREE.SphereGeometry(1.05, 28, 20);
    const mesh = new THREE.Mesh(geometry, materialFor('cell', 0, true));
    mesh.name = 'navigation-current-cell';
    mesh.userData.navigationLeaf = true;
    mesh.userData.navigationId = currentTarget;
    mesh.position.set(0, 0.15, 0);
    mesh.scale.set(1.15, 0.82, 0.92);
    deepGroup.add(mesh);
  }

  function rebuild() {
    const manager = window.spatialViewportManager;
    if (!managerReady()) return false;

    const currentLevel = level();
    const currentTarget = target();
    const currentPath = path().join(' > ');
    const currentChildren = children();
    const isMacro = currentLevel === 'macro' || currentLevel === 'macro anatomy';
    const state = `${currentLevel}|${currentPath}|${currentTarget}`;

    const group = ensureGroup(manager);
    group.visible = !isMacro;
    manager.active.root.visible = isMacro;
    clearGroup();
    manager.activeKey = `${currentLevel}|${currentTarget}`;

    if (isMacro) {
      manager.active.clickable = [...(manager.active.clickable || [])];
      lastVisualState = '';
      return true;
    }

    const kind = currentLevel === 'tissue' ? 'tissue'
      : currentLevel === 'cellular' ? 'cellular'
      : currentLevel === 'cell' ? 'cell'
      : null;
    if (!kind) return true;

    if (state !== lastVisualState) {
      cameraFor(kind);
      lastVisualState = state;
    }

    if (!currentChildren.length) {
      addLeaf(kind, currentTarget);
      manager.active.clickable = [...deepGroup.children];
      group.position.set(0, 0.25, 0);
      return true;
    }

    const spacing = kind === 'cell' ? 1.65 : 2.25;
    const geometry = kind === 'tissue'
      ? new THREE.CapsuleGeometry(0.62, 1.5, 8, 18)
      : kind === 'cellular'
        ? new THREE.BoxGeometry(1.35, 0.72, 0.32)
        : new THREE.SphereGeometry(0.48, 20, 16);

    currentChildren.forEach((label, index) => {
      const mesh = new THREE.Mesh(geometry.clone(), materialFor(kind, index));
      mesh.name = `navigation-target-${index}`;
      mesh.userData.navigationIndex = index;
      mesh.userData.navigationLabel = label;
      mesh.position.set((index - (currentChildren.length - 1) / 2) * spacing, 0.15, 0);
      if (kind === 'tissue') mesh.scale.set(1.15, 0.82, 0.78);
      if (kind === 'cellular') mesh.rotation.y = (index - 1) * 0.22;
      group.add(mesh);
    });

    manager.active.clickable = [...group.children];
    group.position.set(0, 0.25, 0);
    return true;
  }

  window.testhpViewportPostRender = rebuild;

  function publish(reason) {
    const manager = window.spatialViewportManager;
    if (!managerReady()) return;
    window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', {
      detail: { level: level(), target: target(), path: path(), children: children(), renderer: 'ThreeCanvasRenderer', reason }
    }));
  }

  function clickSpatialTargetByIndex(index) {
    const button = Number.isInteger(index) ? childButtons()[index] : null;
    if (!button) return false;
    button.click();
    return true;
  }

  function handleDeepClick(event) {
    if (level() === 'macro' || level() === 'macro anatomy' || !deepGroup?.visible) return false;
    const manager = window.spatialViewportManager;
    if (!managerReady()) return false;
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return false;

    pointer.x = Math.max(-1, Math.min(1, ((event.clientX - rect.left) / rect.width) * 2 - 1));
    pointer.y = Math.max(-1, Math.min(1, -(((event.clientY - rect.top) / rect.height) * 2 - 1)));
    raycaster.setFromCamera(pointer, manager.active.camera);

    const hit = raycaster.intersectObjects(deepGroup.children, true).find(x => x.object?.userData);
    if (!hit) return false;

    const data = hit.object.userData;
    const index = Number.isInteger(data.navigationIndex) ? data.navigationIndex : null;
    const navigated = index === null ? false : clickSpatialTargetByIndex(index);
    window.dispatchEvent(new CustomEvent('testhp:viewport-deep-click', {
      detail: { level: level(), target: target(), path: path(), child: data.navigationLabel || data.navigationId || target(), index, navigated, leaf: !!data.navigationLeaf }
    }));
    return navigated;
  }

  canvas.addEventListener('click', event => {
    if (level() === 'macro' || level() === 'macro anatomy') return;
    handleDeepClick(event);
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);

  window.addEventListener('testhp:viewport-rendered', () => {
    if (!managerReady()) return;
    rebuild();
    window.spatialViewportManager.active.renderer?.render?.(window.spatialViewportManager.active.scene, window.spatialViewportManager.active.camera);
  }, true);

  window.addEventListener('testhp:spatial-layer-changed', event => {
    const manager = window.spatialViewportManager;
    const detail = event.detail || {};
    if (!manager || !detail.level) return;
    manager.activeKey = `${String(detail.level).toLowerCase()}|${detail.target || 'spatial-target'}`;
    lastVisualState = '';
    rebuild();
  });

  const observer = new MutationObserver(() => {
    hookManager();
    rebuild();
    publish('dom-mutation');
  });
  ['spatial-level-badge', 'spatial-breadcrumb', 'spatial-node', 'spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
  });

  function hookManager() {
    const manager = window.spatialViewportManager;
    if (!managerReady() || managerHooked) return !!manager;
    const originalRender = manager.render.bind(manager);
    manager.render = () => {
      const result = originalRender();
      rebuild();
      manager.active.renderer?.render?.(manager.active.scene, manager.active.camera);
      return result;
    };
    managerHooked = true;
    rebuild();
    publish('manager-hooked');
    return true;
  }

  const timer = setInterval(() => { if (hookManager()) rebuild(); }, 100);
  window.addEventListener('beforeunload', () => { clearInterval(timer); observer.disconnect(); }, { once: true });
  window.addEventListener('testhp:viewport-manager-ready', () => { hookManager(); rebuild(); publish('manager-ready'); });

  hookManager();
  rebuild();
  publish('initial');
})();
