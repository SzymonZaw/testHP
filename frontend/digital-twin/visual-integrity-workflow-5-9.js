(() => {
  const ID = 'visual-integrity-workflow-5-9';
  const $ = (s, root = document) => root.querySelector(s);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  const state = () => {
    const capture = window.testhpHandGeometryCapture?.getState?.() || {};
    const measurements = capture.measurements || {};
    const hasMeasurements = Number(measurements.palmLength) > 0 && Number(measurements.palmWidth) > 0;
    let reconstruction = null;
    try { reconstruction = JSON.parse(localStorage.getItem('testhp.handGeometryCapture.v1') || 'null'); } catch {}
    const captured = reconstruction?.captured || {};
    const photoViews = ['front','back','side_left','side_right','thumb'].filter(v => captured[v]).length;
    let projection = null;
    try { projection = JSON.parse(localStorage.getItem('digitalTwinSurfaceProjection.v2') || 'null'); } catch {}
    const projected = !!(projection?.views?.length || document.querySelector('#__spatial_registry_evidence_projection__'));
    const children = document.querySelector('#__spatial_registry_evidence_projection__')?.children?.length || 0;
    return { hasMeasurements, photoViews, projected, children, hasCaptureApi: !!window.testhpHandGeometryCapture, hasProjectionApi: !!window.testhpPhotoSurfaceProjection };
  };

  function install() {
    if ($(ID)) return $(ID);
    const anchor = document.querySelector('#hand-geometry-capture') || document.querySelector('.twin-panel');
    if (!anchor?.parentElement) return null;
    const el = document.createElement('section');
    el.id = ID;
    el.className = 'panel';
    el.innerHTML = `
      <div class="viw-head">
        <div><span class="viw-kicker">DOPASOWANIE DO RZECZYWISTEJ DŁONI</span><h2>Od pomiaru do modelu 3D</h2><p>Przejdź przez kolejne kroki. Każdy krok wykorzystuje dane z poprzedniego i nie zmienia oryginalnych zdjęć.</p></div>
        <span class="viw-status" id="viw-status">Sprawdzanie…</span>
      </div>
      <div class="viw-steps">
        <button type="button" data-viw="5"><b>5</b><span>Pomiar</span><small>skala i wymiary</small></button>
        <button type="button" data-viw="6"><b>6</b><span>Dopasowanie</span><small>parametry modelu</small></button>
        <button type="button" data-viw="7"><b>7</b><span>Rekonstrukcja</span><small>zdjęcia → geometria</small></button>
        <button type="button" data-viw="8"><b>8</b><span>Powierzchnia</span><small>zdjęcia na modelu</small></button>
        <button type="button" data-viw="9"><b>9</b><span>Kontrola</span><small>sprawdź wynik</small></button>
      </div>
      <div class="viw-body" id="viw-body"></div>`;
    anchor.parentElement.insertBefore(el, anchor);
    el.querySelectorAll('[data-viw]').forEach(b => b.addEventListener('click', () => render(Number(b.dataset.viw))));
    render(5);
    window.testhpVisualIntegrityWorkflow = { refresh: () => render(5), getState: state };
    return el;
  }

  function captureStage(n) {
    const api = window.testhpHandGeometryCapture;
    if (!api) return;
    api.goTo?.(n);
    document.querySelector('#hand-geometry-capture')?.scrollIntoView({behavior:'smooth', block:'start'});
  }

  function render(step) {
    const el = install();
    if (!el) return;
    const s = state();
    el.querySelectorAll('[data-viw]').forEach(b => b.classList.toggle('active', Number(b.dataset.viw) === step));
    const status = $('#viw-status', el);
    status.textContent = s.projected ? `Powierzchnia: ${s.children || 'gotowa'}` : s.hasMeasurements ? 'Pomiar zapisany' : 'Wymaga pomiaru';
    const body = $('#viw-body', el);
    const data = {
      5: { title:'Pomiar referencyjny', text:'Najpierw ustal skalę i podstawowe wymiary dłoni. To pozwala zachować rzeczywiste proporcje modelu.', checks:[['Skala', !!(Number((window.testhpHandGeometryCapture?.getState?.()||{}).scaleMm)>0 && Number((window.testhpHandGeometryCapture?.getState?.()||{}).scalePx)>0)],['Długość dłoni', Number((window.testhpHandGeometryCapture?.getState?.()?.measurements?.palmLength))>0],['Szerokość dłoni', Number((window.testhpHandGeometryCapture?.getState?.()?.measurements?.palmWidth))>0]], action:'Wprowadź pomiary'},
      6: { title:'Automatyczne dopasowanie', text:'Pomiary są przeliczane na parametry istniejącego modelu. Nie tworzysz drugiego, równoległego edytora.', checks:[['Pomiary wejściowe', s.hasMeasurements],['Przeliczenie parametrów', !!window.testhpHandGeometryCapture?.fit],['Edytor 3D', !!window.__testhpPermanentGeometry]], action:'Przelicz i zastosuj'},
      7: { title:'Rekonstrukcja geometrii', text:'Jeżeli dostępne są zarejestrowane zdjęcia, możesz przejść od modelu parametrycznego do geometrii odtworzonej ze zdjęć.', checks:[['Widoki zdjęć', s.photoViews >= 2],['Moduł rekonstrukcji', !!window.PhotoReconstruction3D],['Model 3D', !!window.spatialViewportManager?.active?.scene]], action:'Otwórz moduł zdjęć'},
      8: { title:'Zdjęcia na powierzchni', text:'Po przygotowaniu geometrii zdjęcia powierzchni są przypisywane do odpowiednich widoków i nakładane na model 3D.', checks:[['Źródła zdjęć', s.photoViews >= 2],['Projekcja', s.projected],['Nałożone obrazy', s.children > 0]], action:'Odśwież projekcję'},
      9: { title:'Kontrola wyniku', text:'Na koniec sprawdź trzy rzeczy: kształt dłoni, ciągłość zdjęć na powierzchni i zgodność wybranego miejsca z danymi.', checks:[['Model 3D aktywny', !!window.spatialViewportManager?.active?.scene],['Zdjęcia powierzchni', s.children > 0],['Cel przestrzenny', !!(window.selectedSpatialNode || window.spatialEvidenceTarget)]], action:'Sprawdź model'}
    }[step];
    const checks = data.checks.map(([label, ok]) => `<div class="viw-check ${ok?'ok':''}"><i>${ok?'✓':'○'}</i><span>${esc(label)}</span><b>${ok?'Gotowe':'Do uzupełnienia'}</b></div>`).join('');
    body.innerHTML = `<div class="viw-copy"><h3>${data.title}</h3><p>${data.text}</p></div><div class="viw-checks">${checks}</div><div class="viw-actions"><button type="button" class="primary" id="viw-action">${data.action}</button></div>`;
    $('#viw-action', body).onclick = () => {
      if (step === 5) captureStage(2);
      else if (step === 6) { const r = window.testhpHandGeometryCapture?.apply?.(); render(6); if (r?.applied) alert('Pomiary zastosowano do modelu 3D.'); }
      else if (step === 7) document.querySelector('#hand-surface-unified')?.scrollIntoView({behavior:'smooth',block:'start'});
      else if (step === 8) window.testhpPhotoSurfaceProjection?.sync?.().then(() => render(8));
      else if (step === 9) document.querySelector('#twin-viewport')?.scrollIntoView({behavior:'smooth',block:'center'});
    };
  }

  const boot = () => { if (!install()) new MutationObserver((_, obs) => { if (install()) obs.disconnect(); }).observe(document.body, {childList:true, subtree:true}); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true}); else setTimeout(boot, 0);
})();
