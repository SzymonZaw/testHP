(() => {
  const esc = value => String(value ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const target = () => window.testhpSpatialContract?.getTarget?.() || window.selectedSpatialNode || window.spatialEvidenceTarget || null;
  const targetId = t => String(t?.spatial_id || t?.spatialId || t?.id || t || '').replace(/^\/+|\/+$/g, '').toLowerCase();

  function addAction() {
    const shell = document.getElementById('hand-surface-unified');
    if (!shell || document.getElementById('hand-photo-source-add')) return;

    const material = shell.querySelector('[data-hsu-section="material"]');
    if (!material) return;

    // In the current unified UI "Zdjęcia / źródła" is a sub-navigation tab,
    // not a heading. Mount the action directly below that navigation so it
    // remains visible regardless of which legacy source panel is rendered.
    const subnav = material.querySelector('.hsu-subnav');
    const sourceTab = subnav?.querySelector('[data-hsu-under="evidence"]');
    if (!subnav || !sourceTab) return;

    const t = target();
    const action = document.createElement('div');
    action.id = 'hand-photo-source-add';
    action.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:10px 0 12px;padding:11px 12px;border:1px solid var(--border,#d8dee8);border-radius:10px;background:rgba(79,111,143,.04);';
    action.innerHTML = `<div><strong>Dodaj materiał fotograficzny</strong><div style="font-size:12px;color:#667085;margin-top:3px">Zdjęcia zostaną przypisane do aktualnie wybranego celu: <code>${esc(targetId(t) || 'brak')}</code>.</div></div><button id="hand-photo-source-add-button" type="button" class="primary" ${targetId(t) ? '' : 'disabled'}>＋ Dodaj zdjęcia</button>`;

    subnav.insertAdjacentElement('afterend', action);

    action.querySelector('button')?.addEventListener('click', () => {
      const input = document.getElementById('p3r-clean-files');
      if (input) {
        input.click();
        return;
      }
      window.dispatchEvent(new CustomEvent('testhp:hand-photo-source-add-request', {
        detail: { spatialTarget: targetId(target()), target: target() }
      }));
    });
  }

  let scheduled = false;
  const schedule = () => {
    if (scheduled) return;
    scheduled = true;
    setTimeout(() => { scheduled = false; addAction(); }, 0);
  };

  ['testhp:spatial-contract-changed','testhp:spatial-layer-changed','testhp:inspector-scope-updated'].forEach(event => window.addEventListener(event, schedule));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule, { once: true });
  else schedule();
  new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
})();