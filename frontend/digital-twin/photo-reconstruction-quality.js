(() => {
  const API = '/api/hand/photo-reconstruction/quality';
  const esc = value => String(value ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));

  async function json(url, options) {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
  }

  function render(container, state) {
    const validation = state.validation || {};
    const reconstruction = state.reconstruction;
    const views = ['front', 'back', 'side_left', 'side_right', 'thumb'];
    const labels = {front:'Front', back:'Back', side_left:'Side left', side_right:'Side right', thumb:'Thumb'};
    const cards = views.map(view => {
      const record = state.views?.[view];
      const registered = record?.registration?.status === 'registered';
      const prepared = !!record?.prepared;
      const status = registered ? 'Ready' : prepared ? 'Prepared' : 'Missing';
      return `<article class="photo-recon-view ${registered ? 'ready' : ''}"><strong>${labels[view]}</strong><span>${status}</span>${record?.filename ? `<small>${esc(record.filename)}</small>` : ''}</article>`;
    }).join('');
    const warnings = (validation.warnings || []).map(w => `<li>${esc(w)}</li>`).join('');
    const errors = (validation.errors || []).map(e => `<li>${esc(e)}</li>`).join('');
    container.innerHTML = `<section class="photo-recon-panel photo-recon-quality"><header><h2>Photo 3D Reconstruction</h2><p>Real photographs → 3D hand</p></header><div class="photo-recon-views">${cards}</div><p class="photo-recon-count">${state.prepared_count || 0} / 5 views prepared · ${state.registered_count || 0} registered</p>${errors ? `<div class="photo-recon-error"><strong>Needs attention</strong><ul>${errors}</ul></div>` : ''}${warnings ? `<details><summary>Photo warnings (${validation.warnings.length})</summary><ul>${warnings}</ul></details>` : ''}<div class="photo-recon-actions"><button type="button" data-action="build" ${validation.status !== 'ready' ? 'disabled' : ''}>Build 3D reconstruction</button><button type="button" data-action="clear" ${reconstruction ? '' : 'disabled'}>Clear reconstruction</button></div><div class="photo-recon-result">${reconstruction ? `<strong>Reconstruction ready</strong><br>${reconstruction.mesh.vertex_count} vertices · ${reconstruction.mesh.face_count} faces` : esc(validation.message || 'Add at least two prepared photographs.')}</div></section>`;
    container.querySelector('[data-action="build"]')?.addEventListener('click', async event => {
      event.currentTarget.disabled = true;
      try { await json(`${API}/build`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({subject_id:state.subject_id,timepoint:state.timepoint})}); mount(container, state.subject_id, state.timepoint); }
      catch (error) { alert(error.message); event.currentTarget.disabled = false; }
    });
    container.querySelector('[data-action="clear"]')?.addEventListener('click', async event => {
      event.currentTarget.disabled = true;
      await json(`${API}/clear`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({subject_id:state.subject_id,timepoint:state.timepoint})});
      mount(container, state.subject_id, state.timepoint);
    });
  }

  function mount(container, subjectId = 'default', timepoint = 'default') {
    json(`${API}/state?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}`).then(state => render(container, state)).catch(error => { container.textContent = error.message; });
  }

  window.PhotoReconstructionQualityUI = { mount };
})();
