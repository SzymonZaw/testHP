(() => {
  const WORKFLOW_ID = 'hand-surface-workflow';
  const PHOTO_RE = /PHOTO\s*3D\s*RECONSTRUCTION/i;
  const HAND_RE = /HAND\s*SURFACE/i;
  const text = el => (el?.textContent || '').replace(/\s+/g, ' ').trim();

  function findPanel(regex) {
    const hit = [...document.querySelectorAll('section,article,aside,div')].find(el => regex.test(text(el)) && el.children.length);
    if (!hit) return null;
    return hit.closest('.panel') || hit.closest('section') || hit;
  }

  function makeStep(title, subtitle, number) {
    const el = document.createElement('div');
    el.className = 'surface-workflow-step';
    el.innerHTML = `<span class="surface-workflow-step-number">${number}</span><div><strong>${title}</strong><span>${subtitle}</span></div>`;
    return el;
  }

  function ensureWorkflow() {
    if (document.getElementById(WORKFLOW_ID)) return true;
    const hand = findPanel(HAND_RE);
    const photo = findPanel(PHOTO_RE);
    if (!hand && !photo) return false;

    const anchor = hand || photo;
    const shell = document.createElement('section');
    shell.id = WORKFLOW_ID;
    shell.className = 'panel surface-workflow';
    shell.innerHTML = `
      <div class="panel-title surface-workflow-title">
        <div><span class="section-kicker">POWIERZCHNIA DŁONI 3D</span><strong>REALISTYCZNA POWIERZCHNIA DLA MODELU PRZESTRZENNEGO</strong></div>
        <span class="surface-workflow-status" id="surface-workflow-status">Proceduralna</span>
      </div>
      <p class="surface-workflow-intro">Dodaj zdjęcia dłoni, przygotuj je i utwórz na ich podstawie powierzchnię 3D. Gotową powierzchnię możesz zastosować do cyfrowego bliźniaka.</p>
      <div class="surface-workflow-steps" aria-label="Proces tworzenia powierzchni">
        <div class="surface-workflow-step active"><span class="surface-workflow-step-number">1</span><div><strong>Zdjęcia</strong><span>Dodaj zdjęcia z różnych stron dłoni.</span></div></div>
        <div class="surface-workflow-step"><span class="surface-workflow-step-number">2</span><div><strong>Przygotowanie</strong><span>System przygotuje zdjęcia do rekonstrukcji.</span></div></div>
        <div class="surface-workflow-step"><span class="surface-workflow-step-number">3</span><div><strong>Rekonstrukcja</strong><span>Zbuduj powierzchnię 3D.</span></div></div>
        <div class="surface-workflow-step"><span class="surface-workflow-step-number">4</span><div><strong>Podgląd</strong><span>Sprawdź wynik przed zastosowaniem.</span></div></div>
        <div class="surface-workflow-step"><span class="surface-workflow-step-number">5</span><div><strong>Zastosowanie</strong><span>Użyj powierzchni w modelu przestrzennym.</span></div></div>
      </div>
      <div class="surface-workflow-requirement"><strong>Minimum 2 zdjęcia</strong><span>Wybierz zdjęcia z różnych stron dłoni. Więcej widoków daje lepsze pokrycie powierzchni.</span></div>
    `;
    anchor.parentNode.insertBefore(shell, anchor);

    [hand, photo].filter(Boolean).forEach((panel, index) => {
      panel.classList.add('surface-workflow-detail');
      const title = panel.querySelector('.panel-title');
      if (title) {
        const kicker = title.querySelector('.section-kicker');
        const strong = title.querySelector('strong');
        if (index === 0 && HAND_RE.test(text(panel))) {
          if (kicker) kicker.textContent = 'KROK 2 · PRZYGOTOWANIE';
          if (strong) strong.textContent = 'Przygotuj zdjęcia';
        }
        if (PHOTO_RE.test(text(panel))) {
          if (kicker) kicker.textContent = 'KROK 3 · REKONSTRUKCJA';
          if (strong) strong.textContent = 'Zbuduj powierzchnię 3D';
        }
      }
      panel.querySelectorAll('h1,h2,h3,h4').forEach(h => {
        if (PHOTO_RE.test(h.textContent)) h.textContent = 'Rekonstrukcja powierzchni 3D';
      });
    });
    return true;
  }

  function updateStatus() {
    const status = document.getElementById('surface-workflow-status');
    if (!status) return;
    const photoPanel = [...document.querySelectorAll('.surface-workflow-detail')].find(p => PHOTO_RE.test(text(p)) || /Zbuduj powierzchnię 3D/i.test(text(p)));
    const inputs = photoPanel ? text(photoPanel) : '';
    if (/reconstruction ready|reconstruction complete|reconstruction available|rekonstrukcja gotowa|reconstruction generated/i.test(inputs)) {
      status.textContent = 'Fotograficzna · gotowa';
      status.classList.add('ready');
    } else {
      const count = inputs.match(/(\d+)\s*\/\s*5/);
      status.textContent = count && Number(count[1]) >= 2 ? `Gotowe do rekonstrukcji · ${count[1]} widoki` : 'Proceduralna';
    }
  }

  function init() {
    if (!ensureWorkflow()) return;
    updateStatus();
  }

  const observer = new MutationObserver(() => init());
  observer.observe(document.body, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
  window.addEventListener('testhp:spatial-contract-changed', updateStatus);
})();
