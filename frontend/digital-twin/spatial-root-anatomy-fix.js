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

  let applied = false;
  let reason = '';

  function setDiagnostic(detail) {
    reason = detail;
    window.__testhpSpatialNavDiagnostic = {
      reason: detail,
      rootTarget: 'Dłoń',
      expectedChildren: ROOT_PARTS.map(x => x.label),
      expectedChildLevel: 'Anatomia makro',
      invalidFallback: 'Regional field',
      source: 'spatial-root-anatomy-fix.js'
    };
    window.dispatchEvent(new CustomEvent('testhp:spatial-diagnostic', { detail: window.__testhpSpatialNavDiagnostic }));
    const panel = $('twin-debug-panel');
    if (!panel) return;
    let pre = $('twin-debug-navigation');
    if (!pre) {
      pre = document.createElement('pre');
      pre.id = 'twin-debug-navigation';
      pre.style.cssText = 'margin:8px 0 0;padding:8px;border-top:1px solid #31534c;white-space:pre-wrap;color:#dcece6;font:11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace';
      panel.appendChild(pre);
    }
    pre.textContent = [
      '', 'NAVIGATION DIAGNOSTIC',
      `reason:          ${detail}`,
      'root target:     Dłoń',
      `expected next:   ${ROOT_PARTS.map(x => x.label).join(' | ')}`,
      'expected level:  Anatomia makro',
      'bad fallback:    Regional field',
      'correction:      root-level targets are anatomical parts; tissue begins only after a selected part'
    ].join('\n');
  }

  function renderRootParts() {
    const children = $('spatial-children');
    if (!children || !currentIsRoot()) return false;

    const before = [...children.querySelectorAll('.spatial-target strong')].map(x => x.textContent.trim());
    children.replaceChildren();
    ROOT_PARTS.forEach(part => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'spatial-target spatial-root-anatomical-part';
      button.dataset.rootAnatomicalPart = part.id;
      const title = document.createElement('strong');
      title.textContent = part.label;
      const meta = document.createElement('span');
      meta.textContent = 'Anatomia makro';
      button.append(title, meta);
      button.addEventListener('click', () => {
        const manager = window.spatialViewportManager;
        if (manager?.setSpatialTarget) {
          manager.setSpatialTarget({ ...part });
          setDiagnostic(`Selected anatomical part '${part.label}' from root Dłoń.`);
        }
      });
      children.appendChild(button);
    });

    const wasFallback = before.length === 1 && before[0].toLowerCase() === 'regional field';
    setDiagnostic(wasFallback
      ? "The canonical navigator exposed 'Regional field' because childTargets(hand) used a generic tissue fallback for the root node with no regionId."
      : "Root Dłoń is being rendered as an anatomical macro container; 'Regional field' is not a valid immediate anatomical child.");
    applied = true;
    return true;
  }

  function install() {
    const tryApply = () => {
      if (!currentIsRoot()) return;
      renderRootParts();
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
    setInterval(() => { if (currentIsRoot()) tryApply(); }, 500);
    setDiagnostic('Waiting for canonical spatial manager; root navigation will use anatomical parts instead of a generic tissue fallback.');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
