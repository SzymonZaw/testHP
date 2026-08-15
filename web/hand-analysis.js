(() => {
  const esc = (v) => String(v ?? '').replace(/[&<>\"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;', "'":'&#39;' }[c]));

  function addSection() {
    if (document.getElementById('hand-analysis')) return document.getElementById('hand-analysis');
    const section = document.createElement('section');
    section.id = 'hand-analysis';
    section.className = 'card';
    section.innerHTML = `
      <div class="section-head">
        <div>
          <span class="eyebrow">HAND · DIGITAL TWIN V0</span>
          <h2>Own-cohort hand analysis</h2>
          <p class="section-note">First working layer: detect the hand, measure geometry, create stable anatomical zones and identify technical review areas. No disease inference is made here.</p>
        </div>
        <button id="hand-run" type="button">Analyze own hand</button>
      </div>
      <div id="hand-status" class="badge neutral">Not analyzed</div>
      <div id="hand-summary" style="margin-top:18px"></div>
      <div id="hand-twin" style="margin-top:18px"></div>
      <div id="hand-stages" style="margin-top:18px"></div>
      <div id="hand-observations" style="margin-top:18px"></div>
      <div id="hand-zones" style="margin-top:18px"></div>
      <div id="hand-images" style="margin-top:18px"></div>
      <div id="hand-limitations" style="margin-top:18px"></div>
    `;
    const footer = document.querySelector('footer');
    document.querySelector('main.container').insertBefore(section, footer);
    document.getElementById('hand-run').addEventListener('click', run);
    return section;
  }

  function setStatus(text, kind) {
    const el = document.getElementById('hand-status');
    el.textContent = text;
    el.className = `badge ${kind || 'neutral'}`;
  }

  function twinSvg(hand) {
    if (!hand || !hand.landmarks_2d || !hand.landmarks_2d.length) return '<div class="output-empty"><strong>No digital twin geometry.</strong></div>';
    const points = hand.landmarks_2d;
    const scale = 320;
    const xy = points.map((p) => ({ x: 20 + p.x * 280, y: 20 + p.y * 280 }));
    const edges = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[0,9],[9,10],[10,11],[11,12],[0,13],[13,14],[14,15],[15,16],[0,17],[17,18],[18,19],[19,20],[5,9],[9,13],[13,17]];
    const lines = edges.map(([a,b]) => `<line x1="${xy[a].x}" y1="${xy[a].y}" x2="${xy[b].x}" y2="${xy[b].y}" stroke="currentColor" stroke-width="3" opacity="0.7"/>`).join('');
    const dots = xy.map((p,i) => `<circle cx="${p.x}" cy="${p.y}" r="4" fill="currentColor"><title>landmark ${i}</title></circle>`).join('');
    return `<div class="result-card"><div class="result-card-head"><div><strong>Digital Twin v0 · ${esc(hand.handedness)}</strong><span>21 normalized landmarks</span></div><span class="status ok">geometry</span></div><svg viewBox="0 0 ${scale} ${scale}" width="100%" height="360" role="img" aria-label="Normalized hand landmark digital twin" style="max-width:420px;display:block;margin:12px auto">${lines}${dots}</svg><p>Spatial representation for later observations and ROI selection. It is not a biological or diagnostic model.</p></div>`;
  }

  function render(run) {
    const summary = document.getElementById('hand-summary');
    const twin = run.digital_twin;
    summary.innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px">
        <div class="metric card"><span>Own images</span><strong>${esc(run.files)}</strong><small>analyzed</small></div>
        <div class="metric card"><span>Hands detected</span><strong>${esc(run.hand_instances)}</strong><small>instances</small></div>
        <div class="metric card"><span>Images with hand</span><strong>${esc(run.images_with_hands)}</strong><small>successful detection</small></div>
        <div class="metric card"><span>Digital twin</span><strong>${twin ? 'v0' : '—'}</strong><small>${twin ? 'landmark geometry' : 'not created'}</small></div>
      </div>
    `;

    const firstHand = (run.images || []).flatMap((x) => x.hands || [])[0];
    document.getElementById('hand-twin').innerHTML = `<span class="eyebrow">DIGITAL TWIN</span><h3>Normalized hand geometry</h3>${twinSvg(firstHand)}`;

    document.getElementById('hand-stages').innerHTML = `
      <span class="eyebrow">HAND LADDER</span>
      <h3>H0–H7 implementation state</h3>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-top:10px">
        ${(run.stages || []).map((s) => `<div class="result-card"><strong>${esc(s.id)} · ${esc(s.name)}</strong><p>${esc(s.purpose)}</p><span class="status ${s.status === 'completed' ? 'ok' : 'warning'}">${esc(s.status)}</span></div>`).join('')}
      </div>
    `;

    document.getElementById('hand-observations').innerHTML = `
      <span class="eyebrow">OBSERVATIONS</span>
      <h3>What was measured</h3>
      ${(run.observations || []).map((x) => `<div class="finding" style="margin-top:10px"><div><span>${esc(x.level)}</span><strong>${esc(x.type)}</strong></div><p>${esc(x.text)}</p></div>`).join('') || '<p class="muted">No observations.</p>'}
    `;

    const zones = run.zones || [];
    document.getElementById('hand-zones').innerHTML = `
      <span class="eyebrow">SPATIAL MAP</span>
      <h3>Hand zones and technical review priority</h3>
      <p class="section-note">Priority is based only on landmark visibility. It does not mean that a zone is diseased.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:12px">
        ${zones.map((z) => `<div class="result-card"><strong>${esc(z.id)}</strong><p>visibility confidence: <b>${esc(z.confidence)}</b></p><span class="status ${z.review_priority === 'normal' ? 'ok' : 'warning'}">${esc(z.review_priority)}</span></div>`).join('') || '<p class="muted">No zones created.</p>'}
      </div>
    `;

    document.getElementById('hand-images').innerHTML = `
      <span class="eyebrow">INPUT REVIEW</span>
      <h3>Per-image detection</h3>
      <div class="table-wrap" style="margin-top:10px"><table><thead><tr><th>File</th><th>Status</th><th>Hands</th><th>Size</th><th>Brightness</th></tr></thead><tbody>
      ${(run.images || []).map((x) => `<tr><td><strong>${esc(x.file)}</strong></td><td><span class="status ${x.status === 'ok' ? 'ok' : 'warning'}">${esc(x.status)}</span></td><td>${esc(x.hands_detected || 0)}</td><td>${esc(x.quality?.width || '—')} × ${esc(x.quality?.height || '—')}</td><td>${esc(x.quality?.mean_brightness ?? '—')}</td></tr>`).join('')}
      </tbody></table></div>
    `;

    document.getElementById('hand-limitations').innerHTML = `
      <span class="eyebrow">BOUNDARY</span>
      <h3>What this stage does not claim</h3>
      ${(run.limitations || []).map((x) => `<div class="limitation"><span>!</span><p>${esc(x)}</p></div>`).join('')}
    `;
  }

  async function run() {
    addSection();
    const button = document.getElementById('hand-run');
    button.disabled = true;
    button.textContent = 'Analyzing…';
    setStatus('Checking hand input…', 'warning');
    try {
      const response = await fetch('/api/hand/analysis', { cache: 'no-store' });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const data = await response.json();
      render(data);
      setStatus(data.status === 'ready' ? 'Hand analysis complete' : 'Hand analysis needs review', data.status === 'ready' ? 'ok' : 'warning');
    } catch (error) {
      setStatus(`Hand analysis error: ${error.message}`, 'warning');
    } finally {
      button.disabled = false;
      button.textContent = 'Analyze own hand';
    }
  }

  document.addEventListener('DOMContentLoaded', () => addSection());
})();
