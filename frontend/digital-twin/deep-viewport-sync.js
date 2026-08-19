import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  const canvas = document.getElementById('twin-canvas');
  if (!canvas) return;

  let group = null;
  let sceneRef = null;
  let wrapped = false;
  let lastKey = '';

  const text = id => document.getElementById(id)?.textContent?.trim() || '';
  const levelFromDom = () => {
    const value = text('spatial-level-badge').toLowerCase();
    if (value.includes('pojedyncz') || value.includes('single') || value.includes('cell')) return 'cell';
    if (value.includes('komórkow') || value.includes('cellular')) return 'cellular';
    if (value.includes('tkank') || value.includes('tissue')) return 'tissue';
    return 'macro';
  };
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const children = () => [...document.querySelectorAll('#spatial-children .spatial-target')]
    .map(b => b.querySelector('strong')?.textContent?.trim()).filter(Boolean);
  const ready = () => { const m = window.spatialViewportManager; return !!(m?.active?.scene && m?.active?.camera && m?.active?.renderer); };

  const ensureGroup = m => {
    if (!group) { group = new THREE.Group(); group.name = 'canonical-deep-navigation-layer'; }
    if (sceneRef !== m.active.scene) {
      if (group.parent) group.parent.remove(group);
      m.active.scene.add(group); sceneRef = m.active.scene;
    }
    return group;
  };
  const clear = () => {
    if (!group) return;
    for (const object of [...group.children]) {
      object.traverse(child => {
        if (!child.isMesh) return;
        child.geometry?.dispose?.();
        if (Array.isArray(child.material)) child.material.forEach(x => x.dispose?.()); else child.material?.dispose?.();
      });
      group.remove(object);
    }
  };
  const material = (kind, index) => {
    const colors = kind === 'tissue' ? [0x8bd3c7,0x72b8df,0xd6a64f] : kind === 'cellular' ? [0x7fc8ff,0xb78cff,0x7fe0b0] : [0x66b3ff,0xd6a64f,0xc58cff];
    const color = colors[index % colors.length];
    return new THREE.MeshStandardMaterial({color, roughness:.52, metalness:.04, transparent:true, opacity:kind==='cell'?.92:.78, emissive:color, emissiveIntensity:.12});
  };

  function rebuild(force = false) {
    if (!ready()) return false;
    const m = window.spatialViewportManager;
    const currentLevel = levelFromDom();
    const labels = children();
    const currentTarget = target();
    const key = `${currentLevel}|${currentTarget}|${labels.join('|')}`;
    const g = ensureGroup(m);
    const isMacro = currentLevel === 'macro';
    if (!force && key === lastKey) { g.visible = !isMacro; m.active.root.visible = isMacro; return true; }
    lastKey = key; clear();
    g.visible = !isMacro; m.active.root.visible = isMacro; m.active.activeLayer = isMacro ? 'macro' : 'deep'; m.activeKey = `${currentLevel}|${currentTarget}`;

    if (isMacro) {
      m.active.deepClickable = []; m.active.clickable = [...(m.active.root?.children || [])];
      m.active.renderer.render(m.active.scene, m.active.camera); return true;
    }

    const kind = currentLevel === 'tissue' ? 'tissue' : currentLevel === 'cellular' ? 'cellular' : 'cell';
    if (!labels.length && kind === 'cell') {
      const mesh = new THREE.Mesh(new THREE.SphereGeometry(1.05,32,24), material('cell',0));
      mesh.name='canonical-current-cell'; mesh.userData.navigationLeaf=true; mesh.userData.navigationId=currentTarget; mesh.position.set(0,.15,0); mesh.scale.set(1.2,.86,.95); g.add(mesh);
    } else if (labels.length) {
      const geometry = kind === 'tissue' ? new THREE.CapsuleGeometry(.62,1.5,8,20) : kind === 'cellular' ? new THREE.BoxGeometry(1.4,.76,.34) : new THREE.SphereGeometry(.5,24,18);
      const spacing = kind === 'cell' ? 1.8 : 2.35;
      labels.forEach((label,index) => {
        const mesh = new THREE.Mesh(geometry.clone(), material(kind,index));
        mesh.name=`canonical-navigation-target-${index}`; mesh.userData.navigationIndex=index; mesh.userData.navigationLabel=label; mesh.position.set((index-(labels.length-1)/2)*spacing,.15,0);
        if (kind==='tissue') mesh.scale.set(1.15,.82,.78); if (kind==='cellular') mesh.rotation.y=(index-1)*.22; g.add(mesh);
      });
      geometry.dispose?.();
    }

    m.active.deepClickable=[...g.children]; m.active.clickable=[...g.children];
    const camera=m.active.camera, controls=m.active.controls;
    if (camera && controls) { const z=kind==='cell'?5.8:kind==='cellular'?7.2:8; camera.position.set(0,kind==='cell'?.55:.8,z); controls.target.set(0,.2,0); controls.update(); }
    m.active.renderer.render(m.active.scene,m.active.camera);
    window.dispatchEvent(new CustomEvent('testhp:deep-viewport-sync',{detail:{level:currentLevel,target:currentTarget,children:labels,activeLayer:m.active.activeLayer,deepVisible:g.visible,deepChildren:g.children.length,clickable:m.active.clickable.length,renderer:'ThreeCanvasRenderer',reason:force?'forced':'state-change'}}));
    return true;
  }

  function install() {
    const m=window.spatialViewportManager;
    if (!ready()) return false;
    if (!wrapped) {
      const original=m.render?.bind(m);
      if (original) m.render=(...args)=>{ const result=original(...args); rebuild(true); return result; };
      wrapped=true;
    }
    rebuild(true); return true;
  }

  const observer=new MutationObserver(()=>requestAnimationFrame(install));
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{ const el=document.getElementById(id); if(el) observer.observe(el,{childList:true,subtree:true,characterData:true,attributes:true}); });
  window.addEventListener('testhp:spatial-layer-changed',()=>requestAnimationFrame(install),true);
  window.addEventListener('testhp:viewport-rendered',()=>requestAnimationFrame(install),true);
  window.setInterval(install,200);
  window.addEventListener('beforeunload',()=>observer.disconnect(),{once:true});
  install();
})();
