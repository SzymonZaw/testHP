(() => {
  const TARGET_LABEL = () => {
    const node = window.selectedSpatialNode || window.spatialEvidenceTarget;
    if (node && typeof node === 'object') return node.label || node.spatial_id || node.id || 'Bieżący cel';
    return window.spatialEvidenceTarget || document.body.dataset.spatialTarget || 'hand';
  };

  const findTextPanel = (text) => [...document.querySelectorAll('.panel, section, article')]
    .find(el => (el.textContent || '').includes(text));

  const clickStage = (panelId, tab) => {
    const panel = document.getElementById(panelId);
    const button = panel?.querySelector(`[data-tab="${tab}"]`);
    button?.click();
    panel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  function installCss() {
    if (document.getElementById('hand-surface-simple-ui-css')) return;
    const style = document.createElement('style');
    style.id = 'hand-surface-simple-ui-css';
    style.textContent = `
      #hand-surface-simple-nav{margin:16px 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
      #hand-surface-simple-nav .simple-context{flex:1 1 100%;font-size:13px;color:var(--muted,#667085);margin-bottom:2px}
      #hand-surface-simple-nav button{border:1px solid var(--border,#d8dee8);background:var(--panel,#fff);border-radius:999px;padding:9px 15px;cursor:pointer;font-weight:600}
      #hand-surface-simple-nav button.active{background:#172033;color:#fff;border-color:#172033}
      .hss-simple-actions{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
      .hss-simple-actions button{border:1px solid var(--border,#d8dee8);background:transparent;border-radius:999px;padding:7px 11px;cursor:pointer}
      .hss-simple-actions button.primary{background:#172033;color:#fff}
      #hand-surface-studio .hss-tabs[data-simple-hidden],#hand-surface-stages-20-22 .hss22-tabs[data-simple-hidden]{display:none!important}
      #hand-surface-simple-status{margin-left:auto;font-size:12px;color:var(--muted,#667085)}
    `;
    document.head.appendChild(style);
  }

  function simplifyStudio() {
    const studio = document.getElementById('hand-surface-studio');
    if (!studio || studio.dataset.simpleUi === '1') return;
    studio.dataset.simpleUi = '1';
    const tabs = studio.querySelector('.hss-tabs');
    if (tabs) tabs.dataset.simpleHidden = '1';

    const header = studio.querySelector('.panel-title');
    if (header) {
      header.innerHTML = `<div><span class="section-kicker">MATERIAŁ</span><strong>Źródła → przygotowanie → geometria</strong></div><span class="muted">Cel: ${TARGET_LABEL()}</span>`;
    }

    const actions = document.createElement('div');
    actions.className = 'hss-simple-actions';
    actions.innerHTML = `
      <button class="primary" data-simple-stage="evidence">Źródła</button>
      <button data-simple-stage="prepare">Przygotowanie</button>
      <button data-simple-stage="geometry">Geometria</button>
      <span id="hand-surface-simple-status">Techniczne etapy 11–15 pozostają w tle.</span>`;
    studio.insertBefore(actions, studio.querySelector('#hss-content'));
    actions.querySelectorAll('[data-simple-stage]').forEach(btn => btn.onclick = () => {
      const stage = btn.dataset.simpleStage;
      studio.querySelectorAll('[data-simple-stage]').forEach(x => x.classList.toggle('primary', x === btn));
      studio.querySelector(`.hss-tabs [data-tab="${stage}"]`)?.click();
    });

    studio.querySelector('.hss-tabs [data-tab="evidence"]')?.click();
  }

  function simplifyRegistration() {
    const panel = document.getElementById('hand-surface-stages-20-22');
    if (!panel || panel.dataset.simpleUi === '1') return;
    panel.dataset.simpleUi = '1';
    const tabs = panel.querySelector('.hss22-tabs');
    if (tabs) tabs.dataset.simpleHidden = '1';
    const header = panel.querySelector('.panel-title');
    if (header) {
      header.innerHTML = `<div><span class="section-kicker">REJESTRACJA</span><strong>Widoki → mapowanie → kontrola jakości</strong></div><span class="muted">Cel: ${TARGET_LABEL()}</span>`;
    }
    const actions = document.createElement('div');
    actions.className = 'hss-simple-actions';
    actions.innerHTML = `
      <button class="primary" data-simple-reg="registration">Kontrola jakości</button>
      <button data-simple-reg="projection">Plan projekcji</button>
      <button data-simple-reg="package">Pakiet bliźniaka</button>`;
    panel.insertBefore(actions, panel.querySelector('#hss22-content'));
    actions.querySelectorAll('[data-simple-reg]').forEach(btn => btn.onclick = () => {
      actions.querySelectorAll('[data-simple-reg]').forEach(x => x.classList.toggle('primary', x === btn));
      panel.querySelector(`.hss22-tabs [data-tab="${btn.dataset.simpleReg}"]`)?.click();
    });
    panel.querySelector('.hss22-tabs [data-tab="registration"]')?.click();
  }

  function installTopNavigation() {
    if (document.getElementById('hand-surface-simple-nav')) return;
    const anchor = document.getElementById('hand-surface-studio') || document.querySelector('.timeline');
    if (!anchor?.parentElement) return;
    const nav = document.createElement('nav');
    nav.id = 'hand-surface-simple-nav';
    nav.innerHTML = `
      <div class="simple-context"><strong>AKTUALNY CEL</strong> · ${TARGET_LABEL()} · wszystko poniżej dotyczy tego samego miejsca</div>
      <button class="active" data-simple-nav="material">Materiał</button>
      <button data-simple-nav="registration">Rejestracja</button>
      <button data-simple-nav="interpretation">Interpretacja</button>
      <span id="hand-surface-simple-status">Jedna ścieżka pracy dla wybranego celu.</span>`;
    anchor.parentElement.insertBefore(nav, anchor);
    nav.querySelectorAll('[data-simple-nav]').forEach(btn => btn.onclick = () => {
      nav.querySelectorAll('[data-simple-nav]').forEach(x => x.classList.toggle('active', x === btn));
      const kind = btn.dataset.simpleNav;
      if (kind === 'material') {
        simplifyStudio();
        document.getElementById('hand-surface-studio')?.scrollIntoView({behavior:'smooth',block:'start'});
      } else if (kind === 'registration') {
        simplifyRegistration();
        document.getElementById('hand-surface-stages-20-22')?.scrollIntoView({behavior:'smooth',block:'start'});
      } else {
        const panel = findTextPanel('INTERPRETACJA BADAWCZA');
        if (panel) panel.scrollIntoView({behavior:'smooth',block:'start'});
      }
    });
  }

  function boot() {
    installCss();
    installTopNavigation();
    simplifyStudio();
    simplifyRegistration();
  }

  const observer = new MutationObserver(() => {
    installTopNavigation();
    simplifyStudio();
    simplifyRegistration();
  });
  observer.observe(document.body, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
