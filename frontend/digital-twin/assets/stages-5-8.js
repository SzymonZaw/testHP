(() => {
  const EVIDENCE_KEY = 'digitalTwinEvidenceUX.v2';
  const TARGET_ROOT = 'hand';
  const VIEWS = ['front','back','side_left','side_right','thumb'];
  const panel = document.createElement('section');
  panel.className = 'panel';
  panel.id = 'stages-5-8-panel';

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const readEvidence = () => {
    try {
      const value = JSON.parse(localStorage.getItem(EVIDENCE_KEY) || '{}');
      return Array.isArray(value.evidence) ? value.evidence.filter(item => !item.archived) : [];
    } catch { return []; }
  };
  const spatialIdOf = value => {
    if (!value) return null;
    if (typeof value === 'string') return value;
    return value.spatial_id || value.spatialId || value.targetSpatialId || value.target || value.spatialTarget || null;
  };
  const currentTarget = () => String(
    spatialIdOf(window.spatialEvidenceTarget) ||
    spatialIdOf(window.selectedSpatialNode) ||
    spatialIdOf(window.spatialViewportManager?.state?.spatialTarget) ||
    document.body.dataset.spatialTarget || TARGET_ROOT
  );
  const targetLabel = () => {
    const node = window.selectedSpatialNode;
    if (node?.label) return node.label;
    return document.querySelector('#spatial-node strong')?.textContent?.trim() || currentTarget();
  };
  const targetEvidence = target => readEvidence().filter(item => spatialIdOf(item.target || item.spatialTarget) === target);
  const viewOf = item => {
    const explicit = String(item?.view || item?.preparedAsset?.view || '').toLowerCase();
    if (VIEWS.includes(explicit)) return explicit;
    const name = String(item?.filename || item?.preparedAsset?.name || '').toLowerCase().replace(/[- ]/g, '_');
    return VIEWS.find(view => name.includes(view)) || null;
  };
  const levelOf = item => String(item?.biologicalLayer || item?.level || item?.type || '').toLowerCase();
  const render = () => {
    const target = currentTarget();
    const evidence = targetEvidence(target);
    const prepared = evidence.filter(item => item.prepared || item.sourceType === 'prepared-image');
    const views = VIEWS.filter(view => prepared.some(item => viewOf(item) === view));
    const levels = new Set(evidence.map(levelOf).filter(Boolean));
    const timepoints = [...new Set(evidence.map(item => item.timepoint).filter(Boolean))].sort();
    panel.innerHTML = `
      <div class="panel-title">
        <div><span class="section-kicker">SILNIK CYFROWEGO BLIŹNIAKA</span><strong>ETAPY 5–8</strong></div>
        <span class="research-badge">TYLKO DO BADAŃ</span>
      </div>
      <div class="s58-target"><span>AKTUALNY CEL</span><strong>${esc(targetLabel())}</strong><code>${esc(target)}</code></div>
      <div class="s58-grid">
        <article class="state-card"><span>Warstwa danych</span><strong>${evidence.length ? `${evidence.length} rekordów` : 'Brak danych'}</strong><small>Etap 5 · dane są przypisane do dokładnego spatial_id.</small></article>
        <article class="state-card"><span>Anatomia</span><strong>${levels.size ? [...levels].slice(0,3).join(' · ') : 'Brak warstwy'}</strong><small>Etap 6 · warstwa biologiczna wynika z rekordu, nie z samego kliknięcia.</small></article>
        <article class="state-card"><span>Postępująca rozdzielczość</span><strong>${views.length}/5 widoków przygotowanych</strong><small>Etap 7 · postęp jest liczony dla bieżącego celu; brak danych nie jest zastępowany fallbackiem.</small></article>
        <article class="state-card"><span>Historia podłużna</span><strong>${timepoints.length ? `${timepoints.length} punktów` : 'Brak historii'}</strong><small>Etap 8 · historia jest widoczna tylko, gdy istnieją rekordy z różnymi punktami czasu.</small></article>
      </div>
      <div class="s58-findings">
        <div><strong>Stan wejścia</strong><span>${evidence.length ? 'Dane istnieją dla tego celu.' : 'Brak danych przypisanych do tego celu.'}</span></div>
        <div><strong>Rozdzielczość</strong><span>${views.length === 5 ? 'Komplet pięciu przygotowanych widoków.' : `Brakuje ${5 - views.length} widoków.`}</span></div>
        <div><strong>Czas</strong><span>${timepoints.length > 1 ? `Dostępne punkty: ${timepoints.map(esc).join(', ')}` : 'Brak porównania podłużnego.'}</span></div>
      </div>
      <p class="s58-note">Etapy 5–8 opisują stan danych dla aktualnego celu. Nie tworzą diagnozy, nie wnioskują o anatomii na podstawie samego modelu 3D i nie zastępują rejestracji fotograficznej.</p>`;
  };
  const installCss = () => {
    if (document.getElementById('stages-5-8-css')) return;
    const style = document.createElement('style');
    style.id = 'stages-5-8-css';
    style.textContent = `#stages-5-8-panel{margin-top:16px}.s58-target{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid var(--border,#d8dee8)}.s58-target span{font-size:10px;font-weight:800;letter-spacing:.08em;color:#667085}.s58-target strong{font-size:15px}.s58-target code{font-size:11px;color:#667085}.s58-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;padding:16px}.s58-findings{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;padding:0 16px 12px}.s58-findings>div{border:1px solid var(--border,#d8dee8);border-radius:9px;padding:10px}.s58-findings strong,.s58-findings span{display:block}.s58-findings span{margin-top:4px;font-size:12px;color:#667085}.s58-note{margin:0;padding:0 16px 16px;font-size:12px;color:#667085}@media(max-width:900px){.s58-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.s58-findings{grid-template-columns:1fr}}@media(max-width:520px){.s58-grid{grid-template-columns:1fr}}`;
    document.head.appendChild(style);
  };
  const mount = () => {
    const anchor = document.querySelector('.timeline');
    if (anchor && !document.getElementById('stages-5-8-panel')) anchor.after(panel);
    installCss();
    render();
  };
  const refresh = () => render();
  window.addEventListener('testhp:spatial-target-changed', refresh);
  window.addEventListener('testhp:spatial-layer-changed', refresh);
  window.addEventListener('testhp:evidence-attached', refresh);
  window.addEventListener('testhp:spatial-contract-changed', refresh);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once:true});
  else mount();
})();
