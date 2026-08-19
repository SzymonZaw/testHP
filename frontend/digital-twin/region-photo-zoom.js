(() => {
  const STYLE_ID = 'ri-photo-zoom-style';
  const DIALOG_ID = 'ri-photo-zoom-dialog';

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .ri-photo-zoom-trigger{display:block;width:100%;padding:0;border:0;background:transparent;cursor:zoom-in}
      .ri-photo-zoom-trigger:focus-visible{outline:2px solid #146b55;outline-offset:-2px}
      .ri-photo-zoom-dialog{width:min(92vw,1100px);height:min(92vh,850px);max-width:92vw;max-height:92vh;padding:0;border:0;border-radius:12px;background:#101619;box-shadow:0 24px 90px rgba(0,0,0,.45);overflow:hidden}
      .ri-photo-zoom-dialog::backdrop{background:rgba(8,13,16,.72)}
      .ri-photo-zoom-stage{position:relative;width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden;touch-action:none}
      .ri-photo-zoom-image{max-width:100%;max-height:100%;object-fit:contain;transform-origin:center;user-select:none;cursor:grab;transition:transform .08s ease-out}
      .ri-photo-zoom-image.dragging{cursor:grabbing;transition:none}
      .ri-photo-zoom-toolbar{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);display:flex;align-items:center;gap:5px;padding:6px;border-radius:10px;background:rgba(16,22,25,.86);backdrop-filter:blur(8px)}
      .ri-photo-zoom-toolbar button{border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.08);color:#fff;border-radius:7px;padding:6px 9px;min-width:34px;font-size:12px;font-weight:750;cursor:pointer}
      .ri-photo-zoom-toolbar button:hover{background:rgba(255,255,255,.16)}
      .ri-photo-zoom-title{position:absolute;left:14px;top:12px;max-width:calc(100% - 28px);padding:6px 9px;border-radius:8px;background:rgba(16,22,25,.76);color:#fff;font-size:10px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .ri-photo-zoom-close{position:absolute;right:12px;top:10px;border:0;background:rgba(16,22,25,.76);color:#fff;border-radius:50%;width:32px;height:32px;font-size:18px;cursor:pointer;z-index:2}
      .ri-photo-zoom-close:hover{background:rgba(16,22,25,.95)}
    `;
    document.head.appendChild(style);
  }

  function ensureDialog() {
    let dialog = document.getElementById(DIALOG_ID);
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.id = DIALOG_ID;
    dialog.className = 'ri-photo-zoom-dialog';
    dialog.innerHTML = `
      <div class="ri-photo-zoom-stage">
        <button type="button" class="ri-photo-zoom-close" aria-label="Zamknij">×</button>
        <div class="ri-photo-zoom-title"></div>
        <img class="ri-photo-zoom-image" alt="">
        <div class="ri-photo-zoom-toolbar" aria-label="Narzędzia powiększania">
          <button type="button" data-zoom="out" aria-label="Pomniejsz">−</button>
          <button type="button" data-zoom="reset">100%</button>
          <button type="button" data-zoom="in" aria-label="Powiększ">＋</button>
        </div>
      </div>`;
    document.body.appendChild(dialog);

    const img = dialog.querySelector('.ri-photo-zoom-image');
    const title = dialog.querySelector('.ri-photo-zoom-title');
    let scale = 1, x = 0, y = 0, dragging = false, startX = 0, startY = 0;

    const apply = () => { img.style.transform = `translate(${x}px, ${y}px) scale(${scale})`; };
    const reset = () => { scale = 1; x = 0; y = 0; apply(); };
    const setScale = next => { scale = Math.min(5, Math.max(1, next)); if (scale === 1) { x = 0; y = 0; } apply(); };

    dialog.querySelector('[data-zoom="out"]').onclick = () => setScale(scale - .25);
    dialog.querySelector('[data-zoom="in"]').onclick = () => setScale(scale + .25);
    dialog.querySelector('[data-zoom="reset"]').onclick = reset;
    dialog.querySelector('.ri-photo-zoom-close').onclick = () => dialog.close();
    dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener('wheel', e => { e.preventDefault(); setScale(scale + (e.deltaY < 0 ? .25 : -.25)); }, {passive:false});
    img.addEventListener('pointerdown', e => { if (scale <= 1) return; dragging = true; img.classList.add('dragging'); startX = e.clientX - x; startY = e.clientY - y; img.setPointerCapture?.(e.pointerId); });
    img.addEventListener('pointermove', e => { if (!dragging) return; x = e.clientX - startX; y = e.clientY - startY; apply(); });
    img.addEventListener('pointerup', e => { dragging = false; img.classList.remove('dragging'); img.releasePointerCapture?.(e.pointerId); });
    img.addEventListener('pointercancel', () => { dragging = false; img.classList.remove('dragging'); });
    dialog.addEventListener('close', reset);

    dialog._openPhoto = (src, name) => { img.src = src; img.alt = name || 'Zdjęcie regionu'; title.textContent = name || 'Zdjęcie regionu'; reset(); dialog.showModal(); };
    return dialog;
  }

  function bindGallery() {
    const gallery = document.getElementById('ri-photo-gallery');
    if (!gallery || gallery.dataset.zoomBound === '1') return;
    gallery.dataset.zoomBound = '1';
    gallery.addEventListener('click', e => {
      const button = e.target.closest('[data-photo-zoom]');
      if (!button) return;
      const img = button.querySelector('img');
      if (!img) return;
      e.preventDefault();
      ensureDialog()._openPhoto(img.src, img.alt);
    });
  }

  function enhanceCards() {
    document.querySelectorAll('#ri-photo-gallery .ri-photo-card').forEach(card => {
      const img = card.querySelector('img');
      if (!img || card.querySelector('[data-photo-zoom]')) return;
      const trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'ri-photo-zoom-trigger';
      trigger.dataset.photoZoom = '1';
      trigger.title = 'Powiększ zdjęcie';
      img.replaceWith(trigger);
      trigger.appendChild(img);
    });
    bindGallery();
  }

  function observeGallery() {
    enhanceCards();
    const observer = new MutationObserver(enhanceCards);
    observer.observe(document.body, {childList:true, subtree:true});
  }

  function init() {
    ensureStyles();
    ensureDialog();
    observeGallery();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
