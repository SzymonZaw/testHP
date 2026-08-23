(() => {
  const movePhotoPanel = () => {
    const shell = document.getElementById('hand-surface-unified');
    const material = shell?.querySelector('[data-hsu-section="material"]');
    const photo = document.getElementById('photo-3d-reconstruction');
    if (!shell || !material || !photo) return false;
    if (photo.parentElement !== material) material.appendChild(photo);
    photo.querySelector('.panel-title')?.remove();
    photo.style.marginTop = '0';
    return true;
  };
  const hideLegacySurfacePanels = () => {
    const shell = document.getElementById('hand-surface-unified');
    if (!shell) return;
    ['hand-surface-studio','hand-surface-stages-20-22'].forEach(id => {
      const el = document.getElementById(id);
      if (el && !shell.contains(el)) el.style.display = 'none';
    });
  };
  const run = () => { movePhotoPanel(); hideLegacySurfacePanels(); };
  const schedule = () => requestAnimationFrame(run);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:spatial-contract-changed', schedule);
  const observer = new MutationObserver(schedule);
  if (document.body) observer.observe(document.body, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true }); else run();
})();
