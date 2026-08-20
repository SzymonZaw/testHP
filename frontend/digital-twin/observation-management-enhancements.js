(() => {
  const SUBJECT = 'own_cohort';
  const LEVELS = [['', 'Wszystkie poziomy'], ['macro', 'Macro'], ['tissue', 'Tissue'], ['cellular', 'Cellular'], ['molecular', 'Molecular']];
  let allItems = [];
  let search = '';
  let level = '';
  let timepoint = 'all';
  let sort = 'observed_at_desc';

  const root = document.getElementById('observation-manager');
  if (!root) return;
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function addStyles() {
    if (document.getElementById('om-admin-styles')) return;
    const style = document.createElement('style'); style.id = 'om-admin-styles';
    style.textContent = `
      .om-admin-tools{display:grid;grid-template-columns:minmax(180px,2fr) repeat(2,minmax(120px,1fr)) minmax(150px,1fr);gap:6px;margin:10px 0}
      .om-admin-tools input,.om-admin-tools select{box-sizing:border-box;width:100%;padding:7px;border:1px solid #d5dde2;border-radius:7px;background:#fff;font-size:8px;color:#34424c}
      .om-admin-table-wrap{overflow:auto;border:1px solid #e1e6ea;border-radius:9px;background:#fff}.om-admin-table{width:100%;border-collapse:collapse;min-width:700px}
      .om-admin-table th{padding:7px;text-align:left;font-size:7px;letter-spacing:.05em;color:#7b8992;background:#f5f7f8;border-bottom:1px solid #e1e6ea}.om-admin-table td{padding:7px;border-bottom:1px solid #edf0f2;font-size:8px;color:#53616c;vertical-align:top}.om-admin-table tr:last-child td{border-bottom:0}.om-admin-table .primary-text{font-weight:800;color:#34424c}.om-admin-table .muted{font-size:7px;color:#8a969f}.om-admin-actions{display:flex;gap:4px}.om-admin-actions button{border:1px solid #d5dde2;background:#fff;color:#53616c;border-radius:6px;padding:4px 6px;font-size:7px;font-weight:750;cursor:pointer}.om-admin-actions button:hover{border-color:#9fc5b8;background:#e9f4f0;color:#146b55}
      .om-admin-empty{padding:12px;border:1px dashed #d5dde2;border-radius:8px;color:#8a969f;font-size:9px}.om-admin-diff{display:grid;gap:6px;margin-top:10px}.om-admin-diff-row{border:1px solid #e1e6ea;border-radius:7px;padding:7px;background:#fafbfc;font-size:8px}.om-admin-diff-row b{display:block;color:#34424c;margin-bottom:3px}.om-admin-diff-row span{display:block;color:#7d8991}.om-admin-diff-row .after{color:#146b55;margin-top:2px}
      @media(max-width:800px){.om-admin-tools{grid-template-columns:1fr 1fr}.om-admin-tools input{grid-column:1/-1}}
    `; document.head.appendChild(style);
  }

  function ensureTools() {
    if (root.querySelector('.om-admin-tools')) return;
    const tabs = root.querySelector('.om-tabs');
    const tools = document.createElement('div'); tools.className = 'om-admin-tools';
    tools.innerHTML = `<input id="om-admin-search" type="search" placeholder="Szukaj: nazwa, region, modality, subject…"><select id="om-admin-level">${LEVELS.map(([v,l]) => `<option value="${v}">${l}</option>`).join('')}</select><select id="om-admin-time"><option value="all">Wszystkie timepointy</option><option>T0</option><option>T1</option><option>T2</option><option>T3</option></select><select id="om-admin-sort"><option value="observed_at_desc">Najnowsze</option><option value="observed_at_asc">Najstarsze</option><option value="region_asc">Region A–Z</option><option value="level_asc">Typ A–Z</option><option value="version_desc">Wersja malejąco</option><option value="author_asc">Autor A–Z</option></select>`;
    tabs.after(tools);
    tools.querySelector('#om-admin-search').oninput = e => { search = e.target.value.trim().toLowerCase(); render(); };
    tools.querySelector('#om-admin-level').onchange = e => { level = e.target.value; render(); };
    tools.querySelector('#om-admin-time').onchange = e => { timepoint = e.target.value; render(); };
    tools.querySelector('#om-admin-sort').onchange = e => { sort = e.target.value; render(); };
  }

  async function load() {
    const response = await fetch(`/api/observations?subject_id=${encodeURIComponent(SUBJECT)}&include_archived=false`);
    if (!response.ok) throw new Error('Nie udało się pobrać rejestru obserwacji.');
    allItems = (await response.json()).observations || [];
    render();
  }

  function filtered() {
    let items = allItems.filter(item => (!level || item.biological_level === level) && (timepoint === 'all' || item.timepoint === timepoint));
    if (search) items = items.filter(item => [item.name,item.spatial_id,item.location_name,item.modality,item.subject_id,item.source,item.author].some(v => String(v ?? '').toLowerCase().includes(search)));
    return items.sort((a,b) => {
      if (sort === 'region_asc') return String(a.spatial_id).localeCompare(String(b.spatial_id));
      if (sort === 'level_asc') return String(a.biological_level).localeCompare(String(b.biological_level));
      if (sort === 'version_desc') return Number(b.version||1) - Number(a.version||1);
      if (sort === 'author_asc') return String(a.author||'').localeCompare(String(b.author||''));
      const diff = new Date(a.observed_at||0) - new Date(b.observed_at||0); return sort === 'observed_at_asc' ? diff : -diff;
    });
  }

  function findLegacyButton(id, action) {
    return root.querySelector(`.om-list [data-${action}="${CSS.escape(id)}"]`);
  }

  function render() {
    addStyles(); ensureTools();
    const oldList = root.querySelector('.om-list');
    if (oldList) oldList.style.display = 'none';
    let host = root.querySelector('.om-admin-list');
    if (!host) { host = document.createElement('div'); host.className = 'om-admin-list'; root.appendChild(host); }
    const items = filtered();
    if (!items.length) { host.innerHTML = '<div class="om-admin-empty">Brak obserwacji spełniających wybrane kryteria.</div>'; return; }
    host.innerHTML = `<div class="om-admin-table-wrap"><table class="om-admin-table"><thead><tr><th>Obserwacja</th><th>Region</th><th>Typ</th><th>Czas</th><th>Modality</th><th>Autor / wersja</th><th></th></tr></thead><tbody>${items.map(item => `<tr><td><span class="primary-text">${esc(item.name)}</span><br><span class="muted">${esc(item.value == null ? '—' : typeof item.value === 'object' ? JSON.stringify(item.value) : item.value)}</span></td><td>${esc(item.location_name || item.spatial_id)}<br><span class="muted">${esc(item.spatial_id)}</span></td><td>${esc(item.biological_level)}</td><td>${esc(item.timepoint)}<br><span class="muted">${esc(item.observed_at)}</span></td><td>${esc(item.modality)}</td><td>${esc(item.author || 'local-user')}<br><span class="muted">v${esc(item.version || 1)}</span></td><td><div class="om-admin-actions"><button type="button" data-admin-detail="${esc(item.id)}">Szczegóły</button><button type="button" data-admin-edit="${esc(item.id)}">Edytuj</button></div></td></tr>`).join('')}</tbody></table></div>`;
    host.querySelectorAll('[data-admin-detail]').forEach(btn => btn.onclick = () => showDetail(btn.dataset.adminDetail));
    host.querySelectorAll('[data-admin-edit]').forEach(btn => btn.onclick = () => {
      const legacy = findLegacyButton(btn.dataset.adminEdit, 'edit');
      if (legacy) legacy.click(); else alert('Edytor obserwacji nie jest dostępny. Odśwież stronę.');
    });
  }

  async function showDetail(id) {
    const response = await fetch(`/api/observations/${encodeURIComponent(id)}`); if (!response.ok) return;
    const {observation:item} = await response.json();
    let dialog = document.getElementById('om-admin-detail-dialog');
    if (!dialog) { dialog = document.createElement('dialog'); dialog.id='om-admin-detail-dialog'; dialog.className='om-dialog'; document.body.appendChild(dialog); }
    const value = typeof item.value === 'string' ? item.value : JSON.stringify(item.value ?? null, null, 2);
    const history = (item.audit || []).map(entry => {
      const diff = Object.entries(entry.diff || {}).map(([field, change]) => `<div class="om-admin-diff-row"><b>${esc(field)}</b><span>stara wartość: ${esc(JSON.stringify(change.before))}</span><span class="after">nowa wartość: ${esc(JSON.stringify(change.after))}</span></div>`).join('');
      return `<div><b>v${esc(entry.version)}</b> · ${esc(entry.action)} · ${esc(entry.at)} · autor: ${esc(entry.author || 'local-user')}${diff ? `<div class="om-admin-diff">${diff}</div>` : ''}</div>`;
    }).join('<hr>') || 'Brak historii.';
    dialog.innerHTML = `<div class="om-form"><h3>Szczegóły obserwacji</h3><p class="om-subtitle">${esc(item.location_name || item.spatial_id)} · ${esc(item.timepoint)}</p><div class="om-detail"><div class="om-detail-row"><b>Poziom</b><span>${esc(item.biological_level)}</span></div><div class="om-detail-row"><b>Nazwa</b><span>${esc(item.name)}</span></div><div class="om-detail-row"><b>Wartość</b><span><pre>${esc(value)}</pre></span></div><div class="om-detail-row"><b>Region</b><span>${esc(item.spatial_id)}</span></div><div class="om-detail-row"><b>Modality</b><span>${esc(item.modality)}</span></div><div class="om-detail-row"><b>Źródło</b><span>${esc(item.source)}</span></div><div class="om-detail-row"><b>Evidence</b><span>${esc(item.evidence_id || 'brak jawnego powiązania')}</span></div><div class="om-detail-row"><b>Autor</b><span>${esc(item.author || 'local-user')}</span></div><div class="om-detail-row"><b>Wersja</b><span>v${esc(item.version || 1)}</span></div><div class="om-detail-row"><b>Obserwowano</b><span>${esc(item.observed_at)}</span></div><div class="om-detail-row"><b>Notatka</b><span>${esc(item.notes || '—')}</span></div></div><div class="om-history"><strong>Historia i diff</strong><div class="om-history-item">${history}</div></div><div class="om-form-actions"><button type="button" id="om-admin-close">Zamknij</button></div></div>`;
    dialog.querySelector('#om-admin-close').onclick = () => dialog.close(); dialog.showModal();
  }

  addStyles(); ensureTools();
  window.addEventListener('testhp:observation-changed', load);
  window.addEventListener('testhp:spatial-layer-changed', () => { /* global register: region selection does not filter this view */ });
  load().catch(error => { const host = document.createElement('div'); host.className='om-admin-empty'; host.textContent=error.message; root.appendChild(host); });
})();
