(() => {
  const src = '/digital-twin/viewport-geometry-bridge.js?v=main-geometry-bridge-1';
  if (document.querySelector(`script[src^="${src.split('?')[0]}"]`)) return;
  const s = document.createElement('script');
  s.src = src;
  s.dataset.mainGeometryBridge = '1';
  (document.head || document.body).appendChild(s);
})();
