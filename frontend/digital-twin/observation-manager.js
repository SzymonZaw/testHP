(() => {
  const SUBJECT = 'own_cohort';
  const LEVELS = [
    ['macro', 'Macro'],
    ['tissue', 'Tissue'],
    ['cellular', 'Cellular'],
    ['molecular', 'Molecular'],
  ];
  const TIMEPOINTS = ['all', 'T0', 'T1', 'T2', 'T3'];
  let target = { spatial_id: 'hand', path: ['Hand'], location_name: 'Hand' };
  let timepointFilter = 'all';
  let selectedId = null;

  const root = document.getElementById('observation-manager');
  if (!root) return;

  const style = document.createElement('style');
  style.textContent = `
    .om-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.om-head h2{margin:0;color:#26343e;font-size:17px}.om-context{margin:4px 0 0;color:#7b8992;font-size:9px}.om-add{border:0;border-radius:8px;background:#146b55;color:#fff;padding:8px 11px;font-size:9px;font-weight:800;cursor:pointer}.om-tabs{display:flex;gap:5px;flex-wrap:wrap;margin:12px 0}.om-tab{border:1px solid #d5dde2;background:#fff;color:#68757e;border-radius:7px;padding:5px 8px;font-size:8px;font-weight:750;cursor:pointer}.om-tab.active{background:#e9f4f0;border-color:#9fc5b8;color:#146b55}.om-list{display:grid;gap:7px}.om-card{border:1px solid #e1e6ea;border-radius:9px;background:#fafbfc;padding:9px}.om-card-head{display:flex;justify-content:space-between;gap:8px}.om-title{font-size:10px;font-weight:800;color:#34424c}.om-badge{font-size:7px;font-weight:800;color:#146b55;background:#e9f4f0;border-radius:5px;padding:3px 5px;white-space:nowrap}.om-meta{margin-top:4px;color:#7d8991;font-size:8px;line-height:1.5}.om-actions{display:flex;gap:5px;margin-top:7px}.om-actions button{flex:1;border:1px solid #d5dde2;background:#fff;color:#53616c;border-radius:7px;padding:5px;font-size:8px;font-weight:750;cursor:pointer}.om-empty{padding:12px;border:1px dashed #d5dde2;border-radius:8px;color:#8a969f;font-size:9px}.om-dialog{width:min(520px,calc(100vw - 28px));border:1px solid #d5dde2;border-radius:12px;padding:0;box-shadow:0 18px 60px rgba(24,38,48,.2)}.om-dialog::backdrop{background:rgba(20,30,35,.28)}.om-form{padding:16px}.om-form h3{margin:0 0 4px;font-size:14px;color:#26343e}.om-form .om-subtitle{margin:0 0 12px;color:#87929a;font-size:8px}.om-form label{display:block;margin:8px 0 4px;font-size:8px;font-weight:750;color:#53616c}.om-form input,.om-form select,.om-form textarea{box-sizing:border-box;width:100%;padding:8px;border:1px solid #d5dde2;border-radius:7px;background:#fff;font-size:9px}.om-form textarea{min-height:70px;resize:vertical}.om-form-actions{display:flex;justify-content:flex-end;gap:6px;margin-top:13px}.om-form-actions button{border:1px solid #d5dde2;background:#fff;border-radius:7px;padding:7px 10px;font-size:9px;font-weight:750;cursor:pointer}.om-form-actions .primary{background:#146b55;border-color:#146b55;color:#fff}.om-detail{display:grid;gap:8px}.om-detail-row{display:grid;grid-template-columns:120px 1fr;gap:8px;font-size:9px}.om-detail-row b{color:#68757e}.om-detail-row span{color:#26343e;word-break:break-word}.om-history{margin-top:10px;padding-top:8px;border-top:1px solid #e1e6ea}.om-history strong{font-size:9px}.om-history-item{font-size:8px;color:#7d8991;margin-top:5px}
  `;
  document.head.appendChild(style);

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function currentPathText() {
    return (target.path || []).join(' > ');
  }

  function ensureDialog() {
    let dialog = document.getElementById('om-dialog');
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.id = 'om-dialog';
    dialog.className = 'om-dialog';
    dialog.innerHTML = `<form class="om-form" id="om-form"><h3 id="om-form-title">Dodaj obserwację biologiczną</h3><p class="om-subtitle" id="om-form-subtitle"></p><input id="om-id" type="hidden"><label>Poziom biologiczny</label><select id="om-level">${LEVELS.map(([v,l]) => `<option value="${v}">${l}</option>`).join('')}</select><label>Modality / metoda</label><input id="om-modality" value="manual-entry" placeholder="np. microscopy"><label>Nazwa obserwacji</label><input id="om-name" required placeholder="np. Cell density"><label>Wartość</label><textarea id="om-value" placeholder='np. 33 albo {"count":33,"unit":"cells/mm²"}'></textarea><label>Źródło</label><input id="om-source" value="manual-entry" placeholder="np. microscopy-field-A"><label>Data obserwacji</label><input id="om-observed-at" type="datetime-local"><label>Notatka</label><textarea id="om-notes" placeholder="Kontekst, metoda, ograniczenia…"></textarea><div class="om-form-actions"><button type="button" id="om-cancel">Anuluj</button><button type="submit" class="primary">Zapisz obserwację</button></div></form>`;
    document.body.appendChild(dialog);
    document.getElementById('om-cancel').onclick = () => dialog.close();
    document.getElementById('om-form').onsubmit = saveObservation;
    return dialog;
  }

  function ensureDetailDialog() {
    let dialog = document.getElementById('om-detail-dialog');
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.id = 'om-detail-dialog';
    dialog.className = 'om-dialog';
    dialog.innerHTML = `<div class="om-form"><h3>Szczegóły obserwacji</h3><p class="om-subtitle" id="om-detail-subtitle"></p><div id="om-detail-content"></div><div class="om-form-actions"><button type="button" id="om-detail-close">Zamknij</button></div></div>`;
    document.body.appendChild(dialog);
    document.getElementById('om-detail-close').onclick = () => dialog.close();
    return dialog;
  }

  async function load() {
    const params = new URLSearchParams({subject_id: SUBJECT});
    if (timepointFilter !== 'all') params.set('timepoint', timepointFilter);
    if (target.spatial_id) params.set('spatial_id', target.spatial_id);
    const response = await fetch(`/api/observations?${params}`);
    if (!response.ok) throw new Error('Nie udało się pobrać obserwacji.');
    return (await response.json()).observations || [];
  }

  async function render() {
    root.querySelector('.om-context').textContent = `· ${currentPathText()}`;
    const list = root.querySelector('.om-list');
    list.innerHTML = '<div class="om-empty">Ładowanie obserwacji…</div>';
    try {
      const items = await load();
      if (!items.length) {
        list.innerHTML = '<div class="om-empty">Brak jawnie zarejestrowanych obserwacji dla tego celu przestrzennego.</div>';
        return;
      }
      list.innerHTML = items.map(item => `<article class="om-card"><div class="om-card-head"><span class="om-title">${escapeHtml(item.name)}</span><span class="om-badge">${escapeHtml(item.biological_level)} · ${escapeHtml(item.timepoint)}</span></div><div class="om-meta"><b>${escapeHtml(item.modality)}</b> · ${escapeHtml(item.source || 'manual-entry')} · ${escapeHtml(item.observed_at || '')}${item.version ? ` · v${escapeHtml(item.version)}` : ''}</div><div class="om-actions"><button type="button" data-detail="${escapeHtml(item.id)}">Szczegóły</button><button type="button" data-edit="${escapeHtml(item.id)}">Edytuj</button></div></article>`).join('');
      list.querySelectorAll('[data-detail]').forEach(button => button.onclick = () => showDetail(button.dataset.detail));
      list.querySelectorAll('[data-edit]').forEach(button => button.onclick = () => openEditor(button.dataset.edit));
    } catch (error) {
      list.innerHTML = `<div class="om-empty">${escapeHtml(error.message)}</div>`;
    }
  }

  function openEditor(id = null) {
    selectedId = id;
    const dialog = ensureDialog();
    document.getElementById('om-form-title').textContent = id ? 'Edytuj obserwację' : 'Dodaj obserwację biologiczną';
    document.getElementById('om-form-subtitle').textContent = currentPathText();
    document.getElementById('om-id').value = id || '';
    document.getElementById('om-level').value = 'cellular';
    document.getElementById('om-modality').value = 'manual-entry';
    document.getElementById('om-name').value = '';
    document.getElementById('om-value').value = '';
    document.getElementById('om-source').value = 'manual-entry';
    document.getElementById('om-observed-at').value = new Date().toISOString().slice(0,16);
    document.getElementById('om-notes').value = '';
    if (id) {
      fetch(`/api/observations/${encodeURIComponent(id)}`).then(r => r.json()).then(({observation:item}) => {
        document.getElementById('om-level').value = item.biological_level || 'cellular';
        document.getElementById('om-modality').value = item.modality || 'manual-entry';
        document.getElementById('om-name').value = item.name || '';
        document.getElementById('om-value').value = typeof item.value === 'string' ? item.value : JSON.stringify(item.value ?? '', null, 2);
        document.getElementById('om-source').value = item.source || 'manual-entry';
        document.getElementById('om-notes').value = item.notes || '';
        document.getElementById('om-observed-at').value = String(item.observed_at || '').slice(0,16);
      });
    }
    dialog.showModal();
  }

  function parseValue(raw) {
    const text = raw.trim();
    if (!text) return null;
    try { return JSON.parse(text); } catch { return text; }
  }

  async function saveObservation(event) {
    event.preventDefault();
    const id = document.getElementById('om-id').value;
    const payload = {
      biological_level: document.getElementById('om-level').value,
      modality: document.getElementById('om-modality').value.trim() || 'manual-entry',
      name: document.getElementById('om-name').value.trim(),
      value: parseValue(document.getElementById('om-value').value),
      source: document.getElementById('om-source').value.trim() || 'manual-entry',
      observed_at: document.getElementById('om-observed-at').value ? new Date(document.getElementById('om-observed-at').value).toISOString() : new Date().toISOString(),
      notes: document.getElementById('om-notes').value.trim(),
    };
    if (!payload.name) return;
    const url = id ? `/api/observations/${encodeURIComponent(id)}` : '/api/observations';
    const method = id ? 'PATCH' : 'POST';
    const body = id ? payload : {...payload, subject_id: SUBJECT, timepoint: timepointFilter === 'all' ? 'T0' : timepointFilter, spatial_id: target.spatial_id, location_name: target.location_name, location_level: 'site', parent_id: target.spatial_id.includes('/') ? target.spatial_id.split('/').slice(0,-1).join('/') : null};
    const response = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if (!response.ok) { alert((await response.json()).detail || 'Nie udało się zapisać obserwacji.'); return; }
    ensureDialog().close();
    await render();
  }

  async function showDetail(id) {
    const response = await fetch(`/api/observations/${encodeURIComponent(id)}`);
    if (!response.ok) return;
    const {observation:item} = await response.json();
    const dialog = ensureDetailDialog();
    document.getElementById('om-detail-subtitle').textContent = `${item.location_name} · ${item.timepoint}`;
    const value = typeof item.value === 'string' ? item.value : JSON.stringify(item.value ?? null, null, 2);
    const audit = (item.audit || []).map(x => `<div class="om-history-item">v${escapeHtml(x.version)} · ${escapeHtml(x.action)} · ${escapeHtml(x.at)}${x.changed_fields ? ` · ${escapeHtml(x.changed_fields.join(', '))}` : ''}</div>`).join('');
    document.getElementById('om-detail-content').innerHTML = `<div class="om-detail"><div class="om-detail-row"><b>Poziom</b><span>${escapeHtml(item.biological_level)}</span></div><div class="om-detail-row"><b>Modality</b><span>${escapeHtml(item.modality)}</span></div><div class="om-detail-row"><b>Nazwa</b><span>${escapeHtml(item.name)}</span></div><div class="om-detail-row"><b>Wartość</b><span><pre>${escapeHtml(value)}</pre></span></div><div class="om-detail-row"><b>Źródło</b><span>${escapeHtml(item.source)}</span></div><div class="om-detail-row"><b>Evidence</b><span>${escapeHtml(item.evidence_id || 'brak jawnego powiązania')}</span></div><div class="om-detail-row"><b>Obserwowano</b><span>${escapeHtml(item.observed_at)}</span></div><div class="om-detail-row"><b>Wersja</b><span>${escapeHtml(item.version)}</span></div><div class="om-detail-row"><b>Notatka</b><span>${escapeHtml(item.notes || '—')}</span></div></div><div class="om-history"><strong>Historia zmian</strong>${audit || '<div class="om-history-item">Brak historii.</div>'}</div>`;
    dialog.showModal();
  }

  root.querySelectorAll('[data-timepoint]').forEach(button => button.onclick = () => {
    timepointFilter = button.dataset.timepoint;
    root.querySelectorAll('[data-timepoint]').forEach(x => x.classList.toggle('active', x === button));
    render();
  });
  root.querySelector('.om-add').onclick = () => openEditor();

  window.addEventListener('testhp:spatial-layer-changed', event => {
    const detail = event.detail || {};
    target = {
      spatial_id: detail.spatial_id || detail.id || 'hand',
      path: detail.path || [detail.target || 'Hand'],
      location_name: detail.target || 'Hand',
    };
    render();
  });
  window.addEventListener('testhp:observation-changed', render);
  render();
})();
