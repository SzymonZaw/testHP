(() => {
  'use strict';

  const KEY = '__testhpDigitalTwinEndUserUIV1';
  if (window[KEY]) return;

  const MODALITIES = [
    ['hand_images', 'Hand Images'],
    ['hand_video', 'Hand Video'],
    ['hand_3d', '3D Scan'],
    ['tissue_wsi', 'WSI'],
    ['single_cell_rna', 'RNA'],
    ['proteomics', 'Proteomics'],
    ['epigenetics', 'Epigenetics'],
    ['genomics', 'Genomics']
  ];
  const REGIONS = ['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'];

  const state = { analysis: null, region: 'palm', activeTab: 'evidence' };

  const esc = value => String(value ?? '').replace(/[&<>\"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[ch]));
  const available = asset => ['ready', 'available', 'verified'].includes(String(asset?.status || '').toLowerCase());

  function assets() {
    return Array.isArray(state.analysis?.assets) ? state.analysis.assets : [];
  }

  function hasModality(modality) {
    const aliases = {
      hand_images: ['hand', 'hand_images', 'image'],
      hand_video: ['hand_video', 'video'],
      hand_3d: ['hand_3d', '3d', 'mesh'],
      tissue_wsi: ['wsi', 'tissue_wsi'],
      single_cell_rna: ['rna', 'single_cell_rna', 'scrna'],
      proteomics: ['proteomics', 'protein'],
      epigenetics: ['epigenetics', 'methylation', 'chromatin'],
      genomics: ['genomics', 'genome', 'variant']
    };
    const names = aliases[modality] || [modality];
    return assets().some(a => available(a) && names.includes(String(a.modality || '').toLowerCase()));
  }

  function evidenceScore() {
    const present = MODALITIES.filter(([id]) => hasModality(id)).length;
    return Math.round((present / MODALITIES.length) * 100);
  }

  function confidenceScore() {
    const values = assets().filter(available).map(a => Number(a.confidence)).filter(Number.isFinite).map(v => Math.max(0, Math.min(1, v)));
    if (!values.length) return null;
    return Math.round(values.reduce((a,b) => a+b, 0) / values.length * 100);
  }

  function confidenceLabel(score) {
    if (score == null) return 'Not established';
    if (score >= 80) return 'High';
    if (score >= 60) return 'Moderate';
    return 'Low';
  }

  function healthForRegion(region) {
    const assessments = Array.isArray(state.analysis?.assessments) ? state.analysis.assessments : [];
    const item = assessments.find(a => String(a.region_id || a.regionId || '').toLowerCase() === region);
    if (!item) return { state: 'Unknown', confidence: null, evidence: [] };
    const value = String(item.health_state || item.state || item.label || 'Unknown');
    const normalized = ['healthy', 'at risk', 'diseased', 'unknown'].includes(value.toLowerCase()) ? value : 'Unknown';
    return { state: normalized, confidence: Number.isFinite(Number(item.confidence)) ? Number(item.confidence) : null, evidence: Array.isArray(item.evidence) ? item.evidence : [] };
  }

  function cellSummary(region) {
    const cells = Array.isArray(state.analysis?.cells) ? state.analysis.cells : [];
    const inRegion = cells.filter(c => String(c.region_id || c.regionId || region).toLowerCase() === region);
    const groups = new Map();
    inRegion.forEach(c => {
      const type = c.cell_type || c.cellType || 'Unclassified';
      groups.set(type, (groups.get(type) || 0) + 1);
    });
    return [...groups.entries()].map(([type, count]) => ({ type, count }));
  }

  function render() {
    const host = document.getElementById('testhp-end-user-layer');
    if (!host) return;
    const coverage = evidenceScore();
    const confidence = confidenceScore();
    const missing = MODALITIES.filter(([id]) => !hasModality(id)).map(([,label]) => label);
    const health = healthForRegion(state.region);
    const cells = cellSummary(state.region);

    host.innerHTML = `
      <section class="testhp-eu-shell" aria-label="Digital twin evidence and biological state">
        <div class="testhp-eu-tabs" role="tablist">
          ${['evidence','health','cells','molecular'].map(tab => `<button type="button" role="tab" aria-selected="${state.activeTab === tab}" class="${state.activeTab === tab ? 'active' : ''}" data-eu-tab="${tab}">${tab === 'evidence' ? 'Evidence' : tab === 'health' ? 'Health State' : tab === 'cells' ? 'Cells' : 'Molecular'}</button>`).join('')}
        </div>

        <div class="testhp-eu-context">
          <strong>${esc(state.analysis?.subject_id || state.analysis?.subjectId || 'User Digital Twin')}</strong>
          <span>Region: ${esc(state.region)}</span>
          <select id="testhp-eu-region" aria-label="Region">
            ${REGIONS.map(r => `<option value="${r}" ${r === state.region ? 'selected' : ''}>${r[0].toUpperCase()+r.slice(1)}</option>`).join('')}
          </select>
        </div>

        ${state.activeTab === 'evidence' ? evidenceView(coverage, confidence, missing) : ''}
        ${state.activeTab === 'health' ? healthView(health) : ''}
        ${state.activeTab === 'cells' ? cellsView(cells) : ''}
        ${state.activeTab === 'molecular' ? molecularView() : ''}
      </section>`;

    host.querySelectorAll('[data-eu-tab]').forEach(button => button.addEventListener('click', () => { state.activeTab = button.dataset.euTab; render(); }));
    host.querySelector('#testhp-eu-region')?.addEventListener('change', event => { state.region = event.target.value; render(); window.dispatchEvent(new CustomEvent('testhp:end-user-region-changed', { detail: { region: state.region } })); });
  }

  function evidenceView(coverage, confidence, missing) {
    return `<div class="testhp-eu-grid">
      <div class="testhp-eu-card testhp-eu-card-wide">
        <div class="testhp-eu-card-title"><span>Evidence Coverage</span><strong>${coverage}%</strong></div>
        <div class="testhp-eu-progress"><i style="width:${coverage}%"></i></div>
        <p>${coverage === 100 ? 'All declared modalities are available.' : 'Coverage describes which declared evidence modalities are currently available. It is not a clinical confidence score.'}</p>
      </div>
      <div class="testhp-eu-card"><span class="testhp-eu-kicker">Confidence</span><strong class="testhp-eu-number">${confidence == null ? '—' : confidence + '%'}</strong><span>${confidenceLabel(confidence)}</span></div>
      <div class="testhp-eu-card"><span class="testhp-eu-kicker">Missing modalities</span><strong class="testhp-eu-number">${missing.length}</strong><span>${missing.length ? esc(missing.join(', ')) : 'None'}</span></div>
      <div class="testhp-eu-card testhp-eu-card-wide"><div class="testhp-eu-card-title"><span>Evidence sources</span><span>Available</span></div>${MODALITIES.map(([id,label]) => `<div class="testhp-eu-row"><span>${esc(label)}</span><b class="${hasModality(id) ? 'yes' : 'no'}">${hasModality(id) ? '✓' : '✗'}</b></div>`).join('')}</div>
      <div class="testhp-eu-card testhp-eu-card-wide"><span class="testhp-eu-kicker">Interpretation</span><p>Results are limited to evidence actually supplied or computed. Missing modalities are not treated as evidence of health or disease. A confidence value is shown only when the upstream result provides one.</p></div>
    </div>`;
  }

  function healthView(health) {
    const states = ['Healthy','At Risk','Diseased','Unknown'];
    return `<div class="testhp-eu-grid"><div class="testhp-eu-card testhp-eu-card-wide"><span class="testhp-eu-kicker">${esc(state.region)}</span><h2>${esc(health.state)}</h2><p>Health state is <strong>Unknown</strong> when no explicit assessment is linked to this region.</p><div class="testhp-eu-health-options">${states.map(s => `<span class="${s.toLowerCase() === health.state.toLowerCase() ? 'selected' : ''}">${s}</span>`).join('')}</div></div><div class="testhp-eu-card"><span class="testhp-eu-kicker">Confidence</span><strong class="testhp-eu-number">${health.confidence == null ? '—' : Math.round(health.confidence*100) + '%'}</strong></div><div class="testhp-eu-card"><span class="testhp-eu-kicker">Evidence</span><strong class="testhp-eu-number">${health.evidence.length || 0}</strong><span>linked assessment sources</span></div></div>`;
  }

  function cellsView(cells) {
    const total = cells.reduce((sum, x) => sum + x.count, 0);
    return `<div class="testhp-eu-grid"><div class="testhp-eu-card testhp-eu-card-wide"><span class="testhp-eu-kicker">Cell Explorer · ${esc(state.region)}</span><strong class="testhp-eu-number">${total}</strong><span>cells currently linked to this region</span></div>${(cells.length ? cells : [{type:'Unclassified',count:0}]).map(c => `<div class="testhp-eu-card"><strong>${esc(c.type)}</strong><span>${c.count} cells</span><span>health: Unknown · age: Not established · confidence: —</span></div>`).join('')}<div class="testhp-eu-card testhp-eu-card-wide"><p>Cell type, health and age are displayed only when an upstream validated result is present. Detection alone does not establish a biological cell type or disease state.</p></div></div>`;
  }

  function molecularView() {
    const molecular = [['single_cell_rna','RNA'],['proteomics','Proteomics'],['epigenetics','Epigenetics'],['genomics','Genomics']];
    return `<div class="testhp-eu-grid">${molecular.map(([id,label]) => `<div class="testhp-eu-card"><span class="testhp-eu-kicker">${label}</span><strong>${hasModality(id) ? 'Available' : 'Missing'}</strong><span>quality: ${hasModality(id) ? 'available data' : 'not supplied'}</span><span>confidence: ${hasModality(id) ? '—' : '—'}</span></div>`).join('')}<div class="testhp-eu-card testhp-eu-card-wide"><p>Molecular evidence is kept separate from imaging evidence. RNA, proteomics, epigenetics and genomics are not inferred from their absence and are not substituted for one another.</p></div></div>`;
  }

  function mount() {
    let host = document.getElementById('testhp-end-user-layer');
    if (!host) {
      host = document.createElement('div');
      host.id = 'testhp-end-user-layer';
      document.body.appendChild(host);
    }
    if (!document.getElementById('testhp-end-user-layer-style')) {
      const style = document.createElement('style');
      style.id = 'testhp-end-user-layer-style';
      style.textContent = `#testhp-end-user-layer{font-family:Inter,system-ui,sans-serif;color:#e8edf5;max-width:1180px;margin:24px auto;padding:0 18px}.testhp-eu-shell{background:#111722;border:1px solid #293345;border-radius:18px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.2)}.testhp-eu-tabs{display:flex;gap:4px;padding:8px;background:#0b1018;border-bottom:1px solid #293345}.testhp-eu-tabs button{background:transparent;border:0;color:#94a0b5;padding:12px 16px;border-radius:10px;cursor:pointer}.testhp-eu-tabs button.active{background:#202a3a;color:#fff}.testhp-eu-context{display:flex;align-items:center;gap:14px;padding:18px 20px;border-bottom:1px solid #293345}.testhp-eu-context span{color:#94a0b5}.testhp-eu-context select{margin-left:auto;background:#161e2b;color:#e8edf5;border:1px solid #364155;border-radius:8px;padding:8px}.testhp-eu-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:18px}.testhp-eu-card{background:#171f2d;border:1px solid #2a3548;border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:7px;min-height:100px}.testhp-eu-card-wide{grid-column:1/-1}.testhp-eu-card-title{display:flex;justify-content:space-between;align-items:center}.testhp-eu-card-title strong{font-size:28px}.testhp-eu-kicker{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#8190a8}.testhp-eu-number{font-size:28px}.testhp-eu-card p{color:#9aa6ba;line-height:1.5;margin:4px 0}.testhp-eu-progress{height:9px;background:#0c121b;border-radius:99px;overflow:hidden;margin:10px 0}.testhp-eu-progress i{display:block;height:100%;background:#66b3ff;border-radius:inherit}.testhp-eu-row{display:flex;justify-content:space-between;padding:9px 0;border-top:1px solid #293345}.testhp-eu-row b.yes{color:#69d19a}.testhp-eu-row b.no{color:#718096}.testhp-eu-health-options{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.testhp-eu-health-options span{border:1px solid #344056;border-radius:999px;padding:7px 11px;color:#8290a7}.testhp-eu-health-options span.selected{color:#fff;border-color:#66b3ff;background:#1b3047}@media(max-width:700px){.testhp-eu-grid{grid-template-columns:1fr}.testhp-eu-card-wide{grid-column:auto}.testhp-eu-context{flex-wrap:wrap}.testhp-eu-context select{margin-left:0}}`;
      document.head.appendChild(style);
    }
    render();
  }

  function setAnalysis(analysis) { state.analysis = analysis || null; mount(); }
  window[KEY] = Object.freeze({ mount, setAnalysis });
  window.addEventListener('testhp:analysis-ready', event => setAnalysis(event.detail?.analysis || event.detail || null));
  window.addEventListener('testhp:digital-twin-analysis-ready', event => setAnalysis(event.detail?.analysis || event.detail || null));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
