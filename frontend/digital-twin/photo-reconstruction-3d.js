(() => {
  const API = '/api/hand/photo-reconstruction';
  const VIEW_ORDER = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const LABELS = { front: 'Front', back: 'Back', side_left: 'Side left', side_right: 'Side right', thumb: 'Thumb' };

  async function json(url, options) {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
  }

  function render(container, state) {
    const records = state.records || [];
    const cards = VIEW_ORDER.map(view => {
      const record = (state.views || {})[view];
      const ready = record?.registration?.status === 'registered';
      const prepared = !!record?.prepared;
      return `<article class="photo-recon-view ${ready ? 'ready' : ''}">
        <strong>${LABELS[view]}</strong>
        <span>${ready ? '✓ Registered' : prepared ? '✓ Prepared' : '○ Missing'}</span>
        ${record?.filename ? `<small>${record.filename}</small>` : ''}
      </article>`;
    }).join('');
    const reconstruction = state.reconstruction;
    container.innerHTML = `<section class="photo-recon-panel">
      <header><h2>Photo 3D Reconstruction</h2><p>Real photographs → 3D hand</p></header>
      <div class="photo-recon-views">${cards}</div>
      <p class="photo-recon-count">${state.prepared_count || 0} / 5 views prepared · ${state.registered_count || 0} registered</p>
      <div class="photo-recon-actions">
        <button type="button" data-action="build" ${(state.registered_count || 0) < 2 ? 'disabled' : ''}>Build 3D reconstruction</button>
        <button type="button" data-action="clear" ${reconstruction ? '' : 'disabled'}>Clear reconstruction</button>
      </div>
      <div class="photo-recon-result">${reconstruction ? `<strong>Reconstruction ready</strong><br>${reconstruction.mesh.vertex_count} vertices · ${reconstruction.mesh.face_count} faces<br><a target="_blank" rel="noopener" href="${API}/asset/${encodeURIComponent(reconstruction.reconstruction_id)}/hand.obj">Open mesh</a>` : 'No reconstruction yet.'}</div>
    </section>`;
    container.querySelector('[data-action="build"]')?.addEventListener('click', async e => {
      e.currentTarget.disabled = true;
      try { render(container, await json(`${API}/state?subject_id=${encodeURIComponent(state.subject_id)}&timepoint=${encodeURIComponent(state.timepoint)}`)); await json(`${API}/build`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({subject_id: state.subject_id, timepoint: state.timepoint})}); render(container, await json(`${API}/state?subject_id=${encodeURIComponent(state.subject_id)}&timepoint=${encodeURIComponent(state.timepoint)}`)); }
      catch (err) { alert(err.message); e.currentTarget.disabled = false; }
    });
    container.querySelector('[data-action="clear"]')?.addEventListener('click', async e => {
      e.currentTarget.disabled = true;
      await json(`${API}/clear`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({subject_id: state.subject_id, timepoint: state.timepoint}) });
      render(container, await json(`${API}/state?subject_id=${encodeURIComponent(state.subject_id)}&timepoint=${encodeURIComponent(state.timepoint)}`));
    });
  }

  window.PhotoReconstruction3D = { mount(container, subjectId = 'default', timepoint = 'default') {
    json(`${API}/state?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}`).then(state => render(container, state)).catch(err => { container.textContent = err.message; });
  }};
})();
