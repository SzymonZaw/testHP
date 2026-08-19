import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  // Bridge around the canonical Three.js viewport owned by app.js.
  // This module never creates a second renderer. It only adds/removes
  // navigation-only geometry inside the canonical scene and lets the
  // existing animation loop render it.
  const viewport = document.getElementById('twin-viewport');
  const canvas = document.getElementById('twin-canvas');
  if (!viewport || !canvas) return;

  const level = () => (document.getElementById('spatial-level-badge')?.textContent || 'MACRO').trim().toLowerCase();
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const crumbs = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const children = () => [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);

  const canonical = () => {
    const manager = window.spatialViewportManager;
    return !!(manager && manager.version === 'canonical-three-1' && manager.active?.scene && manager.active?.camera);
  };

  let lastSignature = '';
  let deepGroup = null;
  let lastVisualState = '';
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  function publish(reason = 'state-change') {
    const manager = window.spatialViewportManager;
    if (!manager) {
      window.dispatchEvent(new CustomEvent('testhp:viewport-waiting', { detail: { reason: 'canonical manager not published yet' } }));
      return false;
    }
    if (!canonical()) {
      window.dispatchEvent(new CustomEvent('testhp:viewport-error', { detail: { error: new Error('Non-canonical viewport manager detected; refusing to replace the real renderer') } }));
      return false;
    }

    const detail = {
      level: level(),
      target: target(),
      path: crumbs(),
      children: children(),
      renderer: manager.active?.constructor?.name || 'ThreeCanvasRenderer',
      reason
    };
    const signature = JSON.stringify(detail);
    if (signature !== lastSignature) {
      lastSignature = signature;
      window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', { detail }));
    }
    return true;
  }

  function clearDeepGroup() {
    if (!deepGroup) return;
    deepGroup.traverse(object => {
      if (!object.isMesh) return;
      object.geometry?.dispose?.();
      if (Array.isArray(object.material)) object.material.forEach(m => m.dispose?.());
      else object.material?.dispose?.();
    });
    deepGroup.clear();
  }

  function ensureDeepGroup() {
    if (deepGroup) return deepGroup;
    const manager = window.spatialViewportManager;
    if (!manager?.active?.scene) return null;
    deepGroup = new THREE.Group();
    deepGroup.name = 'digital-twin-navigation-layer';
    manager.active.scene.add(deepGroup);
    return deepGroup;
  }

  function materialFor(currentLevel, index) {
    const colors = {
      tissue: [0x8bd3c7, 0x72b8df, 0xd6a64f],
      cellular: [0x7fc8ff, 0xb78cff, 0x7fe0b0],
      cell: [0x66b3ff, 0xd6a64f, 0xc58cff]
    };
    const color = (colors[currentLevel] || colors.tissue)[index % 3];
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.55,
      metalness: 0.05,
      transparent: true,
      opacity: currentLevel === 'cell' ? 0.9 : 0.72,
      emissive: color,
      emissiveIntensity: 0.12
    });
  }

  function focusDeepView(manager, state) {
    if (!manager?.active?.camera || !manager.active?.controls || state === lastVisualState) return;
    const camera = manager.active.camera;
    const controls = manager.active.controls;
    camera.position.set(0, 0.8, 7.2);
    controls.target.set(0, 0.2, 0);
    controls.update();
    lastVisualState = state;
  }

  function buildDeepGeometry() {
    const manager = window.spatialViewportManager;
    if (!manager?.active?.root || !manager.active?.scene) return;
    const currentLevel = level();
    const currentTarget = target();
    const currentPath = crumbs().join(' > ');
    const currentChildren = children();
    const state = `${currentLevel}|${currentPath}|${currentTarget}`;

    const root = manager.active.root;
    const isMacro = currentLevel === 'macro' || currentLevel === 'macro anatomy';
    root.visible = isMacro;

    const group = ensureDeepGroup();
    if (!group) return;
    group.visible = !isMacro;
    clearDeepGroup();

    manager.activeKey = `${currentLevel}|${currentTarget}`;
    manager.active = {
      ...manager.active,
      clickable: group.visible ? group.children : manager.active.clickable
    };

    if (isMacro || !currentChildren.length) return;

    const isTissue = currentLevel.includes('tissue');
    const isCellular = currentLevel.includes('cellular');
    const isCell = currentLevel.includes('single') || currentLevel.includes('cell');
    if (!isTissue && !isCellular && !isCell) return;

    focusDeepView(manager, state);

    const spacing = isCell ? 1.65 : 2.25;
    const geometry = isTissue
      ? new THREE.CapsuleGeometry(0.62, 1.5, 8, 18)
      : isCellular
        ? new THREE.BoxGeometry(1.35, 0.72, 0.32)
        : new THREE.SphereGeometry(0.48, 20, 16);

    currentChildren.forEach((label, index) => {
      const mesh = new THREE.Mesh(geometry.clone(), materialFor(isTissue ? 'tissue' : isCellular ? 'cellular' : 'cell', index));
      mesh.name = `navigation-target-${index}`;
      mesh.userData.navigationLabel = label;
      mesh.position.set((index - (currentChildren.length - 1) / 2) * spacing, 0.15, 0);
      if (isTissue) mesh.scale.set(1.15, 0.82, 0.78);
      if (isCellular) mesh.rotation.y = (index - 1) * 0.22;
      group.add(mesh);
    });

    // Schematic navigation geometry only. It represents a spatial target,
    // never fabricated biological evidence.
    group.position.set(0, 0.25, 0);
  }

  function clickSpatialTarget(label) {
    const button = [...document.querySelectorAll('#spatial-children .spatial-target')]
      .find(el => el.querySelector('strong')?.textContent?.trim() === label);
    if (button) {
      button.click();
      return true;
    }
    return false;
  }

  function handleDeepClick(event) {
    const currentLevel = level();
    if (currentLevel === 'macro' || currentLevel === 'macro anatomy') return false;
    if (!deepGroup?.visible) return false;

    const manager = window.spatialViewportManager;
    if (!manager?.active?.camera) return false;
    const rect = canvas.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
    raycaster.setFromCamera(pointer, manager.active.camera);
    const hits = raycaster.intersectObjects(deepGroup.children, true);
    const hit = hits.find(item => item.object?.userData?.navigationLabel);
    if (!hit) return false;

    const label = hit.object.userData.navigationLabel;
    const navigated = clickSpatialTarget(label);
    window.dispatchEvent(new CustomEvent('testhp:viewport-deep-click', {
      detail: {
        level: currentLevel,
        target: target(),
        path: crumbs(),
        child: label,
        navigated,
        clientX: event.clientX,
        clientY: event.clientY,
        message: navigated ? '3D navigation target selected.' : '3D target found, but matching spatial control was unavailable.'
      }
    }));
    return navigated;
  }

  // In deep layers the canonical macro click handler must not receive the
  // event. We raycast the navigation-only layer first and then route the hit
  // through the existing DOM spatial target button, keeping one source of truth.
  canvas.addEventListener('click', event => {
    const currentLevel = level();
    if (currentLevel === 'macro' || currentLevel === 'macro anatomy') return;
    handleDeepClick(event);
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);

  const observer = new MutationObserver(() => {
    buildDeepGeometry();
    publish('dom-mutation');
  });
  ['spatial-level-badge', 'spatial-breadcrumb', 'spatial-node', 'spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
  });

  window.addEventListener('testhp:viewport-manager-ready', () => {
    buildDeepGeometry();
    publish('manager-ready');
  });
  window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });

  buildDeepGeometry();
  publish('initial');
})();
