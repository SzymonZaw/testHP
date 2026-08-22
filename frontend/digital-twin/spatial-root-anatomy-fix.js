import('./spatial-writer-debug.js?v=writer-debug-1').catch(error => console.error('[Twin navigation] writer debug failed to load', error));

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
    const target = { ...part, spatial_id: part.id, spatialId: part.id };
    const manager = window.spatialViewportManager;
    if (manager?.setSpatialTarget) {
      try {
        manager.setSpatialTarget(target);
        if (window.testhpSpatialContract?.publish) window.testhpSpatialContract.publish(target);
        setDiagnostic(`Selected anatomical part '${part.label}' from root Dłoń.`);
        return;
      } catch (error) {
        console.error('[Twin navigation] target selection failed', error);
      }
    }
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

  function isCanonicalRootDom(children) {
    const direct = [...children.children];
    if (direct.length !== ROOT_PARTS.length) return false;
    if (!direct.every(el => el.matches('button.spatial-root-anatomical-part.spatial-target'))) return false;
    const directLabels = direct.map(el => el.querySelector(':scope > strong')?.textContent?.trim() || '');
    if (!directLabels.every((value, i) => value === ROOT_PARTS[i].label)) return false;
    if (children.querySelector('.spatial-root-anatomical-part .spatial-target')) return false;
    return true;
  }

  function installDelegatedRootClick() {
    if (window.__testhpRootMacroClickHandlerInstalled) return;
    window.__testhpRootMacroClickHandlerInstalled = true;
    document.addEventListener('click', event => {
      const button = event.target?.closest?.('#spatial-children > .spatial-root-anatomical-part');
      if (!button || !currentIsRoot()) return;
      const part = ROOT_PARTS.find(x => x.id === button.dataset.spatialId);
      if (!part) return;
      event.preventDefault();
      event.stopPropagation();
      activate(part);
    }, true);
  }

  function renderRootParts() {
    const children = $('spatial-children');
    if (!children || !currentIsRoot()) return false;

    if (isCanonicalRootDom(children)) {
      children.querySelectorAll(':scope > .spatial-root-anatomical-part').forEach(installButtonStyle);
      setDiagnostic('Root Dłoń has exactly 7 direct anatomical macro targets; no nested navigation targets.');
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

    setDiagnostic("Root Dłoń was normalized: only direct anatomical macro targets remain; stale nested targets were removed.");
    return true;
  }

  function install() {
    installDelegatedRootClick();
    let scheduled = false;
    const tryApply = () => {
      scheduled = false;
      if (currentIsRoot()) renderRootParts();
    };
    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(tryApply);
    };

    tryApply();
    const observer = new MutationObserver(schedule);
    ['spatial-breadcrumb', 'spatial-children', 'spatial-node', 'spatial-level-badge'].forEach(id => {
      const el = $(id);
      if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
    });
    window.addEventListener('testhp:viewport-manager-ready', schedule);
    window.addEventListener('testhp:spatial-layer-changed', schedule);
    window.addEventListener('testhp:viewport-rendered', schedule);
    window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
