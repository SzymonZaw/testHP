(() => {
  const style = document.createElement('style');
  style.textContent = `
    .region-inspector-tools{display:flex;align-items:center;gap:6px;margin-top:-6px;margin-bottom:10px}
    .region-inspector-tools button{border:1px solid #d5dde2;background:#fff;color:#53616c;border-radius:8px;padding:6px 9px;font-size:9px;font-weight:750;cursor:pointer}
    .region-inspector-tools button:hover{border-color:#9fc5b8;background:#e9f4f0;color:#146b55}
    .ri-help{display:none;margin:0 0 12px;padding:10px 11px;border:1px solid #dbe5e1;border-radius:10px;background:#f7fbf9;color:#66747d;font-size:9px;line-height:1.55}
    .ri-help.open{display:block}
    .ri-help strong{display:block;margin-bottom:4px;color:#26343e;font-size:10px}
    .ri-evidence-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin:0 0 12px}
    .ri-evidence-chip{padding:7px 6px;border:1px solid #e1e6ea;border-radius:8px;background:#fafbfc;text-align:center}
    .ri-evidence-chip strong{display:block;font-size:10px;color:#26343e}
    .ri-evidence-chip span{display:block;margin-top:3px;font-size:7px;color:#8a969f;text-transform:uppercase;letter-spacing:.06em}
    .ri-evidence-chip.available{border-color:#cfe5dc;background:#f4faf7}
    .ri-evidence-chip.available span{color:#146b55}
    .ri-workflow{margin-top:10px;padding:9px 10px;border:1px dashed #cfd8de;border-radius:9px;background:#fff;color:#788690;font-size:8px;line-height:1.5}
    .ri-workflow strong{color:#53616c}
    .ri-action-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}
    .ri-action-row button{border:1px solid #d5dde2;background:#fff;color:#45525d;border-radius:8px;padding:7px 8px;font-size:9px;font-weight:700;cursor:pointer}
    .ri-action-row button:hover{border-color:#9fc5b8;background:#e9f4f0;color:#146b55}
    @media(max-width:700px){.ri-evidence-summary{grid-template-columns:repeat(2,1fr)}}
  `;
  document.head.appendChild(style);

  const get = id => document.getElementById(id);

  function ensureTools() {
    const inspector = document.querySelector('.inspector');
    const title = inspector?.querySelector('.panel-title');
    if (!inspector || !title || get('region-inspector-tools')) return;

    const tools = document.createElement('div');
    tools.id = 'region-inspector-tools';
    tools.className = 'region-inspector-tools';
    tools.innerHTML = '<button type="button" id="ri-help-toggle">ⓘ Jak to działa?</button>';
    title.after(tools);

    const help = document.createElement('div');
    help.id = 'ri-help';
    help.className = 'ri-help';
    help.innerHTML = '<strong>Wybrany region</strong>Ten panel pokazuje dane przypisane bezpośrednio do zaznaczonego miejsca. Makro oznacza fotografie powierzchni, tkanka — dane WSI, komórkowe — mikroskopię, a molekularne — pomiary molekularne. Brak danych oznacza brak jawnie przypiętego rekordu — system nie tworzy danych automatycznie.';
    tools.after(help);
    get('ri-help-toggle').onclick = () => {
      help.classList.toggle('open');
      get('ri-help-toggle').textContent = help.classList.contains('open') ? 'ⓘ Ukryj instrukcję' : 'ⓘ Jak to działa?';
    };

    const summary = document.createElement('div');
    summary.id = 'ri-evidence-summary';
    summary.className = 'ri-evidence-summary';
    summary.innerHTML = [['macro','Makro'],['tissue','Tkanka'],['cellular','Komórkowe'],['molecular','Molekularne']].map(([key,label]) => `<div class="ri-evidence-chip" data-ri-chip="${key}"><strong>—</strong><span>${label}</span></div>`).join('');
    help.after(summary);

    const workflow = document.createElement('div');
    workflow.id = 'ri-workflow';
    workflow.className = 'ri-workflow';
    workflow.innerHTML = '<strong>Przepływ danych</strong><br>przypisane → przygotowane → zarejestrowane → gotowe do projekcji 3D';
    summary.after(workflow);

    const actions = document.createElement('div');
    actions.id = 'ri-action-row';
    actions.className = 'ri-action-row';
    actions.innerHTML = '<button type="button" id="ri-add">＋ Dodaj obserwację</button><button type="button" id="ri-manage">Zarządzaj obserwacjami</button>';
    workflow.after(actions);

    get('ri-add').onclick = () => {
      const target = document.getElementById('register-observation') || document.getElementById('add-biological-observation');
      if (target) target.click();
      else document.querySelector('[data-action="add-observation"]')?.click();
    };
    get('ri-manage').onclick = () => {
      const target = document.querySelector('.evidence-management, [data-section="evidence-management"]');
      if (target) target.scrollIntoView({behavior:'smooth', block:'center'});
      else window.dispatchEvent(new CustomEvent('testhp:region-inspector-manage', {detail:{region:get('zone-label')?.textContent || 'palm'}}));
    };
  }

  function updateSummary() {
    const values = {
      macro: get('macro-state')?.textContent || '—',
      tissue: get('tissue-state')?.textContent || '—',
      cellular: get('cellular-state')?.textContent || '—',
      molecular: get('molecular-state')?.textContent || '—'
    };
    Object.entries(values).forEach(([key,value]) => {
      const chip = document.querySelector(`[data-ri-chip="${key}"]`);
      if (!chip) return;
      const strong = chip.querySelector('strong');
      if (strong && strong.textContent !== value) strong.textContent = value;
      const available = !/niedostępne|brak danych|nie pokazano|tylko dane nadrzędne|—/i.test(value);
      chip.classList.toggle('available', available);
    });
  }

  let scheduled = false;
  let running = false;
  const observer = new MutationObserver(() => {
    if (running || scheduled) return;
    scheduled = true;
    queueMicrotask(() => {
      scheduled = false;
      if (running) return;
      running = true;
      observer.disconnect();
      try { ensureTools(); updateSummary(); }
      finally {
        const inspector = document.querySelector('.inspector');
        if (inspector) observer.observe(inspector, {subtree:true, childList:true, characterData:true});
        running = false;
      }
    });
  });

  const start = () => {
    ensureTools();
    updateSummary();
    const inspector = document.querySelector('.inspector');
    if (inspector) observer.observe(inspector, {subtree:true, childList:true, characterData:true});
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true}); else start();
})();