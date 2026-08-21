(() => {
  'use strict';

  const clean = value => String(value ?? '').replace(/^\/+|\/+$/g, '');
  const labelFor = node => node?.label || document.querySelector('#spatial-node strong')?.textContent?.trim() || '?';
  const levelFor = node => String(node?.level || '').toLowerCase() || 'unknown';
  const selected = () => {
    const node = window.__testhpCanonicalSpatialSelection || window.selectedSpatialNode;
    const id = clean(node?.spatial_id || node?.id || window.spatialEvidenceTarget || 'hand');
    return {
      spatial_id: id || 'hand',
      label: labelFor(node),
      level: levelFor(node),
      path: [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean)
    };
  };

  let lastOpen = null;
  let lastValidation = null;
  let boundForms = new WeakSet();

  const debug = detail => {
    window.dispatchEvent(new CustomEvent('testhp:spatial-write-target-validation', { detail }));
  };

  function targetBox(form) {
    let box = form.querySelector('.ri-write-target-lock');
    if (box) return box;
    box = document.createElement('div');
    box.className = 'ri-write-target-lock';
    box.style.cssText = 'margin:10px 0;padding:9px;border:1px solid #9fc5b8;border-radius:8px;background:#eef8f4;font-size:9px;line-height:1.45;color:#31564a';
    const typeLabel = form.querySelector('label[for="ri-data-type"]');
    if (typeLabel) typeLabel.insertAdjacentElement('beforebegin', box);
    else form.prepend(box);
    return box;
  }

  function bindForm(form) {
    if (!form || boundForms.has(form)) return;
    boundForms.add(form);

    form.addEventListener('submit', event => {
      const now = selected();
      const locked = lastOpen?.spatial_id || now.spatial_id;
      const pass = clean(locked) === clean(now.spatial_id);
      lastValidation = {
        phase: 'submit',
        selected_spatial_id: now.spatial_id,
        selected_label: now.label,
        selected_level: now.level,
        locked_spatial_id: locked,
        locked_label: lastOpen?.label || now.label,
        pass,
        action: pass ? 'WRITE_ALLOWED' : 'WRITE_BLOCKED',
        at: new Date().toISOString()
      };
      debug(lastValidation);
      if (!pass) {
        event.preventDefault();
        event.stopImmediatePropagation();
        alert(`Nie można zapisać danych. Wybrany cel przestrzenny zmienił się z „${lastOpen?.label || locked}” na „${now.label}”. Wybierz ponownie „Dodaj dane” dla aktualnego celu.`);
        return;
      }
    }, true);
  }

  function refreshDialogTarget() {
    const form = document.getElementById('ri-data-form');
    if (!form) return;
    bindForm(form);
    const node = selected();
    const id = form.querySelector('#ri-data-id')?.value || '';
    const box = targetBox(form);
    const mode = id ? 'Edycja' : 'Nowe dane';
    box.innerHTML = `<strong>${mode} · cel przestrzenny</strong><br><span>${node.path.length ? node.path.join(' › ') : node.label}</span><br><code>${node.spatial_id}</code> · ${node.level}<br><small>Cel jest zablokowany na aktualnie wybranym elemencie. Nie można zapisać danych do rodzica, potomka ani rodzeństwa.</small>`;
  }

  function watchDialog() {
    const dialog = document.getElementById('ri-data-dialog');
    if (!dialog) return;
    const observer = new MutationObserver(refreshDialogTarget);
    observer.observe(dialog, { childList: true, subtree: true });
    refreshDialogTarget();
  }

  function bindOpeners() {
    document.querySelectorAll('.ri-data-tools button, [data-ri-edit]').forEach(button => {
      if (button.dataset.writeTargetBound) return;
      button.dataset.writeTargetBound = '1';
      button.addEventListener('click', () => {
        const node = selected();
        lastOpen = { ...node, at: new Date().toISOString() };
        debug({ phase: 'open', ...lastOpen, rule: 'EXACT_SELECTED_SPATIAL_ID_ONLY' });
        setTimeout(refreshDialogTarget, 0);
      }, true);
    });
  }

  const observer = new MutationObserver(() => {
    bindOpeners();
    watchDialog();
  });
  observer.observe(document.body, { childList: true, subtree: true });

  window.addEventListener('testhp:spatial-layer-changed', () => {
    lastOpen = null;
    bindOpeners();
  });

  window.addEventListener('testhp:spatial-selection-contract-updated', () => {
    bindOpeners();
    refreshDialogTarget();
  });

  window.spatialWriteTargetContract = {
    version: 'exact-selected-spatial-v1',
    get selected() { return selected(); },
    get lastOpen() { return lastOpen; },
    get lastValidation() { return lastValidation; },
    validate(target) { return clean(target) === clean(selected().spatial_id); }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { bindOpeners(); watchDialog(); }, { once: true });
  } else {
    bindOpeners();
    watchDialog();
  }
})();
