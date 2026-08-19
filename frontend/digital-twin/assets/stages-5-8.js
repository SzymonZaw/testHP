(() => {
  const panel = document.createElement('section');
  panel.className = 'panel';
  panel.id = 'stages-5-8-panel';
  panel.innerHTML = `
    <div class="panel-title"><div><span class="section-kicker">DIGITAL TWIN ENGINE</span><strong>STAGES 5–8</strong></div><span class="research-badge">RESEARCH ONLY</span></div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;padding:16px">
      <article class="state-card"><span>Longitudinal</span><strong id="s58-longitudinal">Awaiting observations</strong><small>Stage 5 · change over time</small></article>
      <article class="state-card"><span>Prediction</span><strong id="s58-prediction">Not established</strong><small>Stage 6 · trajectory extrapolation</small></article>
      <article class="state-card"><span>Research Copilot</span><strong id="s58-copilot">No summary</strong><small>Stage 7 · evidence interpretation</small></article>
      <article class="state-card"><span>Human Twin</span><strong id="s58-human">Hand scope</strong><small>Stage 8 · extensible body architecture</small></article>
    </div>
    <div id="s58-findings" style="padding:0 16px 16px"></div>`;
  const timeline = document.querySelector('.timeline');
  timeline?.after(panel);

  async function getJSON(url, options) { const r = await fetch(url, options); if (!r.ok) throw new Error(await r.text()); return r.json(); }
  async function refresh() {
    try {
      const human = await getJSON('/api/human-twin?subject_id=own_cohort');
      document.getElementById('s58-human').textContent = (human.twin?.systems || ['hand']).join(', ');
      const copilot = await getJSON('/api/copilot/stage7', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subject_id:'own_cohort',node_id:'hand',observations:[]})});
      document.getElementById('s58-copilot').textContent = copilot.findings?.length ? 'Summary ready' : 'No summary';
      const findingBox = document.getElementById('s58-findings');
      findingBox.textContent = copilot.summary || 'No research interpretation is available for the current evidence.';
    } catch (e) { console.debug('Stages 5-8 panel:', e); }
  }
  refresh();
})();
