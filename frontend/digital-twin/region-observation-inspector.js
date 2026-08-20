(() => {
  const SUBJECT = 'own_cohort';
  const LEVELS = [
    ['macro', 'MACRO'],
    ['tissue', 'TKANKA'],
    ['cellular', 'KOMÓRKOWE'],
    ['molecular', 'MOLEKULARNE'],
  ];

  let target = { spatial_id: 'hand', location_name: 'Hand', path: ['Hand'] };
  let requestSerial = 0;

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  const pathText = () => (target.path || []).join(' > ');

  function getTargetFromDetail(detail = {}) {
    return {
      spatial_id: detail.spatial_id || detail.id || detail.region_id || 'hand',
      location_name: detail.target || detail.location_name || detail.name || 'Hand',
      path: detail.path || [detail.target || detail.location_name || detail.name || 'Hand'],
    };
  }

  function ensureStyles() {
    if (document.getElementById('roi-observation-styles')) return;
    const style = document.createElement('style');
    style.id = 'roi-observation-styles';
    style.textContent = `
      .roi-observation-panel{margin-top:12px;padding-top:11px;border-top:1px solid #e1e6ea}
      .roi-observation-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
      .roi-observation-head strong{font-size:9px;letter-spacing:.08em;color:#34424c}
      .roi-observation-head span{font-size:7px;color:#8a969f}
      .roi-observation-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-top:7px}
      .roi-observation-count{border:1px solid #e1e6ea;border-radius:7px;background:#fafbfc;padding:6px 5px;min-width:0}
      .roi-observation-count b{display:block;font-size:11px;color:#146b55;line-height:1}
      .roi-observation-count span{display:block;margin-top:3px;font-size:6px;color:#7d8991;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .roi-observation-list{display:grid;gap:5px;margin-top:7px}
      .roi-observation-card{border:1px solid #e1e6ea;border-radius:8px;background:#fafbfc;padding:7px}
      .roi-observation-card button{width:100%;border:0;background:transparent;text-align:left;padding:0;cursor:pointer}
      .roi-observation-title{font-size:8px;font-weight:800;color:#34424c}
      .roi-observation-meta{margin-top:3px;font-size:7px;color:#7d8991;line-height:1.4}
      .roi-observation-empty{padding:8px;border:1px dashed #d5dde2;border-radius:8px;color:#8a969f;font-size:8px;margin-top:7px}
      .roi-observation-dialog{width:min(500px,calc(100vw - 28px));border:1px solid #d5dde2;border-radius:12px;padding:0;box-shadow:0 18px 60px rgba(24,38,48,.2)}
      .roi-observation-dialog::backdrop{background:rgba(20,30,35,.28)}
      .roi-observation-detail{padding:15px}.roi-observation-detail h3{margin:0 0 4px;font-size:13px;color:#26343e}
      .roi-observation-detail .sub{margin:0 0 12px;color:#87929a;font-size:8px}
      .roi-observation-detail-grid{display:grid;gap:7px}.roi-observation-detail-row{display:grid;grid-template-columns:105px 1fr;gap:8px;font-size:8px}
      .roi-observation-detail-row b{color:#68757e}.roi-observation-detail-row span{color:#26343e;word-break:break-word}
      .roi-observation-detail pre{white-space:pre-wrap;margin:0;font:inherit}.roi-observation-close{display:flex;justify-content:flex-end;margin-top:12px}
      .roi-observation-close button{border:1px solid #d5dde2;background:#fff;border-radius:7px;padding:7px 10px;font-size:9px;font-weight:750;cursor:pointer}
    `;
    document.head.appendChild(style);
  }

  function ensurePanel() {
    const inspector = document.querySelector('.inspector');
    if (!inspector) return null;
    let panel = inspector.querySelector('.roi-observation-panel');
    if (panel) return panel;
    panel = document.createElement('section');
    panel.className = 'roi-observation-panel';
    panel.innerHTML = `
      <div class="roi-observation-head"><strong>OBSERWACJE REGIONU</strong><span class="roi-observation-context"></span></div>
      <div class="roi-observation-summary">
        ${LEVELS.map(([level, label]) => `<div class="roi-observation-count" data-roi-count="${level}"><b>0</b><span>${label}</span></div>`).join('')}
      </div>
      <div class="roi-observation-list"><div class="roi-observation-empty">Ładowanie obserwacji…</div></div>
    `;
    const actions = inspector.querySelector('.inspector-actions');
    (actions || inspector).before(panel);
    return panel;
  }

  function ensureDialog() {
    let dialog = document.getElementById('roi-observation-dialog');
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.id = 'roi-observation-dialog';
    dialog.className = 'roi-observation-dialog';
    dialog.innerHTML = `<div class="roi-observation-detail"><h3>Obserwacja</h3><p class="sub" id="roi-observation-subtitle"></p><div id="roi-observation-detail-content"></div><div class="roi-observation-close"><button type="button" id="roi-observation-close">Zamknij</button></div></div>`;
    document.body.appendChild(dialog);
    document.getElementById('roi-observation-close').onclick = () => dialog.close();
    return dialog;
  }

  async function fetchObservations() {
    const params = new URLSearchParams({ subject_id: SUBJECT, spatial_id: target.spatial_id, include_archived: 'false' });
    const response = await fetch(`/api/observations?${params.toString()}`);
    if (!response.ok) throw new Error('Nie udało się pobrać obserwacji regionu.');
    return (await response.json()).observations || [];
  }

  async function showDetail(id) {
    const response = await fetch(`/api/observations/${encodeURIComponent(id)}`);
    if (!response.ok) return;
    const { observation: item } = await response.json();
    const dialog = ensureDialog();
    const value = typeof item.value === 'string' ? item.value : JSON.stringify(item.value ?? null, null, 2);
    const audit = (item.audit || []).map((entry) => `v${escapeHtml(entry.version)} · ${escapeHtml(entry.action)} · ${escapeHtml(entry.at)}${entry.changed_fields ? ` · ${escapeHtml(entry.changed_fields.join(', '))}` : ''}`).join('<br>') || 'Brak historii.';
    document.getElementById('roi-observation-subtitle').textContent = `${item.location_name || target.location_name} · ${item.timepoint || ''}`;
    document.getElementById('roi-observation-detail-content').innerHTML = `
      <div class="roi-observation-detail-grid">
        <div class="roi-observation-detail-row"><b>Poziom</b><span>${escapeHtml(item.biological_level)}</span></div>
        <div class="roi-observation-detail-row"><b>Nazwa</b><span>${escapeHtml(item.name)}</span></div>
        <div class="roi-observation-detail-row"><b>Wartość</b><span><pre>${escapeHtml(value)}</pre></span></div>
        <div class="roi-observation-detail-row"><b>Modality</b><span>${escapeHtml(item.modality)}</span></div>
        <div class="roi-observation-detail-row"><b>Źródło</b><span>${escapeHtml(item.source || '—')}</span></div>
        <div class="roi-observation-detail-row"><b>Region</b><span>${escapeHtml(item.spatial_id || '—')}</span></div>
        <div class="roi-observation-detail-row"><b>Subject</b><span>${escapeHtml(item.subject_id || '—')}</span></div>
        <div class="roi-observation-detail-row"><b>Timepoint</b><span>${escapeHtml(item.timepoint || '—')}</span></div>
        <div class="roi-observation-detail-row"><b>Evidence</b><span>${escapeHtml(item.evidence_id || 'brak jawnego powiązania')}</span></div>
        <div class="roi-observation-detail-row"><b>Wersja</b><span>v${escapeHtml(item.version || 1)}</span></div>
        <div class="roi-observation-detail-row"><b>Obserwowano</b><span>${escapeHtml(item.observed_at || '—')}</span></div>
        <div class="roi-observation-detail-row"><b>Notatka</b><span>${escapeHtml(item.notes || '—')}</span></div>
        <div class="roi-observation-detail-row"><b>Historia</b><span>${audit}</span></div>
      </div>`;
    dialog.showModal();
  }

  async function render() {
    ensureStyles();
    const panel = ensurePanel();
    if (!panel) return;
    panel.querySelector('.roi-observation-context').textContent = pathText();
    const serial = ++requestSerial;
    try {
      const items = await fetchObservations();
      if (serial !== requestSerial) return;
      LEVELS.forEach(([level]) => {
        const count = items.filter((item) => item.biological_level === level).length;
        const element = panel.querySelector(`[data-roi-count="${level}"] b`);
        if (element) element.textContent = count;
      });
      const list = panel.querySelector('.roi-observation-list');
      if (!items.length) {
        list.innerHTML = '<div class="roi-observation-empty">Brak jawnie zarejestrowanych obserwacji dla tego regionu.</div>';
        return;
      }
      list.innerHTML = items.map((item) => `
        <article class="roi-observation-card">
          <button type="button" data-roi-detail="${escapeHtml(item.id)}">
            <div class="roi-observation-title">${escapeHtml(item.name)}</div>
            <div class="roi-observation-meta">${escapeHtml(item.biological_level)} · ${escapeHtml(item.timepoint)} · ${escapeHtml(item.modality || 'manual-entry')} · v${escapeHtml(item.version || 1)}</div>
          </button>
        </article>`).join('');
      list.querySelectorAll('[data-roi-detail]').forEach((button) => {
        button.onclick = () => showDetail(button.dataset.roiDetail);
      });
    } catch (error) {
      panel.querySelector('.roi-observation-list').innerHTML = `<div class="roi-observation-empty">${escapeHtml(error.message)}</div>`;
    }
  }

  window.addEventListener('testhp:spatial-layer-changed', (event) => {
    target = getTargetFromDetail(event.detail || {});
    render();
  });
  window.addEventListener('testhp:observation-changed', render);
  window.addEventListener('testhp:region-data-changed', render);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render, { once: true });
  else render();
})();
