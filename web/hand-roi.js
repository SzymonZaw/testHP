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
          <span class="eyebrow">HAND · H9 · ROI</span>
          <h2>Region-of-interest review</h2>
          <p class="section-note">The system now exposes the prioritized hand regions as the next analysis targets. Priority is technical only and is not a disease score.</p>
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
      <p class="section-note">Selection only determines where the next analysis should look. It does not establish pathology.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:12px">
        ${zones.map((z, i) => `<button type="button" class="result-card hand-roi-zone" data-zone="${esc(z.id)}" style="text-align:left;border:1px solid currentColor;cursor:pointer"><strong>${esc(i + 1)} · ${esc(z.id)}</strong><p>Mean visibility: <b>${esc(z.mean_confidence)}</b></p><span class="status ${z.review_priority === 'normal' ? 'ok' : 'warning'}">${esc(z.review_priority)}</span></button>`).join('') || '<p class="muted">No ROI candidates are available yet. Run the hand analysis first.</p>'}
      </div>`;

    document.querySelectorAll('.hand-roi-zone').forEach(btn => btn.addEventListener('click', () => {
      const z = zones.find(x => x.id === btn.dataset.zone);
      if (!z) return;
      document.getElementById('hand-roi-detail').innerHTML = `
        <div class="result-card">
          <span class="eyebrow">SELECTED ROI</span>
          <h3>${esc(z.id)}</h3>
          <div class="detail-stats">
            <div><span>Observations</span><strong>${esc(z.observations)}</strong></div>
            <div><span>Mean confidence</span><strong>${esc(z.mean_confidence)}</strong></div>
            <div><span>Technical priority</span><strong>${esc(z.review_priority)}</strong></div>
          </div>
          <div class="detail-note"><strong>Next layer</strong><p>Use this region as the spatial target for deeper acquisition/analysis. Future modules can attach image patches, WSI regions, cellular measurements or molecular observations here.</p></div>
          <div class="detail-note"><strong>Evidence boundary</strong><p>${esc(data.next_action || 'No biological interpretation is made at H9.')}</p></div>
        </div>`;
    }));
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
      status(data.zone_summary?.length ? 'ROI map ready' : 'No ROI candidates yet', data.zone_summary?.length ? 'ok' : 'warning');
    } catch (error) {
      status(`ROI error: ${error.message}`, 'warning');
    } finally {
      button.disabled = false;
      button.textContent = 'Load ROI map';
    }
  }

  document.addEventListener('DOMContentLoaded', () => addSection());
})();
