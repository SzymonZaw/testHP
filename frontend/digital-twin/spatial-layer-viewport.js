(() => {
  const canvas = document.getElementById('twin-canvas');
  if (!canvas) return;
  const level = () => document.getElementById('spatial-level-badge')?.textContent?.trim() || 'MACRO';
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const crumbs = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const children = () => [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);
  function report() {
    const m = window.spatialViewportManager;
    if (!m?.active?.scene) return;
    m.render?.();
    window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', {detail:{level:level(),target:target(),path:crumbs(),children:children(),renderer:'ThreeCanvasRenderer'}}));
  }
  const observer = new MutationObserver(() => requestAnimationFrame(report));
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, {childList:true,subtree:true,characterData:true});
  });
  window.addEventListener('testhp:viewport-manager-ready', report);
  window.addEventListener('resize', () => window.spatialViewportManager?.resize?.(), {passive:true});
  window.addEventListener('beforeunload', () => observer.disconnect(), {once:true});
  report();
})();
