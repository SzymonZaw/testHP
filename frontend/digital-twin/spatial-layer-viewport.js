(() => {
  const canvas = document.getElementById('twin-canvas');
  if (!canvas) return;
  const level = () => document.getElementById('spatial-level-badge')?.textContent?.trim() || 'MACRO';
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const crumbs = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const children = () => [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);

  const HAND_MACRO_TARGETS = [
    { id: 'palm', label: 'Śródręcze' },
    { id: 'little', label: 'Mały palec' },
    { id: 'ring', label: 'Palec serdeczny' },
    { id: 'middle', label: 'Palec środkowy' },
    { id: 'index', label: 'Palec wskazujący' },
    { id: 'thumb', label: 'Kciuk' },
    { id: 'wrist', label: 'Nadgarstek' }
  ];

  function isHandRoot() {
    const m = window.spatialViewportManager;
    const state = m?.state;
    const path = crumbs();
    return state?.level === 'macro' && state?.id === 'hand' && path.length === 1;
  }

  function installHandMacroTargets() {
    if (!isHandRoot()) return false;
    const container = document.getElementById('spatial-children');
    const manager = window.spatialViewportManager;
    if (!container || !manager?.setSpatialTarget) return false;

    const current = [...container.querySelectorAll('.spatial-target strong')].map(x => x.textContent.trim());
    const expected = HAND_MACRO_TARGETS.map(x => x.label);
    if (JSON.stringify(current) === JSON.stringify(expected)) return false;

    container.replaceChildren();
    for (const target of HAND_MACRO_TARGETS) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'spatial-target';
      const title = document.createElement('strong');
      title.textContent = target.label;
      const meta = document.createElement('span');
      meta.textContent = 'Macro anatomy';
      button.append(title, meta);
      button.addEventListener('click', () => manager.setSpatialTarget({
        id: target.id,
        label: target.label,
        level: 'macro',
        regionId: target.id
      }));
      container.appendChild(button);
    }

    window.dispatchEvent(new CustomEvent('testhp:spatial-root-macro-fixed', {
      detail: { target: 'Dłoń', children: expected }
    }));
    return true;
  }

  function report() {
    const m = window.spatialViewportManager;
    if (!m?.active?.scene) return;
    installHandMacroTargets();
    m.render?.();
    installHandMacroTargets();
    window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', {
      detail: { level: level(), target: target(), path: crumbs(), children: children(), renderer: 'ThreeCanvasRenderer' }
    }));
  }

  const observer = new MutationObserver(() => requestAnimationFrame(report));
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList:true, subtree:true, characterData:true });
  });
  window.addEventListener('testhp:viewport-manager-ready', report);
  window.addEventListener('testhp:spatial-layer-changed', report);
  window.addEventListener('resize', () => window.spatialViewportManager?.resize?.(), { passive:true });
  window.addEventListener('beforeunload', () => observer.disconnect(), { once:true });
  report();
})();