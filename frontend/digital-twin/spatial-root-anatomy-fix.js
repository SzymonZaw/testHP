(() => {
  const ROOT_PARTS = [
    { id: 'palm', label: 'Śródręcze', level: 'macro', regionId: 'palm' },
    { id: 'thumb', label: 'Kciuk', level: 'macro', regionId: 'thumb' },
    { id: 'index', label: 'Palec wskazujący', level: 'macro', regionId: 'index' },
    { id: 'middle', label: 'Palec środkowy', level: 'macro', regionId: 'middle' },
    { id: 'ring', label: 'Palec serdeczny', level: 'macro', regionId: 'ring' },
    { id: 'little', label: 'Mały palec', level: 'macro', regionId: 'little' },
    { id: 'wrist', label: 'Nadgarstek', level: 'macro', regionId: 'wrist' }
  ];

  const $ = id => document.getElementById(id);
  const labels = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(b => b.textContent.trim()).filter(Boolean);
  const currentIsRoot = () => {
    const path = labels();
    return path.length === 1 && /^(dłoń|hand)$/i.test(path[0]);
  };

  function setDiagnostic(detail) {
    window.__testhpSpatialNavDiagnostic = {
      reason: detail,
      rootTarget: 'Dłoń',
      expectedChildren: ROOT_PARTS.map(x => x.label),
      expectedChildLevel: 'Anatomia makro',
      invalidFallback: 'Regional field',
      source: 'spatial-root-anatomy-fix.js'
    };
    window.dispatchEvent(new CustomEvent('testhp:spatial-diagnostic', { detail: window.__testhpSpatialNavDiagnostic }));
  }

  function activate(part) {
    const target = {
      ...part,
      spatial_id: part.id,
      spatialId: part.id
    };
    const manager = window.spatialViewportManager;

    // The canonical target contract uses spatial_id. Keep id/regionId as
    // compatibility fields because the renderer still consumes them.
    if (manager?.setSpatialTarget) {
      try {
        manager.setSpatialTarget(target);
        window.dispatchEvent(new CustomEvent('testhp:spatial-layer-changed', { detail: target }));
        window.dispatchEvent(new CustomEvent('testhp:spatial-target-changed', { detail: target }));
        if (window.testhpSpatialContract?.publish) window.testhpSpatialContract.publish(target);
        setDiagnostic(`Selected anatomical part '${part.label}' from root Dłoń.`);
        return;
      } catch (error) {
        console.error('[Twin navigation] target selection failed', error);
      }
    }

    // Keep the navigation responsive even if the renderer manager is temporarily unavailable.
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-request', { detail: target }));
    if (window.testhpSpatialContract?.publish) window.testhpSpatialContract.publish(target);
    setDiagnostic(`Selected anatomical part '${part.label}' from root Dłoń; renderer manager was unavailable.`);
  }

  function installButtonStyle(button) {
    button.disabled = false;
    button.removeAttribute('aria-disabled');
    button.style.pointerEvents = 'auto';
    button.style.cursor = 'pointer';
    button.style.position = 'relative';
    button.style.zIndex = '1';
  }

  function renderRootParts() {
    const children = $('spatial-children');
    if (!children || !currentIsRoot()) return false;
    const expected = ROOT_PARTS.map(x => x.label);
    const existing = [...children.querySelectorAll('.spatial-root-anatomical-part')].map(x => x.querySelector('strong')?.textContent.trim() || '');
    if (existing.length === expected.length && existing.every((value, i) => value === expected[i])) {
      children.querySelectorAll('.spatial-root-anatomical-part').forEach(installButtonStyle);
      setDiagnostic("Root Dłoń is normalized to anatomical macro parts.");
      return false;
    }

    children.replaceChildren();
    ROOT_PARTS.forEach(part => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'spatial-target spatial-root-anatomical-part';
      button.dataset.spatialId = part.id;
      button.dataset.rootAnatomicalPart = part.id;
      const title = document.createElement('strong');
      title.textContent = part.label;
      const meta = document.createElement('span');
      meta.textContent = 'Anatomia makro';
      button.append(title, meta);
      installButtonStyle(button);
      button.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        activate(part);
      });
      children.appendChild(button);
    });

    setDiagnostic("Root Dłoń is rendered as clickable anatomical macro targets; 'Regional field' is not used here.");
    return true;
  }

  function install() {
    const tryApply = () => {
      if (currentIsRoot()) renderRootParts();
    };
    tryApply();
    const observer = new MutationObserver(() => {
      if (currentIsRoot()) requestAnimationFrame(tryApply);
    });
    ['spatial-breadcrumb', 'spatial-children', 'spatial-node', 'spatial-level-badge'].forEach(id => {
      const el = $(id);
      if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
    });
    window.addEventListener('testhp:viewport-manager-ready', tryApply);
    window.addEventListener('testhp:spatial-layer-changed', tryApply);
    window.addEventListener('testhp:viewport-rendered', tryApply);
    setInterval(tryApply, 500);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
