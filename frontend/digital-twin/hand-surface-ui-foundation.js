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

  const ensurePhotoAction = () => {
    const shell = document.getElementById('hand-surface-unified');
    const material = shell?.querySelector('[data-hsu-section="material"]');
    if (!material || material.querySelector('#hand-surface-add-photo-action')) return;

    const subnav = material.querySelector('.hsu-subnav');
    if (!subnav) return;

    const action = document.createElement('div');
    action.id = 'hand-surface-add-photo-action';
    action.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:10px 0 12px;padding:10px 12px;border:1px solid var(--border,#d8dee8);border-radius:10px;background:var(--panel,#fff)';
    action.innerHTML = '<div><strong style="display:block;font-size:13px">Zdjęcia / źródła</strong><span style="font-size:12px;color:#667085">Dodaj zdjęcia dla aktualnie wybranego celu przestrzennego.</span></div><button type="button" id="hand-surface-add-photo-btn" class="primary">＋ Dodaj zdjęcia</button>';
    subnav.insertAdjacentElement('afterend', action);

    action.querySelector('#hand-surface-add-photo-btn').addEventListener('click', () => {
      const input = document.getElementById('p3r-clean-files');
      if (input) {
        input.click();
        return;
      }
      window.dispatchEvent(new CustomEvent('testhp:open-hand-photo-upload'));
    });
  };

  const hideLegacySurfacePanels = () => {
    const shell = document.getElementById('hand-surface-unified');
    if (!shell) return;
    ['hand-surface-studio','hand-surface-stages-20-22'].forEach(id => {
      const el = document.getElementById(id);
      if (el && !shell.contains(el)) el.style.display = 'none';
    });
  };

  const run = () => {
    movePhotoPanel();
    hideLegacySurfacePanels();
    ensurePhotoAction();
  };
  const schedule = () => requestAnimationFrame(run);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:spatial-contract-changed', schedule);
  window.addEventListener('testhp:evidence-attached', schedule);
  const observer = new MutationObserver(schedule);
  if (document.body) observer.observe(document.body, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true }); else run();
})();
