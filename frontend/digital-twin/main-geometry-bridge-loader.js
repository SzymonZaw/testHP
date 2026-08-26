(() => {
  const loaders = [
    ['/digital-twin/viewport-geometry-bridge.js?v=main-geometry-bridge-1', 'mainGeometryBridge'],
    ['/digital-twin/hand-geometry-mode-switch.js?v=hand-geometry-mode-1', 'handGeometryMode'],
  ];
  loaders.forEach(([src, dataKey]) => {
    const clean = src.split('?')[0];
    if (document.querySelector(`script[src^="${clean}"]`)) return;
    const s = document.createElement('script');
    s.src = src;
    s.dataset[dataKey] = '1';
    (document.head || document.body).appendChild(s);
  });
})();
