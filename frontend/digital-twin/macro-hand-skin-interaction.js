(() => {
  const viewport = document.getElementById('twin-viewport');
  const baseCanvas = document.getElementById('twin-canvas');
  if (!viewport || !baseCanvas) return;

  const attach = () => {
    const canvas = document.getElementById('macro-hand-skin-canvas');
    if (!canvas || canvas.dataset.interactionReady === '1') return;
    canvas.dataset.interactionReady = '1';
    canvas.style.pointerEvents = 'auto';

    let downX = 0;
    let downY = 0;
    let moved = false;
    canvas.addEventListener('pointerdown', event => {
      downX = event.clientX;
      downY = event.clientY;
      moved = false;
    }, true);
    canvas.addEventListener('pointermove', event => {
      if (Math.hypot(event.clientX - downX, event.clientY - downY) > 6) moved = true;
    }, true);
    canvas.addEventListener('click', event => {
      if (moved) return;
      const forwarded = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        clientX: event.clientX,
        clientY: event.clientY,
        button: event.button
      });
      baseCanvas.dispatchEvent(forwarded);
    }, true);
  };

  const observer = new MutationObserver(attach);
  observer.observe(viewport, { childList: true, subtree: true });
  attach();
})();
