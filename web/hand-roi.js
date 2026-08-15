(() => {
  const esc = (v) => String(v ?? '').replace(/[&<>\"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;', "'":'&#39;' }[c]));

  function addSection() {
    if (document.getElementById('hand-roi')) return document.getElementById('hand-roi');
    const section = document.createElement('section');
    section.id = 'hand-roi';
    section.className = 'card';
    section.innerHTML = `
      <div class="section-head">
        <div>
          <span class="eyebrow">HAND · H9–H10 · ROI</span>
          <h2>Region-of-interest review</h2>
          <p class="section-note">H9 prioritizes regions from landmark visibility. H10 binds a selected region to real source-image coordinates and defines the evidence slots that deeper analyses may later fill.</p>
        </div>
        <button id="hand-roi-run" type="button">Load ROI map</button>
      </div>
      <div id="hand-roi-status" class="badge neutral">Awaiting hand analysis</div>
      <div id="hand-roi-summary" style="margin-top:18px"></div>
      <div id="hand-roi-list" style="margin-top:18px"></div>
      <div id="hand-roi-detail" style="margin-top:18px"></div>
    `;
    const footer = document.querySelector('footer');
    document.querySelector('main.container').insertBefore(section, footer);
    document.getElementById('hand-roi-run').addEventListener('click', load);
    return section;
  }

  function status(text, kind='neutral') {
    const el = document.getElementById('hand-roi-status');
    el.textContent = text;
    el.className = `badge ${kind}`;
  }

  async function showDetail(zoneId) {
    const target = document.getElementById('hand-roi-detail');
    target.innerHTML = '<div class="output-empty"><strong>Loading spatial binding…</strong><p>Resolving the selected region against the source images.</p></div>';
    try {
      const response = await fetch(`/api/hand/roi/${encodeURIComponent(zoneId)}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const data = await response.json();
      const slots = data.evidence_slots || [];
      const bindings = data.spatial_bindings || [];
      target.innerHTML = `
        <div class="result-card">
          <span class="eyebrow">H10 · SELECTED ROI</span>
          <h3>${esc(data.zone)}</h3>
          <div class="detail-stats">
            <div><span>Spatial bindings</span><strong>${bindings.length}</strong></div>
            <div><span>Mean confidence</span><strong>${esc(data.zone_summary?.mean_confidence ?? '—')}</strong></div>
            <div><span>Technical priority</span><strong>${esc(data.zone_summary?.review_priority ?? '—')}</strong></div>
          </div>
          <div class="detail-note"><strong>Spatial binding</strong><p>The ROI is currently defined from hand landmarks. The coordinates below identify where the region lies in the original image; they are not a tissue or cell segmentation.</p></div>
          <div class="table-wrap" style="margin-top:12px"><table><thead><tr><th>Source</th><th>Hand</th><th>Normalized ROI</th><th>Pixel ROI</th></tr></thead><tbody>
            ${bindings.map(b => `<tr><td><strong>${esc(b.file)}</strong></td><td>${esc(b.handedness || '—')} #${esc(b.hand_index)}</td><td><code>${esc(JSON.stringify(b.bbox_norm))}</code></td><td><code>${esc(JSON.stringify(b.bbox_px || {}))}</code></td></tr>`).join('') || '<tr><td colspan="4">No spatial binding available.</td></tr>'}
          </tbody></table></div>
          <div style="margin-top:18px"><span class="eyebrow">EVIDENCE SLOTS</span><h3>What can eventually be attached to this ROI?</h3>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin-top:10px">
              ${slots.map(s => `<div class="result-card"><strong>${esc(s.level)} · ${esc(s.id)}</strong><p>${esc(s.purpose)}</p><span class="status ${s.status === 'available' ? 'ok' : 'warning'}">${esc(s.status)}</span></div>`).join('')}
            </div>
          </div>
          <div class="detail-note"><strong>Evidence boundary</strong><p>Observed now: landmark-derived coordinates and source-image metadata. Not observed: tissue state, cell state, molecular state or disease state.</p></div>
          <div class="detail-note"><strong>Next layer</strong><p>${esc(data.next_action || 'Attach a validated deeper measurement to this spatial target.')}</p></div>
        </div>`;
    } catch (error) {
      target.innerHTML = `<div class="limitation"><span>!</span><p>H10 error: ${esc(error.message)}</p></div>`;
    }
  }

  function render(data) {
    const zones = data.zone_summary || [];
    const high = zones.filter(z => z.review_priority === 'high').length;
    const review = zones.filter(z => z.review_priority === 'review').length;
    document.getElementById('hand-roi-summary').innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px">
        <div class="metric card"><span>Regions</span><strong>${zones.length}</strong><small>ROI candidates</small></div>
        <div class="metric card"><span>High priority</span><strong>${high}</strong><small>technical review</small></div>
        <div class="metric card"><span>Review</span><strong>${review}</strong><small>technical review</small></div>
        <div class="metric card"><span>Stage</span><strong>${esc(data.stage || 'H9')}</strong><small>current ladder</small></div>
      </div>`;

    document.getElementById('hand-roi-list').innerHTML = `
      <span class="eyebrow">PRIORITIZED REGIONS</span>
      <h3>Select a region</h3>
      <p class="section-note">Selection determines the next spatial target. It does not establish pathology.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:12px">
        ${zones.map((z, i) => `<button type="button" class="result-card hand-roi-zone" data-zone="${esc(z.id)}" style="text-align:left;border:1px solid currentColor;cursor:pointer"><strong>${esc(i + 1)} · ${esc(z.id)}</strong><p>Mean visibility: <b>${esc(z.mean_confidence)}</b></p><span class="status ${z.review_priority === 'normal' ? 'ok' : 'warning'}">${esc(z.review_priority)}</span></button>`).join('') || '<p class="muted">No ROI candidates are available yet. Run the hand analysis first.</p>'}
      </div>`;

    document.querySelectorAll('.hand-roi-zone').forEach(btn => btn.addEventListener('click', () => showDetail(btn.dataset.zone)));
  }

  async function load() {
    addSection();
    const button = document.getElementById('hand-roi-run');
    button.disabled = true;
    button.textContent = 'Loading…';
    status('Checking ROI map…', 'warning');
    try {
      const response = await fetch('/api/hand/roi', { cache: 'no-store' });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const data = await response.json();
      render(data);
      status(data.zone_summary?.length ? 'ROI map ready · H10 available' : 'No ROI candidates yet', data.zone_summary?.length ? 'ok' : 'warning');
    } catch (error) {
      status(`ROI error: ${error.message}`, 'warning');
    } finally {
      button.disabled = false;
      button.textContent = 'Load ROI map';
    }
  }

  document.addEventListener('DOMContentLoaded', () => addSection());
})();
