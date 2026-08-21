(() => {
  const get = id => document.getElementById(id);
  const button = get('biological-state-add-evidence');
  if (!button) return;

  const spatial = () => {
    const node = window.selectedSpatialNode;
    if (node) return {
      spatial_id: node.spatial_id || node.id || node.regionId || 'hand',
      location_name: node.name || node.label || node.regionName || 'Wybrany region',
      location_level: node.level || 'site',
      parent_id: node.parent_id || node.parentId || null,
    };
    return {
      spatial_id: window.spatialEvidenceTarget || get('zone-label')?.textContent || 'hand',
      location_name: get('region-title')?.textContent || 'Wybrany region',
      location_level: 'site',
      parent_id: null,
    };
  };

  function openDialog() {
    if (get('biological-state-evidence-dialog')) {
      get('biological-state-evidence-dialog').showModal();
      return;
    }
    const dialog = document.createElement('dialog');
    dialog.id = 'biological-state-evidence-dialog';
    dialog.style.cssText = 'width:min(520px,calc(100vw - 28px));border:1px solid #d5dde2;border-radius:12px;padding:0;box-shadow:0 18px 60px rgba(24,38,48,.2)';
    dialog.innerHTML = `<form id="biological-state-evidence-form" style="padding:16px">
      <h3 style="margin:0 0 8px">Dodaj dane do interpretacji</h3>
      <p style="font-size:.85em;color:#66747e;margin:0 0 12px">Utworzy obserwację z jawnym evidence. Dopiero takie dane są liczone przez „Dane” w Interpretacji badawczej.</p>
      <label style="display:block;margin:8px 0 4px;font-size:.85em;font-weight:700">Poziom danych<select id="bse-level" style="display:block;width:100%;margin-top:4px;padding:7px"><option value="macro">Makro</option><option value="tissue">Tkanka</option><option value="cellular">Komórkowe</option><option value="molecular">Molekularne</option></select></label>
      <label style="display:block;margin:8px 0 4px;font-size:.85em;font-weight:700">Nazwa<input id="bse-name" required placeholder="np. Ocena obrazu Kciuka" style="display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:7px"></label>
      <label style="display:block;margin:8px 0 4px;font-size:.85em;font-weight:700">Wartość<input id="bse-value" placeholder="np. 333" style="display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:7px"></label>
      <label style="display:block;margin:8px 0 4px;font-size:.85em;font-weight:700">ID evidence<input id="bse-evidence" required placeholder="np. evidence-thumb-01" style="display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:7px"></label>
      <label style="display:block;margin:8px 0 4px;font-size:.85em;font-weight:700">Pewność evidence (0–1)<input id="bse-confidence" type="number" min="0" max="1" step="0.01" placeholder="0.8" style="display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:7px"></label>
      <label style="display:block;margin:8px 0 4px;font-size:.85em;font-weight:700">Notatka<textarea id="bse-notes" style="display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:7px;min-height:60px"></textarea></label>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px"><button type="button" id="bse-cancel">Anuluj</button><button type="submit" class="primary">Zapisz dane</button></div>
      <div id="bse-status" aria-live="polite" style="margin-top:8px;font-size:.8em"></div>
    </form>`;
    document.body.appendChild(dialog);
    get('bse-cancel').onclick = () => dialog.close();
    get('biological-state-evidence-form').onsubmit = async event => {
      event.preventDefault();
      const target = spatial();
      const payload = {
        subject_id: 'own_cohort',
        timepoint: 'T0',
        ...target,
        biological_level: get('bse-level').value,
        modality: 'manual-entry',
        name: get('bse-name').value.trim(),
        value: get('bse-value').value.trim() || null,
        source: 'manual-entry',
        notes: get('bse-notes').value.trim(),
        evidence_id: get('bse-evidence').value.trim(),
        evidence_confidence: get('bse-confidence').value === '' ? null : Number(get('bse-confidence').value),
        evidence_type: 'source',
        author: 'local-user',
      };
      const status = get('bse-status');
      status.textContent = 'Zapisywanie…';
      try {
        const response = await fetch('/api/observations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
        status.textContent = 'Zapisano. Odświeżam interpretację…';
        window.dispatchEvent(new CustomEvent('testhp:observation-updated', { detail: result }));
        if (window.biologicalStateUI?.refresh) await window.biologicalStateUI.refresh(window.lastSpatialDetail || target);
        setTimeout(() => dialog.close(), 300);
      } catch (error) {
        status.textContent = `Błąd: ${error.message}`;
      }
    };
    dialog.showModal();
  }

  button.addEventListener('click', openDialog);
})();
