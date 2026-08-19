import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  const viewport = document.getElementById('twin-viewport');
  const canvas = document.getElementById('twin-canvas');
  if (!viewport || !canvas) return;

  const text = id => document.getElementById(id)?.textContent?.trim() || '';
  const level = () => text('spatial-level-badge').toLowerCase();
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const path = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const children = () => [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);

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

    // The canonical manager may replace `active` (and therefore its Scene)
    // during every render. Keep the deep navigation group attached to the
    // CURRENT scene instead of leaving it orphaned on a previous scene.
    if (attachedScene !== scene) {
      if (deepGroup.parent) deepGroup.parent.remove(deepGroup);
      scene.add(deepGroup);
      attachedScene = scene;
    }
    return deepGroup;
  }

  function materialFor(kind, index) {
    const colors = {
      tissue: [0x8bd3c7, 0x72b8df, 0xd6a64f],
      cellular: [0x7fc8ff, 0xb78cff, 0x7fe0b0],
      cell: [0x66b3ff, 0xd6a64f, 0xc58cff]
    };
    const color = colors[kind][index % 3];
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.55,
      metalness: 0.05,
      transparent: true,
      opacity: kind === 'cell' ? 0.9 : 0.72,
      emissive: color,
      emissiveIntensity: 0.12
    });
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

    // Always synchronize the canonical descriptor with the DOM spatial state.
    // The canonical render loop may replace `active`, so this must run after
    // every canonical render, not only after navigation clicks.
    manager.activeKey = `${currentLevel}|${currentTarget}`;

    if (isMacro || !currentChildren.length) {
      // Deep levels own the interaction pool. Never leave the canonical
      // macro-region meshes clickable after a deep render has replaced them.
      manager.active.clickable = isMacro ? [...(manager.active.clickable || [])] : [];
      return true;
    }

    const kind = currentLevel.includes('tissue') ? 'tissue'
      : currentLevel.includes('cellular') ? 'cellular'
      : (currentLevel.includes('single') || currentLevel.includes('cell')) ? 'cell'
      : null;
    if (!kind) return true;

    if (state !== lastVisualState) {
      manager.active.camera.position.set(0, kind === 'cell' ? 0.55 : 0.8, kind === 'cell' ? 5.8 : 7.2);
      manager.active.controls.target.set(0, 0.2, 0);
      manager.active.controls.update();
      lastVisualState = state;
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

  // app.js historically supports this post-render hook. Keep it registered so
  // the canonical renderer can explicitly ask the spatial layer to resync.
  window.testhpViewportPostRender = rebuild;

  function publish(reason) {
    const manager = window.spatialViewportManager;
    if (!managerReady()) return;
    window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', {
      detail: {
        level: level(), target: target(), path: path(), children: children(),
        renderer: manager.active?.constructor?.name || 'ThreeCanvasRenderer', reason
      }
    }));
  }

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

  function clickSpatialTarget(label) {
    const button = [...document.querySelectorAll('#spatial-children .spatial-target')]
      .find(el => el.querySelector('strong')?.textContent?.trim() === label);
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
    const hit = raycaster.intersectObjects(deepGroup.children, true).find(x => x.object?.userData?.navigationLabel);
    if (!hit) return false;
    const label = hit.object.userData.navigationLabel;
    const navigated = clickSpatialTarget(label);
    window.dispatchEvent(new CustomEvent('testhp:viewport-deep-click', {
      detail: { level: level(), target: target(), path: path(), child: label, navigated }
    }));
    return navigated;
  }

  canvas.addEventListener('click', event => {
    if (level() === 'macro' || level() === 'macro anatomy') return;
    handleDeepClick(event);
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);

  // The canonical manager emits this event AFTER replacing `active`. Rebuild
  // immediately so the deep scene and clickable pool cannot be stale for a
  // render tick (the previous 100 ms polling window was race-prone).
  window.addEventListener('testhp:viewport-rendered', () => {
    if (managerReady()) {
      rebuild();
      window.spatialViewportManager.active.renderer?.render?.(
        window.spatialViewportManager.active.scene,
        window.spatialViewportManager.active.camera
      );
    }
  }, true);

  // Navigation changes are the authoritative source of activeKey. Synchronize
  // it immediately instead of waiting for the next renderer cycle.
  window.addEventListener('testhp:spatial-layer-changed', event => {
    const manager = window.spatialViewportManager;
    const detail = event.detail || {};
    if (!manager || !detail.level) return;
    manager.activeKey = `${String(detail.level).toLowerCase()}|${detail.target || 'spatial-target'}`;
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

  const timer = setInterval(() => {
    if (hookManager()) rebuild();
  }, 100);
  window.addEventListener('beforeunload', () => { clearInterval(timer); observer.disconnect(); }, { once: true });
  window.addEventListener('testhp:viewport-manager-ready', () => { hookManager(); rebuild(); publish('manager-ready'); });

  hookManager();
  rebuild();
  publish('initial');
})();
